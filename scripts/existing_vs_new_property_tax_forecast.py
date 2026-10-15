"""
Existing-vs-new-property tax split, extended FY2026-2040 under Phase 2's
four new-growth scenarios - the forward continuation of
`existing_vs_new_property_tax.py`'s real FY2005-2025 reconstruction,
answering the question Ben confirmed wanting (2026-09-01): "what would
different new-growth futures do to existing residents' tax bills?"

Mechanically this is the SAME cohort model as the historical script (an
"existing" cohort fixed as of FY2005, a "new" cohort that permanently
absorbs each year's new-growth $ from that year forward, both compounding
at 2.5%/yr plus their own pro-rata share of debt exclusions) - just run
forward past FY2025 using Phase 2's new_growth_scenario_forecast.py as the
source of each year's new-growth $ and debt-exclusion $, instead of real
DOR-certified historical figures. See that script's own docstring for the
full cohort-split derivation; this one only covers what's new.

**Anchor**: FY2025's real existing/new split (`existing_vs_new_property_
tax_fy05_25.csv`), value-share-rescaled onto `new_growth_scenario_
forecast.py`'s own FY2025 operating-levy anchor (see "Anchor
reconciliation" in write_methodology() below - a real ~0.9% gap between
the two scripts' independently-computed FY2025 bases, reconciled by
rescaling rather than left to silently drift).

**Policy assumptions, explicit and held flat (same convention as every
other forward-looking piece of this project)**: no future overrides
(override=0 every year - the baseline stays override-free by design, per
`.claude/memorialized.md`), no banked excess capacity (excess_capacity=0
every year - Phase 1/2 already assume the Town raises its full allowed
levy annually, this just inherits that). Debt exclusion is real through
FY2031 (Town's own bond-by-bond LRFP figures) and held flat FY2032-2040
(no new exclusions assumed) - identical to Phase 1/2's own convention,
consumed here via `new_growth_scenario_forecast.py`'s
`debt_exclusion_revenue` column, split between the two cohorts by each
year's own value share (same method as the historical script).

**What this deliberately does NOT do**: disaggregate the "existing"
cohort down to one representative household. The cohort's own aggregate
%-growth rate is the number reported - the honest resident-facing
translation is "in aggregate, this is what all pre-2005 property owners
together would see," not "your bill grows exactly this much" (individual
parcels vary with their own reassessment, which this model doesn't
track). That's a real simplification, not a hidden one - flagged plainly
in the methodology doc's own output.

Outputs:
  ../output/existing_vs_new_property_tax_fy26_40_scenarios.csv
  ../output/existing_vs_new_property_tax_fy26_40_scenarios_methodology.md
"""
import csv

from new_growth_scenario_forecast import read_historical

HIST_PATH = "../output/existing_vs_new_property_tax_fy05_25.csv"
SCENARIOS_PATH = "../output/new_growth_scenarios_fy26_40.csv"
OUT_PATH = "../output/existing_vs_new_property_tax_fy26_40_scenarios.csv"
METHODOLOGY_PATH = "../output/existing_vs_new_property_tax_fy26_40_scenarios_methodology.md"

FORECAST_YEARS = list(range(2026, 2041))


def read_fy2025_anchor():
    with open(HIST_PATH) as f:
        rows = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    r = rows[2025]
    return float(r["existing_allowed_levy_limit"]), float(r["new_allowed_levy_limit"])


def read_scenarios():
    with open(SCENARIOS_PATH) as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        s, y = r["scenario"], int(r["fiscal_year"])
        out.setdefault(s, {})[y] = {
            "operating": float(r["property_tax_operating"]),
            "debt_exclusion": float(r["debt_exclusion_revenue"]),
        }
    return out


def run_forward(name, years, existing_share_2025, fy2025_operating):
    """
    years: {2026: {'operating':..., 'debt_exclusion':...}, ..., 2040: {...}}
    Rescales FY2025's real existing/new split onto this scenario's own
    FY2025 operating-levy anchor (see module docstring, "Anchor
    reconciliation") - preserves the real FY2025 existing_share exactly,
    only the dollar base it's applied to changes.
    """
    existing_allowed = existing_share_2025 * fy2025_operating
    new_allowed = (1 - existing_share_2025) * fy2025_operating
    prior_operating = fy2025_operating

    rows = []
    prior_existing_total, prior_town_total = None, None
    fy2026_existing_total, fy2026_town_total = None, None
    for y in FORECAST_YEARS:
        operating_y = years[y]["operating"]
        debt_excl_y = years[y]["debt_exclusion"]
        new_growth_y = operating_y - prior_operating * 1.025

        existing_pre = existing_allowed * 1.025
        new_pre = new_allowed * 1.025 + new_growth_y
        total_pre = existing_pre + new_pre
        existing_share = existing_pre / total_pre if total_pre else 0.0

        existing_allowed = existing_pre
        new_allowed = new_pre
        existing_debt_excl = debt_excl_y * existing_share
        new_debt_excl = debt_excl_y * (1 - existing_share)

        existing_total_tax = existing_allowed + existing_debt_excl
        new_total_tax = new_allowed + new_debt_excl
        town_total_tax = existing_total_tax + new_total_tax

        if y == 2026:
            fy2026_existing_total, fy2026_town_total = existing_total_tax, town_total_tax

        rows.append({
            "scenario": name, "fiscal_year": y,
            "existing_allowed_levy_limit": round(existing_allowed),
            "existing_debt_exclusion_share": round(existing_debt_excl),
            "existing_total_tax": round(existing_total_tax),
            "new_allowed_levy_limit": round(new_allowed),
            "new_debt_exclusion_share": round(new_debt_excl),
            "new_total_tax": round(new_total_tax),
            "town_total_tax": round(town_total_tax),
            "new_growth_dollars": round(new_growth_y),
            "existing_pct_growth_yoy": None if prior_existing_total is None else round(
                existing_total_tax / prior_existing_total - 1, 5),
            "existing_pct_growth_from_fy2026": 0.0 if y == 2026 else None,
            "town_pct_growth_yoy": None if prior_town_total is None else round(
                town_total_tax / prior_town_total - 1, 5),
            "town_pct_growth_from_fy2026": 0.0 if y == 2026 else None,
        })

        prior_existing_total, prior_town_total = existing_total_tax, town_total_tax
        prior_operating = operating_y

    for r in rows:
        if r["fiscal_year"] != 2026:
            r["existing_pct_growth_from_fy2026"] = round(r["existing_total_tax"] / fy2026_existing_total - 1, 5)
            r["town_pct_growth_from_fy2026"] = round(r["town_total_tax"] / fy2026_town_total - 1, 5)

    n = len(rows) - 1
    existing_cagr = (rows[-1]["existing_total_tax"] / rows[0]["existing_total_tax"]) ** (1 / n) - 1
    town_cagr = (rows[-1]["town_total_tax"] / rows[0]["town_total_tax"]) ** (1 / n) - 1
    return rows, {"existing_cagr": existing_cagr, "town_cagr": town_cagr,
                  "fy2040_existing": rows[-1]["existing_total_tax"], "fy2040_town": rows[-1]["town_total_tax"]}


def main():
    existing_allowed_2025, new_allowed_2025 = read_fy2025_anchor()
    existing_share_2025 = existing_allowed_2025 / (existing_allowed_2025 + new_allowed_2025)

    hist = read_historical()
    fy2025_operating = float(hist[2025]["total_levy"]) - float(hist[2025]["debt_exclusions"])

    scenarios = read_scenarios()

    out_rows = []
    summary = {}
    for name, years in scenarios.items():
        rows, cagrs = run_forward(name, years, existing_share_2025, fy2025_operating)
        out_rows.extend(rows)
        summary[name] = cagrs

    fieldnames = [
        "scenario", "fiscal_year",
        "existing_allowed_levy_limit", "existing_debt_exclusion_share", "existing_total_tax",
        "new_allowed_levy_limit", "new_debt_exclusion_share", "new_total_tax",
        "town_total_tax", "new_growth_dollars",
        "existing_pct_growth_yoy", "existing_pct_growth_from_fy2026",
        "town_pct_growth_yoy", "town_pct_growth_from_fy2026",
    ]
    with open(OUT_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {OUT_PATH}: {len(out_rows)} rows")

    print(f"\n{'Scenario':<28} {'Existing CAGR':>14} {'Town CAGR':>12} {'Gap':>8}")
    for name, c in summary.items():
        print(f"{name:<28} {c['existing_cagr']:>13.3%} {c['town_cagr']:>11.3%} "
              f"{c['town_cagr']-c['existing_cagr']:>7.3%}")

    write_methodology(summary, existing_share_2025)


def write_methodology(summary, existing_share_2025):
    lines = []
    lines.append("# Existing-vs-new-property tax split, FY2026-2040 scenarios\n\n")
    lines.append(
        "Forward continuation of `existing_vs_new_property_tax.py`'s real FY2005-2025 "
        "reconstruction, run under each of Phase 2's four new-growth scenarios "
        "(`new_growth_scenario_forecast.py`). Answers: what would different new-growth "
        "futures do to the tax burden on property that already existed as of FY2005, "
        "in aggregate - not a single household's bill, but the whole pre-2005 cohort's "
        f"combined tax growth. FY2025 existing-cohort value share: {existing_share_2025:.2%} "
        f"(the rest, {1-existing_share_2025:.2%}, is the cumulative \"new\" cohort - all "
        "construction/renovation/reclassification value added since FY2005).\n\n"
    )
    lines.append("## Results by scenario, FY2026->FY2040 (14 years)\n\n")
    lines.append("| Scenario | Existing-cohort CAGR | Town-total CAGR | Gap |\n|---|---|---|---|\n")
    for name, c in summary.items():
        lines.append(f"| {name} | {c['existing_cagr']:.3%}/yr | {c['town_cagr']:.3%}/yr | "
                      f"{c['town_cagr']-c['existing_cagr']:.3%}/yr |\n")
    lines.append(
        "\nThe gap column is the direct, concrete answer to \"what does new growth buy "
        "existing residents\": every year of that gap is town-wide levy growth that did "
        "NOT have to come out of existing property owners' pockets. A bigger gap (more "
        "new growth, per Phase 2's peer-target scenarios) means the existing cohort's "
        "tax bill grows more slowly, not that the Town collects less overall.\n\n"
        "**The three `peer_target_*` scenarios are numerically identical here, and "
        "that's expected, not a bug**: this cohort model only consumes each year's TOTAL "
        "new-growth $, not its physical composition (residential vs. commercial, new "
        "vs. renovation) - Phase 2's three peer-target scenarios are constructed to hit "
        "the exact same total (the 80th-percentile peer rate), just via different "
        "physical mixes, so they only diverge from each other in `new_growth_"
        "scenarios_fy26_40.csv`'s implied-units/implied-sqft columns, never in the "
        "dollar total this script reads.\n\n"
    )
    lines.append("## Assumptions held flat (see module docstring for the full list)\n\n")
    lines.append(
        "No future overrides, no banked excess capacity (Town raises its full allowed "
        "levy every year), debt exclusion real through FY2031 then held flat - all "
        "identical to Phase 1/2's own baseline conventions, not new assumptions "
        "introduced here.\n\n"
    )
    lines.append("## Anchor reconciliation\n\n")
    lines.append(
        "FY2025's real existing/new split (`existing_vs_new_property_tax_fy05_25.csv`) "
        "is computed against the ALLOWED FY2025 levy limit; `new_growth_scenario_"
        "forecast.py`'s FY2025 base is the ACTUALLY-RAISED FY2025 operating levy (total "
        "levy minus debt exclusion) - these differ by FY2025's real excess capacity "
        "(~$2.56M, under 1% of the ~$290M base), a genuine historical fact, not a bug in "
        "either script. This script rescales the real FY2025 existing_share onto Phase "
        "2's own actually-raised anchor so the two series it depends on are internally "
        "consistent, rather than letting a base mismatch compound forward silently.\n"
    )
    with open(METHODOLOGY_PATH, "w") as f:
        f.writelines(lines)
    print(f"Wrote methodology doc to {METHODOLOGY_PATH}")


if __name__ == "__main__":
    main()
