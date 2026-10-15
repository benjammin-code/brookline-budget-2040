# Departmental Category-Level Forecast (FY2026-2040) — Methodology

Companion to `departmental_category_forecast_fy26_40.csv`. Replaces `baseline_expense_forecast.py`'s `trend_corrected` departmental line (previously a single blended 3.77%/yr trailing-5yr CAGR) with Schedule A's own 5 functional categories, each grown at its own trailing-5yr rate. See this script's own module docstring for why this one is deliberately simpler than the Schools/Benefits decompositions (no new data sourcing needed, no extreme rate-window divergence to work around).

## FY2025 shares and rates

| Category | FY2025 $ | Share | 5yr CAGR (used) | 20yr CAGR (cross-check) |
|---|---:|---:|---:|---:|
| General Government | $14,585,216 | 17.2% | 3.00%/yr | 0.89%/yr |
| Public Safety | $43,497,816 | 51.4% | 4.37%/yr | 2.73%/yr |
| Public Works | $15,080,716 | 17.8% | 3.43%/yr | 0.47%/yr |
| Human Services | $2,793,578 | 3.3% | 3.41%/yr | 2.66%/yr |
| Culture & Recreation | $8,665,288 | 10.2% | 2.89%/yr | 1.46%/yr |
| **Total** | **$84,622,614** | 100.0% | | |

Two categories (General Government, Public Works) show a larger 5yr-vs-20yr *ratio* than the others - but the 5yr rate itself is unremarkable (3.00%/3.43%), the ratio is large only because the 20yr rate is unusually low. Nothing here approaches the magnitude that made trailing-5yr risky for Schools/Benefits categories, so this build uses trailing-5yr uniformly, no per-category overrides - consistent with this project's general convention elsewhere.

## FY2026-2031: a decomposition of the Town's own known total, not an independent estimate

The Town doesn't publish department-level FY2026-2031 figures (only one aggregate `departmental_town` line), and unlike Schools or Benefits' Pensions, there's no independent data source suggesting that aggregate needs correcting. So FY2026-2031 splits the Town's real, known total by each category's FY2025 actual share - a decomposition, not a re-estimate. FY2032-2040 is where the real divergence from a single blended rate happens, since no Town figure exists for any of this past FY2031 anyway.

## Result vs. the previous single-line approach

FY2040 total: **$159,954,743** (category-level) vs. **$159,602,589** (old single-line 3.77%/yr trailing-5yr CAGR on the FY2031 total) — a **+0.2%** difference. Much smaller than the Schools/Benefits gaps, as expected - none of these 5 categories individually diverges far from the old blended rate, so decomposing them mostly sharpens the *composition* (which category is really driving departmental growth), not the total.

## Is the low CAGR real, or is it masking service cuts? — FTE/wage diagnosis

Added 2026-09-02 (Ben: "is it important to know what allows the historical CAGR for these departments to be so low? ... are these departments actually shrinking? ... we should be able to back up the forecast with some logic about whether services stay the same or shrink"). A fair challenge - a 3%/yr departmental CAGR next to 4-5%/yr wage growth only makes sense if something else is offsetting it, and "headcount is shrinking" is one obvious candidate worth actually checking, not assuming either way. Real Town headcount (FTE) and salary-budget data, FY2019 vs FY2026, from `department_fte_history.py` (its own captured dataset - see `output/department_fte_salary_fy19_fy26.csv` and `output/department_fte_salary_fy19_fy26_notes.md` for the full 18-department detail and per-department footnotes), rolled up onto these same 5 categories:

| Category | FTE FY19→FY26 | FTE CAGR | Salary $/FTE CAGR (implied) |
|---|---:|---:|---:|
| General Government | 126.6 → 135.6 | +0.99%/yr | +2.02%/yr |
| Public Safety | 340.8 → 334.3 | -0.27%/yr | +3.89%/yr |
| Public Works | 130.4 → 133.9 | +0.38%/yr | +1.83%/yr |
| Human Services | 37.0 → 47.4 | +3.61%/yr | +0.11%/yr |
| Culture & Recreation | 64.8 → 67.2 | +0.52%/yr | +1.55%/yr |

**The answer: services are not, on net, being cut to hold costs down.** Headcount actually *grew* in 4 of the 5 categories - Human Services grew fastest (+3.6%/yr FTE, mostly public-health staffing) while its per-employee cost stayed nearly flat (+0.1%/yr), meaning essentially all of that category's real dollar growth is more staff, not more expensive staff. General Government, Public Works, and Culture & Recreation all show modest headcount growth alongside modest per-employee growth - broadly steady service levels, growing in step with cost.

**Public Safety is the one real exception, and it explains most of the story Ben's question was getting at.** Its headcount actually shrank (-0.28%/yr, largely Police - down 7.5 FTE net, per the ERSC report's own footnote: "held open 6 officers... to balance the 2026 budget") while its implied cost-per-employee rose faster than every other category (+3.89%/yr) - this category's dollar growth is real, but it's wage/overtime/arbitration-driven, not headcount-driven. This matches the same report's own narrative on the same page: police and fire secure JLMC-arbitrated wage gains beyond COLA (a 2023 retroactive settlement added a 4% "Certification Differential" stipend, since increased to 7.5% by 2027, plus new tenure-based step increases), which the Town has partly funded by leaving positions unfilled - i.e., trading headcount for compensation growth, not shrinking the service itself.

**What this means for the forecast**: for General Government/Public Works/Human Services/Culture & Recreation, projecting continued trailing-5yr growth is not assuming service cuts - the real FY2019-2026 pattern behind those CAGRs is modest, broad-based headcount growth roughly matched by modest per-employee cost growth, a defensible pattern to extend. For Public Safety, the story is different: its 4.37%/yr trailing-5yr CAGR reflects arbitration-driven wage growth on a headcount that's held flat-to-shrinking by budget pressure, not rising service levels - extending that same rate assumes the arbitration/COLA dynamic (not more police officers or firefighters) continues to be the main cost driver, which is the same real pattern already documented in the ERSC report as an active, unresolved cost pressure (not something this forecast is inventing).

## What this deliberately does not do

- **`town_assumptions` is unchanged** — still the Town's own aggregate departmental figure, FY26-31 Town-published + Town-implied CAGR extension FY32-40.
- **No sub-department detail within each category** (e.g. Police vs. Fire within Public Safety) - Schedule A's own 5-category split is the finest granularity available from this project's existing data without a new research effort, which wasn't asked for here.

## Sources

- `output/brookline_historical_financials_fy05_25.csv` (Schedule A, FY2005-2025)
- `output/town_own_forecast_fy26_31.csv` (Town's own FY26-31 departmental_town aggregate)
