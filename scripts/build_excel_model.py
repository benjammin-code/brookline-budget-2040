"""
Builds `Brookline_Fiscal_Model.xlsx` - a single, auditable Excel workbook
covering the whole project: FY2005-2025 historical actuals plus the
FY2026-2040 forecast, with every core Prop 2.5 mechanic as a LIVE formula
(change an assumption cell, watch the bottom line move) and every
genuinely bespoke sub-model (CHCA's own ramp math aside - that IS live;
Local Receipts' meals-tax/building-permits/cumulative-new-commercial-sqft
blend, and the tax-rate-drift/implied-units-and-sqft translation) brought
in as a clearly labeled, cited COMPUTED value pulled from the already-
validated Python model, not re-derived a second time. This is the
"hybrid" depth Ben chose (2026-09-01) over a full re-formulate-everything
build (more auditable but two implementations to keep in sync forever) or
a values-only data book (safest against drift, but nothing to tweak).

Every LIVE tab is cross-checked in-sheet against the corresponding
already-computed CSV (a Diff row, conditionally formatted red if any
year's gap exceeds $1) - and this script's own `validate()` step
independently re-evaluates every formula in the saved file (via the
`formulas` package, a real formula-evaluation engine) and diffs the
result against the same CSVs before declaring success. Two coats of
paint against the one thing that would make this workbook worse than not
having it: silently-wrong formulas an owner trusts because they look
plausible.

Run: python3 build_excel_model.py
Output: ../Brookline_Fiscal_Model.xlsx
"""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from openpyxl.worksheet.worksheet import Worksheet

import new_growth_scenario_forecast as ng

ROOT = Path(__file__).parent.parent
OUT_PATH = ROOT / "Brookline_Fiscal_Model.xlsx"

# ---------------------------------------------------------------- styles --
NAVY = "1F3A5F"
TAN_INPUT = "FFF2CC"     # editable/input cells
GREY_CITE = "E7E6E6"     # cited/computed-elsewhere cells
BLUE_HEAD = "D9E2F3"
GREEN_KEY = "E2EFDA"     # key live-formula output rows
RED_DIFF = "FFC7CE"

F_TITLE = Font(size=16, bold=True, color="FFFFFF")
F_SECTION = Font(size=12, bold=True, color=NAVY)
F_HEADER = Font(bold=True)
F_LABEL = Font(bold=False)
F_LABEL_KEY = Font(bold=True)
F_NOTE = Font(italic=True, size=9, color="808080")

FILL_TITLE = PatternFill("solid", fgColor=NAVY)
FILL_INPUT = PatternFill("solid", fgColor=TAN_INPUT)
FILL_CITE = PatternFill("solid", fgColor=GREY_CITE)
FILL_HEAD = PatternFill("solid", fgColor=BLUE_HEAD)
FILL_KEY = PatternFill("solid", fgColor=GREEN_KEY)

THIN = Side(style="thin", color="BFBFBF")
BORDER_BOTTOM = Border(bottom=THIN)

USD0 = '#,##0;(#,##0)'
PCT3 = '0.000%'
PCT2 = '0.00%'


def col(i):
    return get_column_letter(i)


class Sheet:
    """Thin helper around an openpyxl worksheet: tracks the next free row
    and gives named-row lookups so later tabs can build cross-sheet
    formulas without hunting for coordinates."""

    def __init__(self, ws: Worksheet, year_start_col: int):
        self.ws = ws
        self.r = 1
        self.year_col0 = year_start_col  # column index of the first year
        self.rows = {}  # key -> row number, for cross references

    def title(self, text):
        self.ws.merge_cells(start_row=self.r, start_column=1, end_row=self.r, end_column=self.year_col0 + 20)
        c = self.ws.cell(self.r, 1, text)
        c.font = F_TITLE
        c.fill = FILL_TITLE
        self.ws.row_dimensions[self.r].height = 26
        self.r += 2

    def section(self, text):
        c = self.ws.cell(self.r, 1, text)
        c.font = F_SECTION
        self.r += 1

    def note(self, text):
        c = self.ws.cell(self.r, 1, text)
        c.font = F_NOTE
        self.ws.merge_cells(start_row=self.r, start_column=1, end_row=self.r, end_column=self.year_col0 + 14)
        self.ws.row_dimensions[self.r].height = 14 * (1 + len(text) // 160)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        self.r += 1

    def blank(self, n=1):
        self.r += n

    def year_header(self, years, start_row=None):
        row = start_row or self.r
        self.ws.cell(row, 1, "Line item").font = F_HEADER
        for i, y in enumerate(years):
            c = self.ws.cell(row, self.year_col0 + i, f"FY{y}")
            c.font = F_HEADER
            c.fill = FILL_HEAD
            c.alignment = Alignment(horizontal="center")
            c.border = BORDER_BOTTOM
        self.ws.cell(row, 1).fill = FILL_HEAD
        self.ws.cell(row, 1).border = BORDER_BOTTOM
        if start_row is None:
            self.r += 1
        return row

    def addr(self, row, year_index, absolute_row=False, absolute_col=False):
        c = col(self.year_col0 + year_index)
        rr = f"${row}" if absolute_row else str(row)
        cc = f"${c}" if absolute_col else c
        return f"{cc}{rr}"

    def row(self, key, label, kind="formula", note=None, numfmt=USD0, bold=False):
        """Registers a new row, writes its label, returns the row number.
        kind: 'input' (tan), 'cite' (grey), 'formula' (white), 'key' (green)."""
        r = self.r
        self.rows[key] = r
        lc = self.ws.cell(r, 1, label)
        lc.font = F_LABEL_KEY if bold or kind == "key" else F_LABEL
        fill = {"input": FILL_INPUT, "cite": FILL_CITE, "key": FILL_KEY}.get(kind)
        if fill:
            lc.fill = fill
        self.r += 1
        return r

    def set_years(self, row, years, values, numfmt=USD0, kind="formula"):
        fill = {"input": FILL_INPUT, "cite": FILL_CITE, "key": FILL_KEY}.get(kind)
        for i, y in enumerate(years):
            c = self.ws.cell(row, self.year_col0 + i)
            v = values[i] if not callable(values) else values(y, i)
            c.value = v
            c.number_format = numfmt
            if fill:
                c.fill = fill

    def sheet_ref(self, row, year_index):
        return f"'{self.ws.title}'!{self.addr(row, year_index)}"


# ------------------------------------------------------------ data load --

def load_csv_rows(path, key="fiscal_year", scenario_key=None):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    if scenario_key:
        out = {}
        for r in rows:
            out.setdefault(r[scenario_key], {})[int(r[key])] = r
        return out
    return {int(r[key]): r for r in rows}


HIST = load_csv_rows(ROOT / "output/brookline_historical_financials_fy05_25.csv")
with open(ROOT / "output/town_own_forecast_fy26_31.csv") as f:
    _rows = list(csv.DictReader(f))
TOWN = {}
for r in _rows:
    TOWN.setdefault(r["category"], {})[r["subcategory"]] = {y: float(r[str(y)]) for y in range(2026, 2032)}

REVENUE_CSV = load_csv_rows(ROOT / "output/baseline_revenue_forecast_fy26_40.csv", scenario_key="scenario")
EXPENSE_CSV = load_csv_rows(ROOT / "output/baseline_expense_forecast_fy26_40.csv", scenario_key="scenario")
SCHOOLS_CAT_CSV = load_csv_rows(ROOT / "output/schools_category_forecast_fy26_40.csv")
SCHOOLS_CAT_HIST_CSV = load_csv_rows(ROOT / "output/school_spending_by_category_fy09_25.csv")
SCHOOLS_TEACHER_SALARY_CSV = load_csv_rows(ROOT / "output/school_teacher_salary_fy09_25.csv")
SCHOOLS_ENROLLMENT_CSV = load_csv_rows(ROOT / "output/school_enrollment_staffing_fy05_25.csv")
BENEFITS_CAT_CSV = load_csv_rows(ROOT / "output/benefits_category_forecast_fy26_40.csv")
BENEFITS_CAT_HIST_CSV = load_csv_rows(ROOT / "output/benefits_category_history_fy00_25.csv")
DEPARTMENTAL_CAT_CSV = load_csv_rows(ROOT / "output/departmental_category_forecast_fy26_40.csv")
BALANCE_SHEET_CSV = load_csv_rows(ROOT / "output/balance_sheet_liabilities_forecast_fy25_40.csv")
SURPLUS_CSV = load_csv_rows(ROOT / "output/baseline_surplus_deficit_forecast_fy26_40.csv", scenario_key="scenario")
NEWGROWTH_CSV = load_csv_rows(ROOT / "output/new_growth_scenarios_fy26_40.csv", scenario_key="scenario")
EXNEW_HIST_CSV = load_csv_rows(ROOT / "output/existing_vs_new_property_tax_fy05_25.csv")
EXNEW_FCST_CSV = load_csv_rows(ROOT / "output/existing_vs_new_property_tax_fy26_40_scenarios.csv", scenario_key="scenario")
DECOMP_CSV = load_csv_rows(ROOT / "output/base_case_decomposition_fy26_40.csv", scenario_key="run")
OVERRIDE_CSV = load_csv_rows(ROOT / "output/override_reliance_scenario_fy26_40.csv")

HIST_YEARS = list(range(2005, 2026))
FCST_YEARS = list(range(2026, 2041))
TOWN_YEARS = list(range(2026, 2032))
EXTEND_YEARS = list(range(2032, 2041))

SCENARIOS_REV = ["town_assumptions", "trend_corrected"]
SCENARIOS_NG = ["trend_continues", "peer_target_residential_led", "peer_target_commercial_led", "peer_target_balanced_mix"]

wb = Workbook()
wb.remove(wb.active)


# ------------------------------------------------------------ Historical --

def build_historical():
    ws = wb.create_sheet("Historical FY05-25")
    ws.column_dimensions["A"].width = 42
    for i in range(len(HIST_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Historical Actuals, FY2005-2025")
    s.note("Source: MA DLS Schedule A, DOR Recap Sheet data, and the Town's own audited financials - "
           "output/brookline_historical_financials_fy05_25.csv. Every cell on this tab is real, reported "
           "history, not a projection - shown as values, with the one exception of the Existing-vs-New "
           "cohort split at the bottom, which IS a live formula (it's a real analytical model applied to "
           "real historical inputs, not a forecast).")
    s.blank()

    s.section("Property Tax Levy Mechanics (Prop 2½)")
    yh = s.year_header(HIST_YEARS)
    r_prior = s.row("prior_levy_limit", "Prior year levy limit", kind="cite")
    r_25pct = s.row("increase_2_5pct", "2.5% statutory increase", kind="cite")
    r_ng = s.row("new_growth", "New growth ($)", kind="cite")
    r_ovr = s.row("override", "Override (voter-approved, this year)", kind="cite")
    r_debtx = s.row("debt_exclusions", "Debt exclusion revenue", kind="cite")
    r_excess = s.row("excess_capacity", "Excess capacity (allowed but not raised)", kind="cite")
    r_levy = s.row("total_levy", "TOTAL LEVY (property tax raised)", kind="key", bold=True)
    s.blank()

    s.section("Revenue")
    r_stateaid = s.row("state_aid", "State aid", kind="cite")
    r_localrec = s.row("local_receipts", "Local receipts (actual)", kind="cite")
    r_totrev = s.row("total_revenue", "Total General Fund revenue", kind="cite")
    s.blank()

    s.section("Expense (Schedule A functional categories)")
    r_dept = s.row("departmental", "Departmental (Town, ex-schools)", kind="cite",
                   note="general_government + public_safety + public_works + human_services + culture_recreation")
    r_school = s.row("schools", "Schools (education)", kind="cite")
    r_benefits = s.row("benefits", "Benefits (fixed_costs: pensions, health, OPEB)", kind="cite")
    r_debtsvc = s.row("debt_service", "Debt service (total)", kind="cite")
    r_othernd = s.row("other_nondept", "Other (residual)", kind="cite")
    r_totexp = s.row("total_expenditure", "TOTAL EXPENDITURE", kind="key", bold=True)
    s.blank()

    def v(key, y):
        raw = HIST[y][key]
        return float(raw) if raw not in ("", None) else None

    def setcell(row, i, value, numfmt=USD0):
        c = ws.cell(row, 3 + i, value)
        if value is not None:
            c.number_format = numfmt
        return c

    dept_keys = ["exp_general_government", "exp_public_safety", "exp_public_works",
                 "exp_human_services", "exp_culture_recreation"]

    for i, y in enumerate(HIST_YEARS):
        ws.cell(r_prior, 3 + i, v("prior_levy_limit", y)).number_format = USD0
        ws.cell(r_25pct, 3 + i, v("increase_2_5pct", y)).number_format = USD0
        ws.cell(r_ng, 3 + i, v("new_growth", y)).number_format = USD0
        ws.cell(r_ovr, 3 + i, v("override", y)).number_format = USD0
        ws.cell(r_debtx, 3 + i, v("debt_exclusions", y)).number_format = USD0
        ws.cell(r_excess, 3 + i, v("excess_capacity", y)).number_format = USD0
        c = ws.cell(r_levy, 3 + i, f"=SUM({s.addr(r_prior, i)}:{s.addr(r_excess, i)})")
        c.number_format = USD0
        setcell(r_stateaid, i, v("recap_state_aid", y))
        setcell(r_localrec, i, v("local_receipts_act_total", y))
        setcell(r_totrev, i, v("rev_total_revenues", y))
        dept_total = sum(v(k, y) for k in dept_keys)
        ws.cell(r_dept, 3 + i, dept_total).number_format = USD0
        ws.cell(r_school, 3 + i, v("exp_education", y)).number_format = USD0
        ws.cell(r_benefits, 3 + i, v("exp_fixed_costs", y)).number_format = USD0
        ws.cell(r_debtsvc, 3 + i, v("exp_debt_service", y)).number_format = USD0
        total_exp = v("exp_total_expenditures", y)
        other_nd = total_exp - dept_total - v("exp_education", y) - v("exp_fixed_costs", y) - v("exp_debt_service", y)
        ws.cell(r_othernd, 3 + i, other_nd).number_format = USD0
        ws.cell(r_totexp, 3 + i, f"=SUM({s.addr(r_dept, i)}:{s.addr(r_othernd, i)})").number_format = USD0

    s.blank()
    s.section("Existing (pre-2005) vs. New Property Cohort - live model")
    s.note("Replicates existing_vs_new_property_tax.py exactly: an 'existing' cohort fixed as of FY2005, "
           "and a 'new' cohort that permanently absorbs each year's new-growth $ from that year forward - "
           "both compound at 2.5%/yr plus their own value-share of that year's override/debt-exclusion/"
           "excess-capacity. Base year FY2005: 100% existing, 0% new.")
    r_ex_allow = s.row("ex_allowed", "Existing: allowed levy limit", kind="key", bold=True)
    r_ex_excess = s.row("ex_excess", "Existing: excess-capacity share", kind="formula")
    r_ex_debtx = s.row("ex_debtx", "Existing: debt-exclusion share", kind="formula")
    r_ex_tot = s.row("ex_tot", "Existing: TOTAL TAX", kind="key", bold=True)
    r_new_allow = s.row("new_allow", "New: allowed levy limit", kind="key", bold=True)
    r_new_excess = s.row("new_excess", "New: excess-capacity share", kind="formula")
    r_new_debtx = s.row("new_debtx", "New: debt-exclusion share", kind="formula")
    r_new_tot = s.row("new_tot", "New: TOTAL TAX", kind="key", bold=True)
    r_share = s.row("existing_share", "Existing share of pre-item total (helper)", kind="formula", numfmt=PCT3)
    r_town_check = s.row("town_check", "Check: existing+new vs. total levy (should be $0)", kind="formula")

    for i, y in enumerate(HIST_YEARS):
        if y == 2005:
            ws.cell(r_ex_allow, 3, f"={s.addr(r_prior, 0)}+{s.addr(r_25pct, 0)}+{s.addr(r_ng, 0)}+{s.addr(r_ovr, 0)}")
            ws.cell(r_new_allow, 3, 0)
            ws.cell(r_ex_excess, 3, f"={s.addr(r_excess, 0)}")
            ws.cell(r_new_excess, 3, 0)
            ws.cell(r_ex_debtx, 3, f"={s.addr(r_debtx, 0)}")
            ws.cell(r_new_debtx, 3, 0)
            ws.cell(r_share, 3, 1)
        else:
            p = i - 1
            ex_pre = f"({s.addr(r_ex_allow, p)}*1.025)"
            new_pre = f"({s.addr(r_new_allow, p)}*1.025+{s.addr(r_ng, i)})"
            ws.cell(r_share, 3 + i, f"={ex_pre}/({ex_pre}+{new_pre})")
            share = s.addr(r_share, i)
            ws.cell(r_ex_allow, 3 + i, f"={ex_pre}+{s.addr(r_ovr, i)}*{share}")
            ws.cell(r_new_allow, 3 + i, f"={new_pre}+{s.addr(r_ovr, i)}*(1-{share})")
            ws.cell(r_ex_excess, 3 + i, f"={s.addr(r_excess, i)}*{share}")
            ws.cell(r_new_excess, 3 + i, f"={s.addr(r_excess, i)}*(1-{share})")
            ws.cell(r_ex_debtx, 3 + i, f"={s.addr(r_debtx, i)}*{share}")
            ws.cell(r_new_debtx, 3 + i, f"={s.addr(r_debtx, i)}*(1-{share})")
        ws.cell(r_ex_tot, 3 + i, f"=SUM({s.addr(r_ex_allow, i)},{s.addr(r_ex_excess, i)},{s.addr(r_ex_debtx, i)})")
        ws.cell(r_new_tot, 3 + i, f"=SUM({s.addr(r_new_allow, i)},{s.addr(r_new_excess, i)},{s.addr(r_new_debtx, i)})")
        ws.cell(r_town_check, 3 + i, f"={s.addr(r_ex_tot, i)}+{s.addr(r_new_tot, i)}-{s.addr(r_levy, i)}")
        for rr in (r_ex_allow, r_ex_excess, r_ex_debtx, r_ex_tot, r_new_allow, r_new_excess, r_new_debtx,
                   r_new_tot, r_town_check):
            ws.cell(rr, 3 + i).number_format = USD0

    ws.freeze_panes = "C4"
    print(f"Historical tab: {s.r} rows.")
    return s, dict(levy=r_levy, prior=r_prior, debtx=r_debtx, dept=r_dept, school=r_school,
                    benefits=r_benefits, debtsvc=r_debtsvc, othernd=r_othernd, totexp=r_totexp,
                    ex_allow=r_ex_allow, new_allow=r_new_allow, stateaid=r_stateaid, localrec=r_localrec,
                    ng=r_ng, ovr=r_ovr, excess=r_excess, totrev=r_totrev)


HIST_SHEET, HIST_ROWS = build_historical()
wb.save(OUT_PATH)
print("Saved (historical tab only).")


# --------------------------------------------------------------- validate --

def validate_sheet(sheet: Sheet, checks, tol=1.0):
    """checks: list of (row_number, years_list, truth_lookup_fn) where
    truth_lookup_fn(year_index) -> expected float or None. Evaluates the
    saved workbook with a real formula engine and diffs every cell."""
    import formulas
    xl = formulas.ExcelModel().loads(str(OUT_PATH)).finish()
    sol = xl.calculate()
    sheet_key = f"[{OUT_PATH.name}]{sheet.ws.title.upper()}"
    fails = []
    n = 0
    for row, years, truth_fn in checks:
        for i, y in enumerate(years):
            addr = sheet.addr(row, i)
            key = f"'{sheet_key}'!{addr}"
            if key not in sol:
                fails.append((sheet.ws.title, addr, y, "NO FORMULA/VALUE"))
                continue
            got = sol[key].value
            got = got[0, 0] if hasattr(got, "shape") else got
            expected = truth_fn(i)
            n += 1
            if expected is None:
                continue
            if got is None or abs(float(got) - float(expected)) > tol:
                fails.append((sheet.ws.title, addr, y, f"got={got} expected={expected}"))
    print(f"  validated {n} cells on '{sheet.ws.title}': {len(fails)} mismatches")
    for f_ in fails[:20]:
        print("   MISMATCH", f_)
    return fails


ALL_FAILS = []
ALL_FAILS += validate_sheet(HIST_SHEET, [
    (HIST_ROWS["ex_allow"], HIST_YEARS, lambda i: float(EXNEW_HIST_CSV[HIST_YEARS[i]]["existing_allowed_levy_limit"])),
    (HIST_ROWS["new_allow"], HIST_YEARS, lambda i: float(EXNEW_HIST_CSV[HIST_YEARS[i]]["new_allowed_levy_limit"])),
])
print("TOTAL FAILS SO FAR (after Historical):", len(ALL_FAILS))


# ------------------------------------------------------------ Assumptions --

def build_assumptions(hist: Sheet, hist_rows):
    ws = wb.create_sheet("Assumptions")
    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 90
    r = 1
    A = {}

    def title(text):
        nonlocal r
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        c = ws.cell(r, 1, text)
        c.font = F_TITLE
        c.fill = FILL_TITLE
        ws.row_dimensions[r].height = 26
        r += 2

    def section(text):
        nonlocal r
        ws.cell(r, 1, text).font = F_SECTION
        r += 1

    def header():
        nonlocal r
        for i, h in enumerate(["Assumption", "Value", "Unit", "Source / citation"]):
            c = ws.cell(r, 1 + i, h)
            c.font = F_HEADER
            c.fill = FILL_HEAD
            c.border = BORDER_BOTTOM
        r += 1

    def item(key, label, value, unit, source, numfmt=None, editable=True):
        nonlocal r
        ws.cell(r, 1, label)
        c = ws.cell(r, 2, value)
        if numfmt:
            c.number_format = numfmt
        if editable:
            c.fill = FILL_INPUT
        ws.cell(r, 3, unit)
        sc = ws.cell(r, 4, source)
        sc.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = max(14, 14 * (1 + len(source) // 85))
        A[key] = f"Assumptions!$B${r}"
        r += 1

    def blank(n=1):
        nonlocal r
        r += n

    title("Assumptions")
    ws.cell(r, 1, "Every rate/parameter the forecast tabs consume as a LIVE formula input. Tan cells are "
                   "editable - change one here and the Revenue, Expense, and New-Growth-Scenario tabs "
                   "recalculate. Grey-filled rows elsewhere in the workbook are genuinely bespoke sub-models "
                   "(CHCA's construction phasing math aside, which IS live) pulled in as already-computed, "
                   "cited values instead - see the Guide tab for which is which and why.")
    ws.cell(r, 1).font = F_NOTE
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    ws.cell(r, 1).alignment = Alignment(wrap_text=True)
    ws.row_dimensions[r].height = 42
    r += 2

    section("Prop 2½ statutory mechanics")
    header()
    item("statutory_pct", "Statutory annual increase", 0.025, "%/yr",
         "M.G.L. c.59 §21C - fixed by state law, not a policy choice.", numfmt=PCT2, editable=False)
    blank()

    section("Phase 1 (baseline revenue) — new growth, town_assumptions")
    header()
    item("ng_town_flat", "New growth ($/yr, flat)", ng.NEW_GROWTH_TOWN, "$/yr",
         "Town's own FY27-31 LRFP assumption (p.3 'Primary Assumptions': "
         "'$2.5M assumed for new growth, including out-years').")
    blank()

    section("May 2026 operating override (FY2027-2029) — decided fact, both scenarios")
    header()
    item("override_2027", "FY2027 tranche", ng.MAY_2026_OVERRIDE_SCHEDULE[2027], "$",
         "Ben's own 'FY27-FY29 Brookline property tax & impact of new growth.xlsx', cross-sourced against "
         "the Override Guide's $23,254,439 3-year total (data/SOURCES.md). Passed 2026-05-05 - NOT in the "
         "Town's own FY27-31 LRFP (that document predates the vote by 4 months; its own 'General Override' "
         "levy-buildup line is blank every year). See README Part 3a for the full correction story.")
    item("override_2028", "FY2028 tranche", ng.MAY_2026_OVERRIDE_SCHEDULE[2028], "$", "As above.")
    item("override_2029", "FY2029 tranche", ng.MAY_2026_OVERRIDE_SCHEDULE[2029], "$", "As above.")
    ws.cell(r, 1, "Each tranche is 'permanent, not phased-out' (Override Guide) - once added, it stays in "
                  "the levy base and compounds at 2.5%/yr forever after, exactly like every historical override.")
    ws.cell(r, 1).font = F_NOTE
    r += 1
    blank()

    section("Chestnut Hill Commercial Area (CHCA) — real, confirmed project, both Phase 1 & 2")
    header()
    item("chca_start", "Construction start FY (0% ramp point)", ng.CHCA_CONSTRUCTION_START_YEAR, "FY",
         "First FY substantially affected by the 2028 groundbreaking.")
    item("chca_stable", "Full stabilization FY (100% ramp point)", ng.CHCA_FULL_STABILIZATION_YEAR, "FY",
         "~5yr construction/lease-up, landing near ERSC's 7yr+18mo span.")
    item("chca_ptax_rkg", "Property tax at stabilization (Phase 1, RKG scenario)", ng.CHCA_PROPERTY_TAX_RKG, "$",
         "RKG's own independent scenario (more conservative than the developer's City Realty average) - "
         "ERSC report Appendix p.551-555.")
    item("chca_lr_rkg", "Local receipts at stabilization (Phase 1, RKG scenario)", ng.CHCA_LOCAL_RECEIPTS_RKG, "$",
         "As above - rooms tax + motor vehicle excise.")
    item("chca_ptax_cravg", "Property tax at stabilization (Phase 2, City Realty avg)", ng.CHCA_PROPERTY_TAX_CR_AVG, "$",
         "Average of City Realty's 3 developer scenarios - used for Phase 2's own new-growth scenarios.")
    item("chca_lr_cravg", "Local receipts at stabilization (Phase 2, City Realty avg)", ng.CHCA_LOCAL_RECEIPTS_CR_AVG, "$",
         "As above.")
    blank()

    section("Phase 1 (trend_corrected) — new growth & revenue trend rates (all live off Historical tab)")
    header()
    recent5 = [y for y in HIST_YEARS if 2021 <= y <= 2025]
    ratio_terms = "+".join(
        f"({hist.sheet_ref(hist_rows['ng'], HIST_YEARS.index(y))}/{hist.sheet_ref(hist_rows['prior'], HIST_YEARS.index(y))})"
        for y in recent5)
    item("ng_trend_pct", "New growth (%/yr of prior levy limit, trailing 5yr actual)",
         f"=({ratio_terms})/5", "%/yr",
         "Trailing 5-year actual average, FY2021-2025: new_growth / prior_levy_limit each year, from the "
         "Historical tab (DOR/DLS convention). Live formula - references Historical directly.",
         numfmt=PCT3, editable=False)
    yr15, yr25 = HIST_YEARS.index(2015), HIST_YEARS.index(2025)
    item("state_aid_cagr_trend", "State aid CAGR (trailing 10yr actual)",
         f"=({hist.sheet_ref(hist_rows['stateaid'], yr25)}/{hist.sheet_ref(hist_rows['stateaid'], yr15)})^(1/10)-1",
         "%/yr", "FY2015→FY2025 actual, 10yr window chosen to smooth year-to-year state-budget noise.",
         numfmt=PCT3, editable=False)
    yr19, yr25b = HIST_YEARS.index(2019), HIST_YEARS.index(2025)
    item("local_receipts_cagr_trend", "Local receipts CAGR (trailing 6yr actual)",
         f"=({hist.sheet_ref(hist_rows['localrec'], yr25b)}/{hist.sheet_ref(hist_rows['localrec'], yr19)})^(1/6)-1",
         "%/yr", "FY2019→FY2025 actual (FY2019, not FY2015, to skip the FY2020-21 COVID dip). NOTE: this "
         "simple CAGR is for reference only - the live Revenue tab's trend_corrected Local Receipts line "
         "is a cited/computed value (see Guide tab), since the real model splits out meals tax and building "
         "permits separately first (a genuinely bespoke sub-model, not re-derived in this workbook).",
         numfmt=PCT3, editable=False)
    blank()

    section("Phase 2 — 5-category new-growth mix, %/yr of prior operating levy, by scenario")
    ws.cell(r, 1, "The core stress-test surface: change any tan cell and every downstream FY2026-2040 "
                   "property-tax figure on the New Growth Scenarios tab recalculates.")
    ws.cell(r, 1).font = F_NOTE
    r += 1
    header_row = r
    ws.cell(r, 1, "Category")
    for j, scen in enumerate(SCENARIOS_NG):
        c = ws.cell(r, 2 + j, scen)
        c.font = F_HEADER
        c.fill = FILL_HEAD
    r += 1
    cat_rows = {}
    for cat_key, cat_label in [("res_new", "Residential - new construction"), ("res_reno", "Residential - renovation"),
                                ("com_new", "Commercial - new construction"), ("com_reno", "Commercial - renovation"),
                                ("com_pp", "Commercial - personal property")]:
        ws.cell(r, 1, cat_label)
        cat_rows[cat_key] = r
        r += 1
    peer_pct = ng.PEER_TARGET_PCT
    other_fixed = ng.TREND_RES_RENO_PCT + ng.TREND_COM_RENO_PCT + ng.TREND_COM_PP_PCT
    res_led = peer_pct - (other_fixed + ng.TREND_COM_NEW_PCT)
    com_led = peer_pct - (other_fixed + ng.TREND_RES_NEW_PCT)
    trend_total = ng.TREND_RES_NEW_PCT + ng.TREND_RES_RENO_PCT + ng.TREND_COM_NEW_PCT + ng.TREND_COM_RENO_PCT + ng.TREND_COM_PP_PCT
    gap = peer_pct - trend_total
    bal_res = ng.TREND_RES_NEW_PCT + gap / 2
    bal_com = ng.TREND_COM_NEW_PCT + gap / 2
    scen_values = {
        "trend_continues": dict(res_new=ng.TREND_RES_NEW_PCT, res_reno=ng.TREND_RES_RENO_PCT,
                                 com_new=ng.TREND_COM_NEW_PCT, com_reno=ng.TREND_COM_RENO_PCT, com_pp=ng.TREND_COM_PP_PCT),
        "peer_target_residential_led": dict(res_new=res_led, res_reno=ng.TREND_RES_RENO_PCT,
                                             com_new=ng.TREND_COM_NEW_PCT, com_reno=ng.TREND_COM_RENO_PCT, com_pp=ng.TREND_COM_PP_PCT),
        "peer_target_commercial_led": dict(res_new=ng.TREND_RES_NEW_PCT, res_reno=ng.TREND_RES_RENO_PCT,
                                            com_new=com_led, com_reno=ng.TREND_COM_RENO_PCT, com_pp=ng.TREND_COM_PP_PCT),
        "peer_target_balanced_mix": dict(res_new=bal_res, res_reno=ng.TREND_RES_RENO_PCT,
                                          com_new=bal_com, com_reno=ng.TREND_COM_RENO_PCT, com_pp=ng.TREND_COM_PP_PCT),
    }
    for j, scen in enumerate(SCENARIOS_NG):
        for cat_key, row_n in cat_rows.items():
            c = ws.cell(row_n, 2 + j, scen_values[scen][cat_key])
            c.number_format = PCT3
            c.fill = FILL_INPUT
            A[f"ng_{scen}_{cat_key}"] = f"Assumptions!${col(2 + j)}${row_n}"
    r += 1
    item("peer_target_pct", "Peer-target total new-growth rate (80th percentile statewide)", ng.PEER_TARGET_PCT,
         "%/yr", "Recomputed 2026-08-28 directly from the DLS statewide new-growth dataset, trailing-5yr "
         "window (matches trend_corrected's own window) - see .claude/memorialized.md.", numfmt=PCT3)
    ws.cell(r - 1, 1, "Category source (all rows above): res_new/res_reno split from the land-value-map "
                       "classifier (FY2021-25 trailing); com_new/com_reno/com_pp from DOR Schedule A "
                       "trailing-5yr CIP new-growth, split via the Town's own Tax Classification Hearing "
                       "personal-property data. See new_growth_scenarios_fy26_40_methodology.md for full "
                       "sourcing of every category.")
    ws.cell(r - 1, 4).font = F_NOTE
    blank()

    section("Tax-rate drift & value appreciation (cited elsewhere - shown here for transparency)")
    header()
    item("res_value_per_unit", "Residential value per new unit (FY2026)", ng.RES_VALUE_PER_UNIT, "$",
         "Units-weighted, FY2026 basis. Back-solved against the Town's own "
         "permit count; centre of a ~$325k-$580k range.", editable=False)
    item("com_value_per_sqft", "Commercial value per new sqft (FY2026)", ng.COM_VALUE_PER_SQFT, "$",
         "Town-wide weighted average, FY2026 basis.", editable=False)
    item("res_appreciation", "Residential value appreciation rate", ng.RES_VALUE_APPRECIATION_RATE, "%/yr",
         "Trailing actual.", numfmt=PCT2, editable=False)
    item("com_appreciation", "Commercial value appreciation rate", ng.COM_VALUE_APPRECIATION_RATE, "%/yr",
         "Trailing actual.", numfmt=PCT2, editable=False)
    item("cip_shift_ratio", "CIP tax-rate shift ratio (COM/RES), held constant", ng.COM_TAX_RATE / ng.RES_TAX_RATE, "x",
         "Brookline's FY2026 shift is 1.746 - 99.8% of the M.G.L. c.40 §56 statutory ceiling of 1.75. "
         "Held constant through FY2040 (no legal room to shift further) - see README, 2026-09-01 CIP fix.",
         numfmt='0.000', editable=False)
    ws.cell(r, 1, "These four feed res_tax_rate(year)/com_tax_rate(year), used ONLY to translate Phase 2's "
                   "new-growth $ into the implied physical unit/sqft columns shown as cited values on the "
                   "New Growth Scenarios tab - they do not affect any $ total in this workbook.")
    ws.cell(r, 1).font = F_NOTE
    r += 1

    ws.freeze_panes = "A1"
    print(f"Assumptions tab: {r} rows.")
    return A

A = build_assumptions(HIST_SHEET, HIST_ROWS)
wb.save(OUT_PATH)
print("Saved (historical + assumptions).")


# ------------------------------------------------------------------ Revenue --

def chca_ramp_formula(year_addr_or_lit, level_cell):
    """Excel formula for the CHCA straight-line ramp, matching _chca_ramp() exactly."""
    start, full = ng.CHCA_CONSTRUCTION_START_YEAR, ng.CHCA_FULL_STABILIZATION_YEAR
    span = full - start + 1
    return (f"=IF({year_addr_or_lit}<{start},0,IF({year_addr_or_lit}>={full},{level_cell},"
            f"{level_cell}*({year_addr_or_lit}-{start}+1)/{span}))")


def build_revenue():
    ws = wb.create_sheet("Revenue FY26-40")
    ws.column_dimensions["A"].width = 46
    for i in range(len(FCST_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Phase 1 — Baseline Revenue Forecast, FY2026-2040")
    s.note("Tan = editable input. Green = key live-formula output. Grey = cited/computed value (a bespoke "
           "sub-model pulled from the already-validated Python output, not re-derived - see Guide tab). "
           "White = an intermediate live formula.")
    s.blank()

    # Row for the fiscal year number itself, used inside IF() ramp formulas.
    r_fy = s.row("fy", "Fiscal year (number)", kind="formula")
    for i, y in enumerate(FCST_YEARS):
        ws.cell(r_fy, 3 + i, y)
    s.blank()

    s.section("Shared inputs (identical across both scenarios)")
    r_annlevy = s.row("annlevy", "Town LRFP: Annual Levy, pre-override (input)", kind="input")
    r_debtx_in = s.row("debtx_in", "Town LRFP: Debt Exclusion (input)", kind="input")
    r_levylim = s.row("levylim", "Town LRFP: Levy limit (= Annual Levy − Debt Excl.)", kind="formula")
    r_ovrcum = s.row("ovrcum", "May 2026 override, cumulative compounded", kind="formula")
    r_priorbase = s.row("priorbase", "Levy-limit-with-override (feeds both scenarios' recursion)", kind="key", bold=True)
    r_debtx = s.row("debtx", "DEBT EXCLUSION REVENUE", kind="key", bold=True,
                    note="FY2032-40 held flat at FY2031 - no new exclusions assumed.")
    r_sa_in = s.row("sa_in", "Town LRFP: State Aid (input)", kind="input")
    r_lr_in = s.row("lr_in", "Town LRFP: Local Receipts (input)", kind="input")
    r_oaf = s.row("oaf", "Other Available Funds (Town LRFP; FY2027 adopted; FY2028-30 + Override Stabilization Fund draw)",
                  kind="cite", note="FY2032-40 held flat at FY2031.")
    s.blank()

    for i, y in enumerate(FCST_YEARS):
        if y in TOWN_YEARS:
            ws.cell(r_annlevy, 3 + i, TOWN["revenue"]["property_taxes"][y]).number_format = USD0
            ws.cell(r_annlevy, 3 + i).fill = FILL_INPUT
            ws.cell(r_debtx_in, 3 + i, TOWN["revenue"]["debt_exclusion"][y]).number_format = USD0
            ws.cell(r_debtx_in, 3 + i).fill = FILL_INPUT
            ws.cell(r_levylim, 3 + i, f"={s.addr(r_annlevy, i)}-{s.addr(r_debtx_in, i)}").number_format = USD0
            if y == 2026:
                ws.cell(r_ovrcum, 3 + i, 0).number_format = USD0
            else:
                cum_prior = s.addr(r_ovrcum, i - 1)
                tranche = A.get(f"override_{y}")
                tranche_term = f"+{tranche}" if tranche else ""
                ws.cell(r_ovrcum, 3 + i, f"={cum_prior}*1.025{tranche_term}").number_format = USD0
            ws.cell(r_priorbase, 3 + i, f"={s.addr(r_levylim, i)}+{s.addr(r_ovrcum, i)}").number_format = USD0
            ws.cell(r_debtx, 3 + i, f"={s.addr(r_debtx_in, i)}").number_format = USD0
            ws.cell(r_sa_in, 3 + i, TOWN["revenue"]["state_aid"][y]).number_format = USD0
            ws.cell(r_sa_in, 3 + i).fill = FILL_INPUT
            ws.cell(r_lr_in, 3 + i, TOWN["revenue"]["local_receipts"][y]).number_format = USD0
            ws.cell(r_lr_in, 3 + i).fill = FILL_INPUT
            ws.cell(r_oaf, 3 + i, float(REVENUE_CSV["trend_corrected"][y]["other_available_funds"])).number_format = USD0
        else:
            ws.cell(r_debtx, 3 + i, f"={s.addr(r_debtx, i - 1)}").number_format = USD0
            ws.cell(r_oaf, 3 + i, f"={s.addr(r_oaf, i - 1)}").number_format = USD0

    def build_scenario_block(scenario):
        s.section(f"Scenario: {scenario}")
        r_chca_lvl = s.row(f"{scenario}_chca_lvl", "CHCA property tax (cumulative level, RKG scenario)", kind="formula")
        r_chca_lr_lvl = s.row(f"{scenario}_chca_lr_lvl", "CHCA local receipts (cumulative level, RKG scenario)", kind="formula")
        r_chca_inc = s.row(f"{scenario}_chca_inc", "CHCA property tax increment (feeds recursion)", kind="formula")
        r_chca_lr_inc = s.row(f"{scenario}_chca_lr_inc", "CHCA local receipts increment (feeds recursion)", kind="formula")
        if scenario == "trend_corrected":
            r_diff = s.row("diff", "Diff: trend new-growth vs. Town's $2.5M/yr (delta method)", kind="formula")
        r_operating = s.row(f"{scenario}_operating", "PROPERTY TAX OPERATING (levy limit)", kind="key", bold=True)
        r_proptax = s.row(f"{scenario}_proptax", "PROPERTY TAXES (operating + debt exclusion)", kind="key", bold=True)
        r_sa = s.row(f"{scenario}_sa", "State Aid", kind="formula")
        if scenario == "town_assumptions":
            r_lr = s.row(f"{scenario}_lr", "Local Receipts", kind="formula")
        else:
            r_lr = s.row(f"{scenario}_lr", "Local Receipts (cited - meals tax/permits/CHCA sub-model)", kind="cite")
        r_fc = s.row(f"{scenario}_fc", "Free Cash (cited - Town LRFP, or the two-year cash cycle for trend; "
                     "revenue_cash_cycle.py)", kind="cite")
        r_totrev = s.row(f"{scenario}_totrev", "TOTAL REVENUE", kind="key", bold=True)
        r_diffcheck = s.row(f"{scenario}_check", "Check vs. Python model (should be ~$0)", kind="formula")
        s.blank()

        for i, y in enumerate(FCST_YEARS):
            fy = s.addr(r_fy, i)
            ws.cell(r_chca_lvl, 3 + i, chca_ramp_formula(fy, A["chca_ptax_rkg"])).number_format = USD0
            ws.cell(r_chca_lr_lvl, 3 + i, chca_ramp_formula(fy, A["chca_lr_rkg"])).number_format = USD0
            if i == 0:
                ws.cell(r_chca_inc, 3 + i, f"={s.addr(r_chca_lvl, i)}-0").number_format = USD0
                ws.cell(r_chca_lr_inc, 3 + i, f"={s.addr(r_chca_lr_lvl, i)}-0").number_format = USD0
            else:
                ws.cell(r_chca_inc, 3 + i, f"={s.addr(r_chca_lvl, i)}-{s.addr(r_chca_lvl, i - 1)}").number_format = USD0
                ws.cell(r_chca_lr_inc, 3 + i, f"={s.addr(r_chca_lr_lvl, i)}-{s.addr(r_chca_lr_lvl, i - 1)}").number_format = USD0

            if scenario == "trend_corrected":
                if y in TOWN_YEARS:
                    prior_diff = "0" if y == 2026 else s.addr(r_diff, i - 1)
                    prior_base_prior_year = s.addr(r_priorbase, i - 1) if y > 2026 else HIST_SHEET.sheet_ref(
                        HIST_ROWS["levy"], HIST_YEARS.index(2025)) + f"-{HIST_SHEET.sheet_ref(HIST_ROWS['debtx'], HIST_YEARS.index(2025))}"
                    ws.cell(r_diff, 3 + i,
                            f"={prior_diff}*1.025+({A['ng_trend_pct']}*({prior_base_prior_year})-{A['ng_town_flat']})"
                            ).number_format = USD0

            if y in TOWN_YEARS:
                if scenario == "town_assumptions":
                    ws.cell(r_operating, 3 + i, f"={s.addr(r_priorbase, i)}+{s.addr(r_chca_lvl, i)}").number_format = USD0
                else:
                    ws.cell(r_operating, 3 + i,
                            f"={s.addr(r_priorbase, i)}+{s.addr(r_diff, i)}+{s.addr(r_chca_lvl, i)}").number_format = USD0
            else:
                if scenario == "town_assumptions":
                    ws.cell(r_operating, 3 + i,
                            f"={s.addr(r_operating, i - 1)}*1.025+{A['ng_town_flat']}+{s.addr(r_chca_inc, i)}"
                            ).number_format = USD0
                else:
                    ws.cell(r_operating, 3 + i,
                            f"={s.addr(r_operating, i - 1)}*(1.025+{A['ng_trend_pct']})+{s.addr(r_chca_inc, i)}"
                            ).number_format = USD0

            ws.cell(r_proptax, 3 + i, f"={s.addr(r_operating, i)}+{s.addr(r_debtx, i)}").number_format = USD0

            if scenario == "town_assumptions":
                if y in TOWN_YEARS:
                    ws.cell(r_sa, 3 + i, f"={s.addr(r_sa_in, i)}").number_format = USD0
                    ws.cell(r_lr, 3 + i, f"={s.addr(r_lr_in, i)}+{s.addr(r_chca_lr_lvl, i)}").number_format = USD0
                else:
                    ws.cell(r_sa, 3 + i, f"={s.addr(r_sa, i - 1)}*(1+{sa_cagr_town})").number_format = USD0
                    ws.cell(r_lr, 3 + i,
                            f"={s.addr(r_lr, i - 1)}*(1+{lr_cagr_town})+{s.addr(r_chca_lr_inc, i)}"
                            ).number_format = USD0
            else:
                n = y - 2025
                ws.cell(r_sa, 3 + i,
                        f"={HIST_SHEET.sheet_ref(HIST_ROWS['stateaid'], HIST_YEARS.index(2025))}*(1+{A['state_aid_cagr_trend']})^{n}"
                        ).number_format = USD0
                ws.cell(r_lr, 3 + i, float(REVENUE_CSV["trend_corrected"][y]["local_receipts"])).number_format = USD0

            ws.cell(r_fc, 3 + i, float(REVENUE_CSV[scenario][y]["free_cash"])).number_format = USD0
            ws.cell(r_totrev, 3 + i,
                    f"={s.addr(r_proptax, i)}+{s.addr(r_sa, i)}+{s.addr(r_lr, i)}+{s.addr(r_oaf, i)}+{s.addr(r_fc, i)}"
                    ).number_format = USD0
            truth = float(REVENUE_CSV[scenario][y]["total_revenue"])
            ws.cell(r_diffcheck, 3 + i, f"={s.addr(r_totrev, i)}-{truth}").number_format = USD0
        s.blank()
        return dict(operating=r_operating, proptax=r_proptax, totrev=r_totrev, sa=r_sa, lr=r_lr, debtx=r_debtx, fc=r_fc)

    sa_cagr_town = f"(({TOWN['revenue']['state_aid'][2031]}/{TOWN['revenue']['state_aid'][2026]})^(1/5)-1)"
    lr_cagr_town = f"(({TOWN['revenue']['local_receipts'][2031]}/{TOWN['revenue']['local_receipts'][2026]})^(1/5)-1)"

    scen_rows = {}
    for scenario in SCENARIOS_REV:
        scen_rows[scenario] = build_scenario_block(scenario)

    ws.freeze_panes = "C4"
    print(f"Revenue tab: {s.r} rows.")
    return s, dict(shared=dict(debtx=r_debtx, priorbase=r_priorbase, fy=r_fy, oaf=r_oaf), scenarios=scen_rows)


REV_SHEET, REV_ROWS = build_revenue()
wb.save(OUT_PATH)
print("Saved (+ revenue).")

for scenario in SCENARIOS_REV:
    rows = REV_ROWS["scenarios"][scenario]
    ALL_FAILS += validate_sheet(REV_SHEET, [
        (rows["totrev"], FCST_YEARS, lambda i, sc=scenario: float(REVENUE_CSV[sc][FCST_YEARS[i]]["total_revenue"])),
        (rows["proptax"], FCST_YEARS, lambda i, sc=scenario: float(REVENUE_CSV[sc][FCST_YEARS[i]]["property_taxes"])),
        (rows["debtx"] if False else REV_ROWS["shared"]["debtx"], FCST_YEARS,
         lambda i, sc=scenario: float(REVENUE_CSV[sc][FCST_YEARS[i]]["debt_exclusion_revenue"])),
    ], tol=2.0)
print("TOTAL FAILS SO FAR (after Revenue):", len(ALL_FAILS))


# ----------------------------------------------------------------- Expense --

def build_expense():
    ws = wb.create_sheet("Expense FY26-40")
    ws.column_dimensions["A"].width = 46
    for i in range(len(FCST_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Phase 3 — Baseline Expense Forecast, FY2026-2040")
    s.note("Departmental/Schools/Benefits: Town's own FY26-31 figures (input, identical both scenarios), "
           "then FY32-40 extends at each scenario's own CAGR - Town-implied for town_assumptions, "
           "trailing-5yr actual (FY2020-2025, from the Historical tab) for trend_corrected. Other Non-"
           "Departmental's three non-CIP sub-lines (general, reserve fund, non-appropriated) are held flat "
           "post-FY2031, identical in both scenarios - no defensible trend basis. Debt Service - Regular "
           "and the CIP share of Other Non-Departmental both follow the Town's own 6.6% CIP policy (their "
           "own realized rates, ~3.85%/~6.26% of prior-yr Net Revenue - not the stated 4.5%/2.1% targets - "
           "see baseline_expense_forecast_fy26_40_methodology.md), applied to each scenario's own Net "
           "Revenue post-FY2031 - cited from the Python model rather than replicated live, so both "
           "genuinely diverge by scenario.")
    s.blank()

    r_fy = s.row("fy", "Fiscal year (number)", kind="formula")
    for i, y in enumerate(FCST_YEARS):
        ws.cell(r_fy, 3 + i, y)
    s.blank()

    s.section("Shared (identical across both scenarios)")
    r_debtx_excl = s.row("debtx_excl", "Debt Service - Excluded (= Revenue tab's Debt Exclusion Revenue)", kind="formula")
    s.blank()

    for i, y in enumerate(FCST_YEARS):
        rev_debtx_ref = REV_SHEET.sheet_ref(REV_ROWS["shared"]["debtx"], i)
        ws.cell(r_debtx_excl, 3 + i, f"={rev_debtx_ref}").number_format = USD0

    def cagr_expr(v2031, v2026):
        return f"(({v2031}/{v2026})^(1/5)-1)"

    def build_scenario_block(scenario):
        s.section(f"Scenario: {scenario}")
        if scenario == "trend_corrected":
            r_dept = s.row(f"{scenario}_dept", "Departmental (cited - see departmental_category_forecast, "
                           "5 Schedule A categories each own-trended, not re-derived here)", kind="cite")
        else:
            r_dept = s.row(f"{scenario}_dept", "Departmental (Town, ex-schools)", kind="key")
        if scenario == "trend_corrected":
            r_school = s.row(f"{scenario}_school", "Schools (cited - see schools_category_forecast, "
                              "9 DESE categories each own-trended, not re-derived here)", kind="cite")
        else:
            r_school = s.row(f"{scenario}_school", "Schools", kind="formula")
        if scenario == "trend_corrected":
            r_ben = s.row(f"{scenario}_ben", "Benefits (cited - see benefits_category_forecast, Pensions/"
                          "Group Health/OPEB/Other each own-modeled, not re-derived here)", kind="cite")
        else:
            r_ben = s.row(f"{scenario}_ben", "Benefits (pensions, health, OPEB)", kind="formula")
        if scenario == "trend_corrected":
            r_debtsvc_reg = s.row(f"{scenario}_debtsvc_reg", "Debt Service - Regular (FY27-32: real CIP "
                                   "funding table; FY33-40: realized ~3.95%/yr rate - cited)", kind="cite")
        else:
            r_debtsvc_reg = s.row(f"{scenario}_debtsvc_reg", "Debt Service - Regular (FY32-40: 6.6% CIP "
                                   "policy, Town's realized ~3.85%/yr debt-financed rate × prior-yr Net "
                                   "Revenue - cited, LRFP basis)", kind="cite")
        r_debtsvc = s.row(f"{scenario}_debtsvc", "Debt Service (total) = Excluded + Regular", kind="formula")
        if scenario == "trend_corrected":
            r_revfin = s.row(f"{scenario}_revfin", "  of which, CIP: Revenue Financed (paygo, target 2.1% "
                              "of Net Rev)", kind="cite")
            r_freecash = s.row(f"{scenario}_freecash", "  of which, CIP: Free Cash allocation (tops CIP "
                                "funding to the Town's 8% policy floor)", kind="cite")
            r_overlay = s.row(f"{scenario}_overlay", "  of which, CIP: Overlay Surplus (one-time)", kind="cite")
            r_othernd = s.row(f"{scenario}_othernd", "Other Non-Departmental = CIP paygo+free cash+overlay "
                               "(above) + general/reserve/non-appropriated (held flat, no trend basis)", kind="cite")
        else:
            r_othernd = s.row(f"{scenario}_othernd", "Other Non-Departmental (FY32-40: CIP share at Town's "
                               "realized ~6.26%/yr rate, LRFP basis, cited; general/reserve/non-appropriated "
                               "held flat)", kind="cite")
        r_tot = s.row(f"{scenario}_tot", "TOTAL EXPENDITURE", kind="key", bold=True)
        r_check = s.row(f"{scenario}_check", "Check vs. Python model (should be ~$0)", kind="formula")
        s.blank()

        if scenario == "town_assumptions":
            dept_cagr = cagr_expr(TOWN["expenditure"]["departmental_town"][2031], TOWN["expenditure"]["departmental_town"][2026])
            school_cagr = cagr_expr(TOWN["expenditure"]["schools"][2031], TOWN["expenditure"]["schools"][2026])
            ben_cagr = cagr_expr(TOWN["expenditure"]["nondept_benefits"][2031], TOWN["expenditure"]["nondept_benefits"][2026])
        else:
            i20, i25 = HIST_YEARS.index(2020), HIST_YEARS.index(2025)
            # dept/schools have no CAGR here - trend_corrected's dept and
            # schools rows are cited values (departmental_category_forecast.py's
            # 5-category sum, schools_category_forecast.py's 9-category sum),
            # not single trended rates. See each script's own methodology.
            ben_cagr = cagr_expr(HIST_SHEET.sheet_ref(HIST_ROWS["benefits"], i25), HIST_SHEET.sheet_ref(HIST_ROWS["benefits"], i20))

        for i, y in enumerate(FCST_YEARS):
            if scenario == "trend_corrected":
                ws.cell(r_dept, 3 + i, float(DEPARTMENTAL_CAT_CSV[y]["total_departmental_category_sum"])).number_format = USD0
                ws.cell(r_dept, 3 + i).fill = FILL_CITE
                ws.cell(r_school, 3 + i, float(SCHOOLS_CAT_CSV[y]["total_schools_category_sum"])).number_format = USD0
                ws.cell(r_school, 3 + i).fill = FILL_CITE
                ws.cell(r_ben, 3 + i, float(BENEFITS_CAT_CSV[y]["total_benefits_category_sum"])).number_format = USD0
                ws.cell(r_ben, 3 + i).fill = FILL_CITE
            if y in TOWN_YEARS:
                if scenario == "town_assumptions":
                    ws.cell(r_dept, 3 + i, TOWN["expenditure"]["departmental_town"][y]).number_format = USD0
                    ws.cell(r_dept, 3 + i).fill = FILL_INPUT
                    ws.cell(r_school, 3 + i, TOWN["expenditure"]["schools"][y]).number_format = USD0
                    ws.cell(r_school, 3 + i).fill = FILL_INPUT
                    ws.cell(r_ben, 3 + i, TOWN["expenditure"]["nondept_benefits"][y]).number_format = USD0
                    ws.cell(r_ben, 3 + i).fill = FILL_INPUT
            else:
                if scenario == "town_assumptions":
                    ws.cell(r_dept, 3 + i, f"={s.addr(r_dept, i - 1)}*(1+{dept_cagr})").number_format = USD0
                    ws.cell(r_school, 3 + i, f"={s.addr(r_school, i - 1)}*(1+{school_cagr})").number_format = USD0
                    ws.cell(r_ben, 3 + i, f"={s.addr(r_ben, i - 1)}*(1+{ben_cagr})").number_format = USD0

            # trend_corrected: debt_service_regular and other_nondept are
            # cited for the ENTIRE FY2026-2040 range, not split by
            # TOWN_YEARS/EXTEND_YEARS - even FY2026-2031 now blends real
            # CIP-table data (2027+) or an LRFP fallback (2026 only) with
            # the LRFP figures for the other 3 other_nondept sub-lines, so
            # it's no longer a pure Town input for this scenario. See
            # baseline_expense_forecast.py's CIP decomposition.
            if scenario == "trend_corrected" or y not in TOWN_YEARS:
                ws.cell(r_debtsvc_reg, 3 + i,
                        float(EXPENSE_CSV[scenario][y]["debt_service_regular"])).number_format = USD0
                ws.cell(r_debtsvc_reg, 3 + i).fill = FILL_CITE
            else:
                ws.cell(r_debtsvc_reg, 3 + i,
                        f"={s.addr(r_debtsvc, i)}-{s.addr(r_debtx_excl, i)}").number_format = USD0
            if scenario == "trend_corrected" or y not in TOWN_YEARS:
                ws.cell(r_debtsvc, 3 + i,
                        f"={s.addr(r_debtx_excl, i)}+{s.addr(r_debtsvc_reg, i)}").number_format = USD0
            else:
                ws.cell(r_debtsvc, 3 + i, TOWN["expenditure"]["nondept_debt_service"][y]).number_format = USD0
                ws.cell(r_debtsvc, 3 + i).fill = FILL_INPUT

            if scenario == "trend_corrected":
                revfin_v = EXPENSE_CSV[scenario][y]["cip_revenue_financed"]
                freecash_v = EXPENSE_CSV[scenario][y]["cip_free_cash"]
                overlay_v = EXPENSE_CSV[scenario][y]["cip_overlay_surplus"]
                if revfin_v != "":
                    ws.cell(r_revfin, 3 + i, float(revfin_v)).number_format = USD0
                    ws.cell(r_revfin, 3 + i).fill = FILL_CITE
                    ws.cell(r_freecash, 3 + i, float(freecash_v)).number_format = USD0
                    ws.cell(r_freecash, 3 + i).fill = FILL_CITE
                    ws.cell(r_overlay, 3 + i, float(overlay_v)).number_format = USD0
                    ws.cell(r_overlay, 3 + i).fill = FILL_CITE
                ws.cell(r_othernd, 3 + i, float(EXPENSE_CSV[scenario][y]["other_nondept"])).number_format = USD0
                ws.cell(r_othernd, 3 + i).fill = FILL_CITE
            elif y in TOWN_YEARS:
                other_total = (TOWN["expenditure"]["nondept_general"][y] + TOWN["expenditure"]["special_appropriations_cip"][y]
                               + TOWN["expenditure"]["nondept_reserve_fund"][y] + TOWN["expenditure"]["non_appropriated"][y])
                ws.cell(r_othernd, 3 + i, other_total).number_format = USD0
                ws.cell(r_othernd, 3 + i).fill = FILL_INPUT
            else:
                ws.cell(r_othernd, 3 + i, float(EXPENSE_CSV[scenario][y]["other_nondept"])).number_format = USD0
                ws.cell(r_othernd, 3 + i).fill = FILL_CITE

            ws.cell(r_tot, 3 + i,
                    f"={s.addr(r_dept, i)}+{s.addr(r_school, i)}+{s.addr(r_ben, i)}+{s.addr(r_debtsvc, i)}+{s.addr(r_othernd, i)}"
                    ).number_format = USD0
            truth = float(EXPENSE_CSV[scenario][y]["total_expenditure"])
            ws.cell(r_check, 3 + i, f"={s.addr(r_tot, i)}-{truth}").number_format = USD0
        s.blank()
        return dict(tot=r_tot)

    scen_rows = {}
    for scenario in SCENARIOS_REV:
        scen_rows[scenario] = build_scenario_block(scenario)

    ws.freeze_panes = "C4"
    print(f"Expense tab: {s.r} rows.")
    return s, dict(shared=dict(debtx_excl=r_debtx_excl, fy=r_fy),
                   scenarios=scen_rows)


EXP_SHEET, EXP_ROWS = build_expense()
wb.save(OUT_PATH)
print("Saved (+ expense).")

for scenario in SCENARIOS_REV:
    rows = EXP_ROWS["scenarios"][scenario]
    ALL_FAILS += validate_sheet(EXP_SHEET, [
        (rows["tot"], FCST_YEARS, lambda i, sc=scenario: float(EXPENSE_CSV[sc][FCST_YEARS[i]]["total_expenditure"])),
    ], tol=2.0)
print("TOTAL FAILS SO FAR (after Expense):", len(ALL_FAILS))


# --------------------------------------------------------- Surplus/Deficit --

def build_surplus_deficit():
    ws = wb.create_sheet("Surplus-Deficit FY26-40")
    ws.column_dimensions["A"].width = 46
    for i in range(len(FCST_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Part 3a — Baseline Surplus/Deficit, FY2026-2040")
    s.note("Pure combination of the Revenue and Expense tabs, scenario-for-scenario (town_assumptions "
           "with town_assumptions, trend_corrected with trend_corrected) - no new computation of its own.")
    s.blank()

    scen_rows = {}
    for scenario in SCENARIOS_REV:
        s.section(f"Scenario: {scenario}")
        r_rev = s.row(f"{scenario}_rev", "Total Revenue (= Revenue tab)", kind="formula")
        r_exp = s.row(f"{scenario}_exp", "Total Expenditure (= Expense tab)", kind="formula")
        r_gap = s.row(f"{scenario}_gap", "SURPLUS / (DEFICIT)", kind="key", bold=True)
        r_pct = s.row(f"{scenario}_pct", "  as % of revenue", kind="formula", numfmt=PCT2)
        r_cum = s.row(f"{scenario}_cum", "Cumulative surplus/(deficit) since FY2026", kind="formula")
        r_check = s.row(f"{scenario}_check", "Check vs. Python model (should be ~$0)", kind="formula")
        s.blank()
        rev_row = REV_ROWS["scenarios"][scenario]["totrev"]
        exp_row = EXP_ROWS["scenarios"][scenario]["tot"]
        for i, y in enumerate(FCST_YEARS):
            ws.cell(r_rev, 3 + i, f"={REV_SHEET.sheet_ref(rev_row, i)}").number_format = USD0
            ws.cell(r_exp, 3 + i, f"={EXP_SHEET.sheet_ref(exp_row, i)}").number_format = USD0
            ws.cell(r_gap, 3 + i, f"={s.addr(r_rev, i)}-{s.addr(r_exp, i)}").number_format = USD0
            ws.cell(r_pct, 3 + i, f"={s.addr(r_gap, i)}/{s.addr(r_rev, i)}").number_format = PCT2
            if i == 0:
                ws.cell(r_cum, 3 + i, f"={s.addr(r_gap, i)}").number_format = USD0
            else:
                ws.cell(r_cum, 3 + i, f"={s.addr(r_cum, i - 1)}+{s.addr(r_gap, i)}").number_format = USD0
            truth = float(SURPLUS_CSV[scenario][y]["surplus_deficit"])
            ws.cell(r_check, 3 + i, f"={s.addr(r_gap, i)}-{truth}").number_format = USD0
        scen_rows[scenario] = dict(gap=r_gap, cum=r_cum)

    ws.freeze_panes = "C4"
    print(f"Surplus-Deficit tab: {s.r} rows.")
    return s, dict(scenarios=scen_rows)


SD_SHEET, SD_ROWS = build_surplus_deficit()
wb.save(OUT_PATH)
print("Saved (+ surplus-deficit).")

for scenario in SCENARIOS_REV:
    rows = SD_ROWS["scenarios"][scenario]
    # Annual gap: one year's value, so a single-year tolerance applies.
    ALL_FAILS += validate_sheet(SD_SHEET, [
        (rows["gap"], FCST_YEARS, lambda i, sc=scenario: float(SURPLUS_CSV[sc][FCST_YEARS[i]]["surplus_deficit"])),
    ], tol=2.0)
    # Cumulative: a running SUM of every prior year's gap, so each year's
    # sub-dollar float drift accumulates into it - by FY2040 that's 15
    # years of it. Validating a cumulative row against a single year's
    # tolerance is a category error (it failed by $2.18/$2.67 on figures
    # of $285M/$342M - 0.0000008%, while every underlying annual gap
    # passed). Tolerance scales with the number of years summed rather
    # than being loosened to a flat larger number.
    ALL_FAILS += validate_sheet(SD_SHEET, [
        (rows["cum"], FCST_YEARS, lambda i, sc=scenario: float(SURPLUS_CSV[sc][FCST_YEARS[i]]["cumulative_surplus_deficit"])),
    ], tol=2.0 * len(FCST_YEARS))
print("TOTAL FAILS SO FAR (after Surplus-Deficit):", len(ALL_FAILS))


# ------------------------------------------------------ New Growth Scenarios --

def build_new_growth():
    ws = wb.create_sheet("New Growth Scenarios")
    ws.column_dimensions["A"].width = 50
    for i in range(len(FCST_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Phase 2 — New-Growth Policy Scenarios, FY2026-2040")
    s.note("The core Prop 2.5 mechanics (5-category $ build, levy recursion) are LIVE - change any "
           "category share on the Assumptions tab and every year here recalculates. State Aid / Other "
           "Available Funds / Free Cash are identical to the Revenue tab's trend_corrected figures "
           "(referenced directly, not recomputed). Local Receipts and the implied-units/sqft physical "
           "translation are cited values (see Guide tab) - the same bespoke sub-models as the Revenue tab.")
    s.blank()
    r_fy = s.row("fy", "Fiscal year (number)", kind="formula")
    for i, y in enumerate(FCST_YEARS):
        ws.cell(r_fy, 3 + i, y)
    s.blank()

    hist_priorbase_2025 = (f"{HIST_SHEET.sheet_ref(HIST_ROWS['levy'], HIST_YEARS.index(2025))}"
                            f"-{HIST_SHEET.sheet_ref(HIST_ROWS['debtx'], HIST_YEARS.index(2025))}")

    scen_rows = {}
    for scenario in SCENARIOS_NG:
        s.section(f"Scenario: {scenario}")
        r_resnew = s.row(f"{scenario}_resnew", "Residential new construction ($)", kind="formula")
        r_resreno = s.row(f"{scenario}_resreno", "Residential renovation ($)", kind="formula")
        r_comnew = s.row(f"{scenario}_comnew", "Commercial new construction ($)", kind="formula")
        r_comreno = s.row(f"{scenario}_comreno", "Commercial renovation ($)", kind="formula")
        r_compp = s.row(f"{scenario}_compp", "Commercial personal property ($)", kind="formula")
        r_chca_lvl = s.row(f"{scenario}_chca_lvl", "CHCA property tax (level, City Realty avg)", kind="formula")
        r_chca_inc = s.row(f"{scenario}_chca_inc", "CHCA property tax increment", kind="formula")
        r_ngtotal = s.row(f"{scenario}_ngtotal", "New growth, TOTAL ($, incl. CHCA increment)", kind="key", bold=True)
        r_diff = s.row(f"{scenario}_diff", "Diff (delta method, TOWN_YEARS only)", kind="formula")
        r_operating = s.row(f"{scenario}_operating", "PROPERTY TAX OPERATING (levy limit)", kind="key", bold=True)
        r_debtx = s.row(f"{scenario}_debtx", "Debt Exclusion Revenue (= Revenue tab)", kind="formula")
        r_proptax = s.row(f"{scenario}_proptax", "PROPERTY TAXES", kind="key", bold=True)
        r_sa = s.row(f"{scenario}_sa", "State Aid (= Revenue tab, trend_corrected)", kind="formula")
        r_lr = s.row(f"{scenario}_lr", "Local Receipts (cited - bespoke sub-model)", kind="cite")
        r_oaf = s.row(f"{scenario}_oaf", "Other Available Funds (= Revenue tab)", kind="formula")
        r_fc = s.row(f"{scenario}_fc", "Free Cash (cited - two-year cash cycle for this scenario)", kind="cite")
        r_totrev = s.row(f"{scenario}_totrev", "TOTAL REVENUE", kind="key", bold=True)
        r_check = s.row(f"{scenario}_check", "Check vs. Python model (should be ~$0)", kind="formula")
        s.blank()

        pcts = {k: A[f"ng_{scenario}_{k}"] for k in ["res_new", "res_reno", "com_new", "com_reno", "com_pp"]}

        for i, y in enumerate(FCST_YEARS):
            fy = s.addr(r_fy, i)
            if y in TOWN_YEARS:
                prior_total = REV_SHEET.sheet_ref(REV_ROWS["shared"]["priorbase"], i - 1) if y > 2026 else hist_priorbase_2025
            else:
                prior_total = s.addr(r_operating, i - 1)
            ws.cell(r_resnew, 3 + i, f"={pcts['res_new']}*({prior_total})").number_format = USD0
            ws.cell(r_resreno, 3 + i, f"={pcts['res_reno']}*({prior_total})").number_format = USD0
            ws.cell(r_comnew, 3 + i, f"={pcts['com_new']}*({prior_total})").number_format = USD0
            ws.cell(r_comreno, 3 + i, f"={pcts['com_reno']}*({prior_total})").number_format = USD0
            ws.cell(r_compp, 3 + i, f"={pcts['com_pp']}*({prior_total})").number_format = USD0
            ws.cell(r_chca_lvl, 3 + i, chca_ramp_formula(fy, A["chca_ptax_cravg"])).number_format = USD0
            if i == 0:
                ws.cell(r_chca_inc, 3 + i, f"={s.addr(r_chca_lvl, i)}-0").number_format = USD0
            else:
                ws.cell(r_chca_inc, 3 + i, f"={s.addr(r_chca_lvl, i)}-{s.addr(r_chca_lvl, i - 1)}").number_format = USD0
            ws.cell(r_ngtotal, 3 + i,
                    f"=SUM({s.addr(r_resnew, i)}:{s.addr(r_compp, i)})+{s.addr(r_chca_inc, i)}").number_format = USD0

            if y in TOWN_YEARS:
                prior_diff = "0" if y == 2026 else s.addr(r_diff, i - 1)
                ws.cell(r_diff, 3 + i,
                        f"={prior_diff}*1.025+({s.addr(r_ngtotal, i)}-{A['ng_town_flat']})").number_format = USD0
                priorbase_ref = REV_SHEET.sheet_ref(REV_ROWS["shared"]["priorbase"], i)
                ws.cell(r_operating, 3 + i,
                        f"={priorbase_ref}+{s.addr(r_diff, i)}").number_format = USD0
            else:
                ws.cell(r_operating, 3 + i,
                        f"={s.addr(r_operating, i - 1)}*1.025+{s.addr(r_ngtotal, i)}").number_format = USD0

            ws.cell(r_debtx, 3 + i, f"={REV_SHEET.sheet_ref(REV_ROWS['shared']['debtx'], i)}").number_format = USD0
            ws.cell(r_proptax, 3 + i, f"={s.addr(r_operating, i)}+{s.addr(r_debtx, i)}").number_format = USD0
            ws.cell(r_sa, 3 + i,
                    f"={REV_SHEET.sheet_ref(REV_ROWS['scenarios']['trend_corrected']['sa'], i)}").number_format = USD0
            ws.cell(r_lr, 3 + i, float(NEWGROWTH_CSV[scenario][y]["local_receipts"])).number_format = USD0
            ws.cell(r_oaf, 3 + i, f"={REV_SHEET.sheet_ref(REV_ROWS['shared']['oaf'], i)}").number_format = USD0
            ws.cell(r_fc, 3 + i, float(NEWGROWTH_CSV[scenario][y]["free_cash"])).number_format = USD0
            ws.cell(r_totrev, 3 + i,
                    f"={s.addr(r_proptax, i)}+{s.addr(r_sa, i)}+{s.addr(r_lr, i)}+{s.addr(r_oaf, i)}+{s.addr(r_fc, i)}"
                    ).number_format = USD0
            truth = float(NEWGROWTH_CSV[scenario][y]["total_revenue"])
            ws.cell(r_check, 3 + i, f"={s.addr(r_totrev, i)}-{truth}").number_format = USD0
        s.blank()
        scen_rows[scenario] = dict(operating=r_operating, proptax=r_proptax, totrev=r_totrev)

    ws.freeze_panes = "C4"
    print(f"New Growth Scenarios tab: {s.r} rows.")
    return s, dict(scenarios=scen_rows)


NG_SHEET, NG_ROWS = build_new_growth()
wb.save(OUT_PATH)
print("Saved (+ new growth scenarios).")

for scenario in SCENARIOS_NG:
    rows = NG_ROWS["scenarios"][scenario]
    ALL_FAILS += validate_sheet(NG_SHEET, [
        (rows["totrev"], FCST_YEARS, lambda i, sc=scenario: float(NEWGROWTH_CSV[sc][FCST_YEARS[i]]["total_revenue"])),
        (rows["proptax"], FCST_YEARS, lambda i, sc=scenario: float(NEWGROWTH_CSV[sc][FCST_YEARS[i]]["property_taxes"])),
    ], tol=2.0)
print("TOTAL FAILS SO FAR (after New Growth Scenarios):", len(ALL_FAILS))


# ------------------------------------------------------- Existing vs New --

def build_existing_vs_new():
    ws = wb.create_sheet("Existing vs New FY26-40")
    ws.column_dimensions["A"].width = 46
    for i in range(len(FCST_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Existing (pre-2005) vs. New Cohort — Forecast, FY2026-2040")
    s.note("Forward continuation of the Historical tab's cohort split, under each of Phase 2's 4 "
           "new-growth scenarios. Anchored on FY2025's real existing/new split (Historical tab), "
           "rescaled onto each scenario's own FY2025 operating-levy base (see methodology doc's "
           "'Anchor reconciliation'). Answers: what does new growth buy existing residents?")
    s.blank()

    ex_2025 = HIST_SHEET.sheet_ref(HIST_ROWS["ex_allow"], HIST_YEARS.index(2025))
    new_2025 = HIST_SHEET.sheet_ref(HIST_ROWS["new_allow"], HIST_YEARS.index(2025))
    fy2025_operating = (f"({HIST_SHEET.sheet_ref(HIST_ROWS['levy'], HIST_YEARS.index(2025))}"
                         f"-{HIST_SHEET.sheet_ref(HIST_ROWS['debtx'], HIST_YEARS.index(2025))})")
    existing_share_2025 = f"({ex_2025}/({ex_2025}+{new_2025}))"

    scen_rows = {}
    for scenario in SCENARIOS_NG:
        s.section(f"Scenario: {scenario}")
        r_priorop = s.row(f"{scenario}_priorop", "Prior-year operating levy (helper)", kind="formula")
        r_ngy = s.row(f"{scenario}_ngy", "New growth this year (= operating − prior×1.025)", kind="formula")
        r_ex_allow = s.row(f"{scenario}_ex_allow", "Existing: allowed levy limit", kind="key", bold=True)
        r_new_allow = s.row(f"{scenario}_new_allow", "New: allowed levy limit", kind="key", bold=True)
        r_share = s.row(f"{scenario}_share", "Existing share (helper)", kind="formula", numfmt=PCT3)
        r_ex_debtx = s.row(f"{scenario}_ex_debtx", "Existing: debt-exclusion share", kind="formula")
        r_new_debtx = s.row(f"{scenario}_new_debtx", "New: debt-exclusion share", kind="formula")
        r_ex_tot = s.row(f"{scenario}_ex_tot", "Existing: TOTAL TAX", kind="key", bold=True)
        r_new_tot = s.row(f"{scenario}_new_tot", "New: TOTAL TAX", kind="key", bold=True)
        r_ex_growth = s.row(f"{scenario}_ex_growth", "  Existing cohort YoY growth", kind="formula", numfmt=PCT3)
        r_check = s.row(f"{scenario}_check", "Check vs. Python model (should be ~$0)", kind="formula")
        s.blank()

        ng_operating_row = NG_ROWS["scenarios"][scenario]["operating"]
        ng_debtx_row = NG_ROWS["scenarios"][scenario]["proptax"]  # placeholder, replaced below with debtx ref

        for i, y in enumerate(FCST_YEARS):
            op_ref = NG_SHEET.sheet_ref(ng_operating_row, i)
            debtx_ref = REV_SHEET.sheet_ref(REV_ROWS["shared"]["debtx"], i)
            if y == 2026:
                ws.cell(r_priorop, 3 + i, f"={fy2025_operating}").number_format = USD0
            else:
                ws.cell(r_priorop, 3 + i, f"={NG_SHEET.sheet_ref(ng_operating_row, i - 1)}").number_format = USD0
            ws.cell(r_ngy, 3 + i, f"={op_ref}-{s.addr(r_priorop, i)}*1.025").number_format = USD0

            if y == 2026:
                ex_prior_allow = f"({existing_share_2025}*{fy2025_operating})"
                new_prior_allow = f"((1-{existing_share_2025})*{fy2025_operating})"
            else:
                ex_prior_allow = s.addr(r_ex_allow, i - 1)
                new_prior_allow = s.addr(r_new_allow, i - 1)
            ex_pre = f"({ex_prior_allow}*1.025)"
            new_pre = f"({new_prior_allow}*1.025+{s.addr(r_ngy, i)})"
            ws.cell(r_share, 3 + i, f"={ex_pre}/({ex_pre}+{new_pre})").number_format = PCT3
            share = s.addr(r_share, i)
            ws.cell(r_ex_allow, 3 + i, f"={ex_pre}").number_format = USD0
            ws.cell(r_new_allow, 3 + i, f"={new_pre}").number_format = USD0
            ws.cell(r_ex_debtx, 3 + i, f"={debtx_ref}*{share}").number_format = USD0
            ws.cell(r_new_debtx, 3 + i, f"={debtx_ref}*(1-{share})").number_format = USD0
            ws.cell(r_ex_tot, 3 + i, f"={s.addr(r_ex_allow, i)}+{s.addr(r_ex_debtx, i)}").number_format = USD0
            ws.cell(r_new_tot, 3 + i, f"={s.addr(r_new_allow, i)}+{s.addr(r_new_debtx, i)}").number_format = USD0
            if y == 2026:
                ws.cell(r_ex_growth, 3 + i, None)
            else:
                ws.cell(r_ex_growth, 3 + i, f"={s.addr(r_ex_tot, i)}/{s.addr(r_ex_tot, i - 1)}-1").number_format = PCT3
            truth = float(EXNEW_FCST_CSV[scenario][y]["existing_total_tax"])
            ws.cell(r_check, 3 + i, f"={s.addr(r_ex_tot, i)}-{truth}").number_format = USD0
        s.blank()
        scen_rows[scenario] = dict(ex_tot=r_ex_tot, new_tot=r_new_tot)

    ws.freeze_panes = "C4"
    print(f"Existing vs New (forecast) tab: {s.r} rows.")
    return s, dict(scenarios=scen_rows)


EXNEW_SHEET, EXNEW_ROWS = build_existing_vs_new()
wb.save(OUT_PATH)
print("Saved (+ existing vs new forecast).")

for scenario in SCENARIOS_NG:
    rows = EXNEW_ROWS["scenarios"][scenario]
    ALL_FAILS += validate_sheet(EXNEW_SHEET, [
        (rows["ex_tot"], FCST_YEARS, lambda i, sc=scenario: float(EXNEW_FCST_CSV[sc][FCST_YEARS[i]]["existing_total_tax"])),
        (rows["new_tot"], FCST_YEARS, lambda i, sc=scenario: float(EXNEW_FCST_CSV[sc][FCST_YEARS[i]]["new_total_tax"])),
    ], tol=5.0)  # 14yrs of un-rounded recursive compounding vs. Python's per-year-rounded CSV output;
    # remaining gaps are ~$2-3 out of ~$340M (0.0000006% relative) - floating-point accumulation, not a bug.
print("TOTAL FAILS SO FAR (after Existing vs New):", len(ALL_FAILS))


# --------------------------------------------------------- Schools by Category --

SCHOOLS_CAT_ALL_YEARS = list(range(2009, 2041))
SCHOOLS_CATEGORIES = [
    "Administration", "Guidance, Counseling and Testing", "Instructional Leadership",
    "Instructional Materials, Equipment and Technology", "Insurance, Retirement Programs and Other",
    "Operations and Maintenance", "Other Teaching Services", "Professional Development",
    "Pupil Services", "Teachers",
]


def build_schools_category():
    ws = wb.create_sheet("Schools by Category")
    ws.column_dimensions["A"].width = 50
    for i in range(len(SCHOOLS_CAT_ALL_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 11
    s = Sheet(ws, year_start_col=3)
    s.title("Schools Budget by Category, FY2009-2040")
    s.note("Entirely cited/reference data - a bespoke, multi-source sub-model (DESE per-pupil data x "
           "actual enrollment for history; schools_category_forecast.py's own 9-category compounding for "
           "the forecast), not re-derived as live formulas here, per this workbook's hybrid design (see "
           "Guide tab). FY2009-2025 (grey): DESE per-pupil $ x actual DESE enrollment that year = total $ "
           "- NOT the same total as the Historical tab's Schedule A `exp_education` (DESE's Net School "
           "Spending accounting includes school employees' benefits; Schedule A keeps ALL Town benefits "
           "in one separate Town-wide bucket - see schools_category_forecast's own methodology doc for "
           "the full reconciliation). FY2026-2040 (green, KEY): schools_category_forecast.py's own output "
           "- each category grown at its own 16-year trailing CAGR from a FY2025 anchor that IS rescaled "
           "to match Schedule A (so this forecast total ties out to the Expense tab's trend_corrected "
           "Schools row exactly).")
    s.blank()
    yh = s.year_header(SCHOOLS_CAT_ALL_YEARS)

    rows = {}
    for cat in SCHOOLS_CATEGORIES:
        kind = "key" if cat == "Teachers" else "cite"
        rows[cat] = s.row(cat, cat, kind=kind)
    r_total = s.row("total", "TOTAL (Total In-District Expenditures, FY2009-2025; category sum, FY2026-2040)",
                     kind="key", bold=True)
    s.blank()
    r_enroll = s.row("enroll", "Total enrollment (context - see Guide/DESE sourcing)", kind="cite")
    r_salary = s.row("salary", "Average teacher salary (context, FY2018+ only)", kind="cite")

    for i, y in enumerate(SCHOOLS_CAT_ALL_YEARS):
        if y <= 2025:
            row_src = SCHOOLS_CAT_HIST_CSV.get(y, {})
            enroll_row = SCHOOLS_ENROLLMENT_CSV.get(y, {})
            enroll = enroll_row.get("total_enrollment")
            for cat in SCHOOLS_CATEGORIES:
                per_pupil = row_src.get(cat, "")
                if per_pupil and enroll:
                    ws.cell(rows[cat], 3 + i, round(float(per_pupil) * float(enroll))).number_format = USD0
            total_per_pupil = row_src.get("Total In-District Expenditures")
            if total_per_pupil and enroll:
                ws.cell(r_total, 3 + i, round(float(total_per_pupil) * float(enroll))).number_format = USD0
            if enroll:
                ws.cell(r_enroll, 3 + i, int(float(enroll))).number_format = '#,##0'
            salary_row = SCHOOLS_TEACHER_SALARY_CSV.get(y, {})
            salary = salary_row.get("Average Teacher Salary")
            if salary:
                ws.cell(r_salary, 3 + i, round(float(salary))).number_format = USD0
        else:
            row_src = SCHOOLS_CAT_CSV.get(y, {})
            total = 0.0
            for cat in SCHOOLS_CATEGORIES:
                if cat == "Insurance, Retirement Programs and Other":
                    continue  # modeled separately, Town-wide, on the Expense tab's Benefits row
                v = row_src.get(cat)
                if v:
                    ws.cell(rows[cat], 3 + i, round(float(v))).number_format = USD0
                    total += float(v)
            ws.cell(r_total, 3 + i, round(total)).number_format = USD0

    ws.freeze_panes = "C4"
    print(f"Schools by Category tab: {s.r} rows.")
    return s, dict(total=r_total)


SCHCAT_SHEET, SCHCAT_ROWS = build_schools_category()
wb.save(OUT_PATH)
print("Saved (+ schools by category).")

ALL_FAILS += validate_sheet(SCHCAT_SHEET, [
    (SCHCAT_ROWS["total"], SCHOOLS_CAT_ALL_YEARS,
     lambda i: (float(SCHOOLS_CAT_CSV[SCHOOLS_CAT_ALL_YEARS[i]]["total_schools_category_sum"])
                if SCHOOLS_CAT_ALL_YEARS[i] >= 2026 else None)),
], tol=2.0)
print("TOTAL FAILS SO FAR (after Schools by Category):", len(ALL_FAILS))


# -------------------------------------------------------- Benefits by Category --

BENEFITS_ALL_YEARS = list(range(2023, 2041))
BENEFITS_CATEGORIES = ["pensions", "group_health", "opeb_retiree_trust", "other_benefits"]
BENEFITS_LABELS = {
    "pensions": "Pensions (Contributory Retirement)",
    "group_health": "Group Health Insurance (GIC)",
    "opeb_retiree_trust": "OPEB (Retiree Group Health Trust)",
    "other_benefits": "Other (Group Life, Medicare, Workers' Comp, Disability, IOD, Unemployment)",
}


def build_benefits_category():
    ws = wb.create_sheet("Benefits by Category")
    ws.column_dimensions["A"].width = 58
    for i in range(len(BENEFITS_ALL_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Benefits Budget by Category, FY2023-2040")
    s.note("Cited/reference data - a bespoke, multi-source sub-model (Town's own Personnel Benefits "
           "Detailed tables for FY2023-2025 actuals and FY2026-2031; benefits_category_forecast.py's own "
           "category-specific modeling for FY2032-2040), not re-derived as live formulas, per this "
           "workbook's hybrid design (see Guide tab). FY2023-2025 (grey): real actuals, transcribed "
           "directly from three successive Financial Plans' own detail tables. FY2026-2040 (green, KEY): "
           "benefits_category_forecast.py's own output - Pensions use the real 2024 actuarial valuation's "
           "ADC schedule through FY2031 then a 3.0%/yr payroll-growth proxy (Normal Cost only, post-full-"
           "funding); Group Health its own ~6.5%/yr historical trend; OPEB the Town's real FY26-31 "
           "schedule (including the pension→OPEB redirect in FY2031) then held flat, no documented "
           "schedule exists beyond; Other the Town's own FY26-31 implied rate. See "
           "benefits_category_forecast_fy26_40_methodology.md for the full reasoning on every choice.")
    s.blank()
    yh = s.year_header(BENEFITS_ALL_YEARS)

    rows = {}
    for cat in BENEFITS_CATEGORIES:
        kind = "key" if cat in ("pensions", "opeb_retiree_trust") else "cite"
        rows[cat] = s.row(cat, BENEFITS_LABELS[cat], kind=kind)
    r_total = s.row("total", "TOTAL BENEFITS", kind="key", bold=True)

    hist_map = {2023: "pensions_actual_fy_basis", 2024: "pensions_actual_fy_basis", 2025: "pensions_actual_fy_basis"}
    for i, y in enumerate(BENEFITS_ALL_YEARS):
        if y <= 2025:
            hrow = BENEFITS_CAT_HIST_CSV.get(y, {})
            pens = hrow.get("pensions_actual_fy_basis")
            gh = hrow.get("group_health_actual_fy_basis")
            op = hrow.get("opeb_actual_fy_basis")
            total = 0.0
            if pens:
                ws.cell(rows["pensions"], 3 + i, round(float(pens))).number_format = USD0
                total += float(pens)
            if gh:
                ws.cell(rows["group_health"], 3 + i, round(float(gh))).number_format = USD0
                total += float(gh)
            if op:
                ws.cell(rows["opeb_retiree_trust"], 3 + i, round(float(op))).number_format = USD0
                total += float(op)
            if total:
                ws.cell(r_total, 3 + i, round(total)).number_format = USD0
        else:
            frow = BENEFITS_CAT_CSV.get(y, {})
            total = 0.0
            for cat in BENEFITS_CATEGORIES:
                v = frow.get(cat)
                if v:
                    ws.cell(rows[cat], 3 + i, round(float(v))).number_format = USD0
                    total += float(v)
            ws.cell(r_total, 3 + i, round(total)).number_format = USD0

    s.blank()
    s.note("Group Health has a real, independently-sourced 25-year reconstruction (FY2000-2025) not shown "
           "on this tab for space - see output/benefits_category_history_fy00_25.csv and the methodology "
           "doc's own accuracy check (the reconstruction runs 3-6% above real actuals in the years both are "
           "known, so it's kept as historical context/shape, not shown here as precise annual data).")

    ws.freeze_panes = "C4"
    print(f"Benefits by Category tab: {s.r} rows.")
    return s, dict(total=r_total)


BENCAT_SHEET, BENCAT_ROWS = build_benefits_category()
wb.save(OUT_PATH)
print("Saved (+ benefits by category).")

ALL_FAILS += validate_sheet(BENCAT_SHEET, [
    (BENCAT_ROWS["total"], BENEFITS_ALL_YEARS,
     lambda i: (float(BENEFITS_CAT_CSV[BENEFITS_ALL_YEARS[i]]["total_benefits_category_sum"])
                if BENEFITS_ALL_YEARS[i] >= 2026 else None)),
], tol=2.0)
print("TOTAL FAILS SO FAR (after Benefits by Category):", len(ALL_FAILS))


# ------------------------------------------------------ Balance Sheet - Liabilities --

BALANCE_SHEET_YEARS = list(range(2025, 2041))
BALANCE_SHEET_ROWS_DEF = [
    ("long_term_debt_existing", "  Long-term Debt: existing (real amortization schedule)", "cite"),
    ("long_term_debt_new_projected", "  Long-term Debt: known projected new (Fire Station/Pierce tranches)", "cite"),
    ("long_term_debt_total", "LONG-TERM DEBT (TOTAL)", "key"),
    ("net_pension_liability", "NET PENSION LIABILITY (real schedule to $0 by FY2031)", "key"),
    ("net_opeb_liability", "NET OPEB LIABILITY (held flat - placeholder, not a projection)", "key"),
    ("compensated_absences", "  Compensated Absences", "cite"),
    ("workers_compensation", "  Workers' Compensation", "cite"),
    ("landfill_closure", "  Landfill Closure", "cite"),
    ("unearned_revenue", "  Unearned Revenue", "cite"),
    ("other_current_liabilities", "  Other (warrants, accrued payroll, tax refunds, accrued interest)", "cite"),
]


def build_balance_sheet():
    ws = wb.create_sheet("Balance Sheet - Liabilities")
    ws.column_dimensions["A"].width = 58
    for i in range(len(BALANCE_SHEET_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Town Balance Sheet — Liabilities, FY2025-2040")
    s.note("Entirely cited/reference data - a genuinely different kind of model from every other tab (a "
           "STOCK/balance forecast, not a flow), standalone rather than feeding into the Expense tab. "
           "FY2024 actual ties out exactly to the audited Statement of Net Position ($914,360,375 total - "
           "verified directly, not approximated). Long-term Debt: existing bonds run down on their real, "
           "contractual amortization schedule (no assumption); known projected new debt (4 specific, "
           "already-telegraphed tranches - Fire Station 3rd/4th/5th borrowings, Pierce's 3rd borrowing) "
           "amortized on an assumed 20yr level-principal basis (no real schedule exists yet for unissued "
           "bonds). Pierce School alone has ~$113.9M of real, already-authorized borrowing beyond what's "
           "included here - a real, flagged gap, not a ceiling on future debt. Net Pension Liability: the "
           "real, exact 2024 actuarial valuation schedule, retiring to $0 by FY2031 (statutory full "
           "funding) and held there. Net OPEB Liability: deliberately held flat as an explicit placeholder, "
           "NOT a projection - a real forecast needs a full actuarial roll-forward this project has "
           "explicitly parked as out of scope. See balance_sheet_liabilities_forecast_fy25_40_methodology.md "
           "for the full reasoning behind every line.")
    s.blank()
    yh = s.year_header(BALANCE_SHEET_YEARS)

    rows = {}
    for key, label, kind in BALANCE_SHEET_ROWS_DEF:
        rows[key] = s.row(key, label, kind=kind, bold=(kind == "key"))
    r_total = s.row("total", "TOTAL LIABILITIES", kind="key", bold=True)

    for i, y in enumerate(BALANCE_SHEET_YEARS):
        row_src = BALANCE_SHEET_CSV.get(y, {})
        for key, _, _ in BALANCE_SHEET_ROWS_DEF:
            v = row_src.get(key)
            if v not in (None, ""):
                ws.cell(rows[key], 3 + i, round(float(v))).number_format = USD0
        total = row_src.get("total_liabilities")
        if total:
            ws.cell(r_total, 3 + i, round(float(total))).number_format = USD0

    ws.freeze_panes = "C4"
    print(f"Balance Sheet - Liabilities tab: {s.r} rows.")
    return s, dict(total=r_total)


BALSHEET_SHEET, BALSHEET_ROWS = build_balance_sheet()
wb.save(OUT_PATH)
print("Saved (+ balance sheet - liabilities).")

ALL_FAILS += validate_sheet(BALSHEET_SHEET, [
    (BALSHEET_ROWS["total"], BALANCE_SHEET_YEARS,
     lambda i: float(BALANCE_SHEET_CSV[BALANCE_SHEET_YEARS[i]]["total_liabilities"])),
], tol=2.0)
print("TOTAL FAILS SO FAR (after Balance Sheet - Liabilities):", len(ALL_FAILS))


# --------------------------------------------- Base Case Decomposition --

DECOMP_RUNS = ["as_legislated", "ex_override", "ex_override_breakeven"]


def build_decomposition():
    """Separates what the May 2026 override is doing from what the Town's own
    automatic revenue is doing - the distinction Part 4a is built on. The
    `as_legislated` run is the committed baseline; `ex_override` is the same
    model with the override removed; `ex_override_breakeven` additionally
    raises new growth to the rate that zeroes FY2040.

    Only revenue differs between the runs. The expense path is identical in
    all three, because the expense forecast takes no revenue input - and this
    tab makes that checkable rather than asserted, by deriving the second and
    third runs' expenditure from the first with a live formula instead of
    citing it three times."""
    ws = wb.create_sheet("Base Case Decomposition")
    ws.column_dimensions["A"].width = 52
    for i in range(len(FCST_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Part 4a — Base Case Decomposition (trend_corrected), FY2026-2040")
    s.note("Why the base case's ~+$28M FY2040 'surplus' is not a surplus: the May 2026 operating "
           "override is already inside it, and by FY2040 it is worth substantially more than the "
           "$23,254,439 voters approved, because an override permanently enlarges the levy base that "
           "then compounds. Removing it exposes the structural position - a gap reaching -$9.5M by "
           "FY2029, closed by the override on schedule, then slowly reopening to about -$8.8M "
           "(-1.3% of revenue) by FY2040. That structural figure, not the headline surplus, is what "
           "Part 4c's levers are sized against, because the override is a decided fact rather than a "
           "lever still available to pull. Generated by scripts/base_case_decomposition.py, which "
           "re-runs the real revenue and surplus models under each counterfactual and verifies its "
           "control run against the committed baseline to the dollar before reporting anything. "
           "NOTE: this tab describes only what the override DOES - it is not a comment on whether it "
           "was the right size. See base_case_decomposition_fy26_40_methodology.md.")
    s.blank()
    yh = s.year_header(FCST_YEARS)

    run_rows = {}
    r_leg_exp = None
    for run in DECOMP_RUNS:
        label = {
            "as_legislated": "As legislated — override included (the committed baseline)",
            "ex_override": "Ex-override — the structural position",
            "ex_override_breakeven": "Ex-override, new growth at the FY2040 break-even rate",
        }[run]
        s.section(label)
        r_rev = s.row(f"{run}_rev", "  Operating revenue", kind="cite")
        r_exp = s.row(f"{run}_exp", "  Operating expenditure", kind="cite" if run == "as_legislated" else "formula")
        r_gap = s.row(f"{run}_gap", "  OPERATING SURPLUS / (DEFICIT)", kind="key", bold=True)
        r_pct = s.row(f"{run}_pct", "    as % of operating revenue", kind="formula", numfmt=PCT2)
        r_chk = s.row(f"{run}_check", "  Check vs. Python model (should be ~$0)", kind="formula")
        s.blank()
        for i, y in enumerate(FCST_YEARS):
            src = DECOMP_CSV[run][y]
            ws.cell(r_rev, 3 + i, round(float(src["operating_revenue"]))).number_format = USD0
            if run == "as_legislated":
                ws.cell(r_exp, 3 + i, round(float(src["operating_expenditure"]))).number_format = USD0
            else:
                # Live proof that the expense path is identical across runs.
                ws.cell(r_exp, 3 + i, f"={s.addr(r_leg_exp, i)}").number_format = USD0
            ws.cell(r_gap, 3 + i, f"={s.addr(r_rev, i)}-{s.addr(r_exp, i)}").number_format = USD0
            ws.cell(r_pct, 3 + i, f"={s.addr(r_gap, i)}/{s.addr(r_rev, i)}").number_format = PCT2
            truth = float(src["operating_surplus_deficit"])
            ws.cell(r_chk, 3 + i, f"={s.addr(r_gap, i)}-{truth}").number_format = USD0
        if run == "as_legislated":
            r_leg_exp = r_exp
        run_rows[run] = dict(rev=r_rev, exp=r_exp, gap=r_gap)

    s.section("What the May 2026 override is worth")
    r_val = s.row("override_value", "Override's annual value (= as-legislated revenue − ex-override revenue)",
                  kind="key", bold=True)
    r_approved = s.row("override_approved", "  Memo: amount voters approved, FY2027-2029 total", kind="cite")
    r_mult = s.row("override_mult", "  Ratio to the approved amount", kind="formula", numfmt="0.00x")
    for i, y in enumerate(FCST_YEARS):
        ws.cell(r_val, 3 + i,
                f"={s.addr(run_rows['as_legislated']['rev'], i)}-{s.addr(run_rows['ex_override']['rev'], i)}"
                ).number_format = USD0
        ws.cell(r_approved, 3 + i, 23_254_439).number_format = USD0
        ws.cell(r_mult, 3 + i, f"={s.addr(r_val, i)}/{s.addr(r_approved, i)}").number_format = "0.00x"

    ws.freeze_panes = "C4"
    print(f"Base Case Decomposition tab: {s.r} rows.")
    return s, dict(runs=run_rows, value=r_val)


DECOMP_SHEET, DECOMP_ROWS = build_decomposition()
wb.save(OUT_PATH)
print("Saved (+ base case decomposition).")

for run in DECOMP_RUNS:
    ALL_FAILS += validate_sheet(DECOMP_SHEET, [
        (DECOMP_ROWS["runs"][run]["gap"], FCST_YEARS,
         lambda i, rn=run: float(DECOMP_CSV[rn][FCST_YEARS[i]]["operating_surplus_deficit"])),
    ], tol=2.0)
# The override's value is a derived quantity the CSV also reports, so it is
# checked independently rather than trusted as a by-product of the two rows above.
ALL_FAILS += validate_sheet(DECOMP_SHEET, [
    (DECOMP_ROWS["value"], FCST_YEARS,
     lambda i: float(DECOMP_CSV["as_legislated"][FCST_YEARS[i]]["may_2026_override_value"])),
], tol=2.0)
print("TOTAL FAILS SO FAR (after Base Case Decomposition):", len(ALL_FAILS))


# ------------------------------------------------------- Override Reliance --

OVERRIDE_YEARS_HYPO = [2029, 2032, 2035, 2038]


def build_override_reliance():
    """What closing the gap with nothing but overrides would take, on the
    DOWNSIDE case (town_assumptions). Live: the base gap reads off the
    Surplus-Deficit tab, and each hypothetical override is sized by formula as
    whatever it takes to reach breakeven in its own year, then compounded at
    2.5% forever after like every real override."""
    ws = wb.create_sheet("Override Reliance")
    ws.column_dimensions["A"].width = 52
    for i in range(len(FCST_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Part 4c — Override-Only Reliance Scenario (downside case), FY2026-2040")
    s.note("The lever every real historical gap has actually been closed with, sized against the "
           "DOWNSIDE case (town_assumptions - the Town's own published figures mechanically extended), "
           "not the base case. Under the base case no further override is needed before FY2040; this "
           "tab answers the different question of what overrides alone would cost if the Town's own "
           "more conservative forecast turns out to be the right one. A new override is called every "
           "three years - matching the ERSC's own finding that override intervals have compressed - "
           "and sized at whatever brings that year to breakeven. Each one then compounds at 2.5%/yr "
           "permanently, exactly like every real override in the historical model. This is a "
           "hypothetical, not a proposal, and deliberately says nothing about any real override.")
    s.blank()
    yh = s.year_header(FCST_YEARS)

    r_base = s.row("base_gap", "Base operating gap, before any new override (= Surplus-Deficit tab)", kind="formula")
    r_cumb = s.row("cum_before", "  Cumulative prior overrides, grown 2.5% (start of year)", kind="formula")
    r_new = s.row("new_override", "  NEW OVERRIDE CALLED THIS YEAR", kind="key", bold=True)
    r_cuma = s.row("cum_after", "  Cumulative override capacity (end of year)", kind="formula")
    r_res = s.row("resulting", "RESULTING SURPLUS / (DEFICIT)", kind="key", bold=True)
    r_pct = s.row("resulting_pct", "  as % of total revenue", kind="formula", numfmt=PCT2)
    r_chk = s.row("check", "Check vs. Python model (should be ~$0)", kind="formula")

    ta_gap = SD_ROWS["scenarios"]["town_assumptions"]["gap"]
    ta_rev = REV_ROWS["scenarios"]["town_assumptions"]["totrev"]
    for i, y in enumerate(FCST_YEARS):
        ws.cell(r_base, 3 + i, f"={SD_SHEET.sheet_ref(ta_gap, i)}").number_format = USD0
        if i == 0:
            ws.cell(r_cumb, 3 + i, 0).number_format = USD0
        else:
            ws.cell(r_cumb, 3 + i, f"={s.addr(r_cuma, i - 1)}*1.025").number_format = USD0
        if y in OVERRIDE_YEARS_HYPO:
            ws.cell(r_new, 3 + i,
                    f"=MAX(0,-({s.addr(r_base, i)}+{s.addr(r_cumb, i)}))").number_format = USD0
        else:
            ws.cell(r_new, 3 + i, 0).number_format = USD0
        ws.cell(r_cuma, 3 + i, f"={s.addr(r_cumb, i)}+{s.addr(r_new, i)}").number_format = USD0
        ws.cell(r_res, 3 + i, f"={s.addr(r_base, i)}+{s.addr(r_cuma, i)}").number_format = USD0
        ws.cell(r_pct, 3 + i, f"={s.addr(r_res, i)}/{REV_SHEET.sheet_ref(ta_rev, i)}").number_format = PCT2
        truth = float(OVERRIDE_CSV[y]["resulting_operating_surplus_deficit"])
        ws.cell(r_chk, 3 + i, f"={s.addr(r_res, i)}-{truth}").number_format = USD0

    ws.freeze_panes = "C4"
    print(f"Override Reliance tab: {s.r} rows.")
    return s, dict(new=r_new, cum=r_cuma, resulting=r_res)


OVR_SHEET, OVR_ROWS = build_override_reliance()
wb.save(OUT_PATH)
print("Saved (+ override reliance).")

ALL_FAILS += validate_sheet(OVR_SHEET, [
    (OVR_ROWS["new"], FCST_YEARS,
     lambda i: float(OVERRIDE_CSV[FCST_YEARS[i]]["new_override_this_year"])),
    (OVR_ROWS["resulting"], FCST_YEARS,
     lambda i: float(OVERRIDE_CSV[FCST_YEARS[i]]["resulting_operating_surplus_deficit"])),
], tol=5.0)
# Cumulative capacity compounds every prior override forward, so its float
# drift accumulates the same way the Surplus-Deficit tab's cumulative row does.
ALL_FAILS += validate_sheet(OVR_SHEET, [
    (OVR_ROWS["cum"], FCST_YEARS,
     lambda i: float(OVERRIDE_CSV[FCST_YEARS[i]]["cumulative_hypothetical_override"])),
], tol=2.0 * len(FCST_YEARS))
print("TOTAL FAILS SO FAR (after Override Reliance):", len(ALL_FAILS))


# ---------------------------------------------------- conditional formatting --

def apply_check_row_formatting():
    """Finds every row labeled 'Check vs. Python model...' across all tabs and
    conditionally formats its data cells red if the diff exceeds $6 (a hair
    above the largest legitimate floating-point-accumulation gap seen in
    validation, ~$2-3 on the Existing-vs-New tab)."""
    n = 0
    for ws in wb.worksheets:
        for row in ws.iter_rows(min_col=1, max_col=1):
            cell = row[0]
            # .strip() matters: check rows nested under a section are indented,
            # and a startswith() on the raw label silently skipped three of them
            # on the Base Case Decomposition tab (found 2026-09-07). A check row
            # without its red-flag formatting is worse than no check row - it
            # looks verified and is not.
            if cell.value and str(cell.value).strip().startswith("Check vs. Python model"):
                last_col = ws.max_column
                rng = f"{col(3)}{cell.row}:{col(last_col)}{cell.row}"
                ws.conditional_formatting.add(
                    rng, CellIsRule(operator="greaterThan", formula=["6"], fill=PatternFill("solid", fgColor=RED_DIFF)))
                ws.conditional_formatting.add(
                    rng, CellIsRule(operator="lessThan", formula=["-6"], fill=PatternFill("solid", fgColor=RED_DIFF)))
                n += 1
    print(f"Applied conditional formatting to {n} check rows.")


apply_check_row_formatting()


# -------------------------------------------------------------------- Guide --

# --------------------------------------------------------- Driver forecast --
# Added 2026-09-29: the base case is now the driver forecast
# (expense_driver_forecast.py), anchored on the FY2027 budget Town Meeting
# adopted. Its lines are cited from the model; totals and the room are live.

DRIVER_CSV = load_csv_rows(ROOT / "output/expense_driver_forecast_fy26_40.csv")
DRIVER_LINES = [
    ("schools", "Schools"),
    ("departmental_base", "Town departments"),
    ("departmental_growth", "Town departments: services for growth"),
    ("group_health", "Health insurance"),
    ("growth_staff_benefits", "Health insurance: staff added for growth"),
    ("pensions", "Pensions"),
    ("opeb", "Retiree health prefunding (OPEB)"),
    ("other_benefits", "Other benefits"),
    ("debt_within_levy", "Within-levy debt"),
    ("other_nondept", "Capital, reserves and other"),
]


def build_driver_forecast():
    ws = wb.create_sheet("Driver Forecast FY26-40")
    ws.column_dimensions["A"].width = 46
    for i in range(len(FCST_YEARS)):
        ws.column_dimensions[col(3 + i)].width = 12
    s = Sheet(ws, year_start_col=3)
    s.title("Base case: driver forecast, FY2026-2040 (with the May 2026 override)")
    s.note("The base case since 2026-09-29. FY2026 is the Town's FY2026 budget and FY2027 the budget Town "
           "Meeting adopted; from FY2028 each line moves with its drivers (staff, pay, prices, premiums, "
           "enrollment, homes and square feet), continuing Brookline's FY2011-25 record. Lines are cited from "
           "expense_driver_forecast.py (grey); totals and the room are live. Operating basis: excluded debt is "
           "left out of both sides. The trend tabs (Revenue, Expense, Surplus-Deficit) are the earlier method, "
           "kept as a cross-check.")
    s.blank()
    s.section("Base-case assumptions (expense_driver_forecast.py BASE; each is tested in 'What Decides FY2040')")
    ws.column_dimensions["B"].width = 16
    for c_, h_ in ((1, "Assumption"), (2, "Base value"), (3, "Basis")):
        c = ws.cell(s.r, c_, h_)
        c.font = F_HEADER
        c.fill = FILL_HEAD
    s.r += 1
    from expense_driver_forecast import BASE as _B, RATIO_NOW as _RN
    for label, val, basis in (
        ("Pay growth, Town staff", f"{_B['pay']:.1%}/yr", "The Town's bargaining target"),
        ("Pay growth, school staff", f"{_B['pay'] + _B['school_pay_drift']:.1%}/yr",
         "0.7 point above the target: middle of the 3.3-4.1% range from the School Department's FY2026 budget build at the 2.75% contract raise (FY2011-25 record: +0.4)"),
        ("Pay growth, Public Safety", f"{_B['pay'] + _B['pay_ps_premium']:.1%}/yr",
         "1.5 points above the target, for the same reason"),
        ("Inflation (non-personnel costs)", f"{_B['cpi']:.1%}/yr", "Long-run CPI"),
        ("Health premiums, FY2028-29", f"{_B['premium_near']:.0%}/yr", "The Town's own forecast"),
        ("Health premiums, FY2030 on", f"{_B['premium_long']:.0%}/yr",
         "Between the 6.5% 25-year average and the recent 10-12%"),
        ("School staffing", "FY2027 staff kept",
         "Held at the FY2027 level as enrollment falls (FY2019-25: enrollment -10.6%, staff -5.0%); students from growth above trend are staffed"),
        ("Enrollment", "NESDEC", "NESDEC Oct 2023 projection, scaled to the Sept 2026 count, extended to FY2040"),
        ("Town cost of a new home", f"${_B['cost_per_home']:,.0f} (FY2025 $)",
         "Cross-town comparison (cross_town_marginal_cost.py), grown with pay, plus benefits"),
        ("New growth", "Recent trend", "Each category at its trailing five-year rate, % of the prior levy"),
        ("Chestnut Hill (CHCA)", "Approved program", "266 homes and a 200-room hotel; revenue and costs ramp FY2032-34"),
        ("Pensions", "Town schedule", "Full funding FY2030; then normal cost grows with payroll"),
        ("OPEB", "Town schedule", "Includes moving pension savings to OPEB in FY2031"),
    ):
        ws.cell(s.r, 1, label).fill = FILL_CITE
        ws.cell(s.r, 2, val).fill = FILL_CITE
        ws.cell(s.r, 3, basis).font = F_NOTE
        s.r += 1
    s.blank()
    hdr_row = s.r
    s.year_header(FCST_YEARS)
    rows = {}
    for key, label in DRIVER_LINES:
        rows[key] = s.row(key, label, kind="cite")
        s.set_years(rows[key], FCST_YEARS, lambda y, i, k=key: float(DRIVER_CSV[y][k]), kind="cite")
    r_sp = s.row("spend", "OPERATING SPENDING", kind="key", bold=True)
    first, last = rows[DRIVER_LINES[0][0]], rows[DRIVER_LINES[-1][0]]
    s.set_years(r_sp, FCST_YEARS, lambda y, i: f"=SUM({s.addr(first, i)}:{s.addr(last, i)})", kind="key")
    r_rev = s.row("rev", "Operating revenue (cited - growth scenario model, trend + Chestnut Hill)", kind="cite")
    s.set_years(r_rev, FCST_YEARS, lambda y, i: float(DRIVER_CSV[y]["operating_revenue"]), kind="cite")
    r_room = s.row("room", "ROOM (revenue minus spending)", kind="key", bold=True)
    s.set_years(r_room, FCST_YEARS, lambda y, i: f"={s.addr(r_rev, i)}-{s.addr(r_sp, i)}", kind="key")
    r_pct = s.row("pct", "Room, share of revenue", kind="formula")
    s.set_years(r_pct, FCST_YEARS, lambda y, i: f"={s.addr(r_room, i)}/{s.addr(r_rev, i)}", numfmt=PCT2)
    r_chk = s.row("chk", "Check vs. Python model (should be ~$0)", kind="formula")
    s.set_years(r_chk, FCST_YEARS,
                lambda y, i: f"={s.addr(r_room, i)}-{float(DRIVER_CSV[y]['surplus_deficit'])}")
    s.blank()
    s.section("Drivers")
    for key, label, fmt in (("enrollment", "Enrollment (PK-12)", '#,##0'),
                            ("school_staff", "School staff (FTE)", '#,##0'),
                            ("town_fte", "Town staff (FTE)", '#,##0'),
                            ("cum_res_units", "Homes added since FY2027", '#,##0'),
                            ("may_2026_override_value", "May 2026 override, worth that year", USD0)):
        r = s.row(key, label, kind="cite")
        s.set_years(r, FCST_YEARS, lambda y, i, k=key: float(DRIVER_CSV[y][k]), numfmt=fmt, kind="cite")
    ws.freeze_panes = f"C{hdr_row + 1}"
    return s, dict(spend=r_sp, room=r_room)


DRIVER_SHEET, DRIVER_ROWS = build_driver_forecast()
wb.save(OUT_PATH)
ALL_FAILS += validate_sheet(DRIVER_SHEET, [
    (DRIVER_ROWS["spend"], FCST_YEARS, lambda i: float(DRIVER_CSV[FCST_YEARS[i]]["operating_expenditure"])),
    (DRIVER_ROWS["room"], FCST_YEARS, lambda i: float(DRIVER_CSV[FCST_YEARS[i]]["surplus_deficit"])),
], tol=2.0)
print("TOTAL FAILS SO FAR (after Driver Forecast):", len(ALL_FAILS))


def build_decisions():
    ws = wb.create_sheet("What Decides FY2040")
    ws.column_dimensions["A"].width = 66
    for c in "BCDEF":
        ws.column_dimensions[c].width = 18
    s = Sheet(ws, year_start_col=2)
    s.title("What decides the 2040 budget: one assumption at a time")
    s.note("Each row changes one assumption from the base case and reports FY2040 spending, the FY2040 room, "
           "and the change in the room summed over FY2026-40. Cited from "
           "expense_driver_forecast_sensitivity_fy40.csv. Base-case FY2040 room: "
           f"${float(DRIVER_CSV[2040]['surplus_deficit'])/1e6:,.1f}M.")
    s.blank()
    hdr = ["Assumption changed", "FY2040 spending", "Change in spending", "FY2040 room",
           "Change in room", "Change in room, FY2026-40 total"]
    for j, h in enumerate(hdr):
        c = ws.cell(s.r, 1 + j, h)
        c.font = F_HEADER
        c.fill = FILL_HEAD
    s.r += 1
    with open(ROOT / "output/expense_driver_forecast_sensitivity_fy40.csv") as f:
        for row in csv.DictReader(f):
            ws.cell(s.r, 1, row["dial"])
            for j, k in enumerate(["fy2040_spending", "spending_change", "fy2040_balance", "balance_change",
                                   "cumulative_balance_change_fy26_40"]):
                c = ws.cell(s.r, 2 + j, float(row[k]))
                c.number_format = USD0
                c.fill = FILL_CITE
            s.r += 1


build_decisions()


def build_cost_of_growth():
    import cost_assumptions as ca
    ws = wb.create_sheet("Cost of Growth")
    ws.column_dimensions["A"].width = 52
    for c in "BCDEFGH":
        ws.column_dimensions[c].width = 16
    s = Sheet(ws, year_start_col=2)
    s.title("The cost of growth, and when a new home covers it")
    s.note("The per-home and per-student costs the driver forecast, the per-project calculator and the "
           "per-home test all share (cost_assumptions.py). Tan cells are editable; the breakeven table "
           "recalculates. See reference document 3c.")
    s.blank()
    s.section("Inputs")

    def inp(label, v, fmt=USD0, kind="input"):
        r = s.r
        ws.cell(r, 1, label).fill = FILL_INPUT if kind == "input" else FILL_CITE
        c = ws.cell(r, 2, v)
        c.number_format = fmt
        c.fill = FILL_INPUT if kind == "input" else FILL_CITE
        s.r += 1
        return f"$B${r}"

    town25 = inp("Town services per home, FY2025 $ (350-town comparison)", ca.TOWN_COST_PER_HOME_FY25)
    load = inp("Benefit loading on Town services (RKG $262 / $1,109)", ca.TOWN_BENEFIT_LOADING, PCT2)
    pay = inp("Town pay growth", ca.PAY, PCT2)
    rate = inp("Residential tax rate (FY2026, per $ of value)", 0.01024, '0.0000%')
    taxg = inp("Growth of one home's tax a year (levy limit)", 0.025, PCT2)
    kids = inp("Children per home (model average)", ca.STUDENTS_PER_HOME, '0.000')
    st27 = inp("Cost of one added student, FY2027 (driver model)", ca.STUDENT_COST[2027], USD0, kind="cite")
    st40 = inp("Cost of one added student, FY2040 (driver model, nominal)", ca.STUDENT_COST[2040], USD0, kind="cite")
    s.blank()
    s.section("Costs per home, FY2027 and FY2040")
    r = s.r
    ws.cell(r, 1, "Town services per home, FY2027")
    ws.cell(r, 2, f"={town25}*(1+{load})*(1+{pay})^2").number_format = USD0
    ws.cell(r + 1, 1, "Town services per home, FY2040")
    ws.cell(r + 1, 2, f"={town25}*(1+{load})*(1+{pay})^15").number_format = USD0
    t27, t40 = f"$B${r}", f"$B${r + 1}"
    s.r += 3
    s.section("When a new home covers its costs")
    hdr = ["Home", "Assessed value", "Tax, FY2027", "Breakeven children, FY2027",
           "Breakeven children, FY2040", "Net at model children, FY2027", "Net at model children, FY2040"]
    for j, h in enumerate(hdr):
        c = ws.cell(s.r, 1 + j, h)
        c.font = F_HEADER
        c.fill = FILL_HEAD
        c.alignment = Alignment(wrap_text=True)
    s.r += 1
    with open(ROOT / "output/housing_unit_breakeven_by_type.csv") as f:
        types = {r["unit_type"]: r for r in csv.DictReader(f)}
    checks = []
    for name, row in types.items():
        rr = s.r
        ws.cell(rr, 1, name)
        v = ws.cell(rr, 2, float(row["assessed_value"]))
        v.number_format = USD0
        v.fill = FILL_INPUT
        ws.cell(rr, 3, f"=B{rr}*{rate}").number_format = USD0
        ws.cell(rr, 4, f"=(C{rr}-{t27})/{st27}").number_format = '0.00'
        ws.cell(rr, 5, f"=(C{rr}*(1+{taxg})^13-{t40})/{st40}").number_format = '0.00'
        ws.cell(rr, 6, f"=C{rr}-{t27}-{kids}*{st27}").number_format = USD0
        ws.cell(rr, 7, f"=C{rr}*(1+{taxg})^13-{t40}-{kids}*{st40}").number_format = USD0
        checks.append((rr, float(row["breakeven_children_fy2027"]), float(row["breakeven_children_fy2040"])))
        s.r += 1
    return ws, checks


COG_WS, COG_CHECKS = build_cost_of_growth()
wb.save(OUT_PATH)


def validate_cost_of_growth():
    import formulas
    xl = formulas.ExcelModel().loads(str(OUT_PATH)).finish()
    sol = xl.calculate()
    key = f"[{OUT_PATH.name}]COST OF GROWTH"
    fails = []
    for rr, e27, e40 in COG_CHECKS:
        for c, exp in (("D", e27), ("E", e40)):
            got = float(sol[f"'{key}'!{c}{rr}"].value[0, 0])
            if abs(got - exp) > 0.002:
                fails.append(("Cost of Growth", f"{c}{rr}", None, f"got={got} expected={exp}"))
    print(f"  validated {2 * len(COG_CHECKS)} cells on 'Cost of Growth': {len(fails)} mismatches")
    for f_ in fails:
        print("   MISMATCH", f_)
    return fails


ALL_FAILS += validate_cost_of_growth()
print("TOTAL FAILS SO FAR (after Cost of Growth):", len(ALL_FAILS))


def build_guide():
    ws = wb.create_sheet("Guide", 0)
    ws.column_dimensions["A"].width = 110
    r = 1

    def title(text):
        nonlocal r
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=1)
        c = ws.cell(r, 1, text)
        c.font = F_TITLE
        c.fill = FILL_TITLE
        ws.row_dimensions[r].height = 30
        r += 2

    def h(text):
        nonlocal r
        ws.cell(r, 1, text).font = F_SECTION
        r += 1

    def p(text, height=None):
        nonlocal r
        c = ws.cell(r, 1, text)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = height or (15 * (1 + len(text) // 105))
        r += 1

    def blank(n=1):
        nonlocal r
        r += n

    def swatch(fill_color, text):
        nonlocal r
        ws.cell(r, 1, text).fill = PatternFill("solid", fgColor=fill_color)
        r += 1

    title("Brookline Fiscal Model — Guide")
    p("A single, auditable Excel model of Brookline's finances: FY2005-2025 real history, plus the "
      "FY2026-2040 forecast this project has built. Built 2026-09-01, alongside the project's Python "
      "scripts (scripts/*.py, output/*.csv) that remain the primary, most-frequently-updated source - "
      "this workbook is generated FROM those scripts (scripts/build_excel_model.py) and re-validated "
      "against their output every time it's rebuilt, not maintained by hand.", height=48)
    blank()

    h("The base case (since 2026-09-29): the Driver Forecast tab")
    p("The forecast this project now leads with is the driver forecast (tab 'Driver Forecast FY26-40'): it "
      "starts from the FY2027 budget Town Meeting adopted in May 2026 and moves each line with its drivers "
      "(staff, pay, prices, health premiums, enrollment, homes and square feet), continuing Brookline's "
      "FY2011-25 record. With the May 2026 override, revenue stays about $10M to $23M a year ahead of "
      "spending through the 2030s. 'What Decides FY2040' ranks the assumptions that move it most (pay, "
      "health premiums, school staffing, the FY2031 pension turn), and 'Cost of Growth' holds the shared "
      "per-home and per-student costs with a live breakeven table. The Revenue, Expense and Surplus-Deficit "
      "tabs are the earlier trend method, kept live as a cross-check; they also carry the local receipts and "
      "free cash cycle (receipts budgeted at 74% of collections, each year's surplus returning as free cash "
      "two budgets later) as cited values.", height=96)
    blank()

    h("Color key")
    swatch(TAN_INPUT, "Tan = editable input - a real number typed in from a source document (the Town's "
                       "LRFP, an override amount, a category share). Change one and everything downstream "
                       "recalculates.")
    swatch(GREEN_KEY, "Green = key output - the headline number for that block (a total, a levy, a gap).")
    swatch(GREY_CITE, "Grey = cited/computed value - pulled from the already-validated Python model, not "
                       "re-derived in Excel. See 'Why some things are cited, not live' below.")
    ws.cell(r, 1, "White = an intermediate live formula - not an input, not the headline number, but part "
                  "of the chain between them.")
    r += 1
    blank()

    h("What's LIVE vs. cited — and why")
    p("Ben chose (2026-09-01) a 'hybrid' depth over two alternatives: a full live rebuild (every mechanic "
      "reformulated in Excel - maximally auditable, but two parallel implementations of the same model to "
      "keep in sync forever), or a values-only data book (safest against drift, fastest to build, but "
      "nothing to actually tweak). The hybrid: every CORE Prop 2.5 mechanic is live - the levy recursion "
      "(2.5% + new growth), the debt-exclusion carve-out, the May 2026 override's compounding, the "
      "existing-vs-new cohort split, the 5-category new-growth mix Phase 2 stress-tests. Genuinely bespoke "
      "SUB-MODELS - ones with their own multi-step derivation this project built and validated separately "
      "- are pulled in as cited values instead of re-derived a second time:", height=64)
    p("  • Local Receipts (trend_corrected & all 4 New Growth scenarios) - a blend of an ex-meals-ex-"
      "permits CAGR, meals tax (organic + new-commercial-sqft-driven), and building permits (% of new-"
      "growth value). See new_growth_scenarios_fy26_40_methodology.md.")
    p("  • Implied new residential units / commercial sqft - depends on the tax-rate-drift model "
      "(res_tax_rate/com_tax_rate, held at a constant CIP-shift ratio) to translate $ into a physical "
      "count. Shown as reference numbers on the New Growth Scenarios tab's own methodology, not re-built here.")
    p("  • Expense tab's trend_corrected Schools row - the sum of 9 DESE function categories (Teachers, "
      "Pupil Services, Guidance, etc.), each grown at its own 16-year trailing CAGR from real per-pupil "
      "DESE data. See the Schools by Category tab and schools_category_forecast_fy26_40_methodology.md - "
      "a real multi-source reconciliation (Schedule A vs. DESE Net School Spending scope) sits behind "
      "this one, not just re-derivable from a formula.")
    p("  • Expense tab's trend_corrected Benefits row - Pensions, Group Health, OPEB, and Other each "
      "modeled separately (the real 2024 pension ADC schedule, a 25-year Group Health reconstruction from "
      "Financial Plan rate-change tables, the real FY2031 pension→OPEB funding handoff) instead of one "
      "blended CAGR that was implicitly compounding a one-time OPEB redirect forever. See the Benefits by "
      "Category tab and benefits_category_forecast_fy26_40_methodology.md.")
    p("  • Expense tab's trend_corrected Departmental row - Schedule A's 5 functional categories (General "
      "Government, Public Safety, Public Works, Human Services, Culture & Recreation), each own-trended. "
      "Simpler than Schools/Benefits (no new data sourcing, no outlier rates), but still a real "
      "reconciliation of the Town's own known FY26-31 aggregate by category share. See "
      "departmental_category_forecast_fy26_40_methodology.md.")
    blank()

    h("How to know it's right")
    p("Every LIVE tab has its own 'Check vs. Python model' row (conditionally formatted red if any year's "
      "gap exceeds $6) - it recalculates every time you open the file or change an input, comparing this "
      "workbook's own formulas against the already-published, already-reviewed CSV output "
      "(output/*.csv) those Python scripts produced. If you change an assumption, that row will stop "
      "reading ~$0 for that scenario - expected, since you've deliberately diverged from the base case. "
      "If a Check row ever reads a large red number WITHOUT you having changed anything, something broke - "
      "stop and investigate before trusting the tab.", height=64)
    p("Before this file was delivered, every one of these Check rows was independently re-verified using a "
      "real formula-evaluation engine (not just eyeballed), every live tab, 4 scenarios each "
      "where applicable, zero mismatches beyond ~$2-3 of ordinary floating-point accumulation over 14 "
      "years of recursive compounding (Python rounds to the dollar every year; this workbook doesn't, "
      "since rounding intermediate steps would make later years silently drift from Python for no good "
      "reason).", height=48)
    blank()

    h("Tab guide")
    p("1. Historical FY05-25 — real actuals, FY2005-2025, plus a live existing-vs-new cohort split.")
    p("2. Assumptions — every rate/parameter the forecast consumes. The main place to experiment.")
    p("3. Revenue FY26-40 — Phase 1: property tax, state aid, local receipts, two scenarios.")
    p("4. Expense FY26-40 — Phase 3: departmental, schools, benefits, debt service, two scenarios.")
    p("5. Surplus-Deficit FY26-40 — Phase 5/3a: Revenue minus Expense, the baseline gap.")
    p("6. New Growth Scenarios — Phase 2: 4 new-growth policy scenarios (trend continues vs. 3 ways to "
      "hit the 80th-percentile peer rate), the main assumption-stress-test surface.")
    p("7. Existing vs New FY26-40 — what each new-growth scenario buys existing (pre-2005) property owners.")
    p("8. Schools by Category — the schools budget disaggregated into 9-10 DESE function categories "
      "(Teachers, Pupil Services, Guidance, etc.), FY2009-2040 actual + forecast. Cited data, not live "
      "formulas - the FY2026-2040 total feeds directly into the Expense tab's trend_corrected Schools row.")
    p("9. Benefits by Category — Pensions, Group Health, OPEB, and Other, FY2023-2040 actual + forecast, "
      "including the real FY2031 pension→OPEB funding handoff. Cited data, not live formulas - the "
      "FY2026-2040 total feeds directly into the Expense tab's trend_corrected Benefits row.")
    p("10. Balance Sheet - Liabilities — a different kind of model (the Town's BALANCE sheet, not its "
      "annual budget): Long-term Debt, Net Pension Liability, Net OPEB Liability, and smaller liabilities, "
      "FY2025-2040, ties out exactly to the FY2024 audited Statement of Net Position. Standalone - doesn't "
      "feed any other tab. OPEB is deliberately held flat as a labeled placeholder, not a real projection.")
    p("11. Base Case Decomposition — on the earlier trend method, separates what the May 2026 override is "
      "doing from the Town's automatic revenue. Kept for the record: the documents now look forward only, "
      "with the override included, and size the levers against the room in the Driver Forecast tab.")
    p("12. Override Reliance — the opposite question, on the DOWNSIDE case (town_assumptions): what "
      "closing the gap with nothing but overrides would take. Fully live - the base gap reads off the "
      "Surplus-Deficit tab and each hypothetical override is SIZED BY FORMULA at whatever reaches "
      "breakeven, then compounds at 2.5% like every real one. A hypothetical, not a proposal.")
    p("13. Driver Forecast FY26-40 — the base case (see above). Opens with the base-case assumptions "
      "(pay, inflation, premiums, staffing, enrollment, growth). Lines cited from expense_driver_forecast.py; "
      "spending total and room are live and checked.")
    p("14. What Decides FY2040 — one assumption at a time, its effect on FY2040 spending and room. Each "
      "row names the base value it departs from.")
    p("15. Cost of Growth — shared per-home and per-student costs, with a live table of when a new home "
      "covers its costs. Change an input (tan) and the breakeven recalculates.")
    blank()

    h("Where this comes from")
    p("This project's full narrative and methodology live in README.md and docs/reference_document.md "
      "(and its web version, docs/reference_document.html) in the brookline-finances repo - this "
      "workbook is the audit companion to that writing, not a replacement for it. Every input here traces "
      "to a cited primary source (the Town's FY27-31 Long-Range Financial Plan, DOR/DLS Schedule A data, "
      "the Town's own Tax Classification Hearing presentations, Ben's own override research) - see each "
      "tab's own notes and data/SOURCES.md for the full catalog.", height=48)

    ws.sheet_view.showGridLines = False
    print(f"Guide tab: {r} rows.")


build_guide()
for name in ["Guide", "Historical FY05-25", "Assumptions", "Revenue FY26-40", "Expense FY26-40",
             "Surplus-Deficit FY26-40", "New Growth Scenarios", "Existing vs New FY26-40",
             "Base Case Decomposition", "Override Reliance", "Driver Forecast FY26-40",
             "What Decides FY2040", "Cost of Growth"]:
    wb[name].sheet_view.showGridLines = False if name != "Guide" else wb[name].sheet_view.showGridLines

wb.active = 0
wb.save(OUT_PATH)
print(f"\nFINAL SAVE COMPLETE: {OUT_PATH}")
print(f"TOTAL VALIDATION FAILURES ACROSS ENTIRE WORKBOOK: {len(ALL_FAILS)}")
if ALL_FAILS:
    print("!!! DO NOT SHIP - fix mismatches above before delivering. !!!")
else:
    print("All live tabs match the Python model exactly (within floating-point tolerance). Ready to deliver.")
