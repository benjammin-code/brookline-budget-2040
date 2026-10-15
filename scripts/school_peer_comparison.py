"""
Brookline Public Schools vs. peer Massachusetts districts: staffing, student
needs, and spending, SY2014-15 (sy=2015) vs. SY2024-25 (sy=2025), plus
SY2025-26 (sy=2026) where DESE has published it (enrollment and staffing only).

Added 2026-09-29. Question: is Brookline's staffing (about 5.6 students per
total staff FTE and 12.9 per teacher FTE in FY2025) high given its needs?

All inputs are DESE data pulled from the Education-to-Career (E2C) Research
and Data Hub (Socrata, educationtocareer.data.mass.gov), saved as raw CSVs in
data/dese_peers/, plus one DESE Profiles state report (FY2015 average teacher
salary, which the E2C finance dataset does not carry before FY2024 for most
districts). `--fetch` re-downloads the E2C files; default reads the saved raw
files.

"sy" in every E2C dataset is the spring year of the school year (sy=2025 is
SY2024-25 / FY2025). Verified: Brookline sy=2025 enrollment 7,023, teacher
FTE 544.1, total staff FTE 1,249.4 all match the project's existing
school_enrollment_staffing_fy05_25.csv (scraped from Profiles).

Outputs:
  output/school_peer_comparison.csv
"""
import subprocess
import sys
import urllib.parse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "dese_peers"
OUT = ROOT / "output" / "school_peer_comparison.csv"

# org_code -> (name, grade span, note). Codes confirmed from the E2C
# enrollment dataset's own org_code/org_name pairs (org_type = District).
DISTRICTS = {
    "00460000": ("Brookline", "PK-12", ""),
    "02070000": ("Newton", "PK-12", ""),
    "01550000": ("Lexington", "PK-12", ""),
    "03170000": ("Wellesley", "PK-12", ""),
    "01990000": ("Needham", "PK-12", ""),
    "00490000": ("Cambridge", "PK-12", ""),
    "00100000": ("Arlington", "PK-12", ""),
    "00260000": ("Belmont", "PK-12", ""),
    "03440000": ("Winchester", "PK-12", ""),
    "00670000": ("Concord", "PK-8", "Concord town district is PK-8; high school is Concord-Carlisle regional"),
    "06400000": ("Concord-Carlisle", "9-12", "Regional high school for Concord and Carlisle"),
    "03150000": ("Wayland", "PK-12", ""),
    "03300000": ("Weston", "PK-12", ""),
    "02740000": ("Somerville", "PK-12", ""),
    "03140000": ("Watertown", "PK-12", ""),
    "01890000": ("Milton", "PK-12", ""),
    "01980000": ("Natick", "PK-12", ""),
    "02880000": ("Sudbury", "PK-8", "Sudbury town district is PK-8; high school is Lincoln-Sudbury regional"),
    "06950000": ("Lincoln-Sudbury", "9-12", "Regional high school for Lincoln and Sudbury"),
    "00090000": ("Andover", "PK-12", ""),
    "01310000": ("Hingham", "PK-12", ""),
    "03350000": ("Westwood", "PK-12", ""),
}
YEARS = ["2015", "2025", "2026"]
BASE = "https://educationtocareer.data.mass.gov/resource"


def fetch():
    codes = ",".join(f"'{c}'" for c in DISTRICTS)
    yrs = ",".join(f"'{y}'" for y in YEARS)
    jobs = {
        "enrollment_selectedpops_t8td-gens.csv": ("t8td-gens", f"org_code in({codes}) AND sy in({yrs})"),
        "staffing_by_jobclass_j5ue-xkfn.csv": ("j5ue-xkfn", f"org_code in({codes}) AND sy in({yrs})"),
        "teacher_data_4684-cw3t.csv": ("4684-cw3t", f"org_code in({codes}) AND sy in({yrs})"),
        "district_expenditures_er3w-dyti.csv": ("er3w-dyti", f"dist_code in({codes}) AND sy in('2015','2024','2025')"),
        "district_exp_by_function_cnfs-edqq.csv": ("cnfs-edqq", f"dist_code in({codes}) AND sy in('2015','2025')"),
        "sped_program_characteristics_n62c-bx65.csv": ("n62c-bx65", f"dist_code in({codes})"),
    }
    for fn, (ds, where) in jobs.items():
        url = f"{BASE}/{ds}.csv?$where={urllib.parse.quote(where)}&$limit=50000"
        data = subprocess.run(["curl", "-s", "--max-time", "120", url], capture_output=True).stdout
        (RAW / fn).write_bytes(data)
        print("fetched", fn, len(data))


def num(s):
    return pd.to_numeric(s.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")


def build():
    rd = lambda fn: pd.read_csv(RAW / fn, dtype=str)

    # --- Enrollment and selected populations (Oct 1 headcount, incl. PK and SP)
    en = rd("enrollment_selectedpops_t8td-gens.csv")
    en = en[en.org_type == "District"]
    e = pd.DataFrame({
        "org_code": en.org_code, "sy": en.sy,
        "total_enrollment": num(en.total_cnt),
        "swd_pct": num(en.swd_pct) * 100,
        "high_needs_pct": num(en.hn_pct) * 100,
        "el_pct": num(en.el_pct) * 100,
        # Low Income (pre-2015 and 2022+) and Economically Disadvantaged
        # (2015-2021) are different measures; keep the one DESE published.
        "low_income_or_ecd_pct": np.where(en.li_pct.notna(), num(en.li_pct) * 100, num(en.ecd_pct) * 100),
        "low_income_measure": np.where(en.li_pct.notna(), "Low Income (2022+ definition)",
                                        np.where(en.ecd_pct.notna(), "Economically Disadvantaged (2015-2021 measure)", "")),
    })

    # --- Staffing by job classification (Oct 1, all EPIMS-reported staff)
    st = rd("staffing_by_jobclass_j5ue-xkfn.csv")
    st["fte"] = num(st.fte_total)
    g = lambda mask: st[mask].groupby(["org_code", "sy"]).fte.sum()
    s = pd.DataFrame({
        "total_staff_fte": g(st.jobclass == "All"),
        "instructional_staff_fte": g(st.jobclass_cat == "Instructional Staff"),
        "paraprofessional_fte": g(st.jobclass_cat == "Paraprofessional"),
        "administrator_fte": g(st.jobclass_cat == "Administrators"),
        "sped_related_staff_fte": g(st.jobclass_cat == "Special Education Related Staff"),
        "teacher_support_content_fte": g(st.jobclass == "Teacher - support content instruction"),
    }).reset_index()
    # Classification-sensitivity check: Teacher + Co-teacher + support content
    s_chk = g(st.jobclass.isin(["Teacher", "Co-teacher", "Teacher - support content instruction"])).rename("teacher_fte_from_jobclass").reset_index()

    # --- Teacher FTE ("All Teachers" row of the Teacher Data report)
    td = rd("teacher_data_4684-cw3t.csv")
    td = td[(td.subject == "All Teachers") & (td.org_type == "District")]
    t = pd.DataFrame({"org_code": td.org_code, "sy": td.sy, "teacher_fte": num(td.tchr_cnt),
                      "dese_students_per_teacher": num(td.stu_tchr_ratio.str.replace(" to 1", ""))})

    # --- Finance (FY; sy=2025 is FY2025)
    fx = rd("district_expenditures_er3w-dyti.csv")
    fx["v"] = num(fx.ind_value)
    fp = fx.pivot_table(index=["dist_code", "sy"], columns="ind_subcat", values="v", aggfunc="first").reset_index()
    f = pd.DataFrame({
        "org_code": fp.dist_code, "sy": fp.sy,
        "in_district_ppx": fp["Total In-District Expenditures"],
        "total_ppx": fp["Total Expenditures"],
        "avg_teacher_salary": fp["Average Teacher Salary"],
        "in_district_fte_pupils": fp["In-District FTE Pupils"],
        "out_of_district_fte_pupils": fp["Out-of-District FTE Pupils"],
        "total_fte_pupils": fp["Total FTE Pupils"],
    })
    f["out_of_district_pupil_pct"] = f.out_of_district_fte_pupils / f.total_fte_pupils * 100
    f["avg_teacher_salary_source"] = np.where(f.avg_teacher_salary.notna(), "E2C er3w-dyti", "")

    fc = rd("district_exp_by_function_cnfs-edqq.csv")
    fc["x"] = num(fc.tot_exp)
    fcp = fc[fc.func_code.isin(["TTPP", "IIII", "OODD", "9300", "9400", "9200", "9100"])].pivot_table(
        index=["dist_code", "sy"], columns="func_code", values="x", aggfunc="sum").reset_index()
    fcp = fcp.rename(columns={"dist_code": "org_code"})
    fcp["total_expenditure_dollars"] = fcp.TTPP
    fcp["out_of_district_tuition_dollars"] = fcp.OODD
    fcp["out_of_district_tuition_pct_of_total_exp"] = fcp.OODD / fcp.TTPP * 100
    fcp["private_and_collab_tuition_dollars"] = fcp[["9300", "9400", "9200"]].sum(axis=1, min_count=1)
    fcp = fcp[["org_code", "sy", "total_expenditure_dollars", "out_of_district_tuition_dollars",
               "out_of_district_tuition_pct_of_total_exp", "private_and_collab_tuition_dollars"]]

    # FY2015 average teacher salary from Profiles state report (E2C lacks it)
    ts = pd.read_csv(RAW / "teacher_salaries_fy2015_profiles_statereport.csv", dtype=str)
    ts = pd.DataFrame({"org_code": ts.org_code, "sy": "2015", "avg_teacher_salary_fy15": num(ts.average_salary)})

    # --- SPED placement (RADAR): % of SWD placed out of district (2020+)
    sp = rd("sped_program_characteristics_n62c-bx65.csv")
    ood = sp[(sp.ind_cat == "In District/Out of District") & (sp.ind_desc == "Out-of-District")]
    ood = pd.DataFrame({"org_code": ood.dist_code, "sy": ood.sy, "swd_out_of_district_pct": num(ood.ind_pct) * 100,
                        "swd_out_of_district_count": num(ood.ind_cnt)})
    fte100 = sp[(sp.ind_cat == "Special Education FTEs per 100 SWDs") & (sp.ind_desc == "Total Special Education FTEs")]
    fte100 = pd.DataFrame({"org_code": fte100.dist_code, "sy": fte100.sy,
                           "sped_fte_per_100_in_district_swd": num(fte100.ind_pct) * 100})

    df = e
    for other in [s, s_chk, t, f, fcp, ts, ood, fte100]:
        df = df.merge(other, on=["org_code", "sy"], how="left")
    df = df[df.sy.isin(YEARS)]
    df["avg_teacher_salary"] = df.avg_teacher_salary.fillna(df.avg_teacher_salary_fy15)
    df.loc[df.avg_teacher_salary_fy15.notna() & (df.sy == "2015"), "avg_teacher_salary_source"] = \
        "DESE Profiles statereport/teachersalaries.aspx FY2015"
    df = df.drop(columns=["avg_teacher_salary_fy15"])

    df["students_per_teacher"] = df.total_enrollment / df.teacher_fte
    df["students_per_total_staff"] = df.total_enrollment / df.total_staff_fte
    df["students_per_instructional_staff"] = df.total_enrollment / df.instructional_staff_fte
    df["staff_per_100_students"] = df.total_staff_fte / df.total_enrollment * 100
    df["paras_per_100_students"] = df.paraprofessional_fte / df.total_enrollment * 100

    df["district"] = df.org_code.map(lambda c: DISTRICTS[c][0])
    df["grade_span"] = df.org_code.map(lambda c: DISTRICTS[c][1])
    df["district_note"] = df.org_code.map(lambda c: DISTRICTS[c][2])
    df["school_year"] = df.sy.map(lambda y: f"SY{int(y)-1}-{y[2:]}")
    df["fiscal_year"] = "FY" + df.sy
    df.loc[df.sy == "2026", "year_note"] = "SY2025-26: enrollment/staffing only; finance and RADAR not yet published for FY2026"
    df.loc[df.sy == "2015", "year_note"] = "Low-income column is Economically Disadvantaged (not comparable to 2022+ Low Income); SWD out-of-district % not published before 2020"
    df["source"] = ("DESE via E2C Hub: enrollment t8td-gens; staffing j5ue-xkfn (jobclass FTE, Oct 1); "
                    "teacher FTE 4684-cw3t (All Teachers); per-pupil/salary/OOD pupils er3w-dyti; "
                    "OOD tuition cnfs-edqq; SWD placement n62c-bx65 (RADAR). FY2015 salary: Profiles teachersalaries report")

    # Rank among PK-12 districts (partial-span districts excluded), 1 = lowest ratio / lowest value
    k12 = df.grade_span == "PK-12"
    for col in ["students_per_total_staff", "students_per_teacher", "swd_pct", "high_needs_pct", "el_pct",
                "low_income_or_ecd_pct", "in_district_ppx", "total_ppx", "avg_teacher_salary"]:
        df[f"rank_{col}"] = np.nan
        df.loc[k12, f"rank_{col}"] = df[k12].groupby("sy")[col].rank(method="min", ascending=True)
        df.loc[k12 & df[col].isna(), f"rank_{col}"] = np.nan
    df["n_pk12_districts_ranked"] = df[k12].groupby("sy").org_code.transform("count")

    # Needs-adjusted staffing: OLS of staff per 100 students on high-needs %
    # among PK-12 peers, per year; residual = actual minus predicted.
    df["staff_per_100_predicted_from_high_needs"] = np.nan
    for y in YEARS:
        m = k12 & (df.sy == y) & df.staff_per_100_students.notna() & df.high_needs_pct.notna()
        b, a = np.polyfit(df.loc[m, "high_needs_pct"], df.loc[m, "staff_per_100_students"], 1)
        df.loc[m, "staff_per_100_predicted_from_high_needs"] = a + b * df.loc[m, "high_needs_pct"]
        print(f"{y}: staff/100 = {a:.2f} + {b:.3f} * high_needs_pct  (n={m.sum()})")
    df["staff_per_100_residual_vs_needs_fit"] = df.staff_per_100_students - df.staff_per_100_predicted_from_high_needs

    cols = ["district", "org_code", "grade_span", "school_year", "fiscal_year", "total_enrollment",
            "total_staff_fte", "teacher_fte", "instructional_staff_fte", "paraprofessional_fte", "administrator_fte",
            "sped_related_staff_fte", "teacher_support_content_fte", "teacher_fte_from_jobclass",
            "students_per_total_staff", "students_per_teacher", "dese_students_per_teacher",
            "students_per_instructional_staff", "staff_per_100_students", "paras_per_100_students",
            "swd_pct", "high_needs_pct", "el_pct", "low_income_or_ecd_pct", "low_income_measure",
            "in_district_ppx", "total_ppx", "avg_teacher_salary", "avg_teacher_salary_source",
            "in_district_fte_pupils", "out_of_district_fte_pupils", "total_fte_pupils", "out_of_district_pupil_pct",
            "total_expenditure_dollars", "out_of_district_tuition_dollars", "out_of_district_tuition_pct_of_total_exp",
            "private_and_collab_tuition_dollars", "swd_out_of_district_pct", "swd_out_of_district_count",
            "sped_fte_per_100_in_district_swd",
            "staff_per_100_predicted_from_high_needs", "staff_per_100_residual_vs_needs_fit",
            "n_pk12_districts_ranked"] + [c for c in df.columns if c.startswith("rank_")] + \
           ["district_note", "year_note", "source"]
    df = df[cols].sort_values(["school_year", "district"])
    for c in df.select_dtypes("float").columns:
        df[c] = df[c].round(2)
    df.to_csv(OUT, index=False)
    print("wrote", OUT, len(df))
    return df


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    d = build()
    b = d[d.district == "Brookline"]
    print(b.T.to_string())
