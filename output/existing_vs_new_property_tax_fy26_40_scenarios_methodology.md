# Existing-vs-new-property tax split, FY2026-2040 scenarios

Forward continuation of `existing_vs_new_property_tax.py`'s real FY2005-2025 reconstruction, run under each of Phase 2's four new-growth scenarios (`new_growth_scenario_forecast.py`). Answers: what would different new-growth futures do to the tax burden on property that already existed as of FY2005, in aggregate - not a single household's bill, but the whole pre-2005 cohort's combined tax growth. FY2025 existing-cohort value share: 77.27% (the rest, 22.73%, is the cumulative "new" cohort - all construction/renovation/reclassification value added since FY2005).

## Results by scenario, FY2026->FY2040 (14 years)

| Scenario | Existing-cohort CAGR | Town-total CAGR | Gap |
|---|---|---|---|
| trend_continues | 2.313%/yr | 4.185%/yr | 1.873%/yr |
| peer_target_residential_led | 2.275%/yr | 4.817%/yr | 2.542%/yr |
| peer_target_commercial_led | 2.275%/yr | 4.817%/yr | 2.542%/yr |
| peer_target_balanced_mix | 2.275%/yr | 4.817%/yr | 2.542%/yr |

The gap column is the direct, concrete answer to "what does new growth buy existing residents": every year of that gap is town-wide levy growth that did NOT have to come out of existing property owners' pockets. A bigger gap (more new growth, per Phase 2's peer-target scenarios) means the existing cohort's tax bill grows more slowly, not that the Town collects less overall.

**The three `peer_target_*` scenarios are numerically identical here, and that's expected, not a bug**: this cohort model only consumes each year's TOTAL new-growth $, not its physical composition (residential vs. commercial, new vs. renovation) - Phase 2's three peer-target scenarios are constructed to hit the exact same total (the 80th-percentile peer rate), just via different physical mixes, so they only diverge from each other in `new_growth_scenarios_fy26_40.csv`'s implied-units/implied-sqft columns, never in the dollar total this script reads.

## Assumptions held flat (see module docstring for the full list)

No future overrides, no banked excess capacity (Town raises its full allowed levy every year), debt exclusion real through FY2031 then held flat - all identical to Phase 1/2's own baseline conventions, not new assumptions introduced here.

## Anchor reconciliation

FY2025's real existing/new split (`existing_vs_new_property_tax_fy05_25.csv`) is computed against the ALLOWED FY2025 levy limit; `new_growth_scenario_forecast.py`'s FY2025 base is the ACTUALLY-RAISED FY2025 operating levy (total levy minus debt exclusion) - these differ by FY2025's real excess capacity (~$2.56M, under 1% of the ~$290M base), a genuine historical fact, not a bug in either script. This script rescales the real FY2025 existing_share onto Phase 2's own actually-raised anchor so the two series it depends on are internally consistent, rather than letting a base mismatch compound forward silently.
