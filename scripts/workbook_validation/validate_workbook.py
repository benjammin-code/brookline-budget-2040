"""
Recalculates Brookline_Forecast_Model.xlsx with the `formulas` engine for every scenario in
scen.json and compares each year's revenue, spending and room with the Explorer engine
(run_engine.js). Exits 1 if any gap exceeds $5. Run from the project root:
    python3 scripts/workbook_validation/validate_workbook.py [workbook]
"""
import formulas, json, openpyxl, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
ROOT = HERE.parent.parent
wbf = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "Brookline_Forecast_Model.xlsx")
E = json.loads(subprocess.run(["node", str(HERE / "run_engine.js"), str(ROOT), str(HERE / "scen.json")],
                              check=True, capture_output=True, text=True).stdout)
S = json.load(open(HERE / "scen.json"))
wb = openpyxl.load_workbook(wbf); fc = wb["Forecast"]; data = wb["Data"]
rows = {fc.cell(r, 1).value: r for r in range(1, fc.max_row + 1)}
cell = {}
for n, dn in wb.defined_names.items():
    if n.startswith("In_"):
        cell[n[3:]] = dn.attr_text.split("!")[1].replace("$", "")
# option label for each code, from the Data sheet's choices table
opt = {}; cur = None
for r in range(1, data.max_row + 1):
    a, c, d = data.cell(r, 1).value, data.cell(r, 3).value, data.cell(r, 4).value
    if a in ("opeb","staffing","homes","mix","fill","enroll","capital","chca","slip","ps_staff"): cur = a
    if cur and c is not None and d is not None and c != "Choice":
        opt.setdefault(cur, {})[str(d)] = c
    if a == "New-growth revenue grid": cur = None
selects = set(opt)
fname = wbf.split("/")[-1]
xl = formulas.ExcelModel().loads(wbf).finish()
cols = "DEFGHIJKLMNOPQ"
res = {}
for nm, ch in S.items():
    inputs = {}
    for k, v in ch.items():
        val = opt[k][str(v)] if k in selects else (int(v) if k == "ov_year" else v)
        inputs[f"'[{fname}]SETTINGS'!{cell[k]}"] = val
    sol = xl.calculate(inputs=inputs)
    g = lambda a: sol[f"'[{fname}]FORECAST'!{a}"].value[0][0]
    e = E[nm]; gaps = {}
    for lab, k in [("Total revenue", "revenue"), ("Total spending", "spending"), ("Room: revenue minus spending", "room")]:
        r = rows[lab]
        gaps[k] = max(abs(float(g(f"{c}{r}")) - e[k][i]) for i, c in enumerate(cols))
    res[nm] = (gaps, e["room"][-1], float(g(f"Q{rows['Room: revenue minus spending']}")))
    print(f"{nm:46s} room {gaps['room']:8.2f}  revenue {gaps['revenue']:8.2f}  spending {gaps['spending']:8.2f}   FY2040 room engine {e['room'][-1]/1e6:7.2f}M  workbook {res[nm][2]/1e6:7.2f}M", flush=True)
worst = max(max(v[0].values()) for v in res.values())
print("WORST GAP", round(worst, 4))
sys.exit(0 if worst <= 5 else 1)
