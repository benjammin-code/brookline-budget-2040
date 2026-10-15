# Phase 2: New-Growth Revenue Scenarios, FY2026-2040

Extends Phase 1's `trend_corrected` baseline by splitting the single blended new-growth rate (1.277%/yr) into five independently adjustable **percentage** categories (not physical counts - see module docstring for why that correction matters) - residential new construction, residential renovation, commercial new construction, commercial renovation, and commercial personal property (business equipment/furniture/fixtures, split out 2026-08-30 - see the Personal Property section below) - plus a named Chestnut Hill Commercial Area (CHCA) addition. See `scripts/new_growth_scenario_forecast.py` module docstring for the full derivation of every factor below, and `.claude/memorialized.md` (2026-08-28/29/30 entries) for context.

## Why percentages, not physical counts, drive the dollars

An earlier version of this script drove res-new/com-new directly from fixed unit/sqft counts per year. Ben caught the problem: a fixed physical pace's dollar contribution grows at its own appreciation rate, not the levy's growth rate - fine for residential (appreciation 4.96%/yr, faster than typical levy growth), but for commercial (1.28%/yr, *slower*) it silently became a shrinking share of the levy over time - exactly the problem Ben originally flagged for Phase 1's flat-dollar new-growth figure. Fixed: all four categories are %-of-prior-levy now. Physical units/sqft are still shown, but as a **derived, reported** quantity each year (dollars / appreciated $/unit or $/sqft), not an input.

## Conversion factors

| Factor | Value | Source |
|---|---|---|
| Residential $/new unit (units-weighted) | $585,000.0 | back-solved against the Town's own net-new-housing permit count (Development Look-Ahead, 2026-06-16, slide 9: 499 units over CY2022-24). Recalibrated 2026-09-22 from $324,000, which was the median per *event* and so the wrong estimator for a dollars-to-units divisor - see module docstring for the derivation and the $325k-$580k range |
| Commercial $/sqft | $518/sqft | current GIS snapshot, taxable commercial classes only - see sanity-check note in module docstring (10 Brookline Place implies ~2x this figure) |
| Residential tax rate (FY2026) | 0.9836% | DLS statewide dataset, FY21-25 avg |
| Commercial tax rate (FY2026) | 1.6238% | same |
| Residential value appreciation | 4.96%/yr | town-wide value growth net of DOR new growth, FY18-24 avg |
| Commercial value appreciation | 1.28%/yr | same - volatile/negative in COVID years, noisier |

## Tax rate drift, bounded by the CIP shift factor (2026-08-30, fixed 2026-09-01)


The residential/commercial tax rate above is a FY2026 starting point, not held flat through FY2040 - `res_tax_rate(year)`/`com_tax_rate(year)` drift it forward. Since the levy is capped but assessed value isn't, and Town-wide value appreciates faster than the levy can grow (4.63%/yr blended vs. 3.735%/yr), **both rates decline together** over the forecast - by FY2040, roughly 11.3% lower than FY2026, for residential and commercial alike. This doesn't change any `$` revenue figures in this script directly (new-growth dollars are computed as a %-of-prior-levy trend, not from units x value x rate) - it changes the *implied physical unit/sqft* translation, which matters because that translation is what Phase 4's marginal-cost model (`marginal_expense_forecast.py`) consumes.

**Fixed 2026-09-01 - the original version let commercial and residential rates drift independently, each off its own class's value-appreciation rate, and that was wrong, not just unsupportable.** Run to FY2040 it implied the commercial rate rising ~41% while residential fell ~15% - a commercial/residential rate ratio of 2.72x, starting from today's 1.65x. The residential/commercial split isn't a market residual - it's a Select Board policy choice each year (the CIP shift factor, a.k.a. the Minimum Residential Factor), bounded by **M.G.L. c.40 §56** (not c.59 §5C, the earlier miscitation - that section is the unrelated residential exemption) at a **175% shift ceiling** (CIP's rate can't exceed 1.75x the single/uniform rate). **Confirmed directly**: Brookline's actual FY2026 shift, from `data/FY2026-Classification-Hearing%20Presentation-FINAL.pptx` (slide 9, the Select Board's adopted 20%-residential-exemption scenario), is **1.746 - 99.8% of the legal ceiling.** There is essentially no room left for the shift to climb further, so a model that lets the commercial rate keep climbing independently has no basis in what the actual policy lever can do.

**Fix**: hold the shift ratio (COM_TAX_RATE/RES_TAX_RATE, 1.651 for this script's trailing-5yr-smoothed anchors) constant across the forecast - both rates now drift off ONE blended, value-share-weighted appreciation rate (4.63%/yr, 90.9% residential / 9.1% CIP by FY2026 assessed value) instead of each class's own rate independently - preserving today's near-ceiling ratio through FY2040 by construction, the reasonable "no future policy change" baseline this project uses for every other policy lever (overrides, the residential exemption itself).


## Personal property: split out of "com-other," its own trend


Added 2026-08-30 (Ben: does commercial assessed value include non-land/non-building property, and does it matter?). Confirmed via the Town's own FY2022-2025 Tax Classification Hearing presentations (Board of Assessors) that what this project's historical `output/brookline_historical_financials_fy05_25.csv` calls the "commercial" trailing rate is actually DOR's **CIP** total (Commercial + Industrial + Personal Property combined - Industrial is negligible in Brookline). Personal property (business equipment/furniture/fixtures - tracked in a wholly separate roll, not in the parcel-level CAMA extract the land-value-map classifier uses, so it was invisible to the com-new/com-other split entirely) has grown from 36.4% to 86.3% of CIP new-growth tax dollars over four straight years, as real commercial real estate growth collapsed:

| FY | Commercial (real estate) tax growth | Personal property tax growth | PP share |
|---|---|---|---|
| 2022 | $1,006,965 | $575,402 | 36.4% |
| 2023 | $247,544 | $545,083 | 68.8% |
| 2024 | $182,141 | $685,825 | 79.0% |
| 2025 | $90,168 | $568,802 | 86.3% |

Personal property's own rate as %-of-prior-levy is far more stable than real commercial's (0.20-0.26%/yr each of the 4 years, avg **0.2407%/yr**) - it's driven by business/equipment activity, not construction, so **it stays fixed at trend in every scenario, independent of com_new_sqft** (Ben's direction) - same treatment as res-reno, not something `peer_target_*` scenarios solve for. `com-reno` (**0.1349%/yr**) is now the residual *after* removing personal property too - real estate renovation/undetected expansion specifically, not a blend of that with personal property the way the old "com-other" bucket was. Building permits (see above) now exclude personal property entirely, correctly - equipment purchases don't need one.

## Scenarios

### `trend_continues`

Trend continues: same category shares as the FY18-24 DOR reconciliation (numerically identical to Phase 1's trend_corrected, plus CHCA)

### `peer_target_residential_led`

Hit the 2.03%/yr peer (80th-percentile) target entirely via more housing: res-new 1.0043%/yr (vs. 0.2073% trend), commercial/renovation/personal property held at trend

### `peer_target_commercial_led`

Hit the 2.03%/yr peer target entirely via commercial: com-new 0.8054%/yr (vs. 0.0084% trend), residential/personal property held at trend

### `peer_target_balanced_mix`

Hit the 2.03%/yr peer target via an even split of the gap between residential and commercial new construction


Because every category is now %-of-the-same-prior-total-levy base, **the three `peer_target_*` scenarios are revenue-identical for every year of the forecast** - `res_new_pct`, `com_new_pct` and the balanced split all sum to the exact same 2.03%/yr target regardless of which category supplies it, so the property-tax dollar path (and FY2040 totals below) come out exactly the same. What genuinely differs between them is the **implied physical count**, and that drifts in *opposite directions* over the 15-year window:

| Scenario | Implied res. units, FY26 -> FY40 | Implied com. sqft, FY26 -> FY40 |
|---|---|---|
| `peer_target_residential_led` | 507 -> 581 | n/a |
| `peer_target_commercial_led` | n/a | 278,231 -> 525,061 |

Residential's implied unit count *falls* over time (appreciation, 4.96%/yr, outpaces the levy's own growth rate, so fewer units are needed each year to sustain the same % contribution) while commercial's implied sqft *rises* (appreciation, 1.28%/yr, is slower than the levy's growth rate, so more sqft is needed each year to keep pace). Same dollars, opposite physical trajectories - a real nuance for the "which kind of growth" political question.

## Chestnut Hill Commercial Area (CHCA)


Added 2026-08-29. Zoning approved by Town Meeting 217-20, May 28-29, 2026 (confirmed - supersedes the ERSC report's earlier "may be brought to Spring 2026 TM" framing). City Realty, 1280-1330 Boylston St, 5-acre site: 3 buildings (14/12/7 stories), 200-room hotel, 266 apartments/condos, medical office, ground-floor retail - over 50% of floor area required commercial by the zoning itself. Construction "not planned to begin until 2028" at the earliest per the developer, who called that timeline optimistic ("all the pieces fall into place perfectly"). Estimated gross new revenue at full stabilization, averaged across **City Realty's 3 own scenarios** (of RKG's 5 total modeled - ERSC report Appendix, p.551-555, Ben's transcription in `data/Brookline property tax revenue over 20 years.xlsx`, "Fiscal Impact Model" tab). Ben's call (2026-08-30): EDAB and RKG's own scenarios came in noticeably more conservative than the developer's - use the CR average here (Phase 2 explores what growth could plausibly look like) and reserve RKG's single independent scenario for the baseline forecast instead: **$5,408,241 in property tax** (residential + commercial real/personal property tax - the only portion that counts toward the Prop 2.5 levy limit) plus **$917,905 in local receipts** (local rooms tax + motor vehicle excise - added to the `local_receipts` line instead, since neither counts toward the levy limit). None of the 5 RKG-modeled scenarios exactly matches the final approved plan's mix (200 hotel rooms matches CR Scenario 1 exactly; 266 total residential units is closest to the RKG Scenario's 265 - no scenario matches both), so an average is the more defensible choice absent an updated FIM run against the as-approved plan.

No public building-by-building revenue phasing was found, so both streams are modeled as a **straight-line ramp** from FY2032 to full stabilization in FY2034 - a stated simplification, not a claim about actual phasing, chosen to land on roughly the same total span (~7yr construction + ~18mo to stabilized revenue) the ERSC report described. Added identically on top of every scenario above (and on top of both `town_assumptions` and `trend_corrected` in the baseline forecast) - it's a real, specific, now-confirmed project, not part of the FY18-24 historical detection the trend rates are built from, so it doesn't double-count with them.

## Local receipts beyond CHCA: building permits and meals tax


Added 2026-08-30 (Ben: new commercial construction generates new local receipts too, not just via CHCA specifically). Grounded from `data/revenue & expenditures all MA/LocalReciptesActVsEst {year}.xls` (DOR's itemized local-receipts breakdown by category, all 351 municipalities - more granular than the aggregate figure used elsewhere).

**Building permits**: applied to the four *real estate* new-growth categories (res-new, res-reno, com-new, com-reno) - personal property is deliberately excluded (see Personal Property section above - equipment purchases don't need a building permit). Ben confirmed permits are pulled for renovation too, not just new construction, and are charged as a % of construction cost. Rate: **2.00%** through FY2026 ("$20 per $1,000 of construction value", fee schedule effective 2022-07-18, brooklinema.gov/183/Permit-Fee-Schedule), rising to **2.10%** from FY2027 on - the Town raised permit fees to "$21 / $1,000 of estimated cost, with specific exceptions" effective July 1, 2026, the first day of FY2027 (dated notice on brooklinema.gov/172/Building-Department, found 2026-09-04; note the dedicated fee-schedule page still showed the old $20 rate at that date and should not be read as current on its own). No residential/commercial or new-construction-vs-alteration distinction. Cross-checked against actual collections (DOR's itemized local-receipts data, Brookline's "A.Building Permits" line, cleanly separated only FY2023-25 - a DOR reporting-format change limits this to 3 years): 1.69% pooled against DOR's new-growth *value* (FY23 2.43%, FY24 1.35%, FY25 1.49% - real year-to-year variation on a small sample) - running somewhat below the statutory rate, plausibly self-reported construction values on permit applications running below eventual assessed value. This is a one-time fee tied to that year's construction activity, not a persistent addition to the tax base.

**Meals tax**: split into an "organic" component (**5.96%/yr**, FY19-25 actual CAGR - inflation/spending growth at existing restaurants) plus an increment tied to cumulative new commercial sqft built since the forecast start, at **$0.2778/sqft/yr** (FY2025 meals tax / Brookline's existing taxable commercial sqft stock - a citywide *average* intensity, not a restaurant-specific rate, since restaurants are almost always tenants inside RES/COMM- or RETAIL STORE-classified buildings, not their own assessed class - no clean way to isolate a "restaurant share of new commercial sqft" from parcel data). Room tax is *not* generalized this way - hotels are the outlier commercial type (room tax grew 11.3%/yr FY17-25, 17.4%/yr pre-COVID, vs. 5.5%/yr for meals tax and 2.6%/yr for motor vehicle excise - a real, much steeper trend, plausibly tracking Brookline's actual hotel openings), and is already handled correctly for the one real hotel project in the forecast (CHCA) via its own project-specific figures.

Both are pulled out of the generic `local_receipts` trend before extending the rest, to avoid double-counting each one's own historical growth twice (once via the generic trend, again via the explicit formula) - the residual base also has the FY2025 *level* of building permits subtracted for the same reason (a clean ex-permits *growth rate* isn't computable without FY2019 permits data, which doesn't exist pre-FY2023 reporting-format change - a stated approximation, not fully precise).


## FY2040 property tax by scenario


- `trend_continues`: $587,425,857

- `peer_target_residential_led`: $644,345,112

- `peer_target_commercial_led`: $644,345,112

- `peer_target_balanced_mix`: $644,345,112


## What this deliberately excludes

- **Not a budget-balancing solver.** No expense forecast exists yet (Phase 3/4).
- **CHCA's ramp shape is an assumption**, not sourced phasing - flagged explicitly above, worth revisiting if the Town publishes a building-by-building schedule.
- **Commercial $/sqft has an unresolved ~2x gap** against one real named project (10 Brookline Place) - see module docstring.
- **Zoning capacity is not modeled** beyond CHCA specifically - the five trend/peer categories state a %/implied-count, not a claim about what current zoning would actually permit town-wide.
- **State aid, other available funds, and free cash are identical across every scenario here** - only property tax and local receipts vary. Local receipts is *not* identical across scenarios (unlike an earlier version of this doc claimed) - building permits and the meals-tax new-commercial increment both scale with each scenario's own res-new/com-new mix. Counterintuitively, `peer_target_residential_led` generates slightly *more* local receipts than `peer_target_commercial_led` at the same total new-growth rate (FY2026: $52.78M vs. $51.10M) - not because residential drives more local receipts per se, but because residential's lower tax rate (0.98% vs. commercial's 1.62%) means the same applied-levy dollar implies a *larger* underlying construction value for residential, and building permits scale off that value at one flat rate regardless of type - this outweighs meals tax's smaller, commercial-only contribution.
