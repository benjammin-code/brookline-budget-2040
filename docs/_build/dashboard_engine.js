/* Driver forecast engine for the dashboard (docs/forecast_dashboard.html).

   A line-for-line port of expense_driver_forecast.run() (spending) and of the
   revenue side of new_growth_scenario_forecast.main() with the free-cash cycle
   (revenue_cash_cycle.apply). Inputs come from output/dashboard_data.json
   (scripts/export_dashboard_data.py). scripts/test_dashboard_engine.js checks it
   against the Python model for the base case, every "What Decides FY2040" dial,
   growth-grid points and changed revenue rates.

   a  : model settings, same keys as expense_driver_forecast.BASE, plus growth
        (a grid or named scenario) and chca
   rv : revenue settings { sa: state aid growth, lr: local receipts growth,
        ovAmt: a further override in dollars of its first year, ovYear }
        The override is the one input with no Python counterpart: it is added to
        the levy from ovYear and grows 2.5% a year (new growth on it is ignored). */

function runModel(D, a, rv) {
  rv = rv || {};
  var Y = D.years, Y0 = D.consts.anchor, K = D.consts, A = D.adopted, TS = D.town;
  var chca = a.chca || "approved";
  var G = D.growth[chca][a.growth], Gt = D.growth[chca]["trend_continues"];
  if (!G) throw new Error("no growth scenario " + a.growth);
  var chcaOn = chca === "in_trend" ? 0 : 1;
  var i0 = Y.indexOf(Y0);

  function ip(rate, rates) {
    var out = {}, v = 1;
    Y.forEach(function (y) {
      if (y >= Y0 + 1) v *= 1 + (rates && rates[y] != null ? rates[y] : rate);
      out[y] = v;
    });
    return out;
  }
  var adj = a.dept_pay_adj || 0;
  var W = ip(a.pay), Wdep = ip(a.pay + adj), Wps = ip(a.pay + adj + a.pay_ps_premium),
      Wsch = ip(a.pay + a.school_pay_drift), C = ip(a.cpi), Cnp = ip(a.cpi + a.sch_np_extra),
      prem = ip(a.premium_long, { 2028: a.premium_near, 2029: a.premium_near });
  var w25 = Math.pow(1 + a.pay, Y0 - 2025);
  var ps25 = Math.pow(1 + a.pay + adj + a.pay_ps_premium, Y0 - 2025);

  function cum(arr) {
    var out = {}, s = 0, s0 = 0;
    Y.forEach(function (y, i) { s += arr[i]; if (i === i0) s0 = s; out[y] = s; });
    Y.forEach(function (y) { out[y] = Math.max(out[y] - s0, 0); });
    return out;
  }
  var units = cum(G.units), unitsT = cum(Gt.units), sqft = cum(G.sqft);
  var ramp = {};
  Y.forEach(function (y) { ramp[y] = chcaOn * D.chca_ramp[y]; });
  // homes in town each year, for the fire company and police steps; the per-home charge drops
  // fire's (or police's) part of its public safety share when that service is modeled in steps
  var stock = {}, sAll = 0;
  Y.forEach(function (y, i) { sAll += G.units[i]; stock[y] = K.homes_fy2025 + sAll + K.chca_units * ramp[y]; });
  var fireStep = a.fire_step !== false;
  var policeStep = a.police_step === true;
  var perHome = a.cost_per_home * (1 - K.ps_share * ((fireStep ? 1 - K.ps_share_police : 0) + (policeStep ? K.ps_share_police : 0)));
  var restoreN = a.ps_restore ? K.ps_restore_positions : 0;

  // ---------------- revenue
  var R = D.revenue;
  var sa = rv.sa != null ? rv.sa : R.sa_cagr, lr = rv.lr != null ? rv.lr : R.lr_cagr;
  var ov = {};
  Y.forEach(function (y) {
    ov[y] = rv.ovAmt && y >= rv.ovYear ? rv.ovAmt * Math.pow(1.025, y - rv.ovYear) : 0;
  });
  var fcBy = {}, netRev = {}, surplus = {}, rev = [], parts = { property_tax: [], state_aid: [], local_receipts: [],
                                         free_cash: [], other_funds: [], override: [] };
  Y.forEach(function (y, i) {
    // state aid: the Town's FY2026 and adopted FY2027 figures, then the growth rate (2.5% base)
    var saY = y <= 2026 ? R.sa_2026 : R.sa_2027 * Math.pow(1 + sa, y - 2027);
    var actual = G.lr_rest[i] + R.lr_resid_2025 * Math.pow(1 + lr, y - 2025);
    var baseTotal = G.prop_tax[i] + saY + G.other_funds[i] + ov[y];
    var budgeted = R.adopted_budgeted_receipts[y] != null ? R.adopted_budgeted_receipts[y] : actual * R.budget_ratio;
    var fc;
    if (R.known_fc_years.indexOf(y) >= 0 || surplus[y - 2] == null)
      fc = R.adopted_fc[y] != null ? R.adopted_fc[y] : R.town_fc[y];
    else fc = R.appropriated_share * surplus[y - 2];
    var total = baseTotal + budgeted + fc;
    fcBy[y] = fc;
    // net revenue for the capital policy: less excluded debt, free cash and any further override
    netRev[y] = total - G.debt_excl[i] - fc - ov[y] - K.non_approp_fy27 * Math.pow(1 + K.non_approp_growth, y - 2027);
    // the other surplus is measured on Schedule A revenues: actual receipts, no free cash
    surplus[y] = (actual - budgeted) + R.other_surplus_share * (baseTotal + actual);
    if (y < Y0) return;
    rev.push(total - G.debt_excl[i]);
    parts.property_tax.push(G.prop_tax[i] - G.debt_excl[i]);
    parts.state_aid.push(saY); parts.local_receipts.push(budgeted); parts.free_cash.push(fc);
    parts.other_funds.push(G.other_funds[i]); parts.override.push(ov[y]);
  });


  var townFte = K.town_fte;
  var nes = D.enrollment.nesdec, enroll = {};
  Y.forEach(function (y) {
    enroll[y] = a.enroll_mode === "cm" ? D.enrollment.cm[y] : nes[y];
  });
  var e0 = enroll[Y0];
  if (a.enroll_mode === "flat") Y.forEach(function (y) { if (y > Y0) enroll[y] = e0; });
  var extra = {}, E = {};
  Y.forEach(function (y) {
    extra[y] = Math.max(units[y] - unitsT[y], 0) * K.students_per_home
      + K.chca_units * ramp[y] * K.chca_students_per_unit;
    E[y] = enroll[y] + extra[y];
  });
  var staff0 = K.staff26 + A.school_fte_change, ratio0 = e0 / staff0, v = K.school_variable_share;
  var staff = {};
  Y.forEach(function (y) {
    var ratio = ratio0;
    if (a.ratio_mode === "partial") {
      var target = ratio0 + (K.ratio_fy2019 - ratio0) / 3;
      ratio = ratio0 + (target - ratio0) * Math.min(Math.max((y - Y0) / 5, 0), 1);
    }
    // fill_capacity (keep mode): students from growth fill seats freed by the decline;
    // staff are added only once total enrollment is back above FY2027
    var sv = a.fill_capacity && a.ratio_mode === "keep" ? staff0 + Math.max(E[y] - e0, 0) / ratio0
      : a.ratio_mode === "keep" ? staff0 + extra[y] / ratio0
      // with "half", half the decline's seats stay open; growth's students are staffed beyond them
      : a.fill_capacity && a.ratio_mode === "half" ? staff0 + (0.5 / v) * Math.min(enroll[y] - e0, 0) / ratio0
          + Math.max(enroll[y] - e0, 0) / ratio0 + Math.max(extra[y] - 0.5 * Math.max(e0 - enroll[y], 0), 0) / ratio0
      // "half": half as fast on the way down; a rise is staffed in full
      : a.ratio_mode === "half" ? staff0 + extra[y] / ratio0 + (0.5 / v) * Math.min(enroll[y] - e0, 0) / ratio0
          + Math.max(enroll[y] - e0, 0) / ratio0
      : E[y] / ratio;
    staff[y] = (staff0 * (1 - v) + v * sv) * Math.pow(1 + (a.school_staff_growth || 0), Math.max(y - Y0, 0));
  });
  // students from growth left unstaffed by fill_capacity cost the middle tier (open seat plus special
  // education, K.fill_seat_cost_fy27); the enrollment index already charges them non-personnel costs
  var unstaffed = {};
  Y.forEach(function (y) {
    unstaffed[y] = a.fill_capacity && a.ratio_mode === "keep" ? Math.max(Math.min(extra[y], e0 - enroll[y]), 0)
      : a.fill_capacity && a.ratio_mode === "half" ? Math.min(extra[y], 0.5 * Math.max(e0 - enroll[y], 0)) : 0;
  });
  var fillAdd = K.fill_seat_cost_fy27 - A.schools * (1 - K.school_personnel_share) * v / e0;
  var fteTot0 = townFte + staff0;
  var slip = a.pension_slip || 0, red = a.opeb_redirect, hold = a.opeb_hold !== false;
  // payroll of all staff, Town and schools, weighted by FY2027 pay (payroll-linked benefits after FY2031)
  var wTown = A.town_departments * K.pD, wSch = A.schools * K.school_personnel_share, payroll = {};
  Y.forEach(function (y) {
    if (y >= Y0) payroll[y] = (wTown * (K.psD * Wps[y] + (1 - K.psD) * Wdep[y])
                               + wSch * Wsch[y] * staff[y] / staff0) / (wTown + wSch);
  });
  // pensions after FY2031: the normal cost at pay + the actuary's premium; a slip pays FY2030's
  // catch-up in slip + 1 level installments, the rest of the set-aside going to retiree health
  var ncG = a.pay + K.pension_nc_premium;
  function penPlan(y) { return y <= 2031 ? TS.pensions[y] : TS.pensions[2031] * Math.pow(1 + ncG, y - 2031); }
  var nc30 = TS.pensions[2031] / (1 + ncG), slipPay = 0;
  if (slip) {
    var ann = 0;
    for (var k = 0; k <= slip; k++) ann += Math.pow(1 + K.pension_rate, -k);
    slipPay = (TS.pensions[2030] - nc30) / ann;
  }

  var out = { years: [], lines: {} };
  var keys = ["departmental_base", "departmental_growth", "schools", "group_health",
              "growth_staff_benefits", "pensions", "opeb", "other_benefits", "debt_within_levy",
              "other_nondept"];
  keys.forEach(function (k) { out.lines[k] = []; });
  var oTol, oA, oSc, oB;   // retiree health liability state
  out.enrollment = []; out.school_staff = []; out.units = []; out.fire_company = []; out.homes_total = [];

  Y.forEach(function (y) {
    if (y < Y0) return;
    var payMix = K.psD * Wps[y] + (1 - K.psD) * Wdep[y];
    var depBase = A.town_departments * (K.pD * payMix + (1 - K.pD) * C[y]);
    var emp = sqft[y] / K.sqft_per_emp + K.chca_employees * ramp[y];
    var homes = units[y] + K.chca_units * ramp[y];
    var depGrowth = (homes * perHome + emp * K.cost_per_emp_fy25) * w25 * W[y];
    // planning and permitting staff, in proportion to real-estate new growth above the trend
    if (y > Y0) depGrowth += K.permitting_cost_fy27 * Math.max(G.re_ng[Y.indexOf(y)] / Gt.re_ng[Y.indexOf(y)] - 1, 0) * W[y];
    // a fire company once homes reach the threshold (its cost already carries health insurance,
    // so no benefit loading), and police and fire restored to earlier staffing
    var company = fireStep && y > Y0 && stock[y] >= K.fire_company_homes ? K.fire_company_cost_fy25 * ps25 * Wps[y] : 0;
    var restore = y > Y0 ? restoreN * K.ps_position_cost_fy25 * ps25 * Wps[y] : 0;
    // commitments already agreed: the fire contract's new steps from FY2028, and four police
    // positions refilled in FY2028-29 (already counted when staffing is restored)
    if (y >= 2028) restore += K.fire_steps_fy28 * Wps[y] / Wps[2028];
    if (!a.ps_restore) restore += (K.police_refill[Math.min(y, 2029)] || 0) * K.ps_position_cost_fy25 * ps25 * Wps[y];
    // police kept at the peer ratio, one officer at a time (health included)
    var policeN = policeStep && y > Y0 ? Math.max(Math.floor(stock[y] * K.police_peer_per_1000 / 1000 + 1e-9) - K.police_budget_fy27
      - (K.police_refill[Math.min(y, 2029)] || 0), 0) : 0;
    var police = policeN * K.ps_position_cost_fy25 * ps25 * Wps[y];
    depBase += restore;
    depGrowth += company + police;
    var SPS = K.school_personnel_share;
    var sch = A.schools * (SPS * Wsch[y] * staff[y] / staff0
                           + (1 - SPS) * Cnp[y] * ((1 - v) + v * E[y] / e0))
      + unstaffed[y] * fillAdd * Wsch[y] / Wsch[Y0];
    var fteTot = townFte + staff[y];
    var subs = (1 - K.retiree_cost_share) * fteTot / fteTot0 + K.retiree_cost_share * Math.pow(1 + K.retiree_growth, y - Y0);
    var gh = A.group_health * subs * prem[y];
    var gb = (depGrowth - company - police) * K.benefit_loading;
    var pen = y === Y0 ? A.pensions : penPlan(y);
    var opeb;
    if (y === Y0) opeb = A.opeb;
    else if (y <= 2030 || (y === 2031 && red)) opeb = TS.opeb[Math.min(y, 2031)];
    else if (red) opeb = TS.opeb[2031];
    else opeb = TS.opeb[2030] + 0.25e6 * (y - 2030);
    if (slip && y >= 2030 && y <= 2030 + slip) {
      var penSlip = (y === 2030 ? nc30 : penPlan(y)) + slipPay;
      if (red) opeb += pen - penSlip;
      pen = penSlip;
    }
    // retiree health liability, rolled forward from the FY2024 audit; the deposit stops once paid off
    if (y === Y0) { oTol = K.opeb_start[0]; oA = K.opeb_start[1]; oSc = K.opeb_start[2]; oB = K.opeb_start[3]; }
    else if (y > Y0) {
      // on the actuary's healthcare trend, not the premium settings
      var gmO = K.opeb_trend[y] != null ? K.opeb_trend[y] : K.opeb_trend_long;
      oSc *= 1 + gmO;
      oB *= (1 + gmO) * (1 + K.retiree_growth);
      oTol = oTol * (1 + K.opeb_rate) + oSc - oB;
      var oDep = Math.min(opeb, Math.max(oTol - oA * (1 + K.opeb_rate), 0));
      oA = Math.min(oA * (1 + K.opeb_rate) + oDep, oTol);   // held at the liability once paid off
      // what the payoff frees is a decision, not room: the base case keeps the planned deposit
      if (!(hold && red)) opeb = oDep;
    }
    var ob;
    if (y === Y0) ob = A.other_benefits;
    else if (y <= 2031) ob = TS.other_benefits[y];
    else ob = TS.other_benefits[2031] * payroll[y] / payroll[2031];
    var debt = y === Y0 ? A.within_levy_debt
      : (y <= 2032 ? TS.debt[y] : TS.debt[2032] * Math.pow(1.035, y - 2032));
    var other = y === Y0 ? A.other_nondept : TS.other_nondept[y];
    // the non-departmental lines by Town policy: the reserve fund at 1% of the prior year's net
    // revenue; from FY2032 general non-departmental with net revenue, non-appropriated at 2.38%
    if (y > Y0) {
      other += K.reserve_fund_share * netRev[y - 1] - TS.reserve_fund[Math.min(y, 2031)];
      if (y > 2031) {
        other += K.nondept_general_fy31 * (netRev[y - 1] / netRev[2030] - 1)
               + K.non_approp_fy31 * (Math.pow(1 + K.non_approp_growth, y - 2031) - 1);
      }
      // free cash by Town policy: never the operating budget. What is left after the uses already
      // counted goes to capital and one-time uses; a shortfall trims capital
      if (a.free_cash_policy !== false) {
        var gen = y <= 2031 ? TS.nondept_general[y] : K.nondept_general_fy31 * netRev[y - 1] / netRev[2030];
        other += fcBy[y] - (TS.cip_freecash[y] + K.fc_deposit_share * gen + K.fc_reserve_share * netRev[y - 1]);
      }
    }
    // capital at the 6.6% policy from revenue (the base case); off, the Town's table's dollars
    if (a.capital_full && y > Y0) {
      other += Math.max(K.cip_policy_share * netRev[y - 1] - debt - TS.cip_revfin[y], 0);
    }
    var vals = [depBase, depGrowth, sch, gh, gb, pen, opeb, ob, debt, other];
    keys.forEach(function (k, j) { out.lines[k].push(vals[j]); });
    out.years.push(y);
    out.enrollment.push(E[y]); out.school_staff.push(staff[y]); out.units.push(homes);
    out.fire_company.push(company); out.homes_total.push(stock[y]);
  });

  out.revenue = rev;
  out.revenue_parts = parts;
  out.spending = out.years.map(function (_, j) {
    return keys.reduce(function (s, k) { return s + out.lines[k][j]; }, 0);
  });
  out.room = out.years.map(function (_, j) { return rev[j] - out.spending[j]; });
  return out;
}

if (typeof module !== "undefined") module.exports = { runModel: runModel };
