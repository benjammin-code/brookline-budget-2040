# Peer New-Growth Comparison — Methodology

Companion to `peer_new_growth_rates.csv`. Supports §2c of `docs/reference_document.md`. Replaces an ad-hoc 2026-08-28 calculation whose results lived only in `.claude/memorialized.md`.

`data/2026 MA state new growth for all towns 20 years.xlsx`, sheet `data`, is
the raw DLS Gateway pull: 351 municipalities x FY2003-2026, with each town's
"Total New Growth Applied to Limit as a % of PY Levy Limit" already computed
by DLS. A town's rate for a window is the simple mean of that column across
the window's years - the same convention the whitepaper used and the standard
DOR/DLS way of comparing new growth across towns and over time, because it
normalises for town size and scales with the levy base.

Towns missing any year in a window are excluded from that window's ranking
rather than averaged over a short series, which would bias them.

Two windows are reported, and both matter:

- **FY2005-2025** — the full period the document covers.
- **FY2021-2025** — the trailing five years, which tell a different and more
  complicated story: Brookline barely moved, but the 80th-percentile bar came
  *down*, so Brookline's ranking improved without Brookline improving much.

## Where Brookline sits

| Window | Towns ranked | Brookline | Percentile | Median | 80th pct |
|---|---|---|---|---|---|
| FY2005–2025 | 350 | **1.37%** | **26.6th** | 1.62% | **2.03%** |
| FY2021–2025 | 351 | **1.28%** | **40.2th** | 1.40% | **1.97%** |

Brookline's ranking improves from the 26th to the 40th percentile between the two windows while its own rate *falls* (1.37% to 1.28%). That is peers slowing down, not Brookline speeding up — the 80th-percentile bar drops from 2.03% to 1.97% and the median falls with it. Stating the ranking improvement without that context would read as a turnaround that did not happen.

## The full distribution, FY2005–2025

| Percentile | New growth, %/yr |
|---|---|
| 10th | 1.11% |
| 25th | 1.35% |
| 50th | 1.62% |
| 75th | 1.96% |
| 80th | 2.03% |
| 90th | 2.40% |

## Named peers

| Town | FY2005–2025 | FY2021–2025 |
|---|---|---|
| Somerville | 3.80% | 6.48% |
| Cambridge | 3.19% | 2.83% |
| Watertown | 3.12% | 5.07% |
| Boston | 2.97% | 3.50% |
| Needham | 2.80% | 3.03% |
| Lexington | 2.45% | 2.83% |
| Newton | 1.47% | 1.57% |
| Arlington | 1.00% | 0.87% |
| **Brookline** | **1.37%** | **1.28%** |

## What this corrects

The reference document and README both claimed peer towns "Cambridge, Boston, Needham, and Lexington" each generated "2.5%+" new growth. Two problems:

1. **Lexington is 2.45%** on the FY2005–2025 window that the surrounding sentence cites — below the stated floor. The claim holds only on the trailing five years.
2. **It was selective.** Newton (1.47%) and Arlington (1.00%) are equally reasonable inner-suburb peers and sit at or below Brookline. A reader shown only the four fastest peers is being shown a tail, not a comparison.

Both are now corrected in §2c, which states the distribution and names peers on both sides of Brookline. The underlying point survives intact and is better for being stated properly: Brookline is in the bottom third of the state, and towns very much like it have done substantially better.

## Source

- `data/2026 MA state new growth for all towns 20 years.xlsx`, sheet `data` — the raw MA Department of Local Services Gateway pull, 351 municipalities x FY2003–2026.
- Note the workbook's `pivot` sheet carries an older hand-built percentile ladder (Brookline 1.3305%, 28.1st percentile, 80th at 2.0044%) computed on an FY2006–2025 window. Those are not the figures used here; this script recomputes from the raw sheet on the stated windows.
