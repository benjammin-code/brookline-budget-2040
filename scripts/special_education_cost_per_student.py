"""
The middle tier of an added student's cost: an open seat plus special education.

Three tiers for what one more student costs the schools a year (FY2027 dollars):
  1. Fills an open seat, no new staff: the budget lines that grow with each student
     (supplies, books, online tools, computers), FY2026 budget closing summary.
  2. Fills an open seat, plus special education at the district average: tier 1 plus
     Brookline's special education spending per student, net of federal grants and of
     the state's Circuit Breaker reimbursement, plus benefits for the staff it pays.
     Special education staff and services grow with enrollment; classrooms don't.
  3. Opens a new classroom with full staff: marginal_cost_per_student.csv (the
     driver forecast's cost of an added student, staff hired for every student).

Tier 2 assumes new students need special education at the district's average rate and
mix of needs (18.6% of students had disabilities in 2024-25). More high-cost needs raise
it; fewer lower it.

Sources (all saved under data/, URLs in data/SOURCES.md):
  data/dese_sped/direct-expenditure-trends.xlsx           DESE, Direct Special Education
      Expenditures FY08-FY25, sheet "data", Brookline FY2025. From the End of Year
      Report, Schedule 4: instructional services (function 2000) and tuition (9000),
      including spending from the Circuit Breaker fund; employee benefits (5000) are
      reported separately and are not included.
  data/dese_sped/circuit-breaker-fy2026-reimbursement.xlsx  DESE, FY2026 Circuit
      Breaker reimbursement, which repays FY2025 claims: Brookline $5,237,567.
  output/marginal_cost_per_student.csv                    benefit loading: health
      insurance and other payroll-linked benefits per salary dollar.

Writes output/special_education_cost_per_student.csv.
"""

import csv
from pathlib import Path

import openpyxl

ROOT = Path(__file__).parent.parent
OUT = ROOT / "output/special_education_cost_per_student.csv"

FY25_ENROLLMENT = 7023          # DESE October 1, 2024 count (FY2025)
FY26_ENROLLMENT = 6948          # DESE October 1, 2025 count, as in the FY2026 per-student table
SEAT_LINES_FY26 = 4_520_903     # FY2026 budget: supplies, online tools, computers, textbooks
CB_FOR_FY25 = 5_237_567         # Circuit Breaker paid in FY2026 for FY2025 claims
PAY = 0.03                      # Town pay target, used to carry FY2025 and FY2026 $ to FY2027


def dese_fy25():
    wb = openpyxl.load_workbook(ROOT / "data/dese_sped/direct-expenditure-trends.xlsx",
                                read_only=True, data_only=True)
    for r in wb["data"].iter_rows(values_only=True):
        if r and r[2] == "Brookline" and str(r[3]) == "2025":
            keys = ["teaching", "other_instructional", "in_district_transport",
                    "ma_public_collab", "private_out_of_state", "ood_transport",
                    "nonpublic_health", "grants_revolving", "combined"]
            return {k: float(v or 0) for k, v in zip(keys, r[4:13])}
    raise SystemExit("Brookline FY2025 row not found")


def cost_components():
    with open(ROOT / "output/marginal_cost_per_student.csv") as f:
        return {r["component"]: float(r["value"]) for r in csv.DictReader(f)}


def main():
    d = dese_fy25()
    c = cost_components()
    loading = (c["health insurance"] + c["other payroll-linked benefits"]) / c["staff"]

    local = d["combined"] - d["grants_revolving"]          # appropriation + Circuit Breaker
    net = local - CB_FOR_FY25                              # what Brookline's budget carries
    payroll = d["teaching"] + d["other_instructional"]     # staff and contracted services
    benefits = payroll * loading
    sped_fy25 = (net + benefits) / FY25_ENROLLMENT
    sped_fy27 = sped_fy25 * (1 + PAY) ** 2
    seat_fy26 = SEAT_LINES_FY26 / FY26_ENROLLMENT
    seat_fy27 = seat_fy26 * (1 + PAY)

    rows = [
        ("In-district teaching", d["teaching"], "DESE FY2025, Schedule 4"),
        ("Other in-district instruction (therapists, aides, services)", d["other_instructional"], "DESE FY2025"),
        ("In-district transportation", d["in_district_transport"], "DESE FY2025"),
        ("Tuition, Massachusetts public schools and collaboratives", d["ma_public_collab"], "DESE FY2025"),
        ("Tuition, private and out-of-state schools", d["private_out_of_state"], "DESE FY2025"),
        ("Out-of-district transportation", d["ood_transport"], "DESE FY2025"),
        ("Total, before federal grants", d["combined"], "DESE FY2025"),
        ("Less federal grants and other revolving funds", -d["grants_revolving"], "DESE FY2025; not paid by Brookline"),
        ("Less Circuit Breaker reimbursement for FY2025", -CB_FOR_FY25, "DESE FY2026 Circuit Breaker listing"),
        ("Net special education spending", net, "paid from Brookline's school budget"),
        (f"Plus benefits at {loading:.1%} of teaching and other instruction", benefits,
         "health insurance and payroll-linked benefits per salary dollar, marginal_cost_per_student.csv"),
        ("Special education, all in", net + benefits, "FY2025 dollars"),
    ]
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["line", "fy2025_dollars", "per_student_fy2025", "source"])
        for name, v, src in rows:
            w.writerow([name, round(v), round(v / FY25_ENROLLMENT), src])
        w.writerow([])
        w.writerow(["tier", "fy2027_dollars_per_student", "", "how"])
        w.writerow(["1. Fills an open seat, no new staff", round(seat_fy27), "",
                    f"${SEAT_LINES_FY26:,} / {FY26_ENROLLMENT:,} students (FY2026), +3%"])
        w.writerow(["2. Open seat plus special education at the district average", round(seat_fy27 + sped_fy27), "",
                    f"tier 1 + ${sped_fy25:,.0f} (FY2025) carried two years at 3% = ${sped_fy27:,.0f}"])
        w.writerow(["3. Opens a new classroom with full staff", round(c["total"]), "", "marginal_cost_per_student.csv"])

    for name, v, _ in rows:
        print(f"{name:<75} {v:>14,.0f} {v / FY25_ENROLLMENT:>8,.0f}")
    print(f"tier 1 ${seat_fy27:,.0f}  tier 2 ${seat_fy27 + sped_fy27:,.0f}  tier 3 ${c['total']:,.0f}")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
