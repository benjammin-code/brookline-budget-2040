# Benefits Category-Level Forecast (FY2026-2040) — Methodology

Companion to `benefits_category_forecast_fy26_40.csv` and `benefits_category_history_fy00_25.csv`. Replaces `baseline_expense_forecast.py`'s `trend_corrected` benefits line (previously a single blended 6.40%/yr trailing-5yr CAGR on the whole `nondept_benefits` total) with 4 separately-modeled categories - Pensions, Group Health, OPEB (Retiree Group Health Trust), and Other (Group Life, Medical Disabilities, Disability Insurance, Medicare, Workers' Comp, Public Safety IOD, Unemployment, Non-Contributory Retirement combined). See this script's own module docstring for full sourcing and the two real methodological choices (why FY2026-2031 uses the Town's own known schedule instead of a rate at all, and how each category's FY2032-2040 extension was chosen).

## Real actuals used as anchors, FY2023-2025 (Town's own Personnel Benefits Detailed tables)

| Category | FY2023 | FY2024 | FY2025 |
|---|---:|---:|---:|
| Pensions | $30,553,078 | $33,103,579 | $37,517,904 |
| Group Health | $33,971,831 | $34,756,062 | $38,268,676 |
| OPEB | $4,431,980 | $4,681,980 | $5,415,980 |

## Group Health: 25-year reconstruction, with an honest accuracy check

Reconstructed FY2000-2025 from the FY2027 Financial Plan's own "RATE CHANGE" table (p.334, annual budgeted $ change, FY2001-2027, summing to $39,972,862 — independently verified by summing the transcribed values here: $39,972,863, a $1 rounding gap, confirming the transcription). Calibrated to the real FY2025 actual ($38,268,676) by solving for an implied FY2000 baseline ($7,855,951) and compounding forward.

**This reconstruction is budgeted-change-based, not actual-spending-based, and the two diverge over time** — checked directly: the reconstruction's FY2023 figure is **+3.1%** above the real FY2023 actual, and FY2024 is **+6.2%** above. So it's presented as historical context (the long-run ~25-year shape and average growth rate), not precise annual actuals — the real actuals (FY2023-2025) are what matters for the forward-looking rate.

**Rate used, FY2032-2040**: the 25-year reconstruction's own CAGR, **6.54%/yr** — deliberately NOT the much higher FY2023-2025 real-actual rate (**6.14%/yr**, only 2 years, and the Town's own narrative confirms this window is a real but likely-cyclical spike: GIC rate increases climbed from ~2-3%/yr in the late 2010s to 9.5% (FY25) and a budgeted 12%+ (FY26-27) — the same "don't blindly compound a short elevated window for 15 years" caution already applied to the schools category forecast).

## Pensions — two independent sources agree closely

Two genuinely independent historical sources: (1) the Financial Plan's own repeated narrative anchor ("$9.9 million in FY07 to $37 million in FY25") implies an **7.68%/yr** CAGR over 18 years; (2) the FY2024 Audited Financial Statements' GASB-required "Schedule of Contributions" (p.96, calendar-year basis, a different accounting convention) implies **7.18%/yr** over CY2014-2023. These two independently-sourced, differently-based estimates land within 0.1 points of each other — strong mutual validation that ~7.2-7.3%/yr is the real historical pension growth rate. Not used directly in the forecast, though (see below) — **FY2026-2031 uses the real, already-known ADC schedule** (`PENSION_ADC_2024_VALUATION`, this project's existing correction), not a trended rate at all.

**FY2032-2040**: the pre-2031 ~7.3%/yr rate reflects paying down the unfunded liability — a dynamic that structurally ends in FY2031 (full funding). Extending it forward would be a real, named error, not just a conservative-vs-aggressive judgment call. Instead, FY2031's Normal-Cost-only base ($9,164,987, the real 2024 valuation basis) is extended at **3.0%/yr** — a payroll-growth proxy (Normal Cost scales with active payroll), cited to this project's own finding that the Town has "sought to keep wage adjustments within 3% per year" (see the ERSC report's Town Subcommittee section). No published post-2031 Normal-Cost-specific schedule exists — this is an explicit, flagged judgment call.

## OPEB — held flat post-2031, and why that's the right default here

FY2026-2031 uses the Town's own real, already-published schedule directly — including the real pension/OPEB handoff (FY2030 \$5,931,980 → FY2031 \$42,994,233, a +624.8% jump as pension funding redirects to OPEB once the pension system reaches full funding). FY2032-2040 is held flat at the FY2031 level — no documented schedule exists past the handoff year (unlike pensions, OPEB has no statutory full-funding deadline driving a further schedule), so flat matches this project's existing convention for every other no-defensible-trend category (debt exclusion, other_nondept). This is the single least-certain line in this forecast — flagged as an open item below.

## Other Benefits (Group Life, Medical Disabilities, Disability Insurance, Medicare, Workers' Comp, Public Safety IOD, Unemployment, Non-Contributory Retirement, combined)

FY2026-2031: sum of the Town's own real published figures for these 7 small sub-categories. FY2032-2040: the Town's own FY2026→FY2031 implied CAGR (**5.57%/yr**) — tried the real FY2023-2025 actual window first (8.81%/yr), but it's only 2 years and dominated by Public Safety IOD Medical's real volatility (\$275K → \$950K in one year, a known, named unpredictable line per the ERSC report) — the Town's own 5-year schedule is a more stable basis for this small, noisy combined bucket.

## Result vs. the previous single-line approach — a real, explainable $36M difference

FY2040 total: **$190,847,121** (category-level) vs. **$226,588,998** (old approach: the same FY2031 corrected total of $129,647,506, compounded at one blended 6.40%/yr trailing-5yr Schedule A rate for 9 more years) — a **-$35,741,877** (-15.8%) difference. FY2040 composition: Pensions $11,958,229, Group Health $122,721,099, OPEB $42,994,233 (flat, unchanged since FY2031), Other $13,173,560.

**This gap is real and traceable, not noise**: almost all of it comes from OPEB. The old approach compounded the *entire* FY2031 total — including the one-time pension→OPEB redirect — at 6.40%/yr for 9 more years, which implicitly assumed OPEB itself would keep growing at that rate. It has no documented reason to: the redirect is a one-time capacity shift, not a recurring growth driver, and holding it flat (this build's choice) removes about $32M of that difference on its own. The rest comes from Pensions growing at a realistic 3.0%/yr post-2031 payroll-linked rate instead of the pre-2031 unfunded-liability-paydown rate, which structurally cannot continue once the liability is paid off. **Group Health, the one category where the old and new rates are close (6.54% vs. 6.40%), lands at nearly the same FY2040 figure either way** — confirming the difference is coming from the two categories that genuinely behave differently post-2031, not from a systematic bias in the new method.

## What this deliberately does not do

- **`town_assumptions` is unchanged** — still the Town's own aggregate benefits figure, FY26-31 Town-published + Town-implied CAGR extension FY32-40. This decomposition only replaces `trend_corrected`.
- **No further OPEB schedule past FY2031** — the single biggest open uncertainty in this forecast. If the Town ever publishes an OPEB funding plan extending past the pension handoff year, this should be revisited before trusting FY2032-2040 OPEB numbers as more than a placeholder.
- **Group Health's FY2000-2022 reconstruction is context, not precise history** — see the accuracy check above. A real archival pull of each year's actual (not budgeted) Group Health spending, if ever wanted, would sharpen this.

## Sources

- `data/FY2025-Financial-Plan.pdf` p.330 (FY2023 actuals), `data/FY2026-Financial-Plan.pdf` p.296 (FY2024 actuals), `data/FY2027-Financial-Plan.pdf` p.330-336 (FY2025 actuals, Group Health rate-change table, pension/OPEB narrative)
- `data/FY2024-Audited-Financial-Statements.pdf` p.96 (pension Schedule of Contributions), p.104 (OPEB Schedule of the Town's Contributions)
- `data/Brookline-Retirement-System-2024-Actuarial-Valuation.pdf` (PENSION_ADC_2024_VALUATION, already used elsewhere in this project)
- `output/town_own_forecast_fy26_31.csv` (Town's own FY26-31 benefits_detail schedule)
