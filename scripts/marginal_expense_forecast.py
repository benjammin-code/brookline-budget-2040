"""
SUPERSEDED 2026-09-29. The town-wide cost of growth is now carried by the driver
forecast (expense_driver_forecast.py), and the per-home, per-employee and
per-student costs live in cost_assumptions.py, shared with the per-project
calculator. Nothing reads this script's output any more; it is kept, unrun, as
the record of the RKG-based marginal layer (README items 6 and 8).
"""
"""
Phase 4: Marginal (Town-wide) expense impact of new growth, FY2026-2040.

Reuses Phase 2's physical new-growth output (`output/new_growth_scenarios_
fy26_40.csv` - implied new residential units and commercial sqft, per year,
under 4 growth scenarios) and applies per-unit/per-employee/per-pupil
marginal municipal cost figures from the Town's own RKG Associates fiscal
impact model (via the ERSC Final Report, March 2026, Appendix C) to produce
a Town-wide estimate of what new growth costs the Town in services -
distinct from Phase 3's baseline (which holds service levels/growth
constant and says nothing about *why* costs change with development).

## The disputed per-pupil figure - resolved

README/Phase 4 flagged three competing numbers: $15,572 (RKG/ERSC), $18,077.77
(an earlier per-project fiscal impact workbook (not published)), and ~$26,623-30K (DESE "full
average cost"). Read the ERSC report's actual RKG presentation slide
(p.~553 area, not just the committee's own prose summary of it, which is
where the confusion originated) - the arithmetic is:

    Total School Budget (RKG, FY25 basis):        $163,529,116
    Incremental School Budget (67% of total):      $109,612,390
    ÷ In-District Enrollment (Fall 2024):                 7,039
    = Per-Pupil Cost of Local Funding:                  $15,572

$109,612,390 / 7,039 = $15,572.86 - matches essentially exactly. **The
$15,572 figure is arithmetically sound**, not an error - the ERSC
committee's own Appendix D confusion (a member's note asking "cost per
pupil looks to be off by a factor of two") traces to one RKG presentation
slide mislabeling the $163.5M *total* school budget as the *incremental*
figure, which this project's own earlier research (see `.claude/
memorialized.md`, 2026-08-28) read literally and reasonably flagged as
suspicious - re-deriving from the underlying slide (not the committee's
paraphrase of it) resolves it. Cross-checked the 7,039 enrollment
figure against two independent sources: MA DESE's official finance
profile (7,034 in-district FTE, FY2024) and the Town's own FY2027
Financial Plan (6,822-6,899 pupils, Chapter 70 aid calculation,
FY26/27) - all three cluster tightly around ~6,800-7,100, confirming
7,039 is a real, correct enrollment figure, not the source of any error.

**What's still a real, unresolved judgment call** (not an arithmetic
error): the **67% "incremental" share** is explicitly "est. based on
interviews with Town staff" per the RKG slide - a subjective allocation,
not empirically derived from actual cost-behavior data (e.g. how school
costs actually responded to past enrollment changes). This project takes
no position on whether 67% is the right split; it's carried forward as-is
since it's the Town's own consultant's figure and no better alternative
exists yet.

**DESE's $26,682.66/pupil (FY2024, in-district, all funds) is not a
competing estimate of the same thing** - it's the full AVERAGE cost per
pupil (total budget ÷ total enrollment), while $15,572 is the marginal
cost per ADDITIONAL pupil (a fraction of the budget, on the theory that
fixed costs - administration, building operations baseline, etc. - don't
scale with each new student). Both are legitimate, answer different
questions, and this script uses both (see SCHOOL_COST_SCENARIOS below) -
not because one is right and one is wrong, but because "keep what we have"
sizing benefits from an honest low/high range rather than a single point
estimate, per the ERSC report's own closing advice ("Beware of platitudes
- ranges of likely outcomes are highly recommended!").

## Non-school marginal costs

From the same ERSC/RKG appendix (already validated in an earlier session
by reading the PDF page images directly, since text extraction mangles
these specific tables):
  - Residential: **$1,371/occupied unit** (non-school municipal services -
    police, fire, general gov't, public works, etc.)
  - Commercial: **$219/employee** (same service categories), converted to
    a per-sqft basis using RKG's own density multiplier: **1 employee per
    200 sqft** for office/retail/life science (the dominant commercial use
    types for Brookline's actual development pattern - no meaningful
    industrial zoning, and hotel is only relevant via CHCA, which is
    modeled separately with its own RKG-sourced figures and explicitly
    excluded from the generic `com_new` bucket this script uses, so it's
    not double-counted). Total Brookline employees (EOLWD ES-202, Q2 2024):
    17,247, the denominator RKG's own $219/employee is built from.

Both figures are FY25 basis and are extended at the same Schedule A
trailing-actual CAGRs Phase 3 already established (departmental for
non-school, education for school) - reusing Phase 3's own trend rates
rather than inventing new ones.

## Students-per-unit (SAC) assumption — bedroom-tiered, not a flat average

Converts new residential units into new students. Ben's observation
(2026-08-30): RKG's model doesn't apply one flat SAC to every new unit —
general municipal cost applies to every new unit regardless of who lives
there, but school cost is gated by whether a unit is actually likely to
house a school-age child, which varies sharply by bedroom count. Confirmed
directly: RKG's own bedroom-tiered SAC schedule is already in an earlier per-project fiscal impact workbook (not published) (`Unit Mix` tab) — it's
what that workbook's own 0.126 students/unit figure is built from for its
specific (studio/1BR-heavy) unit mix:

| Bedroom type | SAC (students/unit) |
|---|---|
| Studio | 0.00 |
| 1 BR | 0.00 |
| 2 BR | 0.25 |
| 3 BR | 0.35 |

An earlier version of this script used a flat Town-wide average instead
(in-district enrollment ÷ occupied housing units = 0.2585) — a reasonable
approximation, but not RKG's actual method, and not specific to new
construction. **Now uses RKG's real bedroom-tiered schedule, weighted by
Brookline's own actual historical new-construction bedroom mix** —
`land-value-map/scripts/bedrooms_by_new_unit.py` already exists in this
project and pulls average bedrooms/unit for each new-construction event
`land-value-map`'s classifier identified, FY2018-2025 (extended through
FY2025 2026-08-30, once Ben supplied the full FY2025 assessor CAMA export)
(`land-value-map/output/new_unit_bedroom_detail_fy18_25.csv`). Linear-
interpolating RKG's tiers (extrapolating the 2BR→3BR slope beyond 3BR) and
weighting by that dataset's 34 matched new units (avg 2.31 bedrooms/unit)
gives a computed Town-wide SAC of **~0.2442** (`compute_town_wide_sac()`)
— close to the earlier flat estimate (0.2585, within 6%) but grounded in
RKG's real methodology and Brookline's own construction data, not a proxy.

**Real caveat, not resolved here**: that FY18-25 sample is still small (34
units) and skews toward condo conversions, per `land-value-map/
METHODOLOGY.md`'s own documented detection limits — it may not represent
what larger new developments look like. One recent rental project's own
0.126 (a studio/1BR-heavy high-rise) sits well below this Town-wide
figure; CHCA or other large-scale multifamily could plausibly land
anywhere in that range. Treat 0.2442 as this model's best available
Town-wide default, not a tight estimate.

Outputs:
  ../output/marginal_expense_forecast_fy26_40.csv
  ../output/marginal_expense_forecast_fy26_40_methodology.md

Sources: ERSC Final Report FINAL 031326.pdf (Appendix C, RKG Associates
fiscal impact model); MA DESE finance profile (profiles.doe.mass.edu,
Brookline orgcode 00460000, FY2024); Town of Brookline FY2027 Financial
Plan (Chapter 70 enrollment figures); Phase 2 (`new_growth_scenario_
forecast.py`) and Phase 3 (`baseline_expense_forecast.py`) of this project.
"""
import csv

NEW_GROWTH_FILE = "../output/new_growth_scenarios_fy26_40.csv"
HISTORICAL_FILE = "../output/brookline_historical_financials_fy05_25.csv"
OUT_FILE = "../output/marginal_expense_forecast_fy26_40.csv"
METHODOLOGY_FILE = "../output/marginal_expense_forecast_fy26_40_methodology.md"

FORECAST_YEARS = list(range(2026, 2041))
BASIS_YEAR = 2025  # RKG/ERSC figures are FY25 basis

RES_MARGINAL_COST_PER_UNIT_FY25 = 1371.0
COM_MARGINAL_COST_PER_EMPLOYEE_FY25 = 219.0
COM_SQFT_PER_EMPLOYEE = 200.0  # RKG: office/retail/life science density

BEDROOM_DETAIL_FILE = "../land-value-map/output/new_unit_bedroom_detail_fy18_25.csv"
# RKG's own bedroom-tiered SAC schedule (an earlier per-project fiscal impact workbook (not published), "Unit Mix" tab) - linearly interpolated between tiers,
# extrapolating the 2BR->3BR slope beyond 3BR.
RKG_SAC_TIERS = [(0, 0.0), (1, 0.0), (2, 0.25), (3, 0.35)]


def rkg_sac_for_bedrooms(bedrooms):
    if bedrooms <= 0:
        return 0.0
    if bedrooms >= 3:
        return 0.35 + (bedrooms - 3) * (0.35 - 0.25)
    for (x0, y0), (x1, y1) in zip(RKG_SAC_TIERS, RKG_SAC_TIERS[1:]):
        if x0 <= bedrooms <= x1:
            return y0 + (y1 - y0) * (bedrooms - x0) / (x1 - x0)


def compute_town_wide_sac():
    """Units-weighted SAC across Brookline's own actual FY18-25 new-construction
    bedroom mix, applying RKG's bedroom-tiered schedule - see module docstring."""
    with open(BEDROOM_DETAIL_FILE) as f:
        rows = list(csv.DictReader(f))
    total_units = sum(float(r["units_added"]) for r in rows)
    weighted_sac = sum(float(r["units_added"]) * rkg_sac_for_bedrooms(float(r["avg_bedrooms_per_unit"]))
                        for r in rows)
    return weighted_sac / total_units, total_units


SCHOOL_COST_SCENARIOS = {
    # (basis_year, cost_per_pupil_at_basis_year)
    "rkg_marginal": (2025, 15572.0),
    "dese_full_average": (2024, 26682.66),
}


def read_new_growth():
    """Returns {growth_scenario: {year: (res_units, com_sqft)}}."""
    out = {}
    with open(NEW_GROWTH_FILE) as f:
        for row in csv.DictReader(f):
            scenario = row["scenario"]
            y = int(row["fiscal_year"])
            out.setdefault(scenario, {})[y] = (
                float(row["implied_res_new_units"]), float(row["implied_com_new_sqft"]))
    return out


def read_historical():
    with open(HISTORICAL_FILE) as f:
        return {int(row["fiscal_year"]): row for row in csv.DictReader(f)}


def cagr(start, end, years):
    return (end / start) ** (1 / years) - 1


def main():
    new_growth = read_new_growth()
    hist = read_historical()

    dept_cols = ["exp_general_government", "exp_public_safety", "exp_public_works",
                 "exp_human_services", "exp_culture_recreation"]

    def sched_dept(y):
        return sum(float(hist[y][c]) for c in dept_cols)

    def sched_school(y):
        return float(hist[y]["exp_education"])

    # Same trailing-5yr Schedule A CAGRs Phase 3 already established -
    # reused here, not re-derived, so both scripts agree on how these
    # categories grow.
    dept_cagr_trend = cagr(sched_dept(2020), sched_dept(2025), 5)
    school_cagr_trend = cagr(sched_school(2020), sched_school(2025), 5)

    town_wide_sac, bedroom_sample_units = compute_town_wide_sac()

    print(f"Non-school marginal cost growth: {dept_cagr_trend:.2%}/yr (Schedule A departmental trailing CAGR, reused from Phase 3)")
    print(f"School marginal cost growth: {school_cagr_trend:.2%}/yr (Schedule A education trailing CAGR, reused from Phase 3)")
    print(f"Town-wide SAC (students/new unit): {town_wide_sac:.4f} (RKG bedroom-tiered schedule, "
          f"weighted by {bedroom_sample_units:.0f} actual FY18-25 new units' bedroom mix)")

    def res_cost_per_unit(y):
        return RES_MARGINAL_COST_PER_UNIT_FY25 * (1 + dept_cagr_trend) ** (y - BASIS_YEAR)

    def com_cost_per_employee(y):
        return COM_MARGINAL_COST_PER_EMPLOYEE_FY25 * (1 + dept_cagr_trend) ** (y - BASIS_YEAR)

    def school_cost_per_pupil(scenario, y):
        basis_year, basis_cost = SCHOOL_COST_SCENARIOS[scenario]
        return basis_cost * (1 + school_cagr_trend) ** (y - basis_year)

    rows = []
    for growth_scenario, by_year in new_growth.items():
        cumulative_res_units = 0.0
        cumulative_com_sqft = 0.0
        for y in FORECAST_YEARS:
            res_units_this_year, com_sqft_this_year = by_year[y]
            cumulative_res_units += res_units_this_year
            cumulative_com_sqft += com_sqft_this_year
            cumulative_com_employees = cumulative_com_sqft / COM_SQFT_PER_EMPLOYEE
            implied_new_students = cumulative_res_units * town_wide_sac

            res_rate = res_cost_per_unit(y)
            com_rate = com_cost_per_employee(y)
            res_expense = cumulative_res_units * res_rate
            com_expense = cumulative_com_employees * com_rate

            for cost_scenario in SCHOOL_COST_SCENARIOS:
                school_rate = school_cost_per_pupil(cost_scenario, y)
                school_expense = implied_new_students * school_rate
                total = res_expense + com_expense + school_expense

                rows.append([
                    growth_scenario, cost_scenario, y,
                    round(cumulative_res_units), round(cumulative_com_sqft),
                    round(cumulative_com_employees), round(implied_new_students),
                    round(res_rate, 2), round(com_rate, 2), round(school_rate, 2),
                    round(res_expense), round(com_expense), round(school_expense),
                    round(total),
                ])

    with open(OUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "growth_scenario", "school_cost_scenario", "fiscal_year",
            "cumulative_res_new_units", "cumulative_com_new_sqft",
            "cumulative_com_new_employees", "implied_new_students",
            "res_marginal_cost_per_unit", "com_marginal_cost_per_employee",
            "school_marginal_cost_per_pupil",
            "res_marginal_expense", "com_marginal_expense", "school_marginal_expense",
            "total_marginal_expense",
        ])
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUT_FILE}")
    for growth_scenario in new_growth:
        for cost_scenario in SCHOOL_COST_SCENARIOS:
            r40 = next(r for r in rows if r[0] == growth_scenario and r[1] == cost_scenario and r[2] == 2040)
            print(f"{growth_scenario} / {cost_scenario}: FY2040 total marginal expense ${r40[-1]:,.0f} "
                  f"(res ${r40[-4]:,.0f} + com ${r40[-3]:,.0f} + school ${r40[-2]:,.0f}, "
                  f"cumulative {r40[3]} units / {r40[6]} students)")

    write_methodology(dept_cagr_trend, school_cagr_trend, town_wide_sac, bedroom_sample_units, rows)
    print(f"Wrote methodology doc to {METHODOLOGY_FILE}")


def write_methodology(dept_cagr_trend, school_cagr_trend, town_wide_sac, bedroom_sample_units, rows):
    def get(growth, cost, year, col):
        r = next(r for r in rows if r[0] == growth and r[1] == cost and r[2] == year)
        idx = {"cumulative_res_new_units": 3, "cumulative_com_new_sqft": 4,
               "cumulative_com_new_employees": 5, "implied_new_students": 6,
               "total_marginal_expense": 13}[col]
        return r[idx]

    trend_low_2040 = get("trend_continues", "rkg_marginal", 2040, "total_marginal_expense")
    trend_high_2040 = get("trend_continues", "dese_full_average", 2040, "total_marginal_expense")
    students_2040 = get("trend_continues", "rkg_marginal", 2040, "implied_new_students")
    units_2040 = get("trend_continues", "rkg_marginal", 2040, "cumulative_res_new_units")

    doc = f"""# Marginal Expense Forecast (FY2026-2040) — Assumptions & Methodology

Companion to `marginal_expense_forecast_fy26_40.csv`. Phase 4: what new
growth costs the Town in added municipal services, Town-wide - distinct
from Phase 3's baseline (which holds service levels constant and doesn't
attempt to explain cost drivers).

## Scope

Applies per-unit/per-employee/per-pupil marginal cost figures (below) to
Phase 2's physical new-growth output (`new_growth_scenarios_fy26_40.csv`),
cumulatively - a unit built in FY2027 keeps generating marginal cost every
year after that, not just the year it's built. Two independent axes,
crossed (4 x 2 = 8 combinations per year):

- **`growth_scenario`** (from Phase 2): `trend_continues` or one of three
  `peer_target_*` variants - how much physical development happens.
- **`school_cost_scenario`**: `rkg_marginal` ($15,572/pupil, FY25 basis) or
  `dese_full_average` ($26,682.66/pupil, FY2024 basis) - a deliberate
  low/high range, not a right-vs-wrong choice (see below).

Non-school costs (`res_marginal_cost_per_unit`, `com_marginal_cost_per_employee`)
don't vary by `school_cost_scenario` - the dispute this project was asked
to resolve is specifically about the per-pupil figure, not these.

## The disputed per-pupil figure — resolved: $15,572 is arithmetically sound

README/Phase 4 named three numbers: $15,572 (RKG/ERSC), $18,077.77 (an earlier per-project fiscal impact workbook (not published)), and ~$26,623-30K (DESE "full average"). Re-derived directly
from the RKG presentation slide reproduced in the ERSC Final Report
(not the committee's own prose summary of it elsewhere in the report,
which is where an earlier research session's suspicion originated):

    Total School Budget (RKG, FY25 basis):        $163,529,116
    Incremental School Budget (67% of total):      $109,612,390
    ÷ In-District Enrollment (Fall 2024):                 7,039
    = Per-Pupil Cost of Local Funding:                  $15,572

$109,612,390 / 7,039 = $15,572.86 — matches to the dollar. **This is not
an error.** The ERSC committee's own Appendix D (a member's note: "cost
per pupil looks to be off by a factor of two... Is that because the extra
student at the margin does not cost the full load?") traces to one RKG
slide mislabeling the $163.5M *total* school budget as the *incremental*
figure — reading the committee's paraphrase of that mislabeled slide (as
an earlier session of this project did) reasonably raised the same
suspicion; reading the underlying slide itself resolves it.

**Enrollment cross-checked against two independent sources**, not just
taken from the RKG slide: MA DESE's official finance profile
(profiles.doe.mass.edu) reports **7,034 in-district FTE** for FY2024; the
Town's own FY2027 Financial Plan reports **6,822-6,899 pupils** (Chapter
70 aid calculations, FY26/FY27). All three (7,039 RKG, 7,034 DESE, 6,822-
6,899 Financial Plan) cluster tightly in the same ~6,800-7,100 range —
confirms 7,039 is a real, correct figure, not the source of any
discrepancy.

**What's genuinely still a judgment call, not an arithmetic question**:
the **67% "incremental" share** is explicitly "est. based on interviews
with Town staff" on the RKG slide — a subjective allocation of which
school costs scale with enrollment and which are fixed, not derived from
an actual cost-behavior study (e.g. how school spending historically
responded to past enrollment changes). This project takes no position on
whether 67% is right; it's the Town's own consultant's figure and no
better-grounded alternative exists yet. Flagged as the real remaining soft
spot, distinct from the arithmetic (which checks out).

**DESE's $26,682.66/pupil is not a competing estimate of the same
quantity** — it's the full AVERAGE cost per pupil (total budget ÷ total
enrollment, all costs included), while $15,572 is the marginal cost per
ADDITIONAL pupil (only the 67% judged to scale with enrollment). Both are
legitimate concepts answering different questions. This script uses both
as a deliberate low/high range rather than picking one, per the ERSC
report's own closing advice: *"Beware of platitudes — ranges of likely
outcomes are highly recommended!"* This project's own $18,077.77 (a
~16% inflation of the $15,572 RKG figure to a more current school budget
year, per that workbook's own in-file description) falls inside this
range, close to the low end — consistent with, not contradicting, either
bound here.

## Non-school marginal costs: $1,371/unit (residential), $219/employee (commercial)

From the same ERSC/RKG Appendix C (validated in an earlier session by
reading the PDF page images directly — this specific table's text
extraction is unreliable, so these figures are NOT re-derived from a text
grep this session, only reused from prior validated research). FY25
basis, extended at **{dept_cagr_trend:.2%}/yr** — the Schedule A
departmental trailing-5yr CAGR Phase 3 already established
(`baseline_expense_forecast.py`), reused rather than re-derived so the
two scripts agree on how this category grows.

Commercial cost is applied per employee, converted from Phase 2's sqft
figures using RKG's own density multiplier: **1 employee per 200 sqft**
(the rate RKG uses for office/retail/life science — the commercial types
actually relevant to Brookline's development pattern; no meaningful
industrial zoning, and hotel development is only relevant via CHCA, which
has its own RKG-sourced fiscal figures already baked into Phase 1/2 and
is explicitly excluded from the generic `com_new` bucket this script
draws from, avoiding double-counting). Total Brookline employees, the
denominator behind RKG's own $219/employee figure: 17,247 (EOLWD ES-202
Job Data, Q2 2024).

## Students-per-unit (SAC): RKG's bedroom-tiered schedule, weighted by real construction data

Converts cumulative new residential units into new students. Ben's
observation (2026-08-30): RKG's model doesn't apply one flat SAC to every
unit — general municipal cost applies regardless of occupant, but school
cost is gated by bedroom count, since that's what actually predicts
whether a unit houses a school-age child. RKG's own bedroom-tiered SAC
schedule is already in an earlier per-project fiscal impact workbook (not published) (`Unit Mix` tab) — Studio/1BR = 0.00, 2BR = 0.25, 3BR = 0.35 —
and is what that workbook's own project-specific SAC of 0.126 students/unit
is built from, for its particular (studio/1BR-heavy) unit mix.

An earlier version of this script used a flat Town-wide average instead
(in-district enrollment ÷ occupied housing units = 0.2585) — reasonable,
but not RKG's actual method, and not specific to new construction. **Now
uses RKG's bedroom-tiered schedule, weighted by Brookline's own actual
FY2018-2025 new-construction bedroom mix** —
`land-value-map/scripts/bedrooms_by_new_unit.py` (already built in this
project) reports average bedrooms/unit for each new-construction event the
land-value-map classifier identified
(`land-value-map/output/new_unit_bedroom_detail_fy18_25.csv`).
Linear-interpolating RKG's tiers (extrapolating the 2BR→3BR slope beyond
3BR) and weighting by that dataset's **{bedroom_sample_units:.0f} matched
new units** (avg 2.31 bedrooms/unit) gives **{town_wide_sac:.4f}
students/unit** — close to the flat estimate (0.2585, within 6%), but
grounded in RKG's real methodology and Brookline's own construction data
rather than an existing-stock proxy.

**Real caveat, not resolved here**: that sample is small
({bedroom_sample_units:.0f} units) and skews toward condo conversions,
per `land-value-map/METHODOLOGY.md`'s documented detection limits — it may
not represent what larger new developments look like. One recent rental project's own 0.126 (studio/1BR-heavy high-rise) sits well below this
Town-wide figure; CHCA or other large-scale multifamily could plausibly
land anywhere in the range between them. Treat {town_wide_sac:.4f} as this
model's best available Town-wide default, not a tight estimate.

School marginal cost is extended at **{school_cagr_trend:.2%}/yr**
(Schedule A education trailing-5yr CAGR, also reused from Phase 3), from
each scenario's own basis year (FY2025 for `rkg_marginal`, FY2024 for
`dese_full_average`).

## Headline result

`trend_continues` growth scenario, FY2040: cumulative {units_2040:,}
new residential units generate an estimated {students_2040:,.0f} new
students. Total Town-wide marginal expense ranges
**${trend_low_2040:,.0f}** (`rkg_marginal`) to **${trend_high_2040:,.0f}**
(`dese_full_average`) — the gap between these two is almost entirely the
school marginal-cost assumption, since non-school costs don't vary by
scenario. See the CSV for all 4 growth scenarios and both cost scenarios,
year by year.

## What this deliberately excludes

- **CHCA-specific marginal costs** — a real, known project with its own
  RKG-sourced revenue figures already in Phase 1/2, but no CHCA-specific
  marginal *cost* estimate has been built yet. Not included here to avoid
  fabricating a number; a real gap, worth flagging as a next step.
- **Revenue side** — this file is expense-only. Comparing to Phase 1/2's
  revenue-side new-growth figures (net fiscal impact of growth, not just
  its cost) is Phase 5's job.
- **Non-school cost department-level detail** (police vs. fire vs. public
  works, etc.) — available in the ERSC appendix but not carried into this
  Town-wide model; only the totals ($1,371/unit, $219/employee) are used.

## Sources

- `data/ERSC Final Report FINAL 031326.pdf` — RKG Associates fiscal impact
  model, Appendix C (marginal cost figures) and the per-pupil arithmetic
  slide (re-derived this session directly from the slide, not the
  committee's prose summary).
- MA DESE finance profile, Brookline (orgcode 00460000), FY2024
  (profiles.doe.mass.edu) — enrollment and full average cost/pupil.
- `data/FY2027-Financial-Plan.pdf` — Chapter 70 enrollment cross-check.
- `output/new_growth_scenarios_fy26_40.csv` (Phase 2) — physical growth
  scenarios this model applies costs to.
- `output/baseline_expense_forecast_fy26_40.csv` (Phase 3) — source of the
  reused Schedule A trailing CAGRs.
"""
    with open(METHODOLOGY_FILE, "w") as f:
        f.write(doc)


if __name__ == "__main__":
    main()
