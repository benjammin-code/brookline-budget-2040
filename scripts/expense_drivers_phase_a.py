"""
Phase A of the expense-driver rebuild: measure the identity historically.

See `docs/expense_drivers_workplan.md` for the full plan. Phase A answers one
descriptive question with no external data and no forecasting:

    For each expense bucket, was growth more people, more expensive people, or
    something that is not people at all?

Three parts, in order:

  A1  Build one annual FTE panel, FY2004-2027, from the two sources that exist.
  A2  Decompose each bucket's growth into headcount and cost per head, using the
      exact multiplicative identity (1+g_spend) = (1+g_FTE)(1+g_cost).
  A3  Split each bucket into personnel and non-personnel, because the identity
      only describes a bucket well where personnel is most of the spend.

## Two seams, both real, both flagged rather than smoothed over

**The FY2020/FY2021 seam.** The FTE panel comes from two sources that do not
overlap: `department_fte_category_fy04_20.csv` (FY2004-2020) and
`department_fte_annual_fy21_27.csv` (FY2021-2027, stitched from three Financial
Plans). There is no year covered by both, so the join CANNOT be cross-validated
the way the FY2021-2027 stitch itself was. Headcount jumps +18.5 FTE at that
seam after sixteen years of flatness, and this script cannot tell you whether
that is real hiring or a change of basis. Every decomposition below is therefore
reported for three windows: pre-seam, post-seam, and full-window with the
crossing marked.

**The FY2025 basis break in the general-fund file.** `town_fte_general_fund_
fy04_27.csv` matches the category sums exactly for FY2004-2024 and then diverges
by 38-44 FTE for FY2025-2027, because those years come from a different measure
("Net General Funded Positions"). This script uses the category/annual series
throughout so the basis is consistent, and reports the divergence as a check.

## What the measure is, stated precisely

`spend_per_fte` is Schedule A category expenditure divided by budgeted funded
FTE. It is NOT salary per FTE. Two reasons to keep saying so:

  - Schedule A is actual expenditure and includes everything non-personnel:
    contracts, materials, fleet, utilities, solid-waste hauling, library
    acquisitions.
  - FTE counts budgeted funded positions, not filled ones.

A3 quantifies how much that matters, per bucket, using the one year where both
salary and Schedule A exist on the same basis.

Run from `scripts/`:  python3 expense_drivers_phase_a.py
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "output"

FTE_CAT_FILE = OUT / "department_fte_category_fy04_20.csv"
FTE_ANN_FILE = OUT / "department_fte_annual_fy21_27.csv"
FTE_GF_FILE = OUT / "town_fte_general_fund_fy04_27.csv"
HIST_FILE = OUT / "brookline_historical_financials_fy05_25.csv"
SALARY_FILE = OUT / "department_fte_salary_by_category_fy19_fy26.csv"
SCHOOL_FILE = OUT / "school_enrollment_staffing_fy05_25.csv"
DESE_FILE = OUT / "school_spending_by_category_fy09_25.csv"

PANEL_OUT = OUT / "expense_drivers_fte_panel_fy04_27.csv"
DECOMP_OUT = OUT / "expense_drivers_decomposition.csv"
METHOD_OUT = OUT / "expense_drivers_phase_a_methodology.md"

SEAM = 2021  # first year of the second FTE source

# Schedule A category <-> FTE category. The FTE files use two different
# spellings of the same five categories; both map here.
CATEGORIES = [
    ("general_government", "General Government", "exp_general_government"),
    ("public_safety", "Public Safety", "exp_public_safety"),
    ("public_works", "Public Works", "exp_public_works"),
    ("human_services", "Human Services", "exp_human_services"),
    ("culture_recreation", "Culture & Recreation", "exp_culture_recreation"),
]


def fnum(x):
    if x in ("", None):
        return None
    return float(x)


# ----------------------------------------------------------------- A1: panel

def build_fte_panel():
    """One annual FTE series per category, FY2004-2027, from two sources."""
    panel = {}

    with open(FTE_CAT_FILE) as f:
        for r in csv.DictReader(f):
            y = int(r["fiscal_year"])
            panel[y] = {key: float(r[key]) for key, _, _ in CATEGORIES}
            panel[y]["_source"] = "category_file_fy04_20"

    with open(FTE_ANN_FILE) as f:
        rows = list(csv.DictReader(f))
    for y in range(2021, 2028):
        col = f"fy{y}"
        acc = {key: 0.0 for key, _, _ in CATEGORIES}
        label_to_key = {label: key for key, label, _ in CATEGORIES}
        for r in rows:
            v = fnum(r.get(col))
            if v is None:
                continue
            key = label_to_key.get(r["category"])
            if key is None:
                raise SystemExit(f"Unmapped category in annual FTE file: {r['category']!r}")
            acc[key] += v
        if any(acc.values()):
            acc["_source"] = "annual_file_fy21_27"
            panel[y] = acc
    return panel


def check_panel_against_general_fund(panel):
    """The general-fund file is a known mixed basis. Report where it agrees and
    where it does not, rather than assuming either."""
    gf = {}
    with open(FTE_GF_FILE) as f:
        for r in csv.DictReader(f):
            gf[int(r["fiscal_year"])] = float(r["general_fund_fte_total"])
    lines = []
    for y in sorted(panel):
        tot = sum(panel[y][k] for k, _, _ in CATEGORIES)
        g = gf.get(y)
        if g is None:
            continue
        lines.append((y, tot, g, tot - g))
    return lines


# --------------------------------------------------- A2: the decomposition

def detect_reclassifications(hist, threshold=0.15, window=3):
    """Flag PERSISTENT level shifts in a category's share of total expenditure.

    A category can move sharply for real reasons: Public Works swings with snow,
    and a single bad winter is volatility, not a definitional change. What
    distinguishes a reclassification is that the shift *stays*. So compare the
    mean share over the `window` years before a year against the mean over the
    `window` years from it, rather than comparing two adjacent years. A one-year
    spike averages away; a function moved between Schedule A categories does not.

    Written because a naive adjacent-year test flagged twelve years, most of them
    ordinary volatility, and would have driven the window choice off noise.
    """
    years = sorted(hist)
    tot = {y: fnum(hist[y].get("exp_total_expenditures")) for y in years}
    flags = []
    for y in years:
        before = [yy for yy in range(y - window, y) if tot.get(yy)]
        after = [yy for yy in range(y, y + window) if tot.get(yy)]
        if len(before) < window or len(after) < window:
            continue
        for key, label, col in CATEGORIES:
            sb = [fnum(hist[yy].get(col)) / tot[yy] for yy in before
                  if fnum(hist[yy].get(col))]
            sa = [fnum(hist[yy].get(col)) / tot[yy] for yy in after
                  if fnum(hist[yy].get(col))]
            if len(sb) < window or len(sa) < window:
                continue
            mb, ma = sum(sb) / len(sb), sum(sa) / len(sa)
            rel = (ma - mb) / mb
            if abs(rel) >= threshold:
                flags.append(dict(year=y, bucket=label, share_before=mb,
                                  share_after=ma, rel_move=rel))
    return flags


def decompose(spend, fte, y0, y1):
    """Exact multiplicative split. Returns None if either endpoint is missing."""
    if y0 not in spend or y1 not in spend or y0 not in fte or y1 not in fte:
        return None
    if not (spend[y0] and fte[y0] and fte[y1]):
        return None
    n = y1 - y0
    g_spend = (spend[y1] / spend[y0]) ** (1 / n) - 1
    g_fte = (fte[y1] / fte[y0]) ** (1 / n) - 1
    # cost per head is the exact residual of the identity, not a separate
    # measurement: (1+g_spend) = (1+g_fte)(1+g_cost)
    g_cost = (1 + g_spend) / (1 + g_fte) - 1
    return dict(years=n, g_spend=g_spend, g_fte=g_fte, g_cost=g_cost,
                spend0=spend[y0], spend1=spend[y1], fte0=fte[y0], fte1=fte[y1],
                spf0=spend[y0] / fte[y0], spf1=spend[y1] / fte[y1])


def main():
    panel = build_fte_panel()

    with open(HIST_FILE) as f:
        hist = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}

    # ---------------------------------------------------------- CONTROLS
    print("=" * 76)
    print("CONTROLS")
    print("=" * 76)

    gf_lines = check_panel_against_general_fund(panel)
    agree = [l for l in gf_lines if abs(l[3]) < 0.01]
    disagree = [l for l in gf_lines if abs(l[3]) >= 0.01]
    print(f"  Panel vs. general-fund file: agrees to 0.01 FTE in {len(agree)} years "
          f"(FY{min(l[0] for l in agree)}-FY{max(l[0] for l in agree)}), "
          f"diverges in {len(disagree)}")
    for y, tot, g, d in disagree:
        print(f"      FY{y}: panel {tot:,.2f} vs general-fund file {g:,.2f}  ({d:+.2f}) "
              f"- different measure, see module docstring")

    # Negative control: the identity must fail if we feed it a wrong FTE.
    test_spend = {2010: 100.0, 2020: 200.0}
    test_fte = {2010: 10.0, 2020: 10.0}
    d_flat = decompose(test_spend, test_fte, 2010, 2020)
    test_fte_bad = {2010: 10.0, 2020: 20.0}
    d_grow = decompose(test_spend, test_fte_bad, 2010, 2020)
    ok = abs(d_flat["g_cost"] - d_flat["g_spend"]) < 1e-12 and abs(d_grow["g_cost"]) < 1e-12
    print(f"  {'PASS' if ok else 'FAIL'}  identity check: flat headcount puts all growth in "
          f"cost per head ({d_flat['g_cost']:.4%}); headcount doubling with spend doubling "
          f"puts none there ({d_grow['g_cost']:.4%})")

    # Positive control: recompose must return the observed spend growth exactly.
    worst = 0.0
    for key, label, col in CATEGORIES:
        spend = {y: float(hist[y][col]) for y in hist if hist[y].get(col)}
        fte = {y: panel[y][key] for y in panel}
        d = decompose(spend, fte, 2005, 2020)
        if d:
            recomposed = (1 + d["g_fte"]) * (1 + d["g_cost"]) - 1
            worst = max(worst, abs(recomposed - d["g_spend"]))
    print(f"  {'PASS' if worst < 1e-12 else 'FAIL'}  recomposition: headcount x cost per head "
          f"returns observed spend growth, worst error {worst:.2e}")

    flags = detect_reclassifications(hist)
    if flags:
        print(f"  FLAG  persistent shifts in category share of total expenditure:")
        for fl in sorted(flags, key=lambda r: (r["year"], r["bucket"])):
            print(f"      FY{fl['year']} {fl['bucket']:22s} mean share "
                  f"{fl['share_before']*100:5.2f}% -> {fl['share_after']*100:5.2f}%  "
                  f"({fl['rel_move']*100:+.0f}%, 3-year means either side)")
        print("      A share that shifts and stays shifted is a reclassification, not a")
        print("      trend. Any rate measured across one of these years is an artifact.")
    else:
        print("  No persistent category-share shifts detected.")
    print()

    # ---------------------------------------------- A2: town decomposition
    # Windows are chosen deliberately rather than derived from the detector,
    # because the detector reports evidence and the choice of what to do about it
    # is a judgment call that belongs in the open:
    #   FY2011  first year clear of the FY2010 reclassification
    #   FY2020  last year of the first FTE source
    #   FY2021  first year of the second FTE source
    #   FY2025  last year of Schedule A actuals
    windows = [
        ("clean, pre-FTE-seam", 2011, 2020),
        ("post-FTE-seam", 2021, 2025),
        ("clean, crosses FTE seam", 2011, 2025),
        ("all data, spans the FY2010 break", 2005, 2025),
    ]
    rows_out = []

    print("=" * 76)
    print("A2. TOWN DEPARTMENTAL: was it more people, or more expensive people?")
    print("=" * 76)
    for wlabel, y0, y1 in windows:
        cross = y0 < SEAM <= y1
        print(f"\n  --- {wlabel}, FY{y0}-FY{y1}"
              + ("   [CROSSES THE UNVALIDATED FY2020/21 SEAM]" if cross else ""))
        print(f"  {'category':24s}{'spend':>9}{'headcount':>11}{'cost/head':>11}"
              f"{'$/FTE start':>14}{'$/FTE end':>13}")
        for key, label, col in CATEGORIES:
            spend = {y: float(hist[y][col]) for y in hist if hist[y].get(col)}
            fte = {y: panel[y][key] for y in panel}
            d = decompose(spend, fte, y0, y1)
            if not d:
                continue
            print(f"  {label:24s}{d['g_spend']*100:>8.2f}%{d['g_fte']*100:>10.2f}%"
                  f"{d['g_cost']*100:>10.2f}%{d['spf0']:>14,.0f}{d['spf1']:>13,.0f}")
            rows_out.append(dict(
                bucket=label, window=wlabel, fy_start=y0, fy_end=y1,
                crosses_fte_seam=cross,
                spend_cagr=round(d["g_spend"], 6), fte_cagr=round(d["g_fte"], 6),
                cost_per_fte_cagr=round(d["g_cost"], 6),
                spend_start=round(d["spend0"]), spend_end=round(d["spend1"]),
                fte_start=round(d["fte0"], 2), fte_end=round(d["fte1"], 2),
                spend_per_fte_start=round(d["spf0"]), spend_per_fte_end=round(d["spf1"]),
                share_of_growth_from_headcount=round(
                    d["g_fte"] / d["g_spend"], 4) if d["g_spend"] else None,
                measure="Schedule A category expenditure / budgeted funded FTE",
            ))

    # --------------------------------- A2: is the split robust to the window?
    # The FY2010 reclassification forces a judgment about where the clean window
    # starts. That judgment should not decide the answer, so vary it and look.
    print()
    print("  Robustness: share of spend growth coming from headcount, by window start")
    print(f"  {'category':24s}" + "".join(f"{'FY'+str(s)+'-20':>12s}" for s in (2011, 2012, 2013, 2014)))
    worst_head_share = 0.0
    for key, label, col in CATEGORIES:
        spend = {y: float(hist[y][col]) for y in hist if hist[y].get(col)}
        fte = {y: panel[y][key] for y in panel}
        cells = []
        for s in (2011, 2012, 2013, 2014):
            d = decompose(spend, fte, s, 2020)
            if d and d["g_spend"]:
                sh = d["g_fte"] / d["g_spend"]
                worst_head_share = max(worst_head_share, sh)
                cells.append(f"{sh*100:11.0f}%")
            else:
                cells.append(f"{'n/a':>12s}")
        print(f"  {label:24s}" + "".join(cells))
    print(f"  Highest headcount share under ANY of those starts: {worst_head_share*100:.0f}%.")
    print("  Cost per head carries the rest, in every category and every window.")
    print("  Human Services is the one that moves with the start year; read it as a")
    print("  range rather than a number.")

    # ------------------------------------------------------- A2: schools
    print()
    print("=" * 76)
    print("A2. SCHOOLS: the same split, on enrollment and staff")
    print("=" * 76)
    with open(SCHOOL_FILE) as f:
        sch = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    edu = {y: float(hist[y]["exp_education"]) for y in hist if hist[y].get("exp_education")}
    enroll = {y: float(sch[y]["total_enrollment"]) for y in sch if sch[y].get("total_enrollment")}
    staff = {y: float(sch[y]["total_staff_fte"]) for y in sch if sch[y].get("total_staff_fte")}
    teach = {y: float(sch[y]["teacher_fte"]) for y in sch if sch[y].get("teacher_fte")}

    for driver, dlabel in ((staff, "total school staff FTE"), (enroll, "enrollment"),
                           (teach, "teacher FTE")):
        yrs = sorted(set(edu) & set(driver))
        y0, y1 = yrs[0], yrs[-1]
        d = decompose(edu, driver, y0, y1)
        if d:
            print(f"  FY{y0}-FY{y1}, per {dlabel:24s} spend {d['g_spend']*100:5.2f}%"
                  f" = quantity {d['g_fte']*100:5.2f}% + cost per unit {d['g_cost']*100:5.2f}%")
            rows_out.append(dict(
                bucket=f"Schools (per {dlabel})", window="full", fy_start=y0, fy_end=y1,
                crosses_fte_seam=False,
                spend_cagr=round(d["g_spend"], 6), fte_cagr=round(d["g_fte"], 6),
                cost_per_fte_cagr=round(d["g_cost"], 6),
                spend_start=round(d["spend0"]), spend_end=round(d["spend1"]),
                fte_start=round(d["fte0"], 2), fte_end=round(d["fte1"], 2),
                spend_per_fte_start=round(d["spf0"]), spend_per_fte_end=round(d["spf1"]),
                share_of_growth_from_headcount=round(
                    d["g_fte"] / d["g_spend"], 4) if d["g_spend"] else None,
                measure="Schedule A education expenditure / the named quantity",
            ))

    # -------------------------- A3: personnel vs non-personnel, town side
    print()
    print("=" * 76)
    print("A3. HOW MUCH OF EACH BUCKET IS EVEN PEOPLE?")
    print("=" * 76)
    with open(SALARY_FILE) as f:
        sal = {r["category"]: r for r in csv.DictReader(f)}
    print("  Salary budget as a share of Schedule A category spend, FY2019")
    print("  (FY2019 is the one year where both exist on the same basis; the salary")
    print("   table's other year is FY2026 and Schedule A ends FY2025.)")
    print(f"\n  {'category':24s}{'FY19 salary':>14}{'FY19 SchedA':>14}{'personnel':>11}{'non-personnel':>15}")
    a3 = []
    for key, label, col in CATEGORIES:
        s19 = float(sal[label]["salary_budget_fy19"])
        a19 = float(hist[2019][col])
        share = s19 / a19
        print(f"  {label:24s}{s19:>14,.0f}{a19:>14,.0f}{share*100:>10.0f}%{(1-share)*100:>14.0f}%")
        a3.append((label, s19, a19, share))
        rows_out.append(dict(
            bucket=label, window="personnel_share_fy2019", fy_start=2019, fy_end=2019,
            crosses_fte_seam=False, spend_cagr=None, fte_cagr=None,
            cost_per_fte_cagr=None, spend_start=round(a19), spend_end=round(a19),
            fte_start=None, fte_end=None, spend_per_fte_start=None,
            spend_per_fte_end=None,
            share_of_growth_from_headcount=None,
            measure=f"salary {s19:,.0f} / Schedule A {a19:,.0f} = {share:.3f} personnel share",
        ))
    print("\n  Note: water and sewer are self-supporting Enterprise Funds outside the")
    print("  General Fund, so they are not in any row above. Solid-waste collection is,")
    print("  inside Public Works, as a contract rather than as payroll.")

    # ------------------------------ A3: schools, DESE eleven categories
    print()
    print("  School spending disaggregated, DESE per-pupil categories, FY2009-FY2025")
    with open(DESE_FILE) as f:
        dese = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    cats = [c for c in next(iter(dese.values())) if c != "fiscal_year"]
    y0, y1 = min(dese), max(dese)
    n = y1 - y0
    print(f"  {'category':50s}{'FY'+str(y0):>9}{'FY'+str(y1):>9}{'CAGR':>8}{'share':>8}")
    tot1 = float(dese[y1]["Total In-District Expenditures"])
    dese_rows = []
    for c in cats:
        a, b = dese[y0].get(c), dese[y1].get(c)
        if not a or not b:
            continue
        a, b = float(a), float(b)
        g = (b / a) ** (1 / n) - 1
        share = b / tot1 if "Total" not in c else None
        dese_rows.append((c, a, b, g, share))
    for c, a, b, g, share in sorted(dese_rows, key=lambda r: -r[3]):
        st = f"{share*100:7.1f}%" if share is not None else "       -"
        print(f"  {c[:49]:50s}{a:>9,.0f}{b:>9,.0f}{g*100:>7.2f}%{st}")

    # ------------------------------------------------------------- write
    with open(DECOMP_OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    print(f"\nWrote {DECOMP_OUT}")

    with open(PANEL_OUT, "w", newline="") as f:
        cols = ["fiscal_year"] + [k for k, _, _ in CATEGORIES] + ["total", "source"]
        w = csv.writer(f)
        w.writerow(cols)
        for y in sorted(panel):
            vals = [panel[y][k] for k, _, _ in CATEGORIES]
            w.writerow([y] + [round(v, 2) for v in vals]
                       + [round(sum(vals), 2), panel[y]["_source"]])
    print(f"Wrote {PANEL_OUT}")

    write_methodology(panel, gf_lines, rows_out, a3, dese_rows, y0, y1)
    print(f"Wrote {METHOD_OUT}")


def write_methodology(panel, gf_lines, rows_out, a3, dese_rows, dy0, dy1):
    L = []
    L.append("# Expense Drivers, Phase A: what actually drove historical growth\n")
    L.append("Companion to `expense_drivers_decomposition.csv` and "
             "`expense_drivers_fte_panel_fy04_27.csv`. Plan: "
             "`docs/expense_drivers_workplan.md`. Generated by "
             "`scripts/expense_drivers_phase_a.py`.\n")

    L.append("## The question\n")
    L.append("For each expense bucket, was growth more people, more expensive people, "
             "or something that is not people at all? No external data, no forecasting, "
             "no causal claim.\n")

    L.append("## The identity\n")
    L.append("```\n    Spend = FTE x CostPerFTE\n"
             "    (1 + g_spend) = (1 + g_FTE) x (1 + g_cost)\n```\n")
    L.append("`g_cost` is computed as the exact residual of that identity rather than "
             "measured separately, so the two terms always recompose to observed growth. "
             "That is an accounting identity, not a finding, and the script verifies it "
             "to machine precision as a control.\n")

    L.append("## What the measure is, and is not\n")
    L.append("`spend_per_fte` is **Schedule A category expenditure divided by budgeted "
             "funded FTE**. It is not salary per FTE. Schedule A is actual expenditure "
             "and carries everything non-personnel: contracts, materials, fleet, "
             "utilities, solid-waste hauling, library acquisitions. FTE counts budgeted "
             "funded positions, not filled ones. Section A3 quantifies how much that "
             "matters per bucket.\n")

    L.append("## Two seams, flagged rather than smoothed\n")
    L.append("**FY2020/FY2021.** The FTE panel joins two sources that share no year: "
             "`department_fte_category_fy04_20.csv` and "
             "`department_fte_annual_fy21_27.csv`. The join therefore **cannot be "
             "cross-validated**, unlike the FY2021-2027 stitch itself, which was checked "
             "across three Financial Plans with zero discrepancies. Headcount rises "
             f"{panel[2021]['general_government'] + panel[2021]['public_safety'] + panel[2021]['public_works'] + panel[2021]['human_services'] + panel[2021]['culture_recreation'] - sum(panel[2020][k] for k in ('general_government','public_safety','public_works','human_services','culture_recreation')):+.2f}"
             " FTE across that seam after sixteen years of flatness, and this analysis "
             "cannot tell you whether that is hiring or a change of basis. Every "
             "decomposition is reported pre-seam, post-seam and full-window so the "
             "reader can see what depends on it.\n")
    dis = [l for l in gf_lines if abs(l[3]) >= 0.01]
    if dis:
        L.append(f"**FY{min(l[0] for l in dis)}.** `town_fte_general_fund_fy04_27.csv` "
                 "matches the category sums exactly through FY"
                 f"{max(l[0] for l in gf_lines if abs(l[3]) < 0.01)} and then diverges by "
                 f"{min(abs(l[3]) for l in dis):.0f}-{max(abs(l[3]) for l in dis):.0f} FTE, "
                 "because those years use a different measure (Net General Funded "
                 "Positions). This analysis uses the category/annual series throughout so "
                 "the basis stays consistent.\n")

    L.append("## A2. Town departmental\n")
    for wlabel in ("clean, pre-FTE-seam", "post-FTE-seam", "clean, crosses FTE seam", "all data, spans the FY2010 break"):
        sel = [r for r in rows_out if r["window"] == wlabel and r["fte_cagr"] is not None]
        if not sel:
            continue
        w = sel[0]
        cross = " (crosses the unvalidated seam)" if w["crosses_fte_seam"] else ""
        L.append(f"### {wlabel}, FY{w['fy_start']}-FY{w['fy_end']}{cross}\n")
        L.append("| Bucket | Spend | Headcount | Cost per head | $/FTE start | $/FTE end |")
        L.append("|---|---|---|---|---|---|")
        for r in sel:
            if r["bucket"].startswith("Schools"):
                continue
            L.append(f"| {r['bucket']} | {r['spend_cagr']*100:.2f}% | "
                     f"{r['fte_cagr']*100:.2f}% | {r['cost_per_fte_cagr']*100:.2f}% | "
                     f"${r['spend_per_fte_start']:,} | ${r['spend_per_fte_end']:,} |")
        L.append("")

    L.append("## A3. How much of each bucket is even people\n")
    L.append("Salary budget as a share of Schedule A category spend, FY2019. That is the "
             "one year where both exist on the same basis: the salary table carries FY2019 "
             "and FY2026, and Schedule A ends FY2025.\n")
    L.append("| Bucket | FY2019 salary | FY2019 Schedule A | Personnel | Non-personnel |")
    L.append("|---|---|---|---|---|")
    for label, s19, a19, share in sorted(a3, key=lambda r: -r[3]):
        L.append(f"| {label} | ${s19:,.0f} | ${a19:,.0f} | {share*100:.0f}% | "
                 f"{(1-share)*100:.0f}% |")
    L.append("")
    L.append("Water and sewer are self-supporting Enterprise Funds outside the General "
             "Fund and appear nowhere above. Solid-waste collection does appear, inside "
             "Public Works, as a contract rather than as payroll.\n")

    L.append(f"## A3. School spending disaggregated, DESE categories, FY{dy0}-FY{dy1}\n")
    L.append("Per-pupil dollars, so enrollment is already divided out. Sorted by growth "
             "rate.\n")
    L.append(f"| Category | FY{dy0} | FY{dy1} | CAGR | Share of in-district, FY{dy1} |")
    L.append("|---|---|---|---|---|")
    for c, a, b, g, share in sorted(dese_rows, key=lambda r: -r[3]):
        st = f"{share*100:.1f}%" if share is not None else "n/a"
        L.append(f"| {c} | ${a:,.0f} | ${b:,.0f} | {g*100:.2f}% | {st} |")
    L.append("")

    L.append("## What Phase A does not do\n")
    L.append("- **No causal claim.** These are accounting decompositions. That a bucket "
             "grew through cost per head says nothing about why, and the residual has not "
             "been separated into wage growth, step progression, turnover or role mix. "
             "That is Phase B, and it needs an external wage index.\n"
             "- **No link to growth drivers.** Whether headcount responds to new housing "
             "or new commercial space is Phase C, deliberately untouched here.\n"
             "- **No non-personnel model.** A3 measures how large the non-personnel share "
             "is; it does not model what drives it.\n"
             "- **No forecasting.** Phase D.\n")

    with open(METHOD_OUT, "w") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()
