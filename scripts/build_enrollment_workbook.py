"""
Brookline_Enrollment_Explained.xlsx: how the enrollment forecast works, from births to students.

The chain every enrollment forecast here uses (NESDEC's method, and the base case built on it):
  births  ->  kindergarten six years later (births x a kindergarten-per-birth ratio)
          ->  each class moves up a grade each year, multiplied by a grade-to-grade ratio
              (above 1 means more children move in than leave; below 1, the reverse)
          ->  total enrollment = PK + the thirteen K-12 classes

Sheets:
  How it works   the chain in plain words, the colour legend, and where each number comes from
  By year        FY2005-FY2040 side by side: actual, NESDEC (published Oct 2023), the base case
                 (NESDEC adjusted for actual births) and the School Department's forecast
                 (Cropper-McKibben), with births, kindergarten per birth and enrollment per birth
  Your scenario  a live cohort model from the FY2026 actual grades: change the inputs and every
                 year to FY2040 recalculates
  Inputs         births by year, the kindergarten ratio and the grade-to-grade ratios (blue cells)
  Grades         actual enrollment by grade FY2014-FY2026, NESDEC's published grade forecast, and
                 the base case's births-adjusted version

Sources: births, output/brookline_resident_births.csv (DLS databank to 2014, MA DPH 2015-2023) and
the 2024 Annual Town Report (443); grades FY2014-FY2024 and NESDEC's estimated births and forecast,
data/NESDEC-Enrollment-Forecast.pdf (10/31/2023); FY2025-FY2026 grades, DESE enrollment by grade;
totals FY2005-FY2013, output/school_enrollment_staffing_fy05_25.csv; base case and School
Department forecast, scripts/expense_driver_forecast.py.

Run from scripts/:  python3 build_enrollment_workbook.py
"""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

import expense_driver_forecast as edf

ROOT = Path(__file__).parent.parent
OUT = ROOT / "Brookline_Enrollment_Explained.xlsx"

F = "Arial"
BLUE = Font(name=F, color="0000FF")
BOLD = Font(name=F, bold=True)
NORM = Font(name=F)
HEAD = Font(name=F, bold=True, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="1F3A5F")
SUB_FILL = PatternFill("solid", fgColor="E3E9F1")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
THIN = Border(bottom=Side(style="thin", color="CCCCCC"))
GRADES = ["PK", "K"] + [str(g) for g in range(1, 13)]

# ---------------------------------------------------------------- data
births = {}
with open(ROOT / "output" / "brookline_resident_births.csv") as fh:
    for r in csv.DictReader(fh):
        births[int(r["year"])] = (int(r["resident_births"]), r["source"])
births[2024] = (443, "Town Clerk, Brookline 2024 Annual Town Report, p.37")
NESDEC_BIRTHS = {**edf.NESDEC_BIRTHS, 2018: 571, 2019: 581}

# actual grades: NESDEC's historical table FY2014-FY2024 (PK, K-12), DESE FY2025-FY2026
HIST = {
    2014: [259, 631, 676, 618, 539, 656, 562, 519, 533, 493, 466, 445, 475, 403],
    2015: [264, 685, 645, 685, 620, 530, 634, 541, 506, 507, 494, 478, 431, 473],
    2016: [257, 633, 696, 621, 704, 598, 553, 610, 543, 507, 500, 507, 480, 446],
    2017: [262, 582, 627, 678, 633, 677, 584, 549, 576, 531, 500, 509, 492, 479],
    2018: [257, 609, 566, 631, 691, 621, 660, 585, 550, 568, 531, 510, 497, 506],
    2019: [251, 603, 615, 574, 645, 680, 605, 665, 571, 545, 554, 542, 489, 499],
    2020: [252, 600, 614, 613, 573, 624, 657, 582, 618, 561, 521, 557, 512, 474],
    2021: [153, 488, 501, 505, 545, 495, 543, 568, 503, 555, 509, 490, 515, 503],
    2022: [255, 501, 516, 507, 480, 534, 480, 503, 553, 513, 544, 509, 492, 518],
    2023: [257, 509, 527, 547, 534, 504, 544, 467, 521, 563, 510, 552, 507, 497],
    2024: [256, 472, 520, 527, 544, 537, 511, 519, 471, 511, 570, 522, 551, 513],
    2025: [259, 473, 470, 538, 517, 558, 530, 508, 516, 473, 517, 578, 523, 548],
    2026: [237, 453, 491, 482, 542, 501, 547, 528, 503, 517, 499, 535, 584, 519],
    # September 11, 2026 (Superintendent's report to the School Committee, 9/16/26, last page):
    # K-8 by grade = average class size x sections, summed over the eight schools (the school
    # totals reconcile to the reported 4,458 within one); BEEP (PK) 252 and grades 9-12 as reported
    2027: [252, 411, 466, 484, 495, 547, 497, 544, 513, 500, 531, 508, 543, 584],
}
HIST_NOTE = {2027: "September 2026: K-8 derived from the Superintendent's class-size table (average x sections); "
                   "9-12 and BEEP as reported. Approximate to within a student or two per grade."}
# The School Department's forecast: Cropper-McKibben, Demographic Study 2023 (revised 04/03/2024),
# Appendix D, district total by grade. Years to FY2024 are its history; FY2025 on are forecast.
# Excludes its 19 special-program students, which its PK-12 totals include.
CM_GRADES = {
    2020: [252, 600, 613, 613, 574, 627, 654, 586, 618, 561, 521, 557, 512, 474],
    2021: [144, 488, 501, 505, 545, 495, 543, 568, 503, 555, 509, 490, 515, 503],
    2022: [255, 501, 516, 507, 479, 534, 480, 503, 553, 513, 544, 509, 492, 518],
    2023: [257, 509, 527, 547, 534, 504, 544, 467, 521, 563, 510, 552, 507, 497],
    2024: [256, 471, 520, 527, 544, 537, 511, 519, 470, 511, 570, 521, 551, 513],
    2025: [256, 502, 473, 515, 521, 550, 539, 494, 526, 461, 499, 584, 510, 550],
    2026: [256, 497, 505, 474, 512, 528, 553, 522, 501, 519, 454, 515, 578, 515],
    2027: [256, 507, 496, 507, 469, 515, 530, 537, 531, 496, 512, 469, 509, 583],
    2028: [256, 525, 505, 503, 507, 475, 522, 519, 550, 529, 489, 529, 464, 513],
    2029: [256, 529, 520, 511, 503, 515, 485, 512, 534, 550, 522, 505, 523, 468],
    2030: [256, 541, 524, 527, 513, 512, 525, 479, 526, 537, 543, 539, 500, 528],
    2031: [256, 555, 528, 533, 532, 523, 525, 516, 493, 528, 530, 561, 534, 504],
    2032: [256, 583, 544, 537, 535, 545, 535, 518, 530, 500, 520, 548, 555, 539],
    2033: [256, 590, 567, 556, 541, 546, 559, 530, 534, 532, 493, 538, 542, 560],
    2034: [256, 607, 580, 576, 561, 555, 561, 552, 544, 539, 525, 510, 532, 546],
}
totals = {}
with open(ROOT / "output" / "school_enrollment_staffing_fy05_25.csv") as fh:
    for r in csv.DictReader(fh):
        if r["total_enrollment"]:
            totals[int(r["fiscal_year"])] = int(float(r["total_enrollment"]))
totals[2026] = 6948   # DESE October 1, 2025 count
totals[2027] = edf.ACTUAL_SEP_2026
TOTAL_NOTE = {2026: "DESE, October 1, 2025", 2027: "School Department, September 2026 count"}

# base case: NESDEC adjusted for actual births (edf), scaled to the FY2027 actual
# the model's own enrollment (output of expense_driver_forecast.py): NESDEC's path adjusted for
# births and scaled to the Sept 2026 count, plus the children of the Chestnut Hill homes, which
# the model adds on top (about 30 students); this is the figure the site shows
with open(ROOT / "output" / "expense_driver_forecast_fy26_40.csv") as fh:
    base_total = {int(r["fiscal_year"]): float(r["enrollment"]) for r in csv.DictReader(fh)}
scale = edf.ACTUAL_SEP_2026 / edf.NESDEC_PK12[2027]
base_k = {y: edf.NESDEC_GRADES[y][1] * scale for y in range(2028, 2035)}
base_k.update({y: edf.NESDEC_K_LATE * scale for y in range(2035, 2041)})
# the base case by grade, FY2024-FY2040: NESDEC's table adjusted for births, extended past FY2034
# with NESDEC's average ratios exactly as expense_driver_forecast.enrollment_path does, then scaled
# to the September 2026 count (before the Chestnut Hill children, which are not assigned to grades)
_ratios = [sum(edf.NESDEC_GRADES_PUBLISHED[y + 1][gi + 1] / edf.NESDEC_GRADES_PUBLISHED[y][gi]
               for y in range(2024, 2034)) / 10 for gi in range(1, 13)]
base_grades = {y: [v * scale for v in edf.NESDEC_GRADES[y]] for y in range(2024, 2035)}
_g = edf.NESDEC_GRADES[2034][:]
for _y in range(2035, 2041):
    _g = [_g[0], edf.NESDEC_K_LATE] + [_g[1 + i] * _ratios[i] for i in range(12)]
    base_grades[_y] = [v * scale for v in _g]
# NESDEC's grade-to-grade ratios, averaged over its projected years (as the base case extends it)
nesdec_ratio = [sum(edf.NESDEC_GRADES_PUBLISHED[y + 1][gi + 1] / edf.NESDEC_GRADES_PUBLISHED[y][gi]
                    for y in range(2024, 2034)) / 10 for gi in range(1, 13)]
nesdec_kratio = sum(edf.NESDEC_GRADES_PUBLISHED[y][1] / NESDEC_BIRTHS[y - 6] for y in range(2026, 2035)) / 9


def hist_ratio(gi, years):
    return sum(HIST[y + 1][gi + 1] / HIST[y][gi] for y in years) / len(years)


# ---------------------------------------------------------------- helpers
def head(ws, row, labels, widths=None):
    for c, lab in enumerate(labels, 1):
        x = ws.cell(row, c, lab)
        x.font, x.fill = HEAD, HEAD_FILL
        x.alignment = Alignment(wrap_text=True, vertical="bottom", horizontal="center")
    if widths:
        for c, w in enumerate(widths, 1):
            ws.column_dimensions[L(c)].width = w


def put(ws, row, col, value, fmt=None, font=NORM, fill=None, note=None):
    x = ws.cell(row, col, value)
    x.font = font
    if fmt:
        x.number_format = fmt
    if fill:
        x.fill = fill
    if note:
        x.comment = Comment(note, "model")
    return x


wb = Workbook()

# ---------------------------------------------------------------- Inputs
inp = wb.active
inp.title = "Inputs"
inp["A1"] = "Inputs (blue cells can be changed; Your scenario recalculates)"
inp["A1"].font = Font(name=F, bold=True, size=13)
put(inp, 3, 1, "Births a year from 2025 on (not yet counted)", font=BOLD)
put(inp, 3, 2, edf.BIRTHS_AHEAD, "0", BLUE, INPUT_FILL,
    "Base case: the 2022-24 average of actual births (482, 422 and 443). NESDEC's 2023 forecast estimated about 493.")
put(inp, 4, 1, "Kindergartners per birth six years earlier", font=BOLD)
put(inp, 4, 2, round(nesdec_kratio, 3), "0.000", BLUE, INPUT_FILL,
    "NESDEC's own ratio across its forecast years (its K divided by its estimated births). "
    "Actual: 0.93 in FY2026 (453 K from 487 births), 0.81 in FY2025, 1.01 in FY2015.")
put(inp, 5, 1, "Pre-kindergarten (held level)", font=BOLD)
put(inp, 5, 2, 257, "0", BLUE, INPUT_FILL, "NESDEC holds PK at 257-260; FY2026 actual was 237.")
put(inp, 7, 1, "Grade-to-grade ratios: next year's grade / this year's previous grade", font=BOLD)
head(inp, 8, ["Move", "Ratio used (input)", "NESDEC's forecast ratio", "Actual average FY2015-19", "Actual average FY2022-26"],
     [52, 18, 20, 22, 22])
for i in range(12):
    r = 9 + i
    put(inp, r, 1, f"{GRADES[i + 1]} to {GRADES[i + 2]}")
    put(inp, r, 2, round(nesdec_ratio[i], 4), "0.000", BLUE, INPUT_FILL)
    put(inp, r, 3, round(nesdec_ratio[i], 4), "0.000")
    put(inp, r, 4, round(hist_ratio(i + 1, range(2014, 2019)), 4), "0.000")
    put(inp, r, 5, round(hist_ratio(i + 1, range(2021, 2026)), 4), "0.000")
put(inp, 22, 1, "A ratio above 1 means more children of that age move into Brookline (or into the public "
                "schools) than leave; below 1, more leave. The ratios used start at NESDEC's.")
inp["A22"].alignment = Alignment(wrap_text=True)
inp.row_dimensions[22].height = 30
put(inp, 24, 1, "Births by calendar year", font=BOLD)
head(inp, 25, ["Year", "Births used", "Source", "NESDEC's 2023 estimate", "Births used minus NESDEC"])
inp.column_dimensions["C"].width = 60
BIRTH_ROW = {}
for i, y in enumerate(range(1980, 2035)):
    r = 26 + i
    BIRTH_ROW[y] = r
    put(inp, r, 1, y, "0")
    if y in births:
        put(inp, r, 2, births[y][0], "0", BLUE)
        put(inp, r, 3, births[y][1])
    else:
        put(inp, r, 2, "=$B$3", "0")
        put(inp, r, 3, "Assumption: the input in B3")
    if y in NESDEC_BIRTHS:
        put(inp, r, 4, NESDEC_BIRTHS[y], "0", BLUE)
        put(inp, r, 5, f"=B{r}-D{r}", "+0;-0;0")
BFIRST, BLAST = BIRTH_ROW[1980], BIRTH_ROW[2034]
inp.freeze_panes = "A9"


def births_of(year_cell):
    """Formula: births in a calendar year held in another cell (looked up on Inputs)."""
    return f"INDEX(Inputs!$B${BFIRST}:$B${BLAST},MATCH({year_cell},Inputs!$A${BFIRST}:$A${BLAST},0))"


# ---------------------------------------------------------------- Your scenario (live cohort model)
sc = wb.create_sheet("Your scenario")
sc["A1"] = "Your scenario: a live cohort model from the September 2026 (FY2027) actual grades"
sc["A1"].font = Font(name=F, bold=True, size=13)
sc["A2"] = ("Each year: kindergarten = births six years earlier x the kindergarten ratio; every other grade = "
            "last year's grade below x that move's ratio; PK held level. Change the blue cells on Inputs. "
            "Read a class diagonally: down one row and right one column each year.")
sc["A2"].font = NORM
YEARS = list(range(2027, 2041))
head(sc, 4, ["Grade"] + [f"FY{y}" for y in YEARS], [14] + [9] * len(YEARS))
put(sc, 5, 1, "K class born in", font=BOLD)
for j, y in enumerate(YEARS):
    put(sc, 5, 2 + j, y - 6, "0")
for gi, g in enumerate(GRADES):
    r = 6 + gi
    put(sc, r, 1, g, font=BOLD)
    for j, y in enumerate(YEARS):
        c = 2 + j
        if y == 2027:
            put(sc, r, c, HIST[2027][gi], "#,##0", BLUE, note=HIST_NOTE[2027] if gi == 1 else None)
        elif gi == 0:
            put(sc, r, c, "=Inputs!$B$5", "#,##0")
        elif gi == 1:
            put(sc, r, c, f"={births_of(f'{L(c)}$5')}*Inputs!$B$4", "#,##0")
        else:
            put(sc, r, c, f"={L(c - 1)}{r - 1}*Inputs!$B${9 + gi - 2}", "#,##0")
TOT = 6 + len(GRADES)
put(sc, TOT, 1, "Total PK-12", font=BOLD)
for j in range(len(YEARS)):
    c = 2 + j
    put(sc, TOT, c, f"=SUM({L(c)}6:{L(c)}{TOT - 1})", "#,##0", BOLD)
    sc.cell(TOT, c).fill = SUB_FILL
put(sc, TOT + 2, 1, "Compare", font=BOLD)
for k, (lab, src) in enumerate([("Base case", base_total), ("NESDEC", edf.NESDEC_PK12_PUBLISHED),
                                 ("Schools'", edf.CM_PK12)]):
    put(sc, TOT + 3 + k, 1, lab)
    for j, y in enumerate(YEARS):
        if y in src:
            put(sc, TOT + 3 + k, 2 + j, round(src[y]), "#,##0")
put(sc, TOT + 7, 1, "Why this differs a little from the base case: the base case runs NESDEC's own grade table "
                    "(adjusted for actual births), scales it to the September 2026 count and adds the children of "
                    "the Chestnut Hill homes; this sheet starts from the September 2026 grades and applies the "
                    "ratios directly. The September 2026 grades sum to 6,875 (the reported 6,889 also counts "
                    "11 special-program students and rounding).")
sc.freeze_panes = "B6"

# ---------------------------------------------------------------- By year
by = wb.create_sheet("By year", 0)
by["A1"] = "Brookline public school enrollment, FY2005 to FY2040: births, kindergarten and students"
by["A1"].font = Font(name=F, bold=True, size=13)
by["A2"] = ("Fiscal year = the school year that ends in it (FY2027 is 2026-27). Enrollment per birth divides "
            "PK-12 enrollment by the births of the 13 years whose children are in K-12 that year.")
by["A2"].font = NORM
COLS = ["Fiscal year", "School year", "K class born in", "K-12 classes born in",
        "Births in the K class's birth year", "Births, all 13 K-12 years",
        "Kindergarten", "K per birth", "Total PK-12", "Enrollment per birth",
        "NESDEC's estimated births for the K class", "Kindergarten", "Total PK-12", "K per birth",
        "Kindergarten", "Total PK-12", "Enrollment per birth",
        "Kindergarten", "Total PK-12", "K per birth", "Enrollment per birth",
        "Kindergarten", "Total PK-12", "Enrollment per birth"]
groups = [(3, 6, "Births"), (7, 10, "Actual"), (11, 14, "NESDEC, published Oct 2023"),
          (15, 17, "Base case (NESDEC adjusted for actual births)"),
          (18, 21, "School Department's forecast (Cropper-McKibben, 2023)"), (22, 24, "Your scenario (live)")]
for a_, b_, lab in groups:
    by.merge_cells(start_row=3, start_column=a_, end_row=3, end_column=b_)
    x = by.cell(3, a_, lab)
    x.font, x.fill, x.alignment = BOLD, SUB_FILL, Alignment(horizontal="center", wrap_text=True)
by.row_dimensions[3].height = 30
head(by, 4, COLS, [10, 10, 10, 12, 12, 12, 12, 9, 11, 11, 13, 12, 11, 9, 12, 11, 11, 12, 11, 9, 11, 12, 11, 11])
by.row_dimensions[4].height = 58
first = 5
cm_k = {y: g[1] for y, g in CM_GRADES.items()}
for i, y in enumerate(range(2005, 2041)):
    r = first + i
    put(by, r, 1, str(y))
    put(by, r, 2, f"{y - 1}-{str(y)[2:]}")
    put(by, r, 3, f"=VALUE(A{r})-6", "0")
    put(by, r, 4, f'=TEXT(VALUE(A{r})-18,"0")&"-"&TEXT(VALUE(A{r})-6,"0")')
    put(by, r, 5, f"={births_of(f'C{r}')}", "#,##0")
    put(by, r, 6, f"=SUMIFS(Inputs!$B${BFIRST}:$B${BLAST},Inputs!$A${BFIRST}:$A${BLAST},\">=\"&(VALUE(A{r})-18),"
                  f"Inputs!$A${BFIRST}:$A${BLAST},\"<=\"&(VALUE(A{r})-6))", "#,##0")
    if y in HIST:
        put(by, r, 7, HIST[y][1], "#,##0", BLUE, note=HIST_NOTE.get(y))
        put(by, r, 8, f"=G{r}/E{r}", "0.00")
    if y in totals:
        put(by, r, 9, totals[y], "#,##0", BLUE, note=TOTAL_NOTE.get(y))
        put(by, r, 10, f"=I{r}/F{r}", "0.00")
    if y - 6 in NESDEC_BIRTHS and y >= 2024:
        put(by, r, 11, NESDEC_BIRTHS[y - 6], "#,##0", BLUE)
    if y in edf.NESDEC_GRADES_PUBLISHED:
        put(by, r, 12, edf.NESDEC_GRADES_PUBLISHED[y][1], "#,##0", BLUE)
        put(by, r, 13, edf.NESDEC_PK12_PUBLISHED[y], "#,##0", BLUE)
        if y - 6 in NESDEC_BIRTHS:
            put(by, r, 14, f"=L{r}/K{r}", "0.00")
    if y >= 2028:
        put(by, r, 15, round(base_grades[y][1]), "#,##0", BLUE)
    if y >= 2026:
        put(by, r, 16, round(base_total[y]), "#,##0", BLUE)
        put(by, r, 17, f"=P{r}/F{r}", "0.00")
    if y in CM_GRADES:
        put(by, r, 18, cm_k[y], "#,##0", BLUE)
        put(by, r, 20, f"=R{r}/E{r}", "0.00")
    if y in edf.CM_PK12:
        put(by, r, 19, edf.CM_PK12[y], "#,##0", BLUE)
        put(by, r, 21, f"=S{r}/F{r}", "0.00")
    if y >= 2027:
        c = 2 + YEARS.index(y)
        put(by, r, 22, f"='Your scenario'!{L(c)}7", "#,##0", Font(name=F, color="008000"))
        put(by, r, 23, f"='Your scenario'!{L(c)}{TOT}", "#,##0", Font(name=F, color="008000"))
        put(by, r, 24, f"=W{r}/F{r}", "0.00")
    for c in range(1, 25):
        by.cell(r, c).border = THIN
last = first + len(range(2005, 2041)) - 1
put(by, last + 2, 1, "Blue: a number taken from a source. Black: a formula. Green: linked from Your scenario. "
                     "Kindergarten actuals start in FY2014, the first year of NESDEC's grade history. The School "
                     "Department's K per birth uses actual births, which its forecast did not know.")
by.freeze_panes = "C5"

# ---------------------------------------------------------------- Grades
gr = wb.create_sheet("Grades")
gr["A1"] = "Enrollment by grade"
gr["A1"].font = Font(name=F, bold=True, size=13)
row = 3


def grade_table(title, data, note):
    global row
    put(gr, row, 1, title, font=BOLD)
    put(gr, row + 1, 1, note)
    head(gr, row + 2, ["Fiscal year"] + GRADES + ["Total"], [11] + [8] * 15)
    for i, (y, g) in enumerate(sorted(data.items())):
        r = row + 3 + i
        put(gr, r, 1, str(y))
        for k, v in enumerate(g):
            put(gr, r, 2 + k, round(v), "#,##0", BLUE)
        put(gr, r, 2 + len(GRADES), f"=SUM(B{r}:{L(1 + len(GRADES))}{r})", "#,##0", BOLD)
    row = row + 4 + len(data)


grade_table("Actual", HIST, "FY2014-FY2024 from NESDEC's historical table; FY2025-FY2026 from DESE; FY2027 from the "
                            "Superintendent's September 2026 class-size table (approximate). Excludes ungraded and "
                            "special-program students.")
grade_table("NESDEC's forecast, as published (Oct 2023)", edf.NESDEC_GRADES_PUBLISHED,
            "Built on births NESDEC estimated (2022: 459 provisional; 2023 on: 518, 507, 492, 493, 494, 501).")
grade_table("Base case: NESDEC adjusted for actual births, scaled to the September 2026 count", base_grades,
            "Each class born 2022 or later scaled by actual / NESDEC births (2022: 482/459; 2023: 422/518; 2024: "
            f"443/507; 2025 on: the 2022-24 average, 449 a year); extended past FY2034 with NESDEC's average ratios; all x {scale:.3f} so "
            "FY2027 matches 6,889. The model also adds about 30 children from the Chestnut Hill homes, not shown by grade.")
grade_table("The School Department's forecast (Cropper-McKibben, 2023)", CM_GRADES,
            "Appendix D, district total. FY2020-FY2024 are its history; FY2025 on are its forecast. Excludes its 19 "
            "special-program students.")

# ---------------------------------------------------------------- Ratio history
# Every year's actual grade-to-grade ratio, as formulas on the Grades sheet's actual table
# (which starts at row 6 with FY2014, PK in column B, K in C, grade 12 in O).
rh = wb.create_sheet("Ratio history")
rh["A1"] = "How classes have actually grown or shrunk as they move up a grade, FY2014 to FY2027"
rh["A1"].font = Font(name=F, bold=True, size=13)
rh["A2"] = ("Each cell is this year's grade divided by last year's grade below: above 1, the class gained students "
            "(more families moved in or returned than left); below 1, it lost them. Calculated from the actual "
            "grades on the Grades sheet.")
rh["A2"].font = NORM
rh.merge_cells("A2:N2")
rh["A2"].alignment = Alignment(wrap_text=True)
rh.row_dimensions[2].height = 30
ACT = {y: 6 + i for i, y in enumerate(sorted(HIST))}       # Grades sheet row of each actual year
moves = [f"{GRADES[i + 1]} to {GRADES[i + 2]}" for i in range(12)]
head(rh, 4, ["Into school year"] + ["Kindergarten per birth"] + moves + ["K to grade 12, all moves multiplied"],
     [16, 13] + [9] * 12 + [14])
rh.row_dimensions[4].height = 30
yrs = sorted(HIST)
for k, y in enumerate(yrs):
    r = 5 + k
    put(rh, r, 1, f"FY{y}")
    put(rh, r, 2, f"=Grades!C{ACT[y]}/{births_of(str(y - 6))}", "0.00")
    if y - 1 in HIST:
        for i in range(12):
            gc_prev, gc = L(3 + i), L(4 + i)   # grade i (K=C) last year -> grade i+1 this year
            put(rh, r, 3 + i, f"=Grades!{gc}{ACT[y]}/Grades!{gc_prev}{ACT[y - 1]}", "0.00")
end = 5 + len(yrs) - 1
summ = [("Average before COVID (into FY2015-FY2019)", 2015, 2019), ("COVID years (into FY2020-FY2021)", 2020, 2021),
        ("Since (into FY2022-FY2027)", 2022, 2027), ("Since, without the FY2022 rebound (FY2023-FY2027)", 2023, 2027),
        ("All years (into FY2015-FY2027)", 2015, 2027)]
for j, (lab, a_, b_) in enumerate(summ):
    r = end + 2 + j
    put(rh, r, 1, lab, font=BOLD)
    ra, rb = 5 + yrs.index(a_), 5 + yrs.index(b_)
    put(rh, r, 2, f"=AVERAGE(B{5 + yrs.index(max(a_, 2014))}:B{rb})", "0.00", BOLD)
    for i in range(12):
        put(rh, r, 3 + i, f"=AVERAGE({L(3 + i)}{ra}:{L(3 + i)}{rb})", "0.000", BOLD)
    if a_ != 2020:   # multiplying a one-off COVID year across 12 grades has no meaning
        put(rh, r, 15, f"=PRODUCT(C{r}:N{r})", "0.00", BOLD)
    else:
        put(rh, r, 15, "n/a", note="The COVID drop happened once, to every grade in the same year; no class "
                                   "experienced it at every move, so multiplying it across 12 grades means nothing.")
r = end + 2 + len(summ) + 1
put(rh, r, 1, "NESDEC's forecast", font=BOLD)
put(rh, r, 2, round(nesdec_kratio, 3), "0.00", BLUE)
for i in range(12):
    put(rh, r, 3 + i, round(nesdec_ratio[i], 3), "0.000", BLUE)
cm_ratio = [sum(CM_GRADES[y + 1][i + 2] / CM_GRADES[y][i + 1] for y in range(2024, 2034)) / 10 for i in range(12)]
put(rh, r + 1, 1, "School Department's forecast", font=BOLD)
for i in range(12):
    put(rh, r + 1, 3 + i, round(cm_ratio[i], 3), "0.000", BLUE)
for rr in (r, r + 1):
    put(rh, rr, 15, f"=PRODUCT(C{rr}:N{rr})", "0.00", BOLD)
put(rh, r + 1, 2, "see note", note="The School Department's forecast projects births from a population model, so its "
    "kindergarten per actual birth rises from about 1.0 to about 1.35 by FY2034 (607 kindergartners from 2028 births "
    "the base case puts at about 449).")
put(rh, r + 3, 1, "Read across a summary row to see what happens to a class: multiply its ratios together. Before "
                  "COVID a kindergarten class ended grade 12 about 7% smaller; since FY2022 classes have grown about "
                  "6%, partly the return of families who left during COVID. NESDEC assumes about +2%. The forecast "
                  "ratios are averages over each forecast's projected years.")
rh.merge_cells(start_row=r + 3, start_column=1, end_row=r + 3, end_column=14)
rh.cell(r + 3, 1).alignment = Alignment(wrap_text=True)
rh.row_dimensions[r + 3].height = 45
rh.freeze_panes = "B5"

# ---------------------------------------------------------------- One class, step by step
st = wb.create_sheet("One class, step by step", 1)
st.column_dimensions["A"].width = 13
st["A1"] = "One class, step by step: the children who start kindergarten in fall 2026 (FY2027)"
st["A1"].font = Font(name=F, bold=True, size=13)
intro = [
    "These children were mostly born in 2021, when Brookline residents had 491 babies.",
    "Kindergarten: NESDEC multiplies those births by its kindergarten ratio, about 0.845: 491 x 0.845 = 415.",
    "Every year after, the class moves up a grade. NESDEC multiplies last year's size by a grade-to-grade ratio taken "
    "from Brookline's history: a little above 1 in the early grades, where families with young children move in, and "
    "about 0.95 from grade 5 to grade 6, when some families leave for private or other middle schools.",
    "So 415 becomes 415 x 1.029 = 427 in grade 1, then 427 x 1.023 = 437 in grade 2, and so on. The 'Change' columns "
    "show each year's ratio. The base case follows the same steps, from NESDEC's numbers scaled up 1.7% to match the "
    "September 2026 count (2021 births were already counted, so this class needs no births adjustment).",
    "The School Department's forecast starts the same class at 507 and keeps it growing: its ratios assume more "
    "families moving in at every age. The actual kindergarten in September 2026 was about 411.",
]
for i, t in enumerate(intro):
    x = st.cell(3 + i, 1, t)
    x.font = NORM
    x.alignment = Alignment(wrap_text=True, vertical="top")
    st.merge_cells(start_row=3 + i, start_column=1, end_row=3 + i, end_column=11)
    st.row_dimensions[3 + i].height = 32
hr = 9
head(st, hr, ["Fiscal year", "School year", "Grade", "NESDEC", "Change (ratio)", "Base case", "Change (ratio)",
              "School Department", "Change (ratio)", "Your scenario", "Actual"],
     [13, 11, 8, 11, 12, 11, 12, 14, 12, 13, 10])
for k in range(13):
    y = 2027 + k
    r = hr + 1 + k
    gi = 1 + k   # K is index 1
    put(st, r, 1, f"FY{y}")
    put(st, r, 2, f"{y - 1}-{str(y)[2:]}")
    put(st, r, 3, GRADES[gi])
    if y in edf.NESDEC_GRADES_PUBLISHED:
        put(st, r, 4, edf.NESDEC_GRADES_PUBLISHED[y][gi], "#,##0", BLUE)
    if y in base_grades:
        put(st, r, 6, round(base_grades[y][gi]), "#,##0", BLUE)
    if y in CM_GRADES:
        put(st, r, 8, CM_GRADES[y][gi], "#,##0", BLUE)
    if y in YEARS:
        c = 2 + YEARS.index(y)
        put(st, r, 10, f"='Your scenario'!{L(c)}{6 + gi}", "#,##0", Font(name=F, color="008000"))
    if y in HIST:
        put(st, r, 11, HIST[y][gi], "#,##0", BLUE, note=HIST_NOTE.get(y))
    if k > 0:
        for col, src in [(5, 4), (7, 6), (9, 8)]:
            put(st, r, col, f'=IF(AND(ISNUMBER({L(src)}{r}),ISNUMBER({L(src)}{r - 1})),{L(src)}{r}/{L(src)}{r - 1},"")', "0.000")
put(st, hr + 15, 1, "Kindergarten row: NESDEC's 415 = 491 births x 0.845. Your scenario's kindergarten starts from "
                    "the September 2026 count (about 411) and follows the ratios on Inputs. Past FY2034 only the "
                    "base case and Your scenario continue; the base case extends NESDEC's table with its average ratios.")
st.merge_cells(start_row=hr + 15, start_column=1, end_row=hr + 15, end_column=11)
st.cell(hr + 15, 1).alignment = Alignment(wrap_text=True)
st.row_dimensions[hr + 15].height = 45
st.freeze_panes = "A10"

# ---------------------------------------------------------------- How it works
hw = wb.create_sheet("How it works", 0)
hw.column_dimensions["A"].width = 110
lines = [
    ("How Brookline's enrollment forecast works", Font(name=F, bold=True, size=14)),
    ("", NORM),
    ("1. Births. Every kindergarten class starts with the babies born to Brookline residents six years earlier. "
     "Births fell from about 690 a year in 2008-13 to 422 in 2023 and 443 in 2024.", NORM),
    ("2. Kindergarten = births x a kindergarten-per-birth ratio. Some children born here move away or go to "
     "private school; some born elsewhere move in. NESDEC uses about 0.85 kindergartners per birth; Brookline's "
     "actual ratio has ranged from about 0.8 to 1.0.", NORM),
    ("3. Each class moves up a grade every year, multiplied by a grade-to-grade ratio. A ratio above 1 means "
     "families moving in outnumber those leaving at that age; below 1, the reverse. These ratios are where "
     "in-migration shows up.", NORM),
    ("4. Total enrollment is PK plus the thirteen K-12 classes. So a small birth year keeps the total down for "
     "thirteen years as it moves through.", NORM),
    ("", NORM),
    ("The three forecasts", BOLD),
    ("NESDEC (October 2023) runs that chain with births it estimated for 2023 onward, about 500 a year.", NORM),
    ("The base case uses NESDEC's chain but replaces its estimated births with the actual 422 (2023) and 443 "
     "(2024), and holds later births at the 2022-24 average, 449. That lowers every class born from 2023 on.", NORM),
    ("The School Department's forecast (Cropper-McKibben, 2023) expects enrollment to rise again to about 7,400 "
     "by FY2034, which needs far more families moving in for each birth than Brookline has seen.", NORM),
    ("A useful single number is enrollment per birth (By year, column H and others): total students divided by "
     "the births of the 13 years that feed K-12. It was 0.74 in FY2005, about 0.90 at the FY2016-19 peak and "
     "0.84 in FY2025. Each forecast implies its own path for it.", NORM),
    ("", NORM),
    ("The sheets", BOLD),
    ("One class, step by step: the children who start kindergarten in fall 2026, followed through grade 12 under "
     "each forecast, with the ratio applied at every step.", NORM),
    ("By year: every fiscal year FY2005-FY2040 side by side, with the birth years behind each.", NORM),
    ("Ratio history: every year's actual kindergarten-per-birth and grade-to-grade ratio since FY2014, with "
     "averages and the ratios each forecast assumes.", NORM),
    ("Your scenario: a live version of the chain. Change the blue cells on Inputs (births from 2025, the "
     "kindergarten ratio, PK, or any grade-to-grade ratio) and every year to FY2040 recalculates.", NORM),
    ("Inputs: the births series with sources and NESDEC's estimates, and the ratios: NESDEC's, and Brookline's "
     "actual averages before and after COVID for comparison.", NORM),
    ("Grades: actual enrollment by grade, NESDEC's published grade forecast, and the base case's adjusted version.", NORM),
    ("", NORM),
    ("Colours: blue = a number from a source or an input you can change (yellow fill marks the main inputs); "
     "black = a formula; green = linked from Your scenario.", NORM),
    ("Built by scripts/build_enrollment_workbook.py from the same data and model as brooklinefuture.org/forecast.", NORM),
]
for i, (t, f) in enumerate(lines, 1):
    x = hw.cell(i, 1, t)
    x.font = f
    x.alignment = Alignment(wrap_text=True, vertical="top")

# ---------------------------------------------------------------- chart data for the site
# Births by year and enrollment per birth for history and each forecast. Each forecast's
# enrollment per birth is measured against its OWN births assumption, so it shows what it assumes
# about families moving in, separately from what it assumes about births. Cropper-McKibben
# publishes births as five-year district totals (2,940 for 2020-25, 3,080 for 2025-30, 3,140 for
# 2030-35; Appendix C), shown here as yearly averages.
import json
b_act = {y: v[0] for y, v in births.items()}
b_nes = {**b_act, **{y: v for y, v in edf.NESDEC_BIRTHS.items() if y >= 2022}}
b_cm = {**b_act, **{y: 2940 / 5 for y in range(2020, 2025)}, **{y: 3080 / 5 for y in range(2025, 2030)},
        **{y: 3140 / 5 for y in range(2030, 2035)}}
b_base = {**b_act, **{y: edf.BIRTHS_AHEAD for y in range(2025, 2035)}}
pool = lambda b, fy: sum(b[y] for y in range(fy - 18, fy - 5))
chart = {
    "births": {"actual": [[y, b_act[y]] for y in range(2005, 2025)],
               "nesdec": [[y, b_nes[y]] for y in range(2022, 2029)],
               "cm": [[y, round(b_cm[y])] for y in range(2020, 2035)],
               "base": [[y, round(b_base[y], 1)] for y in range(2024, 2035)]},
    "perBirth": {"actual": [[y, round(totals[y] / pool(b_act, y), 3)] for y in sorted(totals) if y >= 2005],
                 "nesdec": [[y, round(edf.NESDEC_PK12_PUBLISHED[y] / pool(b_nes, y), 3)] for y in range(2027, 2035)],
                 "cm": [[y, round(edf.CM_PK12[y] / pool(b_cm, y), 3)] for y in range(2027, 2035)],
                 "base": [[y, round(base_total[y] / pool(b_base, y), 3)] for y in range(2027, 2041)]},
}
# Indicators to watch (the site's yearly panel): the latest actual readings, and what the base case
# and the two published forecasts expect for the next ones. Updates itself when a new year of births
# (brookline_resident_births.csv / births[...]) or a new HIST/totals year is added above.
fy_now, b_last = max(HIST), max(b_act)
kpb = lambda fy: HIST[fy][1] / b_act[fy - 6]
chart["indicators"] = {
    "births_year": b_last, "births": b_act[b_last], "births_prev": b_act[b_last - 1],
    "births_nesdec": edf.NESDEC_BIRTHS.get(b_last), "births_cm": round(b_cm[b_last]), "births_base_ahead": round(edf.BIRTHS_AHEAD),
    "fy": fy_now, "enroll": totals[fy_now], "enroll_prev": totals[fy_now - 1],
    "enroll_next_base": round(base_total[fy_now + 1]), "enroll_next_cm": edf.CM_PK12[fy_now + 1],
    "enroll_next_nesdec": edf.NESDEC_PK12_PUBLISHED[fy_now + 1],
    "k": HIST[fy_now][1], "k_birth_year": fy_now - 6, "k_births": b_act[fy_now - 6], "kpb": round(kpb(fy_now), 2),
    "kpb_min": round(min(kpb(y) for y in HIST if y != 2021), 2), "kpb_max": round(max(kpb(y) for y in HIST if y != 2021), 2),
    "k_next_base": round(base_k[fy_now + 1]), "k_next_cm": CM_GRADES[fy_now + 1][1],
    "k_next_nesdec": edf.NESDEC_GRADES_PUBLISHED[fy_now + 1][1], "k_next_births": b_act[fy_now - 5],
}
(ROOT / "output" / "enrollment_assumptions.json").write_text(json.dumps(chart))

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = ws.title != "How it works"
wb.save(OUT)
print(f"wrote {OUT.name}: sheets {wb.sheetnames}")
