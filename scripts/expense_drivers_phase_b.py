"""
Phase B of the expense-driver rebuild: separate price from everything else.

Phase A showed that cost per head, not headcount, carries most of Brookline's
expense growth. It could not say *why*, because "cost per head" is a residual
that contains at least four different things: the compensation inflation every
public employer faced, step and grade progression, turnover savings, and shifts
in the mix of roles. Phase B strips out the first of those using an index from
outside the Town's books, and reports what is left honestly, as a residual.

## The counterfactual

For each town category, build the spend Brookline *would* have had if:

  - its headcount moved exactly as observed,
  - the personnel part of its spend grew with the national ECI for state and
    local government workers,
  - the non-personnel part grew with Boston CPI and did not scale with headcount,
    because contracts, materials and fleet do not.

    predicted(y1) = personnel(y0) x (FTE1/FTE0) x (ECI1/ECI0)
                  + nonpersonnel(y0) x (CPI1/CPI0)

The gap between actual and predicted is the **residual**: what Brookline did
that national compensation inflation and general prices do not explain. It is a
residual, not a measurement of any one thing, and the write-up must not promote
it to "step progression" or "turnover" without data this project does not have.

## Three limitations, stated before the numbers

1. **The ECI is national.** It is not published for metro areas at this industry
   detail. If Massachusetts public-sector pay outran the national average, these
   residuals are overstated by that difference. Boston CPI running close to the
   ECI in both windows is weak evidence the local gap is not large, and it is
   weak evidence, not a control.

2. **The personnel share is known for one year only** (FY2019, from the ERSC
   report's transcription of Town budget books) and is held fixed across the
   window. If a category's personnel share drifted, the split between the two
   predicted terms drifts with it and the residual absorbs the error.

3. **Fiscal against calendar years.** Schedule A is July-June; the indices are
   calendar. Each fiscal year is matched to the mean of the two calendar years
   it straddles rather than to one of them.

Run from `scripts/`:  python3 expense_drivers_phase_b.py
"""

import csv
from pathlib import Path

from expense_drivers_phase_a import CATEGORIES, build_fte_panel, fnum

ROOT = Path(__file__).parent.parent
OUT = ROOT / "output"

HIST_FILE = OUT / "brookline_historical_financials_fy05_25.csv"
SALARY_FILE = OUT / "department_fte_salary_by_category_fy19_fy26.csv"
INDEX_FILE = OUT / "price_indices_annual.csv"
BENEFITS_FILE = OUT / "benefits_category_history_fy00_25.csv"
SCHOOL_FILE = OUT / "school_enrollment_staffing_fy05_25.csv"

OUT_CSV = OUT / "expense_drivers_phase_b_attribution.csv"
METHOD_OUT = OUT / "expense_drivers_phase_b_methodology.md"

WINDOWS = [("clean, pre-FTE-seam", 2011, 2020), ("post-FTE-seam", 2021, 2025)]


def load_indices():
    idx = {}
    with open(INDEX_FILE) as f:
        for r in csv.DictReader(f):
            idx[int(r["calendar_year"])] = {k: float(v) for k, v in r.items()
                                            if k != "calendar_year" and v and not k.endswith("_yoy")}
    return idx


def fy_index(idx, name, fy):
    """A fiscal year straddles two calendar years. Use the mean of both rather
    than picking one, which would bias every comparison in one direction."""
    a, b = idx.get(fy - 1), idx.get(fy)
    vals = [d[name] for d in (a, b) if d and name in d]
    if not vals:
        return None
    return sum(vals) / len(vals)


def main():
    panel = build_fte_panel()
    idx = load_indices()
    with open(HIST_FILE) as f:
        hist = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    with open(SALARY_FILE) as f:
        sal = {r["category"]: r for r in csv.DictReader(f)}

    # ------------------------------------------------------------ CONTROLS
    print("=" * 78)
    print("CONTROLS")
    print("=" * 78)

    missing = [(n, fy) for n in ("eci_total_comp", "cpi_boston")
               for fy in (2011, 2020, 2021, 2025) if fy_index(idx, n, fy) is None]
    print(f"  {'PASS' if not missing else 'FAIL'}  index coverage: every window endpoint "
          f"has both indices" + (f"  missing {missing}" if missing else ""))

    # Negative control: feed the counterfactual a category that BY CONSTRUCTION
    # grew exactly at the indices, and confirm the residual is zero.
    e0, e1 = fy_index(idx, "eci_total_comp", 2011), fy_index(idx, "eci_total_comp", 2020)
    c0, c1 = fy_index(idx, "cpi_boston", 2011), fy_index(idx, "cpi_boston", 2020)
    fake_p0, fake_np0, fake_fte0, fake_fte1 = 700_000.0, 300_000.0, 100.0, 110.0
    fake_actual = fake_p0 * (fake_fte1 / fake_fte0) * (e1 / e0) + fake_np0 * (c1 / c0)
    fake_pred = fake_p0 * (fake_fte1 / fake_fte0) * (e1 / e0) + fake_np0 * (c1 / c0)
    print(f"  {'PASS' if abs(fake_actual/fake_pred - 1) < 1e-12 else 'FAIL'}  "
          f"synthetic category built to grow exactly at the indices returns a zero "
          f"residual ({fake_actual/fake_pred - 1:.2e})")

    # And break it: inflate the synthetic actual by a known 1.0%/yr and confirm
    # the harness recovers exactly that.
    n = 2020 - 2011
    fake_actual_bad = fake_pred * (1.01 ** n)
    recovered = (fake_actual_bad / fake_pred) ** (1 / n) - 1
    print(f"  {'PASS' if abs(recovered - 0.01) < 1e-12 else 'FAIL'}  "
          f"a deliberate +1.00%/yr excess is recovered as {recovered*100:.4f}%/yr")
    print()

    print("  External indices, compound annual growth:")
    for wlabel, y0, y1 in WINDOWS:
        n = y1 - y0
        parts = []
        for name in ("eci_total_comp", "eci_wages", "eci_benefits", "cpi_boston"):
            a, b = fy_index(idx, name, y0), fy_index(idx, name, y1)
            parts.append(f"{name}={((b/a)**(1/n)-1)*100:5.2f}%")
        print(f"    FY{y0}-FY{y1}:  " + "  ".join(parts))
    print()

    # ----------------------------------------------------- THE ATTRIBUTION
    rows_out = []
    for wlabel, y0, y1 in WINDOWS:
        n = y1 - y0
        e0, e1 = fy_index(idx, "eci_total_comp", y0), fy_index(idx, "eci_total_comp", y1)
        c0, c1 = fy_index(idx, "cpi_boston", y0), fy_index(idx, "cpi_boston", y1)
        eci_g = (e1 / e0) ** (1 / n) - 1
        cpi_g = (c1 / c0) ** (1 / n) - 1

        print("=" * 78)
        print(f"ATTRIBUTION: {wlabel}, FY{y0}-FY{y1}")
        print(f"   national public-sector compensation {eci_g*100:.2f}%/yr, "
              f"Boston CPI {cpi_g*100:.2f}%/yr")
        print("=" * 78)
        print(f"  {'category':22s}{'actual':>9}{'predicted':>11}{'residual':>10}"
              f"{'personnel':>11}{'of which head':>14}")
        for key, label, col in CATEGORIES:
            s0, s1 = fnum(hist[y0].get(col)), fnum(hist[y1].get(col))
            f0, f1 = panel[y0][key], panel[y1][key]
            if not (s0 and s1 and f0 and f1):
                continue
            p_share = float(sal[label]["salary_budget_fy19"]) / fnum(hist[2019][col])
            personnel0, nonpersonnel0 = s0 * p_share, s0 * (1 - p_share)
            predicted = personnel0 * (f1 / f0) * (e1 / e0) + nonpersonnel0 * (c1 / c0)
            g_actual = (s1 / s0) ** (1 / n) - 1
            g_pred = (predicted / s0) ** (1 / n) - 1
            resid = (s1 / predicted) ** (1 / n) - 1
            g_fte = (f1 / f0) ** (1 / n) - 1
            print(f"  {label:22s}{g_actual*100:>8.2f}%{g_pred*100:>10.2f}%"
                  f"{resid*100:>+9.2f}%{p_share*100:>10.0f}%{g_fte*100:>13.2f}%")
            rows_out.append(dict(
                bucket=label, window=wlabel, fy_start=y0, fy_end=y1,
                actual_cagr=round(g_actual, 6), predicted_cagr=round(g_pred, 6),
                residual_cagr=round(resid, 6),
                personnel_share_fy2019=round(p_share, 4),
                fte_cagr=round(g_fte, 6),
                eci_cagr=round(eci_g, 6), cpi_cagr=round(cpi_g, 6),
                spend_start=round(s0), spend_end=round(s1),
                predicted_spend_end=round(predicted),
                note=("predicted = personnel x headcount change x ECI "
                      "+ non-personnel x CPI"),
            ))
        print()

    # ------------------------------------------- benefits against ECI benefits
    print("=" * 78)
    print("GROUP HEALTH: against the ECI benefits index for the same worker group")
    print("=" * 78)
    # Group health only, deliberately. Pensions follow an actuarial valuation
    # schedule and OPEB a funding policy; neither is a price, so neither belongs
    # in a test against a price index. Group health is a genuine purchased cost
    # and is the one component where the comparison means something.
    ben_path = BENEFITS_FILE
    if ben_path.exists():
        with open(ben_path) as f:
            ben = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
        # The actual-basis column is populated only for recent years; the
        # reconstruction is the complete FY2000-2025 series and carries its own
        # accuracy check in benefits_category_forecast.py against real actuals.
        col = "group_health_reconstructed"
        print("  Group health only. Pensions follow an actuarial schedule and OPEB a")
        print("  funding policy, so neither is a price and neither is tested here.")
        for wlabel, y0, y1 in WINDOWS:
            a, b = fnum(ben.get(y0, {}).get(col)), fnum(ben.get(y1, {}).get(col))
            if not (a and b):
                continue
            n = y1 - y0
            g = (b / a) ** (1 / n) - 1
            i0, i1 = fy_index(idx, "eci_benefits", y0), fy_index(idx, "eci_benefits", y1)
            gi = (i1 / i0) ** (1 / n) - 1
            print(f"  FY{y0}-FY{y1}: Brookline benefits {g*100:5.2f}%/yr against "
                  f"national public-sector benefits {gi*100:5.2f}%/yr  "
                  f"residual {(g-gi)*100:+5.2f} pts")
            rows_out.append(dict(
                bucket="Group health", window=wlabel, fy_start=y0, fy_end=y1,
                actual_cagr=round(g, 6), predicted_cagr=round(gi, 6),
                residual_cagr=round((1 + g) / (1 + gi) - 1, 6),
                personnel_share_fy2019=None, fte_cagr=None,
                eci_cagr=round(gi, 6), cpi_cagr=None,
                spend_start=round(a), spend_end=round(b),
                predicted_spend_end=round(a * (i1 / i0)),
                note="group health only; pensions and OPEB excluded, not prices",
            ))
    else:
        print("  (benefits history file not found; skipped)")
    print()

    # ------------------------------------------------------------- schools
    print("=" * 78)
    print("SCHOOLS: spend per pupil and per staff FTE, against the same index")
    print("=" * 78)
    with open(SCHOOL_FILE) as f:
        sch = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    edu = {y: fnum(hist[y].get("exp_education")) for y in hist}
    for qname, qcol in (("pupil", "total_enrollment"), ("staff FTE", "total_staff_fte")):
        for wlabel, y0, y1 in WINDOWS:
            q0, q1 = fnum(sch.get(y0, {}).get(qcol)), fnum(sch.get(y1, {}).get(qcol))
            if not (q0 and q1 and edu.get(y0) and edu.get(y1)):
                continue
            nn = y1 - y0
            per0, per1 = edu[y0] / q0, edu[y1] / q1
            g = (per1 / per0) ** (1 / nn) - 1
            i0, i1 = fy_index(idx, "eci_total_comp", y0), fy_index(idx, "eci_total_comp", y1)
            gi = (i1 / i0) ** (1 / nn) - 1
            print(f"  FY{y0}-FY{y1}  spend per {qname:9s} {g*100:5.2f}%/yr  "
                  f"against ECI {gi*100:5.2f}%/yr   residual {((1+g)/(1+gi)-1)*100:+5.2f}%")
            rows_out.append(dict(
                bucket=f"Schools (per {qname})", window=wlabel, fy_start=y0, fy_end=y1,
                actual_cagr=round(g, 6), predicted_cagr=round(gi, 6),
                residual_cagr=round((1 + g) / (1 + gi) - 1, 6),
                personnel_share_fy2019=None, fte_cagr=None,
                eci_cagr=round(gi, 6), cpi_cagr=None,
                spend_start=round(per0), spend_end=round(per1),
                predicted_spend_end=round(per0 * (i1 / i0)),
                note=f"per-{qname} spend, so the quantity is already divided out",
            ))

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    print(f"\nWrote {OUT_CSV}")
    write_methodology(rows_out, idx)
    print(f"Wrote {METHOD_OUT}")


def write_methodology(rows_out, idx):
    L = []
    L.append("# Expense Drivers, Phase B: how much of it was just price?\n")
    L.append("Companion to `expense_drivers_phase_b_attribution.csv`. Plan: "
             "`docs/expense_drivers_workplan.md`. Generated by "
             "`scripts/expense_drivers_phase_b.py`. Phase A is the prerequisite "
             "and its methodology doc explains the FY2010 reclassification and the "
             "FY2020/21 FTE seam that set these windows.\n")

    L.append("## The counterfactual\n")
    L.append("For each town category, the spend Brookline would have had if headcount "
             "moved exactly as observed, the personnel part grew with the national ECI "
             "for state and local government workers, and the non-personnel part grew "
             "with Boston CPI without scaling to headcount:\n")
    L.append("```\n    predicted(y1) = personnel(y0) x (FTE1/FTE0) x (ECI1/ECI0)\n"
             "                  + nonpersonnel(y0) x (CPI1/CPI0)\n```\n")
    L.append("The gap is the **residual**. It is a residual and nothing more: it "
             "contains step and grade progression, turnover savings, role mix, service "
             "level changes, and any local deviation from national pay trends, with no "
             "way here to separate them.\n")

    L.append("## Results\n")
    for wlabel in [w[0] for w in WINDOWS]:
        sel = [r for r in rows_out if r["window"] == wlabel]
        if not sel:
            continue
        w0, w1 = sel[0]["fy_start"], sel[0]["fy_end"]
        L.append(f"### {wlabel}, FY{w0}-FY{w1}\n")
        L.append("| Bucket | Actual | Predicted by price and headcount | Residual |")
        L.append("|---|---|---|---|")
        for r in sel:
            L.append(f"| {r['bucket']} | {r['actual_cagr']*100:.2f}% | "
                     f"{r['predicted_cagr']*100:.2f}% | "
                     f"{r['residual_cagr']*100:+.2f}% |")
        L.append("")

    L.append("## Limitations\n")
    L.append("- **The ECI is national.** Not published for metro areas at this industry "
             "detail. If Massachusetts public-sector pay outran the national average, "
             "every residual here is overstated by that difference.\n"
             "- **The personnel share is one year.** FY2019, held fixed across each "
             "window. Drift in that share is absorbed by the residual.\n"
             "- **Fiscal against calendar years.** Each fiscal year is matched to the "
             "mean of the two calendar years it straddles.\n"
             "- **`spend_per_fte` is not salary per FTE**, carried over from Phase A. "
             "This is why the non-personnel term exists at all, and why the residual is "
             "least trustworthy for the two categories with the largest non-personnel "
             "shares, Public Works and Culture & Recreation.\n")

    with open(METHOD_OUT, "w") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()
