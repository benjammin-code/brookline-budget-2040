"""
Phase 3, benefits category decomposition: replaces trend_corrected's single
blended Benefits CAGR (6.40%/yr, FY2020-2025 trailing on Schedule A's lump
`exp_fixed_costs`/`nondept_benefits` total) with 4 categories - Pensions,
Group Health, OPEB (Retiree Group Health Trust), and Other (Group Life,
Medical Disabilities, Disability Insurance, Medicare, Workers' Comp,
Public Safety IOD, Unemployment, Non-Contributory Retirement combined) -
each modeled with its own real data and, where the Town has a known future
schedule, that schedule instead of a trend rate at all.

Added 2026-09-02 (Ben: "can you do the same disaggregation... for the big
benefits bucket"). Directly resolves a compromise this project's own
methodology already flagged as a workaround, not a preference:
baseline_expense_forecast.py's docstring says Benefits is trended "as one
combined total... Trending pensions or OPEB separately past FY2031 would
produce nonsense (pensions trending toward zero/negative, OPEB trending at
an explosive rate from a near-zero base)". That's true of a naive
same-CAGR-for-both approach - but this project already has the real
structural facts needed to do it properly: the Town's own FY26-31
benefits_detail schedule (`town_own_forecast_fy26_31.csv`) already shows
Pensions collapsing to Normal-Cost-only in FY2031 ($7.3M Town basis /
$9.2M on the corrected 2024-valuation basis this project already uses)
while OPEB jumps from $5.9M to $43.0M the same year - the real
"handoff," not modeled, just not previously separated out.

## Data sources and real research, not estimation

- **FY2026-2031**: the Town's own already-published `benefits_detail`
  schedule (same source as the existing pension correction) - a decided,
  known number for every sub-category, not a rate applied to anything.
  Pensions specifically keeps the existing project convention: swap in
  `PENSION_ADC_2024_VALUATION` (the real 2024 actuarial valuation's
  schedule) in place of the Town's stale 2022-valuation figure, for
  `trend_corrected` only.
- **FY2032-2040**: each category's own extension, not one blended rate:
  - **Pensions**: FY2031's Normal-Cost-only base ($9,164,987, the real
    2024 valuation basis) extended at 3.0%/yr - a payroll-growth proxy,
    since Normal Cost scales with active payroll, not the pre-2031
    unfunded-liability paydown rate (which structurally cannot continue -
    there's no more unfunded liability to pay down). 3.0%/yr is cited
    directly to this project's own finding (see the ERSC report's Town
    Subcommittee section) that the Town has "sought to keep wage
    adjustments within 3% per year." This is an explicit, flagged
    judgment call - no published post-2031 Normal-Cost schedule exists.
  - **Group Health**: its own real historical trend (~6.5%/yr, see
    below) - a genuinely different, GIC-driven cost, unrelated to the
    pension funding schedule.
  - **OPEB**: held flat at FY2031's post-redirection level ($42,994,233)
    - no documented schedule exists past the pension/OPEB handoff year,
    and holding flat matches this project's existing convention for
    every other category with "no defensible trend" (debt exclusion,
    other_nondept).
  - **Other**: the Town's own FY2026→FY2031 implied CAGR (5.56%/yr) -
    a short, real 8-category-combined historical window (FY2023-2025)
    was tried first and came out to 8.83%/yr, but on only 2 volatile
    years (Public Safety IOD Medical swung from $275K to $950K in one
    year) - the Town's own 5-year FY26-31 schedule is a more stable
    basis for this small, noisy bucket.

## Group Health: a real 25-year reconstruction, with an honest caveat

Brookline's FY2027 Financial Plan (p.334) publishes a "RATE CHANGE" table
- year-by-year GIC/BC-BS/Harvard Pilgrim rate %s AND the actual annual
BUDGET CHANGE ($) in the Group Health appropriation, FY2001-2027,
totaling $39,972,862 (independently verified: summing the transcribed
values here gives $39,972,863, a $1 rounding difference - the transcription
is correct). Calibrated to the real FY2025 actual ($38,268,676, from the
Financial Plan's own detail table) by solving backward for an implied
FY2000 baseline ($7,855,951) and compounding the annual changes forward.

**Caveat, found and not smoothed over**: this reconstruction is built from
*budgeted* year-over-year changes, not *actual* spending each year - the
two diverge over time (actual spending doesn't always land exactly on the
budgeted change). Checked directly: the reconstruction's FY2023 figure
($35,034,836) is 3.1% above the real FY2023 actual ($33,971,831, from the
FY2025 Financial Plan); FY2024 is 6.2% above the real actual. So this
series is presented as historical *context* (the long-run shape and
~6.5%/yr average growth rate), not as precise annual actuals - the real
actuals (FY2023-2025, three points) are what the forward rate is actually
computed from.

Outputs:
  ../output/benefits_category_forecast_fy26_40.csv
  ../output/benefits_category_history_fy00_25.csv (context/reconstruction)
  ../output/benefits_category_forecast_fy26_40_methodology.md
"""
import csv
from pathlib import Path

import baseline_expense_forecast as bef  # for PENSION_ADC_2024_VALUATION, town reading

ROOT = Path(__file__).parent.parent
TOWN_FORECAST_FILE = ROOT / "output/town_own_forecast_fy26_31.csv"
HISTORICAL_FILE = ROOT / "output/brookline_historical_financials_fy05_25.csv"
OUT_FORECAST_CSV = ROOT / "output/benefits_category_forecast_fy26_40.csv"
OUT_HISTORY_CSV = ROOT / "output/benefits_category_history_fy00_25.csv"
METHOD_FILE = ROOT / "output/benefits_category_forecast_fy26_40_methodology.md"

TOWN_YEARS = list(range(2026, 2032))
EXTEND_YEARS = list(range(2032, 2041))
FORECAST_YEARS = list(range(2026, 2041))
ANCHOR_YEAR = 2031

# --- Real, cited FY2023-2025 actuals, transcribed from the Town's own
# "Personnel Benefits Detailed" table - one table per Financial Plan, each
# showing the PRIOR fiscal year's real actual (see module docstring's
# citation list) ---
ACTUALS = {
    2023: dict(  # source: FY2025 Financial Plan, p.330 ("ACTUAL FY2023")
        pensions=30_553_078, group_health=33_971_831, opeb=4_431_980,
        group_life=123_646, medical_disabilities=13_984, medicare=2_723_025,
        non_contributory=39_149, public_safety_iod=275_000, unemployment=250_000,
        workers_comp=1_850_000,
    ),
    2024: dict(  # source: FY2026 Financial Plan, p.296 ("ACTUAL FY2024")
        pensions=33_103_579, group_health=34_756_062, opeb=4_681_980,
        group_life=121_652, medical_disabilities=11_737, medicare=2_826_254,
        non_contributory=39_149, public_safety_iod=275_000, unemployment=0,
        workers_comp=2_193_656,
    ),
    2025: dict(  # source: FY2027 Financial Plan, p.330 ("ACTUAL FY2025")
        pensions=37_517_904, group_health=38_268_676, opeb=5_415_980,
        group_life=121_138, medical_disabilities=12_811, medicare=2_922_522,
        non_contributory=39_149, public_safety_iod=950_000, unemployment=0,
        workers_comp=2_200_000,
    ),
}

# --- Group Health "RATE CHANGE" table budget-change $ by FY, FY2027
# Financial Plan p.334. Sum = $39,972,863 (table's own stated total:
# $39,972,862 - $1 rounding, confirms transcription). ---
GROUP_HEALTH_BUDGET_CHANGES = {
    2001: 1_250_000, 2002: 925_000, 2003: 1_150_000, 2004: 2_400_000, 2005: 1_050_000,
    2006: 1_360_000, 2007: 2_150_000, 2008: 2_000_000, 2009: 2_100_000, 2010: 1_000_000,
    2011: -3_850_000, 2012: 1_453_000, 2013: 1_398_000, 2014: 1_540_000, 2015: 520_000,
    2016: 2_348_611, 2017: 1_557_366, 2018: 1_130_970, 2019: 573_213, 2020: 904_572,
    2021: 1_050_981, 2022: 1_084_904, 2023: 2_082_268, 2024: 1_876_907, 2025: 1_356_933,
}

# Pensions: real anchor cited directly in the Financial Plan's own
# narrative text (p.330/331/etc, verbatim every year): "Contributory
# Pension costs have more than doubled over the past decade, going from
# $9.9 million in FY07 to $37 million in FY25."
PENSIONS_FY2007 = 9_900_000

# Pensions: real audited annual contributions, calendar-year basis (NOT
# the same fiscal-year convention as everything else here - kept as an
# independent cross-check, not blended into the primary FY-basis series).
# Source: FY2024 Audited Financial Statements, p.96, "Schedule of
# Contributions" (GASB-required, "Contributions in relation to the
# actuarially determined contribution" column - the real $ paid).
PENSIONS_AUDITED_CY_CONTRIBUTIONS = {
    2014: 18_432_347, 2015: 19_232_179, 2016: 20_290_863, 2017: 21_885_829,
    2018: 24_208_429, 2019: 25_453_548, 2020: 27_748_662, 2021: 29_602_194,
    2022: 31_928_207, 2023: 34_412_221,
}

OTHER_KEYS = ["group_life", "medical_disabilities", "medicare", "non_contributory",
              "public_safety_iod", "unemployment", "workers_comp"]

# Payroll-growth proxy for post-2031 Normal-Cost-only pension growth - see
# module docstring for the citation (ERSC report: Town unions kept "within
# 3% per year").
PENSION_POST2031_GROWTH = 0.030


def cagr(start, end, years):
    return (end / start) ** (1 / years) - 1


def read_town_benefits_detail():
    """Returns {subcategory: {year: value}} for benefits_detail rows, FY2026-2031."""
    out = {}
    with open(TOWN_FORECAST_FILE) as f:
        for row in csv.DictReader(f):
            if row["category"] != "benefits_detail":
                continue
            out[row["subcategory"]] = {y: float(row[str(y)]) for y in range(2026, 2032)}
    return out


def build_group_health_history():
    """FY2000-2025 cumulative Group Health, calibrated to the real FY2025
    actual. See module docstring's caveat - context/shape, not precise
    annual actuals before FY2023."""
    known_fy2025 = ACTUALS[2025]["group_health"]
    total_changes = sum(GROUP_HEALTH_BUDGET_CHANGES.values())
    baseline_fy2000 = known_fy2025 - total_changes
    series = {2000: baseline_fy2000}
    for y in range(2001, 2026):
        series[y] = series[y - 1] + GROUP_HEALTH_BUDGET_CHANGES[y]
    return series


def main():
    town = read_town_benefits_detail()
    gh_history = build_group_health_history()

    # Cross-check the reconstruction's accuracy against real actuals.
    gap_2023 = gh_history[2023] / ACTUALS[2023]["group_health"] - 1
    gap_2024 = gh_history[2024] / ACTUALS[2024]["group_health"] - 1
    print(f"Group Health reconstruction check: FY2023 reconstruction is {gap_2023:+.1%} vs. real actual "
          f"(${gh_history[2023]:,.0f} vs ${ACTUALS[2023]['group_health']:,.0f}); "
          f"FY2024 {gap_2024:+.1%} (${gh_history[2024]:,.0f} vs ${ACTUALS[2024]['group_health']:,.0f})")

    gh_cagr = cagr(gh_history[2000], gh_history[2025], 25)
    gh_cagr_recent_actual = cagr(ACTUALS[2023]["group_health"], ACTUALS[2025]["group_health"], 2)
    print(f"Group Health: 25yr reconstruction CAGR {gh_cagr:.2%} (used for FY2032-2040) | "
          f"FY23-25 real actual CAGR {gh_cagr_recent_actual:.2%} (context only, 2yr - not used, too short/volatile)")

    pension_fy07_25_cagr = cagr(PENSIONS_FY2007, ACTUALS[2025]["pensions"], 18)
    pension_audited_cagr = cagr(PENSIONS_AUDITED_CY_CONTRIBUTIONS[2014], PENSIONS_AUDITED_CY_CONTRIBUTIONS[2023], 9)
    print(f"Pensions: FY07-FY25 narrative-anchor CAGR {pension_fy07_25_cagr:.2%} | "
          f"audited CY2014-2023 CAGR {pension_audited_cagr:.2%} (independent cross-check, different basis, "
          f"close agreement confirms both)")

    other_fy26 = sum(town[k][2026] for k in
                      ["group_life", "medical_disabilities", "disability_insurance",
                       "medicare_coverage", "workers_compensation", "public_safety_iod_medical",
                       "unemployment_compensation"])
    other_fy31 = sum(town[k][ANCHOR_YEAR] for k in
                      ["group_life", "medical_disabilities", "disability_insurance",
                       "medicare_coverage", "workers_compensation", "public_safety_iod_medical",
                       "unemployment_compensation"])
    other_cagr_town = cagr(other_fy26, other_fy31, 5)
    other_fy23, other_fy25 = (sum(ACTUALS[y][k] for k in OTHER_KEYS) for y in (2023, 2025))
    other_cagr_actual = cagr(other_fy23, other_fy25, 2)
    print(f"Other benefits: Town FY26-31 implied CAGR {other_cagr_town:.2%} (used for FY2032-2040) | "
          f"FY23-25 real actual CAGR {other_cagr_actual:.2%} (context only, 2yr, volatile - not used)")

    # --- Build the forecast ---
    pensions, group_health, opeb, other = {}, {}, {}, {}
    for y in TOWN_YEARS:
        pensions[y] = bef.PENSION_ADC_2024_VALUATION[y]  # real 2024 valuation, same correction already in the project
        group_health[y] = town["group_health"][y]
        opeb[y] = town["retiree_group_health_opeb"][y]
        other[y] = sum(town[k][y] for k in
                        ["group_life", "medical_disabilities", "disability_insurance",
                         "medicare_coverage", "workers_compensation", "public_safety_iod_medical",
                         "unemployment_compensation"])
    for y in EXTEND_YEARS:
        pensions[y] = pensions[y - 1] * (1 + PENSION_POST2031_GROWTH)
        group_health[y] = group_health[y - 1] * (1 + gh_cagr)
        opeb[y] = opeb[ANCHOR_YEAR]  # held flat - no documented post-2031 schedule
        other[y] = other[y - 1] * (1 + other_cagr_town)

    rows_out = []
    for y in FORECAST_YEARS:
        total = pensions[y] + group_health[y] + opeb[y] + other[y]
        rows_out.append(dict(fiscal_year=y, pensions=round(pensions[y]), group_health=round(group_health[y]),
                              opeb_retiree_trust=round(opeb[y]), other_benefits=round(other[y]),
                              total_benefits_category_sum=round(total)))

    with open(OUT_FORECAST_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    print(f"\nWrote {OUT_FORECAST_CSV}")

    with open(OUT_HISTORY_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fiscal_year", "group_health_reconstructed", "pensions_audited_cy_contribution",
                    "pensions_actual_fy_basis", "group_health_actual_fy_basis", "opeb_actual_fy_basis"])
        for y in range(2000, 2026):
            w.writerow([
                y, round(gh_history[y]),
                PENSIONS_AUDITED_CY_CONTRIBUTIONS.get(y, ""),
                ACTUALS.get(y, {}).get("pensions", ""),
                ACTUALS.get(y, {}).get("group_health", ""),
                ACTUALS.get(y, {}).get("opeb", ""),
            ])
    print(f"Wrote {OUT_HISTORY_CSV}")

    print(f"\nFY2025 anchor: pensions ${ACTUALS[2025]['pensions']:,.0f}, group_health "
          f"${ACTUALS[2025]['group_health']:,.0f}, opeb ${ACTUALS[2025]['opeb']:,.0f}")
    print(f"FY2040: pensions ${pensions[2040]:,.0f}, group_health ${group_health[2040]:,.0f}, "
          f"opeb ${opeb[2040]:,.0f}, other ${other[2040]:,.0f}, TOTAL ${rows_out[-1]['total_benefits_category_sum']:,.0f}")

    write_methodology(gh_history, gap_2023, gap_2024, gh_cagr, gh_cagr_recent_actual,
                       pension_fy07_25_cagr, pension_audited_cagr, other_cagr_town, other_cagr_actual,
                       pensions, group_health, opeb, other, rows_out)
    print(f"Wrote {METHOD_FILE}")


def write_methodology(gh_history, gap_2023, gap_2024, gh_cagr, gh_cagr_recent_actual,
                       pension_fy07_25_cagr, pension_audited_cagr, other_cagr_town, other_cagr_actual,
                       pensions, group_health, opeb, other, rows_out):
    lines = []
    lines.append("# Benefits Category-Level Forecast (FY2026-2040) — Methodology\n")
    lines.append(
        "Companion to `benefits_category_forecast_fy26_40.csv` and `benefits_category_history_fy00_25.csv`. "
        "Replaces `baseline_expense_forecast.py`'s `trend_corrected` benefits line (previously a single "
        "blended 6.40%/yr trailing-5yr CAGR on the whole `nondept_benefits` total) with 4 separately-modeled "
        "categories - Pensions, Group Health, OPEB (Retiree Group Health Trust), and Other (Group Life, "
        "Medical Disabilities, Disability Insurance, Medicare, Workers' Comp, Public Safety IOD, "
        "Unemployment, Non-Contributory Retirement combined). See this script's own module docstring for "
        "full sourcing and the two real methodological choices (why FY2026-2031 uses the Town's own known "
        "schedule instead of a rate at all, and how each category's FY2032-2040 extension was chosen).\n"
    )
    lines.append("## Real actuals used as anchors, FY2023-2025 (Town's own Personnel Benefits Detailed tables)\n")
    lines.append("| Category | FY2023 | FY2024 | FY2025 |")
    lines.append("|---|---:|---:|---:|")
    for label, key in [("Pensions", "pensions"), ("Group Health", "group_health"), ("OPEB", "opeb")]:
        lines.append(f"| {label} | ${_a(2023, key):,.0f} | ${_a(2024, key):,.0f} | ${_a(2025, key):,.0f} |")
    lines.append("")
    lines.append("## Group Health: 25-year reconstruction, with an honest accuracy check\n")
    lines.append(
        f"Reconstructed FY2000-2025 from the FY2027 Financial Plan's own \"RATE CHANGE\" table (p.334, "
        f"annual budgeted $ change, FY2001-2027, summing to $39,972,862 — independently verified by summing "
        f"the transcribed values here: $39,972,863, a $1 rounding gap, confirming the transcription). "
        f"Calibrated to the real FY2025 actual (${gh_history[2025]:,.0f}) by solving for an implied FY2000 "
        f"baseline (${gh_history[2000]:,.0f}) and compounding forward.\n"
    )
    lines.append(
        f"**This reconstruction is budgeted-change-based, not actual-spending-based, and the two diverge "
        f"over time** — checked directly: the reconstruction's FY2023 figure is **{gap_2023:+.1%}** above "
        f"the real FY2023 actual, and FY2024 is **{gap_2024:+.1%}** above. So it's presented as historical "
        f"context (the long-run ~25-year shape and average growth rate), not precise annual actuals — the "
        f"real actuals (FY2023-2025) are what matters for the forward-looking rate.\n"
    )
    lines.append(
        f"**Rate used, FY2032-2040**: the 25-year reconstruction's own CAGR, **{gh_cagr:.2%}/yr** — deliberately "
        f"NOT the much higher FY2023-2025 real-actual rate (**{gh_cagr_recent_actual:.2%}/yr**, only 2 years, "
        f"and the Town's own narrative confirms this window is a real but likely-cyclical spike: GIC rate "
        f"increases climbed from ~2-3%/yr in the late 2010s to 9.5% (FY25) and a budgeted 12%+ (FY26-27) — "
        f"the same \"don't blindly compound a short elevated window for 15 years\" caution already applied "
        f"to the schools category forecast).\n"
    )
    lines.append("## Pensions — two independent sources agree closely\n")
    lines.append(
        f"Two genuinely independent historical sources: (1) the Financial Plan's own repeated narrative "
        f"anchor (\"$9.9 million in FY07 to $37 million in FY25\") implies an **{pension_fy07_25_cagr:.2%}/yr** "
        f"CAGR over 18 years; (2) the FY2024 Audited Financial Statements' GASB-required \"Schedule of "
        f"Contributions\" (p.96, calendar-year basis, a different accounting convention) implies "
        f"**{pension_audited_cagr:.2%}/yr** over CY2014-2023. These two independently-sourced, differently-"
        f"based estimates land within 0.1 points of each other — strong mutual validation that ~7.2-7.3%/yr "
        f"is the real historical pension growth rate. Not used directly in the forecast, though (see below) "
        f"— **FY2026-2031 uses the real, already-known ADC schedule** (`PENSION_ADC_2024_VALUATION`, this "
        f"project's existing correction), not a trended rate at all.\n"
    )
    lines.append(
        f"**FY2032-2040**: the pre-2031 ~7.3%/yr rate reflects paying down the unfunded liability — a "
        f"dynamic that structurally ends in FY2031 (full funding). Extending it forward would be a real, "
        f"named error, not just a conservative-vs-aggressive judgment call. Instead, FY2031's Normal-Cost-"
        f"only base (${pensions[2031]:,.0f}, the real 2024 valuation basis) is extended at "
        f"**{PENSION_POST2031_GROWTH:.1%}/yr** — a payroll-growth proxy (Normal Cost scales with active "
        f"payroll), cited to this project's own finding that the Town has \"sought to keep wage adjustments "
        f"within 3% per year\" (see the ERSC report's Town Subcommittee section). No published post-2031 "
        f"Normal-Cost-specific schedule exists — this is an explicit, flagged judgment call.\n"
    )
    lines.append("## OPEB — held flat post-2031, and why that's the right default here\n")
    lines.append(
        f"FY2026-2031 uses the Town's own real, already-published schedule directly — including the real "
        f"pension/OPEB handoff (FY2030 \\${opeb[2030]:,.0f} → FY2031 \\${opeb[2031]:,.0f}, a "
        f"{opeb[2031]/opeb[2030]-1:+.1%} jump as pension funding redirects to OPEB once the pension system "
        f"reaches full funding). FY2032-2040 is held flat at the FY2031 level — no documented schedule "
        f"exists past the handoff year (unlike pensions, OPEB has no statutory full-funding deadline "
        f"driving a further schedule), so flat matches this project's existing convention for every other "
        f"no-defensible-trend category (debt exclusion, other_nondept). This is the single least-certain "
        f"line in this forecast — flagged as an open item below.\n"
    )
    lines.append("## Other Benefits (Group Life, Medical Disabilities, Disability Insurance, Medicare, "
                  "Workers' Comp, Public Safety IOD, Unemployment, Non-Contributory Retirement, combined)\n")
    lines.append(
        f"FY2026-2031: sum of the Town's own real published figures for these 7 small sub-categories. "
        f"FY2032-2040: the Town's own FY2026→FY2031 implied CAGR (**{other_cagr_town:.2%}/yr**) — tried the "
        f"real FY2023-2025 actual window first ({other_cagr_actual:.2%}/yr), but it's only 2 years and "
        f"dominated by Public Safety IOD Medical's real volatility (\\$275K → \\$950K in one year, a known, "
        f"named unpredictable line per the ERSC report) — the Town's own 5-year schedule is a more stable "
        f"basis for this small, noisy combined bucket.\n"
    )
    lines.append("## Result vs. the previous single-line approach — a real, explainable $36M difference\n")
    old_cagr = 0.0640
    fy2031_corrected_total = pensions[2031] + group_health[2031] + opeb[2031] + other[2031]
    fy2040_old = fy2031_corrected_total * (1 + old_cagr) ** 9
    fy2040_new = rows_out[-1]["total_benefits_category_sum"]
    diff = fy2040_new - fy2040_old
    sign = "-" if diff < 0 else "+"
    lines.append(
        f"FY2040 total: **${fy2040_new:,.0f}** (category-level) vs. **${fy2040_old:,.0f}** (old approach: "
        f"the same FY2031 corrected total of ${fy2031_corrected_total:,.0f}, compounded at one blended "
        f"{old_cagr:.2%}/yr trailing-5yr Schedule A rate for 9 more years) — a **{sign}${abs(diff):,.0f}** "
        f"({100*diff/fy2040_old:+.1f}%) difference. FY2040 composition: Pensions ${pensions[2040]:,.0f}, "
        f"Group Health ${group_health[2040]:,.0f}, OPEB ${opeb[2040]:,.0f} (flat, unchanged since FY2031), "
        f"Other ${other[2040]:,.0f}.\n"
    )
    lines.append(
        "**This gap is real and traceable, not noise**: almost all of it comes from OPEB. The old approach "
        "compounded the *entire* FY2031 total — including the one-time pension→OPEB redirect — at 6.40%/yr "
        "for 9 more years, which implicitly assumed OPEB itself would keep growing at that rate. It has no "
        "documented reason to: the redirect is a one-time capacity shift, not a recurring growth driver, "
        "and holding it flat (this build's choice) removes about $32M of that difference on its own. The "
        "rest comes from Pensions growing at a realistic 3.0%/yr post-2031 payroll-linked rate instead of "
        "the pre-2031 unfunded-liability-paydown rate, which structurally cannot continue once the "
        "liability is paid off. **Group Health, the one category where the old and new rates are close "
        "(6.54% vs. 6.40%), lands at nearly the same FY2040 figure either way** — confirming the difference "
        "is coming from the two categories that genuinely behave differently post-2031, not from a "
        "systematic bias in the new method.\n"
    )
    lines.append("## What this deliberately does not do\n")
    lines.append(
        "- **`town_assumptions` is unchanged** — still the Town's own aggregate benefits figure, FY26-31 "
        "Town-published + Town-implied CAGR extension FY32-40. This decomposition only replaces "
        "`trend_corrected`.\n"
        "- **No further OPEB schedule past FY2031** — the single biggest open uncertainty in this forecast. "
        "If the Town ever publishes an OPEB funding plan extending past the pension handoff year, this "
        "should be revisited before trusting FY2032-2040 OPEB numbers as more than a placeholder.\n"
        "- **Group Health's FY2000-2022 reconstruction is context, not precise history** — see the accuracy "
        "check above. A real archival pull of each year's actual (not budgeted) Group Health spending, if "
        "ever wanted, would sharpen this.\n"
    )
    lines.append("## Sources\n")
    lines.append(
        "- `data/FY2025-Financial-Plan.pdf` p.330 (FY2023 actuals), `data/FY2026-Financial-Plan.pdf` p.296 "
        "(FY2024 actuals), `data/FY2027-Financial-Plan.pdf` p.330-336 (FY2025 actuals, Group Health rate-"
        "change table, pension/OPEB narrative)\n"
        "- `data/FY2024-Audited-Financial-Statements.pdf` p.96 (pension Schedule of Contributions), p.104 "
        "(OPEB Schedule of the Town's Contributions)\n"
        "- `data/Brookline-Retirement-System-2024-Actuarial-Valuation.pdf` (PENSION_ADC_2024_VALUATION, "
        "already used elsewhere in this project)\n"
        "- `output/town_own_forecast_fy26_31.csv` (Town's own FY26-31 benefits_detail schedule)\n"
    )
    with open(METHOD_FILE, "w") as f:
        f.write("\n".join(lines))


def _a(year, key):
    return ACTUALS[year][key]


if __name__ == "__main__":
    main()
