# Baseline Revenue Forecast (FY2026-2040) — Assumptions & Methodology

Companion to `baseline_revenue_forecast_fy26_40.csv`. Every `*_assumption`
column in that file states exactly what was applied to that cell - "Town's
own FY26-31 LRFP figure, as published" where we didn't touch it, or the
specific rate/formula where we did. This doc explains where each of those
numbers comes from.

## Scope

This is Phase 1: a "keep what we have" baseline — no new voter overrides,
no new-growth policy change (e.g. upzoning). Those are separate, later
phases (5 and 2 respectively). It answers "what happens to revenue if
nothing changes," not "what should the Town do."

## Two scenarios, both spanning the full FY2026-2040 window

- **town_assumptions**: the Town's own published FY2026-2031 LRFP figures,
  unmodified, then mechanically extended to FY2040 at the growth rates
  those figures themselves imply. Takes the Town's stated planning
  assumptions at face value, long-run.
- **trend_corrected**: our own trend-based assumptions, applied for the
  *entire* FY2026-2040 window — **not** anchored on the Town's FY2031
  figure with divergence starting only afterward. An earlier draft of this
  model did anchor that way, which meant `trend_corrected` was silently
  taking the Town's own (documented-conservative) numbers as truth for 6
  of the 15 forecast years. Ben caught this in review (2026-08-28) and
  asked for the Town's numbers to not be treated as ground truth for
  FY2026-2031 either — fixed, as described below.

## Property Tax — new growth as a % of prior levy, not a flat dollar amount

Uses the actual Massachusetts Proposition 2½ levy-limit formula rather
than a fitted trend line:

    levy(t) = levy(t-1) * 1.025 + new_growth(t)

`new_growth(t)` is expressed as a **percentage of the prior year's levy**
for `trend_corrected`, not a flat dollar amount (Ben, 2026-08-28: "we
found a historical percent growth number - can't we use that? why would
we want to use an absolute number?"). This is the standard DOR/DLS
convention for comparing new growth across towns and over time, and it's
what this project's own founding whitepaper uses ("New growth only
averaged 1.3%/yr... 25th percentile statewide... 2.1%/yr = 80th
percentile"). A flat dollar figure has a hidden implication worth naming:
held constant while the levy base grows, it makes new growth a *shrinking*
share of the levy every year — not supported by the data. The annual
%(`new_growth`/`prior_levy_limit`) over FY2005-2025 has stayed roughly in
the 1.1-1.4% band with no clear trend, even as the dollar levy nearly
tripled ($120M -> $313M).

- **town_assumptions**: **$2,500,000/yr flat**, the Town's own LRFP
  assumption, kept exactly as the Town itself stated it — this scenario is
  explicitly "take the Town's stated assumption at face value," and the
  Town's own planning document states a dollar figure, not a percentage,
  so we don't convert it.
- **trend_corrected**: **1.235%/yr of the prior year's levy** —
  trailing 5-year actual average (FY2021-2025, `new_growth` /
  `prior_levy_limit` from `output/brookline_historical_financials_fy05_25.csv`).
  The 21-year actual average is 1.367%/yr — close enough not to
  matter much, and consistent with the whitepaper's cited ~1.3%/yr.

**FY2026-2031**: we now have the Town's own year-by-year debt exclusion
schedule (see "Debt exclusion carve-out" below), so both scenarios build
the levy-limit-only base as `property_taxes(t) - debt_exclusion(t)`
(the May 2026 operating override is added into `property_taxes(t)` before
this split — see "May 2026 override correction" below for why it isn't
already there — but still isn't separately decomposed from ordinary 2.5%
statutory growth, only from debt exclusions specifically). `trend_corrected`
adds a **delta** on top of that levy-limit base:

    diff(t) = diff(t-1) * 1.025 + (1.235% * town_levy_limit(t-1) - $2,500,000), diff(2025) = 0
    trend_corrected_levy_limit(t) = town_levy_limit(t) + diff(t)        [t = 2026-2031]
    trend_corrected_property_tax(t) = trend_corrected_levy_limit(t) + debt_exclusion(t)

This is mathematically exact for this window (not an approximation): since
both scenarios' levy-limit formulas share the same known override
additions in any given year, those terms cancel out of the difference
between the two scenarios' levy-limit paths, leaving only the new-growth
substitution's compounding effect — which is exactly what `diff(t)`
computes.

**FY2032-2040**: `trend_corrected` switches to a clean geometric formula
on its own prior-year **levy-limit** total (no Town figure or delta
involved once past FY2031, since there's no more known-committed-facts
ambiguity to protect against):

    trend_corrected_levy_limit(t) = trend_corrected_levy_limit(t-1) * (1.025 + 1.235%)
    trend_corrected_property_tax(t) = trend_corrected_levy_limit(t) + debt_exclusion(t)   [debt_exclusion held flat, see below]

`town_assumptions` keeps running `levy_limit(t-1)*1.025 + $2,500,000` for
FY2032-2040 too, then adds the same flat `debt_exclusion(t)`. Both connect
continuously at the FY2031/2032 boundary — no discontinuity, even though
the two scenarios use different formula shapes before and after it.

## May 2026 override correction

Added 2026-09-01, caught by Ben asking directly why this forecast turned to
a deficit so quickly given the May 2026 override had already passed. It
hadn't been included — a real gap, not a design choice. `town_own_forecast_
fy26_31.csv` is a faithful transcription of `data/FY27-FY31-Long-Range-
Financial-Plan.pdf`, presented to the Advisory Committee **2026-01-13**,
four months **before** the override vote (2026-05-05). Checked directly
against that source (slide 8, "PROPERTY TAXES" table): its own "General
Override" line in the levy build-up is blank for every year FY2026-2031 —
this document exists to make the case *for* the override (its own Summary
slide: "Town structural deficit: $2.9M... Schools assumed structural
deficit: $13.5M"), not to reflect its passage. An earlier draft of this
methodology doc claimed the override was "already embedded" in the Town's
levy-limit base — that was wrong, unverified against the primary source.

Both scenarios now add the override in via `apply_may_2026_override()`
(`new_growth_scenario_forecast.py`), applied to `property_taxes` before
the debt-exclusion split below, so it flows identically into both
`town_assumptions` and `trend_corrected` — the same treatment as CHCA and
the debt-exclusion schedule (a decided fact by this project's own "today,"
not a hypothetical future policy lever). Year-by-year amounts (FY2027
$9,852,330 / FY2028 $5,602,871 / FY2029 $7,799,238, from Ben's own
`FY27-FY29 Brookline property tax & impact of new growth.xlsx`, cross-
sourced against the Override Guide's $23,254,439 3-year total) are
"permanent, not phased-out" per the Override Guide — each tranche, once
added, compounds at 2.5%/yr forever after, same as every other historical
override in this project's FY2005-2025 model.

## Debt exclusion carve-out — `property_taxes` = `property_tax_operating` + `debt_exclusion_revenue`

Added 2026-08-30 (Ben: "let's carve out the debt exclusions in detail so
we can focus on operating revenue" — debt exclusions were creating
confusion about what's really "operating" revenue vs. earmarked capital
funding). Sourced bond-by-bond from the Town's own FY27-31 LRFP
(`data/FY27-FY31-Long-Range-Financial-Plan.pdf`, "PROPERTY TAXES" and
"DEBT EXCLUSION" tables, pages 7-8 of that deck) — the Town's own levy
build-up already separates these two components before summing to the
"ANNUAL LEVY" figure that is `town["property_taxes"]`:

| | FY2026 | FY2027 | FY2028 | FY2029 | FY2030 | FY2031 |
|---|---|---|---|---|---|---|
| Sub-total Annual Levy Limit | \$303,957,721 | \$314,072,665 | \$324,424,482 | \$335,035,094 | \$345,910,971 | \$357,058,746 |
| Debt Exclusion (Debt Service) | \$28,596,860 | \$35,379,833 | \$36,013,706 | \$36,726,580 | \$36,720,980 | \$36,720,930 |
| **Annual Levy (= property_taxes)** | \$332,554,581 | \$349,452,499 | \$360,438,187 | \$371,761,674 | \$382,631,951 | \$393,779,676 |

The underlying LRFP bond-by-bond schedule is itself detailed — Florida
Ruffin Ridley School (2015, 2 borrowings), High School (2018, 4
borrowings), Driscoll School (2019 original + 2021 geothermal), Newbury
College (2020), Fire Station renovations (2023, 2 actual + 3 projected
future borrowings), Pierce School Construction (2024, 2 actual + 1
projected $77M future borrowing) — extracted here at the annual-total
level (`output/town_own_forecast_fy26_31.csv`'s new `debt_exclusion` row),
not bond-by-bond, since the annual total is what the property-tax and
debt-service sides of this model actually need.

By Massachusetts Proposition 2½ statute, a debt exclusion is a
**dollar-for-dollar match** to a specific bond's annual debt service: it's
added to the levy *outside* the 2.5% annual cap (not subject to it), and
it expires when the bond retires — legally distinct from the ordinary levy
limit, which grows 2.5%/yr plus new growth indefinitely.

**This carve-out is a real correctness fix, not just a presentational
one.** The previous version of this script grew the *combined* property
tax total (levy limit + embedded debt exclusion) at the 2.5%+new-growth
rate for FY2032-2040 — which silently compounded the debt-exclusion
dollars at that rate too. That's wrong: excluded amounts aren't subject to
the 2.5% cap and don't organically grow with the tax base; if anything
they gently *decline* as bonds retire (absent new exclusions, which this
"keep what we have" baseline already doesn't assume). Quantified: holding
FY2031's \$36,720,930 debt exclusion flat through FY2040 (the
corrected treatment) vs. letting it compound at `trend_corrected`'s
1.235%+2.5% rate for 9 more years (the old, incorrect
behavior) would have produced \$51,078,893 by
FY2040 — **\$14,357,963 of phantom property tax
revenue** that this fix removes.

**Now**: `debt_exclusion_revenue` is held flat at the FY2031 level for
FY2032-2040, identical in both scenarios (no new debt exclusions assumed —
the same policy this model already applies on the expense side for
`debt_service`, see `baseline_expense_forecast_fy26_40_methodology.md`).
`property_tax_operating` (the levy-limit-only component) is what actually
grows at the statutory/new-growth rate. `property_taxes` (the total,
unchanged from before) = `property_tax_operating` + `debt_exclusion_revenue`.

This resolves, in the direction Ben's question suggested, the "recommended
next step" flagged in an earlier draft of this doc (bond-by-bond
amortization detail) — we now have the annual bond-by-bond total through
FY2031, though not each bond's individual maturity/retirement date, so
`debt_exclusion_revenue` still can't be modeled as *declining* post-FY2031
(only held flat) without more data.

## Why this matters: new growth compounds — a small rate difference becomes a large gap

Isolating just the new-growth assumption's effect on property tax (both
scenarios share the same 2.5% statutory mechanic and the same known
committed overrides/debt exclusions, so this gap is purely the new-growth
difference, nothing else):

| Fiscal Year | trend_corrected − town_assumptions (annual) | Cumulative since FY2026 |
|---|---|---|
| FY2026 | $0 | $0 |
| FY2030 | $6,711,177 | $15,372,603 |
| FY2035 | $20,882,660 | $88,797,844 |
| FY2040 | $42,408,356 | $254,524,440 |

In year one, the gap between the Town's $2,500,000/yr assumption and the
trailing-actual 1.235%/yr rate is barely noticeable
($0). By FY2040 it's **$42,408,356
of additional annual property tax revenue** from that one assumption
alone, and **$254,524,440 cumulatively** over the
15-year window — because new growth doesn't just add revenue in the year
it happens, it permanently raises the levy base that the next year's 2.5%
statutory increase (and the year after's new growth) compounds on top of.
This is the same mechanism the founding whitepaper's thesis rests on
(new growth at the 80th percentile vs. the 25th percentile would likely
have avoided four historical overrides) — it's just more visible here
because the forecast window is long enough for the compounding to show up
as a large, striking number rather than a small annual difference. Directly
useful for public communication: "getting new growth right" isn't a
one-time, modest-sounding win — it's a structural lever whose payoff grows
every year it's sustained.

## Physical translation — how much actually gets built, in `trend_corrected`

Added 2026-08-29 (Ben: "can we retroactively make the baseline forecast
match this format so we can say, in the baseline, how much gets built or
renovated?"). Two new columns, `implied_res_new_units` and
`implied_com_new_sqft`, decompose `trend_corrected`'s existing new-growth
$ figure each year into physical counts — **purely additive**, this does
not change `property_taxes` or any other dollar figure above, which are
identical to what's already reported and memorialized.

The decomposition uses the same 5-category trend shares established for
Phase 2 (`scripts/new_growth_scenario_forecast.py` — see that script's
module docstring for full sourcing): residential new construction
(0.2073%/yr) and renovation (0.6437%/yr),
commercial new construction (0.0084%/yr, structurally
near-undetectable — see `land-value-map/METHODOLOGY.md` Section 3b),
commercial renovation (0.1349%/yr), and commercial
personal property (0.2407%/yr — business equipment/
furniture/fixtures, split out from what used to be one blended "other"
bucket once the Town's own Tax Classification Hearing data confirmed it's
a distinct, now-dominant share of commercial new growth — see the
Personal Property entry below). New-construction dollars are converted to
units/sqft via the same appreciated $/unit ($430,000 in FY2026,
recalibrated 2026-09-22 from $324,000, growing 4.96%/yr) and $/sqft ($518 in FY2026, growing 1.28%/yr) Phase 2 uses.

`town_assumptions` is **not** decomposed this way — the Town's own $2.5M/yr
figure is a flat planning assumption they never broke out by construction
type, so inventing a split for it would be fabricating detail the source
doesn't have.

A real, worth-noting finding from this: the implied unit count *declines*
over the forecast window (172 units/yr in FY2026 → 153/yr by FY2040), even
as the dollar total keeps growing. That's because residential values
appreciate (4.96%/yr) faster than the new-growth dollar total compounds
(~2.5% statutory + 1.277% new growth, roughly 3.8%/yr blended) — so fewer
physical units are needed each year to sustain the same dollar contribution
as the ones already assumed get more valuable. Not a claim about actual
future construction pace, just what the dollar assumption implies if held
to this physical translation.

## Personal property: split out of "commercial," its own trend

Added 2026-08-30 (Ben: does commercial assessed value include non-land/
non-building property, and does it matter?). Confirmed via the Town's own
FY2022-2025 Tax Classification Hearing presentations (Board of Assessors)
that the "commercial" trailing rate used throughout this project is
actually DOR's **CIP** total (Commercial + Industrial + Personal Property
combined - Industrial is negligible). Personal property (business
equipment/furniture/fixtures, tracked in a wholly separate roll from the
parcel-level real estate data this project otherwise uses) has grown from
36.4% to 86.3% of CIP new-growth tax dollars over four straight years, as
real commercial real estate growth collapsed (full table and sourcing:
`scripts/new_growth_scenario_forecast.py`'s Personal Property section).
It's driven by business/equipment activity, not construction, so it gets
its own trend rate (**0.2407%/yr**, far more stable
year-to-year than real commercial's) and stays fixed at that rate in
`trend_corrected` - it's not construction-driven, so it isn't part of the
physical-translation columns above.

## Chestnut Hill Commercial Area (CHCA)

Added 2026-08-29, identically to both scenarios. Zoning approved by Town
Meeting 217-20, May 28-29, 2026 (City Realty, 1280-1330 Boylston St - see
`scripts/new_growth_scenario_forecast.py` module docstring for full
project detail). Uses RKG's own independent scenario specifically (not the
City Realty average - see the import comment above for why: EDAB and RKG
both came in more conservative than the developer's 3 scenarios, and a
conservative, independent figure fits this baseline's "keep what we have"
framing better than the developer's own numbers), from the ERSC report
Appendix (p.551-555) - Ben's transcription in `data/Brookline property tax
revenue over 20 years.xlsx`, "Fiscal Impact Model" tab. Split across two
revenue lines: **$3,158,174 in property tax** (residential
+ commercial real/personal property tax - the only portion that counts
toward the Prop 2.5 levy limit) and **$480,435
in local receipts** (local rooms tax + motor vehicle excise - a separate
revenue category, doesn't count toward the levy limit at all). Both ramp
on the same straight-line schedule, FY2032-
2034 (construction "not planned to begin until
2028" at the earliest per the developer; no public building-by-building
phasing found, so the ramp shape is a stated assumption, not sourced
phasing).

## State Aid & Local Receipts — `trend_corrected` ignores the Town's figures entirely

These two lines don't have a "known committed facts" component analogous
to a legislated override, so `trend_corrected` doesn't need the delta
method — it simply extends the last known **actual** figure (FY2025)
forward at a trailing actual CAGR, for all of FY2026-2040, without
reference to the Town's own forecast at all:

- **State Aid** (the exception, changed 2026-10-14): the Town's FY2026 figure and the
  adopted FY2027 budget's, then **2.5%/yr**, the rate in the Town's own long-range plan.
  The trailing FY2015-2025 rate (3.54%/yr, from $24,973,542 in FY2025)
  includes FY2019's one-year 8.6% rise; without it the rate is about 3.0%, FY2019-25 2.0%,
  FY2005-25 1.9%. Ben chose the conservative rate. `town_assumptions` instead uses the Town's own
  FY2026-2031 figures unmodified, extended at **2.38%/yr**
  (the rate those figures themselves imply) for FY2032-2040.
- **Local Receipts**: FY2025 actual `local_receipts_act_total`
  ($44,398,178) grown at **3.41%/yr** (trailing actual
  CAGR FY2019-2025 — FY2019, not FY2015, is the anchor specifically to
  skip the FY2020-2021 COVID dip). `town_assumptions` instead uses the
  Town's own FY2026-2031 figures unmodified, extended at
  **2.02%/yr** for FY2032-2040. **Why not correct the Town's
  own figure instead of ignoring it?** An earlier draft did exactly that —
  scaled the Town's FY26-31 figure up by the actual-vs-estimate ratio
  (~140%) rather than building fresh from the FY2025 actual. Superseded:
  building directly from the actual base is simpler, doesn't require a
  separate correction-factor concept, and is consistent with how State Aid
  is now handled too. (For reference: we still have hard evidence — the
  DLS Local Receipts Actual-vs-Estimate file — that actual Local Receipts
  have run 18-48% above the Recap Sheet estimate every year FY2017-2025,
  which is *why* trend_corrected doesn't use the Town's figure here at
  all; the Town's own Financial Plan confirms this is deliberate
  conservative budgeting policy, not a forecasting miss.)

## Local receipts beyond CHCA: building permits and meals tax

Added 2026-08-30 (Ben: new commercial/residential construction generates
new local receipts too, not just via CHCA specifically), `trend_corrected`
only - same reasoning as the physical-translation columns above,
`town_assumptions`' flat $ figure isn't decomposed by type. Full sourcing
in `scripts/new_growth_scenario_forecast.py`'s module docstring.

- **Building permits**: applied to the four *real estate* new-growth
  categories (res-new, res-reno, com-new, com-reno) - personal property is
  excluded (equipment purchases don't need a building permit; see the
  Personal Property entry below). Ben confirmed permits are pulled for
  renovation too, charged as a % of construction cost, at
  **2.00%** of new-growth *value* (not levy-applied
  $) through FY2026, rising to **2.10%** from
  FY2027 on. The $20-per-$1,000 rate comes
  from the Town's own fee schedule
  (brooklinema.gov/183/Permit-Fee-Schedule, effective 2022-07-18), and the
  increase to "$21 / $1,000 of estimated cost, with specific exceptions"
  from a dated notice on brooklinema.gov/172/Building-Department effective
  July 1, 2026 - the first day of FY2027 (found 2026-09-04; the dedicated
  fee-schedule page still showed the old rate at that date, so it isn't
  reliable on its own). No residential/commercial or new-vs-renovation
  distinction. Cross-checked against actual collections
  (DOR's itemized local-receipts data, `data/revenue & expenditures all MA/
  LocalReciptesActVsEst {year}.xls`, pooled across the only 3 years
  it's cleanly separated - FY23-25, a DOR reporting-format change limits
  this): 1.69%, running somewhat
  below the statutory rate. A one-time fee tied to that year's
  construction activity, not a persistent levy-base addition.
- **Meals tax**: split into an organic trend (**5.96%/yr**,
  FY19-25 actual - inflation/spending growth at existing restaurants) plus
  an increment tied to cumulative new commercial sqft built since the
  forecast start, at **$0.2778/sqft/yr** (a
  citywide average intensity, not a restaurant-specific rate - restaurants
  are almost always tenants inside larger mixed-use/retail-classified
  buildings, not their own assessed class, so no clean way to isolate a
  restaurant share of new commercial sqft from parcel data). Room tax is
  *not* generalized this way - hotels are the outlier commercial type
  (room tax grew 11.3%/yr FY17-25 vs. 5.5%/yr for meals tax), and is
  already handled correctly for CHCA (the one real hotel project in this
  forecast) via its own project-specific figures.

Both are pulled out of the generic Local Receipts trend before extending
the rest, to avoid double-counting each one's own historical growth twice.

## New debt exclusions beyond the known schedule — still assumed at $0, FY2026-2040

The "Debt exclusion carve-out" section above covers the *known, committed*
schedule (now precisely decomposed, bond-by-bond total, through FY2031).
Beyond that known schedule, this model still assumes **zero new debt
exclusions** are authorized FY2026-2040 - stated explicitly rather than
left as a silent gap, per the same logic as excluding new operating
overrides: both require a townwide ballot vote, so neither belongs in a
"keep what we have" baseline.

This is a real, likely-understating simplification worth flagging. Per
`data/brookline_overrides_debt_exclusions_history.csv`
(affordablebrookline.com/past-overrides, cross-validated 2026-08-28 against
this project's own override history - 4 of 5 operating-override dollar
amounts match exactly), Brookline has authorized a **new** debt exclusion
roughly every 1.5-2 years since 2015: Edward Devotion School (2016), High
School renovations (2019), Driscoll School (2021), Newbury College land
(2022), Pierce School (2024), Fire Station (2025). If that cadence
continues, actual property tax revenue (and debt service, on the expense
side) would run higher than either scenario shown here. We don't attempt
to model that continuation quantitatively — no dated schedule of *specific
future* projects exists (see the Baker School note below for the one real
candidate found so far).

**A specific, real candidate for "the next one"**: a 2019 internal BPS
staff memo (`data/2019-09-09-School-Building-Facility-Planning-Staff-Notes.pdf`,
an old informal draft, not a current Town-adopted plan) projected the
Baker School would reach the end of its lifecycle "by 2028" and require
renovation/expansion, with no funding plan yet identified at that writing —
unlike Pierce and Driscoll, which have since both gotten debt exclusions
(2024 and 2021 respectively). Baker has not. Worth verifying against a
current source before relying on it further — see
`.claude/memorialized.md`, 2026-08-28.

## Free Cash & Other Available Funds — identical in both scenarios

No defensible trend basis: these are fund-balance draws (prior-year
turnback, reserve appropriations), not an organically growing revenue
source. Both scenarios use the Town's own FY2026-2031 figures, held flat
at the FY2031 level for FY2032-2040. This is a simplification, not a
forecast — flagged here rather than given a fake trend line, and it's the
one place the two scenarios remain identical throughout the whole horizon
by design, not by omission.

## What this deliberately excludes

- **New voter overrides (operating or debt exclusion)** — by design. This
  baseline shows what happens *without* one; sizing the resulting gap
  against expense growth is Phase 5's job. See the debt-exclusions section
  above for why this is flagged as a likely-understating simplification,
  not a neutral one.
- **New-growth acceleration from policy change** (upzoning, permitting
  reform) — Phase 2's job, layered on top of this baseline. Chestnut Hill
  Commercial Area is the one exception: it's a real, now-confirmed,
  specific project (not a policy-change scenario), so it's included in
  both scenarios here directly — see the CHCA section above.
- **Expense side entirely** — this file is revenue-only. Phase 3 (baseline
  expenses) and Phase 4 (marginal expense impact of new growth) are
  separate, not-yet-built pieces.

## Sanity check

The Town's own FY2026-2031 figures imply total expenditure growing at a
4.85% CAGR — well above either revenue scenario here
(3.22% / 3.76%). That
directionally matches, rather than contradicts, the growing structural
deficit the Town's own LRFP already shows (mostly school-driven). It's not
independent validation of the *forecast* method, but it does confirm the
model isn't producing revenue growth that's implausibly out of step with
what the Town itself expects on the expense side over the years we can
directly check.

Note `trend_corrected`'s FY2026 total ($419,608,131)
is now higher than `town_assumptions`'s ($419,608,131)
even in FY2026 itself, since State Aid and Local Receipts are built from
FY2025 actuals rather than the Town's own FY2026 figure. This is expected,
not a bug — it's the direct consequence of fixing the FY2026-2031
treatment per Ben's review comment above.

## Sources

- `data/FY27-FY31-Long-Range-Financial-Plan.pdf` (Town's own forecast, FY2026-2031 base)
- `output/brookline_historical_financials_fy05_25.csv` (trailing actuals, FY2005-2025)
- `data/SOURCES.md` (full external-source catalog)
- `.claude/memorialized.md`, 2026-08-28 entries (decision log, incl. the
  Town's-forecasts-run-conservative cross-cutting theme this model builds on)
