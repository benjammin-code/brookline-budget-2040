"""
Phase 3, schools category decomposition: replaces trend_corrected's
single blended schools CAGR (3.42%/yr, FY2020-2025 trailing on
Schedule A's lump `exp_education` total) with 9 categories, each grown
at its own trailing rate, using DESE's own End-of-Year Financial Report
function categories (`output/school_spending_by_category_fy09_25.csv` -
see data/SOURCES.md). Directly implements recommendation #1 from
`output/school_budget_drivers_summary.md`: "model categories separately,
not as one blended total."

## Scope-reconciliation - the one non-obvious methodological choice here

DESE's per-pupil categories are NOT on the same accounting basis as this
project's Schedule A `exp_education` total. DESE's "Insurance,
Retirement Programs and Other" category counts school employees'
benefits as school spending (Chapter 70 Net School Spending rules);
Schedule A keeps ALL town employee benefits - schools' included - in
one separate Town-wide "Fixed Costs" bucket (this project's own
`benefits` category, already modeled separately in
baseline_expense_forecast.py). Summing DESE's 9 non-benefits categories
at FY2025 ($22,068/pupil x 7,023 enrollment = ~$155.0M) doesn't exactly
match Schedule A's `exp_education` ($146.4M) either - a residual ~5.5%
gap, expected from two independently-compiled sources on overlapping but
not identical definitions (DESE's Net School Spending includes some
items - e.g., portions of transportation/facility costs - that Schedule
A's DOR-category split allocates elsewhere).

**Fix**: use DESE's 8-category mix as RELATIVE SHARES only (renormalized
to 100%, excluding Insurance/Retirement), applied to the real,
already-modeled Schedule A `exp_education` dollar total at the FY2025
anchor - not DESE's own absolute dollar levels. This keeps the schools
category forecast's total consistent with the rest of Phase 3 (no
double-counting against the separate `benefits` line, no incompatible
parallel total), while still capturing DESE's real, category-specific
GROWTH RATES, which is the actual value-add.

## Growth rate window - deliberately NOT this project's usual trailing-5yr

Every other trend_corrected category in this project (departmental,
schools-as-one-line, benefits) uses a trailing-5yr (FY2020-2025) CAGR,
chosen because "growth has been accelerating... the trailing-5yr figure
is the more current, not the most conservative, choice" (see
baseline_expense_forecast_fy26_40_methodology.md). That reasoning
doesn't transfer cleanly here: several of these 9 categories show a
2-4x acceleration factor between their 5yr and 16yr (FY2009-2025)
CAGRs (Administration 8.66% vs 2.33%; Pupil Services 11.67% vs 5.93%;
Guidance 9.80% vs 4.60%) - a much larger divergence than Departmental's
own mild acceleration (2.96%->3.77%, ~1.27x) or Benefits' (5.53%->6.40%,
~1.16x) that originally justified the trailing-5yr convention. Checked
whether this is a COVID-depressed FY2020 base-year artifact (an
FY2019-2025 6yr CAGR, skipping the COVID trough entirely, should collapse
back toward the 16yr figure if so) - it does NOT: the 6yr figures stay
just as elevated (Administration 9.45%, Pupil Services 10.45%), so this
is a real, sustained recent acceleration, not a base-year artifact.

**Fix**: primary trend_corrected rate here is the 16-year CAGR
(FY2009-2025) - the more conservative, longer, less volatility-prone
window - specifically BECAUSE the divergence magnitude is large enough
that compounding the elevated 5yr/6yr rate for 15 more years to FY2040
would be a real, named forecasting risk (a category at 11.67%/yr
quintuples in 15 years), not a defensible point estimate. The 5yr rate
is still reported, explicitly flagged as an upside-risk cross-check, not
silently discarded.

Outputs:
  ../output/schools_category_forecast_fy26_40.csv
  ../output/schools_category_forecast_fy26_40_methodology.md
"""
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
CATEGORY_CSV = ROOT / "output/school_spending_by_category_fy09_25.csv"
HISTORICAL_CSV = ROOT / "output/brookline_historical_financials_fy05_25.csv"
OUT_CSV = ROOT / "output/schools_category_forecast_fy26_40.csv"
METHOD_FILE = ROOT / "output/schools_category_forecast_fy26_40_methodology.md"

FORECAST_YEARS = list(range(2026, 2041))
ANCHOR_YEAR = 2025

CATEGORIES = [
    "Administration", "Guidance, Counseling and Testing", "Instructional Leadership",
    "Instructional Materials, Equipment and Technology", "Operations and Maintenance",
    "Other Teaching Services", "Professional Development", "Pupil Services", "Teachers",
]
EXCLUDED = "Insurance, Retirement Programs and Other"  # already modeled Town-wide as `benefits`


def cagr(start, end, years):
    return (end / start) ** (1 / years) - 1


def read_category_data():
    with open(CATEGORY_CSV) as f:
        rows = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    return rows


def read_schools_anchor():
    with open(HISTORICAL_CSV) as f:
        rows = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    return float(rows[ANCHOR_YEAR]["exp_education"])


def main():
    cat_data = read_category_data()
    schools_anchor = read_schools_anchor()

    r25 = cat_data[2025]
    values_25 = {c: float(r25[c]) for c in CATEGORIES}
    mix_total = sum(values_25.values())
    shares_25 = {c: values_25[c] / mix_total for c in CATEGORIES}

    rates = {}
    for c in CATEGORIES:
        v09 = float(cat_data[2009][c])
        v20 = float(cat_data[2020][c])
        v19 = float(cat_data[2019][c])
        v25 = float(cat_data[2025][c])
        rates[c] = {
            "cagr16": cagr(v09, v25, 16),
            "cagr5": cagr(v20, v25, 5),
            "cagr6_excovid": cagr(v19, v25, 6),
        }

    dollars_25 = {c: shares_25[c] * schools_anchor for c in CATEGORIES}

    series = {c: {2025: dollars_25[c]} for c in CATEGORIES}
    for y in FORECAST_YEARS:
        for c in CATEGORIES:
            series[c][y] = series[c][y - 1] * (1 + rates[c]["cagr16"])

    rows_out = []
    for y in FORECAST_YEARS:
        row = {"fiscal_year": y}
        total = 0.0
        for c in CATEGORIES:
            v = round(series[c][y])
            row[c] = v
            total += v
        row["total_schools_category_sum"] = round(total)
        rows_out.append(row)

    fieldnames = ["fiscal_year"] + CATEGORIES + ["total_schools_category_sum"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)
    print(f"Wrote {OUT_CSV}")

    for c in CATEGORIES:
        print(f"{c:52s} share={shares_25[c]:6.2%}  16yrCAGR={rates[c]['cagr16']:6.2%}  "
              f"5yrCAGR={rates[c]['cagr5']:6.2%}  6yrExCovidCAGR={rates[c]['cagr6_excovid']:6.2%}")
    print(f"\nFY2025 anchor total: ${schools_anchor:,.0f}")
    print(f"FY2040 category-sum total: ${rows_out[-1]['total_schools_category_sum']:,.0f}")
    implied_cagr = cagr(schools_anchor, rows_out[-1]["total_schools_category_sum"], 15)
    print(f"Implied blended CAGR, FY2025-2040: {implied_cagr:.2%}")

    write_methodology(shares_25, rates, dollars_25, schools_anchor, rows_out, implied_cagr)
    print(f"Wrote {METHOD_FILE}")


def write_methodology(shares_25, rates, dollars_25, schools_anchor, rows_out, implied_cagr):
    lines = []
    lines.append("# Schools Category-Level Forecast (FY2026-2040) — Methodology\n")
    lines.append(
        "Companion to `schools_category_forecast_fy26_40.csv`. Replaces `baseline_expense_forecast.py`'s "
        "`trend_corrected` schools line (previously a single blended 3.42%/yr trailing-5yr CAGR on the "
        "whole `exp_education` total) with 9 separately-trended categories, using DESE's own End-of-Year "
        "Financial Report function categories. See this script's own module docstring for the two real "
        "methodological choices behind this (the Schedule-A-vs-DESE scope reconciliation, and why the "
        "growth-rate window deliberately breaks from this project's usual trailing-5yr convention).\n"
    )
    lines.append("## FY2025 anchor: category shares (of the real Schedule A `exp_education` total)\n")
    lines.append("| Category | Share of FY2025 | FY2025 $ | 16yr CAGR (used) | 5yr CAGR (flagged upside) | 6yr ex-COVID-base CAGR |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for c in shares_25:
        lines.append(
            f"| {c} | {shares_25[c]:.2%} | ${dollars_25[c]:,.0f} | {rates[c]['cagr16']:.2%}/yr | "
            f"{rates[c]['cagr5']:.2%}/yr | {rates[c]['cagr6_excovid']:.2%}/yr |"
        )
    lines.append(f"| **Total** | 100.00% | **${schools_anchor:,.0f}** | | | |\n")
    lines.append(
        "The 5yr and 6yr-ex-COVID-base columns tell the same story independently (ruling out a COVID "
        "base-year artifact): several categories - Administration, Guidance, Instructional Materials, "
        "Pupil Services - have been growing 2-4x faster over the last 5-6 years than their 16-year "
        "average. This forecast uses the more conservative 16-year rate as the primary driver, and flags "
        "this acceleration explicitly as a real, named upside risk rather than silently compounding the "
        "elevated recent rate for all 15 forecast years.\n"
    )
    lines.append("## Result vs. the previous single-line approach — the total barely moves, the MIX changes a lot\n")
    old_cagr = 0.0342  # baseline_expense_forecast.py's existing trend_corrected schools CAGR (trailing-5yr, blended)
    fy2040_new = rows_out[-1]["total_schools_category_sum"]
    fy2040_old = schools_anchor * (1 + old_cagr) ** 15
    diff = fy2040_new - fy2040_old
    lines.append(
        f"Implied blended CAGR of this category-level build, FY2025-2040: **{implied_cagr:.2%}/yr** vs. the "
        f"old single-line trailing-5yr CAGR of **{old_cagr:.2%}/yr** — FY2040 totals of "
        f"**${fy2040_new:,.0f}** vs. **${fy2040_old:,.0f}**, a **{100*diff/fy2040_old:+.1f}%** difference. "
        "**This is smaller than it might look, and for a specific, explainable reason - not because the "
        "category split doesn't matter.** The old figure was itself a trailing-5yr blended rate, which "
        "this doc's own table shows was elevated across nearly every category (a real, recent "
        "acceleration - see above). This build deliberately uses each category's more conservative "
        "16-year rate instead. Teachers - the single largest category at 46.4% of the total - has a "
        "16-year CAGR (2.72%) below even the old blended 5-year rate, which pulls the weighted-average "
        "total down toward it despite several much-faster-growing smaller categories sitting alongside it. "
        "**The real, more useful difference is the underlying composition, not the top-line total**: "
        "Pupil Services, Guidance, and Other Teaching Services all grow 1.6-2.2x faster than Teachers "
        "under this build, so Teachers' own share of the schools budget keeps shrinking through FY2040 - "
        "the same share-erosion dynamic `school_budget_drivers_summary.md` documents already happened, "
        "FY2009-2025 (see that doc's own historical share figures - computed on a different denominator "
        "there, DESE's full per-pupil total including benefits, so not directly comparable number-for-"
        "number to this forecast's FY2025 shares above, but the same underlying pattern). "
        "If the elevated 5yr/6yr rates persist instead of reverting toward each category's 16-year "
        "average, the real total would land meaningfully above both figures here - a named upside "
        "risk, not baked into this point estimate (see the CAGR-window table above).\n"
    )
    lines.append("## What this deliberately does not do\n")
    lines.append(
        "- **No enrollment forecast.** Category dollar totals are grown at their own historical $ CAGR "
        "directly (which already embeds whatever enrollment change occurred FY2009-2025) - not "
        "decomposed into headcount x unit-cost x enrollment (recommendation #2/#4 from "
        "`school_budget_drivers_summary.md`). Enrollment has been roughly flat the last 3 actual years "
        "(7,060/7,039/7,023, FY23-25), so this is a reasonable simplification for now, not a hidden one - "
        "a real enrollment scenario (growth, continued flat, further decline) would be the natural next "
        "extension if this forecast needs to answer 'what if enrollment changes' specifically.\n"
        "- **No out-of-district placement modeling.** DESE's \"Total Expenditures\" (vs. \"Total "
        "In-District Expenditures\") gap - the real, ERSC-flagged volatile cost the Selected Populations "
        "data hints at - isn't separately forecast here.\n"
        "- **`town_assumptions` is unchanged** - still the Town's own aggregate schools figure, FY26-31 "
        "Town-published + Town-implied CAGR extension FY32-40. This category decomposition only replaces "
        "`trend_corrected`, this project's own independently-built estimate — consistent with how every "
        "other `trend_corrected` refinement in this project works.\n"
    )
    lines.append(
        "## Why `trend_corrected` now diverges from the Town's own figures for FY2026-2031 too\n"
        "Previously, both scenarios shared the Town's own published FY26-31 schools figure identically, "
        "only diverging starting FY2032. This category-level build compounds forward from the real "
        "FY2025 actual for the full FY2026-2040 window instead - the same principle Ben already "
        "established for Phase 1's revenue forecast (2026-08-28: don't treat the Town's own near-term "
        "figures as ground truth for `trend_corrected`, which is supposed to be this project's own "
        "independent estimate throughout). `trend_corrected`'s FY2027 schools total under this build will "
        "not equal the Town's own $149.8M FY27 PSB budget figure - a real, deliberate divergence, not an "
        "error; the Town's own near-term budget request is one input, not a ceiling on what this "
        "project's own bottom-up estimate should say.\n"
    )
    lines.append("## Sources\n")
    lines.append(
        "- `output/school_spending_by_category_fy09_25.csv` (DESE, FY2009-2025)\n"
        "- `output/brookline_historical_financials_fy05_25.csv` (Schedule A `exp_education`, FY2025 anchor)\n"
        "- `output/school_budget_drivers_summary.md` (the synthesis this forecast implements recommendation #1 from)\n"
        "- `data/SOURCES.md`, \"School enrollment & staffing history (DESE)\" section\n"
    )
    with open(METHOD_FILE, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
