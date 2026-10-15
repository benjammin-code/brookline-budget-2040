# Override-Reliance Scenario (FY2026-2040) — Methodology

Companion to `override_reliance_scenario_fy26_40.csv`. Part 3b's "overrides-only" lever: what it would take to keep the operating budget balanced through FY2040 using nothing but periodic overrides on top of the `town_assumptions` baseline - no new-growth improvement, no expense management, no permitting/zoning reform.

## Cadence and sizing

Override years: FY2029, FY2032, FY2035, FY2038 - every 3 years, chosen to match the Town's own ERSC Final Report observation that override intervals have compressed (p.12), not fitted to this data. Each override is sized to bring that year's operating surplus/deficit to exactly $0 (breakeven), given every prior hypothetical override already compounding at 2.5%/yr forever after (same mechanic as every real historical override in this project's model). This is the honest *minimum* - real overrides typically build in a buffer.

## Result

| Year | New override | Cumulative override | Resulting gap |
|---|---|---|---|
| FY2026 | $0 | $0 | $1 (+0.0%) |
| FY2029 | $7,609,416 | $7,609,416 | $0 (+0.0%) |
| FY2032 | $18,470,474 | $26,664,983 | $0 (+0.0%) |
| FY2035 | $31,506,989 | $60,222,259 | $0 (+0.0%) |
| FY2038 | $42,055,045 | $106,907,831 | $0 (+0.0%) |
| FY2040 | $0 | $112,320,040 | $-32,807,210 (-5.0%) |

Four overrides, FY2029, FY2032, FY2035, FY2038, totaling $99,641,924 in new nominal override dollars, compound to **$112,320,040/yr** of permanent added levy capacity by FY2040 - roughly 3x this project's own FY2005-2025 real-override total ($38.7M compounded, see Part 2) in about three-quarters of the time. Each override is roughly double the size of the one before it ($8.1M -> $16.8M -> $33.6M -> $42.1M), directly illustrating the ERSC's own 'compressing and growing' pattern rather than just asserting it.

**Even so, the budget is not fully closed by FY2040**: the resulting gap is back to $-32,807,210 (-5.0% of revenue) two years after the last modeled override (FY2038), since the underlying gap grows faster than a fixed 3-year cadence can fully keep pace with by the end of the window. A pure override-reliance strategy would need to keep accelerating - larger and/or more frequent asks - not settle into a steady rhythm.

## What this deliberately does not include

- **No buffer/reserve sizing** - real overrides (like the May 2026 one) often raise more than the strict breakeven amount and bank the excess; this scenario sizes to the minimum needed each cycle.
- **No political/voter-approval likelihood** - this is a mechanical "what size would be needed," not a claim about what would actually pass.
- **No combination with the other levers** - by design, this is the "do nothing but rely on overrides" case, meant to be directly compared against the new-growth, expense-management, and permitting/zoning levers, not blended with them.
