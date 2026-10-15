# Base-Case Decomposition (FY2026-2040) — Methodology

Companion to `base_case_decomposition_fy26_40.csv`. Supports Part 4a of `docs/reference_document.md`, which names `trend_corrected` the base case and sizes Part 4c's levers against it.

## The question this answers

Under `trend_corrected` the operating budget runs a surplus of **+$-3.9 million** a year by FY2040. Taken alone that reads as "Brookline is fine," and it is misleading, because the May 2026 operating override is already sitting in the revenue line. This decomposition separates the two.

## The three runs

- **`as_legislated`** — Committed baseline: May 2026 override included (it is a decided, legislated fact), new growth at the trailing FY2021-25 actual rate.
- **`ex_override`** — Counterfactual: identical, but the May 2026 override never passed. Isolates the structural position of automatic revenue vs. real costs.
- **`ex_override_breakeven`** — Counterfactual: no override, and new growth held at the rate that brings the FY2040 operating balance to zero.

All three re-run the real models (`baseline_revenue_forecast.py`, `baseline_surplus_deficit_forecast.py`) through the sensitivity hooks those modules expose, into a scratch directory. Nothing is reimplemented here. The `as_legislated` run is checked against the committed `baseline_surplus_deficit_forecast_fy26_40.csv` **to the dollar in every year** before any counterfactual is reported; a mismatch aborts the script.

Only the revenue side is re-run, because only the revenue side depends on the override: `baseline_expense_forecast.py` takes no revenue input. Every dollar of difference between the first two runs is therefore revenue.

## Result

| | FY2027 | FY2030 | FY2035 | FY2040 |
|---|---|---|---|---|
| **As legislated** (override in) | -1.8M (-0.4%) | +7.8M (+1.7%) | +1.3M (+0.2%) | -3.9M (-0.6%) |
| **Ex-override** (structural) | -11.7M (-2.9%) | -18.2M (-4.1%) | -30.2M (-5.7%) | -41.8M (-6.7%) |
| *What the override is worth that year* | $9.9M | $26.0M | $31.6M | $38.0M |

The override's value grows from the $23,254,439 voters approved to **$38.0 million a year by FY2040** — because an override permanently enlarges the levy base, which then compounds at 2.5% plus new growth every year after. This is the same mechanic Part 2e measures on the four FY2005-2025 overrides, where $32.4 million raised was worth $38.7 million of annual capacity by FY2025.

Stripping it out, the structural position is a small deficit that reopens slowly: **$41.8 million a year, 6.7% of revenue, by FY2040**. Not a crisis, and not closed either.

## The break-even new-growth rate

Solved by bisection on the sustained new-growth rate, with no override at all: **1.736% a year** of the prior-year levy limit brings the FY2040 operating balance to zero, against the trailing FY2021-25 actual of **1.277%** — a lift of **0.459 percentage points**.

Solved rather than interpolated between two runs: the levy limit is a compounding recursion, so the FY2040 balance is not linear in the rate, and a two-point interpolation would be wrong by a meaningful amount over fifteen years.

The path matters as much as the endpoint. Even at the break-even rate the balance still dips — -22.5M in FY2029 — before compounding catches up. New growth is a real lever and a slow one: value added in FY2027 is worth far more by FY2040 than the same value added in FY2038, and none of it helps in the year it is permitted.

## What this does not do

- **It does not claim the override was unnecessary.** The `ex_override` run shows a deficit reaching $31.9 million by FY2029 — the override closes a real gap, on schedule.
- **It does not model a future override.** See `override_reliance_scenario_fy26_40.csv` for that lever.
- **It does not vary the expense side.** Both the structural gap and the break-even rate are measured against `trend_corrected`'s expense path; a different expense assumption moves both.
- **It says nothing about which kind of growth** delivers the rate lift. That is Part 3's question, and the answer is not neutral — see Part 3b on tenure.

## Sources

- `scripts/baseline_revenue_forecast.py` (+ its methodology doc)
- `scripts/baseline_surplus_deficit_forecast.py` (+ its methodology doc)
- `output/brookline_historical_financials_fy05_25.csv` — for the trailing FY2021-25 new-growth rate
