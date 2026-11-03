"""Compare the School Committee's standing BEU wage offer (fall 2026) with the forecast's school pay rate.

The forecast prices school pay per position at 3.7%/yr from FY2028 (FY2027 is the adopted budget):
the middle of the range PSB's own FY2026 level-service build gives at a 2.75% raise
(raise + steps 1.59% + lanes 0.14% + principals 0.05% - breakage, with breakage between the
budgeted 0.42% and FY2025's actual ~1%). This script swaps the 2.75% raise for the raise the
School Committee's offer gives each fiscal year, keeping the same step/lane/breakage terms.

Sources (see output/beu_bargaining_2026_wage_offers_notes.md):
- Unit A/B offer: Sept 17 / Sept 23, 2026 session recordings; still standing Oct 27.
- Para offer: June 16, 2026 recording ($2/hr per year, schedules 2, 2A, 3, 5; 2% other schedules).
  The latest district para wage offer on the record we found; not restated since.
- Payroll mix: FY2026 closing summary (data/psb_budget/FY26_budget_closing_summary.pdf), YTD actuals.
- Teacher schedule: output/beu_unitA_teacher_salary_schedules_fy24_27.csv (FY2027 = 8/31/2026 grid).
- Para rates: BEU June 2026 presentation, Schedule 2 steps 3-11 (FY2026 rates) + 1% on 8/31/2026.
- Share at top step: ERSC final report, 52% of educators still on steps (so 48% at top);
  a School Committee member said 60/40 at the table on Sept 17.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "beu_offer_vs_forecast.md"

MODEL_RATE = 0.037
MODEL_RAISE = 0.0275
DRIFT_LOW, DRIFT_HIGH = 0.033 - MODEL_RAISE, 0.041 - MODEL_RAISE  # step/lane net of breakage
DRIFT_MID = MODEL_RATE - MODEL_RAISE

# FY2026 salary actuals by account (closing summary, YTD expended)
PAYROLL = {
    "Professional Staff (Unit A)": 87_835_913,
    "Paraprofessionals": 12_963_314,
    "Management (Unit B + non-aligned)": 4_528_170,
    "Leadership": 6_704_693,
    "Administrative Support": 5_271_786,
    "Substitutes": 1_370_151,
    "Custodians": 3_333_180,
    "Summer Programs/Interns": 367_092,
    "Stipends/Extra Comp": 1_664_464,
}  # the one-time Retirement Incentive ($405,575) is left out


def fy_growth(sept, mid, mid_share=0.5):
    """Fiscal-year-over-fiscal-year growth when each year gives +sept on Sept 1 and +mid at mid-year.

    The mid-year raise lands about halfway through the school year, so a fiscal year carries
    half of it; in steady state each year's growth is (1+sept)*(1+mid) - 1."""
    return (1 + sept) * (1 + mid) - 1


def unit_a_top_payroll_share(top_headcount_share):
    """Pay-weight the top step: top-step salary vs the average salary on the lower steps (masters lane)."""
    rows = [r for r in csv.DictReader(open(ROOT / "output" / "beu_unitA_teacher_salary_schedules_fy24_27.csv"))
            if r["fiscal_year"] == "2027" and r["lane"] == "masters"]
    sal = {int(r["step"]): float(r["salary"]) for r in rows}
    top = max(sal)
    lower = [v for k, v in sal.items() if k < top]
    avg_lower = sum(lower) / len(lower)
    t = top_headcount_share * sal[top]
    return t / (t + (1 - top_headcount_share) * avg_lower), sal[top], avg_lower


def para_rate_growth():
    fy26 = [29.47, 30.10, 30.74, 31.39, 32.07, 32.75, 33.46, 34.19, 35.04]  # Schedule 2, steps 3-11
    base = sum(fy26) / len(fy26) * 1.01  # FY2027 rate after the 8/31/2026 1%
    out = []
    for _ in range(3):
        out.append(2.0 / base)
        base += 2.0
    return out  # FY2027, FY2028, FY2029


def main():
    total = sum(PAYROLL.values())
    w = {k: v / total for k, v in PAYROLL.items()}

    nontop = fy_growth(0.015, 0.005)
    top = fy_growth(0.0225, 0.0025)
    para = para_rate_growth()

    lines = ["# School Committee's BEU offer vs. the forecast's 3.7% school pay rate", "",
             "Built by `scripts/beu_offer_vs_forecast.py`. FY2027 is the adopted budget in the model, so the",
             "comparison is FY2028 and FY2029 (contract years 2 and 3).", "",
             "## Payroll mix (FY2026 actual salaries)", "", "| Account | $ | Share |", "|---|---:|---:|"]
    for k, v in PAYROLL.items():
        lines.append(f"| {k} | {v:,.0f} | {w[k]:.1%} |")
    lines += [f"| Total | {total:,.0f} | 100% |", ""]

    results = []
    for label, top_hc, para_dollar_share, other_raise in [
        ("Low", 0.40, 0.70, 0.015),
        ("Middle", 0.48, 0.85, 0.020),
        ("High", 0.48, 1.00, 0.025),
    ]:
        tshare, top_sal, avg_lower = unit_a_top_payroll_share(top_hc)
        unit_a = tshare * top + (1 - tshare) * nontop
        para_fy28 = para_dollar_share * para[1] + (1 - para_dollar_share) * 0.02
        raise_fy28 = (w["Professional Staff (Unit A)"] * unit_a
                      + w["Paraprofessionals"] * para_fy28
                      + w["Management (Unit B + non-aligned)"] * unit_a
                      + w["Stipends/Extra Comp"] * 0.02
                      + sum(w[k] for k in ["Leadership", "Administrative Support", "Substitutes",
                                           "Custodians", "Summer Programs/Interns"]) * other_raise)
        results.append((label, top_hc, tshare, para_dollar_share, other_raise, unit_a, para_fy28, raise_fy28))

    lines += ["## Raise each fiscal year under the offer", "",
              f"- Unit A/B salary cells below the top step: +1.5% Sept 1 and +0.5% mid-year = {nontop:.2%} a year.",
              f"- Top step: +2.25% and +0.25% = {top:.2%} a year.",
              f"- Paras on the hourly schedules: +$2/hr a year = {para[1]:.1%} in FY2028, {para[2]:.1%} in FY2029 "
              f"(Schedule 2 average rate after the 8/31/2026 1%: ${2/para[0]:.2f}/hr).",
              "- Everyone else (leadership, secretaries and custodians in other unions, substitutes) is not",
              "  covered by this offer; assumed 1.5% / 2.0% / 2.5% across the cases (the Town's plan assumes",
              "  1.5-2% for its own staff).", "",
              "| Case | At top step (headcount) | Top step share of Unit A payroll | Paras on $ schedules | Others | Unit A/B | Paras | Weighted raise FY2028 |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in results:
        lines.append(f"| {r[0]} | {r[1]:.0%} | {r[2]:.0%} | {r[3]:.0%} | {r[4]:.1%} | {r[5]:.2%} | {r[6]:.2%} | {r[7]:.2%} |")

    mid = results[1][7]
    lo_total = results[0][7] + DRIFT_LOW
    hi_total = results[2][7] + DRIFT_HIGH
    lines += ["", "## Pay growth per position", "",
              f"Steps, lanes and principal adjustments net of turnover savings add {DRIFT_LOW:.2%} to "
              f"{DRIFT_HIGH:.2%} (PSB's FY2026 build; the model's 3.7% uses the middle, {DRIFT_MID:.2%}).", "",
              f"- Middle case: {mid:.2%} raise + {DRIFT_MID:.2%} = **{mid + DRIFT_MID:.2%}** a year, vs. the model's 3.70%.",
              f"- Full range: {lo_total:.2%} to {hi_total:.2%}.",
              f"- The same arithmetic at the model's 2.75% raise gives 3.70%, so the offer runs "
              f"{(mid - MODEL_RAISE)*100:+.2f} points against the model in the middle case.", "",
              "Pay weighting of the top step: top masters step $%s vs. $%s average on the lower steps (FY2027 grid)." % (
                  f"{unit_a_top_payroll_share(0.48)[1]:,.0f}", f"{unit_a_top_payroll_share(0.48)[2]:,.0f}"),
              "",
              f"In dollars: on a school payroll of about ${total*1.04**2/1e6:,.0f}M in FY2028, the middle case is about "
              f"${(MODEL_RAISE-mid)*total*1.04**2/1e6:.1f}M a year below the model in FY2028 and about "
              f"${2*(MODEL_RAISE-mid)*total*1.04**3/1e6:.1f}M below by FY2029.", "",
              "Cross-check that does not reconcile: on June 16 the district put the para $2/hr raises at about $1.1M",
              f"\"for $6 over 3 years\" (auto-transcript). The rate arithmetic here gives about ${para[1]*0.85*PAYROLL['Paraprofessionals']/1e6:.1f}M in FY2028 alone.",
              "If the district's figure is right, paras weigh less and the offer runs a little further below 3.7%.", "",
              "FY2027 (contract year 1) is outside this comparison: the offer's +1.5% Sept 1 and half a year of the",
              f"+0.5% mid-year add about {fy_growth(0.015, 0.0025):.2%} (${fy_growth(0.015, 0.0025)*total*1.04/1e6:.1f}M) on top of the old contract's 1%. The adopted",
              "FY2027 budget doesn't state what raise it reserved; PSB's estimate of +3.78% for Professional Staff",
              "wages in FY2027 (ERSC footnote 28) leaves room for roughly 1-1.5 points beyond the 1% and steps (inference).", "",
              "Not in this arithmetic: the 6/9/12-week paid parental leave and any change in who is on steps."]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
