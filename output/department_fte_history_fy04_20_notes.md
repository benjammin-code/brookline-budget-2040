# Town General Fund FTE History, FY2004-2027

Source: `data/FY2006/2008/2010/2012/2015/2018/2020-Financial-Plan.pdf` (fetched from the Town's Budget Central archive, brooklinema.gov/851/Budget-Central, which goes back to FY2001) plus the "Net General Funded Positions" row already used in the FY2026/FY2027 Financial Plans for FY2022-2027. Added 2026-09-02 (Ben: "I'd love town FTEs back to 2005 - I think there has been some concern about actual staffing levels"). See this script's own module docstring for the full verification methodology, the Finance/Public Works subtotal-header discovery, and a real, disclosed finding: unlike the cleaner FY2021-2027 series, department-level figures for older years show genuine reclassification between documents (not just recommended-vs-settled refinement) - treat category/townwide trends as solid, individual older-year department figures as approximate.

## Headline: General Fund FTE total, FY2004-2027

| Fiscal Year | General Fund FTE | Source |
|---:|---:|---|
| FY2004 | 684.15 | FY2006 Plan |
| FY2005 | 679.52 | FY2006 Plan |
| FY2006 | 705.52 | FY2010 Plan |
| FY2007 | 702.73 | FY2012 Plan |
| FY2008 | 692.07 | FY2012 Plan |
| FY2009 | 689.40 | FY2012 Plan |
| FY2010 | 676.26 | FY2015 Plan |
| FY2011 | 672.66 | FY2015 Plan |
| FY2012 | 671.45 | FY2015 Plan |
| FY2013 | 674.39 | FY2018 Plan |
| FY2014 | 676.39 | FY2018 Plan |
| FY2015 | 676.39 | FY2020 Plan |
| FY2016 | 680.01 | FY2020 Plan |
| FY2017 | 683.69 | FY2020 Plan |
| FY2018 | 680.69 | FY2020 Plan |
| FY2019 | 685.69 | FY2020 Plan |
| FY2020 | 687.37 | FY2020 Plan |
| FY2022 | 708.49 | Net General Funded Positions, FY2026/FY2027 Financial Plans |
| FY2023 | 712.04 | Net General Funded Positions, FY2026/FY2027 Financial Plans |
| FY2024 | 714.53 | Net General Funded Positions, FY2026/FY2027 Financial Plans |
| FY2025 | 682.99 | Net General Funded Positions, FY2026/FY2027 Financial Plans |
| FY2026 | 675.63 | Net General Funded Positions, FY2026/FY2027 Financial Plans |
| FY2027 | 663.96 | Net General Funded Positions, FY2026/FY2027 Financial Plans |

**FY2004→FY2027: 684.15 → 663.96 FTE (-0.13%/yr over 23 years).** FY2021 has no available figure in this scope (General Fund only) - no source document reports it; left as a gap rather than estimated.

**Read the FY2006 uptick (679.52 → 705.52) with real caution - likely a reporting-convention change, not a staffing event.** The FY2006/FY2008 Plans agree with each other on FY2006-2007; the FY2010/FY2012 Plans (published later) agree with each other too, but ~23-25 FTE higher for the SAME years. Library (+9.6), Public Works (+7.5), and Police (+5.8) account for almost all of it, jumping together at the same document boundary - the signature of a scope/counting change (the FY2010 Plan's own budget message discusses a hiring freeze and retirement-incentive program that year), not 23 real positions added in one year. Not resolved here - both document pairs are internally consistent with themselves; see this script's module docstring for the full reasoning.

## What this deliberately does not do

- **General Fund only, not "All Positions"** - see `department_fte_annual_history.py`'s FY2021-2027 series for the broader (Capital/Grants/Enterprise-inclusive) scope; the two datasets are complementary, not merged, since exact department-level reconciliation between the two scopes isn't cleanly available for every year.
- **No pre-FY2004 data** - FY2004 is the earliest year with a complete department table in any document currently fetched; the archive's FY2001-2003 entries only had Long Range Financial Plan and CIP documents, not the full Program Budget with an FTE table, at least among what's been checked so far.
- **Older-era department-level figures carry more real noise than the modern series** - see the FY2015 example in the module docstring (680.01 vs. 676.39 across two different later documents).
