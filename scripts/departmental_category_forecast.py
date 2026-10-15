"""
Phase 3, departmental category decomposition: replaces trend_corrected's
single blended departmental CAGR (3.77%/yr trailing-5yr) with Schedule A's
own 5 functional categories (General Government, Public Safety, Public
Works, Human Services, Culture & Recreation), each grown at its own rate.

Added 2026-09-02 (Ben: "let's break apart the departmental single blended
CAGR... these are smaller expense lines so let's keep it simple"). Simpler
than the Schools/Benefits decompositions for two real reasons, not just
less effort:

1. **No new data sourcing needed.** Schedule A already carries all 5
   categories, FY2005-2025, in `brookline_historical_financials_fy05_25.csv`
   - the same source `baseline_expense_forecast.py` already reads for its
   single blended departmental CAGR. Nothing to hunt for in a PDF or API.
2. **No extreme rate-window divergence to work around.** Checked directly
   (the same 5yr-vs-longer-window comparison that flagged real problems
   for Schools and Benefits): the 5 categories' trailing-5yr CAGRs range
   2.89%-4.37%/yr, all well-behaved, single-digit, unremarkable numbers to
   compound for 15 years - unlike Pupil Services (11.67%) or Group
   Health (12%+), nothing here is a plausible base-year artifact or an
   unsustainable spike. Two categories (General Government, Public Works)
   do show a larger 5yr-vs-20yr *ratio* (~3-7x) than the others, but the
   5yr rate itself stays modest (3.00% and 3.43%) - the ratio is large
   only because the 20yr rate is unusually low (0.89%, 0.47%), not
   because the 5yr rate is high. So this build uses trailing-5yr
   uniformly for all 5 categories, consistent with this project's
   existing convention everywhere else it applies (Phase 1/2's own
   trailing-5yr default) - no per-category window overrides needed.

## FY2026-2031: a decomposition of a trusted total, not an independent estimate

Unlike Schools (DESE gave real, independent per-category data to build an
independent FY2026-2031 estimate from) or Benefits' Pensions (a real,
independently-sourced corrected ADC schedule existed), there's no
comparable independent source suggesting the Town's own FY2026-2031
`departmental_town` aggregate needs correcting. So `trend_corrected` uses
the Town's own real, known aggregate for FY2026-2031 - split into the 5
categories by their FY2025 actual share, not re-estimated - and only
diverges from a single blended rate starting FY2032, where no Town figure
exists for any decomposition at all. Same treatment as Benefits' Group
Health/OPEB/Other lines.

Outputs:
  ../output/departmental_category_forecast_fy26_40.csv
  ../output/departmental_category_forecast_fy26_40_methodology.md
"""
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOWN_FORECAST_FILE = ROOT / "output/town_own_forecast_fy26_31.csv"
HISTORICAL_FILE = ROOT / "output/brookline_historical_financials_fy05_25.csv"
OUT_CSV = ROOT / "output/departmental_category_forecast_fy26_40.csv"
METHOD_FILE = ROOT / "output/departmental_category_forecast_fy26_40_methodology.md"

TOWN_YEARS = list(range(2026, 2032))
EXTEND_YEARS = list(range(2032, 2041))
FORECAST_YEARS = list(range(2026, 2041))
ANCHOR_YEAR = 2025

CATEGORIES = {
    "general_government": "exp_general_government",
    "public_safety": "exp_public_safety",
    "public_works": "exp_public_works",
    "human_services": "exp_human_services",
    "culture_recreation": "exp_culture_recreation",
}

# --- FTE/headcount vs. wage-driven decomposition, added 2026-09-02 (Ben:
# "is it important to know what allows the historical CAGR for these
# departments to be so low? ... are these departments actually shrinking
# ... we should be able to back up the forecast with some logic about
# whether services stay the same or shrink"). Real Town headcount and
# salary-budget data, FY2019 vs FY2026, now its own captured dataset in
# `department_fte_history.py` (Ben, 2026-09-02: "let's make sure to
# capture the employees by department data... include it in any
# published work") - imported here rather than duplicated, so this
# script's diagnosis and any future published department-level table stay
# in sync automatically. ---
from department_fte_history import category_rollup as _department_category_rollup


def compute_fte_diagnosis():
    out = {}
    for k, d in _department_category_rollup().items():
        fte_cagr = cagr(d["fte19"], d["fte26"], 7)
        salary_cagr = cagr(d["salary19"], d["salary26"], 7)
        cost_per_fte19 = d["salary19"] / d["fte19"]
        cost_per_fte26 = d["salary26"] / d["fte26"]
        cost_per_fte_cagr = cagr(cost_per_fte19, cost_per_fte26, 7)
        out[k] = dict(fte_cagr=fte_cagr, salary_cagr=salary_cagr,
                      cost_per_fte19=cost_per_fte19, cost_per_fte26=cost_per_fte26,
                      cost_per_fte_cagr=cost_per_fte_cagr, **d)
    return out


def cagr(start, end, years):
    return (end / start) ** (1 / years) - 1


def read_town_departmental():
    with open(TOWN_FORECAST_FILE) as f:
        for row in csv.DictReader(f):
            if row["category"] == "expenditure" and row["subcategory"] == "departmental_town":
                return {y: float(row[str(y)]) for y in range(2026, 2032)}
    raise ValueError("departmental_town row not found in " + TOWN_FORECAST_FILE)


def read_historical():
    with open(HISTORICAL_FILE) as f:
        return {int(r["fiscal_year"]): r for r in csv.DictReader(f)}


def main():
    town_dept_total = read_town_departmental()
    hist = read_historical()

    values_2025 = {k: float(hist[2025][c]) for k, c in CATEGORIES.items()}
    mix_total_2025 = sum(values_2025.values())
    shares_2025 = {k: v / mix_total_2025 for k, v in values_2025.items()}

    rates = {}
    for k, c in CATEGORIES.items():
        v20, v25 = float(hist[2020][c]), float(hist[2025][c])
        v05 = float(hist[2005][c])
        rates[k] = dict(cagr5=cagr(v20, v25, 5), cagr20=cagr(v05, v25, 20))

    print("Category shares (FY2025) and rates:")
    for k in CATEGORIES:
        print(f"  {k:20s} share={shares_2025[k]:6.2%}  5yr CAGR (used)={rates[k]['cagr5']:6.2%}  "
              f"20yr CAGR (cross-check)={rates[k]['cagr20']:6.2%}")

    series = {k: {} for k in CATEGORIES}
    for y in TOWN_YEARS:
        for k in CATEGORIES:
            series[k][y] = shares_2025[k] * town_dept_total[y]
    for y in EXTEND_YEARS:
        for k in CATEGORIES:
            series[k][y] = series[k][y - 1] * (1 + rates[k]["cagr5"])

    rows_out = []
    for y in FORECAST_YEARS:
        row = {"fiscal_year": y}
        total = 0.0
        for k in CATEGORIES:
            v = round(series[k][y])
            row[k] = v
            total += v
        row["total_departmental_category_sum"] = round(total)
        rows_out.append(row)

    fieldnames = ["fiscal_year"] + list(CATEGORIES.keys()) + ["total_departmental_category_sum"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)
    print(f"\nWrote {OUT_CSV}")

    # Confirm FY26-31 total exactly matches the Town's known aggregate
    # (a pure decomposition, not an independent re-estimate).
    for y in TOWN_YEARS:
        computed = sum(series[k][y] for k in CATEGORIES)
        gap = computed - town_dept_total[y]
        if abs(gap) > 1:
            print(f"  WARNING: FY{y} decomposition (${computed:,.0f}) doesn't match Town total "
                  f"(${town_dept_total[y]:,.0f}), gap ${gap:,.0f}")
    print(f"FY2026-2031 decomposition ties out to the Town's own aggregate exactly (checked, no warnings above).")

    old_cagr = 0.0377  # baseline_expense_forecast.py's existing trend_corrected departmental CAGR
    fy2031_total = sum(series[k][2031] for k in CATEGORIES)
    fy2040_old = fy2031_total * (1 + old_cagr) ** 9
    fy2040_new = rows_out[-1]["total_departmental_category_sum"]
    print(f"FY2040: category-level ${fy2040_new:,.0f} vs. old single-CAGR ${fy2040_old:,.0f} "
          f"({100*(fy2040_new/fy2040_old-1):+.1f}%)")

    fte_diag = compute_fte_diagnosis()
    print("\nFTE/wage diagnosis (FY2019 vs FY2026, from ERSC report Town personnel table):")
    for k in CATEGORIES:
        d = fte_diag[k]
        print(f"  {k:20s} FTE {d['fte19']:6.1f}->{d['fte26']:6.1f} ({d['fte_cagr']:+6.2%}/yr)  "
              f"$/FTE {d['cost_per_fte19']:>8,.0f}->{d['cost_per_fte26']:>8,.0f} ({d['cost_per_fte_cagr']:+6.2%}/yr)")

    write_methodology(shares_2025, rates, values_2025, mix_total_2025, rows_out, fy2040_old, fy2040_new,
                       old_cagr, fte_diag)
    print(f"Wrote {METHOD_FILE}")


def write_methodology(shares_2025, rates, values_2025, mix_total_2025, rows_out, fy2040_old, fy2040_new,
                       old_cagr, fte_diag):
    lines = []
    lines.append("# Departmental Category-Level Forecast (FY2026-2040) — Methodology\n")
    lines.append(
        "Companion to `departmental_category_forecast_fy26_40.csv`. Replaces `baseline_expense_forecast.py`'s "
        "`trend_corrected` departmental line (previously a single blended 3.77%/yr trailing-5yr CAGR) with "
        "Schedule A's own 5 functional categories, each grown at its own trailing-5yr rate. See this "
        "script's own module docstring for why this one is deliberately simpler than the Schools/Benefits "
        "decompositions (no new data sourcing needed, no extreme rate-window divergence to work around).\n"
    )
    lines.append("## FY2025 shares and rates\n")
    lines.append("| Category | FY2025 $ | Share | 5yr CAGR (used) | 20yr CAGR (cross-check) |")
    lines.append("|---|---:|---:|---:|---:|")
    labels = {"general_government": "General Government", "public_safety": "Public Safety",
              "public_works": "Public Works", "human_services": "Human Services",
              "culture_recreation": "Culture & Recreation"}
    for k in shares_2025:
        lines.append(f"| {labels[k]} | ${values_2025[k]:,.0f} | {shares_2025[k]:.1%} | "
                      f"{rates[k]['cagr5']:.2%}/yr | {rates[k]['cagr20']:.2%}/yr |")
    lines.append(f"| **Total** | **${mix_total_2025:,.0f}** | 100.0% | | |\n")
    lines.append(
        "Two categories (General Government, Public Works) show a larger 5yr-vs-20yr *ratio* than the "
        "others - but the 5yr rate itself is unremarkable (3.00%/3.43%), the ratio is large only because "
        "the 20yr rate is unusually low. Nothing here approaches the magnitude that made trailing-5yr risky "
        "for Schools/Benefits categories, so this build uses trailing-5yr uniformly, no per-category "
        "overrides - consistent with this project's general convention elsewhere.\n"
    )
    lines.append("## FY2026-2031: a decomposition of the Town's own known total, not an independent estimate\n")
    lines.append(
        "The Town doesn't publish department-level FY2026-2031 figures (only one aggregate "
        "`departmental_town` line), and unlike Schools or Benefits' Pensions, there's no independent data "
        "source suggesting that aggregate needs correcting. So FY2026-2031 splits the Town's real, known "
        "total by each category's FY2025 actual share - a decomposition, not a re-estimate. FY2032-2040 "
        "is where the real divergence from a single blended rate happens, since no Town figure exists for "
        "any of this past FY2031 anyway.\n"
    )
    lines.append("## Result vs. the previous single-line approach\n")
    diff = fy2040_new - fy2040_old
    lines.append(
        f"FY2040 total: **${fy2040_new:,.0f}** (category-level) vs. **${fy2040_old:,.0f}** (old single-line "
        f"{old_cagr:.2%}/yr trailing-5yr CAGR on the FY2031 total) — a **{100*diff/fy2040_old:+.1f}%** "
        "difference. Much smaller than the Schools/Benefits gaps, as expected - none of these 5 categories "
        "individually diverges far from the old blended rate, so decomposing them mostly sharpens the "
        "*composition* (which category is really driving departmental growth), not the total.\n"
    )
    lines.append("## Is the low CAGR real, or is it masking service cuts? — FTE/wage diagnosis\n")
    lines.append(
        "Added 2026-09-02 (Ben: \"is it important to know what allows the historical CAGR for these "
        "departments to be so low? ... are these departments actually shrinking? ... we should be able to "
        "back up the forecast with some logic about whether services stay the same or shrink\"). A fair "
        "challenge - a 3%/yr departmental CAGR next to 4-5%/yr wage growth only makes sense if something "
        "else is offsetting it, and \"headcount is shrinking\" is one obvious candidate worth actually "
        "checking, not assuming either way. Real Town headcount (FTE) and salary-budget data, FY2019 vs "
        "FY2026, from `department_fte_history.py` (its own captured dataset - see "
        "`output/department_fte_salary_fy19_fy26.csv` and `output/department_fte_salary_fy19_fy26_notes.md` "
        "for the full 18-department detail and per-department footnotes), rolled up onto these same 5 "
        "categories:\n"
    )
    lines.append("| Category | FTE FY19→FY26 | FTE CAGR | Salary $/FTE CAGR (implied) |")
    lines.append("|---|---:|---:|---:|")
    labels2 = {"general_government": "General Government", "public_safety": "Public Safety",
               "public_works": "Public Works", "human_services": "Human Services",
               "culture_recreation": "Culture & Recreation"}
    for k in fte_diag:
        d = fte_diag[k]
        lines.append(f"| {labels2[k]} | {d['fte19']:.1f} → {d['fte26']:.1f} | {d['fte_cagr']:+.2%}/yr | "
                      f"{d['cost_per_fte_cagr']:+.2%}/yr |")
    lines.append("")
    lines.append(
        "**The answer: services are not, on net, being cut to hold costs down.** Headcount actually *grew* "
        "in 4 of the 5 categories - Human Services grew fastest (+3.6%/yr FTE, mostly public-health staffing) "
        "while its per-employee cost stayed nearly flat (+0.1%/yr), meaning essentially all of that "
        "category's real dollar growth is more staff, not more expensive staff. General Government, Public "
        "Works, and Culture & Recreation all show modest headcount growth alongside modest per-employee "
        "growth - broadly steady service levels, growing in step with cost.\n"
        "\n"
        "**Public Safety is the one real exception, and it explains most of the story Ben's question was "
        "getting at.** Its headcount actually shrank (-0.28%/yr, largely Police - down 7.5 FTE net, per the "
        "ERSC report's own footnote: \"held open 6 officers... to balance the 2026 budget\") while its "
        "implied cost-per-employee rose faster than every other category (+3.89%/yr) - this category's "
        "dollar growth is real, but it's wage/overtime/arbitration-driven, not headcount-driven. This "
        "matches the same report's own narrative on the same page: police and fire secure JLMC-arbitrated "
        "wage gains beyond COLA (a 2023 retroactive settlement added a 4% \"Certification Differential\" "
        "stipend, since increased to 7.5% by 2027, plus new tenure-based step increases), which the Town has "
        "partly funded by leaving positions unfilled - i.e., trading headcount for compensation growth, not "
        "shrinking the service itself.\n"
        "\n"
        "**What this means for the forecast**: for General Government/Public Works/Human Services/Culture & "
        "Recreation, projecting continued trailing-5yr growth is not assuming service cuts - the real "
        "FY2019-2026 pattern behind those CAGRs is modest, broad-based headcount growth roughly matched by "
        "modest per-employee cost growth, a defensible pattern to extend. For Public Safety, the story is "
        "different: its 4.37%/yr trailing-5yr CAGR reflects arbitration-driven wage growth on a headcount "
        "that's held flat-to-shrinking by budget pressure, not rising service levels - extending that same "
        "rate assumes the arbitration/COLA dynamic (not more police officers or firefighters) continues to "
        "be the main cost driver, which is the same real pattern already documented in the ERSC report as "
        "an active, unresolved cost pressure (not something this forecast is inventing).\n"
    )
    lines.append("## What this deliberately does not do\n")
    lines.append(
        "- **`town_assumptions` is unchanged** — still the Town's own aggregate departmental figure, "
        "FY26-31 Town-published + Town-implied CAGR extension FY32-40.\n"
        "- **No sub-department detail within each category** (e.g. Police vs. Fire within Public Safety) - "
        "Schedule A's own 5-category split is the finest granularity available from this project's existing "
        "data without a new research effort, which wasn't asked for here.\n"
    )
    lines.append("## Sources\n")
    lines.append("- `output/brookline_historical_financials_fy05_25.csv` (Schedule A, FY2005-2025)\n"
                  "- `output/town_own_forecast_fy26_31.csv` (Town's own FY26-31 departmental_town aggregate)\n")
    with open(METHOD_FILE, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
