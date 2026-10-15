"""
Pulls a real year-by-year history of Brookline Public Schools enrollment,
staffing, and selected-population demographics, FY2005-2025, directly from
DESE's own School and District Profiles site (profiles.doe.mass.edu) -
each fiscal year has a stable URL via the `fycode` query parameter, so
this is a straight per-year scrape, not an API.

Added 2026-09-02 (Ben: "did you find number of employees... just those
few snapshots?", then "do we have total schools employee count... what
other useful information can we pull?"). First version only had teacher
FTE (DESE's teacher.aspx), which the ERSC report's own Table 5 shows is a
small fraction of true total district staff (1,378.4 FTE district-wide in
FY19-20, vs. teacher.aspx's 645.8 for the same year). Found the report
ERSC's own footnote actually cited (`...&leftNavId=817`) - "Staffing Data
by Race, Ethnicity, Gender by FTE" - independently confirmed its "FTE
Count" row is the real total-district-staff figure: it matches ERSC's
Table 5 FY24-25 entry (1,249.4) exactly.

Five DESE reports, one row per fiscal year:
  - Total enrollment: profiles/student.aspx ("Enrollment by Gender"
    table's Total row). FY2005+.
  - Teacher FTE only: profiles/teacher.aspx ("Total # of Teachers (FTE)"
    row). FY2005+. NOT total staff - see total_staff_fte instead for that.
  - Total staff FTE (all district employees - teachers, paraprofessionals,
    specialists, support staff): profiles/teacher.aspx?...&leftNavId=817
    ("FTE Count" row on the race/ethnicity/gender staffing table). Only
    available FY2008+ ("No Data Reported" for FY2005-2007 - confirmed
    directly, not a scrape failure).
  - Selected Populations (4 metrics in one fetch): profiles/student.aspx
    ?...&leftNavId=305 - Students with Disabilities %, English Learners %,
    Low Income %, First Language Not English % of total enrollment.
    FY2005+. NOTE: "Students with Disabilities %" here is DESE's own
    Selected-Populations definition, NOT the same figure/methodology as
    the Indicator 5 "enrolled students with IEPs" count below - the two
    series disagree somewhat (e.g. FY2005: 18.4% here vs. no Indicator-5
    data that year at all; the two are cross-referenced, not reconciled,
    in the output - see the methodology note in output columns).
  - Students with IEPs (raw count, Indicator 5): gis/sped_map.aspx
    ("Enrolled students with IEPs" row). FY2007+ (not FY2005-2006).

Outputs:
  output/school_enrollment_staffing_fy05_25.csv
"""
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_CSV = ROOT / "output" / "school_enrollment_staffing_fy05_25.csv"

ORGCODE = "00460000"
YEARS = list(range(2005, 2026))


def fetch(url):
    # urllib's default SSL context can't find this machine's CA bundle
    # (a common Python.org-install quirk on macOS) - curl already has it.
    result = subprocess.run(
        ["curl", "-s", "--max-time", "20", "-A", "Mozilla/5.0 (research script, brookline-finances project)", url],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def norm(html):
    """Collapse whitespace/newlines so regexes don't have to guess formatting."""
    return re.sub(r"\s+", " ", html)


def parse_enrollment(html):
    m = re.search(r"Total</td>\s*<td class='center middle'[^>]*>\s*([\d,]+)\s*</td>", norm(html))
    return int(m.group(1).replace(",", "")) if m else None


def parse_teacher_fte(html):
    m = re.search(r"Total # of Teachers \(FTE\)</td>\s*<td class='center'[^>]*>\s*([\d,\.]+)\s*</td>", norm(html))
    return float(m.group(1).replace(",", "")) if m else None


def parse_total_staff_fte(html):
    m = re.search(r"FTE Count</td>\s*<td class='right'[^>]*>\s*([\d,\.]+)\s*</td>", norm(html))
    return float(m.group(1).replace(",", "")) if m else None


def parse_iep_count(html):
    m = re.search(r"Enrolled students with IEPs</td>\s*<td class='nav center middle'>\s*(\d+)\s*</td>", norm(html))
    return int(m.group(1)) if m else None


def parse_selected_populations(html):
    n = norm(html)
    out = {}
    for key, label in [
        ("swd_pct", "Students with Disabilities"),
        ("el_pct", "English Learners"),
        ("low_income_pct", "Low Income"),
        ("not_english_first_lang_pct", "First Language Not English"),
    ]:
        m = re.search(re.escape(label) + r"</td>\s*<td class='center middle'[^>]*>\s*([\d\.]+)", n)
        out[key] = float(m.group(1)) if m else None
    return out


def main():
    rows = []
    for y in YEARS:
        enrollment = teacher_fte = total_staff_fte = iep_count = None
        selpop = {}
        try:
            enrollment = parse_enrollment(fetch(
                f"https://profiles.doe.mass.edu/profiles/student.aspx?orgcode={ORGCODE}&orgtypecode=5&fycode={y}"))
        except Exception as e:
            print(f"FY{y} enrollment fetch failed: {e}")
        time.sleep(0.4)
        try:
            teacher_fte = parse_teacher_fte(fetch(
                f"https://profiles.doe.mass.edu/profiles/teacher.aspx?orgcode={ORGCODE}&orgtypecode=5&fycode={y}"))
        except Exception as e:
            print(f"FY{y} teacher FTE fetch failed: {e}")
        time.sleep(0.4)
        try:
            total_staff_fte = parse_total_staff_fte(fetch(
                f"https://profiles.doe.mass.edu/profiles/teacher.aspx?orgcode={ORGCODE}&orgtypecode=5&fycode={y}&leftNavId=817"))
        except Exception as e:
            print(f"FY{y} total staff FTE fetch failed: {e}")
        time.sleep(0.4)
        try:
            iep_count = parse_iep_count(fetch(
                f"https://profiles.doe.mass.edu/gis/sped_map.aspx?fycode={y}&orgcode={ORGCODE}"))
        except Exception as e:
            print(f"FY{y} IEP count fetch failed: {e}")
        time.sleep(0.4)
        try:
            selpop = parse_selected_populations(fetch(
                f"https://profiles.doe.mass.edu/profiles/student.aspx?orgcode={ORGCODE}&orgtypecode=5&fycode={y}&leftNavId=305"))
        except Exception as e:
            print(f"FY{y} selected populations fetch failed: {e}")
        time.sleep(0.4)

        iep_pct = round(100 * iep_count / enrollment, 2) if (iep_count and enrollment) else None
        students_per_teacher = round(enrollment / teacher_fte, 2) if (enrollment and teacher_fte) else None
        students_per_total_staff = round(enrollment / total_staff_fte, 2) if (enrollment and total_staff_fte) else None
        print(f"FY{y}: enrollment={enrollment} teacher_fte={teacher_fte} total_staff_fte={total_staff_fte} "
              f"iep_count={iep_count} swd_pct={selpop.get('swd_pct')} el_pct={selpop.get('el_pct')} "
              f"low_income_pct={selpop.get('low_income_pct')}")
        rows.append((y, enrollment, teacher_fte, total_staff_fte, students_per_teacher, students_per_total_staff,
                     iep_count, iep_pct, selpop.get("swd_pct"), selpop.get("el_pct"),
                     selpop.get("low_income_pct"), selpop.get("not_english_first_lang_pct")))

    OUT_CSV.parent.mkdir(exist_ok=True)
    cols = ["fiscal_year", "total_enrollment", "teacher_fte", "total_staff_fte",
            "students_per_teacher_fte", "students_per_total_staff_fte",
            "students_with_ieps_indicator5", "iep_pct_of_enrollment_indicator5",
            "students_with_disabilities_pct_selectedpop", "english_learners_pct",
            "low_income_pct", "first_language_not_english_pct"]
    with open(OUT_CSV, "w") as f:
        f.write(",".join(cols) + "\n")
        for row in rows:
            f.write(",".join("" if v is None else str(v) for v in row) + "\n")
    print(f"\nWrote {OUT_CSV}")


if __name__ == "__main__":
    main()
