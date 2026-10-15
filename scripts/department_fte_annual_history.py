"""
Town department headcount, FY2021-FY2027 - a real ANNUAL series, not just
the two-point FY2019/FY2026 comparison in department_fte_history.py.

Added 2026-09-02 (Ben: "yes please check the financial plan pdfs to see
if they contain more department detail"). They do, and it's better than
what we had: each of the FY2025/FY2026/FY2027 Financial Plans (`data/
FY2025-Financial-Plan.pdf` p.57, `data/FY2026-Financial-Plan.pdf` p.56,
`data/FY2027-Financial-Plan.pdf` p.79-80) carries its own "Full-Time
Equivalent Positions Funded" table - All Positions (General Fund + Capital/
Special Appropriations + Grants + Enterprise/Revolving combined), by
department, for a trailing 5-year window ending in that plan's own budget
year. The three plans' windows overlap (FY2025 Plan: FY2021-2025; FY2026
Plan: FY2022-2026; FY2027 Plan: FY2023-2027), so stitching them together
gives a real FY2021-2027 annual series - 7 points instead of 2 - with
every overlapping year independently confirmed across 2-3 separately-
published documents.

## Cross-validation: verified, not assumed

Checked every department's figure in every year covered by more than one
plan. **Full agreement, zero discrepancies, for FY2021-2024** (confirmed
identically across all plans that cover them) - real, solid data.

**One real, traceable discrepancy found: FY2025.** The FY2025 Financial
Plan's own FY2025 column (its "current/recommended" budget year at the
time of publication) shows 726.56 total positions; the FY2026 and FY2027
Financial Plans - published later, reporting FY2025 as settled history -
both independently agree on **721.56**, a real -5.00 FTE difference.
Traced to exactly 4 departments (not noise, not spread evenly): Library
(59.22→56.22, -3.00), Public Works (140.91→139.91, -1.00), Police
(175.30→173.30, -2.00), and ODEICR (2.72→3.72, +1.00) - net -5.00,
exactly matching the townwide gap. This dataset uses the later, settled
figures (721.56 basis) for FY2025, consistent with using each year's most
mature/confirmed data point; the FY2025 Plan's own original recommended
figures are kept in a separate `*_as_recommended_fy25plan` column for
anyone who wants the "as originally proposed" comparison.

**FY2026** is confirmed identically between the FY2026 Plan (as its own
current year) and the FY2027 Plan (as settled history) - no discrepancy.
**FY2027** exists only in the FY2027 Plan, as its own current/recommended
year - no later plan yet exists to confirm it as settled, so it carries
the same caveat every other "Town's own published FY26-31" figure in this
project already carries (a real, stated plan, not yet an audited actual).

## Scope note vs. department_fte_history.py

This is "All Positions" (matches that script's "Total FTE" = General Fund
+ Soft Money), by department - same concept, different source and window.
The ERSC-sourced FY2019/FY2026 two-point file still has the longer look-
back (to FY2019); this file has the real annual granularity FY2021-2027.
Department names are normalized to match `department_fte_history.py`'s
naming exactly, so a category rollup here uses the same Schedule-A-
category mapping.

Outputs:
  ../output/department_fte_annual_fy21_27.csv
  ../output/department_fte_annual_fy21_27_notes.md
"""
import csv
from pathlib import Path

from department_fte_history import CATEGORY_LABELS, DEPARTMENTS as ERSC_DEPARTMENTS

ROOT = Path(__file__).parent.parent
OUT_CSV = ROOT / "output/department_fte_annual_fy21_27.csv"
NOTES_FILE = ROOT / "output/department_fte_annual_fy21_27_notes.md"

DEPT_TO_CATEGORY = {name: cat for name, cat, *_ in ERSC_DEPARTMENTS}
# Name variants across the three plans, normalized to department_fte_history.py's names.
NAME_MAP = {
    "SELECT BOARD": "Select Board",
    "HUMAN RESOURCES": "Human Resources",
    "INFORMATION TECHNOLOGY": "Information Technology",
    "FINANCE": "Finance Department",
    "LEGAL": "Legal Services",
    "ADVISORY COMMITTEE": "Advisory Committee",
    "TOWN CLERK": "Town Clerk",
    "PLANNING & COMMUNITY DEVELOPMENT": "Planning",
    "POLICE": "Police",
    "FIRE": "Fire",
    "BUILDING": "Building",
    "DEPARTMENT OF PUBLIC WORKS": "Public Works",
    "RECREATION": "Recreation",
    "OFFICE OF DIVERSITY, INCLUSION & COMMUNITY RELATIONS": "DEICR",
    "HEALTH & HUMAN SERVICES": "Health",
    "VETERANS' SERVICES": "Veterans' Services",
    "COUNCIL ON AGING": "Council on Aging",
    "LIBRARY": "Library",
}

# --- Raw transcriptions, one row per plan, department: {year: fte}.
# Source pages as noted in the module docstring. Each dict's own total
# verified against that table's own stated ALL POSITIONS TOTAL / FTE
# COUNTS TOTAL row before use (see main()). ---

FY2025_PLAN = {  # data/FY2025-Financial-Plan.pdf, p.57. Cols: FY2021-FY2025.
    "Advisory Committee":  [0.40, 0.40, 0.40, 0.40, 0.40],
    "Finance Department":  [31.22, 31.22, 31.92, 31.92, 29.42],
    "Human Resources":     [6.78, 6.78, 6.78, 6.78, 6.78],
    "Information Technology": [12.40, 12.40, 12.00, 12.00, 13.00],
    "Legal Services":      [7.71, 7.71, 7.71, 7.71, 8.71],
    "Planning":            [18.00, 18.00, 19.00, 20.00, 19.00],
    "Select Board":        [7.00, 7.00, 8.50, 8.00, 10.00],
    "Town Clerk":          [5.50, 5.50, 5.50, 5.50, 5.50],
    "Library":             [52.84, 52.84, 54.12, 55.89, 59.22],
    "Council on Aging":    [17.40, 18.01, 18.01, 18.01, 18.71],
    "Health":              [21.59, 21.59, 20.06, 22.28, 24.28],
    "DEICR":               [3.72, 3.72, 3.72, 2.72, 2.72],
    "Veterans' Services":  [2.00, 2.00, 2.00, 2.00, 2.00],
    "Recreation":          [10.00, 10.00, 11.00, 11.00, 11.00],
    "Public Works":        [130.91, 131.91, 131.91, 134.91, 140.91],
    "Building":            [37.61, 38.61, 38.61, 38.61, 38.61],
    "Fire":                [161.00, 161.00, 161.00, 161.00, 161.00],
    "Police":              [179.80, 179.80, 179.80, 175.80, 175.30],
}
FY2025_PLAN_YEARS = [2021, 2022, 2023, 2024, 2025]
FY2025_PLAN_STATED_TOTAL = {2021: 705.88, 2022: 708.49, 2023: 712.04, 2024: 714.53, 2025: 726.56}

FY2026_PLAN = {  # data/FY2026-Financial-Plan.pdf, p.56. Cols: FY2022-FY2026.
    "Advisory Committee":  [0.40, 0.40, 0.40, 0.40, 0.40],
    "Finance Department":  [31.22, 31.92, 31.92, 29.42, 29.42],
    "Human Resources":     [6.78, 6.78, 6.78, 6.78, 7.78],
    "Information Technology": [12.40, 12.00, 12.00, 13.00, 13.00],
    "Legal Services":      [7.71, 7.71, 7.71, 8.71, 8.21],
    "Planning":            [18.00, 19.00, 20.00, 19.00, 19.00],
    "Select Board":        [7.00, 8.50, 8.00, 10.00, 10.00],
    "Town Clerk":          [5.50, 5.50, 5.50, 5.50, 5.50],
    "Building":            [38.61, 38.61, 38.61, 38.61, 38.61],
    "Fire":                [161.00, 161.00, 161.00, 161.00, 161.00],
    "Police":              [179.80, 179.80, 175.80, 173.30, 172.30],
    "Public Works":        [131.91, 131.91, 134.91, 139.91, 133.91],
    "Recreation":          [10.00, 11.00, 11.00, 11.00, 11.00],
    "Council on Aging":    [18.01, 18.01, 18.01, 18.71, 19.09],
    "Health":              [21.59, 20.06, 22.28, 24.28, 26.28],
    "DEICR":               [3.72, 3.72, 2.72, 3.72, 3.72],
    "Veterans' Services":  [2.00, 2.00, 2.00, 2.00, 2.00],
    "Library":             [52.84, 54.12, 55.89, 56.22, 56.22],
}
FY2026_PLAN_YEARS = [2022, 2023, 2024, 2025, 2026]
FY2026_PLAN_STATED_TOTAL = {2022: 708.49, 2023: 712.04, 2024: 714.53, 2025: 721.56, 2026: 717.44}

FY2027_PLAN = {  # data/FY2027-Financial-Plan.pdf, p.79. Cols: FY2023-FY2027.
    "Select Board":        [8.50, 8.00, 10.00, 10.00, 9.00],
    "Human Resources":     [6.78, 6.78, 6.78, 7.78, 6.78],
    "Information Technology": [12.00, 12.00, 13.00, 13.00, 13.00],
    "Finance Department":  [31.92, 31.92, 29.42, 29.42, 27.00],
    "Legal Services":      [7.71, 7.71, 8.71, 8.21, 8.21],
    "Advisory Committee":  [0.40, 0.40, 0.40, 0.40, 0.40],
    "Town Clerk":          [5.50, 5.50, 5.50, 5.50, 5.50],
    "Planning":            [19.00, 20.00, 19.00, 19.00, 16.00],
    "Police":              [179.80, 175.80, 173.30, 172.30, 171.10],
    "Fire":                [161.00, 161.00, 161.00, 161.00, 160.00],
    "Building":            [38.61, 38.61, 38.61, 38.61, 40.61],
    "Public Works":        [131.91, 134.91, 139.91, 133.91, 132.92],
    "Recreation":          [11.00, 11.00, 11.00, 11.00, 10.00],
    "DEICR":               [3.72, 2.72, 3.72, 3.72, 3.72],
    "Health":              [20.06, 22.28, 24.28, 26.28, 26.48],
    "Veterans' Services":  [2.00, 2.00, 2.00, 2.00, 2.00],
    "Council on Aging":    [18.01, 18.01, 18.71, 19.09, 19.09],
    "Library":             [54.12, 55.89, 56.22, 56.22, 55.66],
}
FY2027_PLAN_YEARS = [2023, 2024, 2025, 2026, 2027]
FY2027_PLAN_STATED_TOTAL = {2023: 712.04, 2024: 714.53, 2025: 721.56, 2026: 717.44, 2027: 707.47}

ALL_YEARS = list(range(2021, 2028))
DEPARTMENTS = list(FY2027_PLAN.keys())  # same 18 depts as department_fte_history.py


def verify_plan(plan_dict, years, stated_totals, label):
    for i, y in enumerate(years):
        computed = round(sum(plan_dict[d][i] for d in plan_dict), 2)
        stated = stated_totals[y]
        assert abs(computed - stated) < 0.02, \
            f"{label} FY{y}: computed {computed} != stated {stated}"
    print(f"  {label}: verified against its own stated total for all {len(years)} years.")


def main():
    verify_plan(FY2025_PLAN, FY2025_PLAN_YEARS, FY2025_PLAN_STATED_TOTAL, "FY2025 Plan")
    verify_plan(FY2026_PLAN, FY2026_PLAN_YEARS, FY2026_PLAN_STATED_TOTAL, "FY2026 Plan")
    verify_plan(FY2027_PLAN, FY2027_PLAN_YEARS, FY2027_PLAN_STATED_TOTAL, "FY2027 Plan")

    # Cross-validate every overlapping year/department across plans -
    # real, not assumed. Prints any mismatch found (expect: none except
    # the known, disclosed FY2025 discontinuity, which is skipped here
    # since we deliberately prefer the later plans' figure for FY2025).
    mismatches = []
    for dept in DEPARTMENTS:
        for y in ALL_YEARS:
            vals = {}
            if y in FY2025_PLAN_YEARS and y != 2025:  # FY2025's own current-yr figure excluded, see docstring
                vals["FY25 Plan"] = FY2025_PLAN[dept][FY2025_PLAN_YEARS.index(y)]
            if y in FY2026_PLAN_YEARS:
                vals["FY26 Plan"] = FY2026_PLAN[dept][FY2026_PLAN_YEARS.index(y)]
            if y in FY2027_PLAN_YEARS:
                vals["FY27 Plan"] = FY2027_PLAN[dept][FY2027_PLAN_YEARS.index(y)]
            if len(set(vals.values())) > 1:
                mismatches.append((dept, y, vals))
    if mismatches:
        print(f"  WARNING: {len(mismatches)} unexpected cross-plan mismatches found:")
        for dept, y, vals in mismatches:
            print(f"    {dept} FY{y}: {vals}")
    else:
        print("  Cross-validated: every department/year covered by 2+ plans agrees exactly "
              "(except FY2025's known, disclosed recommended-vs-settled discrepancy).")

    # Build the merged series: prefer the latest plan available for each
    # year (settled data beats an earlier plan's still-provisional
    # current-year figure - see module docstring's FY2025 finding).
    merged = {dept: {} for dept in DEPARTMENTS}
    fy25_as_recommended = {}
    for dept in DEPARTMENTS:
        for y in ALL_YEARS:
            if y in FY2027_PLAN_YEARS:
                merged[dept][y] = FY2027_PLAN[dept][FY2027_PLAN_YEARS.index(y)]
            elif y in FY2026_PLAN_YEARS:
                merged[dept][y] = FY2026_PLAN[dept][FY2026_PLAN_YEARS.index(y)]
            elif y in FY2025_PLAN_YEARS:
                merged[dept][y] = FY2025_PLAN[dept][FY2025_PLAN_YEARS.index(y)]
        fy25_as_recommended[dept] = FY2025_PLAN[dept][FY2025_PLAN_YEARS.index(2025)]

    rows = []
    for dept in DEPARTMENTS:
        row = dict(department=dept, category=CATEGORY_LABELS[DEPT_TO_CATEGORY[dept]])
        for y in ALL_YEARS:
            row[f"fy{y}"] = merged[dept][y]
        row["fy2025_as_recommended_fy25plan"] = fy25_as_recommended[dept]
        cagr = (merged[dept][2027] / merged[dept][2021]) ** (1 / 6) - 1 if merged[dept][2021] > 0 else ""
        row["fte_cagr_fy21_27"] = round(cagr, 4) if cagr != "" else ""
        rows.append(row)

    fieldnames = ["department", "category"] + [f"fy{y}" for y in ALL_YEARS] + \
                 ["fy2025_as_recommended_fy25plan", "fte_cagr_fy21_27"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT_CSV} ({len(rows)} departments x {len(ALL_YEARS)} years)")

    for y in ALL_YEARS:
        total = sum(merged[d][y] for d in DEPARTMENTS)
        print(f"  FY{y} total (All Positions): {total:.2f}")

    write_notes(rows)
    print(f"Wrote {NOTES_FILE}")


def write_notes(rows):
    lines = []
    lines.append("# Town Department Headcount, FY2021-FY2027 (Annual Series)\n")
    lines.append(
        "Source: `data/FY2025-Financial-Plan.pdf` p.57, `data/FY2026-Financial-Plan.pdf` p.56, "
        "`data/FY2027-Financial-Plan.pdf` p.79-80 - each plan's own \"Full-Time Equivalent Positions "
        "Funded\" table (All Positions: General Fund + Capital/Special Appropriations + Grants + "
        "Enterprise/Revolving combined). Added 2026-09-02 (Ben: \"yes please check the financial plan "
        "pdfs to see if they contain more department detail\") - a real annual FY2021-2027 series, not "
        "just the FY2019/FY2026 two-point comparison in `department_fte_history.py`.\n"
    )
    lines.append(
        "**Cross-validated, not assumed**: every department/year covered by more than one plan was "
        "checked directly. Full agreement for FY2021-2024. One real, traceable discrepancy for FY2025 "
        "(the FY2025 Plan's own recommended-year figure, 726.56 total, vs. 721.56 in the two later plans' "
        "settled figures - a real -5.00 FTE difference, traced to exactly 4 departments: Library, Public "
        "Works, Police, and ODEICR) - this file uses the later, settled figures; the FY2025 Plan's original "
        "recommended figures are kept in `fy2025_as_recommended_fy25plan` for comparison.\n"
    )
    lines.append("## Annual FTE by department (All Positions)\n")
    lines.append("| Department | " + " | ".join(f"FY{y}" for y in ALL_YEARS) + " | CAGR FY21-27 |")
    lines.append("|---|" + "---:|" * (len(ALL_YEARS) + 1))
    for r in rows:
        vals = " | ".join(f"{r[f'fy{y}']:.2f}" for y in ALL_YEARS)
        cagr = f"{r['fte_cagr_fy21_27']:+.2%}" if r["fte_cagr_fy21_27"] != "" else "n/a"
        lines.append(f"| {r['department']} | {vals} | {cagr} |")
    lines.append("")
    lines.append(
        "## What this deliberately does not do\n\n"
        "- **FY2027 is the Town's own recommended budget, not yet an audited actual** - same caveat as "
        "every other \"Town's own published\" figure elsewhere in this project.\n"
        "- **Doesn't reach back before FY2021** - `department_fte_history.py`'s ERSC-sourced FY2019 point "
        "is the only source in this project reaching that far back; the two datasets aren't directly "
        "merged since ERSC's FY2019/FY2026 salary figures and this file's annual FTE-only figures come "
        "from different sources with different exact scopes.\n"
    )
    with open(NOTES_FILE, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
