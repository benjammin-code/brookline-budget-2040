# Reserves and Free Cash — Methodology

Companion to `reserves_and_free_cash.csv` and `statewide_fiscal_context.csv`. All cited data; nothing modelled.

things, which must not be conflated

1. **Unassigned general fund balance** - the GAAP residual after nonspendable,
   restricted, committed and assigned amounts. From the audited financial
   statements.
2. **Total general fund balance** - all five categories.
3. **Available fund balance** - Moody's term, meaning committed + assigned +
   unassigned. **For Brookline this equals total GF balance**, because the
   General Fund carries zero nonspendable, restricted and committed balances
   in every year from FY2016 on. This is the figure that belongs in any peer
   or rating comparison, and it is roughly 7.6 points higher than unassigned.
4. **Certified free cash** - the July 1 balance certified annually by the DLS
   Director of Accounts, after deductions the fund balance figures do not make.
   Roughly half to two-thirds of unassigned fund balance in Brookline's case.

## Two labelling traps

**Free cash year labels differ between DLS and the Town.** DLS labels free
cash by the fiscal year that *begins* on that July 1. Brookline's own budget
documents label the same dollars one year later, because the Town appropriates
them in the budget adopted the following spring. **Brookline budget FY = DLS
FY + 1.** The series below uses the DLS convention throughout and states the
as-of date explicitly so the ambiguity cannot propagate.

**GASB 54 broke the fund balance series at FY2011.** Before FY2011 there was
no "unassigned" category; the closest analogue is undesignated fund balance.
The apparent jump from $11.9M (FY2010) to $22.6M (FY2011) is a reclassification,
not a real change. Pre-FY2011 figures are carried here flagged as a different
basis, and **no trend line should cross that boundary.**

## Brookline, audited

| FY | Unassigned | % rev | Available (= total GF) | % rev | vs 20% policy | Certified free cash |
|---|---|---|---|---|---|---|
| 2011 | $22.6M | 10.88% | $23.5M | **11.35%** | -8.65 pp | $7.1M |
| 2012 | $24.8M | 11.57% | $26.0M | **12.14%** | -7.86 pp | $7.1M |
| 2013 | $25.8M | 11.51% | $27.2M | **12.13%** | -7.87 pp | $9.7M |
| 2014 | $23.9M | 10.30% | $26.1M | **11.27%** | -8.73 pp | $7.1M |
| 2015 | $22.6M | 9.70% | $24.6M | **10.55%** | -9.45 pp | $7.6M |
| 2016 | $21.3M | 8.52% | $28.8M | **11.51%** | -8.49 pp | $7.8M |
| 2017 | $23.4M | 8.45% | $33.7M | **12.17%** | -7.83 pp | $10.9M |
| 2018 | $24.7M | 8.45% | $35.7M | **12.20%** | -7.80 pp | $11.2M |
| 2019 | $26.6M | 8.64% | $37.9M | **12.29%** | -7.71 pp | $11.9M |
| 2020 | $26.6M | 8.04% | $40.4M | **12.23%** | -7.77 pp | $14.4M |
| 2021 | $29.5M | 8.53% | $43.1M | **12.44%** | -7.56 pp | $13.0M |
| 2022 | $49.0M | 13.58% | $62.4M | **17.30%** | -2.70 pp | $14.2M |
| 2023 | $62.4M | 16.83% | $78.4M | **21.14%** | +1.14 pp | $22.8M |
| 2024 | $60.1M | 15.33% | $89.8M | **22.91%** | +2.91 pp | $25.1M |

Available fund balance moved from **11.35%** of revenue in FY2011 to **22.91%** in FY2024, and now sits **+2.91 points** against the Town's own 20% policy floor. Moody's Aaa median for the same measure is **61.7%**, so Brookline meets its own standard and remains well below its rating peers. Both are true and they answer different questions.

## Statewide context

| FY | Statewide free cash | Override munis | Requested | Approved | Pass rate | Munis at levy limit |
|---|---|---|---|---|---|---|
| 2010 | — | — | — | — | — | 257 |
| 2015 | — | — | — | — | — | 166 |
| 2017 | $1.64B | 21 | $19.1M | $3.9M | 54% | — |
| 2018 | $1.71B | 18 | $12.1M | $8.8M | 60% | — |
| 2019 | $1.75B | 26 | $40.1M | $31.4M | 82% | — |
| 2020 | $1.92B | 26 | $35.9M | $33.3M | 76% | 169 |
| 2021 | $1.95B | 14 | $17.5M | $10.7M | 57% | — |
| 2022 | $2.33B | 14 | $28.3M | $19.2M | 86% | — |
| 2023 | $2.65B | 12 | $19.5M | $6.8M | 82% | 148 |
| 2024 | $2.76B | 34 | $70.3M | $52.0M | 74% | 153 |
| 2025 | $3.02B | 42 | $117.2M | $48.2M | 45% | 173 |
| 2026 | $2.89B | 57 | $165.0M | $75.3M | 46% | 186 |
| 2027 | — | 54 | $210.9M | $126.5M | 62% | — |

Statewide certified free cash fell **4.6%** in FY2026, which DLS described as the first decrease since the Great Recession. Override dollars requested rose roughly tenfold between FY2023 and FY2027 while the pass rate fell to 45-46% in FY2025 and FY2026. Municipalities within half a point of their levy limit went from 148 in FY2023 to 186 in FY2026.

For the other side of that picture: MMA and Tufts cSPA find that **nearly 200 of 351 municipalities have pursued zero overrides in the last fifteen years**, and that unrestricted state aid has fallen **25% in real terms since 2002**. Brookline's own state aid grew at 1.9% a year over FY2005-2025 against operating costs at 3.65%, so the statewide pattern and the local one are the same pattern.

## Sources

- Fund balance FY2011-FY2024: Brookline Audited Financial Statements, the
  Governmental Funds balance sheet, General Fund column. Percentages use total
  General Fund revenues from the Statement of Revenues, Expenditures and
  Changes in Fund Balances. Reproduces the 2020 BFAC report's FY2014-FY2019
  figures to the cent.
- **There is no FY2025 audit.** Verified three ways as of 2026-09-13,
  including the Town's own statement in the FY2027 Financial Plan that FY25
  free cash was uncertified at printing. FY2024 is the most recent audited year.
- Certified free cash: MA DLS Databank, "Certified Free Cash as Percent of
  Budget," cross-checked against the signed DLS certification worksheets.
- Statewide free cash: same DLS report, summed across all municipalities.
  DLS publishes no statewide total itself; the FY2026 sum reconciles to the
  $2.88 billion DLS reported narratively in June 2026.

## The Town's own reserve policy

The FY2027 Financial Plan states two different targets. The narrative Free
Cash section gives 10% of revenue; the formal Reserve Policies in the Appendix
state **"no less than 20% of revenue, with a goal of accruing a balance that
falls within the median of Massachusetts Aaa rated communities,"** attributed
to changes in Moody's metrics. The Appendix policy is the governing text and
the narrative appears stale, so 20% is used here as the policy line.

Moody's February 2024 credit opinion names its own downgrade trigger as
available reserves falling below 20% of revenue, so the Town's policy and the
agency's trigger sit at the same number.
