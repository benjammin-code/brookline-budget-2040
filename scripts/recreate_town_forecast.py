"""
Recreate the Town's own FY2027-31 Long Range Financial Plan (January 2026,
before the May 2026 override) with the driver model, and bridge from the
Town's FY2031 result to this project's.

The Town's plan shows spending by line but not the assumptions behind each
line. Running the driver model with the Town's revenue and solving for the pay
and staffing assumptions that reproduce the Town's spending lines shows what
the plan implicitly assumes. Each solve is a bisection on one dial with every
other dial at the base case.

Run from `scripts/`:  python3 recreate_town_forecast.py
"""

import csv
from pathlib import Path

import pandas as pd

import expense_driver_forecast as edf

OUT = Path(__file__).parent.parent / "output"
OUT_CSV = OUT / "recreate_town_forecast_fy31.csv"
METHOD = OUT / "recreate_town_forecast_methodology.md"


def bisect(f, lo, hi, target, iters=60):
    flo = f(lo) - target
    for _ in range(iters):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    data = edf.load()
    tsch = data[0]
    T = lambda cat, sub, y: float(tsch[y][(cat, sub)])
    Y = 2031
    base = edf.run(edf.BASE, data, None)

    def line(df, y, which):
        if which == "dept":
            return df.loc[y, ["departmental_base", "departmental_growth"]].sum()
        if which == "schools":
            return df.loc[y, "schools"]
        if which == "benefits":
            return df.loc[y, ["group_health", "growth_staff_benefits", "pensions", "opeb",
                              "other_benefits"]].sum()

    town = dict(dept=T("expenditure", "departmental_town", Y),
                schools=T("expenditure", "schools", Y),
                benefits=T("expenditure", "nondept_benefits", Y))

    # --- solves (each with everything else at base)
    dept_adj = bisect(lambda x: line(edf.run(dict(edf.BASE, dept_pay_adj=x), data, None), Y, "dept"),
                      -0.05, 0.05, town["dept"])
    sch_drift = bisect(lambda x: line(edf.run(dict(edf.BASE, school_pay_drift=x), data, None), Y, "schools"),
                       -0.05, 0.10, town["schools"])
    sch_staff = bisect(lambda x: line(edf.run(dict(edf.BASE, school_staff_growth=x), data, None), Y, "schools"),
                       -0.05, 0.10, town["schools"])
    base_staff = base.loc[Y, "school_staff"]
    staff_run = edf.run(dict(edf.BASE, school_staff_growth=sch_staff), data, None)

    base_pay_sch = edf.BASE["pay"] + edf.BASE["school_pay_drift"]
    base_pay_dep = edf.BASE["pay"]
    print("=" * 78)
    print(f"WHAT THE TOWN'S FY2027-31 PLAN IMPLIES (solved to FY{Y})")
    print("=" * 78)
    print(f"  Town departments ${town['dept']/1e6:.1f}M: pay growth {base_pay_dep+dept_adj:.2%}/yr "
          f"(Public Safety {base_pay_dep+dept_adj+edf.BASE['pay_ps_premium']:.2%}) with FTE flat; "
          f"base case {base_pay_dep:.2%} / {base_pay_dep+edf.BASE['pay_ps_premium']:.2%}")
    print(f"  Schools ${town['schools']/1e6:.1f}M, either:")
    print(f"     school pay growth {base_pay_sch+sch_drift:.2%}/yr with staff held at today's level "
          f"(base {base_pay_sch:.2%}), or")
    print(f"     staff growing {sch_staff:.2%}/yr at base pay: {staff_run.loc[Y,'school_staff']:,.0f} FTE in "
          f"FY{Y} vs {base_staff:,.0f} held, while enrollment falls to "
          f"{base.loc[Y,'enrollment']:,.0f}")
    print(f"  Benefits: Town ${town['benefits']/1e6:.1f}M vs driver ${line(base, Y, 'benefits')/1e6:.1f}M "
          "(Town schedules used directly; health premiums close)")
    print()

    # --- bridge FY2031: Town balance -> driver base (with override)
    r = pd.read_csv(OUT / "baseline_revenue_forecast_fy26_40.csv")
    tc = r[r.scenario == "trend_corrected"].set_index("fiscal_year").loc[Y]
    bc = pd.read_csv(OUT / "base_case_decomposition_fy26_40.csv")
    ov = bc[(bc.run == "as_legislated") & (bc.scenario == "trend_corrected")].set_index("fiscal_year").loc[Y, "may_2026_override_value"]
    town_rev = T("revenue", "total_revenue", Y) - T("revenue", "debt_exclusion", Y)
    town_exp = T("expenditure", "total_expenditure", Y) - T("revenue", "debt_exclusion", Y)
    town_bal = town_rev - town_exp
    items = [
        ("Town's plan, FY2031 balance", town_bal),
        ("May 2026 override (after the plan)", ov),
        ("Property tax: trend new growth + Chestnut Hill",
         (tc.property_tax_operating - ov) - (T("revenue", "property_taxes", Y) - T("revenue", "debt_exclusion", Y))),
        ("State aid: trend vs Town", tc.state_aid - T("revenue", "state_aid", Y)),
        ("Local receipts (budgeted): trend vs Town", tc.local_receipts - T("revenue", "local_receipts", Y)),
        ("Free cash: cash cycle vs Town", tc.free_cash - T("revenue", "free_cash", Y)),
        ("Other available funds", tc.other_available_funds - T("revenue", "other_available_funds", Y)),
        ("Schools: driver vs Town", town["schools"] - line(base, Y, "schools")),
        ("Town departments: driver vs Town", town["dept"] - line(base, Y, "dept")),
        ("Benefits: driver vs Town", town["benefits"] - line(base, Y, "benefits")),
        ("Capital, reserves, other: project vs Town",
         (T("expenditure", "nondept_general", Y) + T("expenditure", "nondept_reserve_fund", Y)
          + T("expenditure", "special_appropriations_cip", Y) + T("expenditure", "non_appropriated", Y))
         - base.loc[Y, "other_nondept"]),
        ("Within-levy debt", (T("expenditure", "nondept_debt_service", Y) - T("revenue", "debt_exclusion", Y))
         - base.loc[Y, "debt_within_levy"]),
    ]
    running = 0.0
    print("=" * 78)
    print(f"BRIDGE, FY{Y}: Town plan balance to this project's base case")
    print("=" * 78)
    rows = []
    for k, v in items:
        running += v
        print(f"  {k:48s} {v/1e6:+8.1f}M   running {running/1e6:+8.1f}M")
        rows.append(dict(item=k, amount=round(v), running_total=round(running)))
    target = base.loc[Y, "surplus_deficit"]
    resid = target - running
    print(f"  {'Other / rounding':48s} {resid/1e6:+8.1f}M")
    print(f"  {'This project, FY2031 balance with override':48s} {target/1e6:+8.1f}M")
    rows.append(dict(item="Other / rounding", amount=round(resid), running_total=round(target)))
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT_CSV.name}")
    return dict(dept_pay=base_pay_dep + dept_adj, sch_pay=base_pay_sch + sch_drift,
                sch_staff=sch_staff, staff31=staff_run.loc[Y, "school_staff"], rows=rows)


if __name__ == "__main__":
    main()
