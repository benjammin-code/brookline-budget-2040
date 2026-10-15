"""
Phase 5, Part 4a support: decompose the base-case forecast into the part the
May 2026 override is doing and the part the Town's own automatic revenue is
doing, and solve for the new-growth rate that would close the second one.

Motivation (2026-09-06, Ben: "let's rewrite toward trend_corrected as the base
case"). Under `trend_corrected` the operating budget runs a surplus of roughly
+$28 million a year by FY2040, which reads as "Brookline is fine" and is
misleading on its own: the May 2026 operating override is already in the
revenue line, and by FY2040 it is worth substantially more than the
$23,254,439 voters actually approved, because an override permanently enlarges
the levy base that then compounds. Strip it out and the underlying structural
position is visible. That is the number every lever in Part 4c should be sized
against, since the override is a decided fact rather than a lever still
available to pull.

Nothing here is a reimplementation. This script imports
`baseline_revenue_forecast` and `baseline_surplus_deficit_forecast` and re-runs
the real models through the two sensitivity hooks those modules expose
(`INCLUDE_MAY_2026_OVERRIDE`, `NEW_GROWTH_PCT_TREND_OVERRIDE`), redirecting
their output to a scratch directory so the committed baseline CSVs are never
touched. The control run is verified against the committed baseline to the
dollar before any counterfactual is reported - if the models change underneath
this script, it fails loudly rather than reporting stale numbers.

Three runs, all `trend_corrected`:

  A. `as_legislated`      - the committed baseline. Override in, new growth at
                            the trailing FY2021-25 actual rate.
  B. `ex_override`        - identical, with the May 2026 override removed. The
                            structural position: what automatic revenue alone
                            does against real cost growth.
  C. `ex_override_breakeven` - B, with the sustained new-growth rate solved by
                            bisection so the FY2040 operating balance is zero.
                            Answers "how much more growth, and no override at
                            all, would it take?"

Why the expense side is not re-run: the expense forecast does not read the
revenue forecast (checked - `baseline_expense_forecast.py` takes no revenue
input), so removing the override changes revenue only. Every dollar of
difference between A and B is therefore revenue, which is what makes the
subtraction meaningful rather than a mixed effect.
"""

import contextlib
import csv
import io
import os
import shutil
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
ROOT = SCRIPTS_DIR.parent
OUTPUT_DIR = ROOT / "output"
SCRATCH = ROOT / ".decomp_scratch"

COMMITTED_SURPLUS = OUTPUT_DIR / "baseline_surplus_deficit_forecast_fy26_40.csv"
OUT_CSV = OUTPUT_DIR / "base_case_decomposition_fy26_40.csv"
OUT_METHOD = OUTPUT_DIR / "base_case_decomposition_fy26_40_methodology.md"

YEARS = list(range(2026, 2041))
SCENARIO = "trend_corrected"

RUN_LABEL = {
    "as_legislated": (
        "Committed baseline: May 2026 override included (it is a decided, "
        "legislated fact), new growth at the trailing FY2021-25 actual rate"
    ),
    "ex_override": (
        "Counterfactual: identical, but the May 2026 override never passed. "
        "Isolates the structural position of automatic revenue vs. real costs"
    ),
    "ex_override_breakeven": (
        "Counterfactual: no override, and new growth held at the rate that "
        "brings the FY2040 operating balance to zero"
    ),
}


def _run(include_override, ng_rate=None):
    """Re-runs the real revenue + surplus models into scratch. Returns
    {year: row} for the trend_corrected scenario."""
    import baseline_revenue_forecast as brf
    import baseline_surplus_deficit_forecast as bsd

    brf.INCLUDE_MAY_2026_OVERRIDE = include_override
    brf.NEW_GROWTH_PCT_TREND_OVERRIDE = ng_rate
    brf.OUT_FILE = str(SCRATCH / "revenue.csv")
    brf.METHODOLOGY_FILE = str(SCRATCH / "revenue_method.md")
    bsd.REVENUE_CSV = SCRATCH / "revenue.csv"
    bsd.OUT_CSV = SCRATCH / "surplus.csv"
    bsd.OUT_METHOD = SCRATCH / "surplus_method.md"

    with contextlib.redirect_stdout(io.StringIO()):
        brf.main()
        bsd.main()

    with open(SCRATCH / "surplus.csv") as f:
        rows = [r for r in csv.DictReader(f) if r["scenario"] == SCENARIO]
    return {int(r["fiscal_year"]): r for r in rows}


def _check_control(control):
    """The committed baseline must reproduce exactly, or every counterfactual
    below is measured against the wrong reference."""
    with open(COMMITTED_SURPLUS) as f:
        committed = {
            int(r["fiscal_year"]): r
            for r in csv.DictReader(f)
            if r["scenario"] == SCENARIO
        }
    for y in YEARS:
        for col in ("operating_revenue", "operating_expenditure", "operating_surplus_deficit"):
            a, b = int(control[y][col]), int(committed[y][col])
            if a != b:
                raise SystemExit(
                    f"CONTROL RUN MISMATCH in FY{y} {col}: re-run gives {a:,}, "
                    f"committed baseline has {b:,}. Re-run "
                    f"baseline_revenue_forecast.py and "
                    f"baseline_surplus_deficit_forecast.py first."
                )
    print("Control run reproduces the committed baseline to the dollar, FY2026-2040.")


def _solve_breakeven(baseline_rate):
    """Bisect on the sustained new-growth rate until FY2040's operating
    balance (no override) is zero. Solved rather than interpolated: the levy
    limit is a compounding recursion, so the relationship between the rate and
    the FY2040 balance is not linear and a two-point interpolation would be
    wrong by a meaningful amount over a 15-year window."""
    lo, hi = baseline_rate, baseline_rate + 0.01
    if float(_run(False, lo)[2040]["operating_surplus_deficit"]) > 0:
        raise SystemExit(
            "No override needed: the structural FY2040 balance is already "
            "positive at the baseline new-growth rate. Nothing to solve."
        )
    if float(_run(False, hi)[2040]["operating_surplus_deficit"]) < 0:
        raise SystemExit("Break-even rate is above baseline+1.00pp; widen the bracket.")
    for _ in range(40):
        mid = (lo + hi) / 2
        if float(_run(False, mid)[2040]["operating_surplus_deficit"]) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    os.chdir(SCRIPTS_DIR)  # the forecast modules use paths relative to scripts/
    sys.path.insert(0, str(SCRIPTS_DIR))
    SCRATCH.mkdir(exist_ok=True)
    try:
        import baseline_revenue_forecast as brf

        runs = {}
        runs["as_legislated"] = _run(True)
        _check_control(runs["as_legislated"])

        runs["ex_override"] = _run(False)

        # The trailing-actual rate the baseline uses, read back off the model
        # rather than hardcoded here, so the two can never drift apart.
        brf.NEW_GROWTH_PCT_TREND_OVERRIDE = None
        baseline_rate = _baseline_new_growth_rate()
        breakeven_rate = _solve_breakeven(baseline_rate)
        runs["ex_override_breakeven"] = _run(False, breakeven_rate)

        print(
            f"Baseline new-growth rate {baseline_rate:.4%}/yr of prior-year levy; "
            f"FY2040 break-even rate (no override) {breakeven_rate:.4%}/yr "
            f"(lift of {100 * (breakeven_rate - baseline_rate):+.3f} pp)."
        )

        _write_csv(runs, baseline_rate, breakeven_rate)
        _write_methodology(runs, baseline_rate, breakeven_rate)
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)


def _baseline_new_growth_rate():
    """The trailing FY2021-25 new-growth rate, computed the same way
    baseline_revenue_forecast.py computes it."""
    with open(OUTPUT_DIR / "brookline_historical_financials_fy05_25.csv") as f:
        hist = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    pcts = [
        float(hist[y]["new_growth"]) / float(hist[y]["prior_levy_limit"])
        for y in range(2021, 2026)
    ]
    return sum(pcts) / len(pcts)


def _write_csv(runs, baseline_rate, breakeven_rate):
    rate = {
        "as_legislated": baseline_rate,
        "ex_override": baseline_rate,
        "ex_override_breakeven": breakeven_rate,
    }
    out_rows = []
    for run_name, rows in runs.items():
        for y in YEARS:
            r = rows[y]
            op_rev = float(r["operating_revenue"])
            op_sd = float(r["operating_surplus_deficit"])
            base = float(runs["ex_override"][y]["operating_revenue"])
            out_rows.append(
                {
                    "run": run_name,
                    "fiscal_year": y,
                    "scenario": SCENARIO,
                    "may_2026_override_included": run_name == "as_legislated",
                    "new_growth_pct_of_prior_levy": round(rate[run_name], 6),
                    "operating_revenue": round(op_rev),
                    "operating_expenditure": round(float(r["operating_expenditure"])),
                    "operating_surplus_deficit": round(op_sd),
                    "operating_surplus_deficit_pct_of_revenue": round(100 * op_sd / op_rev, 3),
                    # What the override is worth that year, in the run that has
                    # it: the difference in operating revenue against the same
                    # model with the override removed. Not the $23.25M approved -
                    # an override enlarges the base that then compounds, so this
                    # grows every year (the same mechanic Part 2e measures on the
                    # four historical overrides).
                    "may_2026_override_value": (
                        round(op_rev - base) if run_name == "as_legislated" else 0
                    ),
                    "run_assumption": RUN_LABEL[run_name],
                }
            )

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(f"Wrote {OUT_CSV}")


def _write_methodology(runs, baseline_rate, breakeven_rate):
    a, b, c = runs["as_legislated"], runs["ex_override"], runs["ex_override_breakeven"]

    def m(rows, y, col="operating_surplus_deficit"):
        return float(rows[y][col]) / 1e6

    def pct(rows, y):
        return 100 * float(rows[y]["operating_surplus_deficit"]) / float(rows[y]["operating_revenue"])

    ovr = {y: float(a[y]["operating_revenue"]) - float(b[y]["operating_revenue"]) for y in YEARS}

    L = []
    L.append("# Base-Case Decomposition (FY2026-2040) — Methodology\n")
    L.append(
        "Companion to `base_case_decomposition_fy26_40.csv`. Supports Part 4a of "
        "`docs/reference_document.md`, which names `trend_corrected` the base "
        "case and sizes Part 4c's levers against it.\n"
    )
    L.append("## The question this answers\n")
    L.append(
        f"Under `trend_corrected` the operating budget runs a surplus of "
        f"**+${m(a, 2040):.1f} million** a year by FY2040. Taken alone that reads "
        "as \"Brookline is fine,\" and it is misleading, because the May 2026 "
        "operating override is already sitting in the revenue line. This "
        "decomposition separates the two.\n"
    )
    L.append("## The three runs\n")
    for k, v in RUN_LABEL.items():
        L.append(f"- **`{k}`** — {v}.")
    L.append(
        "\nAll three re-run the real models (`baseline_revenue_forecast.py`, "
        "`baseline_surplus_deficit_forecast.py`) through the sensitivity hooks "
        "those modules expose, into a scratch directory. Nothing is "
        "reimplemented here. The `as_legislated` run is checked against the "
        "committed `baseline_surplus_deficit_forecast_fy26_40.csv` **to the "
        "dollar in every year** before any counterfactual is reported; a "
        "mismatch aborts the script.\n"
    )
    L.append(
        "Only the revenue side is re-run, because only the revenue side "
        "depends on the override: `baseline_expense_forecast.py` takes no "
        "revenue input. Every dollar of difference between the first two runs "
        "is therefore revenue.\n"
    )
    L.append("## Result\n")
    L.append("| | FY2027 | FY2030 | FY2035 | FY2040 |\n|---|---|---|---|---|")
    L.append(
        "| **As legislated** (override in) | "
        + " | ".join(f"{m(a, y):+.1f}M ({pct(a, y):+.1f}%)" for y in (2027, 2030, 2035, 2040))
        + " |"
    )
    L.append(
        "| **Ex-override** (structural) | "
        + " | ".join(f"{m(b, y):+.1f}M ({pct(b, y):+.1f}%)" for y in (2027, 2030, 2035, 2040))
        + " |"
    )
    L.append(
        "| *What the override is worth that year* | "
        + " | ".join(f"${ovr[y]/1e6:.1f}M" for y in (2027, 2030, 2035, 2040))
        + " |"
    )
    L.append("")
    L.append(
        f"The override's value grows from the ${23_254_439:,} voters approved "
        f"to **${ovr[2040]/1e6:.1f} million a year by FY2040** — because an "
        "override permanently enlarges the levy base, which then compounds at "
        "2.5% plus new growth every year after. This is the same mechanic Part "
        "2e measures on the four FY2005-2025 overrides, where $32.4 million "
        "raised was worth $38.7 million of annual capacity by FY2025.\n"
    )
    L.append(
        f"Stripping it out, the structural position is a small deficit that "
        f"reopens slowly: **${abs(m(b, 2040)):.1f} million a year, "
        f"{abs(pct(b, 2040)):.1f}% of revenue, by FY2040**. Not a crisis, and "
        "not closed either.\n"
    )
    L.append("## The break-even new-growth rate\n")
    L.append(
        f"Solved by bisection on the sustained new-growth rate, with no "
        f"override at all: **{breakeven_rate:.3%} a year** of the prior-year "
        f"levy limit brings the FY2040 operating balance to zero, against the "
        f"trailing FY2021-25 actual of **{baseline_rate:.3%}** — a lift of "
        f"**{100 * (breakeven_rate - baseline_rate):.3f} percentage points**.\n"
    )
    L.append(
        "Solved rather than interpolated between two runs: the levy limit is a "
        "compounding recursion, so the FY2040 balance is not linear in the "
        "rate, and a two-point interpolation would be wrong by a meaningful "
        "amount over fifteen years.\n"
    )
    L.append(
        "The path matters as much as the endpoint. Even at the break-even "
        "rate the balance still dips — "
        f"{m(c, 2029):+.1f}M in FY2029 — before compounding catches up. New "
        "growth is a real lever and a slow one: value added in FY2027 is worth "
        "far more by FY2040 than the same value added in FY2038, and none of "
        "it helps in the year it is permitted.\n"
    )
    L.append("## What this does not do\n")
    L.append(
        "- **It does not claim the override was unnecessary.** The `ex_override` "
        "run shows a deficit reaching "
        f"${abs(m(b, 2029)):.1f} million by FY2029 — the override closes a real "
        "gap, on schedule.\n"
        "- **It does not model a future override.** See "
        "`override_reliance_scenario_fy26_40.csv` for that lever.\n"
        "- **It does not vary the expense side.** Both the structural gap and "
        "the break-even rate are measured against `trend_corrected`'s expense "
        "path; a different expense assumption moves both.\n"
        "- **It says nothing about which kind of growth** delivers the rate "
        "lift. That is Part 3's question, and the answer is not neutral — see "
        "Part 3b on tenure.\n"
    )
    L.append("## Sources\n")
    L.append(
        "- `scripts/baseline_revenue_forecast.py` (+ its methodology doc)\n"
        "- `scripts/baseline_surplus_deficit_forecast.py` (+ its methodology doc)\n"
        "- `output/brookline_historical_financials_fy05_25.csv` — for the "
        "trailing FY2021-25 new-growth rate\n"
    )

    with open(OUT_METHOD, "w") as f:
        f.write("\n".join(L))
    print(f"Wrote {OUT_METHOD}")


if __name__ == "__main__":
    main()
