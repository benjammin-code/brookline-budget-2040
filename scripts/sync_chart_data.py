"""
Regenerates the model-dependent chart data embedded in docs/_build/charts.js.

Several charts carry their data as `var name = [...];` lines in charts.js. They used to be
pasted in by hand from script output, so a model change left them stale. This replaces each
one from its source:

    growthPathsYears, growthPathsData, growthMixData, seatsHist, seatsProj, seatsCM,
    seatsBase, seatsLevel, seatsRoom, seatsSPH, housingFillData   <- node new_growth_page_data.js
    unitBeData                                          <- output/housing_unit_breakeven_curve.csv
    decisionsData, decisionsRoom                        <- output/expense_driver_forecast_sensitivity_fy40.csv

Prints which arrays changed. Run from scripts/ after export_dashboard_data.py and
housing_unit_breakeven.py:  python3 sync_chart_data.py
"""
import csv
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
CHARTS = HERE.parent / "docs" / "_build" / "charts.js"
CURVE = HERE.parent / "output" / "housing_unit_breakeven_curve.csv"


def generated():
    out = subprocess.run(["node", "new_growth_page_data.js"], cwd=HERE, check=True,
                         capture_output=True, text=True).stdout
    lines = {}
    for line in out.splitlines():
        m = re.match(r"var (\w+) = (.*);$", line)
        if m:
            lines[m.group(1)] = m.group(2)
    with open(CURVE) as fh:
        rows = list(csv.DictReader(fh))
    lines["unitBeData"] = json.dumps([[int(float(r["assessed_value"])), float(r["breakeven_children_fy2027"]),
                                       float(r["breakeven_children_fy2040"])] for r in rows], separators=(",", ":"))
    # the reference document's decisions chart (2026-10-14; was typed in by hand and went stale)
    sens = {r["dial"]: float(r["balance_change"]) / 1e6
            for r in csv.DictReader(open(HERE.parent / "output" / "expense_driver_forecast_sensitivity_fy40.csv"))}
    pick = lambda prefix: next(v for k, v in sens.items() if k.startswith(prefix))
    rows = [("Pay 1 point higher, all staff", "Pay growth +1 point", "decide"),
            ("School pay at schools' forecast", "School pay at PSB's forecast", "decide"),
            ("Health premiums 10% a year", "Health premiums 10%", "outside"),
            ("Enrollment rebounds, staff follow", "Cropper-McKibben enrollment, staff follow", "outside"),
            ("School staff held at FY2027 level", "School staff held at the FY2027 level", "decide"),
            ("Pension savings kept, not OPEB", "Pension savings not moved to OPEB", "decide"),
            ("Retiree health payoff money spent", "Money freed by the retiree health payoff", "decide"),
            ("Chestnut Hill inside trend", "CHCA already inside trend", "growth"),
            ("Capital at the Town's table, about 6%", "Capital held at the Town's capital table", "decide"),
            ("Faster growth, housing-led", "New growth at the peer rate, housing-led (", "growth"),
            ("School staff follow enrollment", "School staff follow enrollment down", "decide"),
            ("Health premiums 6.5% a year", "Health premiums 6.5%", "outside"),
            ("Pay half a point lower", "Pay growth -0.5 point", "decide"),
            ("School & safety pay at target", "School and Public Safety pay held", "decide"),
            ("Faster growth, housing + commercial", "New growth at the peer rate, even mix", "growth"),
            ("Faster growth, commercial-led", "New growth at the peer rate, commercial-led", "growth")]
    data = sorted(({"label": lab, "v": round(pick(pre), 1), "kind": k} for lab, pre, k in rows), key=lambda d: d["v"])
    lines["decisionsData"] = json.dumps(data, separators=(",", ":"))
    lines["decisionsRoom"] = json.dumps(round(
        float(next(r for r in csv.DictReader(open(HERE.parent / "output" / "expense_driver_forecast_fy26_40.csv"))
                   if r["fiscal_year"] == "2040")["surplus_deficit"]) / 1e6, 1))
    return lines


def main():
    js = CHARTS.read_text()
    changed, missing = [], []
    for name, value in generated().items():
        pat = re.compile(r"^(  var " + name + r" = ).*;$", re.M)
        m = pat.search(js)
        if not m:
            missing.append(name)
            continue
        old = m.group(0)
        new = m.group(1) + value + ";"
        if json.loads(old[len(m.group(1)):-1]) != json.loads(value):
            changed.append(name)
        js = js[:m.start()] + new + js[m.end():]
    CHARTS.write_text(js)
    print("chart data changed:", ", ".join(changed) or "none")
    if missing:
        raise SystemExit("not found in charts.js: " + ", ".join(missing))


if __name__ == "__main__":
    main()
