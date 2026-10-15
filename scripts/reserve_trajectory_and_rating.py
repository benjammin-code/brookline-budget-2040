"""
Where reserves go under each forecast, and when that would matter to the rating.

Why this exists (2026-09-13, Ben: "we should also set some rules in the
forecast that say when/if we would be downgraded, and include the increased
borrowing costs that would trigger. we can talk in generalities since you
found that ratings agencies differ").

Reserves are the third thing that closes a budget gap in practice, alongside
overrides and cuts, and unlike the other two they can absorb a gap silently
for several years before anyone votes on anything. They are also what
Massachusetts credit ratings actually turn on: across every 2010-2026
Massachusetts downgrade whose rationale could be verified, reserve depletion
or structural imbalance was the stated driver, and pension and OPEB never
appeared as the lead cause.

## The rule this applies

Start from the last audited available fund balance and roll it forward,
letting reserves absorb each year's operating balance:

    reserves(t) = reserves(t-1) + operating_balance(t)
    ratio(t)    = reserves(t) / operating_revenue(t)

Then flag two thresholds, both of which Brookline has effectively adopted:

- **20% of revenue.** The Town's own formal Reserve Policy (FY2027 Financial
  Plan, Appendix) sets "no less than 20% of revenue," and Moody's February
  2024 credit opinion names a decline below 20% as its downgrade trigger. The
  two numbers coincide.
- **Zero.** The point at which reserves can no longer absorb anything and the
  gap must be met by an override or by cuts in the year it appears.

## What "downgrade" means here, stated carefully

This does NOT predict a downgrade. Rating agencies weigh a scorecard, they
disagree with each other on the same town in the same year (Moody's cut
Braintree in October 2025 while S&P affirmed it in February 2026), and a
single ratio breach is not a mechanical trigger. What the model does is
identify the year a stated threshold would be crossed on each path, which is
the most that can be said honestly.

Brookline's own position also carries more room than the headline suggests:
Moody's most recent published report (May 2025, on FY2023 data) puts its
available fund balance ratio at 27.1%, against the 23.1% in the February 2024
report on FY2022 data. Note that Moody's measure sweeps in operating funds
beyond the General Fund and so runs about six points above this project's
audit-derived figure; the two are tracked separately and never mixed.

## The borrowing cost, in generalities

Municipal AA bonds yielded roughly 10 basis points more than AAA at ten years
and roughly 20 at twenty to thirty years as of September 2026, which is close
to where that gap has sat for most of the last seven years. Applied to
Brookline's projected long-term debt, a one-notch penalty is worth the figures
in the output. This is deliberately expressed as an annual carrying cost on
the debt portfolio rather than as a present value on a single issue, because
the portfolio is what actually gets refinanced over time.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_CSV = ROOT / "output" / "reserve_trajectory_fy25_40.csv"
OUT_METHOD = ROOT / "output" / "reserve_trajectory_fy25_40_methodology.md"

# Base paths follow the driver forecast (the base case since 2026-09-29); the
# downside path stays the Town's own figures extended.
DRIVER = ROOT / "output" / "expense_driver_forecast_fy26_40.csv"
SURPLUS = ROOT / "output" / "baseline_surplus_deficit_forecast_fy26_40.csv"
BALSHEET = ROOT / "output" / "balance_sheet_liabilities_forecast_fy25_40.csv"

# Last audited figures. See reserves_and_free_cash.py for the full series and
# for why total GF balance is the right "available" measure for Brookline.
FY2024_AVAILABLE = 89_795_433
FY2024_REVENUE = 391_949_512

POLICY_FLOOR_PCT = 20.0
SPREAD_BP_LONG = 20      # AAA -> AA, 20-30yr, Sept 2026
SPREAD_BP_TEN = 10       # AAA -> AA, 10yr, Sept 2026

PATHS = {
    "as_legislated": (
        "Driver forecast (base case), with the May 2026 override in place."
    ),
    "structural": (
        "Driver forecast with the May 2026 override's revenue removed, keeping the "
        "spending it funded. Shows what the override is protecting rather than "
        "predicting anything."
    ),
    "downside": (
        "The Town's own published figures extended to FY2040, with reserves "
        "absorbing the whole gap. The stress case, not a forecast."
    ),
}


def load():
    with open(DRIVER) as f:
        d = list(csv.DictReader(f))
    with open(SURPLUS) as f:
        s = list(csv.DictReader(f))
    bal = {}
    with open(BALSHEET) as f:
        for r in csv.DictReader(f):
            bal[int(r["fiscal_year"])] = float(r["long_term_debt_total"])
    series = {
        "as_legislated": {
            int(r["fiscal_year"]): (float(r["surplus_deficit"]), float(r["operating_revenue"]))
            for r in d
        },
        "structural": {
            int(r["fiscal_year"]): (float(r["surplus_deficit_ex_override"]),
                                    float(r["operating_revenue"]) - float(r["may_2026_override_value"]))
            for r in d
        },
        "downside": {
            int(r["fiscal_year"]): (float(r["operating_surplus_deficit"]), float(r["operating_revenue"]))
            for r in s if r["scenario"] == "town_assumptions"
        },
    }
    return series, bal


def main():
    series, debt = load()
    rows = []
    summary = {}

    for name, desc in PATHS.items():
        reserves = FY2024_AVAILABLE
        breach_year = exhaust_year = None
        for year in sorted(series[name]):
            bal, rev = series[name][year]
            reserves += bal
            ratio = 100 * reserves / rev
            if breach_year is None and ratio < POLICY_FLOOR_PCT:
                breach_year = year
            if exhaust_year is None and reserves <= 0:
                exhaust_year = year
            d = debt.get(year, 0.0)
            rows.append(
                {
                    "path": name,
                    "fiscal_year": year,
                    "operating_balance": round(bal),
                    "operating_revenue": round(rev),
                    "available_reserves": round(reserves),
                    "reserves_pct_of_revenue": round(ratio, 2),
                    "below_20pct_policy_floor": ratio < POLICY_FLOOR_PCT,
                    "reserves_exhausted": reserves <= 0,
                    "long_term_debt": round(d),
                    # What one notch would cost that year, as an annual carrying
                    # cost on the whole portfolio. See the docstring.
                    "one_notch_annual_cost_at_20bp": round(d * SPREAD_BP_LONG / 10_000),
                    "path_assumption": desc,
                }
            )
        summary[name] = (breach_year, exhaust_year, reserves, ratio)

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT_CSV}")

    for name, (b, e, r, ratio) in summary.items():
        print(
            f"  {name:15} FY2040 reserves ${r/1e6:8,.1f}M ({ratio:6.1f}% of revenue)"
            f"   below 20%: {b or 'never'}   exhausted: {e or 'never'}"
        )

    write_methodology(rows, summary, debt)
    print(f"Wrote {OUT_METHOD}")


def write_methodology(rows, summary, debt):
    L = ["# Reserve Trajectory and Rating Thresholds, FY2025-2040 — Methodology\n"]
    L.append(
        "Companion to `reserve_trajectory_fy25_40.csv`. Rolls the last audited "
        "reserve balance forward under each forecast and flags where stated "
        "thresholds would be crossed.\n"
    )
    L.append(__doc__.split("## The rule this applies")[1].split("## The borrowing cost")[0].strip() + "\n")

    L.append("## Result\n")
    L.append("| Path | FY2040 reserves | % of revenue | Falls below 20% | Exhausted |\n|---|---|---|---|---|")
    for name, (b, e, r, ratio) in summary.items():
        L.append(
            f"| {name} | ${r/1e6:,.1f}M | {ratio:.1f}% | "
            f"{('FY' + str(b)) if b else 'never'} | {('FY' + str(e)) if e else 'never'} |"
        )
    L.append("")
    L.append(
        "Read the three together rather than separately. Under the base case as "
        "legislated, reserves are never drawn on at all, because the May 2026 "
        "override holds the operating budget in surplus for the whole window. "
        "That is the realistic path and it is the reason this section is not an "
        "alarm. The other two show what reserves are insuring against.\n"
    )
    L.append(
        "One honest qualification on the first path: a town that ran a surplus "
        "of roughly 4% of revenue for fifteen consecutive years would not "
        "accumulate it. The twenty-year record is that Brookline spends close "
        "to what it has. Treat the as-legislated reserve line as headroom that "
        "gets used, not as a balance that builds.\n"
    )

    L.append("## What one notch would cost\n")
    L.append("| FY | Projected long-term debt | Annual cost at 20 bp |\n|---|---|---|")
    for y in (2030, 2035, 2040):
        d = debt.get(y, 0.0)
        L.append(f"| {y} | ${d/1e6:,.1f}M | ${d * SPREAD_BP_LONG / 10_000:,.0f} |")
    L.append("")
    L.append(
        f"At the September 2026 spread of roughly **{SPREAD_BP_TEN} basis points "
        f"at ten years and {SPREAD_BP_LONG} at twenty to thirty**, one notch "
        "costs Brookline in the low hundreds of thousands a year against a "
        "declining debt portfolio. For scale, that is a fraction of the "
        "structural wedge itself.\n"
    )
    L.append(
        "The cost of a downgrade is therefore not mainly the interest. It is "
        "that the conditions producing a downgrade, sustained deficits and "
        "falling reserves, are expensive in their own right, and the rating is "
        "a signal of them rather than the harm itself.\n"
    )

    L.append("## What this deliberately does not claim\n")
    L.append(
        "- **It does not predict a downgrade.** Agencies weigh a full scorecard "
        "and disagree with each other on the same town in the same year. A "
        "single ratio crossing a stated threshold is a flag, not a mechanism.\n"
        "- **It does not model reserve policy behaviour.** Real towns replenish "
        "reserves deliberately, and Brookline has: available fund balance went "
        "from 12.29% of revenue in FY2019 to 22.91% in FY2024. The roll-forward "
        "here is mechanical and makes no allowance for that.\n"
        "- **It does not use Moody's own measure.** Moody's available fund "
        "balance ratio sweeps in operating funds beyond the General Fund and "
        "runs about six points higher than the audit-derived figure used here, "
        "so this model is the conservative one. Peer comparisons should use "
        "Moody's series, not this one.\n"
    )
    OUT_METHOD.write_text("\n".join(L))


if __name__ == "__main__":
    main()
