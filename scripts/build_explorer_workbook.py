"""
Builds Brookline_Forecast_Model.xlsx: the Forecast Explorer as a spreadsheet.

The Explorer (docs/forecast_dashboard.html) runs docs/_build/dashboard_engine.js,
runModel(), on output/dashboard_data_page.json, the data the page embeds. This
workbook reproduces runModel line for line in live formulas, driven by a Settings
sheet that carries every Explorer control with the same label and options:

    Start here   plain-language guide
    Settings     the 22 Explorer controls (yellow cells), and how the model reads them
    Forecast     FY2026-FY2040: revenue, spending, the room, then every working step
    Revenue build  the levy recursion and new growth by kind, as formulas (2026-10-11;
                 it replaced the precomputed grid the Explorer looks up)
    Worked example FY2033 followed by hand
    Assumptions  every constant: a formula over History where measured, typed with its
                 source otherwise
    History      the FY2005-25 record the measured assumptions average over
    Data         the Town's schedules, the May 2026 override, the enrollment paths
    Checks       the base case against the Explorer engine, year by year
    Appendix     history tabs carried over from Brookline_Fiscal_Model.xlsx

The Revenue build mirrors new_growth_scenario_forecast.main().

Validation (scripts/workbook_validation): validate_workbook.py recalculates every year's
room, revenue and spending with the `formulas` package for scenarios covering every
control, against runModel in Node; validate_revenue_build.py checks the Revenue build
against the Explorer's grid for every Chestnut Hill estimate across growth steps and
mixes, and the Assumptions against the values the Explorer embeds.

Run from scripts/:  python3 build_explorer_workbook.py
"""
import csv
import json
import subprocess
import sys
from copy import copy
from pathlib import Path

import openpyxl
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "output" / "dashboard_data_page.json"
ENGINE = ROOT / "docs" / "_build" / "dashboard_engine.js"
HISTORY_SOURCE = ROOT / "Brookline_Fiscal_Model.xlsx"
OUT = ROOT / "Brookline_Forecast_Model.xlsx"

sys.path.insert(0, str(Path(__file__).parent))
import fy2027_adopted as A27
# new-homes inputs, measured from permits and rolls (scripts/new_homes_parameters.py)
_NH = json.loads((Path(__file__).resolve().parents[1] / "output" / "new_homes_parameters.json").read_text())
P_PACE, P_VALUE, P_SPH = (_NH["pace_homes_per_year"], _NH["blended_value_per_net_home_fy2026"],
                          _NH["students_per_home_blended"])                    # noqa: E402
import new_growth_scenario_forecast as ngs      # noqa: E402

D = json.loads(DATA_FILE.read_text())
YEARS = D["years"]                       # 2026..2040
Y0 = D["consts"]["anchor"]               # 2027
FIRST_COL = 3                            # years sit in columns C..Q on Forecast and Data


def ycol(y):
    return get_column_letter(FIRST_COL + YEARS.index(y))


# ---------------------------------------------------------------- styles
NAVY = "1F3A5F"
TITLE = Font(name="Calibri", size=16, bold=True, color=NAVY)
H2 = Font(name="Calibri", size=12, bold=True, color=NAVY)
BOLD = Font(name="Calibri", bold=True)
NOTE = Font(name="Calibri", italic=True, color="555555")
HEAD_FILL = PatternFill("solid", fgColor="E3E9F1")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
WORK_FILL = PatternFill("solid", fgColor="F4F4F2")
ROOM_FILL = PatternFill("solid", fgColor="E8F0E4")
THIN = Side(style="thin", color="BBBBBB")
INPUT_BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
USD = '"$"#,##0;[Red]-"$"#,##0'
USDM = '"$"#,##0.0,,"M";[Red]-"$"#,##0.0,,"M"'
PCT1 = "0.0%"
PCT2 = "0.00%"
PTS = '+0.00%;-0.00%;0.00%'
NUM1 = "#,##0.0"
NUM0 = "#,##0"
YEARFMT = '"FY"0'

wb = openpyxl.Workbook()


def name(nm, ref):
    wb.defined_names[nm] = DefinedName(nm, attr_text=ref)


def title(ws, text, note=None, width_cols=8):
    ws["A1"] = text
    ws["A1"].font = TITLE
    if note:
        ws["A2"] = note
        ws["A2"].font = NOTE
        ws["A2"].alignment = WRAP
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=width_cols)
        ws.row_dimensions[2].height = 48


# ================================================================= History
# The Town's own record, FY2005 to FY2025, one row per year. Assumptions that are measured
# from history are formulas over these cells, so changing the years averaged moves the forecast.
PL = json.loads((ROOT / "output" / "permit_leading_indicator.json").read_text())
HIST_CSV = ROOT / "output" / "brookline_historical_financials_fy05_25.csv"
HROWS = list(csv.DictReader(open(HIST_CSV)))
# FY2026 new growth, certified since the record above was assembled (DLS new growth report): only the
# levy columns the new growth rates are measured from (2026-10-13).
HROWS.append({"fiscal_year": "2026", "prior_levy_limit": "293111747", "total_new_growth_applied": "3561227",
              "res_new_growth_applied": "2425577"})
hs = wb.active
hs.title = "History"
title(hs, "History, FY2005 to FY2025",
      "The record the assumptions are measured from (FY2026: new growth only, as certified). Levy, new growth and overrides: Massachusetts Division of Local "
      "Services (DLS) levy limit and new growth reports. Revenue and spending: DLS Schedule A. State aid and local "
      "receipts: DLS recap sheets and Local Receipts Actual vs Estimate. Surplus: DLS certified free cash. Grey columns "
      "are worked out here.", 22)
HCOLS = [  # (key, csv column, label, format)
    ("fy", "fiscal_year", "Fiscal year", YEARFMT),
    ("prior", "prior_levy_limit", "Levy limit, prior year", USD),
    ("inc", "increase_2_5pct", "2.5% increase", USD),
    ("ng", "total_new_growth_applied", "New growth applied to the levy", USD),
    ("ov", "override", "Override", USD),
    ("dex", "debt_exclusions", "Debt exclusions", USD),
    ("levy", "total_levy", "Total levy raised", USD),
    ("resng", "res_new_growth_applied", "Residential new growth applied", USD),
    ("sa", "recap_state_aid", "State aid", USD),
    ("lre", "local_receipts_est_total", "Local receipts, budget estimate", USD),
    ("lra", "local_receipts_act_total", "Local receipts, actual", USD),
    ("surp", "general_fund_surplus", "General Fund surplus (certified free cash basis)", USD),
    ("rev", "rev_total_revenues", "Total revenues, Schedule A", USD),
    ("gg", "exp_general_government", "Spending: General Government", USD),
    ("ps", "exp_public_safety", "Spending: Public Safety", USD),
    ("pw", "exp_public_works", "Spending: Public Works", USD),
    ("hs", "exp_human_services", "Spending: Human Services", USD),
    ("cr", "exp_culture_recreation", "Spending: Culture and Recreation", USD),
]
HC = {k: get_column_letter(i + 1) for i, (k, *_r) in enumerate(HCOLS)}
HDER = [("res_pct", "Residential new growth, share of prior levy limit", "{resng}/{prior}", "0.000%"),
        ("all_pct", "All new growth, share of prior levy limit", "{ng}/{prior}", "0.000%"),
        ("com_pct", "Commercial, industrial and business equipment new growth, share", "{all_pct}-{res_pct}", "0.000%"),
        ("oth_surp", "Surplus not from receipts beating budget, share of revenue", "({surp}-({lra}-{lre}))/{rev}", "0.00%")]
for i, (k, *_r) in enumerate(HDER):
    HC[k] = get_column_letter(len(HCOLS) + i + 1)
HHEAD = 4
for k, _c, lab, _f in HCOLS:
    hs[f"{HC[k]}{HHEAD}"] = lab
for k, lab, _f, _fmt in HDER:
    hs[f"{HC[k]}{HHEAD}"] = lab
for col in range(1, len(HCOLS) + len(HDER) + 1):
    c = hs.cell(HHEAD, col)
    c.font, c.fill, c.alignment = BOLD, HEAD_FILL, WRAP
hs.row_dimensions[HHEAD].height = 62
HROW = {}
for i, r_ in enumerate(HROWS):
    rr_ = HHEAD + 1 + i
    fy_ = int(r_["fiscal_year"])
    HROW[fy_] = rr_
    for k, ccol, _lab, fmt in HCOLS:
        v = r_.get(ccol)
        if v not in ("", None):
            c = hs[f"{HC[k]}{rr_}"]
            c.value = int(float(v)) if k == "fy" else float(v)
            c.number_format = fmt
    for k, _lab, f, fmt in HDER:
        refs = {kk: f"{HC[kk]}{rr_}" for kk in HC}
        c = hs[f"{HC[k]}{rr_}"]
        c.value = "=IFERROR(" + f.format(**refs) + ',"")'
        c.number_format, c.fill = fmt, WORK_FILL


def H(key, fy, absolute=True):
    """History cell for `key` in fiscal year `fy`."""
    return f"History!${HC[key]}${HROW[fy]}" if absolute else f"History!{HC[key]}{HROW[fy]}"


def HR(key, fy0, fy1):
    return f"History!${HC[key]}${HROW[fy0]}:${HC[key]}${HROW[fy1]}"


# supporting tables under the yearly record
tr = HROW[max(HROW)] + 3
hs.cell(tr, 1, "Town departments: how much of spending is pay").font = H2
hs.cell(tr + 1, 1, "Each department's FY2019 salary budget (FY2019 Financial Plan) as a share of its FY2019 spending, applied "
                   "to FY2025 spending.").font = NOTE
for j, lab in enumerate(["Department", "Spending FY2019", "Spending FY2025", "Salary budget FY2019", "Pay, FY2025 estimate"]):
    c = hs.cell(tr + 2, 1 + j, lab)
    c.font, c.fill = BOLD, HEAD_FILL
SAL = {r_["category"]: float(r_["salary_budget_fy19"])
       for r_ in csv.DictReader(open(ROOT / "output" / "department_fte_salary_by_category_fy19_fy26.csv"))}
PERS_ROWS = {}
for j, (cat, key) in enumerate([("General Government", "gg"), ("Public Safety", "ps"), ("Public Works", "pw"),
                                ("Human Services", "hs"), ("Culture & Recreation", "cr")]):
    rr_ = tr + 3 + j
    hs.cell(rr_, 1, cat)
    hs.cell(rr_, 2, f"={H(key, 2019)}").number_format = USD
    hs.cell(rr_, 3, f"={H(key, 2025)}").number_format = USD
    c = hs.cell(rr_, 4, SAL[cat]); c.number_format = USD; c.font = Font(name="Calibri", color="0000FF")
    hs.cell(rr_, 5, f"=C{rr_}*D{rr_}/B{rr_}").number_format = USD
    hs.cell(rr_, 5).fill = WORK_FILL
    PERS_ROWS[cat] = rr_
p0, p1 = tr + 3, tr + 7
hs.cell(p1 + 1, 1, "Total").font = BOLD
for col in (3, 5):
    hs.cell(p1 + 1, col, f"=SUM({get_column_letter(col)}{p0}:{get_column_letter(col)}{p1})").number_format = USD
PERS_TOTAL = p1 + 1

tr = PERS_TOTAL + 3
hs.cell(tr, 1, "New growth by type, FY2018 to FY2025").font = H2
hs.cell(tr + 1, 1, "Value the assessors added from identified new construction (parcel-by-parcel classifier on the assessment "
                   "rolls, land-value-map), against the total new growth value DLS certified for that class.").font = NOTE
for j, lab in enumerate(["Fiscal year", "Homes: identified new construction", "Homes: all new growth value (DLS)",
                         "Homes: new construction share", "Commercial: identified new or reclassified",
                         "Commercial, industrial and equipment: all new growth value (DLS)", "Commercial: new share"]):
    c = hs.cell(tr + 2, 1 + j, lab)
    c.font, c.fill, c.alignment = BOLD, HEAD_FILL, WRAP
hs.row_dimensions[tr + 2].height = 48
TYPE_ROW = {}
for j, r_ in enumerate(csv.DictReader(open(ROOT / "land-value-map" / "output" / "new_growth_type_split_fy18_25.csv"))):
    rr_ = tr + 3 + j
    fy_ = int(r_["fiscal_year"])
    TYPE_ROW[fy_] = rr_
    hs.cell(rr_, 1, fy_).number_format = YEARFMT
    for col, k in [(2, "res_identified_new_construction"), (3, "dor_res_new_growth_value"),
                   (5, "com_identified_new_or_reclassified_parcel"), (6, "dor_cip_new_growth_value")]:
        hs.cell(rr_, col, float(r_[k])).number_format = USD
    hs.cell(rr_, 4, f"=B{rr_}/C{rr_}").number_format = "0.0%"
    hs.cell(rr_, 7, f"=E{rr_}/F{rr_}").number_format = "0.0%"
    hs.cell(rr_, 4).fill = hs.cell(rr_, 7).fill = WORK_FILL

tr = max(TYPE_ROW.values()) + 3
hs.cell(tr, 1, "Business equipment (personal property) new growth, share of prior levy limit").font = H2
hs.cell(tr + 1, 1, "Board of Assessors, FY2022 to FY2025 Tax Classification Hearing presentations (the only years this split "
                   "is published).").font = NOTE
PP_ROW = {}
for j, (fy_, v) in enumerate([(2022, 0.002374), (2023, 0.002164), (2024, 0.002629), (2025, 0.002011), (2026, 0.002857)]):
    rr_ = tr + 2 + j
    hs.cell(rr_, 1, fy_).number_format = YEARFMT
    c = hs.cell(rr_, 2, v); c.number_format = "0.0000%"; c.font = Font(name="Calibri", color="0000FF")
    PP_ROW[fy_] = rr_
for col in range(1, len(HCOLS) + len(HDER) + 1):
    hs.column_dimensions[get_column_letter(col)].width = 16
hs.column_dimensions["A"].width = 22
hs.freeze_panes = f"B{HHEAD + 1}"


# ================================================================= Data (year series and choices)
data = wb.create_sheet("Data")
title(data, "Year-by-year inputs",
      "Schedules the forecast reads year by year: the Town's own long-range plan (January 2026), the FY2027 budget as "
      "adopted, the override voters approved in May 2026, and the two enrollment forecasts. The Revenue build and "
      "Forecast sheets read them with formulas; nothing here needs editing.", 17)
r = 4
data.cell(r, 1, "Series").font = BOLD
data.cell(r, 2, "Source").font = BOLD
YEAR_HEAD_DATA = r
for y in YEARS:
    c = data.cell(r, FIRST_COL + YEARS.index(y), y)
    c.number_format = YEARFMT
    c.font = BOLD
    c.fill = HEAD_FILL
r += 1
DROW = {}


def year_series(key, label, values, fmt=USD, source=None):
    global r
    data.cell(r, 1, label)
    if source:
        data.cell(r, 2, source).font = NOTE
    for y in YEARS:
        v = values.get(str(y), values.get(y))
        if v is not None:
            c = data.cell(r, FIRST_COL + YEARS.index(y), v)
            c.number_format = fmt
    DROW[key] = r
    r += 1


TOWN_PLAN = {}
for r_ in csv.DictReader(open(ROOT / "output" / "town_own_forecast_fy26_31.csv")):
    if r_["category"] == "revenue":
        TOWN_PLAN[r_["subcategory"]] = {int(k): float(v) for k, v in r_.items() if k.isdigit()}
LRFP = "Town long-range plan, Jan 2026"
year_series("plan_prop", "Town plan: property tax, including debt exclusions (before the May 2026 override)",
            TOWN_PLAN["property_taxes"], source=LRFP)
year_series("plan_dex", "Town plan: debt exclusion tax", TOWN_PLAN["debt_exclusion"], source=LRFP)
year_series("plan_ofund", "Town plan: other available funds", TOWN_PLAN["other_available_funds"], source=LRFP)
year_series("ovr", "May 2026 override: amount added each year", ngs.MAY_2026_OVERRIDE_SCHEDULE,
            source="Override Guide; ballot of May 5, 2026")
year_series("stab", "Override stabilization fund, drawn over three budgets", A27.OVERRIDE_STABILIZATION_DRAW,
            source="FY2027 budget as adopted")
year_series("nes", "Enrollment, NESDEC projection", D["enrollment"]["nesdec"], NUM1,
            source="NESDEC 2023, scaled to Oct 2025")
year_series("cm", "Enrollment, Cropper-McKibben (the schools' forecast)", D["enrollment"]["cm"], NUM1,
            source="Cropper-McKibben 2023")
year_series("pen", "Town plan: pensions", D["town"]["pensions"], source=LRFP)
year_series("opeb", "Town plan: retiree health (OPEB)", D["town"]["opeb"], source=LRFP)
year_series("ob", "Town plan: other benefits", D["town"]["other_benefits"], source=LRFP)
year_series("debt", "Capital table: debt within the levy", D["town"]["debt"],
            source="FY2027 Financial Plan p.384")
year_series("other", "Town plan: capital, reserves and other", D["town"]["other_nondept"], source=LRFP)
year_series("cip", "Town plan: capital funded from revenue", D["town"]["cip_revfin"], source=LRFP)
year_series("resf", "Town plan: reserve fund", D["town"]["reserve_fund"], source=LRFP)
year_series("gen", "Town plan: general non-departmental", D["town"]["nondept_general"], source=LRFP)
year_series("cipfc", "Capital paid from free cash", D["town"]["cip_freecash"],
            source="FY2027 Financial Plan p.384 to FY2032, then a share of net revenue")
year_series("otr", "Retiree health: the actuary's premium trend", {int(k): v for k, v in D["consts"]["opeb_trend"].items() if int(k) >= 2028},
            "0.000%", source="FY2024 audit, OPEB note (Medicare and non-Medicare averaged)")
year_series("abr", "Budgeted local receipts, adopted", D["revenue"]["adopted_budgeted_receipts"],
            source="FY2026 budget (Town plan) and FY2027 budget as adopted")
year_series("plan_fc", "Town plan: free cash", TOWN_PLAN["free_cash"], source=LRFP)
fc_known = {}
for y in D["revenue"]["known_fc_years"]:
    fc_known[str(y)] = D["revenue"]["adopted_fc"].get(str(y), D["revenue"]["town_fc"].get(str(y)))
year_series("fc", "Free cash, known (adopted budget, or the Town plan)", fc_known,
            source="FY2027 adopted; FY2026 Town plan")

# ---- options for the select settings
r += 1
data.cell(r, 1, "Choices for the settings").font = H2
r += 1
data.cell(r, 1, "Setting").font = BOLD
data.cell(r, 3, "Choice").font = BOLD
data.cell(r, 4, "How the model reads it").font = BOLD
r += 1
OPTIONS = {
    "opeb": [("redirect", "Moved to retiree health (OPEB), the Town's plan; once it's paid off, held for a decision"),
             ("spend", "Moved to retiree health (OPEB); once it's paid off, counted as room"),
             ("keep", "Kept in the budget as room")],
    "staffing": [("half", "Fall half as fast as enrollment, as in FY2019 to FY2025"), ("keep", "Held at the FY2027 level"),
                 ("hold", "Follow enrollment, students per staff held"),
                 ("partial", "Follow enrollment, students per staff a third back to FY2019")],
    "mix": [("mix", "Today's mix"), ("housing", "New homes"), ("commercial", "New commercial space"),
            ("even", "Half homes, half commercial")],
    "homes": [("all", "As expected"), ("half", "Half as many"), ("none", "None: renovation and commercial growth only")],
    "fill": [("staff", "Each brings new staff at today's ratio"), ("fill", "Fill seats left open as enrollment falls")],
    "enroll": [("nesdec", "NESDEC (declines)"), ("flat", "Flat at FY2027"), ("cm", "Cropper-McKibben, the schools' forecast (rises)")],
    "capital": [("full", "The 6.6% policy, from FY2028"), ("table", "Held at the Town's six-year table, about 6%")],
    "chca": [("approved", "Approved program, Town Meeting May 2026"), ("cr_avg", "City Realty's average estimate"),
             ("rkg", "RKG's estimate"), ("in_trend", "Already inside trend growth")],
    "ps_staff": [("budget", "FY2027 budget, plus a fire company at about 31,200 homes"),
                 ("police", "FY2027 budget and the fire company, with police growing with homes"),
                 ("restore", "Restored to earlier levels, police 136 and fire 168, plus the company"),
                 ("none", "FY2027 budget, no added fire company")],
    "ng2728": [("trend", "The recent trend (the base case)"), ("permits", "What the 2024 and 2025 permits point to"),
               ("permits_low", "Permits, low end of past rates"), ("permits_high", "Permits, high end of past rates")],
    "slip": [(0, "On schedule, FY2030"), (1, "One year late"), (2, "Two years late"), (3, "Three years late")],
}
OPT_RANGE = {}
for key, opts in OPTIONS.items():
    start = r
    for code, label in opts:
        data.cell(r, 1, key if r == start else None)
        data.cell(r, 3, label)
        data.cell(r, 4, code)
        r += 1
    OPT_RANGE[key] = (f"Data!$C${start}:$C${r - 1}", f"Data!$D${start}:$D${r - 1}")
data.column_dimensions["A"].width = 60
data.column_dimensions["B"].width = 30
for i in range(len(YEARS)):
    data.column_dimensions[get_column_letter(FIRST_COL + i)].width = 14
data.freeze_panes = "C5"


def dat(key, y, absolute=False):
    row_ = DROW[key]
    return f"Data!${ycol(y)}${row_}" if absolute else f"Data!{ycol(y)}{row_}"


# ================================================================= Assumptions
# Every fixed number the forecast uses, with how it is worked out and where it comes from.
# A formula when it can be measured from the History sheet or is arithmetic on published
# figures; a blue typed value when it is read from a document. Where the Python model rounds a
# measured value, the formula rounds it the same way, so the workbook and the Explorer agree.
asm = wb.create_sheet("Assumptions")
title(asm, "Assumptions",
      "Every fixed number the forecast uses. Black values are formulas: measured from the History sheet or worked out "
      "from published figures, so you can change the years averaged or a source figure and the whole forecast follows. "
      "Blue values are typed from the source named. The settings you are meant to vary are on the Settings sheet; these "
      "are the numbers underneath them.", 6)
for j, lab in enumerate(["Name", "Assumption", "Value used", "How it is worked out", "Source"]):
    c = asm.cell(4, 1 + j, lab)
    c.font, c.fill = BOLD, HEAD_FILL
BLUE = Font(name="Calibri", color="0000FF")
pp_rng = f"History!$B${PP_ROW[2022]}:$B${PP_ROW[2026]}"
pers = lambda cat: f"History!$E${PERS_ROWS[cat]}"
share_rng = lambda col: f"History!${col}${TYPE_ROW[2021]}:${col}${TYPE_ROW[2025]}"
A_SECTIONS = [
    ("Property tax: the levy limit and new growth", [
        ("K_LevyCap", "Yearly increase allowed on the levy limit", 0.025, PCT1,
         "Proposition 2½: the levy limit rises 2.5% a year, plus new growth and any override.",
         "Massachusetts General Laws c.59 §21C"),
        ("K_ResTrail", "Residential new growth, share of the prior year's levy limit", 
         f"=ROUND(AVERAGE({HR('res_pct', 2022, 2026)}),5)", "0.000%",
         "Average of FY2022 to FY2026 on History, rounded to 0.001 point. Change the years to test another window.",
         "DLS new growth (History)"),
        ("K_ComTrail", "Commercial, industrial and business equipment new growth, share of the prior levy limit",
         f"=ROUND(AVERAGE({HR('com_pct', 2022, 2026)}),5)", "0.000%",
         "Average of FY2022 to FY2026 on History, rounded the same way.", "DLS new growth (History)"),
        ("K_TrendRate", "Recent new growth rate, all property", "=K_ResTrail+K_ComTrail", "0.000%",
         "The two together. The New growth setting moves the rate up or down from here in tenths of a point.", ""),
        ("K_ResNewShare", "Share of residential new growth from net new homes (the rest is renovation)",
         "=ROUND(K_HomesPace*K_ResValUnit*K_ResTax/(K_ResTrail*Levy2025),4)", PCT1,
         "Set so FY2026 carries the recent pace of net new homes at the value each adds. Total residential new "
         "growth stays at its trend rate, which has held at 0.8% to 1.0% of the levy whether few or many homes were "
         "built; renovation, including houses rebuilt as houses, is the rest.",
         "Building permits and assessment rolls (new_homes_parameters.py)"),
        ("K_ComNewShare", "Share of commercial new growth from new or converted buildings",
         f"=ROUND(AVERAGE({share_rng('G')}),4)", "0.00%",
         "Average of FY2021 to FY2025, same table. Most commercial new growth is renovation and fit-out.", "Same"),
        ("K_PP", "Business equipment (personal property) new growth, share of the prior levy limit", 0.002407, "0.0000%",
         f"Average of FY2022 to FY2026 on History (=AVERAGE({pp_rng}) gives 0.24070%), rounded to 0.2407%. Part of the "
         "commercial rate above, not added to it.", "Board of Assessors classification hearings"),
        ("K_ResNewPct", "New growth rate from new homes", "=K_ResTrail*K_ResNewShare", "0.0000%",
         "Residential rate times the new-homes share.", ""),
        ("K_ResRenoPct", "New growth rate from home renovation", "=K_ResTrail*(1-K_ResNewShare)", "0.0000%",
         "Residential rate times the rest.", ""),
        ("K_ComNewPct", "New growth rate from new commercial space", "=K_ComTrail*K_ComNewShare", "0.0000%",
         "Commercial rate times the new-buildings share.", ""),
        ("K_ComRenoPct", "New growth rate from commercial renovation", "=K_ComTrail-K_ComNewPct-K_PP", "0.0000%",
         "What is left of the commercial rate after new buildings and equipment.", ""),
        ("K_TownNG", "New growth in the Town's own plan, each year", 2_500_000, USD,
         "The Town's long-range plan assumes a flat $2.5M. For FY2026 to FY2031 the forecast starts from the Town's own "
         "property tax figures and adds only the difference its new growth makes; see Revenue build.",
         "Town long-range plan, Jan 2026"),
        ("K_Perm27", "FY2027 real estate new growth tax the 2024 permits point to, middle of past rates",
         round(PL["years"]["2027"]["expected_applied"]["mid"]), USD,
         "Taxable permits times the middle of past ratios of new growth to permits, at the FY2026 tax rate.",
         "Town permit records; DLS new growth (permit_leading_indicator.py)"),
        ("K_Perm27Lo", "The same, low end of past rates", round(PL["years"]["2027"]["expected_applied"]["low"]), USD, "", "Same"),
        ("K_Perm27Hi", "The same, high end of past rates", round(PL["years"]["2027"]["expected_applied"]["high"]), USD, "", "Same"),
        ("K_Perm28", "FY2028 real estate new growth tax the 2025 permits point to, middle of past rates",
         round(PL["years"]["2028"]["expected_applied"]["mid"]), USD,
         "As above. FY2028 is taxed at the FY2027 rate, a little higher after the override, so this runs about 3% low.",
         "Same"),
        ("K_Perm28Lo", "The same, low end of past rates", round(PL["years"]["2028"]["expected_applied"]["low"]), USD, "", "Same"),
        ("K_Perm28Hi", "The same, high end of past rates", round(PL["years"]["2028"]["expected_applied"]["high"]), USD, "", "Same"),
        ("K_NG2026", "New growth in FY2026, as certified", "=" + H("ng", 2026), USD,
         "FY2026 is past, so every run uses the certified figure; the rates above apply from FY2027.", "DLS new growth (History)"),
        ("Levy2025", "FY2025 levy, debt exclusions set aside", f"={H('levy', 2025)}-{H('dex', 2025)}", USD,
         "Total levy raised less debt exclusion tax. New growth in FY2026 is measured against it.", "History"),
    ]),
    ("Turning new growth dollars into homes and commercial space", [
        ("K_HomesPace", "Net new homes a year, building permits issued 2016 to 2025", P_PACE, "0.0",
         "Every permit read and coded by hand, net of demolitions, assisted living counted separately.",
         "Town building permits (output/permit_homes_by_year.csv)"),
        ("K_ResValUnit", "Assessed value added by one net new home, FY2026", P_VALUE, USD,
         "The forecast adds apartments and condominiums, in their 2016 to 2025 proportions (about 80 to 20): "
         "apartments add about $521,000 of assessed value per net home and small multifamily and condominium "
         "buildings about $864,000, measured on the new-growth basis.",
         "Building permits followed onto the assessment rolls, FY2016 to FY2026"),
        ("K_ResApp", "Yearly rise in the value of a new home", 0.0496, "0.00%",
         "Town-wide residential value growth net of new growth, FY2018 to FY2024 average.", "Assessment rolls"),
        ("K_ComValSqft", "Assessed value per square foot of new commercial space, FY2026", 518, USD,
         "Taxable commercial value divided by commercial floor area, weighted (median $529).", "Assessment rolls"),
        ("K_ComApp", "Yearly rise in commercial value per square foot", 0.0128, "0.00%",
         "Town-wide commercial value growth net of new growth, FY2018 to FY2024; volatile in 2020 to 2023.", "Assessment rolls"),
        ("K_ResTax", "Residential tax rate, FY2026 (per dollar of value)", 0.009836, "0.0000%",
         "$9.836 per $1,000.", "Board of Assessors, FY2026 classification"),
        ("K_ComTax", "Commercial tax rate, FY2026 (per dollar of value)", 0.016238, "0.0000%",
         "$16.238 per $1,000.", "Board of Assessors, FY2026 classification"),
        ("K_ResValShare", "Residential share of taxable value, FY2026", "=30758464684/33832309213", PCT1,
         "Residential value over all taxable value.", "Board of Assessors, FY2026 classification"),
        ("K_LevyGrowth", "Yearly levy growth at the recent pace", "=K_LevyCap+K_ResTrail+K_ComTrail", "0.00%",
         "2.5% plus recent new growth.", ""),
        ("K_BlendApp", "Yearly rise in taxable value, all property", "=K_ResValShare*K_ResApp+(1-K_ResValShare)*K_ComApp",
         "0.00%", "The two value growth rates weighted by value. Tax rates drift by the levy's growth over this.", ""),
    ]),
    ("Local receipts and state aid", [
        ("K_PermitRate26", "Building permit fee, through FY2026 (share of construction cost)", 0.02, "0.0%",
         "$20 per $1,000 of estimated cost.", "Town fee schedule, 2022"),
        ("K_PermitRate27", "Building permit fee, from FY2027", 0.021, "0.0%",
         "$21 per $1,000, effective July 1, 2026.", "Town fee schedule, 2026"),
        ("K_Permits2025", "Building permit revenue, FY2025", 4_439_224, USD, "", "DLS local receipts, FY2025"),
        ("K_Inv2019", "Investment income, FY2019", 1_317_178, USD, "", "DLS local receipts"),
        ("K_Inv2025", "Investment income, FY2025", 5_146_469, USD,
         "Raised by high interest rates on Town cash, including unspent federal pandemic aid. Set aside from "
         "the growth rate.", "DLS local receipts"),
        ("K_InvEst2025", "Investment income budgeted, FY2025", 790_593, USD, "", "DLS local receipts"),
        ("K_InvFlat", "Investment income, each forecast year", 934_259, USD,
         "Held flat at the Town's FY2027 budget for investment income. It is part of the growth-linked "
         "receipts row on the Growth sheet.", "FY2027 Financial Plan, p. III-98"),
        ("K_Meals2019", "Meals tax, FY2019", 1_249_434, USD, "", "DLS local receipts"),
        ("K_Meals2025", "Meals tax, FY2025", 1_768_323, USD, "", "DLS local receipts"),
        ("K_MealsGrowth", "Yearly growth of meals tax at existing restaurants", "=ROUND((K_Meals2025/K_Meals2019)^(1/6)-1,4)",
         "0.00%", "FY2019 to FY2025 compound growth, rounded to 0.01 point.", ""),
        ("K_MealsPerSqft", "Meals tax per square foot of commercial space", "=ROUND(K_Meals2025/6364845,4)", '"$"0.0000',
         "FY2025 meals tax over 6,364,845 square feet of taxable commercial space. New commercial space is assumed to "
         "bring meals tax at the average rate.", "Assessment rolls"),
        ("R_LRresid2025", "Local receipts not tied to growth, FY2025",
         f"={H('lra', 2025)}-K_Meals2025-K_Permits2025-K_Inv2025", USD,
         "Actual local receipts less meals tax, building permits and investment income, which are forecast "
         "separately.", "History"),
        ("R_LRbase", "Base case growth of those receipts",
         f"=(({H('lra', 2025)}-K_Meals2025-K_Inv2025)/({H('lra', 2019)}-K_Meals2019-K_Inv2019))^(1/6)-1", "0.00%",
         "FY2019 to FY2025 compound growth, meals tax and investment income set aside. The Local receipts "
         "setting starts here.", "History"),
        ("R_SA2026", "State aid, FY2026", round(D["revenue"]["sa_2026"]), USD, "The Town's FY2026 figure.", "Town long-range plan"),
        ("R_SA2027", "State aid, FY2027", round(D["revenue"]["sa_2027"]), USD, "The adopted FY2027 budget.", "FY2027 adopted budget"),
        ("R_SAbase", "Base case state aid growth", D["revenue"]["sa_cagr"], "0.00%",
         "The rate in the Town's own long-range plan, chosen to be conservative. FY2015 to FY2025 was 3.5%, "
         "including FY2019's one-year 8.6% rise; FY2019 to FY2025 was 2.0%. The State aid setting starts here.",
         "Town long-range plan"),
    ]),
    ("The free cash cycle", [
        ("R_BudgetRatio", "Local receipts budgeted, as a share of what is collected",
         f"=({H('lre', 2025)}-K_InvEst2025+K_InvFlat)/({H('lra', 2025)}-K_Inv2025+K_InvFlat)",
         PCT1, "FY2025 budget estimate over actual, with investment income at its flat forecast level on both "
         "sides. The Town budgets receipts below what it expects to collect.", "History"),
        ("R_OtherSurplus", "Other year-end surplus, share of revenue", f"=AVERAGE({HR('oth_surp', 2022, 2025)})", "0.00%",
         "Surplus beyond receipts beating budget (unspent appropriations and the like), FY2022 to FY2025 average. "
         "Measured on the state's total revenues (actual receipts, no free cash), and applied to the same.", "History"),
        ("R_ApprShare", "Share of free cash the Town appropriates",
         f"=AVERAGE({dat('plan_fc', 2026, True)}/{H('surp', 2024)},{round(D['revenue']['adopted_fc']['2027'])}/{H('surp', 2025)})", PCT1,
         "Free cash used in the FY2026 budget and the adopted FY2027 budget over the surplus two years earlier; "
         "the rest stays in reserves.", "Town plan; FY2027 adopted budget; History"),
    ]),
    ("Chestnut Hill redevelopment", [
        ("K_ChcaStart", "First fiscal year with Chestnut Hill on the tax roll", 2032, "0", "", "Forecast assumption"),
        ("K_ChcaSpan", "Years to build out", 3, "0", "A third of the project each year from the first.", ""),
        ("K_ChcaDollarYr", "Dollar year of the revenue estimates", 2025, "0",
         "RKG built the model on the FY2025 budget. Each third's property tax enters at its entry year's value "
         "(value growth times tax-rate drift, by class), then grows with the levy; rooms tax and excise grow at the "
         "base rate of the other local receipts.", "ERSC report, Appendix E"),
        ("K_ChcaUnits", "Homes", 266, NUM0, "", "Town Meeting approval, May 2026"),
        ("K_ChcaSPU", "School-age children per home", 0.126, "0.000",
         "High-rise, mostly studios and one-bedrooms.", "Fiscal impact estimate for a comparable high-rise"),
        ("K_ChcaEmp", "Employees", "=(79000+105000)/200+200*500/2300", NUM1,
         "184,000 square feet of office and retail at one employee per 200, plus a 200-room hotel.", "City Realty scenario 1"),
    ]),
    ("Town services", [
        ("K_pD", "Town departments: share of spending that is pay", f"=History!$E${PERS_TOTAL}/History!$C${PERS_TOTAL}",
         PCT1, "The pay table on History.", "History; FY2019 Financial Plan"),
        ("K_psD", "Town pay: Public Safety share", f"={pers('Public Safety')}/History!$E${PERS_TOTAL}", PCT1,
         "Public Safety's pay over all departments' pay, same table.", ""),
        ("K_TownFTE", "Town staff, full-time equivalents, FY2027", D["consts"]["town_fte"], NUM1, "", "FY2027 Financial Plan"),
        ("K_BasePay", "Town pay target", D["base"]["pay"], PCT1, "The Pay setting moves every group from here.",
         "Town bargaining target"),
        ("K_BenLoad", "Benefits per dollar of added Town department cost", "=262/1109", "0.0000",
         "RKG's benefits per home over its department cost per home.", "RKG fiscal impact study, FY2025"),
        ("K_CostPerEmp", "Town cost per added commercial employee (FY2025 $)", "=219*1109/1371", '"$"#,##0.00',
         "RKG's $219 per employee, department share only.", "RKG fiscal impact study, FY2025"),
        ("K_SqftPerEmp", "Commercial square feet per employee", 200, NUM0, "", "RKG fiscal impact study"),
        ("K_Permit", "Planning and permitting staff, FY2027", "=1384996+892085+316790", USD,
         "Planning and Community Development, Building Code Enforcement and Building Administration. Grows with real-estate "
         "new growth above the trend.", "FY2027 Financial Plan"),
        ("K_CIP", "Capital policy: share of the prior year's net revenue", 0.066, PCT1,
         "4.5% for debt and 2.1% cash. Held at 6% for FY2026 and FY2027 only.", "Select Board policy; FY2027 Financial Plan pp.352, 363, 459"),
        ("K_NonApp", "Non-appropriated items left out of the policy's net revenue, FY2027", 10_792_034, USD,
         "State assessments and the like.", "FY2027 Financial Plan p.384"),
        ("K_NonAppG", "Non-appropriated items, yearly growth", 0.0238, "0.00%",
         "The Town's own table, FY2027 to FY2032.", "FY2027 Financial Plan p.384"),
        ("K_Reserve", "Reserve fund: share of the prior year's net revenue", 0.01, PCT1,
         "Town policy: 0.75% from the levy and 0.25% from free cash. Applied from FY2028.",
         "Reserve Policies, May 2026 Annual Town Meeting Combined Reports pp.8-8 to 8-9"),
        ("K_GenFY31", "General non-departmental, FY2031 (Town plan)", f"={dat('gen', 2031, True)}", USD,
         "Mostly stabilization and liability fund deposits, whose targets are shares of revenue, so it grows with net "
         "revenue after FY2031.", "Town long-range plan"),
        ("K_NonAppFY31", "Non-appropriated items, FY2031 (Town plan)", round(D["consts"]["non_approp_fy31"]), USD,
         "MBTA and county assessments (capped at 2.5% a year by law) and the overlay. Grows at K_NonAppG after FY2031.",
         "Town long-range plan"),
        ("K_ActShare", "Health plan: share of cost for active employees", 1 - D["consts"]["retiree_cost_share"], "0%",
         "Actives follow staffing; retirees grow on their own. Retirees are 49% of subscribers but 36% of cost "
         "(many are on Medicare supplement plans).",
         "FY2024 audit retiree benefit payments over FY2024 group health spending"),
        ("K_RetGrowth", "Health plan: yearly growth in retiree subscribers", D["consts"]["retiree_growth"], "0.00%",
         "1,459 in FY2011 to 1,659 in FY2025.", "Financial Plan subscriber tables"),
        ("K_OPEBStep", "Retiree health (OPEB) yearly increase if pension savings are kept", 250_000, USD,
         "The Town plan's own yearly step, FY2026 to FY2030.", "Town long-range plan"),
        ("K_PenNCPrem", "Pension normal cost growth above Town pay, after FY2031", D["consts"]["pension_nc_premium"], "0.00%",
         "The actuary's 3.5% payroll growth plus 0.15% for mortality improvement, against the 3.0% pay target.",
         "Brookline Retirement System 2024 valuation, funding schedule notes"),
        ("K_PenRate", "Pension system assumed return", D["consts"]["pension_rate"], "0.0%",
         "Used to spread FY2030's catch-up payment if full funding slips.", "Brookline Retirement System 2024 valuation"),
        ("K_DebtGrowth", "Debt within the levy, yearly growth after FY2032", 0.035, PCT1,
         "Close to revenue growth, as the capital policy ties capital to revenue.", "Forecast assumption"),
    ]),
    ("Police and fire", [
        ("K_Homes25", "Homes in town, FY2025", 28_718, NUM0, "2020 Census plus about 151 a year.", "Census"),
        ("K_FireHomes", "Homes at which a fire company is added", "=ROUND(161/5.16*1000,-2)", NUM0,
         "Brookline's 161 firefighters over the median of 21 nearby cities and towns, 5.16 per 1,000 homes.",
         "Peer staffing, 2020"),
        ("K_FireCost", "A fire company, 20 firefighters a year (FY2025 $, health included)", 3_038_292, USD,
         "20 at $123,639 plus $565,512 overtime at current leave rates.", "Fire Department overtime memo, March 2025, p.7"),
        ("K_PSShare", "Police and fire share of the Town cost of a new home", "=234/663", PCT1,
         "Cross-town estimate.", "350-town spending comparison"),
        ("K_PSPos", "One police or fire position a year (FY2025 $, health included)", 123_639, USD, "",
         "Fire Department overtime memo, March 2025"),
        ("K_PSRestoreN", "Positions restored: police to 136, fire to 168", "=(136-128)+(168-160)", NUM0,
         "Police at the FY2018 to FY2020 level, fire at the FY2004 level.", "Financial Plans"),
        ("K_FireSteps", "Fire contract: new 5- and 10-year steps, from FY2028 (FY2028 $)", 909_471, USD,
         "Agreed in the 2025 contract; grows with Public Safety pay after FY2028.", "ERSC Final Report, March 2026, pp.108-109"),
        ("K_PolRefill28", "Police positions refilled by FY2028", 2, NUM0,
         "Six positions held open to fund the contract are refilled with the override: two in FY2027 (in the budget), "
         "two more in each of FY2028 and FY2029. Already counted when staffing is restored.",
         "Advisory Committee report, May 2026 Combined Reports p.8-19"),
        ("K_PolRefill29", "Police positions refilled by FY2029", 4, NUM0, "", "Advisory Committee report, May 2026"),
        ("K_FCDeposit", "Free cash deposits: share of general non-departmental", D["consts"]["fc_deposit_share"], PCT1,
         "Stabilization, liability and housing trust deposits, FY2027: $6.75M of $8.48M.", "FY2027 budget as adopted"),
        ("K_FCReserve", "Free cash share of the reserve fund (of prior-year net revenue)", D["consts"]["fc_reserve_share"], "0.00%",
         "Free cash never pays for the operating budget; what is left after these uses goes to capital and one-time uses.",
         "Free Cash Policies, May 2026 Combined Reports p.8-8"),
        ("K_OpebRate", "Retiree health liability: interest (discount) rate", D["consts"]["opeb_rate"], "0.00%",
         "The trust's assumed return; the liability grows at this rate too.", "FY2024 audit, OPEB note p.84"),
        ("K_OpebTrendLong", "Retiree health: the actuary's long-run premium trend", D["consts"]["opeb_trend_long"], "0.00%",
         "The liability's service cost and benefits grow at the actuary's trend, not at the premium settings, which move the "
         "health insurance line only.", "FY2024 audit, OPEB note"),
        ("K_OpebTol27", "Retiree health total liability, June 30, 2027", round(D["consts"]["opeb_start"][0]), USD,
         "Rolled forward from the FY2024 audit ($301.8M) on the actuary's trend.", "FY2024 audit; this model"),
        ("K_OpebA27", "Retiree health trust, June 30, 2027", round(D["consts"]["opeb_start"][1]), USD,
         "FY2024 audit ($100.3M) plus deposits and 6.90% a year.", "FY2024 audit; this model"),
        ("K_OpebSC27", "Retiree health service cost, FY2027", round(D["consts"]["opeb_start"][2]), USD,
         "FY2024 audit ($8.5M), grown at the actuary's trend.", "FY2024 audit; this model"),
        ("K_OpebB27", "Retiree health benefits paid, FY2027", round(D["consts"]["opeb_start"][3]), USD,
         "FY2024 audit ($12.4M), grown at the actuary's trend and with retirees.", "FY2024 audit; this model"),
        ("K_PSSharePol", "Police part of the police and fire share", "=448/(448+532)", PCT1,
         "RKG's per-household police and fire costs for Brookline.", "RKG fiscal impact study, FY2025"),
        ("K_PolBudget", "Sworn police, FY2027 budget", 128, NUM0, "", "FY2027 Financial Plan"),
        ("K_PolRatio", "Police per 1,000 homes, median of nearby cities and towns", 4.42, "0.00",
         "Median of the 19 of 21 peers that report.", "FBI staffing data, 2019"),
    ]),
    ("Schools", [
        ("K_Staff26", "School staff, FY2026", 1264.1, NUM1,
         "DESE's count for 2025-26 as the School Department reports it; the adopted FY2027 budget's 22.1 fewer "
         "positions leave 1,242.0.", "FY27-29 PSB budget summary, Table 4"),
        ("K_SPS", "Schools: share of spending that is pay", 0.83, PCT1, "Pay and benefits paid from the school budget over its total.", "School budget, FY2024"),
        ("K_V", "Schools: share of spending that moves with enrollment", 0.67, PCT1,
         "RKG's incremental school budget, set with Town staff; the rest is buildings and administration.",
         "ERSC report, Appendix C"),
        ("K_Ratio2019", "Students per school staff member, FY2019", "=7855/1315.8", "0.000", "", "DESE"),
        ("K_SPH", "School-age children per added home", P_SPH, "0.0000",
         "RKG's per-bedroom rates applied to the mix of homes being built. The forecast adds apartments and "
         "condominiums, not age-restricted homes. Across Massachusetts, added homes have brought fewer public school "
         "students than this.", "RKG fiscal impact study"),
    ]),
    ("FY2027 budget as adopted", [
        ("A_TD", "Town departments", A27.TOWN_DEPARTMENTS, USD, "", "Annual Town Meeting, May 2026, Table 1"),
        ("A_Sch", "Schools", A27.SCHOOLS, USD, "", "Same"),
        ("A_GH", "Health insurance", A27.GROUP_HEALTH, USD, "", "Same"),
        ("A_Pen", "Pensions", A27.PENSIONS, USD, "", "Same"),
        ("A_OPEB", "Retiree health (OPEB)", A27.OPEB, USD, "", "Same"),
        ("A_OB", "Other benefits", "=99123428-A_Pen-A_GH-A_OPEB", USD, "All employee benefits less the three above.", "Same"),
        ("A_Debt", "Debt within the levy", "=49425313-35379833", USD, "All debt service less excluded debt.", "Same"),
        ("A_Other", "Capital, reserves and other", "=15614820+22409889+10792034+15000", USD,
         "General non-departmental, revenue-financed capital, non-appropriated and vocational education.", "Same"),
        ("A_OtherFunds", "Other available funds", A27.OTHER_AVAILABLE_FUNDS, USD, "", "Same"),
        ("A_FTEchg", "Change in school staff from FY2026", A27.SCHOOL_FTE_CHANGE_FROM_FY26, NUM1, "", "Same"),
    ]),
]
ar = 5
ASM_ROW = {}
for sec, items in A_SECTIONS:
    ar += 1
    asm.cell(ar, 1, sec).font = H2
    ar += 1
    for nm, lab, val, fmt, how, src in items:
        asm.cell(ar, 1, nm).font = NOTE
        asm.cell(ar, 2, lab).alignment = WRAP
        c = asm.cell(ar, 3, val)
        c.number_format = fmt
        if not (isinstance(val, str) and val.startswith("=")):
            c.font = BLUE
        asm.cell(ar, 4, how).alignment = WRAP
        asm.cell(ar, 5, src).alignment = WRAP
        name(nm, f"Assumptions!$C${ar}")
        ASM_ROW[nm] = ar
        ar += 1
# Chestnut Hill's revenue under each estimate, picked by the setting
ar += 1
asm.cell(ar, 1, "Chestnut Hill revenue once built, by estimate").font = H2
ar += 1
for j, lab in enumerate(["Estimate", "Residential share of the property tax", "Property tax a year, FY2025 dollars",
                         "Rooms tax and motor vehicle excise a year, FY2025 dollars", "How it is worked out"]):
    c = asm.cell(ar, 1 + j, lab)
    c.font, c.fill = BOLD, HEAD_FILL
ar += 1
CHCA_ROWS = [("approved", "=ROUND(266*1841088/265,0)+2696433", "=762120+ROUND(266*99375/265,0)",
              "RKG's residential tax per home for 266 homes, plus City Realty scenario 1's commercial tax (the one with the "
              "approved 200 rooms); rooms tax for 200 rooms plus RKG's excise per home.",
              "=ROUND(266*1841088/265,0)/(ROUND(266*1841088/265,0)+2696433)"),
             ("cr_avg", 5_408_241, 917_905, "Average of City Realty's three scenarios.", "=3030198/5408241"),
             ("rkg", 3_158_174, 480_435, "RKG's scenario.", "=1841088/3158174"),
             ("in_trend", 0, 0, "Counted inside the recent trend, so nothing added.", 0)]
c0r = ar
for code, pt, lr_, how, rshare in CHCA_ROWS:
    asm.cell(ar, 1, code).font = NOTE
    for col, v, fmt in ((2, rshare, PCT1), (3, pt, USD), (4, lr_, USD)):
        c = asm.cell(ar, col, v)
        c.number_format = fmt
        if not isinstance(v, str):
            c.font = BLUE
    asm.cell(ar, 5, how).alignment = WRAP
    ar += 1
c1r = ar - 1
asm.cell(ar, 1, "Used in this run (from the Chestnut Hill setting)").font = BOLD
asm.cell(ar, 3, f"=INDEX($C${c0r}:$C${c1r},MATCH(ChcaEstimate,$A${c0r}:$A${c1r},0))").number_format = USD
asm.cell(ar, 4, f"=INDEX($D${c0r}:$D${c1r},MATCH(ChcaEstimate,$A${c0r}:$A${c1r},0))").number_format = USD
name("ChcaProp", f"Assumptions!$C${ar}")
name("ChcaLR", f"Assumptions!$D${ar}")
asm.cell(ar, 2, f"=INDEX($B${c0r}:$B${c1r},MATCH(ChcaEstimate,$A${c0r}:$A${c1r},0))").number_format = PCT1
name("ChcaResShare", f"Assumptions!$B${ar}")
asm.column_dimensions["A"].width = 15
asm.column_dimensions["B"].width = 50
asm.column_dimensions["C"].width = 16
asm.column_dimensions["D"].width = 70
asm.column_dimensions["E"].width = 40
asm.freeze_panes = "C5"


# ================================================================= Settings
st = wb.create_sheet("Settings", 0)
title(st, "Settings",
      "Change the yellow cells; the Forecast sheet updates. Each setting matches a control on the Forecast "
      "Explorer, with the same choices. To return to the base case, copy the Base case column back into "
      "Your value.", 6)
st["A4"], st["B4"], st["C4"], st["D4"], st["E4"], st["F4"] = "Setting", "Your value", "Base case", "Allowed", "Works out to", "What it means"
for c in "ABCDEF":
    st[f"{c}4"].font = BOLD
    st[f"{c}4"].fill = HEAD_FILL
R = D["revenue"]
B = D["base"]
SET = [
    ("The big six", None),
    ("pay", "Pay raises compared with the base case", "range", 0.0, (-0.015, 0.02), PTS, "-1.5 to +2.0 points",
     "Moves every employee group's yearly raise by the same amount. The base case starts from the Town's 3.0% "
     "bargaining target, with schools and Public Safety above it (next group)."),
    ("opeb", "Pension savings after full funding", "select", "redirect", None, None, "Choose from the list",
     "The pension system reaches full funding in FY2030. The Town plans to use the money it stops paying toward "
     "pensions to pay down its retiree health (OPEB) liability instead. Once that is paid off, the base case keeps "
     "the money in the budget for a decision then; the second choice counts it as room."),
    ("staffing", "School staff as enrollment falls", "select", "half", None, None, "Choose from the list",
     "From FY2019 to FY2025 enrollment fell 10.6% and school staff 5.0%, about half as fast. The base case continues "
     "that pattern; students from new homes are staffed in full. The School Department's own plan holds staff at the "
     "FY2027 level."),
    ("premium_long", "Health premium growth, FY2030 on", "range", B["premium_long"], (0.05, 0.12), PCT1, "5% to 12%",
     "Yearly rise in health insurance premiums. The 25-year average is 6.5%; recent years ran 10 to 12%."),
    ("growth", "Property tax new growth, tenths of a point above the recent trend", "whole", 0, (-6, 13), "0", "-6 to 13",
     "Tax base added each year by construction, renovation and business equipment, as a share of last year's levy. "
     "0 is the recent trend; each step is a tenth of a percentage point."),
    ("homes", "New homes built", "select", "all", None, None, "Choose from the list",
     "Scales only the new-homes part of new growth (about a sixth of it), including any added growth above; "
     "renovation, commercial space and business equipment continue at their pace. The enrollment forecast is left "
     "as it is."),
    ("The next five", None),
    ("school_drift", "School pay above the Town target", "range", B["school_pay_drift"], (0, 0.025), PTS, "0 to 2.5 points",
     "The base case puts school pay 0.7 point above the Town target (3.7%). The schools' own forecast implies about 2 points."),
    ("ps_premium", "Public Safety pay above the Town target", "range", B["pay_ps_premium"], (0, 0.025), PTS, "0 to 2.5 points",
     "The base case puts Public Safety pay 0.5 point above the target (3.5%). Police and fire cost per position "
     "grew about 3.3% a year from FY2011 to FY2025; the agreed fire steps and police refills are counted on top."),
    ("lr", "Local receipts growth", "range", R["lr_cagr"], (0.01, 0.06), PCT2, "1% to 6%",
     "Fees, excise and other local revenue, apart from meals tax and building permits. Base: the FY2019 to FY2025 rate."),
    ("cpi", "Inflation", "range", B["cpi"], (0.015, 0.05), PCT2, "1.5% to 5%",
     "Price growth for everything that is not pay: supplies, utilities, contracts."),
    ("sa", "State aid growth", "range", R["sa_cagr"], (0, 0.06), PCT2, "0% to 6%",
     "Chapter 70 school aid and unrestricted local aid, from the adopted FY2027 figure. Base: 2.5%, the Town plan's rate."),
    ("Everything else", None),
    ("mix", "Where added growth comes from", "select", "mix", None, None, "Choose from the list",
     "Only matters when new growth is set above the recent trend. New homes add students and services; commercial "
     "space pays a higher tax rate and costs less to serve."),
    ("fill", "Students from added homes", "select", "staff", None, None, "Choose from the list",
     "Students from added homes can fill seats left open as enrollment falls: all of them with staff held at the "
     "FY2027 level, half of them with staff falling half as fast. Has no effect when staff follow enrollment fully."),
    ("enroll", "School enrollment forecast", "select", "nesdec", None, None, "Choose from the list",
     "Which enrollment path the schools serve."),
    ("premium_near", "Health premium growth, FY2028 and FY2029", "range", B["premium_near"], (0.06, 0.14), PCT1, "6% to 14%",
     "The Town's own forecast for the next two years."),
    ("np_extra", "School non-personnel costs above inflation", "range", B["sch_np_extra"], (0, 0.03), PTS, "0 to 3 points",
     "Special education placements and transportation have at times grown faster than prices in general."),
    ("capital", "Capital funding", "select", "full", None, None, "Choose from the list",
     "The Select Board's policy puts 6.6% of the prior year's net revenue into capital from FY2028; holding capital at the Town's six-year table's dollars comes to about 6% of this forecast's net revenue."),
    ("cost_home", "Town cost of serving a new home (FY2025 $)", "range", B["cost_per_home"], (200, 1200), USD, "$200 to $1,200",
     "Town department cost per added home a year, before schools. The forecast leaves out fire's share, about a fifth, "
     "since fire is counted in steps under Police and fire staffing, and police's share too when police grow with homes."),
    ("ps_staff", "Police and fire staffing", "select", "budget", None, None, "Choose from the list",
     "The FY2027 budget funds 128 sworn police and 160 firefighters. A fire company (20 firefighters) is added when the "
     "town reaches about 31,200 homes. Police growing with homes keeps 4.42 officers per 1,000 homes; restoring earlier "
     "staffing adds 16 positions from FY2028."),
    ("chca", "Chestnut Hill redevelopment", "select", "approved", None, None, "Choose from the list",
     "266 homes and a 200-room hotel, arriving FY2032 to FY2034. The estimates differ only in revenue."),
    ("slip", "Pension full funding slips", "select", 0, None, None, "Choose from the list",
     "If investment returns fall short, full pension contributions continue for longer."),
    ("ng2728", "New growth in FY2027 and FY2028", "select", "trend", None, None, "Choose from the list",
     "Building permits show new growth about two years ahead. The 2024 and 2025 permits point to real estate new "
     "growth well below the trend in FY2027 and FY2028; business equipment stays at its trend. The shortfall then "
     "carries through every later levy. The Explorer does not have this setting."),
    ("ov_amt", "A further override (first-year dollars)", "range", 0, (0, 30e6), USD, "$0 to $30,000,000",
     "An operating override added to the levy, growing 2.5% a year after. The forecast itself never assumes one."),
    ("ov_year", "First year of that override", "whole", 2031, (2029, 2035), YEARFMT, "2029 to 2035",
     "Only matters when the override above is more than zero."),
]
IN = {}          # control id -> input cell
row = 5
for item in SET:
    if item[1] is None:
        row += 1
        st.cell(row, 1, item[0]).font = H2
        row += 1
        continue
    cid, label, kind, base, rng, fmt, allowed, help_ = item
    st.cell(row, 1, label)
    if kind == "select":
        lab = dict((c, l) for c, l in OPTIONS[cid])[base]
        cell = st.cell(row, 2, lab)
        st.cell(row, 3, lab)
        dv = DataValidation(type="list", formula1=f"={OPT_RANGE[cid][0]}", allow_blank=False)
    else:
        cell = st.cell(row, 2, base)
        st.cell(row, 3, base).number_format = fmt
        cell.number_format = fmt
        dv = DataValidation(type="whole" if kind == "whole" else "decimal", operator="between",
                            formula1=str(rng[0]), formula2=str(rng[1]), allow_blank=False)
    dv.error, dv.errorTitle, dv.showErrorMessage = f"Allowed: {allowed}", "Out of range", True
    st.add_data_validation(dv)
    dv.add(cell)
    cell.fill = INPUT_FILL
    cell.border = INPUT_BORDER
    st.cell(row, 4, allowed)
    st.cell(row, 6, help_).alignment = WRAP
    st.cell(row, 1).alignment = WRAP
    IN[cid] = row
    name("In_" + cid, f"Settings!$B${row}")
    row += 1

# ---- how the model reads the settings (do not edit)
row += 1
st.cell(row, 1, "How the model reads these settings (worked out, do not edit)").font = H2
row += 1
st.cell(row, 1, "Each line turns a choice above into the value the Forecast sheet uses.").font = NOTE
row += 1


def code_of(cid):
    labs, codes = OPT_RANGE[cid]
    return f"INDEX({codes},MATCH(In_{cid},{labs},0))"


DERIVED = [
    ("PayTown", "Pay growth, Town staff", "K_BasePay+In_pay", PCT2),
    ("PSPrem", "Public Safety above the target", "In_ps_premium", PTS),
    ("SchDrift", "Schools above the target", "In_school_drift", PTS),
    ("PremLong", "Health premiums, FY2030 on", "In_premium_long", PCT2),
    ("PremNear", "Health premiums, FY2028 and FY2029", "In_premium_near", PCT2),
    ("Inflation", "Inflation", "In_cpi", PCT2),
    ("NPExtra", "School non-personnel above inflation", "In_np_extra", PTS),
    ("CostHome", "Town cost of a new home", "In_cost_home", USD),
    ("StateAidGrowth", "State aid growth", "In_sa", PCT2),
    ("ReceiptsGrowth", "Local receipts growth", "In_lr", PCT2),
    ("Redirect", "Pension savings move to OPEB (1 yes, 0 no)", f'IF({code_of("opeb")}="keep",0,1)', "0"),
    ("OpebHold", "Money freed by the OPEB payoff held for a decision (1 yes, 0 no)", f'IF({code_of("opeb")}="redirect",1,0)', "0"),
    ("RatioMode", "School staffing rule", code_of("staffing"), "@"),
    ("MixCode", "Growth mix", code_of("mix"), "@"),
    ("FillCap", "Students fill open seats (1 yes, 0 no)", f'IF({code_of("fill")}="fill",1,0)', "0"),
    ("HomesShare", "Share of expected new homes built", f'IF({code_of("homes")}="half",0.5,IF({code_of("homes")}="none",0,1))', "0%"),
    ("EnrollMode", "Enrollment path", code_of("enroll"), "@"),
    ("CapFull", "Capital at the full policy (1 yes, 0 no)", f'IF({code_of("capital")}="full",1,0)', "0"),
    ("ChcaEstimate", "Chestnut Hill estimate", code_of("chca"), "@"),
    ("NgEarlyYears", "New growth in FY2027 and FY2028", code_of("ng2728"), "@"),
    ("ChcaOn", "Chestnut Hill counted on top of trend (1 yes, 0 no)", 'IF(ChcaEstimate="in_trend",0,1)', "0"),
    ("PensionSlip", "Years pension full funding slips", code_of("slip"), "0"),
    ("FireStep", "Fire company added at the threshold (1 yes, 0 no)", f'IF({code_of("ps_staff")}="none",0,1)', "0"),
    ("PSRestore", "Police and fire restored to earlier staffing (1 yes, 0 no)", f'IF({code_of("ps_staff")}="restore",1,0)', "0"),
    ("PoliceStep", "Police grow with homes at the peer ratio (1 yes, 0 no)", f'IF({code_of("ps_staff")}="police",1,0)', "0"),
    ("GrowthStep", "New growth step, tenths of a point", "In_growth", "0"),
    ("GrowthRate", "New growth rate, share of last year's levy", "K_TrendRate+GrowthStep*0.001", PCT2),
    ("OvAmt", "Further override, first-year dollars", "In_ov_amt", USD),
    ("OvYear", "Further override, first year", "In_ov_year", YEARFMT),
]
for nm, label, f, fmt in DERIVED:
    st.cell(row, 1, label)
    c = st.cell(row, 2, "=" + f)
    c.number_format = fmt
    c.fill = WORK_FILL
    name(nm, f"Settings!$B${row}")
    row += 1
# "works out to" column
st.cell(IN["pay"], 5, "=PayTown").number_format = PCT2
st.cell(IN["school_drift"], 5, "=PayTown+SchDrift").number_format = PCT2
st.cell(IN["ps_premium"], 5, "=PayTown+PSPrem").number_format = PCT2
st.cell(IN["growth"], 5, "=GrowthRate").number_format = PCT2
for rr in (IN["pay"], IN["school_drift"], IN["ps_premium"], IN["growth"]):
    st.cell(rr, 5).fill = WORK_FILL
st.column_dimensions["A"].width = 52
st.column_dimensions["B"].width = 44
st.column_dimensions["C"].width = 44
st.column_dimensions["D"].width = 20
st.column_dimensions["E"].width = 13
st.column_dimensions["F"].width = 90
st.freeze_panes = "B5"


HEAD = 4


def yr(y):
    return f"{ycol(y)}${HEAD}"


# ================================================================= Revenue build
# Property tax and the revenue tied to growth, built up year by year. This replaces the grid
# of precomputed runs the Explorer looks up; scripts/workbook_validation checks that every
# growth setting, mix and Chestnut Hill estimate reproduces that grid.
rb = wb.create_sheet("Revenue build")
title(rb, "Revenue build: property tax and new growth",
      "How the levy grows: last year's levy limit plus 2.5%, plus new growth, plus any override. New growth comes in five "
      "kinds, each a share of last year's levy limit, set on Assumptions and moved by the New growth setting. For FY2026 "
      "to FY2031 the forecast starts from the Town's own plan and adds the difference its new growth makes over the "
      "Town's flat $2.5M; from FY2032 it carries the levy forward itself. Debt exclusions are shown but set aside on the "
      "Forecast sheet.", 17)
for y in YEARS:
    c = rb.cell(HEAD, FIRST_COL + YEARS.index(y), y)
    c.number_format = YEARFMT
    c.font, c.fill = BOLD, HEAD_FILL
# ---- the five new growth rates for this run, beside the recent trend
rr = HEAD + 2
rb.cell(rr, 1, "New growth rates, share of last year's levy limit").font = H2
rb.cell(rr, 3, "This run").font = BOLD
rb.cell(rr, 4, "Recent trend").font = BOLD
rr += 1
RATES = [("ResNew", "New homes", "K_ResNewPct", "housing"), ("ResReno", "Home renovation", "K_ResRenoPct", None),
         ("ComNew", "New commercial space", "K_ComNewPct", "commercial"), ("ComReno", "Commercial renovation", "K_ComRenoPct", None),
         ("PP", "Business equipment", "K_PP", None)]
for key, lab, trend, lever in RATES:
    rb.cell(rr, 1, lab)
    scaled = f"{trend}*GrowthRate/K_TrendRate"
    if lever:
        added = f"{trend}+(GrowthRate-K_TrendRate)*IF(MixCode=\"{lever}\",1,IF(MixCode=\"even\",0.5,0))"
        f = f"=IF(OR(GrowthStep<=0,MixCode=\"mix\"),{scaled},{added})"
    else:
        f = f"=IF(OR(GrowthStep<=0,MixCode=\"mix\"),{scaled},{trend})"
    if key == "ResNew":   # the new-homes setting scales this part only
        f = f"=({f[1:]})*HomesShare"
    c = rb.cell(rr, 3, f); c.number_format = "0.0000%"; c.fill = WORK_FILL
    rb.cell(rr, 4, f"={trend}").number_format = "0.0000%"
    name("Rate_" + key, f"'Revenue build'!$C${rr}")
    rr += 1
rb.cell(rr, 1, "All new growth").font = BOLD
rb.cell(rr, 3, f"=SUM(C{rr - 5}:C{rr - 1})").number_format = "0.0000%"
rb.cell(rr, 4, f"=SUM(D{rr - 5}:D{rr - 1})").number_format = "0.0000%"
rr += 1
rb.cell(rr, 1, "Below the trend every kind is scaled down together. Above it, today's mix scales every kind up; the other "
               "mixes add the extra to new homes, new commercial space, or half to each.").font = NOTE
rr += 2
BROW = {}
BORDER = []


def bplan(key, label, fmt=USD, section=None):
    BORDER.append((key, label, fmt, section))


bplan(None, "The levy, FY2026 to FY2031: the Town's plan plus the difference", section=True)
for k, l in [("plan_levy0", "Town plan: property tax less debt exclusions, before the May 2026 override"),
             ("ovcum", "May 2026 override, built up (each year's amount, then 2.5% a year)"),
             ("plan_levy", "Town plan levy limit with the override")]:
    bplan(k, l)
bplan(None, "New growth this year", section=True)
for k, l in [("base", "Last year's levy limit (this forecast's: the Town plan's plus the difference, through FY2031)"),
             ("ng_scale", "Scale to the Town's budgeted new growth (FY2027 only)"),
             ("ng_resnew", "New homes"), ("ng_resreno", "Home renovation"), ("ng_comnew", "New commercial space"),
             ("ng_comreno", "Commercial renovation"), ("ng_pp", "Business equipment"),
             ("chca_share", "Chestnut Hill: share built and on the roll"), ("chca_level", "Chestnut Hill: property tax once on the roll"),
             ("chca_inc", "Chestnut Hill: added this year, at its entry year's value"), ("ng", "New growth, all")]:
    bplan(k, l, "0.000" if k in ("chca_share", "ng_scale") else USD)
bplan(None, "Property tax", section=True)
for k, l in [("diff", "Difference from the Town plan's $2.5M a year, carried at 2.5% (FY2027 to FY2031; FY2026 is certified in both)"),
             ("levy", "Levy limit: Town plan plus the difference to FY2031, then last year plus 2.5% plus new growth"),
             ("dex", "Debt exclusion tax (Town plan, then held at FY2031)"), ("prop", "Property tax, all")]:
    bplan(k, l)
bplan(None, "Homes and commercial space the new growth stands for", section=True)
for k, l, f in [("val_home", "Assessed value of a new home", USD), ("rate_res", "Residential tax rate", "0.0000%"),
                ("rate_com", "Commercial tax rate", "0.0000%"), ("val_sqft", "Assessed value per commercial square foot", USD),
                ("units", "Homes added this year", NUM1), ("sqft", "Commercial square feet added this year", NUM0),
                ("re_ng", "Real-estate new growth (all but business equipment)", USD)]:
    bplan(k, l, f)
bplan(None, "Local receipts that grow with construction", section=True)
for k, l, f in [("permit_rate", "Building permit fee, share of construction cost", "0.0%"),
                ("permits", "Building permit fees (on the construction value behind this year's real-estate new growth)", USD),
                ("meals_org", "Meals tax at existing restaurants", USD),
                ("sqft_cum", "Commercial square feet added since FY2026", NUM0),
                ("meals_new", "Meals tax from new commercial space", USD),
                ("chca_lr", "Chestnut Hill: rooms tax and motor vehicle excise", USD),
                ("lr_growth", "Local receipts tied to growth", USD)]:
    bplan(k, l, f)
bplan(None, "Other available funds", section=True)
bplan("ofund", "Other available funds (Town plan; FY2027 adopted; override fund drawn FY2028 to FY2030; FY2031 level after)")
bplan(None, "The same at the recent trend, for comparison (the Explorer's planning staff and student counts need it)", section=True)
for k, l, f in [("t_base", "Last year's levy limit, trend", USD), ("t_ng", "New growth, all, trend", USD),
                ("t_diff", "Difference from the Town plan, trend", USD), ("t_levy", "Levy limit, trend", USD),
                ("t_units", "Homes added this year, trend", NUM1), ("t_re_ng", "Real-estate new growth, trend", USD)]:
    bplan(k, l, f)

for key, label, fmt, section in BORDER:
    if section:
        rr += 1
        rb.cell(rr, 1, label).font = H2
        rr += 1
        continue
    BROW[key] = (rr, label, fmt)
    rr += 1


def bat(key, y, absolute=False):
    row_ = BROW[key][0]
    return f"${ycol(y)}${row_}" if absolute else f"{ycol(y)}{row_}"


def brb(key, y):
    """The same cell, addressed from another sheet."""
    return f"'Revenue build'!{bat(key, y)}"


def pv(y):
    return YEARS[YEARS.index(y) - 1]


Y1, YL = YEARS[0], 2031          # first year; last year of the Town's plan
BF = {}
town = lambda y: y <= YL
BF["plan_levy0"] = lambda y: f"{dat('plan_prop', y)}-{dat('plan_dex', y)}" if town(y) else None
BF["ovcum"] = lambda y: (None if not town(y) else
                         (f"N({dat('ovr', y)})" if y == Y1 else f"{bat('ovcum', pv(y))}*(1+K_LevyCap)+N({dat('ovr', y)})"))
BF["plan_levy"] = lambda y: f"{bat('plan_levy0', y)}+{bat('ovcum', y)}" if town(y) else None
# new growth is measured against this forecast's own levy every year: through FY2031 that is the
# Town plan's levy plus the difference carried so far (2026-10-13)
BF["base"] = lambda y: ("Levy2025" if y == Y1 else bat("levy", pv(y)))
# FY2027 is held at the Town's budgeted new growth: every category scaled to that total
BF["ng_scale"] = lambda y: (f"K_TownNG/((Rate_ResNew+Rate_ResReno+Rate_ComNew+Rate_ComReno+Rate_PP)*{bat('base', y)})"
                            if y == 2027 else "1")
for k, rk in [("ng_resnew", "ResNew"), ("ng_resreno", "ResReno"), ("ng_comnew", "ComNew"), ("ng_comreno", "ComReno"), ("ng_pp", "PP")]:
    BF[k] = (lambda rk: lambda y: f"Rate_{rk}*{bat('base', y)}*{bat('ng_scale', y)}")(rk)
BF["chca_share"] = lambda y: f"IF({yr(y)}<K_ChcaStart,0,MIN(({yr(y)}-K_ChcaStart+1)/K_ChcaSpan,1))"
BF["chca_inc"] = lambda y: (f"{bat('chca_share', y)}*ChcaProp*" if y == Y1 else
                            f"({bat('chca_share', y)}-{bat('chca_share', pv(y))})*ChcaProp*") + (
    f"(ChcaResShare*((1+K_ResApp)*(1+K_LevyGrowth)/(1+K_BlendApp))^({yr(y)}-K_ChcaDollarYr)"
    f"+(1-ChcaResShare)*((1+K_ComApp)*(1+K_LevyGrowth)/(1+K_BlendApp))^({yr(y)}-K_ChcaDollarYr))")
BF["chca_level"] = lambda y: (bat("chca_inc", y) if y == Y1 else
                              f"{bat('chca_level', pv(y))}*(1+K_LevyCap)+{bat('chca_inc', y)}")
def _ng(y):
    trend = f"SUM({bat('ng_resnew', y)}:{bat('ng_pp', y)})+{bat('chca_inc', y)}"
    if y not in (2027, 2028):
        return trend
    k = "K_Perm27" if y == 2027 else "K_Perm28"
    permits = f'IF(NgEarlyYears="permits",{k},IF(NgEarlyYears="permits_low",{k}Lo,{k}Hi))+{bat("ng_pp", y)}+{bat("chca_inc", y)}'
    return f'IF(NgEarlyYears="trend",{trend},{permits})'


BF["ng"] = _ng
BF["diff"] = lambda y: (None if not town(y) else
                        ("0" if y == Y1 else f"{bat('diff', pv(y))}*(1+K_LevyCap)+({bat('ng', y)}-K_TownNG)"))
BF["levy"] = lambda y: (f"{bat('plan_levy', y)}+{bat('diff', y)}" if town(y)
                        else f"{bat('levy', pv(y))}*(1+K_LevyCap)+{bat('ng', y)}")
BF["dex"] = lambda y: dat("plan_dex", y) if town(y) else dat("plan_dex", YL, True)
BF["prop"] = lambda y: f"{bat('levy', y)}+{bat('dex', y)}"
BF["val_home"] = lambda y: f"K_ResValUnit*(1+K_ResApp)^({yr(y)}-2026)"
BF["rate_res"] = lambda y: f"K_ResTax*((1+K_LevyGrowth)/(1+K_BlendApp))^({yr(y)}-2026)"
BF["rate_com"] = lambda y: f"K_ComTax*((1+K_LevyGrowth)/(1+K_BlendApp))^({yr(y)}-2026)"
BF["val_sqft"] = lambda y: f"K_ComValSqft*(1+K_ComApp)^({yr(y)}-2026)"
BF["units"] = lambda y: f"{bat('ng_resnew', y)}/({bat('val_home', y)}*{bat('rate_res', y)})"
BF["sqft"] = lambda y: f"{bat('ng_comnew', y)}/({bat('val_sqft', y)}*{bat('rate_com', y)})"
BF["re_ng"] = lambda y: f"SUM({bat('ng_resnew', y)}:{bat('ng_comreno', y)})"
BF["permit_rate"] = lambda y: f"IF({yr(y)}>=2027,K_PermitRate27,K_PermitRate26)"
BF["permits"] = lambda y: (f"{bat('permit_rate', y)}*(({bat('ng_resnew', y)}+{bat('ng_resreno', y)})/{bat('rate_res', y)}"
                           f"+({bat('ng_comnew', y)}+{bat('ng_comreno', y)})/{bat('rate_com', y)})")
BF["meals_org"] = lambda y: f"K_Meals2025*(1+K_MealsGrowth)^({yr(y)}-2025)"
BF["sqft_cum"] = lambda y: f"SUM({bat('sqft', Y1, True)}:{bat('sqft', y)})"
BF["meals_new"] = lambda y: f"K_MealsPerSqft*{bat('sqft_cum', y)}"
BF["chca_lr"] = lambda y: f"ChcaLR*{bat('chca_share', y)}*(1+R_LRbase)^({yr(y)}-K_ChcaDollarYr)"
BF["lr_growth"] = lambda y: f"{bat('permits', y)}+{bat('meals_org', y)}+{bat('meals_new', y)}+{bat('chca_lr', y)}+K_InvFlat"
BF["ofund"] = lambda y: ((f"A_OtherFunds" if y == Y0 else f"{dat('plan_ofund', y)}+N({dat('stab', y)})") if town(y)
                         else bat("ofund", YL, True))
# recent trend: the same levy with the trend rates
BF["t_base"] = lambda y: ("Levy2025" if y == Y1 else bat("t_levy", pv(y)))
BF["t_ng"] = lambda y: ("K_TownNG" if y == 2027 else
                        f"(K_ResNewPct+K_ResRenoPct+K_ComNewPct+K_ComRenoPct+K_PP)*{bat('t_base', y)}+{bat('chca_inc', y)}")
BF["t_diff"] = lambda y: (None if not town(y) else
                          ("0" if y == Y1 else f"{bat('t_diff', pv(y))}*(1+K_LevyCap)+({bat('t_ng', y)}-K_TownNG)"))
BF["t_levy"] = lambda y: (f"{bat('plan_levy', y)}+{bat('t_diff', y)}" if town(y)
                          else f"{bat('t_levy', pv(y))}*(1+K_LevyCap)+{bat('t_ng', y)}")
BF["t_units"] = lambda y: f"K_ResNewPct*{bat('t_base', y)}/({bat('val_home', y)}*{bat('rate_res', y)})"
BF["t_re_ng"] = lambda y: f"(K_ResNewPct+K_ResRenoPct+K_ComNewPct+K_ComRenoPct)*{bat('t_base', y)}"

for key, (row_, label, fmt) in BROW.items():
    rb.cell(row_, 1, label).alignment = Alignment(wrap_text=False)
    for y in YEARS:
        f = BF[key](y)
        if f is None:
            continue
        c = rb.cell(row_, FIRST_COL + YEARS.index(y), "=" + f)
        c.number_format = fmt
    if key in ("ng", "levy", "prop", "lr_growth"):
        for col in range(1, FIRST_COL + len(YEARS)):
            rb.cell(row_, col).font = BOLD
rb.column_dimensions["A"].width = 70
rb.column_dimensions["B"].width = 2
for i in range(len(YEARS)):
    rb.column_dimensions[get_column_letter(FIRST_COL + i)].width = 14
rb.freeze_panes = rb.cell(HEAD + 1, FIRST_COL)


# ================================================================= Forecast
fc = wb.create_sheet("Forecast", 1)
title(fc, "Forecast, FY2027 to FY2040",
      "Revenue and spending of the General Fund, with voter-approved debt exclusions set aside on both sides. "
      "Everything here is a live formula driven by the Settings sheet, the Revenue build sheet and the Assumptions "
      "sheet. FY2026 appears only because the free cash cycle and new growth start from it.", 17)
fc.cell(HEAD, 1, "").font = BOLD
for y in YEARS:
    c = fc.cell(HEAD, FIRST_COL + YEARS.index(y), y)
    c.number_format = YEARFMT
    c.font = BOLD
    c.fill = HEAD_FILL
FROW = {}
ORDER = []


def plan(key, label, fmt=USD, section=None):
    ORDER.append((key, label, fmt, section))


# visible results first
plan(None, "Revenue", section=True)
for k, l in [("rv_prop", "Property tax (debt exclusions set aside)"), ("rv_sa", "State aid"),
             ("rv_lr", "Local receipts, as budgeted"), ("rv_fc", "Free cash"), ("rv_other", "Other available funds"),
             ("rv_ov", "A further override"), ("rev", "Total revenue")]:
    plan(k, l)
plan(None, "Spending", section=True)
for k, l in [("depBase", "Town departments, today's services"), ("depGrowth", "Town services for added homes and businesses"),
             ("sch", "Schools"), ("gh", "Health insurance"), ("gb", "Benefits for staff added by growth"),
             ("pen", "Pensions"), ("opeb", "Retiree health (OPEB)"), ("ob", "Other benefits"),
             ("debt", "Debt within the levy"), ("otherSp", "Capital, reserves and other"), ("spend", "Total spending")]:
    plan(k, l)
plan(None, "", section=True)
plan("room", "Room: revenue minus spending")
plan(None, "Context", section=True)
plan("E", "School enrollment served", NUM0)
plan("staff", "School staff", NUM1)
plan("homes", "Added homes since FY2027, including Chestnut Hill", NUM0)
plan("stock", "Homes in town, including Chestnut Hill", NUM0)
plan("company", "Fire company (included in Town services for growth)", USD)
plan("restore", "Police and fire: restored staffing if chosen, and commitments already agreed (in today's services)", USD)
plan("policeN", "Police officers added to hold the peer ratio", NUM0)
plan("police", "Police added (included in Town services for growth)", USD)
plan(None, "How the model works it out", section=True)
for k, l, f in [
    ("G_units", "Homes added that year (Revenue build)", NUM1), ("Gt_units", "Homes added that year at the recent trend (Revenue build)", NUM1),
    ("G_sqft", "Commercial square feet added that year (Revenue build)", NUM0), ("G_re", "Real-estate new growth (Revenue build)", USD),
    ("Gt_re", "Real-estate new growth at the recent trend (Revenue build)", USD), ("G_prop", "Property tax, all (Revenue build)", USD),
    ("G_dex", "Debt exclusion tax (Revenue build)", USD), ("G_ofund", "Other available funds (Revenue build)", USD),
    ("G_lr", "Local receipts tied to growth (Revenue build)", USD),
    ("units", "Homes added since FY2027", NUM1), ("unitsT", "Homes added since FY2027, recent trend", NUM1),
    ("sqft", "Commercial square feet added since FY2027", NUM0), ("ramp", "Chestnut Hill: share built and counted", "0.000"),
    ("W", "Pay index, Town staff (FY2027 = 1)", "0.0000"), ("Wps", "Pay index, Public Safety", "0.0000"),
    ("Wsch", "Pay index, schools", "0.0000"), ("Cidx", "Price index", "0.0000"),
    ("Cnp", "Price index, school non-personnel", "0.0000"), ("Prem", "Health premium index", "0.0000"),
    ("enroll", "Enrollment on the chosen path", NUM1), ("extra", "Students from growth above the trend", NUM1),
    ("ratio", "Students per staff member", "0.000"), ("sv", "Staff implied by the staffing rule", NUM1),
    ("payMix", "Town pay index, weighted for Public Safety", "0.0000"), ("emp", "Added commercial employees", NUM1),
    ("payroll", "Payroll index, Town and school staff, weighted by FY2027 pay", "0.0000"),
    ("penPlan", "Pensions on schedule (before any slip)", USD),
    ("fteTot", "Town and school staff", NUM1), ("subs", "Health plan subscribers index", "0.0000"),
    ("saY", "State aid", USD), ("actual", "Local receipts, actual", USD), ("ov", "Further override", USD),
    ("baseTotal", "Revenue before receipts and free cash", USD), ("budgeted", "Local receipts, budgeted", USD),
    ("fcash", "Free cash", USD), ("total", "Revenue including debt exclusion tax", USD),
    ("net", "Net revenue for the capital policy (less debt exclusions, free cash, non-appropriated items and any further override)", USD),
    ("surplus", "Year-end surplus (returns as free cash two years later)", USD),
    ("oSC", "Retiree health: service cost", USD), ("oB", "Retiree health: benefits paid (in group health)", USD),
    ("oTol", "Retiree health: total liability, end of year", USD), ("oA", "Retiree health: trust, end of year", USD),
    ("opebPlan", "Retiree health: planned deposit", USD), ("oDep", "Retiree health: deposit, stopping at the payoff", USD)]:
    plan(k, l, f)
plan(None, "Fixed values worked out once", section=True)
for k, l, f in [("E0", "FY2027 enrollment", NUM1), ("Staff0", "FY2027 school staff", NUM1),
                ("Ratio0", "FY2027 students per staff", "0.0000"), ("Target", "Students per staff a third back to FY2019", "0.0000"),
                ("FteTot0", "FY2027 Town and school staff", NUM1), ("W25", "Pay growth, FY2025 to FY2027", "0.0000"),
                ("PS25", "Public Safety pay growth, FY2025 to FY2027", "0.0000"),
                ("NC30", "Pension normal cost, FY2030 (FY2031's, one year back)", USD),
                ("SlipPay", "Pension slip: each installment of FY2030's catch-up", USD)]:
    plan("S_" + k, l, f)

rr = HEAD + 1
for key, label, fmt, section in ORDER:
    if section:
        rr += 1
        fc.cell(rr, 1, label).font = H2
        rr += 1
        continue
    FROW[key] = (rr, label, fmt)
    rr += 1
# scalar names
for k, nm in [("E0", "Enroll27"), ("Staff0", "Staff27"), ("Ratio0", "Ratio27"), ("Target", "RatioTarget"),
              ("FteTot0", "AllStaff27"), ("W25", "PayToFY27"), ("PS25", "PSPayToFY27"), ("NC30", "PenNC30"),
              ("SlipPay", "PenSlipPay")]:
    name(nm, f"Forecast!$C${FROW['S_' + k][0]}")


def at(key, y, absolute=False):
    """Address of row `key` in year y's column on Forecast."""
    row_ = FROW[key][0]
    return f"${ycol(y)}${row_}" if absolute else f"{ycol(y)}{row_}"


def prev(y):
    return YEARS[YEARS.index(y) - 1]


F = {}   # key -> function(y) -> formula (without "="), or None for blank
for k, src in [("G_units", "units"), ("Gt_units", "t_units"), ("G_sqft", "sqft"), ("G_re", "re_ng"), ("Gt_re", "t_re_ng"),
               ("G_prop", "prop"), ("G_dex", "dex"), ("G_ofund", "ofund"), ("G_lr", "lr_growth")]:
    # homes and square feet are carried as whole numbers, as the Python model writes them
    F[k] = (lambda src: lambda y: f"ROUND({brb(src, y)},0)" if src in ("units", "t_units", "sqft") else brb(src, y))(src)
# cumulative counts from FY2027 (engine: cum())
c0, c1 = ycol(YEARS[0]), ycol(Y0)
for k, src in [("units", "G_units"), ("unitsT", "Gt_units"), ("sqft", "G_sqft")]:
    F[k] = (lambda src: lambda y: f"MAX(SUM(${c0}{FROW[src][0]}:{at(src, y)})-SUM(${c0}${FROW[src][0]}:${c1}${FROW[src][0]}),0)")(src)
F["ramp"] = lambda y: f"ChcaOn*{brb('chca_share', y)}"
# indexes (engine: ip(); 1 through FY2027, compounding from FY2028)
for k, rate in [("W", "PayTown"), ("Wps", "(PayTown+PSPrem)"), ("Wsch", "(PayTown+SchDrift)"), ("Cidx", "Inflation"),
                ("Cnp", "(Inflation+NPExtra)"), ("Prem", f"IF(OR({{y}}=2028,{{y}}=2029),PremNear,PremLong)")]:
    def mk(k, rate):
        def f(y):
            if y == YEARS[0]:
                return "1"
            rt = rate.replace("{y}", yr(y))
            return f"IF({yr(y)}>={Y0 + 1},{at(k, prev(y))}*(1+{rt}),1)"
        return f
    F[k] = mk(k, rate)
F["enroll"] = lambda y: (f'IF(EnrollMode="cm",{dat("cm", y)},IF(AND(EnrollMode="flat",{yr(y)}>{Y0}),'
                         f'{dat("nes", Y0, True)},{dat("nes", y)}))')
F["extra"] = lambda y: f"MAX({at('units', y)}-{at('unitsT', y)},0)*K_SPH+K_ChcaUnits*{at('ramp', y)}*K_ChcaSPU"
F["E"] = lambda y: f"{at('enroll', y)}+{at('extra', y)}"
F["ratio"] = lambda y: f'IF(RatioMode="partial",Ratio27+(RatioTarget-Ratio27)*MIN(MAX(({yr(y)}-{Y0})/5,0),1),Ratio27)'
F["sv"] = lambda y: (f'IF(AND(FillCap=1,RatioMode="keep"),Staff27+MAX({at("E", y)}-Enroll27,0)/Ratio27,'
                     f'IF(RatioMode="keep",Staff27+{at("extra", y)}/Ratio27,'
                     f'IF(AND(FillCap=1,RatioMode="half"),Staff27+(0.5/K_V)*MIN({at("enroll", y)}-Enroll27,0)/Ratio27'
                     f'+MAX({at("enroll", y)}-Enroll27,0)/Ratio27'
                     f'+MAX({at("extra", y)}-0.5*MAX(Enroll27-{at("enroll", y)},0),0)/Ratio27,'
                     f'IF(RatioMode="half",Staff27+{at("extra", y)}/Ratio27+(0.5/K_V)*MIN({at("enroll", y)}-Enroll27,0)/Ratio27'
                     f'+MAX({at("enroll", y)}-Enroll27,0)/Ratio27,'
                     f'{at("E", y)}/{at("ratio", y)}))))')
F["staff"] = lambda y: f"Staff27*(1-K_V)+K_V*{at('sv', y)}"
F["S_E0"] = lambda y: at("enroll", Y0, True) if y == YEARS[0] else None
F["S_Staff0"] = lambda y: "K_Staff26+A_FTEchg" if y == YEARS[0] else None
F["S_Ratio0"] = lambda y: "Enroll27/Staff27" if y == YEARS[0] else None
F["S_Target"] = lambda y: "Ratio27+(K_Ratio2019-Ratio27)/3" if y == YEARS[0] else None
F["S_FteTot0"] = lambda y: "K_TownFTE+Staff27" if y == YEARS[0] else None
F["S_W25"] = lambda y: f"(1+PayTown)^({Y0}-2025)" if y == YEARS[0] else None
F["S_PS25"] = lambda y: f"(1+PayTown+PSPrem)^({Y0}-2025)" if y == YEARS[0] else None
F["S_NC30"] = lambda y: f"{dat('pen', 2031, True)}/(1+PayTown+K_PenNCPrem)" if y == YEARS[0] else None
F["S_SlipPay"] = lambda y: (f"IF(PensionSlip>0,({dat('pen', 2030, True)}-PenNC30)/((1-(1+K_PenRate)^(-(PensionSlip+1)))/(1-1/(1+K_PenRate))),0)"
                            if y == YEARS[0] else None)
F["stock"] = lambda y: f"K_Homes25+SUM(${c0}{FROW['G_units'][0]}:{at('G_units', y)})+K_ChcaUnits*{at('ramp', y)}"


def from_anchor(fn):
    return lambda y: fn(y) if y >= Y0 else None


F["payMix"] = from_anchor(lambda y: f"K_psD*{at('Wps', y)}+(1-K_psD)*{at('W', y)}")
F["company"] = from_anchor(lambda y: (f"IF(AND(FireStep=1,{at('stock', y)}>=K_FireHomes),K_FireCost*PSPayToFY27*{at('Wps', y)},0)"
                                      if y > Y0 else "0"))
def _restore(y):
    if y <= Y0:
        return "0"
    f = f"PSRestore*K_PSRestoreN*K_PSPos*PSPayToFY27*{at('Wps', y)}"
    if y >= 2028:   # the commitments already agreed
        refill = "K_PolRefill28" if y == 2028 else "K_PolRefill29"
        f += (f"+K_FireSteps*{at('Wps', y)}/{at('Wps', 2028, True)}"
              f"+(1-PSRestore)*{refill}*K_PSPos*PSPayToFY27*{at('Wps', y)}")
    return f


F["restore"] = from_anchor(_restore)
F["policeN"] = from_anchor(lambda y: (f"IF(PoliceStep=1,MAX(INT({at('stock', y)}*K_PolRatio/1000+1E-9)-K_PolBudget"
                                      f"-{'K_PolRefill29' if y >= 2029 else 'K_PolRefill28' if y == 2028 else '0'},0),0)"
                                      if y > Y0 else "0"))
F["police"] = from_anchor(lambda y: f"{at('policeN', y)}*K_PSPos*PSPayToFY27*{at('Wps', y)}")
F["depBase"] = from_anchor(lambda y: f"A_TD*(K_pD*{at('payMix', y)}+(1-K_pD)*{at('Cidx', y)})+{at('restore', y)}")
F["emp"] = from_anchor(lambda y: f"{at('sqft', y)}/K_SqftPerEmp+K_ChcaEmp*{at('ramp', y)}")
F["homes"] = from_anchor(lambda y: f"{at('units', y)}+K_ChcaUnits*{at('ramp', y)}")
F["depGrowth"] = from_anchor(lambda y: (
    f"({at('homes', y)}*CostHome*(1-K_PSShare*(FireStep*(1-K_PSSharePol)+PoliceStep*K_PSSharePol))+{at('emp', y)}*K_CostPerEmp)*PayToFY27*{at('W', y)}"
    + (f"+K_Permit*MAX({at('G_re', y)}/{at('Gt_re', y)}-1,0)*{at('W', y)}" if y > Y0 else "")
    + f"+{at('company', y)}+{at('police', y)}"))
F["sch"] = from_anchor(lambda y: (f"A_Sch*(K_SPS*{at('Wsch', y)}*{at('staff', y)}/Staff27"
                                  f"+(1-K_SPS)*{at('Cnp', y)}*((1-K_V)+K_V*{at('E', y)}/Enroll27))"))
F["fteTot"] = from_anchor(lambda y: f"K_TownFTE+{at('staff', y)}")
F["subs"] = from_anchor(lambda y: f"K_ActShare*{at('fteTot', y)}/AllStaff27+(1-K_ActShare)*(1+K_RetGrowth)^({yr(y)}-{Y0})")
F["gh"] = from_anchor(lambda y: f"A_GH*{at('subs', y)}*{at('Prem', y)}")
F["gb"] = from_anchor(lambda y: f"({at('depGrowth', y)}-{at('company', y)}-{at('police', y)})*K_BenLoad")


F["payroll"] = from_anchor(lambda y: (f"(A_TD*K_pD*{at('payMix', y)}+A_Sch*K_SPS*{at('Wsch', y)}*{at('staff', y)}/Staff27)"
                                      f"/(A_TD*K_pD+A_Sch*K_SPS)"))
F["penPlan"] = from_anchor(lambda y: "A_Pen" if y == Y0 else (dat("pen", y) if y <= 2031 else
                           f"{dat('pen', 2031, True)}*(1+PayTown+K_PenNCPrem)^({yr(y)}-2031)"))


def _slip_on(y):
    return f"AND(PensionSlip>0,{yr(y)}>=2030,{yr(y)}<=2030+PensionSlip)"


def pen(y):
    if y == Y0:
        return "A_Pen"
    if y < 2030:
        return at("penPlan", y)
    slip_pen = f"{'PenNC30' if y == 2030 else at('penPlan', y)}+PenSlipPay"
    return f"IF({_slip_on(y)},{slip_pen},{at('penPlan', y)})"


def opeb_plan(y):
    if y == Y0:
        return "A_OPEB"
    if y <= 2030:
        base = dat("opeb", y)
    elif y == 2031:
        base = f"IF(Redirect=1,{dat('opeb', 2031, True)},{dat('opeb', 2030, True)}+K_OPEBStep*({yr(y)}-2030))"
    else:
        base = f"IF(Redirect=1,{dat('opeb', 2031, True)},{dat('opeb', 2030, True)}+K_OPEBStep*({yr(y)}-2030))"
    if y >= 2030:   # with a slip, the set-aside not paid to the pension goes to retiree health
        base = f"{base}+IF(AND({_slip_on(y)},Redirect=1),{at('penPlan', y)}-{at('pen', y)},0)"
    return base


def opeb(y):
    # the deposit stops once the liability is paid off; in the base case the budget keeps the
    # planned amount, held for a decision (2026-10-15)
    if y == Y0:
        return "A_OPEB"
    return f"IF(AND(OpebHold=1,Redirect=1),{at('opebPlan', y)},{at('oDep', y)})"


def opeb_dep(y):
    if y == Y0:
        return "A_OPEB"
    return f"MIN({at('opebPlan', y)},MAX({at('oTol', y)}-{at('oA', prev(y))}*(1+K_OpebRate),0))"


def _otrend(y):
    return dat("otr", y) if str(y) in D["consts"]["opeb_trend"] and y >= 2028 else "K_OpebTrendLong"


# the liability follows the actuary's healthcare trend, not the premium settings (2026-10-14)
F["oSC"] = from_anchor(lambda y: "K_OpebSC27" if y == Y0 else f"{at('oSC', prev(y))}*(1+{_otrend(y)})")
F["oB"] = from_anchor(lambda y: "K_OpebB27" if y == Y0 else f"{at('oB', prev(y))}*(1+{_otrend(y)})*(1+K_RetGrowth)")
F["oTol"] = from_anchor(lambda y: "K_OpebTol27" if y == Y0 else
                        f"{at('oTol', prev(y))}*(1+K_OpebRate)+{at('oSC', y)}-{at('oB', y)}")
F["oA"] = from_anchor(lambda y: "K_OpebA27" if y == Y0 else f"MIN({at('oA', prev(y))}*(1+K_OpebRate)+{at('oDep', y)},{at('oTol', y)})")


def ob(y):
    if y == Y0:
        return "A_OB"
    if y <= 2031:
        return dat("ob", y)
    return f"{dat('ob', 2031, True)}*{at('payroll', y)}/{at('payroll', 2031, True)}"


def debt(y):
    if y == Y0:
        return "A_Debt"
    if y <= 2032:
        return dat("debt", y)
    return f"{dat('debt', 2032, True)}*(1+K_DebtGrowth)^({yr(y)}-2032)"


def other(y):
    if y == Y0:
        return "A_Other"
    f = (f"{dat('other', y)}+IF(CapFull=1,MAX(K_CIP*{at('net', prev(y))}-{at('debt', y)}-{dat('cip', y)},0),0)"
         f"+K_Reserve*{at('net', prev(y))}-{dat('resf', min(y, 2031))}")
    if y > 2031:
        f += (f"+K_GenFY31*({at('net', prev(y))}/{at('net', 2030, True)}-1)"
              f"+K_NonAppFY31*((1+K_NonAppG)^({yr(y)}-2031)-1)")
    gen = dat("gen", y) if y <= 2031 else f"K_GenFY31*{at('net', prev(y))}/{at('net', 2030, True)}"
    f += (f"+{at('fcash', y)}-({dat('cipfc', y)}+K_FCDeposit*{gen}+K_FCReserve*{at('net', prev(y))})")
    return f


F["opebPlan"], F["oDep"] = from_anchor(opeb_plan), from_anchor(opeb_dep)
F["pen"], F["opeb"], F["ob"], F["debt"], F["otherSp"] = (from_anchor(pen), from_anchor(opeb), from_anchor(ob),
                                                         from_anchor(debt), from_anchor(other))
SP_KEYS = ["depBase", "depGrowth", "sch", "gh", "gb", "pen", "opeb", "ob", "debt", "otherSp"]
F["spend"] = from_anchor(lambda y: "+".join(at(k, y) for k in SP_KEYS))
# revenue, every year (FY2026 feeds FY2028's free cash)
F["saY"] = lambda y: "R_SA2026" if y <= 2026 else f"R_SA2027*(1+StateAidGrowth)^({yr(y)}-2027)"
F["actual"] = lambda y: f"{at('G_lr', y)}+R_LRresid2025*(1+ReceiptsGrowth)^({yr(y)}-2025)"
F["ov"] = lambda y: f"IF(AND(OvAmt>0,{yr(y)}>=OvYear),OvAmt*(1+K_LevyCap)^({yr(y)}-OvYear),0)"
F["baseTotal"] = lambda y: f"{at('G_prop', y)}+{at('saY', y)}+{at('G_ofund', y)}+{at('ov', y)}"
adopted_abr = [int(k) for k in D["revenue"]["adopted_budgeted_receipts"]]
F["budgeted"] = lambda y: dat("abr", y) if y in adopted_abr else f"{at('actual', y)}*R_BudgetRatio"
known_fc = list(D["revenue"]["known_fc_years"])
F["fcash"] = lambda y: dat("fc", y) if y in known_fc else f"R_ApprShare*{at('surplus', YEARS[YEARS.index(y) - 2])}"
F["total"] = lambda y: f"{at('baseTotal', y)}+{at('budgeted', y)}+{at('fcash', y)}"
F["net"] = lambda y: f"{at('total', y)}-{at('G_dex', y)}-{at('fcash', y)}-{at('ov', y)}-K_NonApp*(1+K_NonAppG)^({yr(y)}-2027)"
F["surplus"] = lambda y: f"({at('actual', y)}-{at('budgeted', y)})+R_OtherSurplus*({at('baseTotal', y)}+{at('actual', y)})"
F["rev"] = from_anchor(lambda y: f"{at('total', y)}-{at('G_dex', y)}")
F["rv_prop"] = from_anchor(lambda y: f"{at('G_prop', y)}-{at('G_dex', y)}")
F["rv_sa"] = from_anchor(lambda y: at("saY", y))
F["rv_lr"] = from_anchor(lambda y: at("budgeted", y))
F["rv_fc"] = from_anchor(lambda y: at("fcash", y))
F["rv_other"] = from_anchor(lambda y: at("G_ofund", y))
F["rv_ov"] = from_anchor(lambda y: at("ov", y))
F["room"] = from_anchor(lambda y: f"{at('rev', y)}-{at('spend', y)}")

for key, (row_, label, fmt) in FROW.items():
    fc.cell(row_, 1, label)
    for y in YEARS:
        f = F[key](y)
        if f is None:
            continue
        c = fc.cell(row_, FIRST_COL + YEARS.index(y), "=" + f)
        c.number_format = fmt
    if key in ("rev", "spend", "room"):
        for col in range(1, FIRST_COL + len(YEARS)):
            fc.cell(row_, col).font = BOLD
    if key == "room":
        for col in range(1, FIRST_COL + len(YEARS)):
            fc.cell(row_, col).fill = ROOM_FILL
GREEN = Font(name="Calibri", color="008000")
for k in ("G_units", "Gt_units", "G_sqft", "G_re", "Gt_re", "G_prop", "G_dex", "G_ofund", "G_lr"):
    for y in YEARS:
        fc.cell(FROW[k][0], FIRST_COL + YEARS.index(y)).font = GREEN
working_start = FROW["G_units"][0]
for row_ in range(working_start, FROW["S_PS25"][0] + 1):
    for col in range(FIRST_COL, FIRST_COL + len(YEARS)):
        if fc.cell(row_, col).value is not None:
            fc.cell(row_, col).fill = WORK_FILL
room_rng = f"{ycol(Y0)}{FROW['room'][0]}:{ycol(YEARS[-1])}{FROW['room'][0]}"
fc.conditional_formatting.add(room_rng, CellIsRule(operator="lessThan", formula=["0"],
                                                   font=Font(color="9C0006", bold=True),
                                                   fill=PatternFill("solid", fgColor="FFC7CE")))
fc.column_dimensions["A"].width = 52
fc.column_dimensions["B"].width = 2
for i in range(len(YEARS)):
    fc.column_dimensions[get_column_letter(FIRST_COL + i)].width = 14
fc.freeze_panes = fc.cell(HEAD + 1, FIRST_COL)


# ================================================================= Worked example
# One year followed by hand, every number a live cell, so a reader can check the arithmetic
# the Forecast and Revenue build sheets repeat for every year.
WY = 2033
we = wb.create_sheet("Worked example")
title(we, f"Worked example: FY{WY}, step by step",
      f"FY{WY} is the first full year after the Town's plan ends, so the levy is carried forward by the forecast alone. "
      "Each value is a live cell: change a setting and this page follows. The last column says where the same step is "
      "done for every year.", 4)
for j, lab in enumerate(["Step", "Value", "How", "Where every year is done"]):
    c = we.cell(4, 1 + j, lab)
    c.font, c.fill = BOLD, HEAD_FILL
fy_ = lambda k, y=WY: f"Forecast!{at(k, y)}"
rbx = lambda k, y=WY: brb(k, y)
WSTEPS = [
    ("Property tax", None, None, None),
    (f"Levy limit, FY{WY - 1}", "=" + rbx("levy", WY - 1), "Debt exclusions set aside.", "Revenue build"),
    ("Plus 2.5%", f"=B6*K_LevyCap", "Proposition 2½.", "Revenue build"),
    ("Plus new growth: new homes", "=" + rbx("ng_resnew"), "=\"Rate \"&TEXT(Rate_ResNew,\"0.000%\")&\" of last year's levy limit\"", "Revenue build"),
    ("Plus new growth: home renovation", "=" + rbx("ng_resreno"), "=\"Rate \"&TEXT(Rate_ResReno,\"0.000%\")", "Revenue build"),
    ("Plus new growth: new commercial space", "=" + rbx("ng_comnew"), "=\"Rate \"&TEXT(Rate_ComNew,\"0.000%\")", "Revenue build"),
    ("Plus new growth: commercial renovation", "=" + rbx("ng_comreno"), "=\"Rate \"&TEXT(Rate_ComReno,\"0.000%\")", "Revenue build"),
    ("Plus new growth: business equipment", "=" + rbx("ng_pp"), "=\"Rate \"&TEXT(Rate_PP,\"0.000%\")", "Revenue build"),
    ("Plus Chestnut Hill added this year", "=" + rbx("chca_inc"), "Fully built by FY2034.", "Revenue build"),
    (f"Levy limit, FY{WY}", "=SUM(B6:B13)", "", "Revenue build"),
    ("Check: same as Revenue build", f"=B14-{rbx('levy')}", "Should be 0.", ""),
    ("Homes the new-homes growth stands for", f"=B8/({rbx('val_home')}*{rbx('rate_res')})",
     f"=\"New homes growth / (value of a new home \"&TEXT({rbx('val_home')},\"$#,##0\")&\" x residential tax rate \"&TEXT({rbx('rate_res')},\"0.000%\")&\")\"",
     "Revenue build"),
    ("Revenue", None, None, None),
    ("Property tax, debt exclusions set aside", "=" + fy_("rv_prop"), "The levy limit above.", "Forecast"),
    ("State aid", "=" + fy_("rv_sa"), f"=\"FY2027 state aid grown \"&TEXT(StateAidGrowth,\"0.00%\")&\" a year\"", "Forecast"),
    ("Local receipts, as budgeted", "=" + fy_("rv_lr"),
     "=\"Receipts not tied to growth, grown \"&TEXT(ReceiptsGrowth,\"0.00%\")&\" a year, plus permits and meals tax; budgeted at \"&TEXT(R_BudgetRatio,\"0%\")&\" of what is collected\"",
     "Forecast"),
    ("Free cash", "=" + fy_("rv_fc"), "=\"The surplus of FY" + str(WY - 2) + " times \"&TEXT(R_ApprShare,\"0%\")", "Forecast"),
    ("Other available funds and any further override", f"={fy_('rv_other')}+{fy_('rv_ov')}", "", "Forecast"),
    ("Total revenue", "=SUM(B18:B22)", "", "Forecast"),
    ("Spending", None, None, None),
    ("Town departments, today's services", "=" + fy_("depBase"),
     f"=\"FY2027 budget x (\"&TEXT(K_pD,\"0%\")&\" pay x pay index \"&TEXT({fy_('payMix')},\"0.000\")&\" + the rest x price index \"&TEXT({fy_('Cidx')},\"0.000\")&\")\"",
     "Forecast"),
    ("Town services for added homes and businesses", "=" + fy_("depGrowth"),
     f"=TEXT({fy_('homes')},\"#,##0\")&\" homes added since FY2027 at \"&TEXT(CostHome,\"$#,##0\")&\" (FY2025 $, less fire's share, which comes as a company), plus any fire company and police steps\"",
     "Forecast"),
    ("Schools", "=" + fy_("sch"),
     f"=\"FY2027 budget: pay part x pay index x staff \"&TEXT({fy_('staff')},\"#,##0\")&\" / \"&TEXT(Staff27,\"#,##0\")&\"; the rest x prices, two thirds moving with enrollment \"&TEXT({fy_('E')},\"#,##0\")",
     "Forecast"),
    ("Health insurance", "=" + fy_("gh"),
     f"=\"FY2027 budget x subscribers \"&TEXT({fy_('subs')},\"0.000\")&\" x premiums \"&TEXT({fy_('Prem')},\"0.000\")",
     "Forecast"),
    ("Pensions, retiree health, other benefits", f"={fy_('pen')}+{fy_('opeb')}+{fy_('ob')}+{fy_('gb')}",
     "Town schedules to FY2031, then with payroll; benefits for staff added by growth.", "Forecast"),
    ("Debt within the levy; capital, reserves and other", f"={fy_('debt')}+{fy_('otherSp')}", "", "Forecast"),
    ("Total spending", "=SUM(B25:B30)", "", "Forecast"),
    ("Room: revenue minus spending", "=B23-B31", "", "Forecast"),
    ("Check: same as Forecast", f"=B32-{fy_('room')}", "Should be 0.", ""),
]
wr = 5
for lab, val, how, where in WSTEPS:
    if val is None:
        we.cell(wr, 1, lab).font = H2
        wr += 1
        continue
    we.cell(wr, 1, lab)
    c = we.cell(wr, 2, val)
    c.number_format = NUM0 if lab.startswith("Homes the") else USD
    we.cell(wr, 3, how).alignment = WRAP
    we.cell(wr, 4, where).font = NOTE
    if lab.startswith(("Levy limit, FY" + str(WY), "Total", "Room")):
        we.cell(wr, 1).font = we.cell(wr, 2).font = BOLD
    wr += 1
we.column_dimensions["A"].width = 46
we.column_dimensions["B"].width = 18
we.column_dimensions["C"].width = 100
we.column_dimensions["D"].width = 24


# ================================================================= Checks
def engine_base_run():
    js = (f"const D=require({json.dumps(str(DATA_FILE))});"
          f"const {{runModel}}=require({json.dumps(str(ENGINE))});"
          "const r=runModel(D,Object.assign({},D.base),{});"
          "console.log(JSON.stringify({years:r.years,room:r.room,revenue:r.revenue,spending:r.spending}));")
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)


ER = engine_base_run()
ck = wb.create_sheet("Checks", 3)
title(ck, "Checks against the Forecast Explorer",
      "The Explorer's own engine, run for the base case, beside this workbook's Forecast sheet. With every "
      "setting at its base case the gaps should all be within $5 a year; red marks a larger gap. If you change "
      "a setting, the gaps will show the effect of your change instead.", 17)
for y in YEARS:
    if y < Y0:
        continue
    c = ck.cell(4, FIRST_COL + YEARS.index(y), y)
    c.number_format = YEARFMT
    c.font = BOLD
    c.fill = HEAD_FILL
rows_ck = [("Explorer engine: total revenue", "revenue"), ("Explorer engine: total spending", "spending"),
           ("Explorer engine: room", "room")]
r0 = 5
for i, (label, k) in enumerate(rows_ck):
    ck.cell(r0 + i, 1, label)
    for j, y in enumerate(ER["years"]):
        ck.cell(r0 + i, FIRST_COL + YEARS.index(y), ER[k][j]).number_format = USD
gap_rows = []
for i, (label, k, fkey) in enumerate([("Gap: total revenue", "revenue", "rev"), ("Gap: total spending", "spending", "spend"),
                                      ("Gap: room", "room", "room")]):
    rr_ = r0 + 4 + i
    ck.cell(rr_, 1, label).font = BOLD
    for y in ER["years"]:
        col = ycol(y)
        ck.cell(rr_, FIRST_COL + YEARS.index(y), f"=Forecast!{col}{FROW[fkey][0]}-{col}{r0 + i}").number_format = '"$"#,##0.00;[Red]-"$"#,##0.00'
    gap_rows.append(rr_)
rng = f"{ycol(Y0)}{gap_rows[0]}:{ycol(YEARS[-1])}{gap_rows[-1]}"
ck.conditional_formatting.add(rng, FormulaRule(formula=[f"ABS({ycol(Y0)}{gap_rows[0]})>5"],
                                               fill=PatternFill("solid", fgColor="FFC7CE"), font=Font(color="9C0006")))
ck.cell(gap_rows[-1] + 2, 1, "Largest gap, any year").font = BOLD
ck.cell(gap_rows[-1] + 2, 3, f"=MAX(MAX({rng}),-MIN({rng}))").number_format = '"$"#,##0.00'
ck.column_dimensions["A"].width = 40
for i in range(len(YEARS)):
    ck.column_dimensions[get_column_letter(FIRST_COL + i)].width = 14


# ================================================================= Start here
sh = wb.create_sheet("Start here", 0)
sh["A1"] = "Brookline's finances to 2040: the forecast as a spreadsheet"
sh["A1"].font = TITLE
LINES = [
    ("What this is", None),
    ("This workbook is the Forecast Explorer (brooklinefuture.org/forecast/explorer) in spreadsheet form. It runs the "
     "same forecast, from the same numbers, with every step a formula you can follow.", None),
    ("How to use it", None),
    ("1. Go to Settings and change any yellow cell. Each setting is a control on the Explorer, with the same choices.", None),
    ("2. Read the result on Forecast: revenue, spending and the room (revenue minus spending) for every year to FY2040. "
     "A negative room means spending runs ahead of revenue that year.", None),
    ("3. To start over, copy the Base case column on Settings back into Your value.", None),
    ("The sheets", None),
    ("Settings: the 23 settings, their base case values and allowed ranges, and, below them, how the model reads each one.", None),
    ("Forecast: the results at the top, then every working step the model takes, row by row, in the order the Explorer's "
     "engine takes them.", None),
    ("Revenue build: property tax year by year. Last year's levy limit, plus 2.5%, plus new growth in five kinds, plus the "
     "May 2026 override; then the homes and commercial space that new growth stands for, and the permit fees and meals tax "
     "that come with it.", None),
    ("Worked example: one year, FY2033, followed step by step from the levy to the room, every number a live cell.", None),
    ("Assumptions: every fixed number the forecast uses, with how it is worked out and its source. Black values are formulas "
     "over the History sheet or published figures; blue values are typed from the source named.", None),
    ("History: the Town's record, FY2005 to FY2025, that the measured assumptions are averaged from.", None),
    ("Data: the Town's own year-by-year schedules (its January 2026 long-range plan, the FY2027 budget as adopted, the "
     "May 2026 override) and the two enrollment forecasts. Nothing there needs editing.", None),
    ("Versus the Town's plan: the step-by-step walk from the Town's January 2026 plan, a deficit in FY2031, to the "
     "base case's room that year.", None),
    ("Checks: the Explorer's engine, run for the base case, beside this workbook. With base settings every gap is within $5 a year.", None),
    ("Appendix sheets: the FY2005 to FY2025 history from the earlier workbook, for reference.", None),
    ("What is typed in rather than calculated", None),
    ("Figures read from documents: the Town's long-range plan and adopted budget, tax rates, fee schedules, the Fire "
     "Department's costing, RKG's study and the enrollment forecasts. Each is in blue on Assumptions or Data with its source. "
     "Everything else is a formula.", None),
    ("How it was checked", None),
    ("Every year's revenue, spending and room were recalculated with a formula engine and compared with the Explorer's own "
     "engine for the base case and for scenarios that move every setting at least once. All matched within $5 a year. The "
     "Revenue build was also checked against the Python revenue model for every growth setting, mix and Chestnut Hill "
     "estimate.", None),
    ("The forecast's method was also run backward over FY2011 to FY2025, given what actually happened to staffing, "
     "enrollment and prices: it came within about 4% of what Town departments actually spent in FY2025, and within 6% for "
     "schools.", None),
    ("Debt exclusions", None),
    ("Voter-approved debt exclusions run through the General Fund but pay for nothing except their own building debt, so "
     "the forecast sets them aside on both the revenue and the spending side; they would add the same amount to each.", None),
]
rr = 3
for text, _ in LINES:
    c = sh.cell(rr, 1, text)
    if len(text) < 45:
        c.font = H2
        rr += 1 if rr == 3 else 0
    else:
        c.alignment = WRAP
        sh.row_dimensions[rr].height = 15 * (1 + len(text) // 120)
    rr += 1
sh.column_dimensions["A"].width = 120


# ================================================================= Versus the Town's plan
# The step-by-step walk from the Town's January 2026 plan to the base case, FY2031: the same table as
# the method page (docs/site/pages/topic-forecast.md), read from it so the two never drift (Ben, 2026-10-13).
import re as _re
_FACTS = json.loads((ROOT / "output" / "site_facts.json").read_text())
_md = (ROOT / "docs" / "site" / "pages" / "topic-forecast.md").read_text()
_sec = _md[_md.index("## From the Town's plan to the base case"):]
_rows = [ln for ln in _sec.split("\n") if ln.startswith("| ")][2:]
_rows = _rows[:next(i for i, ln in enumerate(_rows) if ln.startswith("| End")) + 1]


def _plain(t):
    t = _re.sub(r"\{\{fact:([a-z0-9_]+)\}\}", lambda m: _FACTS[m.group(1)], t)
    t = _re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    return t.replace("**", "").replace("&minus;", "\u2212").strip()


vt = wb.create_sheet("Versus the Town's plan", 4)
title(vt, "From the Town's plan to the base case, FY2031",
      "The Town's long-range plan (January 2026) ends in FY2031 with a deficit; the base case has room that year. "
      "Starting from the Town's plan, each row applies one difference in turn. Dollars a year; a deficit is negative. "
      "The same walk is on the website's method page and in the Explorer.", 4)
for j, lab in enumerate(["Step", "What differs", "Change", "Running balance"]):
    c = vt.cell(4, 1 + j, lab)
    c.font, c.fill = BOLD, HEAD_FILL
for i, ln in enumerate(_rows):
    cells = [_plain(x) for x in ln.strip().strip("|").split("|")]
    for j, v in enumerate(cells[:4]):
        c = vt.cell(5 + i, 1 + j, v)
        c.alignment = WRAP
        if j >= 2:
            c.alignment = Alignment(horizontal="right", vertical="top")
    if cells[0] in ("Start", "End"):
        for j in range(4):
            vt.cell(5 + i, 1 + j).font = BOLD
    vt.row_dimensions[5 + i].height = 15 * (1 + len(cells[1]) // 70)
r_ = 5 + len(_rows) + 1
for para in ("Steps 1 and 4, the override that passed after the Town's plan was written and school pay, are most of "
             "the difference. The other steps are each a few million dollars a year.",
             "Through FY2031 the forecast starts from the Town's plan itself and changes only what differs: its levy "
             "is the Town's plus the extra new growth carried forward, measured against that larger levy; its spending "
             "is the Town's FY2027 budget moved by the forecast's own drivers."):
    c = vt.cell(r_, 1, para); c.alignment = WRAP
    vt.merge_cells(start_row=r_, start_column=1, end_row=r_, end_column=4)
    vt.row_dimensions[r_].height = 48
    r_ += 1
for col, w in zip("ABCD", (28, 90, 12, 16)):
    vt.column_dimensions[col].width = w
vt.freeze_panes = "A5"


# ================================================================= Appendix (history)
def copy_sheet(src, title_text, note, max_col=None, drop_rows=(), relabel=None):
    ws = wb.create_sheet(title_text)
    relabel = relabel or {}
    last_col = max_col or src.max_column
    out_r = 0
    for r_ in range(1, src.max_row + 1):
        if r_ in drop_rows:
            continue
        out_r += 1
        for c_ in range(1, last_col + 1):
            sc = src.cell(r_, c_)
            v = sc.value
            if r_ == 3 and c_ == 1:
                v = note
            if c_ == 1 and isinstance(v, str) and v in relabel:
                v = relabel[v]
            tc = ws.cell(out_r, c_, v)
            if sc.has_style:
                tc.font, tc.fill, tc.border = copy(sc.font), copy(sc.fill), copy(sc.border)
                tc.alignment, tc.number_format = copy(sc.alignment), sc.number_format
        if src.row_dimensions[r_].height:
            ws.row_dimensions[out_r].height = src.row_dimensions[r_].height
    for k, dim in src.column_dimensions.items():
        if openpyxl.utils.column_index_from_string(k) <= last_col:
            ws.column_dimensions[k].width = dim.width
    ws["A1"].font = TITLE
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=min(last_col, 12))
    ws["A3"].alignment = WRAP
    ws.row_dimensions[3].height = 48
    ws.freeze_panes = src.freeze_panes
    return ws


hist = openpyxl.load_workbook(HISTORY_SOURCE)
h = hist["Historical FY05-25"]
copy_sheet(h, "Appendix History FY05-25",
           "History, not forecast: Massachusetts Division of Local Services Schedule A, Department of Revenue recap data "
           "and the Town's audited financial statements, FY2005 to FY2025. The cohort split at the bottom is the one "
           "calculated section: it follows property that existed in FY2005 separately from new growth since.",
           relabel={h.cell(r_, 1).value: "Property that existed in FY2005 is followed separately from the new growth "
                    "added each year after; both grow 2.5% a year plus their share of that year's override, debt "
                    "exclusion and unused levy capacity. FY2005 is 100% existing property."
                    for r_ in range(1, h.max_row + 1)
                    if isinstance(h.cell(r_, 1).value, str) and h.cell(r_, 1).value.startswith("Replicates")})
ws_ = wb["Appendix History FY05-25"]
ws_["A1"] = "Appendix: history, FY2005 to FY2025"
s_ = hist["Schools by Category"]
# keep FY2009-2025 only (later columns are an earlier, superseded forecast)
last = max(c_ for c_ in range(1, s_.max_column + 1) if s_.cell(5, c_).value == "FY2025")
copy_sheet(s_, "Appendix Schools FY09-25",
           "History, not forecast: Massachusetts Department of Elementary and Secondary Education spending per pupil "
           "by category times actual enrollment each year. This is the state's school spending measure, which counts "
           "school staff benefits, so it does not equal the Schedule A schools total.", max_col=last,
           relabel={"TOTAL (Total In-District Expenditures, FY2009-2025; category sum, FY2026-2040)": "TOTAL (in-district spending)",
                    "Total enrollment (context - see Guide/DESE sourcing)": "Total enrollment (context; state data)",
                    "Average teacher salary (context, FY2018+ only)": "Average teacher salary (context, FY2018 on)"})
wb["Appendix Schools FY09-25"]["A1"] = "Appendix: schools spending by category, FY2009 to FY2025"
b_ = hist["Benefits by Category"]
lastb = max(c_ for c_ in range(1, b_.max_column + 1) if b_.cell(5, c_).value == "FY2025")
drop = {r_ for r_ in range(1, b_.max_row + 1) if isinstance(b_.cell(r_, 1).value, str)
        and b_.cell(r_, 1).value.startswith("Group Health has a real")}
copy_sheet(b_, "Appendix Benefits FY23-25",
           "History, not forecast: the Town's own benefits detail tables from three successive Financial Plans, FY2023 to FY2025.",
           max_col=lastb, drop_rows=drop)
wb["Appendix Benefits FY23-25"]["A1"] = "Appendix: benefits by category, FY2023 to FY2025"

ORDER_SHEETS = ["Start here", "Settings", "Forecast", "Revenue build", "Worked example", "Assumptions", "History", "Data",
                "Checks", "Appendix History FY05-25", "Appendix Schools FY09-25", "Appendix Benefits FY23-25"]
wb._sheets = [wb[n] for n in ORDER_SHEETS]
wb.active = 0
wb.save(OUT)
print(f"wrote {OUT.name}: sheets {wb.sheetnames}; forecast rows {len(FROW)}; revenue build rows {len(BROW)}; "
      f"assumptions {len(ASM_ROW)}")
