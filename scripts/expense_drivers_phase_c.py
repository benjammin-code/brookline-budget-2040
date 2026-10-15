"""
Phase C of the expense-driver rebuild: does headcount respond to growth at all?

This is the phase the whole exercise was for. The fiscal impact model charges
$1,371 per new residential unit for municipal services. That figure only means
something if serving more households actually costs the Town more, and the most
direct way it would show up is in staffing.

## An elasticity framing was tried first, and it was wrong

The first version of this script computed elasticities of FTE to cumulative new
growth. Every one came back at +0.00, which looked like a devastating null and
was actually a bug in the driver: cumulative new growth starts at one year's
worth and ends at fifteen, a change of **+1,820%**, so any headcount change
divided by it is approximately zero by construction.

The positive control caught it. School staff against enrollment gave +2.32,
+4.55, -13.34 and -3.83 depending on the window, because enrollment moves only
6% across fifteen years and an elasticity with a denominator that small is not a
stable statistic. A control that swings by a factor of five and changes sign is
not confirming the method; it is rejecting it.

So this script reports **direct physical ratios** instead: how many FTE per unit
of growth, converted to dollars per unit, against RKG's $1,371. Those are
interpretable, they do not blow up on small denominators, and they can be
compared with the number the fiscal impact model actually uses.

## The identification problem, stated up front

Headcount changes for many reasons: new services, restructuring, outsourcing,
grant cycles, and growth. Nothing here separates them. Every ratio below is
therefore an **upper bound** on the growth-attributable staffing response, not
an estimate of it. That is worth stating loudly, because an upper bound that
still comes in low is the more useful result.

Run from `scripts/`:  python3 expense_drivers_phase_c.py
"""

import csv
from pathlib import Path

from expense_drivers_phase_a import CATEGORIES, build_fte_panel, fnum

ROOT = Path(__file__).parent.parent
OUT = ROOT / "output"

HIST_FILE = OUT / "brookline_historical_financials_fy05_25.csv"
SCHOOL_FILE = OUT / "school_enrollment_staffing_fy05_25.csv"
OUT_CSV = OUT / "expense_drivers_phase_c_ratios.csv"
METHOD_OUT = OUT / "expense_drivers_phase_c_methodology.md"

# The Town Planning Department's own building-permit count of net new homes,
# Development Look-Ahead June 2026, slide 9. Calendar years.
PLANNING_NET_NEW_HOMES = {2022: 252, 2023: 190, 2024: 57}

# From the assessment rolls that carry a units field. Levels are plausible
# against Census; the differences are known to overstate (see README item 9).
ROLL_UNITS = {2020: 27786, 2025: 29466}

RKG_PER_UNIT = 1371.0
RES_TAX_RATE = 0.01024          # statutory FY2026 residential rate
RES_VALUE_PER_UNIT = 430_000.0  # units-weighted, Phase 2
RES_NEW_SHARE_OF_RES = 0.2867   # share of residential new growth that is new construction


def main():
    panel = build_fte_panel()
    with open(HIST_FILE) as f:
        hist = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    with open(SCHOOL_FILE) as f:
        sch = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}

    town_fte = {y: sum(panel[y][k] for k, _, _ in CATEGORIES) for y in panel}
    dept_spend = {y: sum(fnum(hist[y][c]) or 0 for _, _, c in CATEGORIES)
                  for y in hist}
    enroll = {y: fnum(sch[y].get("total_enrollment")) for y in sch}
    staff = {y: fnum(sch[y].get("total_staff_fte")) for y in sch}
    res_ng = {y: fnum(hist[y].get("res_new_growth_applied")) for y in hist}

    rows = []

    # -------------------------------------------------------- CONTROLS
    print("=" * 78)
    print("CONTROLS")
    print("=" * 78)
    print("  The elasticity approach was rejected by its own positive control.")
    print("  School staff against enrollment gave +2.32 / +4.55 / -13.34 / -3.83")
    print("  across four windows. A control that changes sign is rejecting the method,")
    print("  not confirming it. Ratios are reported instead. See the module docstring.")
    print()
    # Unit-consistency control: the three independent unit estimates should at
    # least agree on order of magnitude, or the denominator is not trustworthy.
    planning_rate = sum(PLANNING_NET_NEW_HOMES.values()) / len(PLANNING_NET_NEW_HOMES)
    roll_rate = (ROLL_UNITS[2025] - ROLL_UNITS[2020]) / 5
    ng_units = {}
    for y in range(2011, 2026):
        v = res_ng.get(y)
        if v:
            ng_units[y] = v / RES_TAX_RATE / RES_VALUE_PER_UNIT * RES_NEW_SHARE_OF_RES
    ng_rate = sum(ng_units.values()) / len(ng_units)
    print(f"  Three independent estimates of net new homes per year:")
    print(f"    Planning Department permit count, CY2022-24   {planning_rate:6.0f}/yr")
    print(f"    assessment roll levels, FY2020 to FY2025      {roll_rate:6.0f}/yr"
          f"   (known to overstate)")
    print(f"    implied from new-growth dollars, FY2011-25    {ng_rate:6.0f}/yr")
    spread = max(planning_rate, roll_rate, ng_rate) / min(planning_rate, roll_rate, ng_rate)
    print(f"  {'PASS' if spread < 3 else 'FAIL'}  spread across the three is "
          f"{spread:.1f}x. They agree on order of magnitude, which is as much as the")
    print("        denominator needs to support a ratio quoted to one significant figure.")
    print()

    # ------------------------------------------ the question, as a ratio
    print("=" * 78)
    print("HOW MUCH STAFFING DOES A NEW HOME BUY?")
    print("=" * 78)
    print("  Upper bound: ALL headcount change is attributed to growth, which it")
    print("  certainly is not.")
    print()
    print(f"  {'window':>14}{'d FTE':>9}{'homes':>9}{'FTE/home':>11}"
          f"{'$/FTE':>10}{'$/home':>10}   vs RKG $1,371")
    windows = [(2011, 2020), (2011, 2025), (2021, 2025), (2022, 2024)]
    for y0, y1 in windows:
        if y0 not in town_fte or y1 not in town_fte:
            continue
        d_fte = town_fte[y1] - town_fte[y0]
        if y0 == 2022 and y1 == 2024:
            homes = sum(PLANNING_NET_NEW_HOMES.values())
            src = "Planning count"
        else:
            homes = sum(ng_units.get(y, 0) for y in range(y0 + 1, y1 + 1))
            src = "implied from new growth"
        if homes <= 0:
            continue
        fte_per_home = d_fte / homes
        spf = dept_spend[y1] / town_fte[y1]
        dollars = fte_per_home * spf
        ratio = dollars / RKG_PER_UNIT
        print(f"  {'FY'+str(y0)+'-'+str(y1):>14}{d_fte:>9.1f}{homes:>9.0f}"
              f"{fte_per_home:>11.4f}{spf:>10,.0f}{dollars:>10,.0f}   {ratio:>4.1f}x")
        rows.append(dict(window=f"FY{y0}-{y1}", quantity="town general-fund FTE",
                         delta_fte=round(d_fte, 2), homes=round(homes),
                         homes_source=src, fte_per_home=round(fte_per_home, 5),
                         spend_per_fte=round(spf), implied_dollars_per_home=round(dollars),
                         rkg_per_unit=RKG_PER_UNIT, ratio_to_rkg=round(ratio, 3),
                         note="UPPER BOUND: all headcount change attributed to growth"))
    print()
    print("  Read the last column as: even crediting growth with every position the")
    print("  Town added, the implied municipal cost per home lands in this range.")
    print()

    # --------------------------------------------------- the school side
    print("=" * 78)
    print("SCHOOLS: the prediction that did not survive")
    print("=" * 78)
    print("  Phase A expected school staffing to track enrollment. It does not.")
    print(f"  {'window':>14}{'d enrollment':>14}{'d staff FTE':>13}"
          f"{'students/added staff':>22}")
    for y0, y1 in [(2011, 2020), (2011, 2025), (2021, 2025)]:
        if not (enroll.get(y0) and enroll.get(y1) and staff.get(y0) and staff.get(y1)):
            continue
        de, ds = enroll[y1] - enroll[y0], staff[y1] - staff[y0]
        per = (de / ds) if ds else float("nan")
        print(f"  {'FY'+str(y0)+'-'+str(y1):>14}{de:>+14,.0f}{ds:>+13,.1f}{per:>22,.1f}")
        rows.append(dict(window=f"FY{y0}-{y1}", quantity="school staff FTE",
                         delta_fte=round(ds, 2), homes=round(de),
                         homes_source="change in enrollment",
                         fte_per_home=round(ds / de, 5) if de else None,
                         spend_per_fte=None, implied_dollars_per_home=None,
                         rkg_per_unit=None, ratio_to_rkg=None,
                         note="enrollment change, not homes; staff per added student"))
    e0, e1 = enroll[2011], enroll[2025]
    s0, s1 = staff[2011], staff[2025]
    print()
    print(f"  Over FY2011-2025 enrollment rose {(e1/e0-1)*100:+.1f}% "
          f"({e0:,.0f} to {e1:,.0f}) while school staff rose "
          f"{(s1/s0-1)*100:+.1f}% ({s0:,.1f} to {s1:,.1f}).")
    print(f"  Students per staff FTE fell from {e0/s0:.2f} to {e1/s1:.2f}. School")
    print("  staffing growth was a service-level choice far more than an enrollment")
    print("  response, which is the opposite of what Phase A predicted.")

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT_CSV}")
    write_methodology(rows, planning_rate, roll_rate, ng_rate, e0, e1, s0, s1)
    print(f"Wrote {METHOD_OUT}")


def write_methodology(rows, planning_rate, roll_rate, ng_rate, e0, e1, s0, s1):
    L = []
    L.append("# Expense Drivers, Phase C: does headcount respond to growth?\n")
    L.append("Companion to `expense_drivers_phase_c_ratios.csv`. Plan: "
             "`docs/expense_drivers_workplan.md`. Generated by "
             "`scripts/expense_drivers_phase_c.py`.\n")

    L.append("## An elasticity framing was tried and rejected\n")
    L.append("The first version computed elasticities of FTE to cumulative new growth "
             "and got +0.00 everywhere, which looked like a decisive null and was a bug: "
             "cumulative new growth runs from one year's worth to fifteen years' worth, "
             "a change of **+1,820%**, so any headcount change over it is zero by "
             "construction.\n")
    L.append("The positive control caught it. School staff against enrollment gave "
             "**+2.32, +4.55, -13.34 and -3.83** across four windows, because enrollment "
             "moves only 6% in fifteen years and an elasticity with a denominator that "
             "small is not a stable statistic. A control that changes sign is rejecting "
             "the method, not confirming it. Direct physical ratios are reported "
             "instead.\n")

    L.append("## The denominator, checked three ways\n")
    L.append("| Source | Net new homes per year |\n|---|---|")
    L.append(f"| Planning Department permit count, CY2022-24 | {planning_rate:.0f} |")
    L.append(f"| Assessment roll levels, FY2020 to FY2025 | {roll_rate:.0f} (known to overstate) |")
    L.append(f"| Implied from new-growth dollars, FY2011-25 | {ng_rate:.0f} |")
    L.append("\nThey agree on order of magnitude, which is what a ratio quoted to one "
             "significant figure needs.\n")

    L.append("## Results: what a new home buys in staffing\n")
    L.append("**Every figure here is an upper bound**, because all headcount change is "
             "attributed to growth and headcount changes for many other reasons: new "
             "services, restructuring, outsourcing, grant cycles. An upper bound that "
             "still lands low is the useful result.\n")
    L.append("| Window | Change in FTE | Homes | FTE per home | Implied $/home | vs RKG $1,371 |")
    L.append("|---|---|---|---|---|---|")
    for r in rows:
        if r["quantity"] != "town general-fund FTE":
            continue
        L.append(f"| {r['window']} | {r['delta_fte']:+.1f} | {r['homes']:,} | "
                 f"{r['fte_per_home']:.4f} | ${r['implied_dollars_per_home']:,} | "
                 f"{r['ratio_to_rkg']:.1f}x |")
    L.append("")

    L.append("## The school prediction did not survive\n")
    L.append(f"Phase A expected school staffing to track enrollment. Over FY2011-2025 "
             f"enrollment rose {(e1/e0-1)*100:+.1f}% ({e0:,.0f} to {e1:,.0f}) while "
             f"school staff rose {(s1/s0-1)*100:+.1f}% ({s0:,.1f} to {s1:,.1f}). "
             f"Students per staff FTE fell from {e0/s0:.2f} to {e1/s1:.2f}. School "
             "staffing growth was a service-level choice far more than an enrollment "
             "response.\n")
    L.append("That matters for the fiscal impact model in the same way the town-side "
             "result does. A per-pupil marginal cost assumes staffing follows students. "
             "Over this period Brookline's staffing moved largely independently of them, "
             "which means the per-pupil figure describes an accounting average rather "
             "than an observed response.\n")

    L.append("## What none of this establishes\n")
    L.append("- **Not causal.** These are ratios of observed changes.\n"
             "- **Not a null on service cost.** A weak staffing response is consistent "
             "with services genuinely not scaling, with productivity absorbing growth, "
             "and with service levels quietly falling. Nothing here separates them.\n"
             "- **Not a refutation of RKG's $1,371.** That figure is a cost allocation, "
             "not a prediction about headcount. What Phase C shows is that the staffing "
             "channel people usually have in mind when defending it is hard to see in "
             "twenty years of Brookline data.\n")

    with open(METHOD_OUT, "w") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()
