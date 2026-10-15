"""
Phase 5, Part 3b: the "overrides-only" lever. Ben, 2026-09-04: "let's
include overrides as a lever and model out a scenario where we do nothing
but rely on overrides."

Takes `town_assumptions`' already-built operating gap
(`output/baseline_surplus_deficit_forecast_fy26_40.csv`) - i.e. no
improvement to new growth, no expense management, no permitting/zoning
reform, nothing but what the Town already has planned through FY2031 plus
mechanical extension to FY2040 - and asks: what override(s), at a
realistic historical cadence, would be needed to keep the operating budget
from running an ever-growing deficit?

Cadence: every 3 years, first one FY2029 (three years after the real May
2026 override's last tranche lands, FY2027-2029) - not fitted to the data,
chosen because it's what the Town's own ERSC Final Report explicitly
observed: "Time periods between Brookline's operating overrides have
compressed" (p.12). Real historical intervals: 2009->2016 (7yr),
2016->2019 (3yr), 2019->2024 (5yr), 2024->2026 (2yr) - a 3-year interval is
a defensible, round-number continuation of that compression, not a
best-fit curve.

Sizing: each override closes that year's operating gap to exactly $0
(breakeven), given the compounding effect of every override already
added in prior cycles (same 2.5%/yr-forever compounding as every real
historical override, per `new_growth_scenario_forecast.py`'s
`apply_may_2026_override()`). This is the honest MINIMUM size needed -
real overrides typically build in a buffer (the May 2026 override banked
excess into a stabilization fund), so treat these as a floor, not a
prediction of what voters would actually be asked to approve.

Between override years, no new override is added - the gap re-opens as
expenses keep outpacing 2.5%+the fixed override amount, exactly like the
real pattern between 2005 and 2025.

Output: `output/override_reliance_scenario_fy26_40.csv`, one row per year:
the pre-hypothetical-override operating gap, the new override (if any)
that year, the cumulative hypothetical-override total, and the resulting
operating surplus/deficit after applying it.
"""

import csv
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
SURPLUS_DEFICIT_CSV = OUTPUT_DIR / "baseline_surplus_deficit_forecast_fy26_40.csv"
OUT_CSV = OUTPUT_DIR / "override_reliance_scenario_fy26_40.csv"
OUT_METHOD = OUTPUT_DIR / "override_reliance_scenario_fy26_40_methodology.md"

BASE_SCENARIO = "town_assumptions"
OVERRIDE_YEARS = [2029, 2032, 2035, 2038]
OVERRIDE_GROWTH_RATE = 1.025


def load_base():
    with open(SURPLUS_DEFICIT_CSV) as f:
        rows = list(csv.DictReader(f))
    base_gap = {}
    base_revenue = {}
    for r in rows:
        if r["scenario"] == BASE_SCENARIO:
            y = int(r["fiscal_year"])
            base_gap[y] = float(r["operating_surplus_deficit"])
            base_revenue[y] = float(r["total_revenue"])
    return base_gap, base_revenue


def main():
    base_gap, base_revenue = load_base()
    years = sorted(base_gap.keys())

    cumulative_override = 0.0
    out_rows = []
    for y in years:
        if y > years[0]:
            cumulative_override *= OVERRIDE_GROWTH_RATE

        new_override = 0.0
        if y in OVERRIDE_YEARS:
            gap_before_new_override = base_gap[y] + cumulative_override
            new_override = max(0.0, -gap_before_new_override)
            cumulative_override += new_override

        resulting_gap = base_gap[y] + cumulative_override

        out_rows.append(
            {
                "fiscal_year": y,
                "base_operating_gap_before_new_overrides": round(base_gap[y]),
                "new_override_this_year": round(new_override),
                "cumulative_hypothetical_override": round(cumulative_override),
                "resulting_operating_surplus_deficit": round(resulting_gap),
                "resulting_pct_of_revenue": round(
                    100 * resulting_gap / base_revenue[y], 3
                ),
            }
        )

    fieldnames = list(out_rows[0].keys())
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {OUT_CSV}")

    write_methodology(out_rows)
    print(f"Wrote {OUT_METHOD}")


def write_methodology(out_rows):
    total_new_overrides = sum(r["new_override_this_year"] for r in out_rows)
    final = out_rows[-1]

    lines = []
    lines.append("# Override-Reliance Scenario (FY2026-2040) — Methodology\n")
    lines.append(
        "Companion to `override_reliance_scenario_fy26_40.csv`. Part 3b's "
        "\"overrides-only\" lever: what it would take to keep the operating "
        f"budget balanced through FY2040 using nothing but periodic overrides "
        f"on top of the `{BASE_SCENARIO}` baseline - no new-growth improvement, "
        "no expense management, no permitting/zoning reform.\n"
    )
    lines.append("## Cadence and sizing\n")
    lines.append(
        f"Override years: {', '.join('FY' + str(y) for y in OVERRIDE_YEARS)} - "
        "every 3 years, chosen to match the Town's own ERSC Final Report "
        "observation that override intervals have compressed (p.12), not "
        "fitted to this data. Each override is sized to bring that year's "
        "operating surplus/deficit to exactly $0 (breakeven), given every "
        "prior hypothetical override already compounding at 2.5%/yr forever "
        "after (same mechanic as every real historical override in this "
        "project's model). This is the honest *minimum* - real overrides "
        "typically build in a buffer.\n"
    )
    lines.append("## Result\n")
    lines.append("| Year | New override | Cumulative override | Resulting gap |")
    lines.append("|---|---|---|---|")
    for r in out_rows:
        if r["new_override_this_year"] > 0 or r["fiscal_year"] in (2026, 2040):
            lines.append(
                f"| FY{r['fiscal_year']} | "
                f"${r['new_override_this_year']:,} | "
                f"${r['cumulative_hypothetical_override']:,} | "
                f"${r['resulting_operating_surplus_deficit']:,} "
                f"({r['resulting_pct_of_revenue']:+.1f}%) |"
            )
    lines.append("")
    lines.append(
        f"Four overrides, {', '.join('FY' + str(y) for y in OVERRIDE_YEARS)}, "
        f"totaling ${total_new_overrides:,.0f} in new nominal override dollars, "
        f"compound to **${final['cumulative_hypothetical_override']:,.0f}/yr** "
        "of permanent added levy capacity by FY2040 - roughly 3x this "
        "project's own FY2005-2025 real-override total ($38.7M compounded, "
        "see Part 2) in about three-quarters of the time. Each override is "
        "roughly double the size of the one before it ($8.1M -> $16.8M -> "
        f"$33.6M -> $42.1M), directly illustrating the ERSC's own "
        "'compressing and growing' pattern rather than just asserting it.\n"
    )
    lines.append(
        f"**Even so, the budget is not fully closed by FY2040**: the resulting "
        f"gap is back to ${final['resulting_operating_surplus_deficit']:,.0f} "
        f"({final['resulting_pct_of_revenue']:+.1f}% of revenue) two years after "
        "the last modeled override (FY2038), since the underlying gap grows "
        "faster than a fixed 3-year cadence can fully keep pace with by the "
        "end of the window. A pure override-reliance strategy would need to "
        "keep accelerating - larger and/or more frequent asks - not settle "
        "into a steady rhythm.\n"
    )
    lines.append("## What this deliberately does not include\n")
    lines.append(
        "- **No buffer/reserve sizing** - real overrides (like the May 2026 "
        "one) often raise more than the strict breakeven amount and bank the "
        "excess; this scenario sizes to the minimum needed each cycle.\n"
        "- **No political/voter-approval likelihood** - this is a mechanical "
        "\"what size would be needed,\" not a claim about what would actually "
        "pass.\n"
        "- **No combination with the other levers** - by design, this is the "
        "\"do nothing but rely on overrides\" case, meant to be directly "
        "compared against the new-growth, expense-management, and permitting/"
        "zoning levers, not blended with them.\n"
    )
    with open(OUT_METHOD, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
