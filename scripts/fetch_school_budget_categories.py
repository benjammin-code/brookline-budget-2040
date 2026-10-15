"""
Pulls Brookline Public Schools' per-pupil spending broken down by
function/category, average teacher salary, and staff-by-role counts,
FY2009-2025, from the Massachusetts Education-to-Career Research and Data
Hub's "District Expenditures by Spending Category" dataset - a proper
Socrata open-data API (educationtocareer.data.mass.gov, dataset
er3w-dyti), not a page scrape. Added 2026-09-02 (Ben: "please also try to
find a high level breakdown of the budget between categories... would be
nice to disaggregate that large spend into smaller pieces").

This is DESE's own End-of-Year Financial Report categorization - the
same "function" categories used statewide, so these are directly
comparable to peer districts if that's ever wanted. Per-pupil $ amounts
sum to "Total In-District Expenditures" (confirmed: FY2025 category sum
$27,587 vs. reported $27,589, a $2 rounding gap) - "Total Expenditures"
(the larger figure) additionally includes out-of-district placements,
which is its own separately-tracked category, not broken out further
here (matches the ERSC report's flag that out-of-district special-ed
placements are a real, distinct cost driver).

Three outputs, one row per fiscal year:
  output/school_spending_by_category_fy09_25.csv
    Per-pupil $ for: Administration, Guidance/Counseling/Testing,
    Instructional Leadership, Instructional Materials/Equipment/Tech,
    Insurance/Retirement/Other (= benefits), Operations & Maintenance,
    Other Teaching Services, Professional Development, Pupil Services,
    Teachers, plus Total In-District and Total (incl. out-of-district).
  output/school_teacher_salary_fy09_25.csv
    Average teacher salary, teacher FTE, teachers per 100 FTE students.
  output/school_staff_by_role_fy09_25.csv
    Paraprofessional FTE, Special Education Instructional Support FTE,
    Instructional Coach FTE, Instructional Support FTE.
"""
import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "output"
DIST_CODE = "00460000"
API = f"https://educationtocareer.data.mass.gov/resource/er3w-dyti.json?dist_code={DIST_CODE}&$limit=5000"


def fetch_json(url):
    result = subprocess.run(
        ["curl", "-s", "--max-time", "30", "-A", "Mozilla/5.0 (research script, brookline-finances project)", url],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def pivot_and_write(records, category, subcat_order, out_path, id_col_name="fiscal_year"):
    by_year = defaultdict(dict)
    for r in records:
        if r["ind_cat"] == category:
            by_year[r["sy"]][r["ind_subcat"]] = r["ind_value"]
    years = sorted(by_year, key=int)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([id_col_name] + subcat_order)
        for y in years:
            w.writerow([y] + [by_year[y].get(sc, "") for sc in subcat_order])
    print(f"Wrote {out_path} ({len(years)} years)")


def main():
    print(f"Fetching {API}")
    data = fetch_json(API)
    print(f"{len(data)} rows for district {DIST_CODE}")

    pivot_and_write(
        data, "Expenditures Per Pupil",
        ["Administration", "Guidance, Counseling and Testing", "Instructional Leadership",
         "Instructional Materials, Equipment and Technology", "Insurance, Retirement Programs and Other",
         "Operations and Maintenance", "Other Teaching Services", "Professional Development",
         "Pupil Services", "Teachers", "Total In-District Expenditures", "Total Expenditures"],
        OUT_DIR / "school_spending_by_category_fy09_25.csv",
    )
    pivot_and_write(
        data, "Teacher Salaries",
        ["Average Teacher Salary", "Teacher FTE", "Teachers per 100 FTE students"],
        OUT_DIR / "school_teacher_salary_fy09_25.csv",
    )
    pivot_and_write(
        data, "Other Staff",
        ["Paraprofessional FTE", "Special Education Instructional Support FTE",
         "Instructional Coach FTE", "Instructional Support FTE"],
        OUT_DIR / "school_staff_by_role_fy09_25.csv",
    )


if __name__ == "__main__":
    main()
