"""
Checks the workbook's Revenue build and Assumptions sheets against the numbers the Explorer
embeds (output/dashboard_data_page.json), which come from the Python models:

  1. Every Assumptions value the Explorer also carries (consts, revenue parameters, FY2027
     adopted budget, trend rate) must equal it to within a part in a million.
  2. For each Chestnut Hill estimate and a spread of growth steps and mixes, the Revenue build's
     property tax, debt exclusion tax, other available funds, local receipts tied to growth,
     real-estate new growth, homes and commercial square feet must match the Explorer's
     precomputed grid every year: dollars within $5, homes within 0.5, square feet within 1
     (the grid stores those two rounded).

Run from the project root:
    python3 scripts/workbook_validation/validate_revenue_build.py [workbook]
Exits 1 on any failure.
"""
import json, sys
from pathlib import Path
import formulas, openpyxl

ROOT = Path(__file__).parent.parent.parent
wbf = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "Brookline_Forecast_Model.xlsx")
fname = wbf.split("/")[-1]
D = json.loads((ROOT / "output" / "dashboard_data_page.json").read_text())
wb = openpyxl.load_workbook(wbf)
xl = formulas.ExcelModel().loads(wbf).finish()


def named(n):
    return wb.defined_names[n].attr_text.split("!")[1].replace("$", "")


def sheet_of(n):
    return wb.defined_names[n].attr_text.split("!")[0].strip("'").upper()


bad = 0
# ---- 1. assumptions
sol = xl.calculate()
get = lambda n: float(sol[f"'[{fname}]{sheet_of(n)}'!{named(n)}"].value[0][0])
C, R, A = D["consts"], D["revenue"], D["adopted"]
pairs = {"K_pD": C["pD"], "K_psD": C["psD"], "K_TownFTE": C["town_fte"], "K_Staff26": C["staff26"],
         "K_SPS": C["school_personnel_share"], "K_V": C["school_variable_share"], "K_Ratio2019": C["ratio_fy2019"],
         "K_SPH": C["students_per_home"], "K_ChcaUnits": C["chca_units"], "K_ChcaSPU": C["chca_students_per_unit"],
         "K_ChcaEmp": C["chca_employees"], "K_SqftPerEmp": C["sqft_per_emp"], "K_CostPerEmp": C["cost_per_emp_fy25"],
         "K_BenLoad": C["benefit_loading"], "K_Permit": C["permitting_cost_fy27"], "K_CIP": C["cip_policy_share"], "K_NonApp": C["non_approp_fy27"], "K_NonAppG": C["non_approp_growth"],
         "K_Homes25": C["homes_fy2025"], "K_FireHomes": C["fire_company_homes"], "K_FireCost": C["fire_company_cost_fy25"],
         "K_PSShare": C["ps_share"], "K_PSPos": C["ps_position_cost_fy25"], "K_PSRestoreN": C["ps_restore_positions"],
         "K_PSSharePol": C["ps_share_police"], "K_PolBudget": C["police_budget_fy27"], "K_PolRatio": C["police_peer_per_1000"],
         "K_BasePay": D["base"]["pay"], "K_ActShare": 1 - C["retiree_cost_share"], "K_RetGrowth": C["retiree_growth"], "K_TrendRate": D["trend_rate"],
         "R_SA2026": round(R["sa_2026"]), "R_SA2027": round(R["sa_2027"]), "R_SAbase": R["sa_cagr"], "R_LRresid2025": R["lr_resid_2025"], "R_LRbase": R["lr_cagr"],
         "R_BudgetRatio": R["budget_ratio"], "R_OtherSurplus": R["other_surplus_share"], "R_ApprShare": R["appropriated_share"],
         "A_TD": A["town_departments"], "A_Sch": A["schools"], "A_GH": A["group_health"], "A_Pen": A["pensions"],
         "A_OPEB": A["opeb"], "A_OB": A["other_benefits"], "A_Debt": A["within_levy_debt"], "A_Other": A["other_nondept"],
         "A_FTEchg": A["school_fte_change"]}
for n, want in pairs.items():
    have = get(n)
    if abs(have - want) > 1e-6 * max(1.0, abs(want)):
        print(f"ASSUMPTION {n}: workbook {have!r} vs Explorer {want!r}")
        bad += 1
print(f"assumptions checked: {len(pairs)}, mismatches: {bad}")

# ---- 2. revenue build against the grid
rb = wb["Revenue build"]
rows = {rb.cell(r, 1).value: r for r in range(1, rb.max_row + 1)}
SER = [("Property tax, all", "prop_tax", 5), ("Debt exclusion tax (Town plan, then held at FY2031)", "debt_excl", 5),
       ("Local receipts tied to growth", "lr_rest", 5), ("Real-estate new growth (all but business equipment)", "re_ng", 5),
       ("Homes added this year", "units", 0.5), ("Commercial square feet added this year", "sqft", 1.0)]
ofund_row = [r for lab, r in rows.items() if lab and lab.startswith("Other available funds (")][0]
cols = "CDEFGHIJKLMNOPQ"
data = wb["Data"]
labels = {}
cur = None
for r in range(1, data.max_row + 1):
    a, c, d = data.cell(r, 1).value, data.cell(r, 3).value, data.cell(r, 4).value
    if a in ("mix", "chca"):
        cur = a
    elif a is not None:
        cur = None if a not in ("mix", "chca") else a
    if cur and c is not None and d is not None:
        labels.setdefault(cur, {})[str(d)] = c
cases = []
for chca in ("approved", "cr_avg", "rkg", "in_trend"):
    cases.append((chca, 0, "mix"))
    for k in (-6, -2):
        cases.append((chca, k, "mix"))
    for mix in ("mix", "housing", "commercial", "even"):
        for k in ((3, 13) if chca == "approved" else (7,)):
            cases.append((chca, k, mix))
worst = {}
for chca, k, mix in cases:
    s = xl.calculate(inputs={f"'[{fname}]SETTINGS'!{named('In_growth')}": k,
                             f"'[{fname}]SETTINGS'!{named('In_mix')}": labels["mix"][mix],
                             f"'[{fname}]SETTINGS'!{named('In_chca')}": labels["chca"][chca]})
    g = lambda a: float(s[f"'[{fname}]REVENUE BUILD'!{a}"].value[0][0])
    key = "trend_continues" if k == 0 else f"grid_{'mix' if k < 0 else mix}_{k:+d}"
    G = D["growth"][chca][key]
    for lab, ser, tol in SER + [("ofund", "other_funds", 5)]:
        r = ofund_row if lab == "ofund" else rows[lab]
        gap = max(abs(g(f"{c}{r}") - G[ser][i]) for i, c in enumerate(cols))
        worst[ser] = max(worst.get(ser, 0), gap)
        if gap > tol:
            print(f"GRID {chca} {key} {ser}: gap {gap:,.2f}")
            bad += 1
print(f"grid cases checked: {len(cases)}; worst gaps: " + ", ".join(f"{k} {v:,.2f}" for k, v in worst.items()))
print("FAILURES", bad)
sys.exit(1 if bad else 0)
