# What's driving Brookline school budget growth — a 17-20 year view

Companion to `output/school_enrollment_staffing_fy05_25.csv`,
`output/school_spending_by_category_fy09_25.csv`,
`output/school_teacher_salary_fy09_25.csv`, and
`output/school_staff_by_role_fy09_25.csv`. Sourced from DESE's own
School and District Profiles site and the Education-to-Career Research
and Data Hub's Socrata API — full methodology and every gap/caveat found
along the way is in `data/SOURCES.md`, "School enrollment & staffing
history (DESE)". Built 2026-09-02.

## The simple version

Education spending grew from $60.4M to $146.4M, FY2005-2025 (2.4x
nominal, 4.5%/yr). Three things explain most of that growth, and they
are not the same story at different points in the window:

1. **FY2005-2019: real physical growth.** Enrollment rose 31%, from
   5,984 to a peak of 7,855 students. The Town built and expanded
   schools (Pierce, Driscoll, the "expand in place" program that added
   55 classrooms) to keep up, adding staff roughly in proportion — total
   staff FTE grew even faster than enrollment over this window (+42%
   FY2008-2020 vs. enrollment's +26% over the same years). This is a
   real, physical driver: more kids, more sections, more buildings, more
   staff, more debt exclusions for construction.

2. **FY2020-2025: enrollment fell, but the cost drivers that don't move
   with enrollment kept compounding anyway.** Enrollment dropped 11%
   post-COVID. Total staff FTE fell almost exactly in proportion (-9%),
   so overall staffing tracked enrollment reasonably well in both
   directions. But the *dollar* cost of that staff, and the *mix* of
   what it's spent on, did not track enrollment at all:
   - **Average teacher salary** rose from $95,968 to $131,997 in just
     seven years (FY2018-2025), a 4.66%/yr CAGR — collective bargaining
     and cost-of-living pressure, independent of how many students are
     enrolled.
   - **Benefits** (insurance, retirement) more than doubled per pupil
     (+102.5%, FY2009-2025) — the same Town-wide benefits inflation this
     project's Phase 3 model already tracks (5.5%/yr CAGR), landing on
     the schools' side of the ledger identically to the Town's.

3. **A real reallocation toward higher-need students, happening mostly
   in the last five years.** Special Education Instructional Support FTE
   *more than doubled* (10.9→23.7, +117%, FY2009-2025). Pupil Services
   spending per pupil grew the fastest of any category (+151%). This
   isn't enrollment-driven (special-ed enrollment barely moved while
   total enrollment fell 11%) — it's a policy/mandate-driven shift, paid
   for partly by cutting elsewhere (Professional Development spending
   per pupil actually *fell* 29% over the same window, and general
   education staffing was cut to fund it, per the ERSC report's own
   FTE-by-function table).

## The quantified breakdown (FY2009→FY2025, per-pupil $, DESE's own function categories)

| Category | FY2009 | FY2025 | % change | CAGR |
|---|---:|---:|---:|---:|
| Pupil Services | $681 | $1,712 | +151.4% | 5.93%/yr |
| Guidance, Counseling and Testing | $540 | $1,109 | +105.4% | 4.60%/yr |
| Insurance, Retirement Programs and Other (benefits) | $2,725 | $5,519 | +102.5% | 4.51%/yr |
| Other Teaching Services | $1,638 | $3,214 | +96.2% | 4.30%/yr |
| Instructional Materials, Equipment and Technology | $338 | $646 | +91.1% | 4.13%/yr |
| Operations and Maintenance | $1,540 | $2,363 | +53.4% | 2.71%/yr |
| Teachers | $6,661 | $10,233 | +53.6% | 2.72%/yr |
| Administration | $769 | $1,112 | +44.6% | 2.33%/yr |
| Instructional Leadership | $1,098 | $1,507 | +37.2% | 2.00%/yr |
| Professional Development | $243 | $172 | **-29.2%** | -2.14%/yr |
| **Total In-District Expenditures** | **$16,232** | **$27,589** | **+70.0%** | **3.37%/yr** |

(Category $ sum to "Total In-District Expenditures"; the separate,
larger "Total Expenditures" figure additionally includes out-of-district
special-education placements — a real, distinct, individually-negotiated
cost the ERSC report flags as volatile, not broken out further here.)

**The spread is the finding.** Every category grew faster than the
32-year-old "Professional Development" line, which actually shrank. The
fastest four categories (Pupil Services, Guidance, Benefits, Other
Teaching Services) all ran 4.3-5.9%/yr — well above the 3.37%/yr blended
total, and far above Teachers' 2.72%/yr, even though Teachers is by far
the largest single line. A single blended CAGR erases this entirely.

## Why "keep growing at the blended CAGR" will be wrong, and what would fix it

A flat CAGR on the total ($ or per-pupil) implicitly assumes every
category keeps its current *share* of the budget forever. That's
already been false for 16 years running — Teachers' share of total
in-district spending fell from 41.0% (FY2009) to 37.1% (FY2025) even
as its dollar amount grew, because faster-growing categories (Benefits,
Pupil Services) are eating share. Extrapolating the blended rate forward
either overstates Teachers-type costs or understates Benefits/Pupil-
Services-type costs, depending which one you're really trying to answer.

Four concrete ways to do better, using data this project already has or
could build cleanly from what's here:

1. **Model categories separately, not as one blended total.** This
   project's own Phase 3 (`baseline_expense_forecast.py`) already treats
   `benefits` as its own top-level category with a real trailing CAGR
   distinct from `schools`/`departmental` — the same discipline applied
   *inside* the schools budget (Teachers vs. Benefits vs. Pupil Services
   vs. everything else) would carry the same benefit: a category that's
   growing at 5.9%/yr doesn't get flattened into a 3.4%/yr blend just
   because a bigger, slower category sits next to it.

2. **Decompose cost = headcount × unit cost, since both pieces are now
   separately available.** Teacher FTE and Average Teacher Salary are
   two different drivers with two different behaviors — FTE follows
   enrollment (with a lag, see below), salary follows the collective
   bargaining schedule (a knowable, negotiated number, the same way this
   project already pulls the real pension ADC schedule instead of
   trending it). Multiplying two well-modeled pieces is more defensible
   than trending their product.

3. **Give Special Education / Pupil Services its own volatility
   treatment, not a smooth trend.** It's both the fastest-growing
   category *and* the one the ERSC report itself calls "increasing and
   unpredictable" (individually-negotiated out-of-district placements,
   not a smooth function of enrollment or inflation) — a single point
   forecast for this line will be wrong more often than the others by
   construction. A range or a reserve-fund-style buffer (which the ERSC
   report itself recommends the Town adopt operationally) is more honest
   than a CAGR point estimate here specifically.

4. **Model the enrollment-to-staffing relationship with a lag, not an
   instantaneous ratio.** Staffing kept growing through FY2021, a full
   year after enrollment had already turned down (FY2019 peak, FY2020
   already declining) — and did not bottom out until FY2025, four years
   after enrollment's own low point. A model that assumes staffing
   (and therefore departmental/school cost) responds to enrollment in
   the same year will systematically miss both the timing and the
   magnitude of the response in either direction.

## Open items

- Category breakdown only goes back to FY2009 (DESE's Socrata dataset's
  own start point) — 4 years short of this project's FY2005 floor for
  everything else. Not resolvable without a different, older DESE
  source, not yet located.
- Average Teacher Salary only goes back to FY2018 in this same dataset
  (blank for FY2009-2017) — a real gap, not a scrape failure.
- "Total Expenditures" minus "Total In-District Expenditures" (the
  out-of-district placement gap) isn't broken into its own time series
  here — would need a separate pull if that specific line is wanted.
