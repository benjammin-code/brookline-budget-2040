# Automatic Revenue vs. Cost Growth, FY2005-2025 — Methodology

Companion to `automatic_revenue_vs_costs_fy05_25.csv`. Rebuilds the reference document's most-quoted pair of numbers on a consistent basis.

The document's most-quoted pair of numbers, rebuilt on a consistent basis.

Why this exists (2026-09-13): the reference document's headline finding is
that over FY2005-2025 "automatic" revenue grew at 3.91%/yr against actual
spending at 3.92%/yr - essentially identical, hence "finely balanced." Both
figures are individually correct and both reproduce exactly from the
historical file. But they are not measured the same way, and comparing them
overstates how well automatic revenue kept up. Two mismatches:

1. **Basis.** 3.91% is a levy-limit figure, which excludes debt exclusions by
   construction. 3.92% is total expenditure, which INCLUDES debt service on
   excluded debt. That service grew from $1.7M (FY2005) to $22.0M (FY2025) -
   the debt ramp the 2020 BFAC report documents - so it inflates the expense
   side of a comparison the revenue side never included. Everywhere else the
   project is careful that debt exclusions net to zero and are therefore out
   of scope on BOTH sides; the headline is the one place that slipped.

2. **Scope.** 3.91% covers the property tax levy alone, about 78% of General
   Fund revenue. 3.92% covers all spending. Section 1e's own framing asks
   whether "the revenue the Town gets automatically - 2.5% plus new growth,
   with no override and no vote - grows fast enough to keep up with real cost
   growth." State aid and local receipts also arrive without a vote, so the
   right revenue measure for that question is total operating revenue with
   the *levy* replaced by its no-override counterfactual - not the levy alone.

Corrected, the comparison is 3.52% automatic revenue against 3.65% operating
expenditure - a shortfall of 0.13 percentage points a year rather than a dead
heat.

That is a better result for the document's argument, not a worse one. The
current pairing has to explain away an awkwardness: if automatic revenue
really did match cost growth almost exactly, why were four overrides needed?
The document currently hand-waves this ("even though real overrides were
still needed in specific years when the gap opened faster than that average
implies"). At 3.52% vs 3.65% there is nothing to explain away - a persistent
0.13-point annual shortfall is exactly what four overrides across twenty
years look like. It is also consistent with the forward-looking base case,
whose structural wedge is 0.09 points a year, so history and forecast tell
one story instead of two.

## Result

| Series (all ex-debt-exclusion) | FY2005 | FY2025 | CAGR |
|---|---|---|---|
| Automatic levy (2.5% + real new growth, no override) | $118.2M | $254.4M | **3.91%** |
| Actual levy (includes the four overrides) | $118.2M | $290.6M | **4.60%** |
| Non-levy operating revenue (aid, receipts, other excises) | $48.1M | $77.4M | **2.41%** |
| **Automatic TOTAL operating revenue** | $166.3M | $331.8M | **3.52%** |
| Actual total operating revenue | $166.3M | $368.0M | **4.05%** |
| **Operating expenditure** | $167.3M | $342.7M | **3.65%** |

**The corrected headline: automatic revenue grew at 3.52% a year against operating costs at 3.65% — a shortfall of 0.13 percentage points a year, every year, for twenty years.** That is what four overrides were for.

## What the current figures are, and why they differ

The document currently pairs **3.91%** with **3.92%**. Both reproduce exactly from the same source file; neither is a computational error. They are simply not measured the same way — the first is levy-only and ex-debt-exclusion, the second is all spending including debt service on excluded debt. Correcting the basis moves the expense figure from 3.92% to 3.65%; correcting the scope moves the revenue figure from 3.91% to 3.52%.

Note the direction: **each correction on its own would have made the picture look better, and together they make it look worse.** Stripping excluded debt service lowers cost growth; narrowing to the levy raises measured revenue growth. The reason the corrected gap opens rather than closes is that non-levy revenue — state aid, local receipts — grew at only 2.41% a year, well below both the levy and costs, and it is a fifth of the budget.

## What this changes downstream

- The historical finding stops contradicting itself. A dead heat between automatic revenue and costs cannot explain why four overrides were needed; a persistent 0.13-point annual shortfall explains it exactly.
- History and forecast align. The forward base case's structural wedge is 0.09 points a year (see `base_case_decomposition_fy26_40_methodology.md`). At 0.13 points historically, the forecast is describing slightly *less* pressure than the last twenty years actually produced — which is a defensible thing to say and a much easier one than reconciling a wedge against a dead heat.
- The override total is unaffected. Part 2e's finding that the four overrides were worth $38.7M of annual capacity by FY2025 is computed on the levy alone and is untouched by any of this.

## Source

- `output/brookline_historical_financials_fy05_25.csv`
