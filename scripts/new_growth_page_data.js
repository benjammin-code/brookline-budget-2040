// Figures for the new-growth page (docs/new_growth.md): the base case's room
// (revenue minus annual General Fund spending) at other new-growth rates and mixes,
// and what the added growth brings in and costs by FY2040.
//
// Uses the dashboard engine (docs/_build/dashboard_engine.js), which
// test_dashboard_engine.js checks against the Python driver forecast within $5,
// and the same precomputed grid of full revenue-model runs the Forecast Explorer uses.
//
// Run from scripts/ after export_dashboard_data.py:  node new_growth_page_data.js
// Writes output/new_growth_room_by_rate.csv and output/new_growth_mix_fy2040.csv,
// and prints the arrays to paste into docs/_build/charts.js (growthPathsData, growthMixData).
const fs = require("fs");
const { runModel } = require("../docs/_build/dashboard_engine.js");
const D = JSON.parse(fs.readFileSync("../output/dashboard_data.json"));
const T = JSON.parse(fs.readFileSync("../output/dashboard_tests.json"));
const BASE = T.tests[0].a;   // the base case, as exported by export_dashboard_data.py
const TREND = D.trend_rate;  // 1.235%, FY2022-26
const PK = Math.round((D.peer_rate - TREND) * 1000);   // tenths of a point up to the 80th percentile

const name = (mix, k) => k === 0 ? "trend_continues" : `grid_${k < 0 ? "mix" : mix}_${k > 0 ? "+" : ""}${k}`;
const run = (mix, k) => runModel(D, { ...BASE, growth: name(mix, k) }, {});
const r0 = run("mix", 0);
const years = r0.years;
const M = v => +(v / 1e6).toFixed(2);

// 1. Room each year, today's mix, at several rates
const STEPS = [-3, 0, 3, PK];
let csv = "growth_rate_pct,step_points,mix," + years.map(y => "room_fy" + y).join(",") + ",first_year_negative\n";
const paths = [];
for (const mix of ["mix", "housing", "commercial", "even"]) for (const k of [...new Set([-6, -3, -2, -1, 0, 1, 2, 3, 5, 7, PK, 10, 13])].sort((a, b) => a - b)) {
  if (k <= 0 && mix !== "mix") continue;
  const r = run(mix, k);
  const neg = years.find((y, j) => r.room[j] < 0) || "";
  csv += [((TREND + k / 1000) * 100).toFixed(3), (k / 10).toFixed(1), k <= 0 ? "scaled_down" : mix,
          ...r.room.map(M), neg].join(",") + "\n";
  if (mix === "mix" && STEPS.includes(k)) paths.push({ k, rate: +((TREND + k / 1000) * 100).toFixed(2), room: r.room.map(v => +(v / 1e6).toFixed(1)), neg });
}
fs.writeFileSync("../output/new_growth_room_by_rate.csv", csv);

// 2. FY2040: what the added growth brings in and costs, by mix, at +0.3 points and at the 80th percentile
const j = years.indexOf(2040);
const COST = ["departmental_growth", "schools", "group_health", "growth_staff_benefits", "other_benefits", "departmental_base", "pensions", "opeb", "debt_within_levy", "other_nondept"];
let csv2 = "step_points,growth_rate_pct,mix,added_revenue_m,added_spending_m,of_which_schools_m,of_which_town_services_m,of_which_health_and_benefits_m,net_m,added_homes,added_students\n";
const mixRows = [];
// At the 80th percentile the three led mixes use the exact peer-rate scenarios, the same runs as the
// site's text and the decisions chart (2026-10-15; the grid's 0.8 point rounds the rate up slightly,
// which showed $46.3M against the text's $46.1M). Today's mix has no exact-rate run, so it stays on the grid.
const PEER = { commercial: "peer_target_commercial_led", even: "peer_target_balanced_mix", housing: "peer_target_residential_led" };
for (const k of [3, PK]) for (const mix of ["mix", "commercial", "even", "housing"]) {
  const r = k === PK && PEER[mix] ? runModel(D, { ...BASE, growth: PEER[mix] }, {}) : run(mix, k);
  const d = key => r.lines[key][j] - r0.lines[key][j];
  const rev = r.revenue[j] - r0.revenue[j], sp = r.spending[j] - r0.spending[j];
  const row = { k, mix, rev: M(rev), cost: M(sp), schools: M(d("schools")), town: M(d("departmental_growth")),
    benefits: M(d("group_health") + d("growth_staff_benefits") + d("other_benefits")), net: M(rev - sp),
    homes: Math.round(r.units[j] - r0.units[j]), students: Math.round(r.enrollment[j] - r0.enrollment[j]) };
  csv2 += [ (k / 10).toFixed(1), ((TREND + k / 1000) * 100).toFixed(3), mix, row.rev, row.cost, row.schools, row.town, row.benefits, row.net, row.homes, row.students].join(",") + "\n";
  if (k === PK) mixRows.push(row);
}
fs.writeFileSync("../output/new_growth_mix_fy2040.csv", csv2);

console.log("base room FY2031", M(r0.room[years.indexOf(2031)]), "FY2040", M(r0.room[j]));
console.log("var growthPathsYears = " + JSON.stringify(years) + ";");
console.log("var growthPathsData = " + JSON.stringify(paths) + ";");
console.log("var growthMixData = " + JSON.stringify(mixRows.map(r => ({ mix: r.mix, rev: +r.rev.toFixed(1), cost: +r.cost.toFixed(1), net: +r.net.toFixed(1), homes: r.homes, students: r.students }))) + ";");
console.log(csv); console.log(csv2);

// 3. Housing and school seats (added 2026-10-06): enrollment against the FY2027 level,
// the homes that fit under it each year, and what more housing adds to FY2040 with
// students staffed at today's ratio vs filling seats the decline leaves open.
{
  const hist = fs.readFileSync("../output/school_enrollment_staffing_fy05_25.csv", "utf8").trim().split("\n").slice(1)
    .map(l => l.split(",")).filter(c => +c[0] >= 2010).map(c => [+c[0], +c[1]]);
  hist.push([2026, 6949]);   // October 2025 count (expense_driver_forecast.ACTUAL_OCT_2025)
  const e0 = r0.enrollment[0];
  const proj = years.map((y, i) => [y, Math.round(r0.enrollment[i])]);
  const room = years.map((y, i) => [y, Math.round((e0 - r0.enrollment[i]) / D.consts.students_per_home)]);
  const fill = [3, 7, 13].map(k => {
    const a = run("housing", k), b = runModel(D, { ...BASE, growth: name("housing", k), fill_capacity: true }, {});
    return { homes: Math.round(a.units[j] - r0.units[j]), staffed: +((a.room[j] - r0.room[j]) / 1e6).toFixed(1),
             fill: +((b.room[j] - r0.room[j]) / 1e6).toFixed(1), enroll: Math.round(b.enrollment[j]) };
  });
  let csv3 = "fiscal_year,enrollment,kind,homes_beyond_trend_that_fit_under_fy2027_level\n";
  hist.forEach(([y, e]) => { csv3 += `${y},${e},actual,\n`; });
  proj.forEach(([y, e], i) => { if (y > 2026) csv3 += `${y},${e},nesdec_base_case,${room[i][1]}\n`; });
  fs.writeFileSync("../output/new_growth_enrollment_capacity.csv", csv3);
  let csv4 = "added_homes_by_fy2040,fy2040_gain_students_staffed_m,fy2040_gain_students_fill_seats_m,fy2040_enrollment_fill\n";
  fill.forEach(f => { csv4 += `${f.homes},${f.staffed},${f.fill},${f.enroll}\n`; });
  fs.writeFileSync("../output/new_growth_housing_fill_fy2040.csv", csv4);
  console.log("var seatsHist = " + JSON.stringify(hist) + ";");
  console.log("var seatsProj = " + JSON.stringify(proj) + ";");
  // the School Department's forecast (Cropper-McKibben 2023), scaled to the Sept 2026 count
  // as the model's enroll_mode "cm" does; it ends in FY2034
  const cm = years.filter(y => y <= 2034).map(y => [y, Math.round(D.enrollment.cm[y])]);
  console.log("var seatsCM = " + JSON.stringify(cm) + ";");
  // base-case new homes from FY2028 (recent pace plus the approved Chestnut Hill plan)
  console.log("var seatsBase = " + JSON.stringify(years.map((y, i) => [y, Math.round(r0.units[i])])) + ";");
  console.log("var seatsLevel = " + Math.round(e0) + ";");
  console.log("var seatsRoom = " + JSON.stringify(room) + ";");
  console.log("var seatsSPH = " + D.consts.students_per_home + ";");
  console.log("var housingFillData = " + JSON.stringify(fill) + ";");
}
