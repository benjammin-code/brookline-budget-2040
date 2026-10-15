"""
When does a new home cover the cost of the Town services and schooling it adds?

Reference document §3c support, rebuilt 2026-09-29 on the driver forecast's costs
(expense_driver_forecast.py) instead of RKG's average-cost figures, and extended in
time: a home's tax is held to the levy limit's 2.5% a year, while the cost of a
student and of Town services grows with pay and health premiums. So a home that
covers its costs when it opens can stop covering them later.

Annual net for one home in fiscal year y (all nominal dollars):

    tax(y)      = assessed value x residential tax rate x 1.025^(y - 2027)
    town(y)     = town services per home, FY2027, grown with Town pay
    school(y)   = children per home x cost of one added student in year y
    net(y)      = tax(y) - town(y) - school(y)

    breakeven children per home (y) = (tax(y) - town(y)) / cost per added student (y)

Key assumptions (each is varied in the sensitivity table):
  TAX_RATE              FY2026 residential rate, $10.24 per $1,000 (the FY2027 rate is set
                        in December 2026). Before the residential exemption, which lowers
                        the bill for owner-occupied homes; see §3e.
  TAX_GROWTH            2.5%/yr: an existing home's share of a levy that grows 2.5% plus
                        new growth, with new growth paying its own way. The trend-case
                        measure for all existing property is 2.31%/yr
                        (existing_vs_new_property_tax_fy26_40_scenarios.csv).
  TOWN_COST_FY25        $660/home/yr for Town departments (cross_town_marginal_cost.py,
                        350 towns, range $230 to $1,109), plus benefits at RKG's ratio
                        ($262 per $1,109), priced to FY2027 at 3% pay growth.
  STUDENT_COST          $16,236 in FY2027 (marginal_cost_per_student.csv), growing on the
                        driver model's own path to $21,174 (FY2034) and $26,663 (FY2040).
  Children per home     RKG schedule 0.00 / 0.25 / 0.35 by bedrooms; model average 0.244;
                        Brookline's ten recent developments 0.03 to 0.56 (mean ~0.21).

Run from `scripts/`:  python3 housing_unit_breakeven.py
"""

import csv
from pathlib import Path

OUT = Path(__file__).parent.parent / "output"
OUT_CURVE = OUT / "housing_unit_breakeven_curve.csv"
OUT_TYPES = OUT / "housing_unit_breakeven_by_type.csv"
OUT_SENS = OUT / "housing_unit_breakeven_sensitivity.csv"
OUT_METHOD = OUT / "housing_unit_breakeven_methodology.md"

Y0, Y1 = 2027, 2040
TAX_RATE = 0.01024
TAX_GROWTH = 0.025
import cost_assumptions as ca
import cost_assumptions as _ca
import new_growth_scenario_forecast as _ngs
PAY = ca.PAY
TOWN_COST_FY25 = ca.TOWN_COST_PER_HOME_FY25
TOWN_BENEFIT_LOADING = ca.TOWN_BENEFIT_LOADING
STUDENT_COST = ca.STUDENT_COST                   # driver model, nominal
AVERAGE_STUDENT_COST_FY24 = ca.AVERAGE_STUDENT_COST_FY24
MODEL_CHILDREN = round(_ca.STUDENTS_PER_HOME, 3)   # the forecast's children per new home
OBSERVED_RANGE = (0.03, 0.56)
OBSERVED_MEAN = 0.21

# Assessed value per unit, FY2025 roll (§3b), plus the new-construction figures
# the growth model uses.
UNIT_TYPES = [
    ("Condominium (FY2025 roll average)", 1_175_950),
    ("New home, mean of new construction", 794_300),
    ("Apartment, 4-8 units", 672_850),
    ("Apartment, 9+ units", 434_283),
    ("New home, apartments and condominiums (forecast average)", int(_ngs.RES_VALUE_PER_UNIT)),
]


def student_cost(y, base=STUDENT_COST, growth=None):
    """Driver-model path (log-linear between its three published points), or a
    constant growth rate from FY2027 when `growth` is given."""
    if growth is not None:
        return base[2027] * (1 + growth) ** (y - Y0)
    pts = sorted(base)
    for a, b in zip(pts, pts[1:]):
        if a <= y <= b:
            return base[a] * (base[b] / base[a]) ** ((y - a) / (b - a))
    a, b = pts[-2], pts[-1]
    return base[b] * (base[b] / base[a]) ** ((y - b) / (b - a))


def town_cost(y, per_home_fy25=TOWN_COST_FY25, pay=PAY):
    return per_home_fy25 * (1 + TOWN_BENEFIT_LOADING) * (1 + pay) ** (y - 2025)


def tax(value, y, rate=TAX_RATE, growth=TAX_GROWTH):
    return value * rate * (1 + growth) ** (y - Y0)


def breakeven(value, y, **k):
    sc = k.get("student_fn", student_cost)(y)
    return (tax(value, y, k.get("rate", TAX_RATE), k.get("tax_growth", TAX_GROWTH))
            - town_cost(y, k.get("town_fy25", TOWN_COST_FY25))) / sc


def crossover_year(value, children, horizon=2060, **k):
    """First fiscal year in which the home's net turns negative (None if never
    by the horizon; Y0 if already negative when it opens)."""
    for y in range(Y0, horizon + 1):
        if breakeven(value, y, **k) < children:
            return y
    return None


def main():
    # --- control: the growth formula reproduces the three published points
    for y, v in STUDENT_COST.items():
        assert abs(student_cost(y) - v) < 0.5, "student cost path does not hit its own points"
    # --- control: breakeven x cost per student + town cost == tax, at a sample value
    v = 600_000
    assert abs(breakeven(v, 2033) * student_cost(2033) + town_cost(2033) - tax(v, 2033)) < 1e-6

    # curve for the chart
    rows = []
    for value in range(200_000, 1_600_001, 25_000):
        rows.append(dict(assessed_value=value,
                         breakeven_children_fy2027=round(breakeven(value, Y0), 4),
                         breakeven_children_fy2034=round(breakeven(value, 2034), 4),
                         breakeven_children_fy2040=round(breakeven(value, Y1), 4),
                         breakeven_children_fy2027_average_cost=round(
                             breakeven(value, Y0, student_fn=lambda y: AVERAGE_STUDENT_COST_FY24 * 1.03 ** (y - 2024)), 4)))
    with open(OUT_CURVE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # value at which a home with the model's average children just breaks even
    def value_needed(children, y):
        return (children * student_cost(y) + town_cost(y)) / (TAX_RATE * (1 + TAX_GROWTH) ** (y - Y0))

    types = []
    print(f"Costs FY{Y0}: town services ${town_cost(Y0):,.0f}/home, added student ${student_cost(Y0):,.0f}; "
          f"FY{Y1}: ${town_cost(Y1):,.0f} and ${student_cost(Y1):,.0f}")
    print(f"Value a home needs to cover {MODEL_CHILDREN} children: FY{Y0} ${value_needed(MODEL_CHILDREN, Y0):,.0f}, "
          f"FY{Y1} (in FY{Y1} tax terms) ${value_needed(MODEL_CHILDREN, Y1):,.0f}")
    for name, value in UNIT_TYPES:
        b0, b1 = breakeven(value, Y0), breakeven(value, Y1)
        net0 = tax(value, Y0) - town_cost(Y0) - MODEL_CHILDREN * student_cost(Y0)
        net1 = tax(value, Y1) - town_cost(Y1) - MODEL_CHILDREN * student_cost(Y1)
        cx = crossover_year(value, MODEL_CHILDREN)
        types.append(dict(unit_type=name, assessed_value=value, tax_fy2027=round(tax(value, Y0)),
                          breakeven_children_fy2027=round(b0, 3), breakeven_children_fy2040=round(b1, 3),
                          net_fy2027_at_0_244_children=round(net0), net_fy2040_at_0_244_children=round(net1),
                          first_year_negative_at_0_244_children=cx if cx else "after 2060"))
        print(f"  {name:42s} ${value:>9,.0f}  tax ${tax(value, Y0):>6,.0f}  breakeven {b0:.2f} -> {b1:.2f}  "
              f"net at 0.244: ${net0:>7,.0f} -> ${net1:>7,.0f}  negative from {cx or 'after 2060'}")
    with open(OUT_TYPES, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(types[0]))
        w.writeheader()
        w.writerows(types)

    # sensitivity of the breakeven, for two reference homes
    cases = [
        ("Base case", {}),
        ("Student cost at the full average, $26,683 (FY2024) grown 3%/yr",
         dict(student_fn=lambda y: AVERAGE_STUDENT_COST_FY24 * 1.03 ** (y - 2024))),
        ("Student cost grows 5%/yr (school pay at the School Department's forecast)",
         dict(student_fn=lambda y: student_cost(y, growth=0.05))),
        ("Student cost grows 3%/yr (pay and premiums at target)",
         dict(student_fn=lambda y: student_cost(y, growth=0.03))),
        ("Town services $1,109/home (RKG)", dict(town_fy25=1_109.0)),
        ("Town services $230/home", dict(town_fy25=230.0)),
        ("Home's tax grows 2.31%/yr (trend, all existing property)", dict(tax_growth=0.0231)),
        ("Tax rate 10% lower (e.g. residential exemption)", dict(rate=TAX_RATE * 0.9)),
    ]
    sens = []
    for label, k in cases:
        row = dict(case=label)
        for name, value in (("apartment_9plus", 434_283), ("condominium", 1_175_950)):
            row[f"{name}_breakeven_fy2027"] = round(breakeven(value, Y0, **k), 3)
            row[f"{name}_breakeven_fy2040"] = round(breakeven(value, Y1, **k), 3)
        sens.append(row)
    with open(OUT_SENS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sens[0]))
        w.writeheader()
        w.writerows(sens)
    print("\nSensitivity (breakeven children per home, FY2027 -> FY2040):")
    for r in sens:
        print(f"  {r['case']:75s} apt 9+ {r['apartment_9plus_breakeven_fy2027']:.2f} -> "
              f"{r['apartment_9plus_breakeven_fy2040']:.2f}   condo {r['condominium_breakeven_fy2027']:.2f} -> "
              f"{r['condominium_breakeven_fy2040']:.2f}")

    OUT_METHOD.write_text(__doc__.strip() + f"""

## Outputs

- `{OUT_CURVE.name}`: breakeven children per home by assessed value, FY2027, FY2034, FY2040,
  and FY2027 at the full average cost per pupil.
- `{OUT_TYPES.name}`: the same test for five reference homes, with the net at the model's
  0.244 children per home and the first year that net turns negative.
- `{OUT_SENS.name}`: how the breakeven moves when each assumption changes.

## Controls (asserted in the script)

- The student-cost path passes through the driver model's three published points.
- breakeven x cost per student + town cost equals the home's tax.

## Limits

- One home in isolation. It does not add up to the town-wide forecast, where new growth
  also enlarges the levy base and changes the tax rate (see README item 6).
- The marginal student cost assumes an added student is staffed at the district's current
  ratio for the enrollment-linked two-thirds of the budget. A child joining a grade with
  room costs less; one that forces a new section costs a teacher.
- Before any deduction for the tax the parcel already paid (§3a).
""")
    print(f"\nwrote {OUT_CURVE.name}, {OUT_TYPES.name}, {OUT_SENS.name}, {OUT_METHOD.name}")


if __name__ == "__main__":
    main()
