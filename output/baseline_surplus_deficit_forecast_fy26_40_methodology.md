# Baseline Surplus/Deficit Forecast (FY2026-2040) — Methodology

Companion to `baseline_surplus_deficit_forecast_fy26_40.csv`. Part 3a of "the full story" outline: combines Phase 1's revenue forecast (`baseline_revenue_forecast_fy26_40.csv`) and Phase 3's expense forecast (`baseline_expense_forecast_fy26_40.csv`) — both of which already independently reach FY2040 — into one actual surplus/deficit line. This was the single biggest concrete modeling gap left in the project's baseline ("keep what we have") work.

## How the two scenarios are paired

Revenue and expense forecasts share the same two scenario names and are paired scenario-for-scenario, not cross-combined:

- **town_assumptions**: Town's own stated FY26-31 planning figures, mechanically extended to FY2040.
- **trend_corrected**: This project's own trailing-actual-CAGR assumptions, applied FY2026-2040.

Cross-pairing (e.g. the Town's own revenue assumption against this project's own higher expense estimate) would show a wider gap, but wasn't built here — each scenario name already means a consistent end-to-end "whose assumptions" story, and mixing them would blur that. Worth a follow-up if a sensitivity range around the gap is wanted later.

## Debt exclusion nets to exactly zero

`debt_exclusion_revenue` (revenue) and `debt_service_excluded` (expense) match to the dollar every year, FY2026-2040, in both scenarios — by Prop 2.5 statute a debt exclusion is a dollar-for-dollar match to a bond's annual debt service, and both source forecasts already hold it flat post-FY2031 with no new exclusions assumed. So `surplus_deficit` and `operating_surplus_deficit` are identical columns here; both are reported so that fact is checkable rather than asserted.

## Result

| Scenario | FY2026 | FY2030 | FY2035 | FY2040 |
|---|---|---|---|---|
| town_assumptions | $1 (+0.0% of revenue) | $-10,618,508 (-2.1% of revenue) | $-60,222,259 (-10.5% of revenue) | $-145,127,250 (-22.2% of revenue) |
| trend_corrected | $-10,311,097 (-2.5% of revenue) | $7,794,831 (+1.5% of revenue) | $1,336,513 (+0.2% of revenue) | $-3,853,509 (-0.5% of revenue) |

**town_assumptions**: turns to an annual deficit in FY2028 and stays there through FY2040; cumulative surplus/deficit across the full FY2026-2040 window is $-752,499,014.

**trend_corrected**: turns to an annual deficit in FY2026 and stays there through FY2040; cumulative surplus/deficit across the full FY2026-2040 window is $-22,729,480.

## What this deliberately still excludes

- **Any FUTURE voter override or debt exclusion beyond what's already decided.** The May 2026 operating override (FY2027-2029, $23,254,439 over 3 years) IS included on the revenue side — it's a decided, legislated fact by this project's own "today," not a hypothetical lever, so both scenarios' `total_revenue` already reflect it (see `baseline_revenue_forecast_fy26_40_methodology.md`'s "May 2026 override correction" section for why it wasn't already in the Town's own transcribed source data and how it's added). What's excluded is anything *beyond* that — a hypothetical FY2032+ override, for instance. The gap shown here is what such a future lever (or another one) would need to close, not a prediction that Brookline runs an actual cash deficit — Massachusetts towns cannot; in practice, this gap is what gets closed every year by some combination of a future override, a free cash draw, or expense cuts not modeled here.
- **Phase 2's new-growth policy scenarios** (peer-target growth rates) — layered separately in `new_growth_scenarios_fy26_40.csv`; not combined with the expense side here. A natural follow-up: rerun this same combine against Phase 2's `trend_continues`/`peer_target_*` revenue paths to show how much of the gap each closes.
- **Phase 4's marginal expense impact of new growth** — the expense side here is Phase 3's baseline only (no new construction's added service cost). Combining Phase 2 revenue with Phase 3+4 expense together would be the fullest version of this exercise.

## Sources

- `output/baseline_revenue_forecast_fy26_40.csv` + its methodology doc
- `output/baseline_expense_forecast_fy26_40.csv` + its methodology doc
