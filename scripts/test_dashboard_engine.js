// Checks docs/_build/dashboard_engine.js against the Python driver forecast.
// Run from scripts/:  node test_dashboard_engine.js   (after export_dashboard_data.py)
const fs = require("fs");
const { runModel } = require("../docs/_build/dashboard_engine.js");
// the full export, then the rounded copy the page embeds (build_dashboard.py)
const FILES = ["../output/dashboard_data.json", "../output/dashboard_data_page.json"].filter(f => fs.existsSync(f));
const T = JSON.parse(fs.readFileSync("../output/dashboard_tests.json"));
const LINES = ["departmental_base", "departmental_growth", "schools", "group_health", "growth_staff_benefits",
  "pensions", "opeb", "other_benefits", "debt_within_levy", "other_nondept"];
let fails = 0, worst = 0, n = 0;
for (const f of FILES) {
const D = JSON.parse(fs.readFileSync(f));
for (const c of T.tests) {
  // the page carries only the grid and trend scenarios; named peer scenarios are tested on the full export
  if (!D.growth[c.a.chca || "approved"][c.a.growth]) continue;
  n++;
  const r = runModel(D, c.a, c.rev);
  const got = { operating_expenditure: r.spending, operating_revenue: r.revenue, surplus_deficit: r.room };
  LINES.forEach(k => got[k] = r.lines[k]);
  const bad = [];
  for (const k of Object.keys(got)) {
    c.expect[k].forEach((e, j) => {
      const d = Math.abs(got[k][j] - e);
      worst = Math.max(worst, d);
      if (d > 5) bad.push(`${k} FY${T.years[j]} js ${got[k][j].toFixed(0)} py ${e.toFixed(0)}`);
    });
  }
  if (bad.length) { fails++; console.log("FAIL", f, c.label, "\n   ", bad.slice(0, 4).join("\n    ")); }
}
}
console.log(`${n - fails}/${n} cases (${FILES.length} data files) match within $5 (the revenue CSV rounds each component to the dollar); largest gap $${worst.toFixed(4)}`);
process.exit(fails ? 1 : 0);
