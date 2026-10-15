"""
Town department headcount and salary budgets, FY2019 vs FY2026 - captured
as its own first-class dataset, not left buried inside
departmental_category_forecast.py's category-level rollup.

Added 2026-09-02 (Ben, after the FTE/wage diagnosis answered his "are
these departments actually shrinking?" question: "let's make sure to
capture the employees by department data and likely include it in any
published work we do"). This is real, department-level detail (18 Town
departments, not just Schedule A's 5 functional categories) - genuinely
useful for public-facing work independent of the forecast itself, so it
gets its own output rather than staying a private intermediate inside one
script's diagnosis section.

Source: `data/ERSC Final Report FINAL 031326.pdf`, p.106, "Town Personnel
Budgets and Full-Time Equivalents from FY2019 to FY2026" - the ERSC
report's own transcription of Town budget-book figures. Manually
transcribed here (verified: department rows sum to the table's own
stated TOTAL row, $53,218,117/$66,317,226 salary and 699.60/718.44 total
FTEs - both match exactly).

Columns captured: Salary Budget (FY19, FY26), General Fund Budget FTEs,
Soft Money FTEs, and Total FTEs (= General Fund + Soft Money), each for
FY19 and FY26. `category` maps each department onto Schedule A's 5
functional categories (General Government, Public Safety, Public Works,
Human Services, Culture & Recreation) so this rolls up cleanly into
departmental_category_forecast.py's FTE/wage diagnosis - that script
imports `category_rollup()` from here rather than keeping its own
duplicate hardcoded totals.

Outputs:
  ../output/department_fte_salary_fy19_fy26.csv (18 departments)
  ../output/department_fte_salary_by_category_fy19_fy26.csv (5-category rollup)
  ../output/department_fte_salary_fy19_fy26_notes.md
"""
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_DEPT_CSV = ROOT / "output/department_fte_salary_fy19_fy26.csv"
OUT_CAT_CSV = ROOT / "output/department_fte_salary_by_category_fy19_fy26.csv"
NOTES_FILE = ROOT / "output/department_fte_salary_fy19_fy26_notes.md"

# department: (category, salary19, salary26, genfund_fte19, genfund_fte26,
#              softmoney_fte19, softmoney_fte26, footnote)
DEPARTMENTS = [
    ("Select Board", "general_government", 687_929, 966_951, 6.48, 7.50, 0.00, 2.50,
     "Added communications officer (moved from DEICR); one grant-funded position "
     "eliminated in FY26 so actual total is 9 FTEs, not 10.00 as tabulated."),
    ("Human Resources", "general_government", 309_024, 463_096, 3.53, 4.48, 2.25, 3.30,
     "Generalist/investigator position, FY24 override."),
    ("Information Technology", "general_government", 1_156_208, 1_530_186, 12.40, 13.00, 0.00, 0.00, ""),
    ("DEICR", "general_government", 218_753, 352_466, 2.72, 3.72, 0.00, 0.00,
     "Language access coordinator, FY24 override."),
    ("Finance Department", "general_government", 2_318_263, 2_610_351, 31.22, 29.42, 0.00, 0.00,
     "Assessing reorganization to meet FY25 budget deficit."),
    ("Legal Services", "general_government", 694_633, 909_253, 7.03, 8.21, 0.00, 0.00,
     "Labor counsel added FY20."),
    ("Advisory Committee", "general_government", 23_201, 27_312, 0.40, 0.40, 0.00, 0.00, ""),
    ("Town Clerk", "general_government", 651_815, 568_372, 5.50, 5.50, 0.00, 0.00, ""),
    ("Planning", "general_government", 1_078_652, 1_351_660, 13.39, 13.56, 5.10, 5.44, ""),
    ("Police", "public_safety", 15_078_231, 19_502_670, 179.80, 171.30, 1.00, 2.00,
     "Held open 6 officers and eliminated park security officers; budget book "
     "incorrectly shows a reduction of one FTE in FY2026 (corrected in the ERSC "
     "report's own table, used here)."),
    ("Fire", "public_safety", 14_504_987, 18_414_756, 160.00, 161.00, 0.00, 0.00, ""),
    ("Building", "general_government", 2_550_206, 3_159_486, 34.61, 35.76, 2.00, 2.85,
     "Building inspector, short-term rentals, added FY20."),
    ("Public Works", "public_works", 8_152_083, 9_505_745, 126.72, 125.16, 3.66, 8.75,
     "Sanitation reduction; FTEs added and moved to soft funds."),
    ("Library", "culture_recreation", 3_056_639, 3_510_670, 52.84, 56.22, 0.00, 0.00, ""),
    ("Health", "human_services", 941_807, 1_197_408, 12.26, 13.01, 5.78, 13.27, ""),
    ("Veterans' Services", "human_services", 171_571, 168_201, 2.00, 2.00, 0.00, 0.00, ""),
    ("Council on Aging", "human_services", 822_520, 1_134_534, 13.74, 15.39, 3.17, 3.70,
     "Social worker and transportation coordinator, FY24 override."),
    ("Recreation", "culture_recreation", 801_595, 944_109, 12.00, 11.00, 0.00, 0.00, ""),
]

CATEGORY_LABELS = {
    "general_government": "General Government",
    "public_safety": "Public Safety",
    "public_works": "Public Works",
    "human_services": "Human Services",
    "culture_recreation": "Culture & Recreation",
}


def cagr(start, end, years):
    return (end / start) ** (1 / years) - 1


def category_rollup():
    """Used by departmental_category_forecast.py's FTE/wage diagnosis -
    single source of truth for the FY19-vs-FY26 department table."""
    out = {k: dict(fte19=0.0, fte26=0.0, salary19=0.0, salary26=0.0) for k in CATEGORY_LABELS}
    for name, cat, s19, s26, gf19, gf26, sm19, sm26, note in DEPARTMENTS:
        out[cat]["fte19"] += gf19 + sm19
        out[cat]["fte26"] += gf26 + sm26
        out[cat]["salary19"] += s19
        out[cat]["salary26"] += s26
    return out


def main():
    dept_rows = []
    for name, cat, s19, s26, gf19, gf26, sm19, sm26, note in DEPARTMENTS:
        total19, total26 = gf19 + sm19, gf26 + sm26
        dept_rows.append(dict(
            department=name, category=CATEGORY_LABELS[cat],
            salary_budget_fy19=s19, salary_budget_fy26=s26,
            salary_cagr_7yr=round(cagr(s19, s26, 7), 4),
            general_fund_fte_fy19=gf19, general_fund_fte_fy26=gf26,
            soft_money_fte_fy19=sm19, soft_money_fte_fy26=sm26,
            total_fte_fy19=total19, total_fte_fy26=total26,
            total_fte_cagr_7yr=round(cagr(total19, total26, 7), 4) if total19 > 0 else "",
            cost_per_fte_fy19=round(s19 / total19) if total19 > 0 else "",
            cost_per_fte_fy26=round(s26 / total26) if total26 > 0 else "",
            note=note,
        ))

    with open(OUT_DEPT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(dept_rows[0].keys()))
        w.writeheader()
        w.writerows(dept_rows)
    print(f"Wrote {OUT_DEPT_CSV} ({len(dept_rows)} departments)")

    # Verify against the source table's own stated TOTAL row.
    total_s19 = sum(r["salary_budget_fy19"] for r in dept_rows)
    total_s26 = sum(r["salary_budget_fy26"] for r in dept_rows)
    total_fte19 = sum(r["total_fte_fy19"] for r in dept_rows)
    total_fte26 = sum(r["total_fte_fy26"] for r in dept_rows)
    print(f"  Check vs. source TOTAL row: salary ${total_s19:,.0f}/{total_s26:,.0f} "
          f"(source: $53,218,117/$66,317,226), FTE {total_fte19:.2f}/{total_fte26:.2f} "
          f"(source: 699.60/718.44)")
    assert abs(total_s19 - 53_218_117) < 1 and abs(total_s26 - 66_317_226) < 1
    assert abs(total_fte19 - 699.60) < 0.01 and abs(total_fte26 - 718.44) < 0.01
    print("  Verified: department rows sum exactly to the source table's own TOTAL row.")

    rollup = category_rollup()
    cat_rows = []
    for cat, d in rollup.items():
        cat_rows.append(dict(
            category=CATEGORY_LABELS[cat],
            salary_budget_fy19=round(d["salary19"]), salary_budget_fy26=round(d["salary26"]),
            salary_cagr_7yr=round(cagr(d["salary19"], d["salary26"], 7), 4),
            total_fte_fy19=round(d["fte19"], 2), total_fte_fy26=round(d["fte26"], 2),
            total_fte_cagr_7yr=round(cagr(d["fte19"], d["fte26"], 7), 4),
            cost_per_fte_fy19=round(d["salary19"] / d["fte19"]),
            cost_per_fte_fy26=round(d["salary26"] / d["fte26"]),
            cost_per_fte_cagr_7yr=round(cagr(d["salary19"] / d["fte19"], d["salary26"] / d["fte26"], 7), 4),
        ))
    with open(OUT_CAT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cat_rows[0].keys()))
        w.writeheader()
        w.writerows(cat_rows)
    print(f"Wrote {OUT_CAT_CSV} ({len(cat_rows)} categories)")

    write_notes(dept_rows, cat_rows)
    print(f"Wrote {NOTES_FILE}")


def write_notes(dept_rows, cat_rows):
    lines = []
    lines.append("# Town Department Headcount & Salary Budgets, FY2019 vs FY2026\n")
    lines.append(
        "Source: `data/ERSC Final Report FINAL 031326.pdf`, p.106, \"Town Personnel Budgets and "
        "Full-Time Equivalents from FY2019 to FY2026.\" Captured as a standalone dataset "
        "2026-09-02 (Ben: \"let's make sure to capture the employees by department data and "
        "likely include it in any published work we do\") - originally pulled only to diagnose "
        "`departmental_category_forecast.py`'s trailing-CAGR forecast (is it masking service "
        "cuts?), real enough on its own to keep and reuse.\n"
    )
    lines.append(
        "**Verified**: all 18 department rows sum exactly to the source table's own stated TOTAL "
        "row ($53,218,117 → $66,317,226 salary; 699.60 → 718.44 total FTEs) - the same "
        "sum-to-stated-subtotal check used throughout this project to catch transcription errors "
        "before trusting a table.\n"
    )
    lines.append("## By department\n")
    lines.append("| Department | Category | Total FTE FY19→FY26 | FTE CAGR | Salary CAGR | $/FTE FY19→FY26 |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for r in dept_rows:
        fte_cagr = f"{r['total_fte_cagr_7yr']:+.2%}" if r["total_fte_cagr_7yr"] != "" else "n/a"
        cpf = f"${r['cost_per_fte_fy19']:,} → ${r['cost_per_fte_fy26']:,}" if r["cost_per_fte_fy19"] != "" else "n/a"
        lines.append(f"| {r['department']} | {r['category']} | {r['total_fte_fy19']:.2f} → "
                      f"{r['total_fte_fy26']:.2f} | {fte_cagr} | {r['salary_cagr_7yr']:+.2%} | {cpf} |")
    lines.append("")
    lines.append("## By Schedule A category (rollup used in the departmental forecast diagnosis)\n")
    lines.append("| Category | Total FTE FY19→FY26 | FTE CAGR | $/FTE FY19→FY26 | $/FTE CAGR |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in cat_rows:
        lines.append(f"| {r['category']} | {r['total_fte_fy19']:.2f} → {r['total_fte_fy26']:.2f} | "
                      f"{r['total_fte_cagr_7yr']:+.2%} | ${r['cost_per_fte_fy19']:,} → "
                      f"${r['cost_per_fte_fy26']:,} | {r['cost_per_fte_cagr_7yr']:+.2%} |")
    lines.append("")
    lines.append("## Per-department footnotes (from the ERSC report's own table)\n")
    for r in dept_rows:
        if r["note"]:
            lines.append(f"- **{r['department']}**: {r['note']}")
    lines.append("")
    lines.append(
        "## What this deliberately does not do\n\n"
        "- **No years between FY2019 and FY2026** - the source table is a two-point comparison, "
        "not an annual series. If a fuller annual FTE history is needed for publication, that "
        "would require a new research effort (Town budget books year-by-year), not yet done.\n"
        "- **\"Total FTE\" combines General Fund-budgeted and soft-money (grant/other-fund) "
        "positions** - a real distinction (soft-money FTEs aren't necessarily durable/tax-levy-"
        "funded) the source table itself preserves as separate columns (both kept here), but this "
        "dataset doesn't take a further stance on which soft-money positions are likely to "
        "persist.\n"
    )
    with open(NOTES_FILE, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
