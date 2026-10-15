# New homes and school seats: method and sources (2026-10-06)

Supports docs/new_growth.md ("New homes and Brookline's budget"). Figures from
scripts/new_growth_page_data.js (section 3) and the dashboard engine with `fill_capacity`.

## School capacity
- K-8 FY2027 projected enrollment, classes and guidelines by school and grade: Advisory
  Committee Schools Subcommittee FY27 write-up (draft 2026-04-28, data/psb_budget/), tables
  "based on data from October 27, 2025". Seats at guideline = sum over grades of
  guideline x classes; open seats = seats minus projected students (no grade exceeds its
  guideline, so no negatives were netted). Totals: 4,513 students, 233 classes, 5,458 seats,
  945 open (83% full). Driscoll's guideline (24 in grades 3-8) reflects building design;
  Pierce's reflects Fisher Hill classroom sizes (both per the write-up's footnotes).
- High school: expansion completed 2022; the architects (Rawn, via CNU's project page)
  describe capacity rising from about 1,500 to about 2,700. FY2026 enrollment 2,147 (same
  write-up). The architects' figure is a design statement, not a staffed capacity.
- Enrollment path: NESDEC by grade, scaled to the September 2026 count (6,889) and extended
  to FY2040 (expense_driver_forecast.enrollment_path); base-case enrollment includes the
  approved Chestnut Hill homes' students (about 33 by FY2040), so FY2040 is 6,002.

## Capacity level and homes that fit
- Capacity level = FY2027 enrollment (6,889), Ben's choice 2026-10-06 (the alternative was
  the FY2019 peak of 7,855). This ignores the 945 K-8 seats already open, so it is the
  conservative reading.
- Homes beyond trend that fit in year y = (6,889 - base enrollment in y) / 0.2442 students
  per home. Trend homes (about 166 a year) are inside NESDEC's grade ratios.

## Cost of an added student
- Staffed (base case): $16,443 in FY2027 = staff at one position per 8.5 students ($12,092)
  + supplies and transport ($2,477) + health insurance and payroll ($1,874).
- Filling open seats: $2,477, the enrollment-linked non-personnel share (17% of the school
  budget x 67% variable share, per student). Includes transport and tuitions at the average
  rate; special education placements can cost far more for an individual student.

## Model option
- `fill_capacity` (expense_driver_forecast.py and docs/_build/dashboard_engine.js, keep mode
  only): school staff = FY2027 staff + max(total enrollment - FY2027 enrollment, 0) / FY2027
  ratio, on the variable share. Tested in test_dashboard_engine.js (96/96 within $5).
- Results (FY2040 change vs base, including planning and permitting staff for growth above
  trend, added 2026-10-07): +2,916 homes: +$3.6M staffed, +$21.6M filling seats;
  +6,978: +$8.6M / +$30.7M; +13,466: +$16.6M / +$38.6M. Before that cost: +$5.2M / +$23.2M,
  +$12.5M / +$34.6M, +$24.3M / +$46.4M.

## Town services
- Public safety FTE 339.3 (FY2011) to 334.3 (FY2025), Town Financial Plans
  (output/expense_drivers_fte_panel_fy04_27.csv); homes added about 1,640 (reference doc 2b).
- Fire budgeted 161 since FY2010; peer staffing per resident: output/public_safety_staffing_methodology.md.
- Caveat found, not resolved: total Town General Fund FTE differs between the FY2004-20
  category file and the FY2021-27 annual file (e.g. FY2026 675.6 vs 717.4), so total Town
  staffing is not cited on the page; only public safety, which both series agree on.

## Births
- MA DPH resident births by municipality (data/MA-DPH-2020/2023 reports): about 690 a year
  2008-13, 422 in 2023.
