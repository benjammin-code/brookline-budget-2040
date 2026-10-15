# School peer comparison: sources, definitions, caveats

Output: `output/school_peer_comparison.csv` (one row per district per school year; 22 district
entities x 3 years = 66 rows). Built by `scripts/school_peer_comparison.py` from raw files in
`data/dese_peers/` (`python3 scripts/school_peer_comparison.py --fetch` re-downloads them).
Built 2026-09-29.

## Years

| Column value | Meaning | What is populated |
|---|---|---|
| SY2014-15 / FY2015 | ten-years-earlier comparison | everything except SWD out-of-district % (RADAR starts 2020) |
| SY2024-25 / FY2025 | latest complete year | everything (Weston FY2025 average salary missing in source) |
| SY2025-26 / FY2026 | latest enrollment/staffing | enrollment, needs, staffing only; DESE has not yet published FY2026 finance or RADAR data |

Every E2C dataset's `sy` field is the spring year (sy=2025 is SY2024-25 = FY2025). Checked against
known values: Brookline sy=2025 enrollment 7,023, teacher FTE 544.1, total staff FTE 1,249.4 match
the project's Profiles-scraped `school_enrollment_staffing_fy05_25.csv`. Newton FY2025 total staff
(2,150.7) and teacher FTE (1,108.1) were also spot-checked against the live Profiles pages.

## Districts and org codes

Codes are taken from the E2C enrollment dataset's own `org_code`/`org_name` pairs (org_type =
District). Brookline 00460000 confirmed.

Brookline 00460000, Newton 02070000, Lexington 01550000, Wellesley 03170000, Needham 01990000,
Cambridge 00490000, Arlington 00100000, Belmont 00260000, Winchester 03440000, Concord 00670000
(PK-8), Concord-Carlisle 06400000 (9-12 regional), Wayland 03150000, Weston 03300000,
Somerville 02740000, Watertown 03140000, Milton 01890000, Natick 01980000, Sudbury 02880000
(PK-8), Lincoln-Sudbury 06950000 (9-12 regional), Andover 00090000, Hingham 01310000,
Westwood 03350000.

Concord, Sudbury and their regional high schools are kept as separate rows and **excluded from
the rank columns**, because PK-8 and 9-12 districts have structurally different staffing and cost
profiles, and combining them would pull in Carlisle and Lincoln students. Ranks are among the 18
PK-12 districts.

## Sources (all Massachusetts DESE)

| Metric(s) | Source | Dataset / report |
|---|---|---|
| Enrollment, % SWD, % high needs, % EL, % low income / econ. disadvantaged | E2C Hub | *Enrollment: Grade, Race/Ethnicity, Gender, and Selected Populations* (`t8td-gens`); same data as Profiles Enrollment by Selected Population |
| Total staff FTE, paraprofessional, administrator, instructional staff, SPED-related staff, "teacher - support content instruction" FTE | E2C Hub | *Staffing: Race/Ethnicity and Gender* (`j5ue-xkfn`); `jobclass = All` row is total; same data as Profiles "Staffing Data by Race/Ethnicity and Gender" |
| Teacher FTE, DESE's own students per teacher | E2C Hub | *Elementary and Secondary Teacher Data* (`4684-cw3t`), `subject = All Teachers`; same as Profiles Teacher Data report |
| In-district and total per-pupil expenditure, average teacher salary (FY2025), in/out-of-district FTE pupils | E2C Hub | *District Expenditures by Spending Category* (`er3w-dyti`); same as School Finance Dashboard / Profiles ppx |
| Out-of-district tuition dollars and share of total expenditure | E2C Hub | *District Expenditures by Function Code* (`cnfs-edqq`), function categories OODD (out-of-district expenditure), TTPP (total), 9100-9400 (tuition lines) |
| % of students with disabilities placed out of district; SPED FTE per 100 in-district SWD | E2C Hub | *Special Education Program Characteristics and Student Demographics* (`n62c-bx65`, RADAR); 2020+ only |
| Average teacher salary FY2015 | DESE Profiles | `statereport/teachersalaries.aspx`, year 2014-15 (raw HTML and parsed CSV saved). The E2C finance dataset has salary only from FY2024 on for most districts. Brookline FY2024 in both sources is $122,329, so they are the same series |

Raw files in `data/dese_peers/`: `enrollment_selectedpops_t8td-gens.csv`,
`staffing_by_jobclass_j5ue-xkfn.csv`, `teacher_data_4684-cw3t.csv`,
`district_expenditures_er3w-dyti.csv` (FY2015, FY2024, FY2025), `district_exp_by_function_cnfs-edqq.csv`,
`sped_program_characteristics_n62c-bx65.csv`, `teacher_salaries_fy2015_profiles_statereport.csv`
(+ `_raw.html`).

## Definitions (from the dataset documentation, not column names)

- **total_enrollment**: October 1 headcount, all grades including PK and special education beyond
  grade 12.
- **total_staff_fte**: FTE of all staff reported to DESE's EPIMS staffing collection as of October 1
  (`jobclass = All`). This covers the job classifications DESE lists for the dataset: administrators,
  instructional staff, instructional support, SPED shared and related staff, medical/health,
  office/clerical/administrative support, and paraprofessionals. It does **not** include custodial,
  food service or transportation workers (no such classifications exist in the list), so it is
  "educational staff", not every school-department employee.
- **teacher_fte**: the Teacher Data report's "All Teachers" FTE. Reconciled against the staffing
  file: it equals Teacher + Co-teacher + "Teacher - support content instruction" FTE (column
  `teacher_fte_from_jobclass`; matches within 0.1 FTE in 64 of 66 rows, max gap 0.5). Long-term substitutes and
  instructional coaches are not counted as teachers.
- **instructional_staff_fte**: the whole "Instructional Staff" category (teachers, co-teachers,
  support-content teachers, instructional coaches, long-term subs). Added because it is less
  sensitive to how a district splits these codes (see caveat 1).
- **students_per_teacher / students_per_total_staff / students_per_instructional_staff**:
  total_enrollment divided by the FTE. `dese_students_per_teacher` is DESE's own published ratio,
  which matches.
- **staff_per_100_students**: the inverse of students_per_total_staff x 100, used for the needs fit.
- **swd_pct**: students with IEPs as % of enrollment. **el_pct**: English learners.
  **high_needs_pct**: students who are SWD, EL/former EL, or low income (unduplicated).
- **low_income_or_ecd_pct**: DESE's published poverty measure for that year. FY2015 is
  *Economically Disadvantaged* (used 2015-2021); FY2025/26 is the *Low Income* measure in use since
  2022. `low_income_measure` names which. Per the dataset documentation these are different measures;
  **do not read the 2015-to-2025 change in this column, or in high_needs_pct which contains it, as a
  real change in poverty**.
- **in_district_ppx**: total in-district expenditure / in-district FTE pupils. **total_ppx**:
  in-district plus out-of-district expenditure (tuition to other districts, charters, collaboratives,
  private SPED schools) / total FTE pupils. Both come from the End-of-Year Pupil and Financial Report
  and include spending by the municipality on behalf of schools (e.g., employee health insurance and
  retirement, the "Insurance, Retirement Programs and Other" line). Nominal dollars.
- **avg_teacher_salary**: DESE's average teacher salary (teacher salary totals / teacher FTE). Nominal.
- **out_of_district_pupil_pct**: out-of-district FTE pupils / total FTE pupils. Includes all
  tuitioned-out pupils (SPED placements, school choice, charter, vocational), not only SPED.
- **out_of_district_tuition_pct_of_total_exp**: function category OODD / TTPP. The dominant line
  for most of these districts is 9300 "Tuition to Non-Public Schools" (private SPED day/residential),
  reported separately as `private_and_collab_tuition_dollars` (9200 + 9300 + 9400).
- **swd_out_of_district_pct**: RADAR, share of all SWD (in and out of district) placed out of
  district. FY2020+ only.
- **sped_fte_per_100_in_district_swd**: RADAR, SPED teachers + paraprofessionals + service + support
  FTE per 100 in-district SWD.
- **staff_per_100_predicted_from_high_needs / residual**: simple OLS, per year, of
  staff_per_100_students on high_needs_pct across the 18 PK-12 districts. Illustrative only; see
  caveat 4.

## Caveats

1. **Teacher FTE is coding-sensitive, so Brookline's FY2025 12.9 students per teacher is not a
   like-for-like comparison.** DESE's teacher count includes the "Teacher - support content
   instruction" code (interventionists and similar). In FY2025 Brookline reported 0.0 FTE in that code
   and 41.8 FTE as instructional coaches; Newton reported 185, Lexington 146, Cambridge 190, Andover
   123 in it. In FY2026 Brookline reported 80.9 support-content FTE and instructional coaches fell to
   6.5, and its teacher FTE jumped from 544.1 to 630.7 with total staff almost unchanged (1,249 to
   1,264). Brookline's teacher-ratio rank swings from 17th of 18 (FY2025) to 9th of 18 (FY2026) on
   that recoding alone. **Total staff FTE is the robust comparison**; instructional_staff_fte is a
   middle option.
2. Other category shifts also reflect recoding: Brookline's "Special Education Related Staff" went
   99.3 (FY2025) to 51.8 (FY2026). Category-level comparisons across districts should be treated as
   indicative.
3. **High needs and low income are not comparable across the ten-year gap** (definition change in
   2022, see above). SWD % and EL % are comparable.
4. The needs fit is weak. High-needs % explains about 29% of the variation in staff per 100 students
   in FY2015 and about 8% in FY2025 across these 18 districts (r = 0.54 and 0.28). Per-pupil
   spending explains far more (r = 0.89 and 0.81): wealthy districts with modest needs (Wellesley,
   Concord, Weston) staff as richly as higher-needs ones. Somerville is a large negative outlier
   (high needs, comparatively lean staffing and very few paraprofessionals); excluding it raises
   the FY2025 correlation to 0.48.
5. Per-pupil and salary figures are nominal. No inflation adjustment is applied. The project's
   `price_indices_annual.csv` can be used if needed.
6. FY2026 finance data (per-pupil spending, salary, tuition) is not yet published. Weston's FY2025
   average salary is missing in the source (FY2024 was $127,449).
7. Staffing is an October 1 snapshot; mid-year hires and grant-funded summer staff are not captured.
8. `out_of_district_pupil_pct` mixes SPED placements with school choice and charter pupils; for
   SPED specifically use `swd_out_of_district_pct` (FY2025 only) or the tuition-dollar columns.
   Charter tuition assessed through the Cherry Sheet does not flow through district expenditure, so
   it is mostly absent from the tuition columns.

## Gaps

- SWD out-of-district placement % for FY2015 (RADAR begins 2020). Out-of-district FTE pupils and
  out-of-district tuition dollars are used for the ten-year comparison instead.
- Combined K-12 figures for Concord+Concord-Carlisle and Sudbury+Lincoln-Sudbury are not built
  (the regionals also serve Carlisle and Lincoln).
- Non-EPIMS staff (custodial, food service, transportation) are not in any total-staff figure.
