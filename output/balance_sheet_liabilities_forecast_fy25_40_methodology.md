# Town Balance Sheet — Liabilities Forecast (FY2025-2040) — Methodology

Companion to `balance_sheet_liabilities_forecast_fy25_40.csv`. See this script's own module docstring for the full FY2024 liability inventory (from the Statement of Net Position) and the reasoning behind each category's forecast. Summary table below; full reasoning is in the docstring since it's genuinely different per category, not one formula applied five times.

## FY2024 actual (audited) vs. this forecast's endpoints

| Category | FY2024 actual | FY2025 forecast | FY2031 (pension→$0, debt/OPEB milestones) | FY2040 forecast |
|---|---:|---:|---:|---:|
| Long-term Debt | $493,053,255 | $430,912,005 | $384,510,350 | $146,385,000 |
| Net Pension Liability | $170,723,706 | $173,231,820 | $0 | $0 |
| Net OPEB Liability (mechanical roll-forward, floored at $0 - see below) | $201,475,979 | $206,087,382 | $200,894,952 | $0 |
| Compensated Absences | $10,221,570 | $10,528,217 | $12,571,242 | $16,402,619 |
| Workers' Compensation | $2,040,000 | $2,101,200 | $2,508,943 | $3,273,601 |
| Other (unearned revenue, landfill, warrants, etc.) | $36,845,865 | $36,845,865 | $36,845,865 | $36,845,865 |
| **TOTAL LIABILITIES** | **$914,360,375** | **$859,706,489** | **$637,331,352** | **$202,907,085** |

**The headline shape**: total liabilities fall sharply through FY2031 (pension liability retiring to $0, existing debt amortizing down, OPEB liability shrinking as the FY2031 funding redirect kicks in) even before any of the real uncertainty (new Pierce borrowing beyond the known $77M tranche) is factored in - the pension payoff alone removes $173.2M. **This should be read as the most defensible floor for total liabilities, not a confident point forecast** - the debt side is a real known-floor (new Pierce borrowing beyond $77M is real, authorized, and not included), and the OPEB roll-forward doesn't model actuarial assumption/experience changes, the largest real driver of its historical volatility.

## What this deliberately does not do

- **OPEB roll-forward doesn't model actuarial assumption/experience changes** - the largest real driver of historical volatility (e.g. FY2023's real $59.8M assumption-driven liability drop) - see module docstring for the full mechanism and its floor-at-$0 treatment once the FY2031 funding redirect drives the trust past full funding.
- **No new Town debt beyond the 4 already-known projected tranches.** Pierce School alone has $113,916,000 of real, already-authorized borrowing capacity beyond the $77M 3rd tranche this forecast includes - a real, near-certain future addition to Town debt not modeled here.
- **No assumption about future investment returns/losses affecting the pension liability post-FY2031**, or any future benefit enhancements reopening a new unfunded liability.
- **New debt tranches' amortization (20yr level-principal) is an approximation** - no real amortization schedule exists yet for bonds not yet issued.
- **"Existing debt" is a combined total, not separated by debt-exclusion vs. regular (non-excluded) status** - and no future regular/non-excluded borrowing is modeled at all for FY2032-2040 (only the 4 known debt-exclusion tranches above), consistent with this project's existing 'not yet exploited: the 6.6%-of-net-revenue CIP policy' open item on the revenue side.

## Sources

- `data/FY2024-Audited-Financial-Statements.pdf` p.33 (Statement of Net Position), p.71-73 (debt service requirements, changes in long-term liabilities)
- `data/Brookline-Retirement-System-2024-Actuarial-Valuation.pdf` p.27 (pension funding schedule)
- `data/FY27-FY31-Long-Range-Financial-Plan.pdf` p.9 (projected debt exclusion tranches)
