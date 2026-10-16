// Every model-derived number the site's pages quote, in one file (output/site_facts.json).
// Pages write {{fact:key}} and build_pages.py fills it in, so a number has one home and a
// model change reaches every page on the next build. Historical figures that come straight
// from a source document are written into the prose with their source instead.
//
// Run from scripts/, after export_dashboard_data.py:  node site_facts.js
// Uses the dashboard engine (checked against the Python model within $5) for anything that
// needs a model run, and the Python model's own output files for the rest.
const fs = require("fs");
const { runModel } = require("../docs/_build/dashboard_engine.js");
const D = JSON.parse(fs.readFileSync("../output/dashboard_data.json"));
const T = JSON.parse(fs.readFileSync("../output/dashboard_tests.json"));
const BASE = T.tests[0].a;

const facts = {};
const put = (k, v) => { if (k in facts) throw new Error("duplicate fact " + k); facts[k] = v; };
const m1 = v => (v / 1e6).toFixed(1);
const money = v => "$" + m1(Math.abs(v)) + " million";            // $11.5 million
const moneyS = v => "$" + m1(Math.abs(v)) + "M";                 // $11.5M
const signed = v => (v >= 0 ? "+" : "−") + moneyS(v);           // +$11.5M / −$5.1M
const pct = (v, d = 1) => (v * 100).toFixed(d) + "%";

function csv(path) {
  const [head, ...rows] = fs.readFileSync(path, "utf8").replace(/\r/g, "").trim().split("\n");
  const cols = head.split(",");
  return rows.map(line => {
    const cells = line.match(/("([^"]|"")*"|[^,]*)(,|$)/g).map(c => c.replace(/,$/, "").replace(/^"|"$/g, "").replace(/""/g, '"'));
    const o = {}; cols.forEach((c, i) => o[c] = cells[i]); return o;
  });
}

// ---- base case, year by year (Python driver forecast)
const df = csv("../output/expense_driver_forecast_fy26_40.csv");
const byYear = {}; df.forEach(r => byYear[+r.fiscal_year] = r);
for (const y of Object.keys(byYear)) {
  const r = byYear[y];
  put(`room_fy${y}`, money(+r.surplus_deficit));
  put(`room_fy${y}_short`, signed(+r.surplus_deficit));
  put(`revenue_fy${y}`, money(+r.operating_revenue));
  put(`spending_fy${y}`, money(+r.operating_expenditure));
}
// without the May 2026 override's revenue (the outlook picture's second line)
put("room_fy2040_no_override", money(+byYear[2040].surplus_deficit_ex_override));
const r31_38 = [2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038].map(y => +byYear[y].surplus_deficit / 1e6);
put("room_2030s_low", "$" + Math.round(Math.min(...r31_38)) + " million");
put("room_2030s_high", "$" + Math.round(Math.max(...r31_38)) + " million");
put("room_2030s_low_m", "$" + Math.round(Math.min(...r31_38)));
put("room_2030s_high_m", "$" + Math.round(Math.max(...r31_38)) + "M");
const cagr = (a, b, n) => Math.pow(b / a, 1 / n) - 1;
put("spending_growth_fy27_40", pct(cagr(+byYear[2027].operating_expenditure, +byYear[2040].operating_expenditure, 13), 2));
put("revenue_growth_fy27_40", pct(cagr(+byYear[2027].operating_revenue, +byYear[2040].operating_revenue, 13), 2));

// ---- police and fire (Python driver forecast; cost_assumptions.py)
{ const fy = Object.keys(byYear).map(Number).find(y => +byYear[y].fire_company > 0);
  put("fire_company_fy", fy ? "FY" + fy : "after FY2040");
  put("fire_company_homes", "31,200");
  put("fire_company_cost_fy25", "$3.0 million");
  put("homes_fy2040", (Math.round(+byYear[2040].homes_total / 100) * 100).toLocaleString("en-US"));
  if (Math.abs(+byYear[2040].homes_total) < 1) throw new Error("homes_total missing from the forecast");
  // the public safety part of the per-home charge, split police/fire on RKG's FY2025 figures
  const perHome = D.base.cost_per_home * D.consts.ps_share;
  put("ps_share_per_home", "$" + Math.round(perHome / 10) * 10);
  put("ps_share_police_per_home", "$" + Math.round(perHome * D.consts.ps_share_police / 5) * 5);
  put("ps_share_fire_per_home", "$" + Math.round(perHome * (1 - D.consts.ps_share_police) / 5) * 5);
  const pol = csv("../output/public_safety_projection_fy27_40.csv").find(r => r.scenario === "police_grow_with_homes" && +r.fiscal_year === 2040);
  // beyond the budget and the four positions being refilled
  put("police_added_fy2040", String(+pol.police_sworn - D.consts.police_budget_fy27 - D.consts.police_refill["2029"]));
  put("police_peer_per_1000", D.consts.police_peer_per_1000.toFixed(2)); }
const fte = csv("../output/expense_drivers_fte_panel_fy04_27.csv");
const fteBy = {}; fte.forEach(r => fteBy[+r.fiscal_year] = r);
const schStaff = {}; csv("../output/school_enrollment_staffing_fy05_25.csv").filter(r => r.total_staff_fte).forEach(r => schStaff[+r.fiscal_year] = +r.total_staff_fte);
// Town departments: Financial Plan budgeted FTE to FY2027, then held at FY2027 plus the fire
// company; schools: DESE staff FTE to FY2025, then the forecast's school staff
const DEPTS = ["general_government", "public_safety", "public_works", "human_services", "culture_recreation"];
const employees = [];
for (let y = 2008; y <= 2040; y++) {
  const t = fteBy[Math.min(y, 2027)];
  const row = DEPTS.map(d => +t[d]);
  if (y > 2027) row[1] += +byYear[y].ps_added_positions;
  const s = y <= 2025 ? schStaff[y] : +byYear[y].school_staff;
  employees.push([y, ...row.map(v => +v.toFixed(1)), +s.toFixed(1), y > 2027 ? 1 : 0]);
}

// ---- what each assumption is worth (Python sensitivity file)
const SENS = [
  ["pay_up1", /^Pay growth \+1 point/],
  ["pay_down_half", /^Pay growth -0.5 point/],
  ["staff_follow", /^School staff follow enrollment down, ratio held/],
  ["staff_partial", /^School staff follow enrollment and ratio moves a third/],
  ["staff_keep", /^School staff held at the FY2027 level/],
  ["fill_seats", /^Students from new homes fill existing seats/],
  ["peer_housing_fill", /^New growth at the peer rate, housing-led, students fill/],
  ["enroll_flat", /^Enrollment flat at FY2027/],
  ["enroll_cm", /^Enrollment per Cropper-McKibben/],
  ["enroll_cm_staff", /^Cropper-McKibben enrollment, staff follow it/],
  ["school_pay_psb", /^School pay at PSB's forecast/],
  ["pay_to_target", /^School and Public Safety pay held to the 3.0%/],
  ["premiums_low", /^Health premiums 6.5%/],
  ["premiums_high", /^Health premiums 10%/],
  ["premiums_actuary", /^Health premiums 4.5%/],
  ["school_np_extra", /^School non-personnel costs at inflation \+2/],
  ["inflation_high", /^Inflation 3.5%/],
  ["cost_home_rkg", /^Town cost per new home \$1,109/],
  ["cost_home_low", /^Town cost per new home \$230/],
  ["peer_housing", /^New growth at the peer rate, housing-led \(base/],
  ["peer_commercial", /^New growth at the peer rate, commercial-led/],
  ["peer_even", /^New growth at the peer rate, even mix/],
  ["homes_half", /^Half the expected new homes built/],
  ["homes_none", /^No new homes built/],
  ["pension_slip", /^Pension full funding slips/],
  ["chca_cityrealty", /^CHCA at City Realty/],
  ["chca_rkg", /^CHCA at RKG/],
  ["chca_in_trend", /^CHCA already inside trend/],
  ["pension_kept", /^Pension savings not moved to OPEB/],
  ["opeb_spend", /^Money freed by the retiree health payoff/],
  ["capital_table", /^Capital held at the Town's capital table/],
  ["ps_restore", /^Police and fire restored to earlier staffing/],
  ["no_fire_company", /^No added fire company/],
  ["police_step", /^Police grow with homes at the peer ratio/],
];
const sens = csv("../output/expense_driver_forecast_sensitivity_fy40.csv");
for (const [key, re] of SENS) {
  const row = sens.find(r => re.test(r.dial));
  if (!row) throw new Error("sensitivity row not found for " + key);
  put(`fy40_${key}`, signed(+row.balance_change));
  put(`fy40_${key}_abs`, money(+row.balance_change));
  put(`total_${key}`, signed(+row.cumulative_balance_change_fy26_40));
  put(`total_${key}_abs`, "$" + Math.round(Math.abs(+row.cumulative_balance_change_fy26_40) / 1e6) + " million");
}
if (sens.length !== SENS.length) throw new Error(`sensitivity file has ${sens.length} rows, mapped ${SENS.length}`);

// ---- when the room runs out (first year spending passes revenue), engine runs
// the year the room runs out for good: negative that year and every year after to FY2040
// (2026-10-14: FY2028 has so little room that most settings dip just below zero there and
// recover, so the first negative year alone would say FY2028 for nearly all of them)
function firstNegative(a) {
  const r = runModel(D, a, {});
  let y = null;
  for (let j = r.years.length - 1; j >= 0 && r.years[j] >= 2028 && r.room[j] < 0; j--) y = r.years[j];
  return y ? "FY" + y : "not before FY2040";
}
// the first year short at all, for the pages that name a near-term dip
function firstShort(a) {
  const r = runModel(D, a, {});
  const y = r.years.find((yy, j) => yy >= 2028 && r.room[j] < 0);
  return y ? "FY" + y : "not before FY2040";
}
const byLabel = re => { const t = T.tests.find(t => re.test(t.label)); if (!t) throw new Error("no test " + re); return t.a; };
put("runs_out_base", firstNegative(BASE));
// what building permits already say about FY2027-28 new growth (permit_leading_indicator.py)
{ const pl = JSON.parse(fs.readFileSync("../output/permit_leading_indicator.json"));
  const tb = csv("../output/permit_leading_indicator.csv");
  const M = v => "$" + Math.round(v / 1e6) + " million", M5 = v => "about $" + Math.round(v / 5e6) * 5 + " million";
  const M1 = v => "$" + (v / 1e6).toFixed(1) + " million";
  for (const fy of ["2027", "2028"]) { const y = pl.years[fy];
    put(`pl_${fy}_expected`, M5(y.expected_valuation.mid));
    put(`pl_${fy}_range`, M(y.expected_valuation.low) + " to " + M(y.expected_valuation.high));
    put(`pl_${fy}_base`, M5(y.base_valuation));
    put(`pl_${fy}_shortfall`, M1(y.shortfall.mid)); }
  put("pl_effect_fy2028", M1(pl.effect_fy2028.mid));
  { const v = +byYear[2028].surplus_deficit - pl.effect_fy2028.mid;
    put("room_fy2028_after_permits", money(Math.abs(v)));
    // reads after "FY2028 would have": room or a shortfall, whichever the numbers give
    put("fy2028_after_permits", v >= 0 ? "about " + money(v) + " of room" : "a shortfall of about " + money(-v)); }
  put("pl_effect_fy2040", "about " + M1(pl.effect_fy2040.mid).replace(".0 ", " "));
  put("pl_effect_fy2040_range", M1(pl.effect_fy2040.high) + " to " + M1(pl.effect_fy2040.low));
  const tx = y => +tb.find(r => +r.permit_year === y).taxable_permits;
  put("pl_taxable_2024", M(tx(2024))); put("pl_taxable_2025", M(tx(2025)));
  const fitv = tb.filter(r => +r.permit_year >= 2018 && +r.permit_year <= 2023).map(r => +r.taxable_permits);
  put("pl_taxable_fit_range", M(Math.min(...fitv)) + " to " + M(Math.max(...fitv)));
  put("pl_fy2026_certified", M(pl.certified.valuation));
  put("pl_fy2026_real_estate", M(pl.certified.real_estate_valuation));
  put("pl_ratio_range", pl.ratio_min.toFixed(2) + " to " + pl.ratio_max.toFixed(2));
  if (pl.partial_year) { put("pl_partial_year", String(pl.partial_year.year));
    put("pl_partial_to_date", M(pl.partial_year.taxable_to_date)); put("pl_partial_annualized", "about " + M5(pl.partial_year.annualized).replace("about ", "")); }
  const d = new Date(pl.last_permit + "T12:00:00");
  put("pl_last_permit", d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })); }
// faster growth through housing alone: extra homes by FY2040 and the gain per added home
{ const b = runModel(D, BASE, {}), r = runModel(D, { ...BASE, growth: "peer_target_residential_led" }, {});
  const i = b.years.indexOf(2040), extra = r.homes_total[i] - b.homes_total[i];
  put("base_homes_added_fy40", "about " + (Math.round((b.homes_total[i] - D.consts.homes_fy2025) / 100) * 100).toLocaleString("en-US"));
  { const added = b.homes_total[i] - D.consts.homes_fy2025, r10 = v => (Math.round(v / 10) * 10).toLocaleString("en-US");
    put("base_students_low", r10(added * 0.17)); put("base_students_high", r10(added * D.consts.students_per_home)); }
  put("resled_extra_homes", "about " + (Math.round(extra / 100) * 100).toLocaleString("en-US"));
  put("resled_gain_per_home", "about $" + (Math.round((r.room[i] - b.room[i]) / extra / 100) * 100).toLocaleString("en-US")); }
// FY2040 net (tax less service cost) by type of growth and scenario, for the growth-value table
{ const gt = csv("../output/expense_driver_forecast_growth_types.csv").filter(r => +r.fiscal_year === 2040);
  const T = { "New residential units": "homes", "Residential renovation": "resreno", "New commercial space": "com",
              "Commercial renovation": "comreno", "Personal property": "pp", "Chestnut Hill (CHCA)": "chca" };
  const S = { trend_continues: "trend", peer_target_balanced_mix: "even", peer_target_commercial_led: "comled",
              peer_target_residential_led: "resled" };
  gt.forEach(r => { if (T[r.growth_type] && S[r.growth_scenario]) {
    const v = +r.net / 1e6; put(`gt_${T[r.growth_type]}_${S[r.growth_scenario]}`, (v < 0 ? "−" : "+") + "$" + Math.abs(v).toFixed(1) + "M"); } });
  // unsigned, for prose: what the trend's new homes add, net of their students and services, in FY2040
  const h = gt.find(r => r.growth_type === "New residential units" && r.growth_scenario === "trend_continues");
  put("homes_net_fy2040", "$" + (+h.net / 1e6).toFixed(1) + " million"); }
// new homes: pace, value and record from the hand-coded permit count (new_homes_parameters.py)
{ const nh = JSON.parse(fs.readFileSync("../output/new_homes_parameters.json"));
  const by = csv("../output/permit_homes_by_year.csv");
  const near = (v, step) => (Math.round(v / step) * step).toLocaleString("en-US");
  put("homes_pace", "about " + near(nh.pace_homes_per_year, 5));
  put("homes_pace_years", nh.pace_years.join(" to "));
  put("homes_value", "$" + near(nh.blended_value_per_net_home_fy2026, 1000));
  put("homes_value_apts", "$" + near(nh.value_per_net_home_fy2026.apartments, 1000));
  put("homes_value_condos", "$" + near(nh.value_per_net_home_fy2026.small_multifamily, 1000));
  put("homes_age_share", Math.round(nh.mix.age_restricted * 100) + "%");
  put("homes_permitted_fy11_25", "about " + near(nh.homes_permitted_2010_2024, 50));
  put("homes_pace_2008_15", "about " + near(nh.homes_by_period["2008-2015"], 1));
  const yr = y => by.find(r => +r.year === y);
  put("homes_permits_2022", (+yr(2022).net_excluding_assisted_living).toLocaleString("en-US"));
  put("homes_permits_2024", (+yr(2024).net_excluding_assisted_living).toLocaleString("en-US"));
  put("homes_permits_2025", (+yr(2025).net_excluding_assisted_living).toLocaleString("en-US"));
  // permits that could have been finished by the April 2020 Census
  put("homes_permits_09_18", "about " + near(by.filter(r => +r.year >= 2009 && +r.year <= 2018)
    .reduce((t, r) => t + +r.net_excluding_assisted_living, 0), 10)); }
put("runs_out_premiums_high", firstNegative(byLabel(/^Health premiums 10%/)));
put("runs_out_enroll_cm_staff", firstNegative(byLabel(/^Cropper-McKibben enrollment, staff follow it/)));
put("runs_out_pay_up1", firstNegative(byLabel(/^Pay growth \+1 point/)));
put("runs_out_school_pay_psb", firstNegative(byLabel(/^School pay at PSB's forecast/)));
put("runs_out_staff_keep", firstNegative(byLabel(/^School staff held at the FY2027 level/)));
put("runs_out_homes_none", firstNegative(byLabel(/^No new homes built/)));
{ const r = runModel(D, byLabel(/^School staff held at the FY2027 level/), {});
  put("room_fy2040_staff_keep", signed(r.room[r.years.indexOf(2040)])); }
put("runs_out_pay_up1_premiums_high", firstNegative({ ...BASE, pay: 0.04, premium_long: 0.10 }));
// pay one point higher, with new growth at the peer rate: commercial-led vs housing-led
const PAY1_COM = { ...BASE, pay: 0.04, growth: "peer_target_commercial_led" };
const PAY1_HOUSE = { ...BASE, pay: 0.04, growth: "peer_target_residential_led" };
put("runs_out_pay_up1_commercial", firstNegative(PAY1_COM));
put("runs_out_pay_up1_housing", firstNegative(PAY1_HOUSE));
// base-case pay growth by group, and the average weighted by FY2027 payroll (schools' personnel
// share of their budget; Town departments' personnel share, split Public Safety / other)
{ const c = D.consts, ad = D.adopted, b = BASE;
  const town = b.pay, sch = b.pay + b.school_pay_drift, ps = b.pay + b.pay_ps_premium;
  const wS = ad.schools * c.school_personnel_share, wT = ad.town_departments * c.pD;
  const avg = (wS * sch + wT * c.psD * ps + wT * (1 - c.psD) * town) / (wS + wT);
  const pct = v => (v * 100).toFixed(1) + "%";
  put("pay_town", pct(town)); put("pay_school", pct(sch)); put("pay_ps", pct(ps));
  put("pay_avg", pct(avg)); put("pay_avg_up1", pct(avg + 0.01)); }
{ const r = runModel(D, PAY1_COM, {}); put("room_fy2040_pay_up1_commercial", money(r.room[r.years.indexOf(2040)])); }
// growth builds: the room peer-rate growth (even mix) adds by FY2030, against FY2040
{ const b = runModel(D, BASE, {}), r = runModel(D, { ...BASE, growth: "peer_target_balanced_mix" }, {});
  put("growth_peer_even_gain_fy2030", money(r.room[r.years.indexOf(2030)] - b.room[b.years.indexOf(2030)])); }

// ---- new growth (Python breakeven solve and the engine's growth grid)
put("trend_growth_rate", pct(D.trend_rate, 2));
put("peer_growth_rate", pct(D.peer_rate, 2));
const be = csv("../output/driver_forecast_breakeven.csv");
const gapNoOverride = +byYear[2040].surplus_deficit - +byYear[2040].may_2026_override_value;
for (const r of be) {
  const ch = (r.case || r[Object.keys(r)[0]]).replace("new growth via ", "");
  if (!["renovation", "proportional", "housing"].includes(ch)) continue;
  // run directly (2026-10-14): a tenth of a point more through this channel, FY2040 room gained,
  // averaged over the lift to the peer rate (2026-10-15, so a single cost step can't dominate).
  // It had been the no-override gap over the lift that closes it, which fails once there is no gap.
  const tenth = +r.fy2040_per_tenth;
  put(`per_tenth_${ch}`, (tenth < 0 ? "\u2212$" : "$") + Math.abs(tenth / 1e6).toFixed(1) + " million");
  put(`per_tenth_${ch}_m`, (tenth < 0 ? "\u2212$" : "$") + Math.abs(Math.round(tenth / 1e6)) + "M");
}
const room = csv("../output/new_growth_room_by_rate.csv");
const base40 = +byYear[2040].surplus_deficit / 1e6;
const slower = room.find(r => r.step_points === "-0.1");
put("per_tenth_slower", "$" + (base40 - +slower.room_fy2040).toFixed(1) + " million");

// ---- spending growth by cause, FY2011 to FY2025 (expense_drivers_tree.py)
const tree = csv("../output/expense_drivers_tree_fy11_25.csv");
const CAUSE = {
  "Inflation": ["Inflation", "outside"],
  "School & other buildings (debt)": ["Buildings (debt service)", "decide"],
  "Staffing levels (service choices)": ["Staffing levels", "decide"],
  "Legacy pension paydown": ["Past pension shortfall", "past"],
  "New homes & commercial space": ["New homes & commercial space", "growth"],
  "Other": ["Other", "other"],
  "Pay & costs above/below inflation": ["Pay & costs vs inflation", "decide"],
  "OPEB prefunding": ["Retiree health prefunding", "decide"],
  "Enrollment change (not from new homes)": ["Enrollment not from new homes", "other"],
};
const causeTotals = {};
tree.forEach(r => { causeTotals[r.group] = (causeTotals[r.group] || 0) + +r.dollars; });
const treeTotal = Object.values(causeTotals).reduce((a, b) => a + b, 0);
put("spending_growth_fy11_25", "$" + Math.round(treeTotal / 1e6) + " million");
const causes = Object.entries(causeTotals).map(([g, v]) => {
  if (!CAUSE[g]) throw new Error("unmapped spending cause " + g);
  return { label: CAUSE[g][0], kind: CAUSE[g][1], v: +(v / 1e6).toFixed(2),
           parts: tree.filter(r => r.group === g).map(r => [r.block + ": " + r.component, +(+r.dollars / 1e6).toFixed(2)]) };
}).sort((a, b) => b.v - a.v);
causes.forEach(c => { const key = c.label.toLowerCase().replace(/[^a-z]+/g, "_").replace(/_$/, "");
  put("cause_" + key, "$" + c.v.toFixed(1) + " million (" + Math.round(c.v / (treeTotal / 1e6) * 100) + "%)");
  // short forms for tables: "$7.3M" and "4%"
  put("cause_m_" + key, (c.v < 0 ? "−" : "") + "$" + Math.abs(c.v).toFixed(1) + "M");
  put("cause_pct_" + key, Math.round(c.v / (treeTotal / 1e6) * 100) + "%"); });
// growth in the town itself, piece by piece (homes and commercial split by their RKG costs)
{ const g = tree.filter(r => r.group === "New homes & commercial space"), M = v => "$" + (v / 1e6).toFixed(1) + "M";
  const town = +g.find(r => r.block === "Town departments").dollars, note = g.find(r => r.block === "Town departments").note;
  const n = note.match(/([\d,]+) homes x \$([\d,]+) \+ ([\d,]+) commercial employees x \$(\d+)/).slice(1).map(x => +x.replace(/,/g, ""));
  const homesShare = n[0] * n[1] / (n[0] * n[1] + n[2] * n[3]);
  const benefits = g.filter(r => r.block === "Benefits").reduce((a, r) => a + +r.dollars, 0);
  put("growth_piece_schools", M(+g.find(r => r.block === "Schools").dollars));
  put("growth_piece_town_homes", M(town * homesShare)); put("growth_piece_town_com", M(town * (1 - homesShare)));
  put("growth_piece_benefits", M(benefits)); put("growth_piece_total", M(g.reduce((a, r) => a + +r.dollars, 0)));
  put("growth_students_from_homes", "about " + (Math.round(+g.find(r => r.block === "Schools").note.match(/([\d,]+) students/)[1].replace(/,/g, "") / 10) * 10).toLocaleString("en-US"));
  put("cause_staffing_short", "$" + (causeTotals["Staffing levels (service choices)"] / 1e6).toFixed(1) + " million"); }
// who sets it: Brookline's decisions, growth, outside Brookline, past obligations
const assess = tree.filter(r => /assessments/i.test(r.block)).reduce((a, r) => a + +r.dollars, 0);
const who = { decide: 0, growth: 0, outside: assess, past: 0 };
causes.forEach(c => { if (who[c.kind] !== undefined && c.kind !== "outside") who[c.kind] += c.v * 1e6; });
who.outside += causeTotals["Inflation"];
for (const [k, v] of Object.entries(who))
  put("spending_set_by_" + k, "$" + (v / 1e6).toFixed(1) + " million (" + Math.round(v / treeTotal * 100) + "%)");
who.other = treeTotal - who.decide - who.growth - who.outside - who.past;  // other benefits, reconciling items
put("spending_set_by_other", "$" + (who.other / 1e6).toFixed(1) + " million (" + Math.round(who.other / treeTotal * 100) + "%)");
const whoSets = ["outside", "decide", "past", "growth", "other"].map(k => ({ kind: k, v: +(who[k] / 1e6).toFixed(2) }));
// inflation benchmarks and how far Brookline's costs per person ran from them (expense_drivers_tree.py)
const comp = (block, re) => tree.filter(r => r.block === block && re.test(r.component)).reduce((a, r) => a + +r.dollars, 0);
const sm = v => (v < 0 ? "−" : "+") + "$" + (Math.abs(v) / 1e6).toFixed(1) + " million";
put("pay_vs_infl_schools", sm(comp("Schools", /above\/below inflation/)));
put("pay_vs_infl_town", sm(comp("Town departments", /above\/below inflation/)));
put("pay_vs_infl_health", sm(comp("Benefits", /premiums above inflation/)));
put("pay_vs_infl_health_infl", "$" + (comp("Benefits", /premium inflation/) / 1e6).toFixed(1) + " million");
put("pay_vs_infl_pension_rate", sm(comp("Benefits", /higher cost per dollar of pay/)));
const idxRows = csv("../output/price_indices_annual.csv");
const fyIdx = (name, fy) => { const v = idxRows.filter(r => +r.calendar_year === fy - 1 || +r.calendar_year === fy).map(r => +r[name]); return v.reduce((a, b) => a + b, 0) / v.length; };
for (const [k, name] of [["eci", "eci_total_comp"], ["cpi", "cpi_boston"], ["benefits", "eci_benefits"]])
  put(`infl_${k}_fy11_25`, pct(Math.pow(fyIdx(name, 2025) / fyIdx(name, 2011), 1 / 14) - 1, 1));

// ---- school enrollment and staff, FY2008 to FY2025 (DESE, school_enrollment_staffing)
const sch = csv("../output/school_enrollment_staffing_fy05_25.csv").filter(r => r.total_staff_fte);
const staffEnroll = sch.map(r => [+r.fiscal_year, +r.total_enrollment, +r.total_staff_fte]);

// ---- what decides the 2040 budget: each assumption's FY2040 and 15-year effect
const DECIDE = [
  ["pay_up1", "Pay growth 1 point higher for every group", "base: Town 3.0%, schools 3.7%, Public Safety 3.5%", "decide"],
  ["school_pay_psb", "School pay rising about 5% a year", "base: 3.7%, the School Department's own forecast is about 5%", "decide"],
  ["pension_kept", "Freed pension money kept in the budget", "base: from FY2031 it pays down the retiree health (OPEB) liability", "decide"],
  ["opeb_spend", "Money freed by the retiree health payoff spent", "base: held for a decision once the liability is paid off", "decide"],
  ["premiums_high", "Health premiums 10% a year from FY2030", "base: 8%", "outside"],
  ["pay_to_target", "School and Public Safety pay at the 3% target", "base: +0.7 and +0.5 points", "decide"],
  ["staff_keep", "School staff held at the FY2027 level", "base: staff fall half as fast as enrollment, as in FY2019-25", "decide"],
  ["staff_follow", "School staff follow enrollment down fully", "base: staff fall half as fast as enrollment", "decide"],
  ["pay_down_half", "Pay growth half a point lower for every group", "base: Town 3.0%", "decide"],
  ["premiums_low", "Health premiums 6.5% a year from FY2030", "base: 8%", "outside"],
  ["enroll_cm_staff", "Enrollment rebounds, staff follow", "base: NESDEC's decline; rebound per the School Department's forecast", "outside"],
  ["peer_commercial", "Faster growth, led by commercial space", "base: the recent 1.23% a year", "growth"],
  ["peer_even", "Faster growth, half homes and half commercial", "base: the recent 1.23% a year", "growth"],
  ["peer_housing", "Faster growth, led by new homes", "base: the recent 1.23% a year", "growth"],
  ["school_np_extra", "School non-personnel 2 points above prices", "base: prices", "outside"],
  ["inflation_high", "Prices rising 3.5% a year", "base: 2.5%", "outside"],
  ["chca_in_trend", "Chestnut Hill counted inside trend growth", "base: added on top", "growth"],
  ["capital_table", "Capital held at the Town's six-year table, about 6%", "base: the 6.6% policy from FY2028", "decide"],
  ["homes_none", "No new homes built", "base: about the recent pace; renovation and commercial continue", "growth"],
  ["cost_home_rkg", "Town cost of a new home $1,109 (RKG)", "base: $660, with police and fire in steps", "growth"],
  ["cost_home_low", "Town cost of a new home $230", "base: $660", "growth"],
  ["ps_restore", "Police and fire back to earlier staffing", "base: FY2027 budget, 128 police and 160 firefighters", "decide"],
  ["police_step", "Police grow with homes, at the peer ratio", "base: 128 police, with police cost growing a little per home", "decide"],
  ["pension_slip", "Pension full funding two years late", "base: FY2030", "outside"],
];
const decisions = DECIDE.map(([key, label, base, kind]) => {
  const row = sens.find(r => SENS.find(x => x[0] === key)[1].test(r.dial));
  return { key, label, base, kind, fy40: +(+row.balance_change / 1e6).toFixed(2), fy35: +(+row.balance_change_fy2035 / 1e6).toFixed(2), total: +(+row.cumulative_balance_change_fy26_40 / 1e6).toFixed(2) };
}).sort((a, b) => Math.abs(b.fy40) - Math.abs(a.fy40));

// cost of one added student with staff, FY2027 dollars (marginal_student_cost in the driver forecast)
{ const mc = csv("../output/marginal_cost_per_student.csv");
  const v = +mc.find(r => r.component === "total").value;
  put("student_cost", "$" + Math.round(v).toLocaleString("en-US"));
  put("student_cost_about", "$" + (Math.round(v / 100) * 100).toLocaleString("en-US")); }
// ---- typed-number replacements (2026-10-08): figures that used to be typed into pages
// enrollment
const enr = y => +byYear[y].enrollment;
put("enroll_fy2040_about", "about " + (Math.round(enr(2040) / 100) * 100).toLocaleString("en-US"));
put("enroll_fy2040", Math.round(enr(2040)).toLocaleString("en-US"));
put("enroll_fy2030", Math.round(enr(2030)).toLocaleString("en-US"));
put("enroll_fy2028", Math.round(enr(2028)).toLocaleString("en-US"));
put("enroll_fy2034", Math.round(enr(2034)).toLocaleString("en-US"));
// open seats: homes beyond the recent pace whose children fit under the FY2027 level
{ const cap = csv("../output/new_growth_enrollment_capacity.csv").filter(r => r.homes_beyond_trend_that_fit_under_fy2027_level !== "");
  const h = y => +cap.find(r => +r.fiscal_year === y).homes_beyond_trend_that_fit_under_fy2027_level;
  const about = v => "about " + (Math.round(v / 100) * 100).toLocaleString("en-US");
  put("seats_homes_fy2030", about(h(2030))); put("seats_homes_fy2040", about(h(2040)));
  // the same open seats in students, and in homes at other children-per-home rates
  const near = (v, step) => (Math.round(v / step) * step).toLocaleString("en-US");
  for (const y of [2030, 2040]) {
    const st = h(y) * D.consts.students_per_home;
    put(`seats_students_fy${y}`, near(st, 10));
    put(`seats_homes_avg_fy${y}`, near(h(y), 100));
    put(`seats_homes_family_fy${y}`, near(st / 0.56, y === 2030 ? 10 : 100));
    put(`seats_homes_apts_fy${y}`, near(st / 0.11, 100));
  } }
// what extra homes add to FY2040, staffed in full vs filling empty seats (new_growth_page_data.js)
{ const fill = csv("../output/new_growth_housing_fill_fy2040.csv");
  ["a", "b", "c"].forEach((k, i) => { const r = fill[i];
    put(`fill_${k}_homes`, (Math.round(+r.added_homes_by_fy2040 / 100) * 100).toLocaleString("en-US"));
    put(`fill_${k}_staffed`, (+r.fy2040_gain_students_staffed_m < 0 ? "−$" : "$")
      + Math.abs(+r.fy2040_gain_students_staffed_m).toFixed(1) + " million");
    put(`fill_${k}_seats`, (+r.fy2040_gain_students_fill_seats_m < 0 ? "−$" : "$")
      + Math.abs(+r.fy2040_gain_students_fill_seats_m).toFixed(1) + " million"); }); }
// the two enrollment forecasts' gap in FY2034 (School Department's vs the base case)
{ const m = fs.readFileSync("../docs/_build/charts.js", "utf8").match(/var seatsCM = (\[.*?\]);/);
  const cm = JSON.parse(m[1]).find(r => r[0] === 2034)[1];
  put("cm_gap_fy2034", "about " + (Math.round((cm - enr(2034)) / 100) * 100).toLocaleString("en-US")); }
// the walk from the Town's plan to the base case, FY2031: only the schools step and the running
// balances after it move with the model; the other steps are fixed differences with the Town's plan
{ const rec = csv("../output/expense_driver_forecast_reconciliation.csv");
  const g = (y, line) => rec.find(r => +r.fiscal_year === y && r.line === line);
  const sch = (+g(2031, "schools").compare_value - +g(2031, "schools").driver_forecast) / 1e6;
  const start = -42.7, OVR = 27.3;   // the override's FY2031 value, grown with the levy (see the walk text)
  // new growth and other revenue: this forecast's FY2031 revenue against the Town plan's
  const ng = csv("../output/new_growth_scenarios_fy26_40.csv").filter(r => r.scenario === "trend_continues");
  const ngr = y => ng.find(r => +r.fiscal_year === y);
  const tpr = csv("../output/town_own_forecast_fy26_31.csv");
  const tpRev = s => +tpr.find(r => r.category === "revenue" && r.subcategory === s)["2031"];
  const m31 = ngr(2031);
  const stepNG = (+m31.property_taxes - tpRev("property_taxes")) / 1e6 - OVR;
  const rcpt = (+m31.local_receipts - tpRev("local_receipts")) / 1e6;
  const fcD = (+m31.free_cash - tpRev("free_cash")) / 1e6;
  const saD = (+m31.state_aid - tpRev("state_aid")) / 1e6;
  const fcLeft = +byYear[2031].free_cash_left / 1e6;   // set aside for capital and one-time uses by policy
  const stepRev = rcpt + fcD + saD - fcLeft;
  const ngD = y => { const r = ngr(y); return ["new_growth_res_new_dollars", "new_growth_res_reno_dollars",
    "new_growth_com_new_dollars", "new_growth_com_reno_dollars", "new_growth_com_personal_property_dollars",
    "chca_property_tax_dollars"].reduce((t, k) => t + (+r[k] || 0), 0) / 1e6; };
  const beforeSchools = start + OVR + stepNG + stepRev;
  const end = +byYear[2031].surplus_deficit / 1e6;
  // capital: the Town's plan's higher cash capital lines (+4.8), less the capital table's debt
  // service against the Town plan's (both within the levy)
  const tp = csv("../output/town_own_forecast_fy26_31.csv");
  const tpv = (c, s) => +tp.find(r => r.category === c && r.subcategory === s)["2031"];
  const debtGap = (tpv("expenditure", "nondept_debt_service") - tpv("revenue", "debt_exclusion")
    - +byYear[2031].debt_within_levy) / 1e6;
  // and less the top-up that brings capital to the 6.6% policy on this forecast's revenue
  const be31 = csv("../output/baseline_expense_forecast_fy26_40.csv").find(r => r.scenario === "trend_corrected" && +r.fiscal_year === 2031);
  // the capital top-up only; the reserve fund at its 1% policy is a difference of its own, in "other"
  // (free cash left over by policy also sits in other_nondept; it is shown with revenue, step 3)
  const topUp = (+byYear[2031].other_nondept - +be31.other_nondept - +byYear[2031].nondept_policy
    - +byYear[2031].free_cash_left) / 1e6;
  const cap = 4.8 + debtGap - topUp;
  const td = (+g(2031, "departmental_town").compare_value - +g(2031, "departmental_town").driver_forecast) / 1e6;
  const r4 = beforeSchools + sch, r5 = r4 + td, r6 = r5 + cap;   // Town departments, capital
  const sM = v => (v < 0 ? "−" : "+") + "$" + Math.abs(v).toFixed(1) + "M";
  const aM = v => "$" + Math.abs(v).toFixed(1) + "M";
  put("walk_ng", sM(stepNG)); put("walk_run2", sM(start + OVR + stepNG));
  put("walk_ng_fy2028", "$" + ngD(2028).toFixed(1) + "M"); put("walk_ng_fy2031", "$" + ngD(2031).toFixed(1) + "M");
  put("walk_rev", sM(stepRev)); put("walk_run3", sM(beforeSchools));
  put("walk_rev_receipts", sM(rcpt)); put("walk_rev_fc", sM(fcD)); put("walk_rev_sa", sM(saD)); put("walk_rev_fc_left", aM(fcLeft));
  // the policy step reads either way: free cash left over is set aside; a shortfall trims capital
  put("walk_rev_fc_policy", fcLeft >= 0 ? "less " + aM(fcLeft) + " of free cash set aside by policy"
    : "plus " + aM(fcLeft) + " because free cash falls that much short of the capital and reserve uses already counted, which trims capital");
  put("walk_town", sM(td));
  put("walk_schools", sM(sch)); put("walk_schools_abs", "$" + sch.toFixed(1) + " million");
  put("walk_capital", sM(cap)); put("walk_run4", sM(r4)); put("walk_run5", sM(r5)); put("walk_run6", sM(r6));
  put("walk_other", sM(end - r6)); put("walk_end", sM(end));
  put("walk_gap", "$" + (end - start).toFixed(1) + " million");
  put("walk_override_schools", "$" + (27.3 + sch).toFixed(1) + " million");
  put("walk_override_schools_m", "$" + (27.3 + sch).toFixed(1) + "M"); put("walk_gap_m", "$" + (end - start).toFixed(1) + "M"); }
// spending by line, FY2027 adopted / FY2031 / FY2040 (topic-forecast "Where the money goes")
{ const M1 = v => "$" + (v / 1e6).toFixed(1) + "M";
  const cg = (a, b) => (Math.pow(b / a, 1 / 13) - 1) * 100;
  const L = { schools: ["schools"], town: ["departmental_base", "departmental_growth"], total: ["operating_expenditure"],
    health: ["group_health", "growth_staff_benefits"], pensions: ["pensions"], opeb: ["opeb"],
    otherben: ["other_benefits"], debt: ["debt_within_levy"], other: ["other_nondept"] };
  for (const [k, cols] of Object.entries(L)) {
    const v = y => cols.reduce((a, c) => a + +byYear[y][c], 0);
    for (const y of [2027, 2031, 2040]) put(`line_${k}_fy${y}`, M1(v(y)));
    put(`line_${k}_cagr`, cg(v(2027), v(2040)).toFixed(1).replace("-", "−") + "%");
  } }
// the four decisions' range by FY2040
{ const four = ["pay_up1", "pension_kept", "premiums_high", "staff_keep"].map(k => Math.abs(decisions.find(d => d.key === k).fy40));
  put("four_decisions_low", "$" + Math.round(Math.min(...four)) + " million");
  put("four_decisions_high", "$" + Math.round(Math.max(...four)) + " million"); }

// births behind the enrollment path (expense_driver_forecast.births_basis)
{ const bb = {}; csv("../output/enrollment_births_basis.csv").forEach(r => bb[r.item] = +r.value);
  const about = (v, step) => "about " + (Math.round(v / step) * step).toLocaleString("en-US");
  put("births_ahead", Math.round(bb.births_ahead).toLocaleString("en-US"));
  put("birthpool_fall_pct", Math.round((1 - bb.pool_fy2040 / bb.pool_fy2025) * 100) + "%");
  put("birthtab_today_students", about(bb.per_birth_today * bb.pool_fy2040, 10));
  put("birthtab_today_ratio", bb.per_birth_today.toFixed(2));
  put("birthtab_peak_students", about(bb.per_birth_peak * bb.pool_fy2040, 10));
  put("birthtab_base_students", about(bb.per_birth_base_fy2040 * bb.pool_fy2040, 10));
  put("birthtab_base_ratio", bb.per_birth_base_fy2040.toFixed(2));
  put("birthtab_level_ratio", bb.per_birth_level_fy2040.toFixed(2));
  put("birthtab_peak_shortfall", about(6889 - bb.per_birth_peak * bb.pool_fy2040, 100));
  put("cm_per_birth_fy2034", bb.per_birth_cm_fy2034.toFixed(2)); }

// ---- a typical tax bill to FY2040 (tax_bill_paths.py)
const bills = csv("../output/tax_bill_paths.csv");
const billNotes = {}; csv("../output/tax_bill_paths_notes.csv").forEach(r => billNotes[r.item] = +r.value);
const taxBills = { years: [], paths: {}, medians: { single_family: [2396400, 20904], two_family: [2204300, 18937], condo: [839600, 4963],
                                                  apartment: [billNotes.apartment_value_fy26, billNotes.apartment_tax_fy26] },
                   rate: billNotes.tax_rate_fy26, exemption: billNotes.exemption_fy26 };
bills.forEach(r => {
  (taxBills.paths[r.path] = taxBills.paths[r.path] || []).push(+r.bill_index);
  if (r.path === "base") taxBills.years.push(+r.fiscal_year);
});
const dollars = v => "$" + Math.round(v).toLocaleString("en-US");
for (const path of Object.keys(taxBills.paths)) {
  for (const y of [2027, 2030, 2035, 2040]) {
    const row = bills.find(r => r.path === path && +r.fiscal_year === y);
    put(`bill_${path}_sf_fy${y}`, dollars(+row.single_family_bill));
    put(`bill_${path}_condo_fy${y}`, dollars(+row.condo_bill));
    put(`bill_${path}_apt_fy${y}`, dollars(+row.apartment_bill));
    put(`bill_${path}_pct_fy${y}`, Math.round((+row.bill_index - 1) * 100) + "%");
  }
}
const idx = p => taxBills.paths.base[taxBills.years.indexOf(p)];
for (const path of Object.keys(taxBills.paths)) {  // FY2026-40 average annual growth of each path
  const v = taxBills.paths[path];
  put(`bill_${path}_cagr`, pct(Math.pow(v[v.length - 1] / v[0], 1 / (taxBills.years.length - 1)) - 1, 1));
}
for (const path of Object.keys(taxBills.paths)) {  // FY2030-40, after the May 2026 override has phased in
  const v = taxBills.paths[path], i30 = taxBills.years.indexOf(2030);
  put(`bill_${path}_cagr_30_40`, pct(Math.pow(v[v.length - 1] / v[i30], 1 / (taxBills.years.length - 1 - i30)) - 1, 1));
}
put("bill_base_cagr_26_30", pct(Math.pow(idx(2030) / idx(2026), 1 / 4) - 1, 1));
put("bill_apt_fy2026", dollars(billNotes.apartment_tax_fy26));
put("bill_apt_month_fy2026", dollars(billNotes.apartment_tax_fy26 / 12));
put("bill_apt_value_fy2026", dollars(billNotes.apartment_value_fy26));
put("bill_apt_units", Math.round(billNotes.apartment_units).toLocaleString("en-US"));
put("bill_cpa_sf_fy2026", dollars(20904 * 0.01));
put("bill_base_growth_fy30_40", pct(Math.pow(idx(2040) / idx(2030), 0.1) - 1, 1));
put("bill_override_amount", money(billNotes.override_amount));
put("bill_override_fy", "FY" + billNotes.override_first_fy);
put("bill_baker_debt_service", money(billNotes.baker_annual_debt_service));
put("bill_baker_fy", "FY" + billNotes.baker_first_fy);
const diff = (p, y, col) => +bills.find(r => r.path === p && +r.fiscal_year === y)[col] - +bills.find(r => r.path === "base" && +r.fiscal_year === y)[col];
put("bill_baker_sf_extra_fy2035", dollars(diff("baker", 2035, "single_family_bill")));
put("bill_override_sf_extra_fy2040", dollars(diff("override", 2040, "single_family_bill")));
put("bill_growth_sf_saving_fy2040", dollars(-diff("growth", 2040, "single_family_bill")));
put("bill_baker_condo_extra_fy2035", dollars(diff("baker", 2035, "condo_bill")));

// ---- Brookline against its neighbors: births, kindergarten per birth, family-sized homes
// (families_by_town.py -> output/families_by_town.json)
const FT = JSON.parse(fs.readFileSync("../output/families_by_town.json", "utf8"));
{
  const pc = v => Math.round(Math.abs(v) * 100) + "%";
  const T = Object.fromEntries(FT.towns.map(t => [t.town, t]));
  put("births_drop_brookline", pc(FT.change.Brookline));
  put("births_drop_state", pc(FT.change.state));
  put("births_drop_inner", pc(FT.change["Neighboring cities and inner suburbs"]));
  put("births_drop_suburbs", pc(FT.change["Family suburbs"]));
  put("births_drop_rank", FT.brooklineRank + (["th", "st", "nd", "rd"][FT.brooklineRank % 10 < 4 && Math.floor(FT.brooklineRank / 10) % 10 !== 1 ? FT.brooklineRank % 10 : 0]));
  put("births_drop_towns", String(FT.townsRanked));
  for (const t of ["Brookline", "Lexington", "Newton", "Belmont", "Wellesley", "Cambridge", "Somerville", "Arlington", "Needham", "Winchester", "Wayland", "Watertown"]) {
    const k = t.toLowerCase();
    put(`births_change_${k}`, pc(T[t].births_change));
    put(`kpb_${k}`, T[t].k_per_birth.toFixed(2));
    put(`family_share_${k}`, pc(T[t].family_sized_share));
    put(`family_price_${k}`, "$" + (T[t].median_sale_family_sized / 1e6).toFixed(2) + " million");
    put(`hh_children_${k}`, pc(T[t].hh_with_children));
    put(`kids_per_home_${k}`, T[t].kids_per_home.toFixed(2));
    put(`big_share_${k}`, pc(T[t].big_share));
    put(`kids_per_big_${k}`, T[t].kids_per_big_home.toFixed(2));
    put(`pub_per_big_${k}`, T[t].public_per_big_home.toFixed(2));
    put(`public_share_${k}`, pc(T[t].public_share));
    put(`homes_${k}`, (Math.round(T[t].homes / 100) * 100).toLocaleString("en-US"));
  }
  // range across Newton and the family suburbs in the families-page table
  const SUB = ["Newton", "Belmont", "Winchester", "Needham", "Wellesley", "Wayland", "Lexington"];
  const rng = key => { const v = SUB.map(x => T[x][key]); return [Math.min(...v), Math.max(...v)]; };
  const [kl, kh] = rng("kids_per_big_home"), [pl, ph] = rng("public_per_big_home");
  put("kids_per_big_sub_low", kl.toFixed(2)); put("kids_per_big_sub_high", kh.toFixed(2));
  put("pub_per_big_sub_low", pl.toFixed(2)); put("pub_per_big_sub_high", ph.toFixed(2));
  // Brookline's children per 3+ bedroom home, at Lexington's share of 3+ bedroom homes
  put("kids_per_home_brookline_at_lex_mix", (T.Brookline.kids_per_big_home * T.Lexington.big_share).toFixed(2));
  const kpbs = FT.towns.map(t => t.k_per_birth).sort((a, b) => a - b);
  put("kpb_peer_median", ((kpbs[5] + kpbs[6]) / 2).toFixed(2));
  put("corr_kpb_family_share", FT.corr_kpb_family_share.toFixed(2));
  put("corr_kpb_price", FT.corr_kpb_price.toFixed(2));
  put("corr_kpb_acs_3br", FT.corr_kpb_acs_3br.toFixed(2));
  const sfg = t => { const s = FT.sfValue[t]; return s[s.length - 1][1] / s[0][1] - 1; };
  for (const t of ["Brookline", "Lexington", "Newton", "Wellesley"]) put(`sfvalue_growth_${t.toLowerCase()}`, pc(sfg(t)));
  const sv = (t, fy) => FT.sfValue[t].find(p => p[0] === fy)[1];
  put("sfvalue_brookline_fy2026", "$" + (sv("Brookline", 2026) / 1e6).toFixed(2) + " million");
  put("sfvalue_lexington_fy2026", "$" + (sv("Lexington", 2026) / 1e6).toFixed(2) + " million");
  put("sfvalue_ratio_fy2010", (sv("Brookline", 2010) / sv("Lexington", 2010)).toFixed(2));
  put("sfvalue_ratio_fy2026", (sv("Brookline", 2026) / sv("Lexington", 2026)).toFixed(2));
}

// ---- indicators to watch (build_enrollment_workbook.py -> enrollment_assumptions.json .indicators)
{ const I = JSON.parse(fs.readFileSync("../output/enrollment_assumptions.json", "utf8")).indicators;
  const n = v => Math.round(v).toLocaleString("en-US");
  for (const k of ["births", "births_prev", "births_nesdec", "births_cm", "enroll", "enroll_prev", "enroll_next_base", "enroll_next_cm",
                   "enroll_next_nesdec", "k", "k_births", "k_next_base", "k_next_cm", "k_next_nesdec", "k_next_births"]) put(`ind_${k}`, n(I[k]));
  put("cm_kpb_fy2034", (607 / Math.round(I.births_base_ahead)).toFixed(2));  // Cropper-McKibben FY2034 K (Appendix D)
  put("ind_births_year", String(I.births_year)); put("ind_births_prev_year", String(I.births_year - 1));
  put("ind_births_next_year", String(I.births_year + 1));
  put("ind_fy", "FY" + I.fy); put("ind_fy_next", "FY" + (I.fy + 1));
  put("ind_fall", String(I.fy - 1)); put("ind_fall_next", String(I.fy));
  put("ind_k_birth_year", String(I.k_birth_year)); put("ind_k_next_birth_year", String(I.k_birth_year + 1));
  put("ind_kpb", I.kpb.toFixed(2)); put("ind_kpb_min", I.kpb_min.toFixed(2)); put("ind_kpb_max", I.kpb_max.toFixed(2));
  put("ind_enroll_change", n(I.enroll_prev - I.enroll));
  put("ind_enroll_next_gap", "about " + n(Math.round((I.enroll_next_cm - I.enroll_next_base) / 10) * 10)); }

// ---- what new homes do to the budget, year by year (growth_links.py)
const GL = JSON.parse(fs.readFileSync("../output/growth_links.json", "utf8"));
{ const S = GL.summary, C = S.children, r1 = S.revenue_fit.calendar_plus3;
  const nf = v => Math.round(v).toLocaleString("en-US");
  const cents = v => v >= 1 ? "$" + v.toFixed(2) : Math.round(v * 100) + " cents";
  put("gl_permit_r", r1.r.toFixed(2)); put("gl_permit_n", String(r1.n));
  { const ex = GL.revenue.filter(r => r[3] != null);
    put("gl_expect_years", ex.map(r => "FY" + r[4]).join(" and "));
    put("gl_expect_text", ex.map(r => "about $" + Math.round(r[3] / 10) * 10 + " million in FY" + r[4]).join(" and ")); }
  { const P = S.parcel_timing, L = P.legacy, A = S.assessor_units;
    const pct = v => Math.round(v * 100) + "%";
    put("gl_pt_jobs", nf(P.visible)); const frac = v => v < 0.2 ? "under a fifth" : v < 0.4 ? "about a third" : v < 0.6 ? "about half" : "most";
    put("gl_pt_first", frac(P.share_jan1_1)); put("gl_pt_legacy_first", frac(L.share_jan1_1));
    put("gl_pt_h1_first", pct(P.h1_first_jan1)); put("gl_pt_h2_second", pct(P.h2_second_jan1));
    put("gl_pt_months", String(P.months_to_half));
    put("gl_pt_legacy_jobs", nf(L.visible)); put("gl_pt_legacy_months", String(L.months_to_half));
    const era = Object.values(L.months_by_era); put("gl_pt_legacy_months_range", Math.min(...era) + " to " + Math.max(...era));
    put("gl_au_raw", nf(A.raw)); put("gl_au_net", nf(A.net)); put("gl_au_per_year", "about " + Math.round(A.per_year / 10) * 10);
    put("gl_au_from", String(A.first_jan1)); put("gl_au_to", String(A.last_jan1));
    put("gl_au_min", nf(A.min)); put("gl_au_max", nf(A.max)); }
  put("gl_ng_per_permit", cents(r1.ratio_median)); put("gl_ng_per_permit_min", cents(r1.ratio_min)); put("gl_ng_per_permit_max", cents(r1.ratio_max));
  put("gl_children_added", C.children_per_added_home.toFixed(2)); put("gl_children_existing", C.children_per_existing_home.toFixed(2));
  put("gl_children_added_low", C.children_per_added_home_ci[0].toFixed(2)); put("gl_children_added_high", C.children_per_added_home_ci[1].toFixed(2));
  put("gl_children_check", C.children_per_added_home_check.toFixed(2)); put("gl_towns_n", String(C.n));
  put("gl_children_share", "about " + (Math.round(C.children_per_added_home / C.children_per_existing_home * 10) * 10) + "%");
  const B = C.brookline;
  put("gl_bk_homes_added", nf(B.homes_2020 - B.homes_2010)); put("gl_bk_children_added", nf(B.children_2020 - B.children_2010));
  put("gl_bk_children_from_homes", "about " + nf(C.brookline_children_from_added_homes));
  put("gl_kpb_min", S.kpb_min.toFixed(2)); put("gl_kpb_max", S.kpb_max.toFixed(2));
  put("gl_movers_typical", String(S.movers_typical));
  put("gl_units_per_year_06_19", String(S.units_2006_2019_per_year));
  put("gl_k12_2006", nf(S.k12_fall_2006)); put("gl_k12_2019", nf(S.k12_fall_2019)); put("gl_k12_latest", nf(S.k12_latest)); put("gl_latest_fall", String(S.latest_fall));
  put("gl_units_2020_25", nf(S.units_2020_2025)); put("gl_units_peak", String(S.units_peak)); put("gl_units_peak_year", String(S.units_peak_year));
  put("gl_sales_r", S.sales_fit["0"].r.toFixed(2)); put("gl_sales_n", String(S.sales_fit["0"].n));
  put("gl_movers_r0", S.sales_fit.movers["0"].r.toFixed(2)); put("gl_movers_r1", S.sales_fit.movers["1"].r.toFixed(2));
  put("gl_movers_n", String(S.sales_fit.movers["0"].n));
  // services rows: [fy, homes, homes is a Census count, police and fire, other Town, school staff, enrollment]
  const sv = GL.services, at = y => sv.find(r => r[0] === y), a = at(2010), c = at(2020), b = at(2025);
  const pc = (u, v) => Math.round((v / u - 1) * 100) + "%";
  put("gl_homes_2010", nf(a[1])); put("gl_homes_2020", nf(c[1])); put("gl_homes_pct_10_20", pc(a[1], c[1]));
  put("gl_ps_fy10", nf(a[3])); put("gl_ps_fy20", nf(c[3])); put("gl_ps_fy25", nf(b[3]));
  put("gl_other_fy10", nf(a[4])); put("gl_other_fy20", nf(c[4])); put("gl_other_fy25", nf(b[4]));
  put("gl_school_fy10", nf(a[5])); put("gl_school_fy20", nf(c[5])); put("gl_school_fy25", nf(b[5])); put("gl_school_pct_10_20", pc(a[5], c[5]));
  put("gl_enroll_fy10", nf(a[6])); put("gl_enroll_fy20", nf(c[6])); put("gl_enroll_pct_10_20", pc(a[6], c[6]));
  put("gl_students_added", C.students_per_added_home.toFixed(2)); put("gl_students_existing", C.students_per_existing_home.toFixed(2));
  put("gl_students_added_low", (C.students_per_added_home_ci[0] < 0 ? "&minus;" : "") + Math.abs(C.students_per_added_home_ci[0]).toFixed(2));
  put("gl_students_added_high", C.students_per_added_home_ci[1].toFixed(2)); put("gl_districts_n", String(C.districts_n));
  put("students_per_home_short", D.consts.students_per_home.toFixed(2)); }

// how far ahead each reading looks, in years from when the reading is in hand (the leads chart)
{ const fy = +String(facts.fire_company_fy).replace("FY", ""), now = 2026, ahead = isNaN(fy) ? 14 : fy - now;
  const S = GL.summary, r1 = S.revenue_fit.calendar_plus3;
  GL.leads = [
    { label: "Births", wait: 1.5, strong: [3.5, 4.5], loose: [4.5, 16.5], noteAt: 3.5,
      note: "Kindergarten 3 to 4 years after the report, then that class to grade 12",
      text: "The state reports births about a year and a half after the year ends. Kindergarten follows five years after birth, so three to four years after the report, at " + S.kpb_min.toFixed(2) + " to " + S.kpb_max.toFixed(2) + " kindergartners per birth; that class then moves up the grades." },
    { label: "October grade counts", wait: 0, strong: [0.5, 1.5], loose: [1.5, 12], noteAt: 0.5,
      note: "Next fall's grades 1 to 12 closely; each class for years after",
      text: "Next fall's grades 1 through 12 within about one percent, outside the pandemic, and each class as it moves up for years after." },
    { label: "Building permits", wait: 0, strong: [1.5, 2.5], loose: [2.5, 3.5], noteAt: 1.5,
      note: "New growth in the fiscal year that starts 18 months after the year's permits",
      text: "A calendar year's permits are valued on January 1 two years later and become new growth in the fiscal year that starts that July, about a year and a half after the year ends, at " + Math.round(r1.ratio_min * 100) + " to " + Math.round(r1.ratio_max * 100) + " cents of new value per permitted dollar." },
    { label: "Homes in town", wait: 0, strong: [ahead - 0.3, ahead + 0.3], loose: [0, ahead - 0.3], noteAt: 0,
      note: "A fire company at about " + facts.fire_company_homes + " homes, " + facts.fire_company_fy + " at the recent pace",
      text: "Steps such as a fire company, which the base case adds at about " + facts.fire_company_homes + " homes, " + facts.fire_company_fy + " at the recent pace of building, can be seen coming for years." },
    { label: "Home sales", wait: 0, strong: null, loose: [0, 0.8], noteAt: 0,
      note: "Kindergarten the same year, loosely",
      text: "Kindergartners per birth in the same year, a loose link (correlation " + S.sales_fit["0"].r.toFixed(2) + " over " + S.sales_fit["0"].n + " years)." },
  ]; }

const siteData = {
  growthLinks: GL,
  taxBills,
  room: Object.keys(byYear).map(y => [+y, +(+byYear[y].surplus_deficit / 1e6).toFixed(2)]),
  roomOverride: Object.keys(byYear).map(y => [+y, +((+byYear[y].surplus_deficit - +byYear[y].may_2026_override_value) / 1e6).toFixed(2)]),
  decisions, causes, whoSets, staffEnroll, employees,
  enrollAssume: JSON.parse(fs.readFileSync("../output/enrollment_assumptions.json", "utf8")),
  townFamilies: { birthsIndex: FT.birthsIndex, birthsRaw: FT.birthsRaw, groups: FT.groups, towns: FT.towns }, causesTotal: +(treeTotal / 1e6).toFixed(2),
};
fs.writeFileSync("../output/site_data.json", JSON.stringify(siteData));

// the retiree health (OPEB) liability in the base case, on the actuary's trend (2026-10-14)
{ const net = y => +byYear[y].opeb_net_liability;
  for (const y of [2027, 2030, 2031, 2035, 2040]) {
    put(`opeb_net_fy${y}`, "$" + Math.round(net(y) / 1e6) + " million");
    put(`opeb_net_fy${y}_m`, "$" + (net(y) / 1e6).toFixed(1) + "M"); }
  const paid = [...Array(13).keys()].map(i => 2028 + i).find(y => net(y) < 1);
  put("opeb_paid_off", paid ? "FY" + paid : "after FY2040");
  // what the payoff frees, held for a decision in the base case (2026-10-15)
  const held = y => +byYear[y].opeb_held;
  const heldFirst = [...Array(13).keys()].map(i => 2028 + i).find(y => held(y) > 1);
  const heldFull = [...Array(13).keys()].map(i => 2028 + i).find(y => y > (heldFirst || 9999) && held(y) > 1);
  put("opeb_freed_first", heldFirst ? "FY" + heldFirst : "after FY2040");
  put("opeb_freed_full", heldFull ? "FY" + heldFull : "after FY2040");
  put("opeb_freed_fy2040", "$" + Math.round(held(2040) / 1e6) + " million");
  put("opeb_freed_fy2040_m", "$" + Math.round(held(2040) / 1e6) + "M");
  put("opeb_freed_total", "$" + Math.round([...Array(13).keys()].reduce((s, i) => s + held(2028 + i), 0) / 1e6) + " million");
  put("room_fy2040_with_freed", "$" + Math.round((+byYear[2040].surplus_deficit + held(2040)) / 1e6) + " million");
  // total liabilities: the balance-sheet forecast with its OPEB line replaced by the driver model's
  const bs = csv("../output/balance_sheet_liabilities_forecast_fy25_40.csv");
  const tot = y => { const r = bs.find(x => +x.fiscal_year === y); return +r.total_liabilities - +r.net_opeb_liability + net(y); };
  put("liab_total_fy2031", "$" + Math.round(tot(2031) / 1e6) + " million");
  put("liab_total_fy2040", "$" + Math.round(tot(2040) / 1e6) + " million"); }

// the stress case: the Town's plan extended as-is, and the overrides it would take every three years
{ const t = csv("../output/baseline_surplus_deficit_forecast_fy26_40.csv").filter(r => r.scenario === "town_assumptions");
  const at = y => t.find(r => +r.fiscal_year === y);
  const sM1 = v => (v < 0 ? "\u2212$" : "+$") + Math.abs(v / 1e6).toFixed(1) + "M";
  for (const y of [2030, 2034, 2040]) { const r = at(y);
    put(`stress_bal_fy${y}`, sM1(+r.operating_surplus_deficit));
    put(`stress_pct_fy${y}`, (+r.operating_surplus_deficit < 0 ? "\u2212" : "")
      + Math.abs(100 * r.operating_surplus_deficit / r.operating_revenue).toFixed(1) + "%"); }
  const o = csv("../output/override_reliance_scenario_fy26_40.csv");
  o.filter(r => +r.new_override_this_year > 0).forEach(r =>
    put(`stress_ov_fy${r.fiscal_year}`, "$" + (r.new_override_this_year / 1e6).toFixed(1) + "M"));
  const last = o.find(r => +r.fiscal_year === 2040);
  put("stress_ov_total", "$" + (last.cumulative_hypothetical_override / 1e6).toFixed(1) + " million");
  put("stress_gap_fy2040", "\u2212$" + Math.abs(last.resulting_operating_surplus_deficit / 1e6).toFixed(1) + " million"); }

// ---- utilities, FY2006-FY2027 (utilities_history.py, from the Financial Plans)
{ const u = csv("../output/utilities_history.csv"), at = y => u.find(r => +r.fiscal_year === y);
  const g = (a, b, k) => pct(cagr(+at(a)[k], +at(b)[k], b - a));
  put("util_fy2019", money(+at(2019).utilities)); put("util_cpi_fy11_19", g(2011, 2019, "boston_cpi_fy_avg"));
  put("util_growth_fy19_24", g(2019, 2024, "utilities")); put("util_cpi_fy19_24", g(2019, 2024, "boston_cpi_fy_avg"));
  put("util_growth_fy24_27_budget", g(2024, 2027, "utilities"));
  put("util_fy2011", money(+at(2011).utilities)); put("util_fy2024", money(+at(2024).utilities));
  put("util_fy2027", money(+at(2027).utilities));
  put("util_share_fy2027", pct(+at(2027).utilities / +byYear[2027].operating_expenditure));
  // if utilities grew 6% a year from the FY2027 budget instead of the base case's 2.5% for prices
  put("fy40_util_6pct", money(+at(2027).utilities * (Math.pow(1.06, 13) - Math.pow(1.025, 13)))); }

fs.writeFileSync("../output/site_facts.json", JSON.stringify(facts, null, 1));
console.log(`wrote site_facts.json: ${Object.keys(facts).length} facts`);
