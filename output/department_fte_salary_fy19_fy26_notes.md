# Town Department Headcount & Salary Budgets, FY2019 vs FY2026

Source: `data/ERSC Final Report FINAL 031326.pdf`, p.106, "Town Personnel Budgets and Full-Time Equivalents from FY2019 to FY2026." Captured as a standalone dataset 2026-09-02 (Ben: "let's make sure to capture the employees by department data and likely include it in any published work we do") - originally pulled only to diagnose `departmental_category_forecast.py`'s trailing-CAGR forecast (is it masking service cuts?), real enough on its own to keep and reuse.

**Verified**: all 18 department rows sum exactly to the source table's own stated TOTAL row ($53,218,117 → $66,317,226 salary; 699.60 → 718.44 total FTEs) - the same sum-to-stated-subtotal check used throughout this project to catch transcription errors before trusting a table.

## By department

| Department | Category | Total FTE FY19→FY26 | FTE CAGR | Salary CAGR | $/FTE FY19→FY26 |
|---|---|---:|---:|---:|---:|
| Select Board | General Government | 6.48 → 10.00 | +6.39% | +4.98% | $106,162 → $96,695 |
| Human Resources | General Government | 5.78 → 7.78 | +4.34% | +5.95% | $53,464 → $59,524 |
| Information Technology | General Government | 12.40 → 13.00 | +0.68% | +4.08% | $93,243 → $117,707 |
| DEICR | General Government | 2.72 → 3.72 | +4.57% | +7.05% | $80,424 → $94,749 |
| Finance Department | General Government | 31.22 → 29.42 | -0.84% | +1.71% | $74,256 → $88,727 |
| Legal Services | General Government | 7.03 → 8.21 | +2.24% | +3.92% | $98,810 → $110,749 |
| Advisory Committee | General Government | 0.40 → 0.40 | +0.00% | +2.36% | $58,002 → $68,280 |
| Town Clerk | General Government | 5.50 → 5.50 | +0.00% | -1.94% | $118,512 → $103,340 |
| Planning | General Government | 18.49 → 19.00 | +0.39% | +3.28% | $58,337 → $71,140 |
| Police | Public Safety | 180.80 → 173.30 | -0.60% | +3.74% | $83,397 → $112,537 |
| Fire | Public Safety | 160.00 → 161.00 | +0.09% | +3.47% | $90,656 → $114,377 |
| Building | General Government | 36.61 → 38.61 | +0.76% | +3.11% | $69,659 → $81,831 |
| Public Works | Public Works | 130.38 → 133.91 | +0.38% | +2.22% | $62,526 → $70,986 |
| Library | Culture & Recreation | 52.84 → 56.22 | +0.89% | +2.00% | $57,847 → $62,445 |
| Health | Human Services | 18.04 → 26.28 | +5.52% | +3.49% | $52,207 → $45,563 |
| Veterans' Services | Human Services | 2.00 → 2.00 | +0.00% | -0.28% | $85,786 → $84,100 |
| Council on Aging | Human Services | 16.91 → 19.09 | +1.75% | +4.70% | $48,641 → $59,431 |
| Recreation | Culture & Recreation | 12.00 → 11.00 | -1.24% | +2.37% | $66,800 → $85,828 |

## By Schedule A category (rollup used in the departmental forecast diagnosis)

| Category | Total FTE FY19→FY26 | FTE CAGR | $/FTE FY19→FY26 | $/FTE CAGR |
|---|---:|---:|---:|---:|
| General Government | 126.63 → 135.64 | +0.99% | $76,512 → $88,021 | +2.02% |
| Public Safety | 340.80 → 334.30 | -0.27% | $86,805 → $113,423 | +3.89% |
| Public Works | 130.38 → 133.91 | +0.38% | $62,526 → $70,986 | +1.83% |
| Human Services | 36.95 → 47.37 | +3.61% | $52,392 → $52,779 | +0.11% |
| Culture & Recreation | 64.84 → 67.22 | +0.52% | $59,504 → $66,272 | +1.55% |

## Per-department footnotes (from the ERSC report's own table)

- **Select Board**: Added communications officer (moved from DEICR); one grant-funded position eliminated in FY26 so actual total is 9 FTEs, not 10.00 as tabulated.
- **Human Resources**: Generalist/investigator position, FY24 override.
- **DEICR**: Language access coordinator, FY24 override.
- **Finance Department**: Assessing reorganization to meet FY25 budget deficit.
- **Legal Services**: Labor counsel added FY20.
- **Police**: Held open 6 officers and eliminated park security officers; budget book incorrectly shows a reduction of one FTE in FY2026 (corrected in the ERSC report's own table, used here).
- **Building**: Building inspector, short-term rentals, added FY20.
- **Public Works**: Sanitation reduction; FTEs added and moved to soft funds.
- **Council on Aging**: Social worker and transportation coordinator, FY24 override.

## What this deliberately does not do

- **No years between FY2019 and FY2026** - the source table is a two-point comparison, not an annual series. If a fuller annual FTE history is needed for publication, that would require a new research effort (Town budget books year-by-year), not yet done.
- **"Total FTE" combines General Fund-budgeted and soft-money (grant/other-fund) positions** - a real distinction (soft-money FTEs aren't necessarily durable/tax-levy-funded) the source table itself preserves as separate columns (both kept here), but this dataset doesn't take a further stance on which soft-money positions are likely to persist.
