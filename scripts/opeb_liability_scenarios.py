"""
Retiree health (OPEB) liability under different ways of forecasting it, for the explainer in
notes/retiree_health_liability.md (Ben, 2026-10-14). Not part of the site build.

The roll-forward is the model's (expense_driver_forecast.py): each year
    total liability' = liability x 1.069 + service cost - benefits paid  [+ loss term]
    trust'           = min(trust x 1.069 + deposit, liability')
    deposit          = min(planned, what is still unfunded)
Only the deposit touches the budget, so a scenario's room is the base case's room plus the
difference in deposits. Everything else in the forecast is the base case.

Run from `scripts/`:  python3 opeb_liability_scenarios.py
"""

import csv
from pathlib import Path

import expense_driver_forecast as edf

OUT = Path(__file__).parent.parent / "output" / "opeb_liability_scenarios.csv"
AUDIT = (301_751_680, 100_275_701, 8_509_485, 12_388_461)   # FY2024 audit
DEPOSITS_HIST = {2025: 5_431_980, 2026: 4_931_980, 2027: 4_931_980}
BUDGET_GROWTH_HIST = {2025: 0.101, 2026: 0.089, 2027: 0.114}   # group health budget, FY2025-27
R = edf.OPEB_RATE


def premium(y):
    return {2028: 0.12, 2029: 0.12}.get(y, 0.08)


def scenario(growth, loss_term):
    """growth(y): yearly growth in retiree cost per person. loss_term: add liability x (growth -
    actuary's trend) each year, as an actuary would on finding costs beat its assumption."""
    tol, a, sc, ben = AUDIT
    data = edf.load()
    base = edf.run(edf.BASE, data, None)
    tsch = data[0]
    plan = lambda y: float(tsch[min(y, 2031)][("benefits_detail", "retiree_group_health_opeb")])
    rows, paid_off = [], None
    for y in range(2025, 2041):
        g = growth(y)
        sc *= 1 + g
        ben *= (1 + g) * (1 + edf.RETIREE_GROWTH)
        new_tol = tol * (1 + R) + sc - ben + (tol * (g - edf.opeb_trend(y)) if loss_term else 0.0)
        if y <= 2027:
            dep = DEPOSITS_HIST[y]
        else:
            dep = min(plan(y), max(new_tol - a * (1 + R), 0.0))
        tol, a = new_tol, min(a * (1 + R) + dep, new_tol)
        if paid_off is None and tol - a < 1:
            paid_off = y
        if y >= 2027:
            room = float(base.loc[y, "surplus_deficit"]) + float(base.loc[y, "opeb"]) - dep
            rows.append(dict(year=y, total_liability=tol, trust=a, net_liability=tol - a,
                             benefits_paid=ben, deposit=dep, room=room))
    return rows, paid_off


SCENARIOS = {
    "A. Actuary's trend (the base case now)": (edf.opeb_trend, False),
    "B. Actuary's trend + 1 point a year": (lambda y: edf.opeb_trend(y) + 0.01, True),
    "C. Actuary's trend + 2 points a year": (lambda y: edf.opeb_trend(y) + 0.02, True),
    "D. Our premium assumption (12%, then 8%), actuary catches up each year":
        (lambda y: BUDGET_GROWTH_HIST.get(y, premium(y)), True),
}


def main():
    out = []
    print(f"{'scenario':76s} paid off  net FY27  FY31   FY35   FY40 | room FY35  FY40")
    for name, (g, loss) in SCENARIOS.items():
        rows, paid = scenario(g, loss)
        by = {r["year"]: r for r in rows}
        print(f"{name:76s} {str(paid or 'after 2040'):9s}"
              + " ".join(f"{by[y]['net_liability']/1e6:6.0f}" for y in (2027, 2031, 2035, 2040))
              + f" | {by[2035]['room']/1e6:6.1f} {by[2040]['room']/1e6:6.1f}")
        for r in rows:
            out.append(dict(scenario=name, paid_off=paid or "after 2040",
                            **{k: (round(v) if isinstance(v, float) else v) for k, v in r.items()}))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
