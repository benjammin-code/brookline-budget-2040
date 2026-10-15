"""
Phase 2: new-growth revenue scenarios, FY2026-2040, built on top of Phase 1's
"trend_corrected" baseline (`baseline_revenue_forecast.py`).

Phase 1 modeled new growth as one blended rate (1.277%/yr of prior levy) -
Ben's explicit, repeated preference is a %-of-prior-levy mechanic, not a
flat/fixed amount, because a fixed amount implicitly becomes a shrinking
share of a growing levy base over time (see baseline_revenue_forecast.py's
own docstring for the original argument). Ben's direction (2026-08-28):
split that one rate into four categories - residential new construction,
residential renovation, commercial new/expanded space, commercial "other"
(renovation + assessment catch-up, indistinguishable from unmeasured
expansion) - because each has a different implication for Town *expenses*
later (Phase 4), even though this script only handles the *revenue* side.

**Corrected 2026-08-29** (Ben caught this): an earlier version of this
script expressed the residential-new and commercial-new levers as *fixed
physical counts* (units/yr, sqft/yr) rather than percentages. That
reintroduced exactly the problem Ben flagged for Phase 1's flat-dollar
figure - a fixed physical pace's dollar contribution tracks its own
appreciation rate, not the levy's growth rate, so for commercial specifically
(1.28%/yr appreciation vs. ~3.8-4%/yr typical levy growth) it silently
became a *shrinking* share of the levy over the 15-year window. Fixed: all
four categories are now %-of-prior-total-levy, same convention as Phase 1,
with **physical units/sqft as a derived, reported translation** (not an
input) - computed each year by dividing that category's dollar amount by
the *appreciated* $/unit or $/sqft for that year (see
appreciated_res_value_per_unit / appreciated_com_value_per_sqft below).
This means the implied physical count drifts over the forecast window even
though the % driving it is held constant - and it drifts in *different
directions* for residential vs. commercial, which is itself a real finding
(see write_methodology's discussion).

--- Conversion factors (computed 2026-08-28/29, see .claude/memorialized.md
    and land-value-map/METHODOLOGY.md Section 5g/5e for full derivation) ---

RES_VALUE_PER_UNIT: marginal assessed value of one new residential unit.
  **Recalibrated 2026-09-22 from $324,000 to $430,000** (Ben's call), on two
  grounds: the old figure used the wrong statistic for the job, and the Town's
  own permit count now provides a physical check that the old figure fails.

  *Wrong statistic.* This constant does exactly one thing: it divides
  residential new-construction new-growth *dollars* to report an implied unit
  count (`implied_units` below). For `total_dollars / X = total_units` to
  hold, X must be `total_dollars / total_units`, i.e. a **units-weighted
  mean**. The original $324,000 was the MEDIAN per *event* across FY18-24
  new-construction events, chosen to resist skew from luxury-building
  outliers. That is a sound instinct for "what does a typical project add per
  unit" and the wrong estimator for a divisor, because it systematically
  overstates the unit count: at $324,000 the model reported 221 implied units
  in FY2026.

  *Physical check.* The Town's Planning Department published its own net-new-
  housing count from building permits (`data/Development Look-Ahead June
  2026.pdf`, slide 9): CY2022 252, CY2023 190, CY2024 57, **499 over three
  years, 166/yr**. Back-solving the FY2026 residential new-construction
  new growth ($704,990 at RES_TAX_RATE) against that count gives
  **$430,909/unit**, and at $430,000 the model reports 167 implied units,
  matching the Town's count rather than exceeding it by a third.

  *Why not measured from the roll.* The obvious approach - total value added
  over total units added, straight from `classification_fy17_24.csv` - does
  not survive inspection, and the reason is worth recording so nobody retries
  it. Screening to taxable housing descriptions, non-exempt parcels and
  positive value deltas leaves 654 units, of which **half carry only 6% of
  the value, at under $100,000/unit**: these are the assessor's unit-count
  recording changes (the same phenomenon as the FY2021 spike, which is not
  confined to FY2021 - e.g. 388-01 in FY2022 adds 135 units at $66,629 each).
  There is no natural break in the distribution to screen on, and the
  units-weighted mean swings from $437,588 (no threshold) to $1,159,461
  (excluding under $250,000/unit) purely on where the cut is placed. The
  roll's unit-count field cannot support this estimate; the permit count can,
  because it never touches that field.

  *Uncertainty, stated plainly.* The back-solve is sensitive to the permit
  window, because CY2024's 57 is a steep drop: CY2022-23 alone gives
  $324,319/unit (which is where the old figure sat), CY2023-24 alone gives
  $580,360. The three-year average is the middle of that and the most
  defensible single window, but $430,000 should be read as the centre of a
  roughly $325k-$580k range, not a precise quantity. The unscreened roll
  figure of $437,588 lands within 2% of it, which is consistent but is not
  independent corroboration given how unstable that figure is.

  Current stock-wide average ($1.05M/unit, FY2024) is still NOT used here -
  that reflects Brookline's expensive existing housing stock, not what an
  *additional* unit typically adds.
    units-weighted $430,000/unit   old median-per-event $324,000/unit
    simple mean per event $794,300/unit

  Note this constant does not affect any dollar figure in the forecast. New
  growth is modelled as a percentage of the prior levy, so units are a
  derived, reported translation only (see the "physical counts" note above).
  Changing it moves reported unit counts and the per-project calculator's
  generic default, nothing else.

COM_VALUE_PER_SQFT: current assessed value per sqft of taxable commercial
  space. Computed from `data/gis/brookline_parcels_2026-07-10.geojson`
  (TOT_FIN_AREA / TOT_VALUE), restricted to for-profit taxable commercial
  classes. This is a *current cross-sectional* benchmark (no historical
  time series of commercial sqft exists - see land-value-map/METHODOLOGY.md
  Section 3b), not a marginal-new-construction figure. **Sanity check
  (2026-08-29)**: the Town's own cited figure for 10 Brookline Place's 2011
  expansion - 18,000 sqft generating "$300,000 of new commercial tax
  revenue annually" (brooklinema.gov/329/Commercial-Development) - implies
  $16.67/sqft/yr in tax revenue, about **2x** this model's implied
  $8.41/sqft/yr ($518 x 1.6238%). Could reflect that office/medical space
  specifically (10 Brookline Place's use) is worth more per sqft than the
  blended taxable-commercial average used here, or that the 2011 figure
  needs inflating to current dollars, or genuine model conservatism. Flagged
  as an open reconciliation item, not corrected - the blended figure is
  still the best *broad* estimate available without a use-type breakdown.
    $508/sqft (aggregate weighted)   $529/sqft (median)

RES_TAX_RATE / COM_TAX_RATE: converts assessed-*value* dollars into
  levy-*applied* dollars. Back-computed from `data/2026 MA state new growth
  for all towns 20 years.xlsx` ("brookline" sheet) as (New Growth Applied
  to Levy Limit) / (New Growth Value), separately for residential and CIP,
  averaged FY2021-2025 (stable year to year - confirms these track
  Brookline's real split tax rate, not noise). These are FY2026-basis
  starting points, not held flat - see `res_tax_rate(year)`/
  `com_tax_rate(year)` and "Tax rate drift" in write_methodology's output
  for why and how they drift (added 2026-08-30, Ben).
    RES_TAX_RATE = 0.9836%   COM_TAX_RATE = 1.6238%

RES_VALUE_APPRECIATION_RATE / COM_VALUE_APPRECIATION_RATE: annual growth in
  $/unit and $/sqft over the forecast horizon (added 2026-08-29 - Ben asked
  directly whether appraised value grows over time; it didn't before).
  Computed from `land-value-map/output/parcel_history_fy17_24.csv`:
  town-wide assessed value growth net of DOR-certified new growth for that
  year (isolates market appreciation of *existing* stock from new
  construction), FY18-24 avg. Distinct from, not double-counted with, the
  2.5% statutory levy cap (that governs already-taxed property, not what a
  newly-built unit/sqft is worth when added).
    RES_VALUE_APPRECIATION_RATE = 4.96%/yr
    COM_VALUE_APPRECIATION_RATE = 1.28%/yr (volatile/negative in COVID
      years 2020-23 - office/retail distress - treat as noisier)

--- Category shares (how the combined 1.277%/yr trailing-5yr rate splits) ---

Residential is 0.839%/1.277% = 65.7% of the combined rate, commercial
0.438%/1.277% = 34.3% (both DOR-certified, `output/
brookline_historical_financials_fy05_25.csv`). Within residential, 20.9% is
identified new construction / 79.1% renovation (FY18-24 avg excl. the
FY2021 assessor-artifact year - land-value-map classifier, DOR-reconciled).
Within commercial, ~1.3% is identified new/reclassified parcels / 98.7%
undifferentiated "other" (commercial detection is structurally
near-impossible - no sqft data exists for commercial parcels historically,
see METHODOLOGY.md Section 3b). These four shares of 1.277% give the
`trend_continues` scenario's percentages below - by construction, this
scenario is now numerically identical to Phase 1's `trend_corrected`, not
just close (a real improvement over the earlier fixed-count version).

--- Chestnut Hill Commercial Area (CHCA) - added 2026-08-29 ---

A real, now-confirmed, one-time addition on top of the four trend/peer
categories above - NOT part of the FY18-24 historical detection this
script's trend rates are built from (CHCA didn't exist yet), so no
double-counting. See CHCA_* constants and chca_revenue() below; full
sourcing in write_methodology().

--- What this does NOT do ---

Revenue-only - no "solve for what mix balances the budget" (needs Phase
3/4's expense forecast, not built yet). Zoning capacity is not modeled -
these scenarios state a %/implied-count as an input/output, not a claim
about what current zoning would actually permit.

Outputs:
  ../output/new_growth_scenarios_fy26_40.csv
  ../output/new_growth_scenarios_fy26_40_methodology.md
"""
import csv

TOWN_FORECAST_FILE = "../output/town_own_forecast_fy26_31.csv"
HISTORICAL_FILE = "../output/brookline_historical_financials_fy05_25.csv"
OUT_FILE = "../output/new_growth_scenarios_fy26_40.csv"
METHODOLOGY_FILE = "../output/new_growth_scenarios_fy26_40_methodology.md"

FORECAST_YEARS = list(range(2026, 2041))
TOWN_YEARS = list(range(2026, 2032))
ANCHOR_YEAR = 2031
EXTEND_YEARS = list(range(2032, 2041))
NEW_GROWTH_TOWN = 2_500_000  # Town's own flat LRFP assumption (see baseline_revenue_forecast.py)
NEW_GROWTH_FY2026_CERTIFIED = 3_561_227  # DLS new growth report, FY2026 applied
NG_BUDGETED_YEAR = 2027   # new growth held at NEW_GROWTH_TOWN, the adopted budget's figure

# May 2026 operating override (FY2027-2029) - passed 2026-05-05, AFTER
# `data/FY27-FY31-Long-Range-Financial-Plan.pdf` was presented (2026-01-13).
# Confirmed directly against that source (slide 8, "PROPERTY TAXES" table):
# its own "General Override" line in the levy build-up is blank for every
# year FY2026-2031 - this document was built to make the case FOR the
# override (see its own Summary slide: "Town structural deficit: $2.9M...
# Schools assumed structural deficit: $13.5M"), not to reflect its passage.
# `town_own_forecast_fy26_31.csv` is kept as a faithful, untouched
# transcription of that document (same convention as the pension-ADC
# correction - see README, 2026-08-30), so it does NOT include this
# override either. Corrected here, at the point every downstream scenario
# consumes it, since by the time this project's own "today" (2026-09-01)
# the override is a decided, legislated fact, not a hypothetical future
# policy lever - the same treatment already given the debt-exclusion
# schedule and CHCA. Year-by-year split from Ben's own `FY27-FY29 Brookline
# property tax & impact of new growth.xlsx` (cross-sourced against the
# Override Guide's $23,254,439 3-year total - see data/SOURCES.md; the two
# already matched exactly for the Town's $5.31M share, and the Schools
# split was independently refined down 9.6% between the two sources' dates,
# also confirmed in SOURCES.md). Per the Override Guide, this override is
# "permanent, not phased-in like Brookline's historical norm" - each
# tranche, once added, stays in the levy base and compounds at 2.5%/yr
# forever after, exactly like every other historical override in this
# project's FY2005-2025 model.
MAY_2026_OVERRIDE_SCHEDULE = {2027: 9_852_330, 2028: 5_602_871, 2029: 7_799_238}


def apply_may_2026_override(property_taxes):
    """Adds the May 2026 override's compounding cumulative dollars on top of
    the Town's pre-vote `property_taxes` figures, FY2027-2031."""
    cumulative = {2026: 0.0}
    for y in range(2027, 2032):
        cumulative[y] = cumulative[y - 1] * 1.025 + MAY_2026_OVERRIDE_SCHEDULE.get(y, 0)
    return {y: property_taxes[y] + cumulative[y] for y in property_taxes}

# --- Conversion factors (see module docstring for full sourcing) ---
# Units-weighted, back-solved against the Town's own permit count - see the
# module docstring for the full derivation and the +/- range. The old
# median-per-event figure is kept for sensitivity, not as a default.
# Method A (Ben, 2026-10-12; scripts/new_homes_parameters.py): the blended assessed value each net
# new home adds, on the new-growth basis, weighted by the 2016-2025 permit mix. Supersedes the
# 2026-09-22 $430,000 back-solved against the Planning Department's 166 homes a year (described above).
import json as _json
from pathlib import Path as _Path
NEW_HOMES = _json.loads((_Path(__file__).resolve().parents[1] / "output" / "new_homes_parameters.json").read_text())
HOMES_TREND_PER_YEAR = NEW_HOMES["pace_homes_per_year"]
RES_VALUE_PER_UNIT = NEW_HOMES["blended_value_per_net_home_fy2026"]
RES_VALUE_PER_UNIT_EVENT_MEDIAN_OLD = 324_000
RES_VALUE_PER_UNIT_MEAN = 794_300
COM_VALUE_PER_SQFT = 518  # aggregate weighted; median is $529, close enough to use one figure
RES_TAX_RATE = 0.009836
COM_TAX_RATE = 0.016238
RES_VALUE_APPRECIATION_RATE = 0.0496
COM_VALUE_APPRECIATION_RATE = 0.0128


def appreciated_res_value_per_unit(year, res_value_per_unit=RES_VALUE_PER_UNIT):
    return res_value_per_unit * (1 + RES_VALUE_APPRECIATION_RATE) ** (year - 2026)


def appreciated_com_value_per_sqft(year):
    return COM_VALUE_PER_SQFT * (1 + COM_VALUE_APPRECIATION_RATE) ** (year - 2026)


# --- Building permits (added 2026-08-30, Ben) ---
# Permit fees are levied as a % of reported construction cost - and per
# Ben, permits are pulled for renovation too, not just new construction
# (he renovated a Brookline house and confirms this from experience). So
# this applies to the four *real estate* new-growth categories (res-new,
# res-reno, com-new, com-reno), not personal property (see
# TREND_COM_PP_PCT below - equipment purchases don't need a building
# permit, only construction/renovation does).
#
# **Official rate confirmed 2026-08-30** (Ben: "let's research that"),
# directly from the Town's own page (brooklinema.gov/183/Permit-Fee-Schedule,
# fee schedule effective 2022-07-18): **$20 per $1,000 of construction
# value = 2.0% flat** - building, electrical, plumbing, gas fitting,
# mechanical, sprinkler, demolition, fire alarm, and smoke detector
# permits all use this same rate. No residential/commercial distinction,
# no new-construction-vs-alteration distinction - directly confirms Ben's
# point that this applies broadly, not just to new construction.
#
# **RATE INCREASE FOUND 2026-09-04** (Ben: "I think I saw the town
# increased permit fees to $21/1000 of project value recently. can you
# double check?" - he was right). The Town's Building Department page
# (brooklinema.gov/172/Building-Department) carries a dated alert,
# "Building Dept. Fee Increase Effective July 1, 2026": **permit fees
# will be $21 / $1,000 of estimated cost, with specific exceptions** =
# **2.1%**. July 1, 2026 is the first day of FY2027, so FY2026 keeps 2.0%
# and FY2027-2040 use 2.1%.
#
# **Note the source conflict, and which one wins**: the dedicated fee
# schedule page (183) STILL showed "$20 per $1,000" with its 2022
# effective date when re-checked 2026-09-04 - it simply hasn't been
# updated. The Building Department page's dated increase notice is newer
# and more specific, so it governs. This is why the 2026-08-30 comment's
# "still current" phrasing was wrong within about five weeks: a fee
# schedule page carrying an old effective date is evidence of what the
# rate WAS, not proof of what it IS. Re-check both pages before trusting
# this constant again.
#
# Cross-checked against actual collections: `data/revenue & expenditures
# all MA/LocalReciptesActVsEst {year}.xls` (DOR's itemized local-receipts
# breakdown, all 351 municipalities) has Brookline's "A.Building Permits"
# line cleanly separated from the generic "Licenses And Permits" total
# only starting FY2023 (a DOR reporting-format change, not a real trend) -
# 3 years of usable data: FY23 $5,604,768, FY24 $4,322,503, FY25
# $4,439,224. Compared against DOR's own new-growth VALUE (not
# levy-applied $ - permit fees scale with gross construction cost/value,
# not the smaller post-tax-rate applied figure): FY23 2.43%, FY24 1.35%,
# FY25 1.49%, pooled 1.69%.
#
# **Why aggregate collections run below the 2.0% statutory rate - resolved
# 2026-09-15 from the Town's own permit records** (see
# `scripts/permit_analysis.py`). Two mechanisms, both directly measured
# across 51,854 permits:
#   1. **Public projects pay no permit fee**, and they are among the
#      largest construction projects in town. Fee-exempt permits are
#      **15.8% of all construction volume** FY2018-2026. Being tax-exempt
#      they add no new growth either, so they drop out of both sides.
#   2. **The effective rate declines with project size.** The MEDIAN permit
#      pays exactly $20.00 per $1,000, confirming the schedule, but the
#      aggregate effective rate falls monotonically: $19.44/$1,000 for
#      $25-100k permits, $18.74 for $100-500k, $17.88 for $500k-2M, $14.82
#      for $2-10M, $8.52 for permits over $10M. Excluding fee-exempt
#      permits, the pooled effective rate is $18.91/$1,000 (1.89%), close
#      to statutory.
# Estimated cost is **self-reported by the applicant**, which adds variance
# to any value-per-permit-dollar ratio derived from it - a reason to treat
# the coefficients here as central tendencies rather than precise figures.
#
# **The 2.0% constant is validated, not superseded.** Measured against DOR
# new-growth value across FY2019-2025 (8 years, vs the 3 DOR separates),
# permit fees invoiced are **2.09% pooled / 2.17% median**; DOR's reported
# cash receipts over FY23-25 give 1.69%. The statutory 2.0% sits inside
# that 1.69-2.09% band, so it stays as the point estimate. The two measures
# disagree almost entirely in FY2024 (invoiced $6.44M vs DOR $4.32M, a
# 1.49x gap sitting in a few very large commercial permits whose invoicing
# and cash receipt straddle the year end); FY2023 and FY2025 reconcile to
# within 1.2%. The FY2024 gap is unresolved - do not treat either series as
# authoritative for that year alone.
#
# **Known timing simplification**: this function derives fee revenue FROM
# the same year's new-growth dollars, treating the two as contemporaneous.
# They are not. The fee is collected at permit issuance; the assessed value
# appears about two fiscal years later (PERMIT_TO_ASSESSMENT_LAG_YEARS
# below). Fee revenue therefore leads its own new-growth figure by ~2
# years. The effect is small because permit volume is steady year to year,
# and correcting it would mean forecasting permit flow separately from new
# growth; left as a documented simplification rather than silently ignored.
BUILDING_PERMIT_RATE = 0.02  # $20/$1,000, through FY2026
BUILDING_PERMIT_RATE_FY2027 = 0.021  # $21/$1,000, effective July 1 2026 = FY2027
BUILDING_PERMIT_RATE_INCREASE_FY = 2027
BUILDING_PERMIT_RATE_ACTUAL_COLLECTIONS = 0.0169  # cross-check only, not used directly
BUILDING_PERMIT_RATE_INVOICED_FY19_25 = 0.0209  # cross-check, 8yr, from permit records
BUILDING_PERMIT_EFFECTIVE_RATE_ALL = 0.0159  # invoiced / construction cost, all permits
BUILDING_PERMIT_EFFECTIVE_RATE_FEEPAYING = 0.0189  # same, excluding fee-exempt permits
FEE_EXEMPT_SHARE_OF_CONSTRUCTION = 0.158  # Town/Housing Authority projects, FY2018-2026

# --- Permit-derived coefficients (new 2026-09-15, `scripts/permit_analysis.py`) ---
# Measured from the Town Building Department's own permit history joined to
# the assessment roll. These describe the OTHER direction of travel from
# building_permit_revenue() above: given construction activity, how much
# assessed value does it produce, and when.
#
# **Lag.** Value trajectory around a >=$500k building permit, net of
# town-wide appreciation, n=176 parcels: k=-1 1.001, k=0 1.000, k=+1 1.002,
# k=+2 1.242, k=+3 1.359, k=+4 1.384. Flat before and at issuance, a sharp
# break in year 2, ~90% complete by year 3. The flatness where nothing
# should happen is the validation that this is a real signal.
PERMIT_TO_ASSESSMENT_LAG_YEARS = 2
PERMIT_LAG_SHARE_BY_YEAR = {2: 0.62, 3: 0.30, 4: 0.08}  # of total eventual lift

# **Conversion, by segment.** DOR-certified new-growth value per $1 of
# permitted construction cost, FY2019-2025. Residential and commercial
# differ by a factor of ~3.6, which matters because commercial is 55% of
# construction dollars.
#   Residential: 1.305 (range 0.96-1.77, r=0.17)
#   Commercial : 0.363 (range 0.27-0.48, r=0.74)
# The commercial figure is the tighter and better-correlated of the two.
# Commercial property is assessed on capitalized income rather than cost,
# so fit-out spending moves the assessment only insofar as it moves rents.
# The residential figure exceeding 1.0 partly reflects that self-reported
# construction cost is a noisy denominator (see above); read it as "roughly
# dollar-for-dollar or a little better", not as a precise multiplier.
NEW_GROWTH_PER_PERMIT_DOLLAR_RES = 1.305
NEW_GROWTH_PER_PERMIT_DOLLAR_COM = 0.363

# **Detection threshold.** Parcel-level, renovation only (no units added),
# against a property-type-stratified baseline of unpermitted parcels:
# under $100k of permit spend a parcel is statistically indistinguishable
# from one with no permit at all (median growth 1.504 vs 1.511 baseline,
# 5.3% vs 4.4% beating baseline by >20%). The signal appears at $100-500k
# (18.0% beating) and is unmistakable above $500k (median 1.929, 57.2%
# beating). This is why bottom-up renovation detection from the assessment
# roll fails at the low end, and it bounds what any parcel-level renovation
# estimate can see.
RENOVATION_DETECTION_THRESHOLD = 500_000
RENOVATION_LIFT_ABOVE_THRESHOLD = 0.417  # median growth factor vs type baseline
BUILDING_PERMITS_2025_ACTUAL = 4_439_224  # subtracted from the local_receipts base below to avoid double-counting


def building_permit_rate(year):
    """Statutory permit fee rate for a given fiscal year.

    Brookline raised the rate from $20 to $21 per $1,000 of estimated
    construction cost effective July 1, 2026 - the first day of FY2027.
    """
    return (
        BUILDING_PERMIT_RATE_FY2027
        if year >= BUILDING_PERMIT_RATE_INCREASE_FY
        else BUILDING_PERMIT_RATE
    )


def building_permit_revenue(res_new_dollars, res_reno_dollars, com_new_dollars, com_reno_dollars, year=2026):
    """
    One year's building-permit revenue from that year's new-growth $ -
    the four *real estate* categories only (res-new, res-reno, com-new,
    com-reno). Personal property is deliberately excluded - buying
    equipment/furniture doesn't require a building permit, only actual
    construction/renovation does (a real refinement enabled by separating
    personal property out of what used to be one blended "com_other"
    bucket - see TREND_COM_PP_PCT). Converts each category's *applied*
    (levy) dollars back to *value* (gross assessed value/construction-cost)
    dollars via res_tax_rate(year)/com_tax_rate(year) (drifting, not flat -
    see "Tax rate drift" above), since permit fees are a % of construction
    value, not of the smaller levy-applied figure. This is a one-time fee
    tied to that year's construction activity, not a persistent addition
    to the tax base - added fresh to local_receipts each year, no
    increment-vs-level concern (unlike CHCA/property tax).
    """
    res_value = (res_new_dollars + res_reno_dollars) / res_tax_rate(year)
    com_value = (com_new_dollars + com_reno_dollars) / com_tax_rate(year)
    return building_permit_rate(year) * (res_value + com_value)


# --- Meals tax (added 2026-08-30, Ben) ---
# Ben: too hard to cleanly attribute a "restaurant share" of new commercial
# sqft from parcel data (see chat - restaurants are almost always tenants
# inside RES/COMM or RETAIL STORE-classified buildings, not their own
# assessed class), so grow meals tax via two components instead: (1) an
# "organic" trend (inflation/increased spending at existing restaurants)
# and (2) a rough increment tied to new commercial sqft, using the
# *average* meals-tax intensity of Brookline's *existing* commercial stock
# as a stand-in for "how much meals tax does new commercial space
# generate" (rather than trying to isolate a restaurant-specific rate the
# data can't cleanly support).
#
# Meals tax pulled out of the generic `local_receipts` CAGR to avoid
# double-counting its own trend twice (small effect - meals tax is only
# ~4% of total local receipts - but the ex-meals CAGR is computed properly
# rather than skipped, given how many increment/double-counting bugs this
# session already caught).
MEALS_TAX_2019 = 1_249_434
MEALS_TAX_2025 = 1_768_323
MEALS_TAX_ORGANIC_CAGR = 0.0596  # FY19-25 actual CAGR (same window as local_receipts_cagr_actual)
MEALS_TAX_INTENSITY_PER_SQFT = 0.2778  # FY2025 meals tax / 6,364,845 sqft existing taxable commercial stock


# --- Investment income (Ben, 2026-10-14, from the independent review) ---
# Interest on Town cash rose from $1,317,178 in FY2019 to $5,146,469 in
# FY2025 (DOR itemized receipts), nearly half the FY2019-25 rise in all
# local receipts, after negative years in FY2021-22. FP27 p.III-98 puts it
# down to "historically high interest rates"; the January 2026 LRFP calls
# interest income "unreliable & will lessen as ARPA funds are spent" (about
# $44M of ARPA cash, spent by December 2026). Growing it with the other
# receipts would carry a peak-rate level forward as a trend, so it is pulled
# out of the residual and its CAGR and held flat at the Town's own FY2027
# budget for investment income (FP27 p.III-98). Excluding it takes the
# residual CAGR from 3.31% to 1.76%.
INVESTMENT_INCOME_2019 = 1_317_178
INVESTMENT_INCOME_2025 = 5_146_469
INVESTMENT_INCOME_FLAT = 934_259  # FY2027 recommended, investment income only (excludes tax-title interest)


def local_receipts_residual(hist):
    """FY2025 receipts not modeled on their own (ex meals, permits and
    investment income) and their FY2019-25 growth (ex meals and investment
    income; permits are not separable before FY2023)."""
    t19 = float(hist[2019]["local_receipts_act_total"])
    t25 = float(hist[2025]["local_receipts_act_total"])
    resid = t25 - MEALS_TAX_2025 - BUILDING_PERMITS_2025_ACTUAL - INVESTMENT_INCOME_2025
    rate = cagr(t19 - MEALS_TAX_2019 - INVESTMENT_INCOME_2019,
                t25 - MEALS_TAX_2025 - INVESTMENT_INCOME_2025, 6)
    return resid, rate


def meals_tax_organic(year):
    return MEALS_TAX_2025 * (1 + MEALS_TAX_ORGANIC_CAGR) ** (year - 2025)


def meals_tax_from_new_commercial(cumulative_new_commercial_sqft):
    """
    Incremental meals tax from cumulative new commercial sqft built since
    the forecast start - a stock effect (once built, it keeps generating
    meals tax every year after), unlike building permits' one-time flow.
    """
    return MEALS_TAX_INTENSITY_PER_SQFT * cumulative_new_commercial_sqft


# --- Residential/commercial trailing-5yr new-growth rates (DOR-certified,
# `output/brookline_historical_financials_fy05_25.csv`), and the share of
# each that's identified new construction vs. renovation/other ---
# FY2022-26 (2026-10-13, Ben: the window moves forward now that FY2026 is certified; was FY2021-25,
# 0.839% and 0.438%). DLS new growth report: residential applied / prior levy limit, and the rest.
RES_TRAILING_5YR_PCT = 0.00851  # 0.851%/yr of prior levy (rounded to 0.001 point, as the workbook does)
COM_TRAILING_5YR_PCT = 0.00384  # 0.384%/yr of prior levy - this is DOR's
# "CIP" total (Commercial + Industrial + Personal Property combined, not
# commercial real estate alone - Industrial is negligible in Brookline).
# Share of residential new growth that is net new homes (method A, 2026-10-12): set so FY2026 carries
# the permit pace (about 105 homes a year, 2016-2025) at the blended value per home, against the trend
# rate on the FY2025 levy limit. Total residential new growth stays at its trend rate; the rest is
# renovation, including houses rebuilt as houses. Replaces 0.2867, the FY2021-25 classifier share (history
# below), which counted only each new building's first roll and FY2021's first-time unit recordings.
def _levy_limit_2025():
    with open(_Path(__file__).resolve().parents[1] / "output" / "brookline_historical_financials_fy05_25.csv") as f:
        r = {int(x["fiscal_year"]): x for x in csv.DictReader(f)}[2025]
    return float(r["total_levy"]) - float(r["debt_exclusions"])
RES_NEW_SHARE_OF_RES = round(HOMES_TREND_PER_YEAR * RES_VALUE_PER_UNIT * RES_TAX_RATE
                             / (RES_TRAILING_5YR_PCT * _levy_limit_2025()), 4)
# Earlier value: 0.2867, updated 2026-08-30 from 0.209, then FY2021-25
# trailing-5yr (`land-value-map/scripts/split_new_growth_by_type.py`,
# extended through FY2025 the same day) - a real, robust shift: each of the
# 5 years' own detection rate (3.1%/none-real/etc. per year, see
# `.claude/memorialized.md` 2026-08-30) supports it, not driven by one
# outlier year.
COM_NEW_SHARE_OF_COM = 0.0220  # updated 2026-08-30 (same day, second pass)
# from 0.013. First pass that day found the naive FY2021-25 extension moved
# this to an untrustworthy 0.0013, driven by one parcel (083-03, FY2025)
# whose res->commercial conversion got counted as one *netted* event
# (residential value lost minus commercial value gained), producing a
# spurious *negative* "new construction" dollar figure that year. Root
# fix (`classify.py`, same day, Ben's proposal): decompose a conversion
# into two events - a residential loss and a commercial gain, using
# `res_value`/`com_value` separately (already tracked per-parcel) rather
# than the netted total - scoped narrowly to cases with a second,
# corroborating physical signal (res_units actually dropping), not
# applied to every parcel whose res/com value split shifts (most of those
# ~70 cases are the assessor reallocating value on a building that didn't
# physically change, not real conversions - see `.claude/memorialized.md`,
# 2026-08-30). With that fix, the real trailing-5yr rate is 0.0220 - HIGHER
# than the previous 0.013, not lower: the bug was silently netting away
# commercial construction value whenever it coincided with a residential
# teardown (also found in FY2022, previously undercounted $795,600 vs. the
# real $2,826,400).

# --- Personal property (added 2026-08-30, Ben) ---
# Confirmed via the Town's own FY2022-2025 Tax Classification Hearing
# presentations (Board of Assessors - see module docstring / SOURCES.md)
# that COM_TRAILING_5YR_PCT bundles personal property (business equipment/
# furniture/fixtures - tracked in a wholly separate roll, not in the
# parcel-level CAMA extract land-value-map uses) together with real
# commercial real estate. Personal property's own new-growth rate, as %
# of prior levy (4yr avg, FY2022-2025 - the only years this breakdown is
# available; a shorter window than the 5yr one used elsewhere for
# res/commercial due to data availability):
#   FY22 0.2374%   FY23 0.2164%   FY24 0.2629%   FY25 0.2011%   avg 0.2295%
# Notably stable year to year (unlike "Commercial" real estate, which
# swung from >$1M/yr new-growth tax down to <$100K/yr over the same
# window) - personal property is driven by business/equipment activity,
# not construction, so it gets its own trend rate, **independent of
# com_new_sqft** (Ben's direction - it isn't a sqft-driven or
# zoning-driven phenomenon, so it stays flat at trend in every scenario,
# same treatment as res_reno_pct - not something peer-target scenarios
# solve for).
# FY2026 (classification hearing, $837,444 on a prior levy limit of $293.1M; permit_leading_indicator.py) adds
# 0.2857% to the window: FY2022-26 average 0.2407% (2026-10-13; was 0.2295%, FY2022-25).
TREND_COM_PP_PCT = 0.002407

TREND_RES_NEW_PCT = RES_TRAILING_5YR_PCT * RES_NEW_SHARE_OF_RES
TREND_RES_RENO_PCT = RES_TRAILING_5YR_PCT * (1 - RES_NEW_SHARE_OF_RES)
TREND_COM_NEW_PCT = COM_TRAILING_5YR_PCT * COM_NEW_SHARE_OF_COM
# com_reno is now the *residual after removing personal property too* -
# real estate renovation/undetected expansion specifically, not a blend
# of that with personal property the way the old "com_other" was.
TREND_COM_RENO_PCT = COM_TRAILING_5YR_PCT - TREND_COM_NEW_PCT - TREND_COM_PP_PCT

# Peer-target total new-growth rate: 80th percentile statewide, trailing-5yr
# window (matches the window trend_corrected actually uses) - recomputed
# 2026-08-28 directly from the DLS statewide dataset, see memorialized.md.
PEER_TARGET_PCT = 0.02032  # FY2022-26 (2026-10-13; was 0.01974, FY2021-25)

# {name: {"params": (res_new, res_reno, com_new, com_reno, com_pp), "label": str}}
EXTRA_SCENARIOS = {}
# Fewer new homes (Ben, 2026-10-14): what the budget looks like if only half the expected new homes
# are built, or none, with renovation, commercial space and business equipment at their trend.
HOMES_BUILT = {"half": 0.5, "none": 0.0}


def homes_params(params, share):
    """The same new growth with the new-homes part scaled to `share`."""
    return (params[0] * share,) + tuple(params[1:])


def homes_scenarios():
    trend = (TREND_RES_NEW_PCT, TREND_RES_RENO_PCT, TREND_COM_NEW_PCT, TREND_COM_RENO_PCT, TREND_COM_PP_PCT)
    return {f"trend_homes_{k}": {"params": homes_params(trend, h), "label": f"trend, new homes {k}"}
            for k, h in HOMES_BUILT.items()}

# --- Tax rate drift (added 2026-08-30, Ben; CIP-shift-bounded fix 2026-09-01) ---
# RES_TAX_RATE/COM_TAX_RATE above are FY2026-basis levels, held flat by an
# earlier version of this script for the whole FY2026-2040 window. Ben's
# question: since Prop 2.5 caps the LEVY (dollars), not the rate, and
# assessed value isn't capped, shouldn't the *rate* itself drift over
# time as the levy and the tax base grow at different speeds? Yes - but
# NOT by letting each class's rate drift independently off its own
# appreciation rate, per the fix below.
#
# **The independent-drift version (2026-08-30) was wrong, and demonstrably
# so, not just "likely unsupportable."** It applied Town-wide levy growth
# against each class's OWN value-appreciation rate separately - so
# residential (appreciating faster than the levy, 4.96%/yr vs ~3.78%/yr)
# drifted down while commercial (appreciating slower, 1.28%/yr) drifted
# up, with nothing tying the two together. Run out to FY2040 that implies
# a commercial/residential rate RATIO of 2.72x (COM_TAX_RATE rising ~41%,
# RES_TAX_RATE falling ~15%, starting from a 1.65x ratio today) - not
# merely "a lot," but flatly outside what Massachusetts law allows.
#
# The residential/commercial split is a Select Board policy choice each
# year (the "CIP shift factor," a.k.a. Minimum Residential Factor),
# governed by **M.G.L. c.40 §56** (not c.59 §5C, which is the unrelated
# residential-exemption statute - miscited in the 2026-08-30 version of
# this comment) - the shift a town selects can raise the CIP class's rate
# to at most **175% of the single (uniform) rate**, equivalently capping
# CIP's levy share at 150% of its share of town-wide assessed value, with
# residential paying at least 65% of its value share in exchange (source:
# MMA's "Prop 2½ and Municipal Tax Classification" summary of c.40 §56 -
# https://www.mma.org/wp-content/uploads/2024/05/MMA-Prop-2-1_2-Municipal-Tax-Classification.pdf).
# **Brookline's actual FY2026 shift is 1.746** - confirmed directly from
# `data/FY2026-Classification-Hearing%20Presentation-FINAL.pptx` (slide 9:
# the Select Board's adopted 20%-residential-exemption scenario pairs a
# 1.746 shift with the certified $10.24 residential rate, matching
# RES_TAX_RATE's real-dollar anchor exactly) - **99.8% of the 1.75
# statutory ceiling**. There is essentially no room left for the Select
# Board to shift further burden onto CIP even if it wanted to; a model
# that lets the commercial rate keep climbing on its own trajectory has
# no basis in what the policy lever can actually do.
#
# **Fix**: hold the CIP-shift ratio (COM_TAX_RATE / RES_TAX_RATE, ~1.651
# for this script's trailing-5yr-smoothed anchors) CONSTANT across the
# forecast - the reasonable "no future policy change" baseline, consistent
# with how every other policy lever in this project (overrides, the
# residential exemption itself) is held at its current setting rather than
# assumed to move, and doubly justified here since the lever is already
# pinned against its legal ceiling. Only the *blended* Town-wide rate
# drifts, at the ratio of levy growth to a VALUE-WEIGHTED blend of both
# classes' appreciation rates (not either class's rate alone) - both
# `res_tax_rate(year)` and `com_tax_rate(year)` move together, by
# construction preserving today's ratio at every future year.
LEVY_GROWTH_RATE = 0.025 + RES_TRAILING_5YR_PCT + COM_TRAILING_5YR_PCT  # ~3.777%/yr

# FY2026 assessed-value shares (Residential vs. combined CIP), from the same
# Classification Hearing presentation (slide 4): Residential $30,758,464,684,
# Combined CIP $3,073,844,529, of $33,832,309,213 total - used only to weight
# the blended appreciation rate below, not as a running value time series.
RES_VALUE_SHARE_FY26 = 30_758_464_684 / 33_832_309_213  # 0.9091
CIP_VALUE_SHARE_FY26 = 1 - RES_VALUE_SHARE_FY26  # 0.0909
BLENDED_VALUE_APPRECIATION_RATE = (
    RES_VALUE_SHARE_FY26 * RES_VALUE_APPRECIATION_RATE + CIP_VALUE_SHARE_FY26 * COM_VALUE_APPRECIATION_RATE
)  # ~4.63%/yr - both classes' rates drift off this ONE blended figure, not their own


def res_tax_rate(year):
    return RES_TAX_RATE * ((1 + LEVY_GROWTH_RATE) / (1 + BLENDED_VALUE_APPRECIATION_RATE)) ** (year - 2026)


def com_tax_rate(year):
    return COM_TAX_RATE * ((1 + LEVY_GROWTH_RATE) / (1 + BLENDED_VALUE_APPRECIATION_RATE)) ** (year - 2026)

# --- Chestnut Hill Commercial Area (CHCA) - see module docstring ---
# Zoning approved by Town Meeting 217-20, May 28-29, 2026 (confirmed, not
# speculative - supersedes the earlier ERSC report's "may be brought to
# Spring 2026 TM" framing). City Realty, 1280-1330 Boylston St, 5-acre site:
# 3 buildings (14/12/7 stories), 200-room hotel, 266 apartments/condos,
# medical office, ground-floor retail - >50% of floor area required
# commercial by the zoning itself. Construction "not planned to begin until
# 2028" at the earliest per the developer (Bisnow, Brookline.News,
# 2026-05-29) - assumes "all the pieces fall into place perfectly."
#
# **Gross revenue figures, split by scenario source (2026-08-30, Ben)**:
# the ERSC report's Appendix (p.551-555) has RKG's actual fiscal-impact
# model output for 5 scenarios - 3 authored by City Realty (the developer,
# "CR Scenario 1/2/3"), 1 by EDAB (Town's Economic Development Advisory
# Board), 1 by RKG itself (the independent consultant Town staff hired to
# build the model) - broken into 4 revenue lines each. Ben transcribed it
# into `data/Brookline property tax revenue over 20 years.xlsx`, "Fiscal
# Impact Model" tab. Ben's observation: EDAB and RKG (Town-side/independent)
# came in noticeably more conservative than City Realty's own 3 scenarios -
# and his call: use the **RKG scenario** (single, independent, most
# conservative-adjacent) for the "keep what we have" baseline
# (`baseline_revenue_forecast.py`), and the **average of the 3 CR
# scenarios** (the developer's own, presumably closer to what actually gets
# built) for this script's own scenarios - reflecting the baseline's
# conservative framing vs. Phase 2's role exploring what growth could
# realistically look like.
#
#   Revenue line              RKG scenario    CR average (3 scenarios)
#   Residential property tax    $1,841,088       $3,030,198
#   Commercial property tax     $1,317,086       $2,378,043
#   -> Property tax subtotal    $3,158,174       $5,408,241
#   Local Rooms Tax                $381,060         $732,905
#   Motor Vehicle Excise            $99,375         $185,000
#   -> Local receipts subtotal     $480,435         $917,905
#
# ("NET NEW ANNUAL MUNICIPAL REVENUES" is RKG's own label for this - *gross*
# new revenue, before subtracting Town service costs; "net new" as in
# incremental, not net-of-costs. The separate "SURPLUS/(DEFICIT)" row
# further down the table IS net-of-costs and is NOT what belongs in a
# revenue-only forecast.) Property tax (res + commercial real/personal) is
# what counts toward the Prop 2.5 levy limit; Rooms Tax + MV Excise are
# **Local Receipts**, a separate revenue category that does not count
# toward the levy limit at all - each stream goes to its correct line.
#
# No public building-by-building revenue phasing was found for either
# stream - both ramp on the same straight-line schedule (a stated
# simplification), landing on the same "~7yr to completion + 18mo to
# stabilization" span the ERSC report described.
CHCA_PROPERTY_TAX_RKG = 3_158_174        # RKG's own scenario - used in baseline_revenue_forecast.py
CHCA_LOCAL_RECEIPTS_RKG = 480_435
CHCA_PROPERTY_TAX_CR_AVG = 5_408_241     # avg of City Realty's 3 scenarios - used in this script
CHCA_LOCAL_RECEIPTS_CR_AVG = 917_905
# Timing follows the Planning Department's June 2026 pipeline (Development Look-Ahead,
# slide 3): permitting FY2027-28, construction FY2029-31, new property and rooms tax
# revenue from FY2032. Revenue and service costs ramp 1/3, 2/3, full over FY2032-34.
# (Until 2026-09-30: revenue from FY2029, full by FY2033, costs full by FY2034.)
CHCA_CONSTRUCTION_START_YEAR = 2032  # first FY with revenue (name kept for callers)
CHCA_FULL_STABILIZATION_YEAR = 2034  # first FY fully on the roll (was 2035, used as a span of 3)


def chca_ramp_share(year):
    """Share of the stabilized Chestnut Hill project on the roll in `year`; used for
    both revenue here and service costs in expense_driver_forecast.py."""
    if year < CHCA_CONSTRUCTION_START_YEAR:
        return 0.0
    span = CHCA_FULL_STABILIZATION_YEAR - CHCA_CONSTRUCTION_START_YEAR + 1
    return min((year - CHCA_CONSTRUCTION_START_YEAR + 1) / span, 1.0)

# This script's own scenarios use the CR (developer) average - see rationale above.
CHCA_PROPERTY_TAX_AT_STABILIZATION = CHCA_PROPERTY_TAX_CR_AVG
CHCA_LOCAL_RECEIPTS_AT_STABILIZATION = CHCA_LOCAL_RECEIPTS_CR_AVG
CHCA_PROPERTY_TAX_RES_SHARE = 3_030_198 / CHCA_PROPERTY_TAX_CR_AVG   # residential part of the CR average

# Dollars of the estimates (Ben, 2026-10-14, from the independent review). RKG built the model on the
# FY2025 budget (ERSC report, Appendix E questions to Planning staff, December 2025), so its tax and
# receipts figures are read as FY2025 dollars. Until then they were entered unchanged in FY2032-34
# and the receipts stayed flat in dollars forever. Now:
#   property tax: each third enters the levy at the assessed value of its entry year, so it is
#     indexed from FY2025 by each class's value growth times the drift in its tax rate (the same
#     appreciated-value and tax-rate paths every other piece of new growth uses). Once on the roll
#     it grows with the levy, 2.5% a year, like any other property.
#   rooms tax and motor vehicle excise: grow from FY2025 at the rate of the other local receipts
#     (local_receipts_residual(), 1.76%). The rooms tax category alone grew 9.3% a year in
#     FY2019-25, but that was mostly new hotel rooms opening, not a price trend.
CHCA_DOLLAR_YEAR = 2025


def chca_value_index(year, res_share=None):
    """New growth dollars for property valued in FY2025 when it enters the roll in `year`."""
    rs = CHCA_PROPERTY_TAX_RES_SHARE if res_share is None else res_share
    drift = (1 + LEVY_GROWTH_RATE) / (1 + BLENDED_VALUE_APPRECIATION_RATE)
    n = year - CHCA_DOLLAR_YEAR
    return rs * ((1 + RES_VALUE_APPRECIATION_RATE) * drift) ** n \
        + (1 - rs) * ((1 + COM_VALUE_APPRECIATION_RATE) * drift) ** n


_CHCA_RECEIPTS_GROWTH = []


def chca_receipts_growth():
    """The base rate of the other local receipts, computed directly (not through cagr(), which the
    Explorer's tests patch to move the receipts setting; the setting does not move Chestnut Hill)."""
    if not _CHCA_RECEIPTS_GROWTH:
        h = read_historical()
        t19, t25 = (float(h[y]["local_receipts_act_total"]) for y in (2019, 2025))
        _CHCA_RECEIPTS_GROWTH.append(((t25 - MEALS_TAX_2025 - INVESTMENT_INCOME_2025)
                                      / (t19 - MEALS_TAX_2019 - INVESTMENT_INCOME_2019)) ** (1 / 6) - 1)
    return _CHCA_RECEIPTS_GROWTH[0]


def chca_property_tax_increment(year, stabilized_amount=None):
    """The year-over-year *change* in CHCA's property-tax level - this, not the level, is what
    belongs inside a recursive levy computation (levy(t) = levy(t-1)*1.025 + new_growth(t)):
    the share entering this year at this year's value. (See the 2026-08-29 note below on why
    the increment, not the level.)"""
    if stabilized_amount is None:
        stabilized_amount = CHCA_PROPERTY_TAX_AT_STABILIZATION
    share = chca_ramp_share(year) - chca_ramp_share(year - 1)
    return share * stabilized_amount * chca_value_index(year) if share else 0.0


def chca_property_tax(year, stabilized_amount=None):
    """The cumulative CHCA property-tax revenue *level* in `year`: each year's entry carried
    forward with the levy's 2.5%. Reads the module-level amounts at call time so callers can
    vary them."""
    return sum(chca_property_tax_increment(s, stabilized_amount) * 1.025 ** (year - s)
               for s in range(CHCA_CONSTRUCTION_START_YEAR, year + 1))


def chca_local_receipts(year, stabilized_amount=None):
    """The cumulative CHCA local-receipts (rooms tax + MV excise) *level* in `year`."""
    if stabilized_amount is None:
        stabilized_amount = CHCA_LOCAL_RECEIPTS_AT_STABILIZATION
    share = chca_ramp_share(year)
    return stabilized_amount * share * (1 + chca_receipts_growth()) ** (year - CHCA_DOLLAR_YEAR) if share else 0.0


# Backward-compatible alias - this script's own use always means the CR-average figure.
chca_revenue = chca_property_tax


# Why the increment and not the level (2026-08-29): adding the full level every year double-,
# triple-, ...-counts it, since the previous year's level is already embedded in levy(t-1) by the
# time year t's recursion step runs. Caught via a sanity trace of peer_target_residential_led's
# year-over-year growth rate, which ran ~5.3-5.7%/yr instead of the expected steady-state ~4.47%
# (2.5% statutory + 1.974% new growth) even after CHCA had fully stabilized - the tell.
chca_increment = chca_property_tax_increment  # backward-compatible alias


def chca_local_receipts_increment(year, stabilized_amount=None):
    return chca_local_receipts(year, stabilized_amount) - chca_local_receipts(year - 1, stabilized_amount)


# State aid (Ben, 2026-10-14, "be conservative"): the Town's FY2026 figure and the adopted FY2027
# budget's, then 2.5% a year, the rate in the Town's own long-range plan. The FY2015-25 rate (3.54%)
# includes FY2019's one-year 8.6% rise; without it 3.0%, FY2019-25 2.0%, FY2005-25 1.9%.
STATE_AID_GROWTH = 0.025


def state_aid_path(town, years, growth=None):
    import fy2027_adopted as _fy27
    g = STATE_AID_GROWTH if growth is None else growth
    known = {2026: float(town["state_aid"][2026]), 2027: float(_fy27.STATE_AID)}
    return {y: known[y] if y in known else known[2027] * (1 + g) ** (y - 2027) for y in years}


def read_town_forecast():
    out = {}
    with open(TOWN_FORECAST_FILE) as f:
        for row in csv.DictReader(f):
            if row["category"] != "revenue":
                continue
            out[row["subcategory"]] = {y: float(row[str(y)]) for y in range(2026, 2032)}
    out["property_taxes"] = apply_may_2026_override(out["property_taxes"])
    return out


def read_historical():
    with open(HISTORICAL_FILE) as f:
        return {int(row["fiscal_year"]): row for row in csv.DictReader(f)}


def cagr(start, end, years):
    return (end / start) ** (1 / years) - 1


def new_growth_dollars(year, prior_total, res_new_pct, res_reno_pct, com_new_pct, com_reno_pct,
                        com_pp_pct, include_chca=True, res_value_per_unit=RES_VALUE_PER_UNIT):
    """
    One year's new-growth $ (applied to the levy limit) from the 5
    %-of-prior-levy categories (res-new, res-reno, com-new, com-reno,
    com-personal-property), plus CHCA. `total` is what actually belongs
    in a recursive levy computation - it uses CHCA's year-over-year
    *increment*, not its cumulative level (see chca_increment's docstring
    for why: the level is already embedded in prior years' levy once it
    first appears, so re-adding the full level every year would
    double-count it). The returned `chca_level` component is the
    cumulative level, for display only (e.g. "$1.1M, $2.2M, ...$5.5M" is a
    more readable progression than the increment "$1.1M, $1.1M, ...$0").
    Returns the total and a components tuple whose implied_units/implied_sqft
    entries are the *implied physical count* for that year (derived from
    the appreciated $/unit or $/sqft for `year`), not an input -
    com_pp has no physical-count analog (personal property isn't sqft- or
    unit-denominated), so it's just a dollar figure.
    """
    res_new = res_new_pct * prior_total
    res_reno = res_reno_pct * prior_total
    com_new = com_new_pct * prior_total
    com_reno = com_reno_pct * prior_total
    com_pp = com_pp_pct * prior_total
    chca_delta = chca_increment(year) if include_chca else 0.0
    chca_level = chca_revenue(year) if include_chca else 0.0

    implied_units = res_new / (appreciated_res_value_per_unit(year, res_value_per_unit) * res_tax_rate(year))
    implied_sqft = com_new / (appreciated_com_value_per_sqft(year) * com_tax_rate(year))

    total = res_new + res_reno + com_new + com_reno + com_pp + chca_delta
    return total, (res_new, res_reno, com_new, com_reno, com_pp, chca_level, implied_units, implied_sqft)


def run_property_tax(town_property_taxes, town_debt_exclusion, hist_2025_total, hist_2025_debt_exclusion,
                      params, include_chca=True, res_value_per_unit=RES_VALUE_PER_UNIT):
    """
    Replicates trend_corrected's delta method for FY26-31 (so known
    committed overrides/debt exclusions embedded in the Town's own figures
    stay identical) and geometric compounding for FY32-40, but with
    new-growth $ computed from the 5-category %-mix plus CHCA.

    Fixed 2026-09-01 (Ben - found while building the FY26-40 extension of
    `existing_vs_new_property_tax.py`, which needs a clean levy-limit-vs-
    debt-exclusion split as an input and exposed two real bugs here that
    predate that request): this function used the COMBINED total
    (`town_property_taxes`, levy limit + debt exclusion) both as (a) the
    base new-growth % is applied against, and (b) what gets geometrically
    compounded for FY2032-2040. Both are wrong the same way
    `baseline_revenue_forecast.py`'s Phase 1 model already found and fixed
    for itself on 2026-08-30 ("Debt exclusion carve-out"), but that fix was
    never mirrored here:
      (a) RES_TRAILING_5YR_PCT/COM_TRAILING_5YR_PCT (and everything derived
          from them) are calibrated as new_growth/`prior_levy_limit` -
          levy-limit-only, per `brookline_historical_financials_fy05_25.csv`
          - so applying them to a base that also includes debt exclusion
          overstated every category's new-growth $ by roughly debt
          exclusion's share of the total (~8-9%, every year, not just
          FY2032+ - this affected FY2026-2031 too, since `diff` derives
          from the same mis-based `ng`).
      (b) FY2032-2040 compounded the ENTIRE FY2031 total (including its
          ~$36.7M of embedded debt exclusion) at 2.5%+new-growth - debt
          exclusions are dollar-for-dollar bond-service matches outside
          the 2.5% cap, they don't organically grow. Concretely, this
          alone overstated FY2040's trend_continues total by ~$21.4M
          (~3.9%) versus the correctly-decomposed figure, and broke this
          script's own stated claim that trend_continues is "numerically
          identical to Phase 1's trend_corrected" (it wasn't, off by that
          same amount).
    Fix: track the levy-limit-only ("operating") base separately from
    debt exclusion throughout, exactly mirroring baseline_revenue_
    forecast.py's convention - debt exclusion held flat at the FY2031
    (ANCHOR_YEAR) level for FY2032-2040, only the operating component
    compounds, `prop_tax = operating + debt_exclusion` at every year.
    """
    res_new_pct, res_reno_pct, com_new_pct, com_reno_pct, com_pp_pct = params
    prior_base = {2025: hist_2025_total - hist_2025_debt_exclusion}
    prior_base.update({y: town_property_taxes[y] - town_debt_exclusion[y] for y in TOWN_YEARS})

    diff = {2025: 0.0}
    ng_by_year = {}
    for y in range(2026, 2032):
        # the rates apply to this forecast's own levy: the Town's plus the difference carried so far
        # (2026-10-13, Ben: the Town's levy carries only its own $2.5M of new growth)
        ng, components = new_growth_dollars(y, prior_base[y - 1] + diff[y - 1], res_new_pct, res_reno_pct,
                                             com_new_pct, com_reno_pct, com_pp_pct, include_chca,
                                             res_value_per_unit)
        if y == NG_BUDGETED_YEAR:
            # FY2027 at the Town's budgeted $2.5M (Ben, 2026-10-14): the adopted budget carries it, and
            # the 2024-25 permits behind it were the lowest since at least 2018. Every category is
            # scaled to that total, so units, square feet and permit fees stay consistent with it.
            k = NEW_GROWTH_TOWN / ng
            components = tuple(c * k for c in components)
            ng = NEW_GROWTH_TOWN
        ng_by_year[y] = (ng, components)
        # FY2026 is certified, and the Town plan's FY2026 levy already carries the actual $3,561,227
        # (LRFP revenue table, "New Growth 3,561,227"), so no difference that year (fixed 2026-10-14;
        # the 2026-10-13 version added certified - $2.5M on top, counting it twice)
        diff[y] = diff[y - 1] * 1.025 + (0.0 if y == 2026 else ng - NEW_GROWTH_TOWN)

    operating, debt_exclusion, prop_tax = {}, {}, {}
    for y in TOWN_YEARS:
        debt_exclusion[y] = town_debt_exclusion[y]
        operating[y] = town_property_taxes[y] - town_debt_exclusion[y] + diff[y]
        prop_tax[y] = operating[y] + debt_exclusion[y]
    for y in EXTEND_YEARS:
        ng, components = new_growth_dollars(y, operating[y - 1], res_new_pct, res_reno_pct,
                                             com_new_pct, com_reno_pct, com_pp_pct, include_chca,
                                             res_value_per_unit)
        ng_by_year[y] = (ng, components)
        operating[y] = operating[y - 1] * 1.025 + ng
        debt_exclusion[y] = debt_exclusion[ANCHOR_YEAR]
        prop_tax[y] = operating[y] + debt_exclusion[y]

    return prop_tax, ng_by_year, operating, debt_exclusion


def main():
    town = read_town_forecast()
    hist = read_historical()
    hist_2025_total = float(hist[2025]["total_levy"])
    hist_2025_debt_exclusion = float(hist[2025]["debt_exclusions"])

    # State aid / local receipts / other funds / free cash: identical to
    # Phase 1's trend_corrected scenario across every new-growth scenario
    # here - this script only varies the new-growth mix, so it only varies
    # property tax. Reproduced from baseline_revenue_forecast.py.
    # Meals tax AND building permits are pulled out and modeled separately
    # (see MEALS_TAX_*/BUILDING_PERMIT_* above) - the "residual" base/CAGR
    # here is what's left after removing both, to avoid double-counting
    # each one's own trend on top of the explicit formula-based version.
    # Building permits aren't cleanly separable in the FY2019 endpoint (DOR
    # only split "A.Building Permits" out starting FY2023 - before that
    # it's bundled into a generic "Licenses And Permits" total with no
    # sub-split), so only the FY2025 *level* is subtracted before growing
    # the residual at the ex-meals CAGR - a stated approximation, not a
    # fully clean ex-permits growth rate.
    # Investment income is pulled out too and held flat (INVESTMENT_INCOME_FLAT).
    local_receipts_2025_residual, local_receipts_cagr_ex_meals = local_receipts_residual(hist)

    state_aid = state_aid_path(town, FORECAST_YEARS)
    other_funds = dict(town["other_available_funds"])
    free_cash = dict(town["free_cash"])
    import fy2027_adopted as _fy27
    other_funds[2027] = _fy27.OTHER_AVAILABLE_FUNDS   # adopted FY2027 budget, not the Jan LRFP
    for _y, _d in _fy27.OVERRIDE_STABILIZATION_DRAW.items():   # FY2027 deposit drawn over 3 yrs
        other_funds[_y] += _d
    for y in EXTEND_YEARS:
        other_funds[y] = other_funds[ANCHOR_YEAR]
        free_cash[y] = free_cash[ANCHOR_YEAR]

    print(f"trend_continues percentages: res-new {TREND_RES_NEW_PCT:.4%} + res-reno "
          f"{TREND_RES_RENO_PCT:.4%} + com-new {TREND_COM_NEW_PCT:.4%} + com-reno "
          f"{TREND_COM_RENO_PCT:.4%} + com-personal-property {TREND_COM_PP_PCT:.4%} = "
          f"{TREND_RES_NEW_PCT+TREND_RES_RENO_PCT+TREND_COM_NEW_PCT+TREND_COM_RENO_PCT+TREND_COM_PP_PCT:.4%}")

    # Solve res_new_pct / com_new_pct to hit PEER_TARGET_PCT, holding the
    # other 3 categories (res-reno, com-reno, com-pp - none of them
    # construction/policy levers) at trend. Pure algebra now that
    # everything is %-of-the-same-base - no representative-base anchoring
    # needed.
    OTHER_FIXED = TREND_RES_RENO_PCT + TREND_COM_RENO_PCT + TREND_COM_PP_PCT
    res_led_new_pct = PEER_TARGET_PCT - (OTHER_FIXED + TREND_COM_NEW_PCT)
    com_led_new_pct = PEER_TARGET_PCT - (OTHER_FIXED + TREND_RES_NEW_PCT)
    trend_total_pct = (TREND_RES_NEW_PCT + TREND_RES_RENO_PCT + TREND_COM_NEW_PCT
                        + TREND_COM_RENO_PCT + TREND_COM_PP_PCT)
    gap_pct = PEER_TARGET_PCT - trend_total_pct
    balanced_res_new_pct = TREND_RES_NEW_PCT + gap_pct / 2
    balanced_com_new_pct = TREND_COM_NEW_PCT + gap_pct / 2

    SCENARIOS = {
        "trend_continues": {
            "params": (TREND_RES_NEW_PCT, TREND_RES_RENO_PCT, TREND_COM_NEW_PCT,
                       TREND_COM_RENO_PCT, TREND_COM_PP_PCT),
            "label": "Trend continues: same category shares as the FY18-24 DOR reconciliation "
                     "(numerically identical to Phase 1's trend_corrected, plus CHCA)",
        },
        "peer_target_residential_led": {
            "params": (res_led_new_pct, TREND_RES_RENO_PCT, TREND_COM_NEW_PCT,
                       TREND_COM_RENO_PCT, TREND_COM_PP_PCT),
            "label": f"Hit the {PEER_TARGET_PCT:.2%}/yr peer (80th-percentile) target entirely via "
                     f"more housing: res-new {res_led_new_pct:.4%}/yr (vs. {TREND_RES_NEW_PCT:.4%} trend), "
                     "commercial/renovation/personal property held at trend",
        },
        "peer_target_commercial_led": {
            "params": (TREND_RES_NEW_PCT, TREND_RES_RENO_PCT, com_led_new_pct,
                       TREND_COM_RENO_PCT, TREND_COM_PP_PCT),
            "label": f"Hit the {PEER_TARGET_PCT:.2%}/yr peer target entirely via commercial: "
                     f"com-new {com_led_new_pct:.4%}/yr (vs. {TREND_COM_NEW_PCT:.4%} trend), "
                     "residential/personal property held at trend",
        },
        "peer_target_balanced_mix": {
            "params": (balanced_res_new_pct, TREND_RES_RENO_PCT, balanced_com_new_pct,
                       TREND_COM_RENO_PCT, TREND_COM_PP_PCT),
            "label": f"Hit the {PEER_TARGET_PCT:.2%}/yr peer target via an even split of the gap "
                     "between residential and commercial new construction",
        },
    }

    # Hook for callers that solve for a growth rate (driver_forecast_breakeven.py):
    # extra scenarios are added only when set; the committed output is unchanged.
    SCENARIOS.update(EXTRA_SCENARIOS)

    print("\n=== Scenario definitions ===")
    for name, s in SCENARIOS.items():
        print(f"{name}: {s['label']}")
    print()

    rows = []
    for name, s in SCENARIOS.items():
        prop_tax, ng_by_year, operating, debt_exclusion = run_property_tax(
            town["property_taxes"], town["debt_exclusion"], hist_2025_total, hist_2025_debt_exclusion, s["params"])
        cumulative_new_com_sqft = 0.0
        actual_lr, pending = {}, []
        for y in FORECAST_YEARS:
            (ng, (res_new, res_reno, com_new, com_reno, com_pp, chca,
                  implied_units, implied_sqft)) = ng_by_year[y]
            cumulative_new_com_sqft += implied_sqft  # a stock - persists once built, unlike permits

            permits = building_permit_revenue(res_new, res_reno, com_new, com_reno, year=y)
            meals_organic = meals_tax_organic(y)
            meals_new = meals_tax_from_new_commercial(cumulative_new_com_sqft)
            lr_residual = local_receipts_2025_residual * (1 + local_receipts_cagr_ex_meals) ** (y - 2025)
            lr_chca = chca_local_receipts(y)
            local_receipts_y = (lr_residual + meals_organic + meals_new + permits + lr_chca
                                + INVESTMENT_INCOME_FLAT)

            actual_lr[y] = local_receipts_y
            pending.append((y, ng, res_new, res_reno, com_new, com_reno, com_pp, chca,
                            implied_units, implied_sqft, permits, meals_organic, meals_new,
                            lr_residual, lr_chca))
        import revenue_cash_cycle as rcc
        base_total = {y: prop_tax[y] + state_aid[y] + other_funds[y] for y in FORECAST_YEARS}
        budget_lr, fc = rcc.apply(FORECAST_YEARS, actual_lr, free_cash, base_total)
        for (y, ng, res_new, res_reno, com_new, com_reno, com_pp, chca, implied_units,
             implied_sqft, permits, meals_organic, meals_new, lr_residual, lr_chca) in pending:
            local_receipts_y = budget_lr[y]
            total = prop_tax[y] + state_aid[y] + local_receipts_y + other_funds[y] + fc[y]
            note = (f"new growth ${ng:,.0f} = res-new ${res_new:,.0f} ({implied_units:,.0f} implied units) "
                    f"+ res-reno ${res_reno:,.0f} + com-new ${com_new:,.0f} ({implied_sqft:,.0f} implied sqft) "
                    f"+ com-reno ${com_reno:,.0f} + com-personal-property ${com_pp:,.0f} "
                    f"+ CHCA (property tax) ${chca:,.0f}; {s['label']}")
            lr_note = (f"residual (ex-meals, ex-permits, ex-investment income) FY2025 actual x "
                       f"{local_receipts_cagr_ex_meals:.2%} "
                       f"CAGR (FY19-25 actual) ${lr_residual:,.0f} + meals tax organic ${meals_organic:,.0f} "
                       f"({MEALS_TAX_ORGANIC_CAGR:.2%}/yr) + meals tax from "
                       f"{cumulative_new_com_sqft:,.0f} cumulative new commercial sqft ${meals_new:,.0f} "
                       f"(${MEALS_TAX_INTENSITY_PER_SQFT:.4f}/sqft) + building permits ${permits:,.0f} "
                       f"({building_permit_rate(y):.2%} of new-growth value, real estate only - excludes "
                       f"personal property) + CHCA (rooms tax + MV excise) ${lr_chca:,.0f} "
                       f"+ investment income held flat ${INVESTMENT_INCOME_FLAT:,.0f}; "
                       f"BUDGETED at {rcc.BUDGET_RATIO:.1%} of that actual (${actual_lr[y]:,.0f}), "
                       "excess arrives as next year's free cash (revenue_cash_cycle.py)")
            rows.append([
                name, y, round(prop_tax[y]), note,
                round(res_new), round(implied_units), round(res_reno),
                round(com_new), round(implied_sqft), round(com_reno), round(com_pp), round(chca),
                round(state_aid[y]), round(local_receipts_y), lr_note, round(other_funds[y]),
                round(fc[y]), round(total),
                round(operating[y]), round(debt_exclusion[y]),
            ])

    with open(OUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scenario", "fiscal_year", "property_taxes", "new_growth_assumption",
            "new_growth_res_new_dollars", "implied_res_new_units",
            "new_growth_res_reno_dollars",
            "new_growth_com_new_dollars", "implied_com_new_sqft",
            "new_growth_com_reno_dollars", "new_growth_com_personal_property_dollars",
            "chca_property_tax_dollars",
            "state_aid", "local_receipts", "local_receipts_assumption",
            "other_available_funds", "free_cash",
            "total_revenue",
            "property_tax_operating", "debt_exclusion_revenue",
        ])
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_FILE}")

    fy40_by_scenario = {r[0]: r[2] for r in rows if r[1] == 2040}
    print("\n=== FY2040 property tax by scenario ===")
    for name in SCENARIOS:
        print(f"  {name}: ${fy40_by_scenario[name]:,.0f}")

    # Implied units/sqft drift, FY2026 vs FY2040, for the write-up.
    fy26_units = {r[0]: r[5] for r in rows if r[1] == 2026}
    fy40_units = {r[0]: r[5] for r in rows if r[1] == 2040}
    fy26_sqft = {r[0]: r[8] for r in rows if r[1] == 2026}
    fy40_sqft = {r[0]: r[8] for r in rows if r[1] == 2040}

    write_methodology(SCENARIOS, res_led_new_pct, com_led_new_pct, fy40_by_scenario,
                       fy26_units, fy40_units, fy26_sqft, fy40_sqft)
    print(f"Wrote methodology doc to {METHODOLOGY_FILE}")


def write_methodology(scenarios, res_led_new_pct, com_led_new_pct, fy40_by_scenario,
                       fy26_units, fy40_units, fy26_sqft, fy40_sqft):
    lines = []
    lines.append("# Phase 2: New-Growth Revenue Scenarios, FY2026-2040\n")
    lines.append(
        "Extends Phase 1's `trend_corrected` baseline by splitting the single "
        "blended new-growth rate (1.277%/yr) into five independently "
        "adjustable **percentage** categories (not physical counts - see "
        "module docstring for why that correction matters) - residential "
        "new construction, residential renovation, commercial new "
        "construction, commercial renovation, and commercial personal "
        "property (business equipment/furniture/fixtures, split out "
        "2026-08-30 - see the Personal Property section below) - plus a "
        "named Chestnut Hill Commercial Area (CHCA) addition. See "
        "`scripts/new_growth_scenario_forecast.py` module docstring for the "
        "full derivation of every factor below, and `.claude/memorialized.md` "
        "(2026-08-28/29/30 entries) for context.\n"
    )
    lines.append("## Why percentages, not physical counts, drive the dollars\n")
    lines.append(
        "An earlier version of this script drove res-new/com-new directly "
        "from fixed unit/sqft counts per year. Ben caught the problem: a "
        "fixed physical pace's dollar contribution grows at its own "
        "appreciation rate, not the levy's growth rate - fine for "
        "residential (appreciation 4.96%/yr, faster than typical levy "
        "growth), but for commercial (1.28%/yr, *slower*) it silently "
        "became a shrinking share of the levy over time - exactly the "
        "problem Ben originally flagged for Phase 1's flat-dollar new-growth "
        "figure. Fixed: all four categories are %-of-prior-levy now. "
        "Physical units/sqft are still shown, but as a **derived, reported** "
        "quantity each year (dollars / appreciated $/unit or $/sqft), not "
        "an input.\n"
    )
    lines.append("## Conversion factors\n")
    lines.append(
        "| Factor | Value | Source |\n|---|---|---|\n"
        f"| Residential $/new unit (units-weighted) | ${RES_VALUE_PER_UNIT:,} | "
        "back-solved against the Town's own net-new-housing permit count "
        "(Development Look-Ahead, 2026-06-16, slide 9: 499 units over "
        "CY2022-24). Recalibrated 2026-09-22 from $324,000, which was the "
        "median per *event* and so the wrong estimator for a dollars-to-units "
        "divisor - see module docstring for the derivation and the "
        "$325k-$580k range |\n"
        f"| Commercial $/sqft | ${COM_VALUE_PER_SQFT}/sqft | current GIS snapshot, "
        "taxable commercial classes only - see sanity-check note in module "
        "docstring (10 Brookline Place implies ~2x this figure) |\n"
        f"| Residential tax rate (FY2026) | {RES_TAX_RATE:.4%} | DLS statewide dataset, FY21-25 avg |\n"
        f"| Commercial tax rate (FY2026) | {COM_TAX_RATE:.4%} | same |\n"
        f"| Residential value appreciation | {RES_VALUE_APPRECIATION_RATE:.2%}/yr | "
        "town-wide value growth net of DOR new growth, FY18-24 avg |\n"
        f"| Commercial value appreciation | {COM_VALUE_APPRECIATION_RATE:.2%}/yr | "
        "same - volatile/negative in COVID years, noisier |\n"
    )
    lines.append("## Tax rate drift, bounded by the CIP shift factor (2026-08-30, fixed 2026-09-01)\n\n")
    lines.append(
        "The residential/commercial tax rate above is a FY2026 starting "
        "point, not held flat through FY2040 - `res_tax_rate(year)`/"
        "`com_tax_rate(year)` drift it forward. Since the levy is capped "
        "but assessed value isn't, and Town-wide value appreciates faster "
        f"than the levy can grow ({BLENDED_VALUE_APPRECIATION_RATE:.2%}/yr "
        f"blended vs. {LEVY_GROWTH_RATE:.3%}/yr), **both rates decline "
        f"together** over the forecast - by FY2040, roughly "
        f"{(1 - (res_tax_rate(2040)/RES_TAX_RATE)):.1%} lower than FY2026, "
        "for residential and commercial alike. This doesn't change any `$` "
        "revenue figures in this script directly (new-growth dollars are "
        "computed as a %-of-prior-levy trend, not from units x value x "
        "rate) - it changes the *implied physical unit/sqft* translation, "
        "which matters because that translation is what Phase 4's "
        "marginal-cost model (`marginal_expense_forecast.py`) consumes.\n\n"
        "**Fixed 2026-09-01 - the original version let commercial and "
        "residential rates drift independently, each off its own class's "
        "value-appreciation rate, and that was wrong, not just "
        "unsupportable.** Run to FY2040 it implied the commercial rate "
        "rising ~41% while residential fell ~15% - a commercial/"
        "residential rate ratio of 2.72x, starting from today's 1.65x. "
        "The residential/commercial split isn't a market residual - it's a "
        "Select Board policy choice each year (the CIP shift factor, a.k.a. "
        "the Minimum Residential Factor), bounded by **M.G.L. c.40 §56** "
        "(not c.59 §5C, the earlier miscitation - that section is the "
        "unrelated residential exemption) at a **175% shift ceiling** "
        "(CIP's rate can't exceed 1.75x the single/uniform rate). "
        "**Confirmed directly**: Brookline's actual FY2026 shift, from "
        "`data/FY2026-Classification-Hearing%20Presentation-FINAL.pptx` "
        "(slide 9, the Select Board's adopted 20%-residential-exemption "
        "scenario), is **1.746 - 99.8% of the legal ceiling.** There is "
        "essentially no room left for the shift to climb further, so a "
        "model that lets the commercial rate keep climbing independently "
        "has no basis in what the actual policy lever can do.\n\n"
        "**Fix**: hold the shift ratio (COM_TAX_RATE/RES_TAX_RATE, "
        f"{COM_TAX_RATE/RES_TAX_RATE:.3f} for this script's trailing-5yr-"
        "smoothed anchors) constant across the forecast - both rates now "
        "drift off ONE blended, value-share-weighted appreciation rate "
        f"({BLENDED_VALUE_APPRECIATION_RATE:.2%}/yr, {RES_VALUE_SHARE_FY26:.1%} "
        f"residential / {CIP_VALUE_SHARE_FY26:.1%} CIP by FY2026 assessed "
        "value) instead of each class's own rate independently - "
        "preserving today's near-ceiling ratio through FY2040 by "
        "construction, the reasonable \"no future policy change\" "
        "baseline this project uses for every other policy lever "
        "(overrides, the residential exemption itself).\n\n"
    )
    lines.append("## Personal property: split out of \"com-other,\" its own trend\n\n")
    lines.append(
        "Added 2026-08-30 (Ben: does commercial assessed value include "
        "non-land/non-building property, and does it matter?). Confirmed "
        "via the Town's own FY2022-2025 Tax Classification Hearing "
        "presentations (Board of Assessors) that what this project's "
        "historical `output/brookline_historical_financials_fy05_25.csv` "
        "calls the \"commercial\" trailing rate is actually DOR's **CIP** "
        "total (Commercial + Industrial + Personal Property combined - "
        "Industrial is negligible in Brookline). Personal property "
        "(business equipment/furniture/fixtures - tracked in a wholly "
        "separate roll, not in the parcel-level CAMA extract the "
        "land-value-map classifier uses, so it was invisible to the "
        "com-new/com-other split entirely) has grown from 36.4% to 86.3% "
        "of CIP new-growth tax dollars over four straight years, as real "
        "commercial real estate growth collapsed:\n\n"
        "| FY | Commercial (real estate) tax growth | Personal property tax growth | PP share |\n"
        "|---|---|---|---|\n"
        "| 2022 | $1,006,965 | $575,402 | 36.4% |\n"
        "| 2023 | $247,544 | $545,083 | 68.8% |\n"
        "| 2024 | $182,141 | $685,825 | 79.0% |\n"
        "| 2025 | $90,168 | $568,802 | 86.3% |\n\n"
        f"Personal property's own rate as %-of-prior-levy is far more "
        f"stable than real commercial's (0.20-0.26%/yr each of the 4 "
        f"years, avg **{TREND_COM_PP_PCT:.4%}/yr**) - it's driven by "
        "business/equipment activity, not construction, so **it stays "
        "fixed at trend in every scenario, independent of com_new_sqft** "
        "(Ben's direction) - same treatment as res-reno, not something "
        "`peer_target_*` scenarios solve for. `com-reno` "
        f"(**{TREND_COM_RENO_PCT:.4%}/yr**) is now the residual "
        "*after* removing personal property too - real estate renovation/"
        "undetected expansion specifically, not a blend of that with "
        "personal property the way the old \"com-other\" bucket was. "
        "Building permits (see above) now exclude personal property "
        "entirely, correctly - equipment purchases don't need one.\n"
    )
    lines.append("## Scenarios\n")
    for name, s in scenarios.items():
        lines.append(f"### `{name}`\n\n{s['label']}\n")
    lines.append(
        "\nBecause every category is now %-of-the-same-prior-total-levy "
        "base, **the three `peer_target_*` scenarios are revenue-identical "
        "for every year of the forecast** - `res_new_pct`, `com_new_pct` "
        "and the balanced split all sum to the exact same "
        f"{PEER_TARGET_PCT:.2%}/yr target regardless of which category "
        "supplies it, so the property-tax dollar path (and FY2040 totals "
        "below) come out exactly the same. What genuinely differs between "
        "them is the **implied physical count**, and that drifts in "
        "*opposite directions* over the 15-year window:\n\n"
        "| Scenario | Implied res. units, FY26 -> FY40 | Implied com. sqft, FY26 -> FY40 |\n"
        "|---|---|---|\n"
        f"| `peer_target_residential_led` | {fy26_units['peer_target_residential_led']:,} -> "
        f"{fy40_units['peer_target_residential_led']:,} | n/a |\n"
        f"| `peer_target_commercial_led` | n/a | {fy26_sqft['peer_target_commercial_led']:,} -> "
        f"{fy40_sqft['peer_target_commercial_led']:,} |\n\n"
        "Residential's implied unit count *falls* over time (appreciation, "
        f"{RES_VALUE_APPRECIATION_RATE:.2%}/yr, outpaces the levy's own "
        "growth rate, so fewer units are needed each year to sustain the "
        "same % contribution) while commercial's implied sqft *rises* "
        f"(appreciation, {COM_VALUE_APPRECIATION_RATE:.2%}/yr, is slower "
        "than the levy's growth rate, so more sqft is needed each year to "
        "keep pace). Same dollars, opposite physical trajectories - a real "
        "nuance for the \"which kind of growth\" political question.\n"
    )
    lines.append("## Chestnut Hill Commercial Area (CHCA)\n\n")
    lines.append(
        "Added 2026-08-29. Zoning approved by Town Meeting 217-20, May "
        "28-29, 2026 (confirmed - supersedes the ERSC report's earlier "
        "\"may be brought to Spring 2026 TM\" framing). City Realty, "
        "1280-1330 Boylston St, 5-acre site: 3 buildings (14/12/7 stories), "
        "200-room hotel, 266 apartments/condos, medical office, "
        "ground-floor retail - over 50% of floor area required commercial "
        "by the zoning itself. Construction \"not planned to begin until "
        "2028\" at the earliest per the developer, who called that "
        "timeline optimistic (\"all the pieces fall into place perfectly\"). "
        "Estimated gross new revenue at full stabilization, averaged across "
        "**City Realty's 3 own scenarios** (of RKG's 5 total modeled - "
        "ERSC report Appendix, p.551-555, Ben's transcription in `data/"
        "Brookline property tax revenue over 20 years.xlsx`, \"Fiscal "
        "Impact Model\" tab). Ben's call (2026-08-30): EDAB and RKG's own "
        "scenarios came in noticeably more conservative than the "
        "developer's - use the CR average here (Phase 2 explores what "
        "growth could plausibly look like) and reserve RKG's single "
        "independent scenario for the baseline forecast instead: "
        f"**${CHCA_PROPERTY_TAX_AT_STABILIZATION:,.0f} in property tax** "
        "(residential + commercial real/personal property tax - the only "
        "portion that counts toward the Prop 2.5 levy limit) plus "
        f"**${CHCA_LOCAL_RECEIPTS_AT_STABILIZATION:,.0f} in local receipts** "
        "(local rooms tax + motor vehicle excise - added to the "
        "`local_receipts` line instead, since neither counts toward the "
        "levy limit). None of the 5 RKG-modeled scenarios exactly matches "
        "the final approved plan's mix (200 hotel rooms matches CR "
        "Scenario 1 exactly; 266 total residential units is closest to "
        "the RKG Scenario's 265 - no scenario matches both), so an "
        "average is the more defensible choice absent an updated FIM run "
        "against the as-approved plan.\n\n"
        "No public building-by-building revenue phasing was found, so both "
        "streams are modeled as a **straight-line ramp** "
        f"from FY{CHCA_CONSTRUCTION_START_YEAR} to full stabilization in "
        f"FY{CHCA_FULL_STABILIZATION_YEAR} - a stated simplification, "
        "not a claim about actual phasing, chosen to land on roughly the "
        "same total span (~7yr construction + ~18mo to stabilized revenue) "
        "the ERSC report described. Added identically on top of every "
        "scenario above (and on top of both `town_assumptions` and "
        "`trend_corrected` in the baseline forecast) - it's a real, "
        "specific, now-confirmed project, not part of the FY18-24 "
        "historical detection the trend rates are built from, so it "
        "doesn't double-count with them.\n"
    )
    lines.append("## Local receipts beyond CHCA: building permits and meals tax\n\n")
    lines.append(
        "Added 2026-08-30 (Ben: new commercial construction generates new "
        "local receipts too, not just via CHCA specifically). Grounded from "
        "`data/revenue & expenditures all MA/LocalReciptesActVsEst "
        "{year}.xls` (DOR's itemized local-receipts breakdown by category, "
        "all 351 municipalities - more granular than the aggregate figure "
        "used elsewhere).\n\n"
        "**Building permits**: applied to the four *real estate* new-growth "
        "categories (res-new, res-reno, com-new, com-reno) - personal "
        "property is deliberately excluded (see Personal Property section "
        "above - equipment purchases don't need a building permit). Ben "
        "confirmed permits are pulled for renovation too, not just new "
        "construction, and are charged as a % of construction cost. Rate: "
        f"**{BUILDING_PERMIT_RATE:.2%}** through FY2026 "
        f"(\"$20 per $1,000 of construction value\", fee schedule effective "
        "2022-07-18, brooklinema.gov/183/Permit-Fee-Schedule), rising to "
        f"**{BUILDING_PERMIT_RATE_FY2027:.2%}** from "
        f"FY{BUILDING_PERMIT_RATE_INCREASE_FY} on - the Town raised permit "
        "fees to \"$21 / $1,000 of estimated cost, with specific "
        "exceptions\" effective July 1, 2026, the first day of FY2027 "
        "(dated notice on brooklinema.gov/172/Building-Department, found "
        "2026-09-04; note the dedicated fee-schedule page still showed the "
        "old $20 rate at that date and should not be read as current on "
        "its own). No residential/commercial or "
        "new-construction-vs-alteration distinction. Cross-checked against "
        "actual collections (DOR's itemized local-receipts data, "
        "Brookline's \"A.Building Permits\" line, cleanly separated only "
        f"FY2023-25 - a DOR reporting-format change limits this to 3 "
        f"years): {BUILDING_PERMIT_RATE_ACTUAL_COLLECTIONS:.2%} pooled "
        "against DOR's new-growth *value* (FY23 2.43%, FY24 1.35%, FY25 "
        "1.49% - real year-to-year variation on a small sample) - running "
        "somewhat below the statutory rate, plausibly self-reported "
        "construction values on permit applications running below "
        "eventual assessed value. This is a one-time fee tied to that "
        "year's construction activity, not a persistent addition to the "
        "tax base.\n\n"
        "**Meals tax**: split into an \"organic\" component "
        f"(**{MEALS_TAX_ORGANIC_CAGR:.2%}/yr**, FY19-25 actual CAGR - "
        "inflation/spending growth at existing restaurants) plus an "
        "increment tied to cumulative new commercial sqft built since the "
        f"forecast start, at **${MEALS_TAX_INTENSITY_PER_SQFT:.4f}/sqft/yr** "
        "(FY2025 meals tax / Brookline's existing taxable commercial sqft "
        "stock - a citywide *average* intensity, not a restaurant-specific "
        "rate, since restaurants are almost always tenants inside "
        "RES/COMM- or RETAIL STORE-classified buildings, not their own "
        "assessed class - no clean way to isolate a \"restaurant share of "
        "new commercial sqft\" from parcel data). Room tax is *not* "
        "generalized this way - hotels are the outlier commercial type "
        "(room tax grew 11.3%/yr FY17-25, 17.4%/yr pre-COVID, vs. 5.5%/yr "
        "for meals tax and 2.6%/yr for motor vehicle excise - a real, "
        "much steeper trend, plausibly tracking Brookline's actual hotel "
        "openings), and is already handled correctly for the one real "
        "hotel project in the forecast (CHCA) via its own project-specific "
        "figures.\n\n"
        "Both are pulled out of the generic `local_receipts` trend before "
        "extending the rest, to avoid double-counting each one's own "
        "historical growth twice (once via the generic trend, again via "
        "the explicit formula) - the residual base also has the FY2025 "
        "*level* of building permits subtracted for the same reason (a "
        "clean ex-permits *growth rate* isn't computable without FY2019 "
        "permits data, which doesn't exist pre-FY2023 reporting-format "
        "change - a stated approximation, not fully precise).\n\n"
    )
    lines.append("## FY2040 property tax by scenario\n\n")
    for name, val in fy40_by_scenario.items():
        lines.append(f"- `{name}`: ${val:,.0f}\n")
    lines.append(
        "\n## What this deliberately excludes\n\n"
        "- **Not a budget-balancing solver.** No expense forecast exists yet "
        "(Phase 3/4).\n"
        "- **CHCA's ramp shape is an assumption**, not sourced phasing - "
        "flagged explicitly above, worth revisiting if the Town publishes "
        "a building-by-building schedule.\n"
        "- **Commercial $/sqft has an unresolved ~2x gap** against one real "
        "named project (10 Brookline Place) - see module docstring.\n"
        "- **Zoning capacity is not modeled** beyond CHCA specifically - "
        "the five trend/peer categories state a %/implied-count, not a "
        "claim about what current zoning would actually permit town-wide.\n"
        "- **State aid, other available funds, and free cash are identical "
        "across every scenario here** - only property tax and local "
        "receipts vary. Local receipts is *not* identical across scenarios "
        "(unlike an earlier version of this doc claimed) - building "
        "permits and the meals-tax new-commercial increment both scale "
        "with each scenario's own res-new/com-new mix. Counterintuitively, "
        "`peer_target_residential_led` generates slightly *more* local "
        "receipts than `peer_target_commercial_led` at the same total "
        "new-growth rate (FY2026: $52.78M vs. $51.10M) - not because "
        "residential drives more local receipts per se, but because "
        "residential's lower tax rate (0.98% vs. commercial's 1.62%) means "
        "the same applied-levy dollar implies a *larger* underlying "
        "construction value for residential, and building permits scale "
        "off that value at one flat rate regardless of type - this "
        "outweighs meals tax's smaller, commercial-only contribution.\n"
    )
    with open(METHODOLOGY_FILE, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
