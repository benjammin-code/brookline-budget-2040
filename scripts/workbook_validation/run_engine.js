// Usage: node run_engine.js <project root> <scenarios.json>  -> JSON results per scenario
// Each scenario is a map of Explorer control id -> value, using the Explorer's codes;
// settings() below mirrors the template's apply() functions exactly.
const fs = require("fs"), path = require("path");
const P = process.argv[2];
const D = JSON.parse(fs.readFileSync(path.join(P, "output/dashboard_data_page.json")));
const { runModel } = require(path.join(P, "docs/_build/dashboard_engine.js"));
const B = D.base, R = D.revenue;
const BASE = { pay: 0, opeb: "redirect", staffing: "half", premium_long: B.premium_long, growth: 0,
  school_drift: B.school_pay_drift, ps_premium: B.pay_ps_premium, lr: R.lr_cagr, cpi: B.cpi, sa: R.sa_cagr,
  mix: "mix", fill: "staff", enroll: "nesdec", premium_near: B.premium_near, np_extra: B.sch_np_extra,
  capital: "full", cost_home: B.cost_per_home, chca: "approved", slip: "0", ov_amt: 0, ov_year: "2031", ps_staff: "budget", homes: "all", migration: 0 };
function settings(st) {
  const a = Object.assign({}, B), rv = {};
  a._step = 0; a._mix = "mix"; rv.ovYear = 2031;
  a.pay = B.pay + st.pay; a.opeb_redirect = st.opeb !== "keep"; a.opeb_hold = st.opeb === "redirect"; a.ratio_mode = st.staffing;
  a.premium_long = st.premium_long; a._step = st.growth; a.school_pay_drift = st.school_drift;
  a.pay_ps_premium = st.ps_premium; rv.lr = st.lr; a.cpi = st.cpi; rv.sa = st.sa; a._mix = st.mix;
  a.fill_capacity = st.fill === "fill"; a.enroll_mode = st.enroll; a.migration = st.migration; a.premium_near = st.premium_near;
  a.sch_np_extra = st.np_extra; a.capital_full = st.capital === "full"; a.cost_per_home = st.cost_home;
  a.chca = st.chca; a.pension_slip = +st.slip;
  a.ps_restore = st.ps_staff === "restore"; a.fire_step = st.ps_staff !== "none"; a.police_step = st.ps_staff === "police"; rv.ovAmt = st.ov_amt; rv.ovYear = +st.ov_year;
  const h = st.homes === "all" ? "" : "_homes_" + st.homes;
  a.growth = a._step === 0 ? (h ? "trend" + h : "trend_continues")
    : "grid_" + (a._step < 0 ? "mix" : a._mix) + "_" + (a._step > 0 ? "+" : "") + a._step + h;
  return { a, rv };
}
const scen = JSON.parse(fs.readFileSync(process.argv[3]));
const out = {};
for (const [nm, ch] of Object.entries(scen)) {
  const s = settings(Object.assign({}, BASE, ch));
  const r = runModel(D, s.a, s.rv);
  out[nm] = { years: r.years, room: r.room, revenue: r.revenue, spending: r.spending, lines: r.lines,
              staff: r.school_staff, enr: r.enrollment, units: r.units };
}
console.log(JSON.stringify(out));
