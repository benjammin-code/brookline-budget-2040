"""
Builds docs/forecast_dashboard.html from docs/_build/dashboard_template.html, the
engine (docs/_build/dashboard_engine.js) and output/dashboard_data.json.

Run from `scripts/`, after export_dashboard_data.py:
    python3 export_dashboard_data.py && python3 build_dashboard.py && node test_dashboard_engine.js
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
B = ROOT / "docs" / "_build"
OUT = ROOT / "docs" / "forecast_dashboard.html"


def slim(x):
    if isinstance(x, float):
        return round(x) if abs(x) >= 1e5 else round(x, 10)   # dollars to the dollar; counts and rates kept
    if isinstance(x, list):
        return [slim(v) for v in x]
    if isinstance(x, dict):
        return {k: slim(v) for k, v in x.items()}
    return x


def main():
    d = json.loads((ROOT / "output" / "dashboard_data.json").read_text())
    # the page only needs the grid and the trend (with its new-homes variants); total_revenue is a check column
    for chca, g in d["growth"].items():
        d["growth"][chca] = {k: {kk: vv for kk, vv in v.items() if kk != "total_revenue"}
                             for k, v in g.items() if k.startswith("grid_") or k.startswith("trend_")}
    slim_d = slim(d)
    (ROOT / "output" / "dashboard_data_page.json").write_text(json.dumps(slim_d))   # what the page embeds
    html = (B / "dashboard_template.html").read_text()
    # model numbers typed into the page's text come from output/site_facts.json, so a model
    # change updates them (run node site_facts.js first); an unknown fact stops the build
    facts = json.loads((ROOT / "output" / "site_facts.json").read_text())
    def _fact(m):
        if m.group(1) not in facts:
            raise SystemExit(f"dashboard_template.html: unknown fact {m.group(1)}")
        return facts[m.group(1)]
    html = re.sub(r"\{\{fact:([a-z0-9_]+)\}\}", _fact, html)
    html = html.replace("/*__ENGINE__*/", (B / "dashboard_engine.js").read_text())
    html = html.replace("/*__DATA__*/", json.dumps(slim_d, separators=(",", ":")))
    OUT.write_text(html)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e3:,.0f} KB)")


if __name__ == "__main__":
    main()
