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

## Outputs

- `housing_unit_breakeven_curve.csv`: breakeven children per home by assessed value, FY2027, FY2034, FY2040,
  and FY2027 at the full average cost per pupil.
- `housing_unit_breakeven_by_type.csv`: the same test for five reference homes, with the net at the model's
  0.244 children per home and the first year that net turns negative.
- `housing_unit_breakeven_sensitivity.csv`: how the breakeven moves when each assumption changes.

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
