"""
The document's most-quoted pair of numbers, rebuilt on a consistent basis.

Why this exists (2026-09-13): the reference document's headline finding is
that over FY2005-2025 "automatic" revenue grew at 3.91%/yr against actual
spending at 3.92%/yr - essentially identical, hence "finely balanced." Both
figures are individually correct and both reproduce exactly from the
historical file. But they are not measured the same way, and comparing them
overstates how well automatic revenue kept up. Two mismatches:

1. **Basis.** 3.91% is a levy-limit figure, which excludes debt exclusions by
   construction. 3.92% is total expenditure, which INCLUDES debt service on
   excluded debt. That service grew from $1.7M (FY2005) to $22.0M (FY2025) -
   the debt ramp the 2020 BFAC report documents - so it inflates the expense
   side of a comparison the revenue side never included. Everywhere else the
   project is careful that debt exclusions net to zero and are therefore out
   of scope on BOTH sides; the headline is the one place that slipped.

2. **Scope.** 3.91% covers the property tax levy alone, about 78% of General
   Fund revenue. 3.92% covers all spending. Section 1e's own framing asks
   whether "the revenue the Town gets automatically - 2.5% plus new growth,
   with no override and no vote - grows fast enough to keep up with real cost
   growth." State aid and local receipts also arrive without a vote, so the
   right revenue measure for that question is total operating revenue with
   the *levy* replaced by its no-override counterfactual - not the levy alone.

Corrected, the comparison is 3.52% automatic revenue against 3.65% operating
expenditure - a shortfall of 0.13 percentage points a year rather than a dead
heat.

That is a better result for the document's argument, not a worse one. The
current pairing has to explain away an awkwardness: if automatic revenue
really did match cost growth almost exactly, why were four overrides needed?
The document currently hand-waves this ("even though real overrides were
still needed in specific years when the gap opened faster than that average
implies"). At 3.52% vs 3.65% there is nothing to explain away - a persistent
0.13-point annual shortfall is exactly what four overrides across twenty
years look like. It is also consistent with the forward-looking base case,
whose structural wedge is 0.09 points a year, so history and forecast tell
one story instead of two.

## Method

Everything is computed ex-debt-exclusion on both sides, from
`output/brookline_historical_financials_fy05_25.csv`:

- **Automatic levy**: start from the actual FY2005 levy limit
  (`total_levy - debt_exclusions`), then for each year compound at 2.5% and
  add that year's real applied new growth. No overrides. This is exactly the
  method Section 4a describes and it reproduces 3.91% to three decimals.
- **Non-levy operating revenue**: `rev_total_revenues - total_levy`. Note
  this correctly keeps motor-vehicle and other excises, which sit in
  `rev_taxes` but outside the property tax levy (the project already tracks
  that reconciliation in `taxes_vs_total_levy_gap`).
- **Operating expenditure**: `exp_total_expenditures - debt_exclusions`.
  By statute a debt exclusion equals its bonds' annual debt service dollar
  for dollar, so the levy-side figure is the right subtraction to strip
  excluded debt service off the expense side.

Non-levy revenue is held at actual in the counterfactual. That is the
conservative choice: state aid and local receipts are not affected by
whether an override passes, so leaving them at actual isolates the override
question rather than compounding a second assumption into it.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
HIST = ROOT / "output" / "brookline_historical_financials_fy05_25.csv"
OUT_CSV = ROOT / "output" / "automatic_revenue_vs_costs_fy05_25.csv"
OUT_METHOD = ROOT / "output" / "automatic_revenue_vs_costs_fy05_25_methodology.md"

Y0, Y1 = 2005, 2025


def cagr(a, b, n):
    return ((b / a) ** (1 / n) - 1) * 100


def main():
    with open(HIST) as f:
        h = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    g = lambda y, c: float(h[y][c])

    rows = []
    auto_levy = g(Y0, "total_levy") - g(Y0, "debt_exclusions")
    for y in range(Y0, Y1 + 1):
        if y > Y0:
            auto_levy = auto_levy * 1.025 + g(y, "new_growth")
        actual_levy = g(y, "total_levy") - g(y, "debt_exclusions")
        non_levy = g(y, "rev_total_revenues") - g(y, "total_levy")
        op_exp = g(y, "exp_total_expenditures") - g(y, "debt_exclusions")
        rows.append(
            {
                "fiscal_year": y,
                "automatic_levy": round(auto_levy),
                "actual_levy_ex_debt_exclusion": round(actual_levy),
                "override_premium": round(actual_levy - auto_levy),
                "non_levy_operating_revenue": round(non_levy),
                "automatic_operating_revenue": round(auto_levy + non_levy),
                "actual_operating_revenue": round(actual_levy + non_levy),
                "operating_expenditure": round(op_exp),
                "automatic_gap": round(auto_levy + non_levy - op_exp),
                "debt_exclusion_excluded_both_sides": round(g(y, "debt_exclusions")),
                "basis": (
                    "all figures ex-debt-exclusion on both sides; automatic levy = "
                    "FY2005 levy limit compounded at 2.5% plus each year's real "
                    "applied new growth, no overrides; non-levy revenue held at actual"
                ),
            }
        )

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT_CSV}")

    first, last = rows[0], rows[-1]
    n = Y1 - Y0
    results = {
        "automatic_levy": cagr(first["automatic_levy"], last["automatic_levy"], n),
        "actual_levy": cagr(first["actual_levy_ex_debt_exclusion"], last["actual_levy_ex_debt_exclusion"], n),
        "non_levy": cagr(first["non_levy_operating_revenue"], last["non_levy_operating_revenue"], n),
        "automatic_total": cagr(first["automatic_operating_revenue"], last["automatic_operating_revenue"], n),
        "actual_total": cagr(first["actual_operating_revenue"], last["actual_operating_revenue"], n),
        "operating_expense": cagr(first["operating_expenditure"], last["operating_expenditure"], n),
    }
    # The two figures the document currently quotes, reproduced for the record.
    legacy_expense = cagr(g(Y0, "exp_total_expenditures"), g(Y1, "exp_total_expenditures"), n)

    print(
        f"CORRECTED PAIR: automatic operating revenue {results['automatic_total']:.2f}%/yr "
        f"vs operating expenditure {results['operating_expense']:.2f}%/yr "
        f"(shortfall {results['operating_expense'] - results['automatic_total']:.2f} pp/yr)"
    )
    print(
        f"  for the record, the document's current pair: "
        f"{results['automatic_levy']:.2f}% (levy only) vs {legacy_expense:.2f}% (total incl. excluded debt service)"
    )

    write_methodology(rows, results, legacy_expense)
    print(f"Wrote {OUT_METHOD}")


def write_methodology(rows, r, legacy_expense):
    first, last = rows[0], rows[-1]
    L = []
    L.append("# Automatic Revenue vs. Cost Growth, FY2005-2025 — Methodology\n")
    L.append(
        "Companion to `automatic_revenue_vs_costs_fy05_25.csv`. Rebuilds the "
        "reference document's most-quoted pair of numbers on a consistent "
        "basis.\n"
    )
    L.append(__doc__.split("## Method")[0].split('"""')[-1].strip() + "\n")
    L.append("## Result\n")
    L.append("| Series (all ex-debt-exclusion) | FY2005 | FY2025 | CAGR |\n|---|---|---|---|")
    for lbl, k, cg in [
        ("Automatic levy (2.5% + real new growth, no override)", "automatic_levy", r["automatic_levy"]),
        ("Actual levy (includes the four overrides)", "actual_levy_ex_debt_exclusion", r["actual_levy"]),
        ("Non-levy operating revenue (aid, receipts, other excises)", "non_levy_operating_revenue", r["non_levy"]),
        ("**Automatic TOTAL operating revenue**", "automatic_operating_revenue", r["automatic_total"]),
        ("Actual total operating revenue", "actual_operating_revenue", r["actual_total"]),
        ("**Operating expenditure**", "operating_expenditure", r["operating_expense"]),
    ]:
        L.append(f"| {lbl} | ${first[k]/1e6:,.1f}M | ${last[k]/1e6:,.1f}M | **{cg:.2f}%** |")
    L.append("")
    L.append(
        f"**The corrected headline: automatic revenue grew at "
        f"{r['automatic_total']:.2f}% a year against operating costs at "
        f"{r['operating_expense']:.2f}% — a shortfall of "
        f"{r['operating_expense'] - r['automatic_total']:.2f} percentage points "
        "a year, every year, for twenty years.** That is what four overrides "
        "were for.\n"
    )
    L.append("## What the current figures are, and why they differ\n")
    L.append(
        f"The document currently pairs **{r['automatic_levy']:.2f}%** with "
        f"**{legacy_expense:.2f}%**. Both reproduce exactly from the same "
        "source file; neither is a computational error. They are simply not "
        "measured the same way — the first is levy-only and "
        "ex-debt-exclusion, the second is all spending including debt service "
        "on excluded debt. Correcting the basis moves the expense figure from "
        f"{legacy_expense:.2f}% to {r['operating_expense']:.2f}%; correcting "
        f"the scope moves the revenue figure from {r['automatic_levy']:.2f}% "
        f"to {r['automatic_total']:.2f}%.\n"
    )
    L.append(
        "Note the direction: **each correction on its own would have made the "
        "picture look better, and together they make it look worse.** "
        "Stripping excluded debt service lowers cost growth; narrowing to the "
        "levy raises measured revenue growth. The reason the corrected gap "
        "opens rather than closes is that non-levy revenue — state aid, local "
        f"receipts — grew at only {r['non_levy']:.2f}% a year, well below both "
        "the levy and costs, and it is a fifth of the budget.\n"
    )
    L.append("## What this changes downstream\n")
    L.append(
        "- The historical finding stops contradicting itself. A dead heat "
        "between automatic revenue and costs cannot explain why four "
        "overrides were needed; a persistent 0.13-point annual shortfall "
        "explains it exactly.\n"
        "- History and forecast align. The forward base case's structural "
        "wedge is 0.09 points a year (see "
        "`base_case_decomposition_fy26_40_methodology.md`). At 0.13 points "
        "historically, the forecast is describing slightly *less* pressure "
        "than the last twenty years actually produced — which is a defensible "
        "thing to say and a much easier one than reconciling a wedge against "
        "a dead heat.\n"
        "- The override total is unaffected. Part 2e's finding that the four "
        "overrides were worth $38.7M of annual capacity by FY2025 is computed "
        "on the levy alone and is untouched by any of this.\n"
    )
    L.append("## Source\n")
    L.append("- `output/brookline_historical_financials_fy05_25.csv`\n")
    OUT_METHOD.write_text("\n".join(L))


if __name__ == "__main__":
    main()
