"""
Phase 5, Part 3a: combine Phase 1 (revenue) and Phase 3 (expense) into one
actual surplus/deficit trajectory, FY2026-2040.

Both source forecasts already reach FY2040 independently
(`output/baseline_revenue_forecast_fy26_40.csv`,
`output/baseline_expense_forecast_fy26_40.csv`) and share the same two
scenario names - "town_assumptions" (the Town's own stated planning
figures, mechanically extended) and "trend_corrected" (this project's own
trailing-actual-CAGR-based assumptions, applied for the full window). This
script pairs them scenario-for-scenario (town_assumptions revenue against
town_assumptions expense, trend_corrected against trend_corrected) rather
than cross-combining, since that diagonal is what each scenario name
already means end-to-end: "the Town's own stated future" vs. "our own
corrected estimate of the future." Nothing here is recomputed - this is
pure combination of two already-built, already-memorialized forecasts.

Debt exclusion nets to exactly zero every year, in both scenarios (verified
directly: `debt_exclusion_revenue` == `debt_service_excluded` to the dollar,
FY2026-2040, both scenarios) - it's a dollar-for-dollar match by statute
(Prop 2.5), and both source forecasts already hold it flat post-FY2031 with
no new exclusions assumed. So the surplus/deficit here is entirely an
operating-budget story; `operating_surplus_deficit` and `surplus_deficit`
are identical columns, both reported for transparency rather than asserted
without the reader being able to check it.
"""

import csv
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
REVENUE_CSV = OUTPUT_DIR / "baseline_revenue_forecast_fy26_40.csv"
EXPENSE_CSV = OUTPUT_DIR / "baseline_expense_forecast_fy26_40.csv"
OUT_CSV = OUTPUT_DIR / "baseline_surplus_deficit_forecast_fy26_40.csv"
OUT_METHOD = OUTPUT_DIR / "baseline_surplus_deficit_forecast_fy26_40_methodology.md"

SCENARIOS = ["town_assumptions", "trend_corrected"]
SCENARIO_LABEL = {
    "town_assumptions": "Town's own stated FY26-31 planning figures, mechanically extended to FY2040",
    "trend_corrected": "This project's own trailing-actual-CAGR assumptions, applied FY2026-2040",
}


def load(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return {(r["scenario"], int(r["fiscal_year"])): r for r in rows}


def main():
    revenue = load(REVENUE_CSV)
    expense = load(EXPENSE_CSV)

    years = sorted({y for (_, y) in revenue.keys()})

    out_rows = []
    for scenario in SCENARIOS:
        cumulative = 0.0
        for year in years:
            r = revenue[(scenario, year)]
            e = expense[(scenario, year)]

            total_revenue = float(r["total_revenue"])
            total_expenditure = float(e["total_expenditure"])
            surplus_deficit = total_revenue - total_expenditure

            operating_revenue = total_revenue - float(r["debt_exclusion_revenue"])
            operating_expenditure = total_expenditure - float(e["debt_service_excluded"])
            operating_surplus_deficit = operating_revenue - operating_expenditure

            cumulative += surplus_deficit

            out_rows.append(
                {
                    "scenario": scenario,
                    "fiscal_year": year,
                    "total_revenue": round(total_revenue),
                    "total_expenditure": round(total_expenditure),
                    "surplus_deficit": round(surplus_deficit),
                    "operating_revenue": round(operating_revenue),
                    "operating_expenditure": round(operating_expenditure),
                    "operating_surplus_deficit": round(operating_surplus_deficit),
                    "cumulative_surplus_deficit": round(cumulative),
                    "surplus_deficit_pct_of_revenue": round(
                        100 * surplus_deficit / total_revenue, 3
                    ),
                }
            )

    fieldnames = list(out_rows[0].keys())
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {OUT_CSV}")
    write_methodology(out_rows, years)
    print(f"Wrote {OUT_METHOD}")


def write_methodology(out_rows, years):
    by_scenario = {s: [r for r in out_rows if r["scenario"] == s] for s in SCENARIOS}

    lines = []
    lines.append("# Baseline Surplus/Deficit Forecast (FY2026-2040) — Methodology\n")
    lines.append(
        "Companion to `baseline_surplus_deficit_forecast_fy26_40.csv`. Part 3a of "
        "\"the full story\" outline: combines Phase 1's revenue forecast "
        "(`baseline_revenue_forecast_fy26_40.csv`) and Phase 3's expense forecast "
        "(`baseline_expense_forecast_fy26_40.csv`) — both of which already "
        "independently reach FY2040 — into one actual surplus/deficit line. This "
        "was the single biggest concrete modeling gap left in the project's "
        "baseline (\"keep what we have\") work.\n"
    )
    lines.append("## How the two scenarios are paired\n")
    lines.append(
        "Revenue and expense forecasts share the same two scenario names and are "
        "paired scenario-for-scenario, not cross-combined:\n"
    )
    for s in SCENARIOS:
        lines.append(f"- **{s}**: {SCENARIO_LABEL[s]}.")
    lines.append(
        "\nCross-pairing (e.g. the Town's own revenue assumption against this "
        "project's own higher expense estimate) would show a wider gap, but "
        "wasn't built here — each scenario name already means a consistent "
        "end-to-end \"whose assumptions\" story, and mixing them would blur that. "
        "Worth a follow-up if a sensitivity range around the gap is wanted later.\n"
    )
    lines.append("## Debt exclusion nets to exactly zero\n")
    lines.append(
        "`debt_exclusion_revenue` (revenue) and `debt_service_excluded` (expense) "
        "match to the dollar every year, FY2026-2040, in both scenarios — by "
        "Prop 2.5 statute a debt exclusion is a dollar-for-dollar match to a "
        "bond's annual debt service, and both source forecasts already hold it "
        "flat post-FY2031 with no new exclusions assumed. So `surplus_deficit` "
        "and `operating_surplus_deficit` are identical columns here; both are "
        "reported so that fact is checkable rather than asserted.\n"
    )
    lines.append("## Result\n")
    lines.append(
        "| Scenario | FY2026 | FY2030 | FY2035 | FY2040 |\n|---|---|---|---|---|"
    )
    for s in SCENARIOS:
        rows = {r["fiscal_year"]: r for r in by_scenario[s]}
        cells = []
        for y in [2026, 2030, 2035, 2040]:
            r = rows[y]
            cells.append(
                f"${r['surplus_deficit']:,} ({r['surplus_deficit_pct_of_revenue']:+.1f}% of revenue)"
            )
        lines.append(f"| {s} | " + " | ".join(cells) + " |")
    lines.append("")

    for s in SCENARIOS:
        rows = {r["fiscal_year"]: r for r in by_scenario[s]}
        first_deficit_year = next(
            (r["fiscal_year"] for r in by_scenario[s] if r["surplus_deficit"] < 0),
            None,
        )
        cum_2040 = rows[2040]["cumulative_surplus_deficit"]
        if first_deficit_year:
            lines.append(
                f"**{s}**: turns to an annual deficit in FY{first_deficit_year} and "
                f"stays there through FY2040; cumulative surplus/deficit across the "
                f"full FY2026-2040 window is ${cum_2040:,}.\n"
            )
        else:
            lines.append(
                f"**{s}**: stays in surplus for the full FY2026-2040 window; "
                f"cumulative surplus/deficit is ${cum_2040:,}.\n"
            )

    lines.append("## What this deliberately still excludes\n")
    lines.append(
        "- **Any FUTURE voter override or debt exclusion beyond what's already "
        "decided.** The May 2026 operating override (FY2027-2029, "
        "$23,254,439 over 3 years) IS included on the revenue side — it's a "
        "decided, legislated fact by this project's own \"today,\" not a "
        "hypothetical lever, so both scenarios' `total_revenue` already "
        "reflect it (see `baseline_revenue_forecast_fy26_40_methodology.md`'s "
        "\"May 2026 override correction\" section for why it wasn't already "
        "in the Town's own transcribed source data and how it's added). What's "
        "excluded is anything *beyond* that — a hypothetical FY2032+ override, "
        "for instance. The gap shown here is what such a future lever (or "
        "another one) would need to close, not a prediction that Brookline "
        "runs an actual cash deficit — Massachusetts towns cannot; in "
        "practice, this gap is what gets closed every year by some "
        "combination of a future override, a free cash draw, or expense cuts "
        "not modeled here.\n"
        "- **Phase 2's new-growth policy scenarios** (peer-target growth rates) — "
        "layered separately in `new_growth_scenarios_fy26_40.csv`; not combined "
        "with the expense side here. A natural follow-up: rerun this same "
        "combine against Phase 2's `trend_continues`/`peer_target_*` revenue "
        "paths to show how much of the gap each closes.\n"
        "- **Phase 4's marginal expense impact of new growth** — the expense "
        "side here is Phase 3's baseline only (no new construction's added "
        "service cost). Combining Phase 2 revenue with Phase 3+4 expense "
        "together would be the fullest version of this exercise.\n"
    )
    lines.append("## Sources\n")
    lines.append(
        "- `output/baseline_revenue_forecast_fy26_40.csv` + its methodology doc\n"
        "- `output/baseline_expense_forecast_fy26_40.csv` + its methodology doc\n"
    )

    with open(OUT_METHOD, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
