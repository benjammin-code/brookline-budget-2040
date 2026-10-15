# Schools Category-Level Forecast (FY2026-2040) — Methodology

Companion to `schools_category_forecast_fy26_40.csv`. Replaces `baseline_expense_forecast.py`'s `trend_corrected` schools line (previously a single blended 3.42%/yr trailing-5yr CAGR on the whole `exp_education` total) with 9 separately-trended categories, using DESE's own End-of-Year Financial Report function categories. See this script's own module docstring for the two real methodological choices behind this (the Schedule-A-vs-DESE scope reconciliation, and why the growth-rate window deliberately breaks from this project's usual trailing-5yr convention).

## FY2025 anchor: category shares (of the real Schedule A `exp_education` total)

| Category | Share of FY2025 | FY2025 $ | 16yr CAGR (used) | 5yr CAGR (flagged upside) | 6yr ex-COVID-base CAGR |
|---|---:|---:|---:|---:|---:|
| Administration | 5.04% | $7,379,376 | 2.33%/yr | 8.66%/yr | 9.45%/yr |
| Guidance, Counseling and Testing | 5.03% | $7,359,468 | 4.60%/yr | 9.80%/yr | 9.12%/yr |
| Instructional Leadership | 6.83% | $10,000,647 | 2.00%/yr | 0.31%/yr | 0.06%/yr |
| Instructional Materials, Equipment and Technology | 2.93% | $4,286,940 | 4.13%/yr | 9.31%/yr | 3.92%/yr |
| Operations and Maintenance | 10.71% | $15,681,174 | 2.71%/yr | 7.66%/yr | 6.82%/yr |
| Other Teaching Services | 14.56% | $21,328,521 | 4.30%/yr | 7.01%/yr | 6.93%/yr |
| Professional Development | 0.78% | $1,141,414 | -2.14%/yr | 4.20%/yr | 4.51%/yr |
| Pupil Services | 7.76% | $11,361,054 | 5.93%/yr | 11.67%/yr | 10.45%/yr |
| Teachers | 46.37% | $67,907,515 | 2.72%/yr | 3.81%/yr | 3.99%/yr |
| **Total** | 100.00% | **$146,446,110** | | | |

The 5yr and 6yr-ex-COVID-base columns tell the same story independently (ruling out a COVID base-year artifact): several categories - Administration, Guidance, Instructional Materials, Pupil Services - have been growing 2-4x faster over the last 5-6 years than their 16-year average. This forecast uses the more conservative 16-year rate as the primary driver, and flags this acceleration explicitly as a real, named upside risk rather than silently compounding the elevated recent rate for all 15 forecast years.

## Result vs. the previous single-line approach — the total barely moves, the MIX changes a lot

Implied blended CAGR of this category-level build, FY2025-2040: **3.32%/yr** vs. the old single-line trailing-5yr CAGR of **3.42%/yr** — FY2040 totals of **$239,100,425** vs. **$242,519,041**, a **-1.4%** difference. **This is smaller than it might look, and for a specific, explainable reason - not because the category split doesn't matter.** The old figure was itself a trailing-5yr blended rate, which this doc's own table shows was elevated across nearly every category (a real, recent acceleration - see above). This build deliberately uses each category's more conservative 16-year rate instead. Teachers - the single largest category at 46.4% of the total - has a 16-year CAGR (2.72%) below even the old blended 5-year rate, which pulls the weighted-average total down toward it despite several much-faster-growing smaller categories sitting alongside it. **The real, more useful difference is the underlying composition, not the top-line total**: Pupil Services, Guidance, and Other Teaching Services all grow 1.6-2.2x faster than Teachers under this build, so Teachers' own share of the schools budget keeps shrinking through FY2040 - the same share-erosion dynamic `school_budget_drivers_summary.md` documents already happened, FY2009-2025 (see that doc's own historical share figures - computed on a different denominator there, DESE's full per-pupil total including benefits, so not directly comparable number-for-number to this forecast's FY2025 shares above, but the same underlying pattern). If the elevated 5yr/6yr rates persist instead of reverting toward each category's 16-year average, the real total would land meaningfully above both figures here - a named upside risk, not baked into this point estimate (see the CAGR-window table above).

## What this deliberately does not do

- **No enrollment forecast.** Category dollar totals are grown at their own historical $ CAGR directly (which already embeds whatever enrollment change occurred FY2009-2025) - not decomposed into headcount x unit-cost x enrollment (recommendation #2/#4 from `school_budget_drivers_summary.md`). Enrollment has been roughly flat the last 3 actual years (7,060/7,039/7,023, FY23-25), so this is a reasonable simplification for now, not a hidden one - a real enrollment scenario (growth, continued flat, further decline) would be the natural next extension if this forecast needs to answer 'what if enrollment changes' specifically.
- **No out-of-district placement modeling.** DESE's "Total Expenditures" (vs. "Total In-District Expenditures") gap - the real, ERSC-flagged volatile cost the Selected Populations data hints at - isn't separately forecast here.
- **`town_assumptions` is unchanged** - still the Town's own aggregate schools figure, FY26-31 Town-published + Town-implied CAGR extension FY32-40. This category decomposition only replaces `trend_corrected`, this project's own independently-built estimate — consistent with how every other `trend_corrected` refinement in this project works.

## Why `trend_corrected` now diverges from the Town's own figures for FY2026-2031 too
Previously, both scenarios shared the Town's own published FY26-31 schools figure identically, only diverging starting FY2032. This category-level build compounds forward from the real FY2025 actual for the full FY2026-2040 window instead - the same principle Ben already established for Phase 1's revenue forecast (2026-08-28: don't treat the Town's own near-term figures as ground truth for `trend_corrected`, which is supposed to be this project's own independent estimate throughout). `trend_corrected`'s FY2027 schools total under this build will not equal the Town's own $149.8M FY27 PSB budget figure - a real, deliberate divergence, not an error; the Town's own near-term budget request is one input, not a ceiling on what this project's own bottom-up estimate should say.

## Sources

- `output/school_spending_by_category_fy09_25.csv` (DESE, FY2009-2025)
- `output/brookline_historical_financials_fy05_25.csv` (Schedule A `exp_education`, FY2025 anchor)
- `output/school_budget_drivers_summary.md` (the synthesis this forecast implements recommendation #1 from)
- `data/SOURCES.md`, "School enrollment & staffing history (DESE)" section
