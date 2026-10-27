"""
Data for the interactive forecast dashboard (docs/forecast_dashboard.html).

The dashboard runs the driver forecast in the browser (docs/_build/dashboard_engine.js),
a line-for-line port of expense_driver_forecast.run() plus the revenue side of
new_growth_scenario_forecast.main() and the free-cash cycle (revenue_cash_cycle.apply).
This script exports what that port needs and the Python results it must reproduce.

Outputs:
  output/dashboard_data.json    inputs for the engine
  output/dashboard_tests.json   Python results for the base case, every "What Decides
                                FY2040" dial, growth-grid points and revenue-rate changes;
                                scripts/test_dashboard_engine.js checks the port against them

New growth in the dashboard is a slider over a precomputed grid: the total new-growth
rate (share of the prior year's levy) from 0.6 point below the recent trend (1.277%) to
1.3 points above it, in 0.1-point steps, for four ways of adding growth above trend:
  today's mix   every category scaled up together
  housing-led   the added growth all from new homes
  commercial    the added growth all from new commercial space
  even split    half each (the peer-target "balanced mix" rule)
Below trend every category is scaled down together, whatever the mix. Each grid point is
a full run of new_growth_scenario_forecast (property tax, permits, meals tax, CHCA) for
each Chestnut Hill case, so the slider shows the model's own numbers, not an interpolation.

Run from `scripts/`:  python3 export_dashboard_data.py
"""

import contextlib
import io
import json
from pathlib import Path

import expense_driver_forecast as edf
import fy2027_adopted as A
import new_growth_scenario_forecast as ngs
import revenue_cash_cycle as rcc

ROOT = Path(__file__).parent.parent
OUT_DATA = ROOT / "output" / "dashboard_data.json"
OUT_TESTS = ROOT / "output" / "dashboard_tests.json"
YEARS = edf.YEARS                       # 2026-2040
SHOW = [y for y in YEARS if y >= 2027]  # the dashboard starts at the adopted FY2027 budget

TREND = (ngs.TREND_RES_NEW_PCT, ngs.TREND_RES_RENO_PCT, ngs.TREND_COM_NEW_PCT,
         ngs.TREND_COM_RENO_PCT, ngs.TREND_COM_PP_PCT)
T = sum(TREND)
STEPS = list(range(-6, 14))             # T - 0.6 pt ... T + 1.3 pt
MIXES = ("mix", "housing", "commercial", "even")


def grid_params(mix, k):
    r = T + k * 0.001
    if k <= 0 or mix == "mix":
        return tuple(p * r / T for p in TREND)
    add = r - T
    rn, rr, cn, cr, pp = TREND
    if mix == "housing":
        return (rn + add, rr, cn, cr, pp)
    if mix == "commercial":
        return (rn, rr, cn + add, cr, pp)
    return (rn + add / 2, rr, cn + add / 2, cr, pp)


def gname(mix, k):
    return f"grid_{mix}_{k:+d}"


GRID = {gname(m, k): {"params": grid_params(m, k), "label": f"dashboard grid {m} {k:+d}"}
        for m in MIXES for k in STEPS}
# the new-homes switch: every grid point again with the new-homes part at half and at none
# (step 0 is the named trend_homes_* scenarios)
GRID.update({f"{gname(m, k)}_homes_{h}": {"params": ngs.homes_params(grid_params(m, k), share),
                                         "label": f"dashboard grid {m} {k:+d}, new homes {h}"}
             for h, share in ngs.HOMES_BUILT.items() for m in MIXES for k in STEPS
             if k > 0 or (k < 0 and m == "mix")})
NAMED = ("trend_continues", "peer_target_residential_led", "peer_target_commercial_led",
         "peer_target_balanced_mix", "trend_homes_half", "trend_homes_none")


def revenue_runs(chca):
    """Run the revenue model for every grid scenario under one CHCA case, capturing the
    inputs to the free-cash cycle so the browser can re-run it with other rates."""
    captured = []
    real_apply = rcc.apply

    def spy(years, actual, town_fc, base_total):
        captured.append(dict(actual=dict(actual), town_fc=dict(town_fc), base_total=dict(base_total)))
        return real_apply(years, actual, town_fc, base_total)

    rcc.apply = spy
    try:
        edf._GROWTH_CACHE.pop(chca, None)
        frame = edf.chca_growth_frame(chca)
    finally:
        rcc.apply = real_apply
    names = list(dict.fromkeys(frame.scenario))
    assert len(names) == len(captured), (len(names), len(captured))
    return frame, dict(zip(names, captured))


def main():
    ngs.EXTRA_SCENARIOS = GRID
    hist = ngs.read_historical()
    # flat investment income rides in lr_rest (actual less the growing residual)
    lr_resid_2025, lr_cagr = ngs.local_receipts_residual(hist)
    sa_2025 = float(hist[2025]["recap_state_aid"])
    sa_cagr = ngs.STATE_AID_GROWTH
    sa_known = ngs.state_aid_path(ngs.read_town_forecast(), [2026, 2027])

    growth = {}
    worst = 0.0
    for chca in ("approved", "cr_avg", "rkg", "in_trend"):
        frame, cap = revenue_runs(chca)
        growth[chca] = {}
        for name in list(GRID) + list(NAMED):
            g = frame[frame.scenario == name].set_index("fiscal_year")
            c = cap[name]
            resid = {y: lr_resid_2025 * (1 + lr_cagr) ** (y - 2025) for y in YEARS}
            sa = {y: sa_known[y] if y in sa_known else sa_known[2027] * (1 + sa_cagr) ** (y - 2027) for y in YEARS}
            # control: state aid as the browser rebuilds it equals the model's
            worst = max(worst, max(abs(sa[y] - g.loc[y, "state_aid"]) for y in YEARS))
            growth[chca][name] = dict(
                # property tax incl. excluded debt; state aid and other funds sit in base_total
                prop_tax=[float(g.loc[y, "property_taxes"]) for y in YEARS],
                debt_excl=[float(g.loc[y, "debt_exclusion_revenue"]) for y in YEARS],
                other_funds=[float(g.loc[y, "other_available_funds"]) for y in YEARS],
                # net revenue as the capital policy defines it (total less excluded debt and free cash)
                net_rev=[float(g.loc[y, "total_revenue"] - g.loc[y, "debt_exclusion_revenue"] - g.loc[y, "free_cash"])
                         for y in YEARS],
                lr_rest=[c["actual"][y] - resid[y] for y in YEARS],
                units=[float(g.loc[y, "implied_res_new_units"]) for y in YEARS],
                sqft=[float(g.loc[y, "implied_com_new_sqft"]) for y in YEARS],
                re_ng=[float(g.loc[y, ["new_growth_res_new_dollars", "new_growth_res_reno_dollars",
                                       "new_growth_com_new_dollars", "new_growth_com_reno_dollars"]].sum())
                       for y in YEARS],
                total_revenue=[float(g.loc[y, "total_revenue"]) for y in YEARS],
            )
            if name == "trend_continues":
                town_fc = {y: c["town_fc"][y] for y in rcc.KNOWN_FREE_CASH_YEARS}
    assert worst < 1, f"state aid rebuild off by ${worst:,.0f}"

    data = edf.load()
    tsch, be, bc, gr, fte, hist_e, sal = data
    T_ = lambda cat, sub, y: float(tsch[y][(cat, sub)])
    ob_town = lambda y: T_("benefits_detail", "total", y) - sum(
        T_("benefits_detail", s, y) for s in ("pensions", "group_health", "retiree_group_health_opeb"))
    cats = [("General Government", "exp_general_government"), ("Public Safety", "exp_public_safety"),
            ("Public Works", "exp_public_works"), ("Human Services", "exp_human_services"),
            ("Culture & Recreation", "exp_culture_recreation")]
    pers = {c: hist_e.loc[2025, col] * sal.loc[c, "salary_budget_fy19"] / hist_e.loc[2019, col]
            for c, col in cats}
    dep25 = sum(hist_e.loc[2025, col] for _, col in cats)

    nesdec = edf.enrollment_path()
    sc = edf.ACTUAL_OCT_2026 / edf.CM_PK12[2027]
    cm = {y: (edf.ACTUAL_OCT_2025 if y == 2026 else edf.CM_PK12[min(y, 2034)] * sc) for y in YEARS}
    # NESDEC as published (before the births update), scaled to the Sept 2026 count like the others; ends FY2034
    sn = edf.ACTUAL_OCT_2026 / edf.NESDEC_PK12_PUBLISHED[2027]
    nesdec_pub = {y: edf.NESDEC_PK12_PUBLISHED[y] * sn for y in YEARS if 2027 <= y <= 2034}
    staff26 = edf.SCHOOL_STAFF_FY26
    tsched = lambda f: {str(y): f(y) for y in range(2028, 2032)}

    out = dict(
        years=YEARS, show_from=2027,
        base=edf.BASE,
        trend_rate=T, peer_rate=ngs.PEER_TARGET_PCT, steps=STEPS, mixes=list(MIXES),
        revenue=dict(sa_2025=sa_2025, sa_2026=sa_known[2026], sa_2027=sa_known[2027], sa_cagr=sa_cagr, lr_resid_2025=lr_resid_2025, lr_cagr=lr_cagr,
                     budget_ratio=rcc.BUDGET_RATIO, other_surplus_share=rcc.OTHER_SURPLUS_SHARE,
                     appropriated_share=rcc.APPROPRIATED_SHARE,
                     known_fc_years=list(rcc.KNOWN_FREE_CASH_YEARS),
                     town_fc={str(k): v for k, v in town_fc.items()},
                     adopted_fc={str(k): v for k, v in rcc.ADOPTED_FREE_CASH.items()},
                     adopted_budgeted_receipts={str(k): v for k, v in rcc.ADOPTED_BUDGETED_RECEIPTS.items()}),
        growth=growth,
        adopted=dict(town_departments=A.TOWN_DEPARTMENTS, schools=A.SCHOOLS, group_health=A.GROUP_HEALTH,
                     pensions=A.PENSIONS, opeb=A.OPEB, other_benefits=A.OTHER_BENEFITS,
                     within_levy_debt=A.WITHIN_LEVY_DEBT, other_nondept=A.OTHER_NONDEPT,
                     school_fte_change=A.SCHOOL_FTE_CHANGE_FROM_FY26),
        town=dict(pensions=tsched(lambda y: T_("benefits_detail", "pensions", y)),
                  opeb=tsched(lambda y: T_("benefits_detail", "retiree_group_health_opeb", y)),
                  other_benefits=tsched(ob_town),
                  # debt within the levy: the capital funding table, FY2027 Financial Plan p.384
                  debt={str(y): float(be.loc[y, "debt_service_regular"]) for y in range(2028, 2033)},
                  other_nondept={str(y): float(be.loc[y, "other_nondept"]) for y in YEARS if y >= 2028},
                  cip_revfin={str(y): float(be.loc[y, "cip_revenue_financed"]) for y in YEARS if y >= 2028},
                  reserve_fund={str(y): T_("expenditure", "nondept_reserve_fund", y) for y in range(2028, 2032)},
                  nondept_general={str(y): T_("expenditure", "nondept_general", y) for y in range(2028, 2032)},
                  cip_freecash={str(y): float(be.loc[y, "cip_free_cash"]) for y in YEARS if y >= 2028}),
        consts=dict(pD=sum(pers.values()) / dep25, psD=pers["Public Safety"] / sum(pers.values()),
                    town_fte=float(fte.loc[2027, "total"]), staff26=staff26,
                    school_personnel_share=edf.SCHOOL_PERSONNEL_SHARE,
                    school_variable_share=edf.SCHOOL_VARIABLE_SHARE, ratio_fy2019=edf.RATIO_FY2019,
                    students_per_home=edf.STUDENTS_PER_HOME, chca_units=edf.CHCA_UNITS,
                    chca_students_per_unit=edf.CHCA_STUDENTS_PER_UNIT, chca_employees=edf.CHCA_EMPLOYEES,
                    sqft_per_emp=edf.SQFT_PER_EMP, cost_per_emp_fy25=edf.RKG_COM_DEPT_PER_EMP_FY25,
                    benefit_loading=edf.TOWN_BENEFIT_LOADING, anchor=edf.ANCHOR_YEAR,
                    permitting_cost_fy27=edf.PERMITTING_COST_FY27, cip_policy_share=edf.CIP_POLICY_SHARE,
                    non_approp_fy27=edf.NON_APPROP_FY27, non_approp_growth=edf.NON_APPROP_GROWTH,
                    fire_steps_fy28=edf.FIRE_STEPS_FY28,
                    opeb_start=list(edf.OPEB_START), opeb_rate=edf.OPEB_RATE,
                    opeb_trend={str(k): v for k, v in edf.OPEB_TREND.items()}, opeb_trend_long=edf.OPEB_TREND_LONG,
                    retiree_cost_share=edf.HEALTH_RETIREE_COST_SHARE, retiree_growth=edf.RETIREE_GROWTH,
                    police_refill={str(k): v for k, v in edf.POLICE_REFILL.items()},
                    reserve_fund_share=edf.RESERVE_FUND_SHARE, fc_deposit_share=edf.FC_DEPOSIT_SHARE,
                    fc_reserve_share=edf.FC_RESERVE_SHARE, nondept_general_fy31=edf.NONDEPT_GENERAL_FY31,
                    non_approp_fy31=edf.NON_APPROP_FY31,
                    pension_nc_premium=edf.PENSION_NC_PREMIUM, pension_rate=edf.PENSION_RATE,
                    homes_fy2025=edf.HOMES_FY2025, fire_company_homes=edf.FIRE_COMPANY_HOMES,
                    fire_company_cost_fy25=edf.FIRE_COMPANY_COST_FY25, ps_share=edf.TOWN_COST_PER_HOME_PS_SHARE,
                    ps_position_cost_fy25=edf.PS_POSITION_COST_FY25,
                    ps_restore_positions=sum(edf.PS_RESTORE_POSITIONS.values()),
                    ps_share_police=edf.PS_SHARE_POLICE, police_budget_fy27=edf.POLICE_BUDGET_FY27,
                    police_peer_per_1000=edf.POLICE_PEER_PER_1000_HOMES),
        chca_ramp={str(y): ngs.chca_ramp_share(y) for y in YEARS},
        enrollment=dict(nesdec={str(y): nesdec[y] for y in YEARS}, cm={str(y): cm[y] for y in YEARS},
                        nesdec_published={str(y): v for y, v in nesdec_pub.items()}),
    )
    OUT_DATA.write_text(json.dumps(out, separators=(",", ":")))

    # ---------------------------------------------------------------- tests
    lines = ["departmental_base", "departmental_growth", "schools", "group_health", "growth_staff_benefits",
             "pensions", "opeb", "other_benefits", "debt_within_levy", "other_nondept"]

    def result(a):
        with contextlib.redirect_stdout(io.StringIO()):
            df = edf.run(a, data, None)
        return {c: [float(df.loc[y, c]) for y in SHOW]
                for c in lines + ["operating_expenditure", "operating_revenue", "surplus_deficit"]}

    cases = [("base", {}, {})]
    import re
    src = Path(edf.__file__).read_text()
    block = src[src.index("    dials = ["):]
    block = block[:block.index("\n    ]")]
    dials = re.findall(r'\("([^"]+)", (dict\([^)]*\))\)', block)
    for label, d in dials:
        cases.append((label, eval(d), {}))
    for k in (-6, -3, 4, 13):
        for m in MIXES:
            cases.append((f"grid {m} {k:+d}", dict(growth=gname(m, k)), {}))
    cases.append(("grid housing +7, CHCA RKG", dict(growth=gname("housing", 7), chca="rkg"), {}))
    cases.append(("grid housing +13, students fill seats", dict(growth=gname("housing", 13), fill_capacity=True), {}))
    cases.append(("grid even +3, students fill seats, CHCA RKG", dict(growth=gname("even", 3), fill_capacity=True, chca="rkg"), {}))
    cases.append(("combo: pay 4%, premiums 10%, staff follow", dict(pay=0.04, premium_long=0.10, ratio_mode="hold"), {}))
    cases.append(("grid housing +7, police grow with homes", dict(growth=gname("housing", 7), police_step=True), {}))
    # revenue-rate changes: patch the CAGRs the revenue model computes
    cases.append(("state aid 1%/yr", {}, dict(sa=0.01)))
    cases.append(("local receipts 5%/yr", {}, dict(lr=0.05)))
    cases.append(("state aid 4%, receipts 2%, growth even +5", dict(growth=gname("even", 5)), dict(sa=0.04, lr=0.02)))

    tests = []
    real_cagr = ngs.cagr
    for label, a_extra, rev in cases:
        if rev:
            def patched(start, end, years, rev=rev):
                if years == 6 and "lr" in rev:
                    return rev["lr"]
                return real_cagr(start, end, years)
            ngs.cagr = patched
            if "sa" in rev:
                ngs.STATE_AID_GROWTH = rev["sa"]
            edf._GROWTH_CACHE.clear()
        try:
            tests.append(dict(label=label, a=dict(edf.BASE, **a_extra), rev=rev, expect=result(dict(edf.BASE, **a_extra))))
        finally:
            if rev:
                ngs.cagr = real_cagr
                ngs.STATE_AID_GROWTH = sa_cagr
                edf._GROWTH_CACHE.clear()
    OUT_TESTS.write_text(json.dumps(dict(years=SHOW, tests=tests)))
    print(f"wrote {OUT_DATA.name} ({OUT_DATA.stat().st_size/1e3:,.0f} KB), {OUT_TESTS.name}: "
          f"{len(tests)} cases ({len(dials)} dials)")


if __name__ == "__main__":
    main()
