"""
One command for any change to the model or its inputs: reruns everything that depends on it,
in order, stops at the first failed check, and reports every published number that moved.

    python3 scripts/rebuild_all.py            (from the project root or scripts/)
    python3 scripts/rebuild_all.py --skip-workbook   (skip the slow Excel recalculation check)

What it does:
1. Snapshots output/site_facts.json and output/site_data.json (every number the site shows
   comes from these two files or from the chart data in charts.js).
2. Runs the chain: the driver forecast, the breakeven and tax-bill scripts, the Explorer
   export and build, the Explorer-vs-Python parity test, the embedded chart data, the site
   facts, the Excel workbook and its formula check, then the pages, documents and site.
3. Checks the built site: unknown facts ("??") and broken links or anchors; then accessibility
   and phone width on the rendered pages (check_site_quality.py, about 15 seconds): every chart
   has a text alternative, images have alt text, controls and links have names, charts offer a
   data table, and nothing pushes a 390px phone screen sideways.
4. Writes output/rebuild_report.md: every fact whose value changed (old -> new) with the pages
   that show it, the site_data series that changed, and STALE COPIES, i.e. places where a
   changed fact's old value still appears as typed text instead of a {{fact:}} marker. Those
   are the edits a person has to make by hand.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = ROOT / "scripts"
OUT = ROOT / "output"
DIST = ROOT / "website" / "dist"
# Where text is typed by hand and could hold a stale copy of a number.
TEXT_SOURCES = [*sorted((ROOT / "docs" / "site" / "pages").glob("*.md")), ROOT / "docs" / "new_growth.md",
                ROOT / "docs" / "article.md", *sorted((ROOT / "website" / "src" / "pages").glob("*.html")),
                ROOT / "docs" / "_build" / "chart_blocks.json", ROOT / "docs" / "_build" / "dashboard_template.html"]

STEPS = [
    ("new homes: pace, mix and value from permits", ["python3", "new_homes_parameters.py"]),
    ("new growth scenarios", ["python3", "new_growth_scenario_forecast.py"]),
    # inputs the driver forecast reads: cash capital shares and the override's value (were last made 2026-09-30)
    ("revenue forecast inputs", ["python3", "baseline_revenue_forecast.py"]),
    ("capital and other non-departmental inputs", ["python3", "baseline_expense_forecast.py"]),
    ("surplus inputs", ["python3", "baseline_surplus_deficit_forecast.py"]),
    ("override value", ["python3", "base_case_decomposition.py"]),
    ("stress case: overrides only", ["python3", "override_reliance_scenario.py"]),
    ("driver forecast", ["python3", "expense_driver_forecast.py"]),
    ("value of faster growth", ["python3", "driver_forecast_breakeven.py"]),
    ("what permits say about the next two years", ["python3", "permit_leading_indicator.py"]),
    ("when a home covers its costs", ["python3", "housing_unit_breakeven.py"]),
    ("tax bill paths", ["python3", "tax_bill_paths.py"]),
    ("Explorer data", ["python3", "export_dashboard_data.py"]),
    ("chart data in charts.js", ["python3", "sync_chart_data.py"]),
    ("enrollment workbook (and its chart data)", ["python3", "build_enrollment_workbook.py"]),
    ("towns compared (births, families, housing)", ["python3", "families_by_town.py"]),
    ("what new homes do, year by year", ["python3", "growth_links.py"]),
    ("spending growth by cause, FY2011-25", ["python3", "expense_drivers_tree.py"]),
    ("site facts", ["node", "site_facts.js"]),
    ("Explorer page", ["python3", "build_dashboard.py"]),
    ("CHECK Explorer matches the Python model", ["node", "test_dashboard_engine.js"]),
    ("Excel workbook", ["python3", "build_explorer_workbook.py"]),
    ("CHECK workbook matches the Explorer", ["python3", "workbook_validation/validate_workbook.py"]),
    ("CHECK workbook revenue build and assumptions", ["python3", "workbook_validation/validate_revenue_build.py"]),
    ("short reads and topic pages", ["python3", "build_pages.py"]),
    ("documents (new homes, article)", ["python3", "build_reference_doc.py"]),
    ("website", ["python3", str(ROOT / "website" / "scripts" / "build_site.py")]),
    ("home page forecast picture", ["python3", str(ROOT / "website" / "scripts" / "home_chart.py")]),
    ("forecast page takeaway pictures", ["python3", str(ROOT / "website" / "scripts" / "takeaway_charts.py")]),
]

# Steps that read the Town's building permit records. Town staff supplied those records, so the
# public GitHub copy leaves them out; there these steps are skipped and their published outputs
# (in output/) are used as they are.
NEEDS = {
    "new homes: pace, mix and value from permits": ["output/permit_homes_coded.csv"],
    "what permits say about the next two years": ["data/permits_cache/foia_joined.csv"],
    "what new homes do, year by year": ["data/permits_cache/foia_joined.csv", "data/permits_cache/geotms.csv"],
}


def run(steps):
    for name, cmd in steps:
        if not all((ROOT / f).exists() for f in NEEDS.get(name, [])):
            print(f"  skip  {name:42s}        needs the permit records (not public); using its saved outputs")
            continue
        t = time.time()
        r = subprocess.run(cmd, cwd=S, capture_output=True, text=True)
        tail = (r.stdout.strip().splitlines() or [""])[-1][:110]
        print(f"  {'ok ' if r.returncode == 0 else 'FAIL'}  {name:42s} {time.time() - t:5.1f}s  {tail}")
        if r.returncode != 0:
            print(r.stdout[-3000:], r.stderr[-3000:])
            raise SystemExit(f"stopped: {name} failed")


def site_checks():
    red = {x["source"]: x["destination"] for x in json.loads((DIST / "vercel.json").read_text())["redirects"]}
    bad = []
    pages = list((DIST / "forecast").rglob("*.html")) + [DIST / "forecast.html"]
    for f in pages:
        t = f.read_text()
        if "??" in re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S):
            bad.append(f"{f.relative_to(DIST)}: unresolved fact (??)")
        for path, anchor in set(re.findall(r'href="(/[^"#?]*)(#[^"]*)?"', t)):
            if path == "/" or path.startswith(("/site.css", "/favicon", "/img", "/maps", "/post", "/pagefind")) \
                    or path.endswith(".xlsx"):
                continue
            if path in red:
                path, _, a2 = red[path].partition("#")
                anchor = anchor or (("#" + a2) if a2 else "")
            tgt = DIST / (path.lstrip("/") + ".html")
            if not tgt.exists() or (anchor and f'id="{anchor[1:]}"' not in tgt.read_text()):
                bad.append(f"{f.relative_to(DIST)}: broken link {path}{anchor or ''}")
    return bad


def number_forms(v):
    """Ways a fact's value might have been typed: '$30.8 million' -> also '$30.8M', '30.8'."""
    forms = {v}
    m = re.match(r"^([−+-]?)\$([\d.,]+)( million|M)?$", v)
    if m:
        n = m.group(2)
        forms |= {f"${n} million", f"${n}M", f"{n} million"}
    return {f for f in forms if len(re.sub(r"\D", "", f)) >= 2}


def report(before_f, after_f, before_d, after_d):
    changed = {k: (before_f.get(k), after_f[k]) for k in after_f if before_f.get(k) != after_f[k]}
    texts = {p: p.read_text() for p in TEXT_SOURCES if p.exists()}
    lines = [f"# Rebuild report, {time.strftime('%Y-%m-%d %H:%M')}", "",
             f"{len(changed)} of {len(after_f)} site facts changed.", ""]
    stale = []
    if changed:
        lines += ["| Fact | Before | After | Shown on |", "|---|---|---|---|"]
        for k, (a, b) in sorted(changed.items()):
            where = [p.name for p, t in texts.items() if "{{fact:" + k + "}}" in t]
            lines.append(f"| {k} | {a} | {b} | {', '.join(where) or 'site data only'} |")
            if a:
                for p, t in texts.items():
                    clean = re.sub(r"\{\{fact:[a-z0-9_]+\}\}", "", t)
                    for form in number_forms(a):
                        for m in re.finditer(re.escape(form) + r"(?![\d.])", clean):
                            ln = clean[:m.start()].count("\n") + 1
                            stale.append(f"- {p.relative_to(ROOT)}:{ln}: '{form}' (fact {k}, now {b})")
    series = sorted(k for k in after_d if before_d.get(k) != after_d[k])
    lines += ["", "Site data series changed: " + (", ".join(series) or "none"), "",
              "## Possible stale copies (typed numbers matching a changed fact's old value)", ""]
    lines += sorted(set(stale)) or ["None found."]
    lines += ["", "Typed numbers that are not facts (for example in docs/new_growth.md) are not covered "
              "by this check; read pages whose subject the change touches."]
    (OUT / "rebuild_report.md").write_text("\n".join(lines) + "\n")
    print(f"\n{len(changed)} facts changed, {len(series)} data series changed, "
          f"{len(set(stale))} possible stale copies. Report: output/rebuild_report.md")


def main():
    skip_wb = "--skip-workbook" in sys.argv
    before_f = json.loads((OUT / "site_facts.json").read_text())
    before_d = json.loads((OUT / "site_data.json").read_text())
    slow = {"Excel workbook", "CHECK workbook matches the Explorer", "CHECK workbook revenue build and assumptions"}
    steps = [s for s in STEPS if not (skip_wb and s[0] in slow)]
    print("Rebuilding:")
    run(steps)
    bad = site_checks()
    print(f"  {'ok ' if not bad else 'FAIL'}  CHECK site links and facts" + (f": {len(bad)} problems" if bad else ""))
    for b in bad[:30]:
        print("       ", b)
    # accessibility and phone width, on the rendered pages (scripts/check_site_quality.py)
    t = time.time()
    q = subprocess.run(["python3", "check_site_quality.py"], cwd=S, capture_output=True, text=True)
    qlines = q.stdout.strip().splitlines()
    print(f"  {'ok ' if q.returncode == 0 else 'FAIL'}  {'CHECK accessibility and phone width':42s} "
          f"{time.time() - t:5.1f}s  {(qlines or [''])[-1][:110]}")
    if q.returncode != 0:
        for ln in qlines[:-1]:
            if "FAIL" in ln:
                print("       ", ln.strip())
    report(before_f, json.loads((OUT / "site_facts.json").read_text()),
           before_d, json.loads((OUT / "site_data.json").read_text()))
    if bad or q.returncode != 0:
        raise SystemExit(1)
    if (ROOT / "public-repo").exists():   # the working project, not the public copy itself
        print("After a production deploy, refresh the public GitHub copy: python3 scripts/export_public_repo.py "
              "(website/README.md, 'Every production deploy').")


if __name__ == "__main__":
    main()
