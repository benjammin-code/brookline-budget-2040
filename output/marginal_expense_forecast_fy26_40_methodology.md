# Marginal Expense Forecast (FY2026-2040) — Assumptions & Methodology

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
basis, extended at **3.77%/yr** — the Schedule A
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
3BR) and weighting by that dataset's **34 matched
new units** (avg 2.31 bedrooms/unit) gives **0.2442
students/unit** — close to the flat estimate (0.2585, within 6%), but
grounded in RKG's real methodology and Brookline's own construction data
rather than an existing-stock proxy.

**Real caveat, not resolved here**: that sample is small
(34 units) and skews toward condo conversions,
per `land-value-map/METHODOLOGY.md`'s documented detection limits — it may
not represent what larger new developments look like. One recent rental project's own 0.126 (studio/1BR-heavy high-rise) sits well below this
Town-wide figure; CHCA or other large-scale multifamily could plausibly
land anywhere in the range between them. Treat 0.2442 as this
model's best available Town-wide default, not a tight estimate.

School marginal cost is extended at **3.42%/yr**
(Schedule A education trailing-5yr CAGR, also reused from Phase 3), from
each scenario's own basis year (FY2025 for `rkg_marginal`, FY2024 for
`dese_full_average`).

## Headline result

`trend_continues` growth scenario, FY2040: cumulative 2,599
new residential units generate an estimated 635 new
students. Total Town-wide marginal expense ranges
**$22,711,724** (`rkg_marginal`) to **$35,355,680**
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
