"""
Expense driver tree: where every dollar of FY2011-2025 General Fund expense
growth came from.

Phases A-C answered the question one bucket at a time and left three gaps: no
test of commercial space, no explanation of non-personnel spending, and pensions
and OPEB set aside. This script closes those and puts every Schedule A dollar of
growth into one of nine driver groups, so the pieces add up to the whole.

## The window

FY2011-FY2025. FY2011 is the first clean year after the FY2010 Schedule A
reclassification (Phase A); FY2025 is the last Schedule A year. The town FTE
series crosses the unvalidated FY2020/21 seam inside this window, and that is
reported beside the result rather than hidden.

## Blocks and how each is split

Town departmental (five Schedule A categories), per category, Phase B's
counterfactual in dollars rather than rates:

    price     = S0 x p x (ECI1/ECI0 - 1) + S0 x (1-p) x (CPI1/CPI0 - 1)
    headcount = S0 x p x (ECI1/ECI0) x (FTE1/FTE0 - 1)
    residual  = S1 - S0 - price - headcount

  Headcount is then split into demand from new homes and commercial space, at
  RKG's rates ($1,371/home, $219/commercial employee), which Phase C found
  consistent with the best-measured observed staffing response, and everything
  else, which is service-level change.

Schools (Schedule A education), the same identity against total school staff:

    price     = S0 x (ECI1/ECI0 - 1)
    staffing  = S0 x (ECI1/ECI0) x (STAFF1/STAFF0 - 1)
       of which enrollment    = S0 x (ECI1/ECI0) x (ENR1/ENR0 - 1)
          of which new homes  = homes x students-per-home / ENR0 share of that
       of which staff ratio   = staffing - enrollment
    residual  = S1 - S0 - price - staffing

Fixed costs (Schedule A), from the Town's Personnel Benefits Detailed actuals:

  Group health: premium price at the national public-sector benefits index,
    covered headcount at total town+school FTE, residual. The headcount part is
    allocated across driver groups in proportion to where the FTE came from.
  Pensions: split into employer normal cost (the cost of pensions being earned
    now, from the 2024 actuarial valuation) and amortization of the unfunded
    liability (paying for pensions already earned, i.e. legacy). The FY2011
    normal cost is ESTIMATED by deflating the FY2025 figure by wage inflation
    and town headcount; no FY2011 valuation is in the repo.
  OPEB: transfers into the retiree health trust, a funding-policy choice.
  Other benefits: Medicare tax, workers' comp, IOD, etc., as one line.
  Reconciling: Schedule A fixed costs minus the benefits detail total.

Debt service: excluded (voter-approved, above the levy limit) against
within-levy, using the debt-exclusion levy amount.

Intergovernmental assessments: state, county and MBTA, outside local control.

## Controls (printed)

  1. The nine groups sum to the Schedule A total change exactly.
  2. Each block sums to its own Schedule A change exactly.
  3. The departmental function reproduces Phase B's FY2011-2020 predicted spend
     for every category to the dollar.
  4. A synthetic category grown exactly at the indices returns a zero residual,
     and one given a known excess returns that excess.

Run from `scripts/`:  python3 expense_drivers_tree.py
"""

import csv
from pathlib import Path

from expense_drivers_phase_a import CATEGORIES, build_fte_panel, fnum
from expense_drivers_phase_b import fy_index, load_indices

ROOT = Path(__file__).parent.parent
OUT = ROOT / "output"

HIST_FILE = OUT / "brookline_historical_financials_fy05_25.csv"
SALARY_FILE = OUT / "department_fte_salary_by_category_fy19_fy26.csv"
SCHOOL_FILE = OUT / "school_enrollment_staffing_fy05_25.csv"
PHASE_B_FILE = OUT / "expense_drivers_phase_b_attribution.csv"

OUT_CSV = OUT / "expense_drivers_tree_fy11_25.csv"
NONPERS_CSV = OUT / "expense_drivers_object_class_fy11_24.csv"
METHOD_OUT = OUT / "expense_drivers_tree_methodology.md"

Y0, Y1 = 2011, 2025

# ---------------------------------------------------------------- sourced inputs
# Personnel Benefits Detailed, actuals. FY2011: FY2015 Financial Plan p. IV
# (table "NON-DEPARTMENTAL Personnel Benefits"). FY2025: FY2027 Financial Plan
# p.330. "other" is the named total minus the three named lines.
BENEFITS = {
    2011: dict(total=39_606_017, pensions=13_975_800, group_health=19_906_659,
               opeb=2_012_531),
    2025: dict(total=87_448_180, pensions=37_517_904, group_health=38_268_676,
               opeb=5_415_980),
}
# Employer normal cost for fiscal 2025, projected to July 1, 2024: Brookline
# Retirement System 2024 Actuarial Valuation, "Employer normal cost projected
# to July 1, 2024" ($7,307,785, 7.71% of payroll).
PENSION_NORMAL_COST_FY25 = 7_307_785
# Employer normal cost for fiscal 2013, projected to July 1, 2012: Brookline
# Retirement System 1/1/2014 Actuarial Valuation (Town DocumentCenter View/6540),
# prior-valuation column ($3,432,407, 5.48% of payroll). The nearest published
# figure to FY2011; carried back two years by wage inflation and town headcount.
PENSION_NORMAL_COST_FY13 = 3_432_407

# Object-class actuals, General Fund operating budget incl. schools.
# FY2011: FY2015 Financial Plan, "Totals by Expenditure Classification".
# FY2023: FY2025 Financial Plan, "Financial Plan by Expense Category".
# FY2024: FY2026 Financial Plan, same table. Budget columns are NOT used:
# the school budget is voted as one number and its budget-year allocation
# puts school non-personnel inside salaries, so only actuals are comparable.
OBJECT_CLASS = {
    2011: dict(personnel=106_005_128, services=17_296_084, supplies=4_064_542,
               other=764_487, utilities=4_988_427, capital=1_788_263),
    2023: dict(personnel=168_265_973, services=21_974_956, supplies=4_238_534,
               other=4_874_979, utilities=5_952_331, capital=1_515_902),
    2024: dict(personnel=177_757_334, services=26_969_021, supplies=3_871_930,
               other=2_821_649, utilities=5_701_380, capital=2_319_423),
}

# Growth quantities, FY2012-2025 (the fourteen new-growth years after FY2011).
# Homes: net new homes on the Town's building permits issued 2010-2024, without assisted living,
# each read and coded by hand (new_homes_parameters.py); they reach the roll about a year after the
# permit, so FY2011-2025. Replaces 1,638, Phase C's count implied from new-growth dollars, which the
# permits do not bear out (2026-10-12).
import json as _json
HOMES = round(_json.loads((Path(__file__).parent.parent / "output" / "new_homes_parameters.json").read_text())
              ["homes_permitted_2010_2024"])
RKG_PER_HOME = 1_371.0
RKG_PER_COM_EMPLOYEE = 219.0
# RKG's $1,371 includes $262 of "Other" (benefits, debt, insurance); the rest is
# department budgets (Police $448, Fire $532, GG $57, PW $48, Library $19, ...).
# ERSC Final Report Appendix C, March 2025. Benefits for added staff are counted
# separately in the tree, so only the department share is used here. The $219
# per commercial employee has the same department breakdown.
RKG_DEPT_SHARE = (1_371.0 - 262.0) / 1_371.0
SQFT_PER_EMPLOYEE = 200.0
COM_VALUE_PER_SQFT = 518.0     # new_growth_scenario_forecast.py
STUDENTS_PER_NEW_HOME = 0.2442  # marginal_expense_forecast.py, RKG tiers x Brookline mix
# FY2026 Classification Hearing, slide "FY2026 New Growth": of $68.58M
# non-residential new growth, commercial was $18.01M and personal property
# $50.57M. One year only; used as the central split, with the all-non-res
# figure as the upper bound.
COM_SHARE_OF_NONRES_NG_FY26 = 18_007_589 / (18_007_589 + 50_570_310)
# DOR new growth, Brookline, total minus residential value, FY2012-2025.
NONRES_NG_VALUE = {
    2012: 22_900_315, 2013: 18_395_660, 2014: 29_878_220, 2015: 35_948_066,
    2016: 30_048_747, 2017: 51_131_347, 2018: 38_140_470, 2019: 62_600_476,
    2020: 62_015_010, 2021: 98_407_020, 2022: 98_959_780, 2023: 47_864_008,
    2024: 51_973_982, 2025: 40_156_628,
}
FY26_COMMERCIAL_VALUE = 2_622_051_179  # same slide deck, total commercial class

GROUPS = [
    "Inflation",
    "New homes & commercial space",
    "Enrollment change (not from new homes)",
    "Staffing levels (service choices)",
    "Pay & costs above/below inflation",
    "Legacy pension paydown",
    "OPEB prefunding",
    "School & other buildings (debt)",
    "Other",
]


def ratio(idx, name, y0, y1):
    return fy_index(idx, name, y1) / fy_index(idx, name, y0)


def departmental(hist, panel, sal, E, C, y0, y1):
    """Per-category split. Returns {label: dict(s0, s1, price, head, resid,
    predicted, dfte)}."""
    out = {}
    for key, label, col in CATEGORIES:
        s0, s1 = fnum(hist[y0][col]), fnum(hist[y1][col])
        f0, f1 = panel[y0][key], panel[y1][key]
        p = float(sal[label]["salary_budget_fy19"]) / fnum(hist[2019][col])
        price = s0 * p * (E - 1) + s0 * (1 - p) * (C - 1)
        head = s0 * p * E * (f1 / f0 - 1)
        out[label] = dict(s0=s0, s1=s1, price=price, head=head,
                          resid=s1 - s0 - price - head,
                          predicted=s0 + price + head, dfte=f1 - f0)
    return out


def main():
    panel = build_fte_panel()
    idx = load_indices()
    with open(HIST_FILE) as f:
        hist = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    with open(SALARY_FILE) as f:
        sal = {r["category"]: r for r in csv.DictReader(f)}
    with open(SCHOOL_FILE) as f:
        sch = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}

    E = ratio(idx, "eci_total_comp", Y0, Y1)
    Ew = ratio(idx, "eci_wages", Y0, Y1)
    B = ratio(idx, "eci_benefits", Y0, Y1)
    C = ratio(idx, "cpi_boston", Y0, Y1)
    n = Y1 - Y0

    rows = []  # block, component, group, dollars, note

    def add(block, component, group, dollars, note=""):
        assert group in GROUPS, group
        rows.append(dict(block=block, component=component, group=group,
                         dollars=dollars, note=note))

    # ============================================================ CONTROLS
    print("=" * 78)
    print("CONTROLS")
    print("=" * 78)
    # (3) reproduce Phase B FY2011-2020
    with open(PHASE_B_FILE) as f:
        pb = [r for r in csv.DictReader(f)
              if r["fy_start"] == "2011" and r["fy_end"] == "2020"
              and r["bucket"] in {c[1] for c in CATEGORIES}]
    d20 = departmental(hist, panel, sal, ratio(idx, "eci_total_comp", 2011, 2020),
                       ratio(idx, "cpi_boston", 2011, 2020), 2011, 2020)
    worst = max(abs(d20[r["bucket"]]["predicted"] - float(r["predicted_spend_end"]))
                for r in pb)
    print(f"  {'PASS' if worst <= 1 and len(pb) == 5 else 'FAIL'}  departmental split "
          f"reproduces Phase B FY2011-20 predicted spend, 5 categories, worst gap "
          f"${worst:,.2f}")
    # (4) synthetic
    s0, p, f0, f1 = 1_000_000.0, 0.8, 100.0, 110.0
    s1 = s0 * p * (f1 / f0) * E + s0 * (1 - p) * C
    price = s0 * p * (E - 1) + s0 * (1 - p) * (C - 1)
    head = s0 * p * E * (f1 / f0 - 1)
    r0 = s1 - s0 - price - head
    print(f"  {'PASS' if abs(r0) < 1e-6 else 'FAIL'}  synthetic category grown exactly "
          f"at the indices returns residual ${r0:.2e}")
    s1b = s1 + 50_000
    r1 = s1b - s0 - price - head
    print(f"  {'PASS' if abs(r1 - 50_000) < 1e-6 else 'FAIL'}  a deliberate +$50,000 "
          f"excess is recovered as ${r1:,.2f}")
    print()
    print(f"  Indices FY{Y0}-FY{Y1}: public-sector compensation x{E:.4f} "
          f"({(E**(1/n)-1)*100:.2f}%/yr), wages x{Ew:.4f}, benefits x{B:.4f} "
          f"({(B**(1/n)-1)*100:.2f}%/yr), Boston CPI x{C:.4f} ({(C**(1/n)-1)*100:.2f}%/yr)")
    print()

    # ===================================================== growth quantities
    nonres = sum(NONRES_NG_VALUE.values())
    com_value_central = nonres * COM_SHARE_OF_NONRES_NG_FY26
    com_sqft_central = com_value_central / COM_VALUE_PER_SQFT
    com_sqft_upper = nonres / COM_VALUE_PER_SQFT
    com_emp_central = com_sqft_central / SQFT_PER_EMPLOYEE
    com_emp_upper = com_sqft_upper / SQFT_PER_EMPLOYEE
    com_cost_central = com_emp_central * RKG_PER_COM_EMPLOYEE
    com_cost_upper = com_emp_upper * RKG_PER_COM_EMPLOYEE
    com_stock_sqft = FY26_COMMERCIAL_VALUE / COM_VALUE_PER_SQFT
    home_cost = HOMES * RKG_PER_HOME
    new_home_students = HOMES * STUDENTS_PER_NEW_HOME

    print("=" * 78)
    print("GROWTH QUANTITIES, FY2012-2025")
    print("=" * 78)
    print(f"  New homes {HOMES:,}  -> RKG municipal cost ${home_cost:,.0f}/yr, "
          f"{new_home_students:,.0f} students at {STUDENTS_PER_NEW_HOME}/home")
    print(f"  Non-residential new growth value ${nonres/1e6:,.1f}M, of which commercial "
          f"(FY26 share {COM_SHARE_OF_NONRES_NG_FY26:.0%}) ${com_value_central/1e6:,.1f}M")
    print(f"  Commercial space added: ~{com_sqft_central:,.0f} sqft central, "
          f"{com_sqft_upper:,.0f} upper bound; stock today ~{com_stock_sqft:,.0f} sqft")
    print(f"  Commercial employees ~{com_emp_central:,.0f} central / {com_emp_upper:,.0f} "
          f"upper -> ${com_cost_central:,.0f} / ${com_cost_upper:,.0f} per yr")
    print()

    # ========================================================= DEPARTMENTAL
    dep = departmental(hist, panel, sal, E, C, Y0, Y1)
    dep_price = sum(d["price"] for d in dep.values())
    dep_head = sum(d["head"] for d in dep.values())
    dep_resid = sum(d["resid"] for d in dep.values())
    dep_change = sum(d["s1"] - d["s0"] for d in dep.values())
    town_dfte = sum(d["dfte"] for d in dep.values())
    growth_town = (home_cost + com_cost_central) * RKG_DEPT_SHARE
    add("Town departments", "Wage & price inflation", "Inflation", dep_price,
        "personnel at national state/local ECI, non-personnel at Boston CPI")
    add("Town departments", "Staff to serve new homes & commercial space",
        "New homes & commercial space", growth_town,
        f"{HOMES:,} homes x ${RKG_PER_HOME:,.0f} + {com_emp_central:,.0f} commercial "
        f"employees x ${RKG_PER_COM_EMPLOYEE:.0f} (RKG), department share "
        f"{RKG_DEPT_SHARE:.0%}; benefits counted under Benefits")
    add("Town departments", "Other staffing change", "Staffing levels (service choices)",
        dep_head - growth_town,
        f"town FTE {town_dfte:+.1f} in total; +18.5 of it at the unvalidated FY2020/21 seam")
    add("Town departments", "Cost per head above/below inflation",
        "Pay & costs above/below inflation", dep_resid,
        "residual: step/grade, turnover, role mix, local pay vs national")
    # FTE attributable to growth, for allocating group health headcount
    avg_cost_per_fte = dep_head / town_dfte
    town_growth_fte = growth_town / avg_cost_per_fte

    print("=" * 78)
    print(f"TOWN DEPARTMENTS  ${dep_change/1e6:+.2f}M")
    print("=" * 78)
    print(f"  {'category':22s}{'change':>10}{'price':>10}{'heads':>10}{'resid':>10}{'dFTE':>8}")
    for label, d in dep.items():
        print(f"  {label:22s}{(d['s1']-d['s0'])/1e6:>9.2f}M{d['price']/1e6:>9.2f}M"
              f"{d['head']/1e6:>9.2f}M{d['resid']/1e6:>9.2f}M{d['dfte']:>+8.1f}")
    print(f"  growth-driven share of headcount $: {growth_town/dep_head:.0%} "
          f"(~{town_growth_fte:.1f} of {town_dfte:+.1f} FTE)")
    print()

    # ============================================================ SCHOOLS
    s0, s1 = fnum(hist[Y0]["exp_education"]), fnum(hist[Y1]["exp_education"])
    st0, st1 = fnum(sch[Y0]["total_staff_fte"]), fnum(sch[Y1]["total_staff_fte"])
    en0, en1 = fnum(sch[Y0]["total_enrollment"]), fnum(sch[Y1]["total_enrollment"])
    # School personnel share, FY2011: total General Fund personnel (object-class
    # actuals, town + schools) minus town-department personnel (Schedule A x the
    # FY2019 salary shares used above), over school spending. DERIVED, not
    # published; FY2024 on the same basis gives about 83%.
    town_pers0 = sum(d["s0"] * float(sal[lab]["salary_budget_fy19"]) /
                     fnum(hist[2019][col])
                     for (key, lab, col), d in zip(CATEGORIES, dep.values()))
    ps = (OBJECT_CLASS[Y0]["personnel"] - town_pers0) / s0
    sch_price = s0 * ps * (E - 1) + s0 * (1 - ps) * (C - 1)
    sch_staff = s0 * ps * E * (st1 / st0 - 1)
    sch_enroll = s0 * ps * E * (en1 / en0 - 1)
    sch_newhome = s0 * ps * E * (new_home_students / en0)
    cost_per_school_staff = s0 * ps * E / st0
    sch_ratio = sch_staff - sch_enroll
    sch_resid = s1 - s0 - sch_price - sch_staff
    add("Schools", "Wage & price inflation", "Inflation", sch_price,
        f"personnel ({ps:.0%}, derived) at the ECI, non-personnel at Boston CPI")
    add("Schools", "Staff for students from new homes", "New homes & commercial space",
        sch_newhome, f"{new_home_students:,.0f} students at {STUDENTS_PER_NEW_HOME}/home, "
        "at the FY2011 staff ratio")
    add("Schools", "Staff for other enrollment change",
        "Enrollment change (not from new homes)", sch_enroll - sch_newhome,
        f"net enrollment {en0:,.0f} -> {en1:,.0f}; peaked at 7,855 in FY2019")
    add("Schools", "Lower students-per-staff ratio", "Staffing levels (service choices)",
        sch_ratio, f"students per staff FTE {en0/st0:.2f} -> {en1/st1:.2f}")
    add("Schools", "Cost per staff above/below inflation",
        "Pay & costs above/below inflation", sch_resid, "residual")
    # FTE shares for group-health allocation
    sch_newhome_fte = st0 * new_home_students / en0
    sch_enroll_fte = st0 * (en1 / en0 - 1)
    sch_ratio_fte = (st1 - st0) - sch_enroll_fte
    # Where the ratio change happened: during the enrollment rise (to the FY2019
    # peak) or after it, when staff fell more slowly than students.
    en_pk, st_pk = fnum(sch[2019]["total_enrollment"]), fnum(sch[2019]["total_staff_fte"])
    ratio_rise = st_pk - st0 * en_pk / en0
    ratio_after = st1 - st_pk * en1 / en_pk

    print("=" * 78)
    print(f"SCHOOLS  ${(s1-s0)/1e6:+.2f}M")
    print("=" * 78)
    print(f"  personnel share {ps:.1%} (derived); cost per added staff member at FY{Y1} "
          f"pay ${cost_per_school_staff:,.0f} (salary; health counted under Benefits)")
    print(f"  staff {st0:,.1f} -> {st1:,.1f} ({st1-st0:+.1f}); enrollment {en0:,.0f} -> "
          f"{en1:,.0f} ({en1-en0:+.0f}); enrollment-proportional staff {sch_enroll_fte:+.1f}, "
          f"ratio change {sch_ratio_fte:+.1f}")
    print(f"  price ${sch_price/1e6:.2f}M  staffing ${sch_staff/1e6:.2f}M "
          f"(enrollment ${sch_enroll/1e6:.2f}M, ratio ${sch_ratio/1e6:.2f}M)  "
          f"residual ${sch_resid/1e6:.2f}M")
    print(f"  ratio change beyond enrollment: {ratio_rise:+.1f} FTE FY{Y0}-2019 while "
          f"enrollment rose, {ratio_after:+.1f} FTE FY2019-{Y1} as staff fell more "
          f"slowly than enrollment ({ratio_rise/(ratio_rise+ratio_after):.0%} / "
          f"{ratio_after/(ratio_rise+ratio_after):.0%})")
    print()

    # ======================================================== FIXED COSTS
    b0, b1 = BENEFITS[Y0], BENEFITS[Y1]
    fx0, fx1 = fnum(hist[Y0]["exp_fixed_costs"]), fnum(hist[Y1]["exp_fixed_costs"])
    # group health
    g0, g1 = b0["group_health"], b1["group_health"]
    fte0 = sum(panel[Y0][k] for k, _, _ in CATEGORIES) + st0
    fte1 = sum(panel[Y1][k] for k, _, _ in CATEGORIES) + st1
    gh_price = g0 * (B - 1)
    gh_head = g0 * B * (fte1 / fte0 - 1)
    gh_resid = g1 - g0 - gh_price - gh_head
    dfte = fte1 - fte0
    shares = {
        "New homes & commercial space": (town_growth_fte + sch_newhome_fte) / dfte,
        "Enrollment change (not from new homes)": (sch_enroll_fte - sch_newhome_fte) / dfte,
        "Staffing levels (service choices)":
            ((town_dfte - town_growth_fte) + sch_ratio_fte) / dfte,
    }
    add("Benefits", "Health: premium inflation", "Inflation", gh_price,
        "national state/local ECI benefits index")
    for grp, sh in shares.items():
        add("Benefits", "Health: more covered staff", grp, gh_head * sh,
            f"{sh:.0%} of the {dfte:+.0f} town+school FTE change")
    add("Benefits", "Health: premiums above inflation",
        "Pay & costs above/below inflation", gh_resid,
        "residual; includes retirees on the plan, who do not scale with active staff")
    # pensions
    p0, p1 = b0["pensions"], b1["pensions"]
    town_fte_ratio = sum(panel[Y1][k] for k, _, _ in CATEGORIES) / \
        sum(panel[Y0][k] for k, _, _ in CATEGORIES)
    nc1 = PENSION_NORMAL_COST_FY25
    town_fte_13 = sum(panel[2013][k] for k, _, _ in CATEGORIES)
    town_fte_11 = sum(panel[Y0][k] for k, _, _ in CATEGORIES)
    nc0 = PENSION_NORMAL_COST_FY13 / (ratio(idx, "eci_wages", Y0, 2013) *
                                      town_fte_13 / town_fte_11)
    nc_price = nc0 * (Ew - 1)
    nc_head = nc0 * Ew * (town_fte_ratio - 1)
    nc_rate = nc1 - nc0 * Ew * town_fte_ratio
    g_sh = town_growth_fte / town_dfte
    add("Benefits", "Pensions being earned now: pay inflation", "Inflation", nc_price,
        f"FY2011 normal cost ${nc0:,.0f}, carried back from the 1/1/2014 valuation's "
        "FY2013 figure; grown at the ECI for wages")
    add("Benefits", "Pensions being earned now: more town staff",
        "New homes & commercial space", nc_head * g_sh, "town FTE growth share")
    add("Benefits", "Pensions being earned now: more town staff",
        "Staffing levels (service choices)", nc_head * (1 - g_sh), "town FTE other share")
    add("Benefits", "Pensions being earned now: higher cost per dollar of pay",
        "Pay & costs above/below inflation", nc_rate,
        "employer normal cost 5.48% of payroll (FY2013) -> 7.71% (FY2025), actuarial "
        "assumption changes")
    add("Benefits", "Pensions: paying down the unfunded liability",
        "Legacy pension paydown", (p1 - nc1) - (p0 - nc0),
        f"amortization ${(p0-nc0)/1e6:.1f}M -> ${(p1-nc1)/1e6:.1f}M; ends at full funding, FY2030")
    add("Benefits", "OPEB trust contributions", "OPEB prefunding",
        b1["opeb"] - b0["opeb"], "funding-policy transfers into the retiree health trust")
    o0 = b0["total"] - b0["pensions"] - b0["group_health"] - b0["opeb"]
    o1 = b1["total"] - b1["pensions"] - b1["group_health"] - b1["opeb"]
    add("Benefits", "Other benefits (Medicare tax, workers' comp, IOD, etc.)", "Other",
        o1 - o0, "")
    add("Benefits", "Other fixed costs & Schedule A reconciling difference", "Other",
        (fx1 - fx0) - (b1["total"] - b0["total"]),
        "Schedule A fixed costs minus the Town's benefits detail")

    print("=" * 78)
    print(f"FIXED COSTS  ${(fx1-fx0)/1e6:+.2f}M  (benefits detail ${(b1['total']-b0['total'])/1e6:+.2f}M)")
    print("=" * 78)
    print(f"  group health ${g0/1e6:.2f}M -> ${g1/1e6:.2f}M: price ${gh_price/1e6:.2f}M, "
          f"heads ${gh_head/1e6:.2f}M, residual ${gh_resid/1e6:.2f}M")
    print(f"  normal cost pieces: price ${nc_price/1e6:.2f}M, heads ${nc_head/1e6:.2f}M, "
          f"rate ${nc_rate/1e6:.2f}M")
    print(f"  pensions ${p0/1e6:.2f}M -> ${p1/1e6:.2f}M: normal cost ${nc0/1e6:.2f}M (est) -> "
          f"${nc1/1e6:.2f}M, amortization ${(p0-nc0)/1e6:.2f}M -> ${(p1-nc1)/1e6:.2f}M")
    print()

    # ================================================================ DEBT
    d0, d1 = fnum(hist[Y0]["exp_debt_service"]), fnum(hist[Y1]["exp_debt_service"])
    x0, x1 = fnum(hist[Y0]["debt_exclusions"]), fnum(hist[Y1]["debt_exclusions"])
    add("Debt service", "Voter-approved excluded debt", "School & other buildings (debt)",
        x1 - x0, "Devotion, BHS, Driscoll, Pierce, Newbury, fire stations")
    add("Debt service", "Routine within-levy borrowing", "School & other buildings (debt)",
        (d1 - x1) - (d0 - x0), "")
    # ======================================================= INTERGOV
    i0, i1 = fnum(hist[Y0]["exp_intergov_assessments"]), fnum(hist[Y1]["exp_intergov_assessments"])
    add("State & MBTA assessments", "State, county and MBTA assessments", "Other",
        i1 - i0, "outside local control")

    # ========================================================= CONTROLS 1,2
    total0 = fnum(hist[Y0]["exp_total_expenditures"])
    total1 = fnum(hist[Y1]["exp_total_expenditures"])
    other0 = fnum(hist[Y0]["exp_other_expenditures"]) or 0
    other1 = fnum(hist[Y1]["exp_other_expenditures"]) or 0
    tree_sum = sum(r["dollars"] for r in rows)
    print("=" * 78)
    print("RECONCILIATION")
    print("=" * 78)
    gap = tree_sum - (total1 - total0 - (other1 - other0))
    print(f"  {'PASS' if abs(gap) < 1 else 'FAIL'}  tree sums to the Schedule A total "
          f"change: ${tree_sum:,.0f} vs ${total1-total0:,.0f} (gap ${gap:,.2f})")
    blocks = {
        "Town departments": dep_change, "Schools": s1 - s0, "Benefits": fx1 - fx0,
        "Debt service": d1 - d0, "State & MBTA assessments": i1 - i0,
    }
    for blk, want in blocks.items():
        got = sum(r["dollars"] for r in rows if r["block"] == blk)
        print(f"  {'PASS' if abs(got-want) < 1 else 'FAIL'}  {blk:26s} ${got:>14,.0f} "
              f"vs ${want:>14,.0f}")
    print()

    print("=" * 78)
    print(f"THE TREE: FY{Y0} ${total0/1e6:.1f}M -> FY{Y1} ${total1/1e6:.1f}M, "
          f"${(total1-total0)/1e6:+.1f}M")
    print("=" * 78)
    by_group = {g: sum(r["dollars"] for r in rows if r["group"] == g) for g in GROUPS}
    for g in GROUPS:
        print(f"  {g:42s}{by_group[g]/1e6:>8.1f}M {by_group[g]/(total1-total0):>6.1%}")
    print()

    # ============================================ non-personnel object check
    print("=" * 78)
    print("NON-PERSONNEL: does it grow faster than prices? (Town object-class actuals)")
    print("=" * 78)
    np_rows = []
    def np_total(d, with_other=True):
        return d["services"] + d["supplies"] + d["utilities"] + d["capital"] + \
            (d["other"] if with_other else 0)
    for y in (2023, 2024):
        k = y - Y0
        cpi = ratio(idx, "cpi_boston", Y0, y)
        eci = ratio(idx, "eci_total_comp", Y0, y)
        for lab, wo in (("all non-personnel", True), ("excluding 'Other'", False)):
            a, b = np_total(OBJECT_CLASS[Y0], wo), np_total(OBJECT_CLASS[y], wo)
            g = (b / a) ** (1 / k) - 1
            gc = cpi ** (1 / k) - 1
            print(f"  FY{Y0}-{y} {lab:20s} ${a/1e6:6.2f}M -> ${b/1e6:6.2f}M "
                  f"{g*100:5.2f}%/yr vs Boston CPI {gc*100:5.2f}%/yr")
            np_rows.append(dict(fy_start=Y0, fy_end=y, measure=lab, start=a, end=b,
                                cagr=round(g, 5), cpi_cagr=round(gc, 5)))
        pa, pb_ = OBJECT_CLASS[Y0]["personnel"], OBJECT_CLASS[y]["personnel"]
        g = (pb_ / pa) ** (1 / k) - 1
        print(f"  FY{Y0}-{y} {'personnel':20s} ${pa/1e6:6.2f}M -> ${pb_/1e6:6.2f}M "
              f"{g*100:5.2f}%/yr vs ECI {(eci**(1/k)-1)*100:5.2f}%/yr")
        np_rows.append(dict(fy_start=Y0, fy_end=y, measure="personnel", start=pa,
                            end=pb_, cagr=round(g, 5), cpi_cagr=None))
    print()

    # ============================================================== write
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["block", "component", "group", "dollars",
                                          "share_of_total_growth", "fy_start",
                                          "fy_end", "note"])
        w.writeheader()
        for r in rows:
            w.writerow(dict(r, dollars=round(r["dollars"]),
                            share_of_total_growth=round(r["dollars"] / (total1 - total0), 4),
                            fy_start=Y0, fy_end=Y1))
    with open(NONPERS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(np_rows[0]))
        w.writeheader()
        w.writerows(np_rows)

    write_methodology(rows, by_group, total0, total1, dict(
        E=E, B=B, C=C, n=n, nc0=nc0, nonres=nonres, com_sqft_central=com_sqft_central,
        com_sqft_upper=com_sqft_upper, com_stock_sqft=com_stock_sqft,
        com_cost_central=com_cost_central, com_cost_upper=com_cost_upper,
        home_cost=home_cost, new_home_students=new_home_students, np_rows=np_rows,
        en0=en0, en1=en1, st0=st0, st1=st1, town_dfte=town_dfte,
        town_growth_fte=town_growth_fte, ratio_rise=ratio_rise, ps=ps,
        cost_per_school_staff=cost_per_school_staff,
        ratio_after=ratio_after))
    print(f"wrote {OUT_CSV.name}, {NONPERS_CSV.name}, {METHOD_OUT.name}")


def m(x):
    return f"${x/1e6:,.1f}M"


def write_methodology(rows, by_group, total0, total1, v):
    tot = total1 - total0
    lines = [
        "# Expense driver tree, FY2011-2025",
        "",
        "Companion to `expense_drivers_tree_fy11_25.csv` and "
        "`expense_drivers_object_class_fy11_24.csv`. Generated by "
        "`scripts/expense_drivers_tree.py`, which prints its own controls. Builds on "
        "Phases A-C (`docs/expense_drivers_workplan.md`).",
        "",
        f"General Fund expenditure (Schedule A) went from {m(total0)} in FY2011 to "
        f"{m(total1)} in FY2025, {m(tot)} of growth. Every dollar of that is assigned "
        "to one of nine driver groups below, and the script checks that they sum "
        "back to the total exactly.",
        "",
        "## Result",
        "",
        "| Driver group | FY2011-25 growth | Share |",
        "|---|---:|---:|",
    ]
    for g in GROUPS:
        lines.append(f"| {g} | {m(by_group[g])} | {by_group[g]/tot:.0%} |")
    lines += ["", "## Every component", "",
              "| Block | Component | Group | $ | Note |", "|---|---|---|---:|---|"]
    for r in rows:
        lines.append(f"| {r['block']} | {r['component']} | {r['group']} | "
                     f"{m(r['dollars'])} | {r['note']} |")
    lines += [
        "",
        "## Commercial space",
        "",
        f"Non-residential new growth value FY2012-25 was {m(v['nonres'])}, but that "
        "includes personal property (mostly utility equipment), which creates no "
        "service demand. In FY2026, the one year with a published split, personal "
        f"property was {1-COM_SHARE_OF_NONRES_NG_FY26:.0%} of non-residential new "
        f"growth. At that split, about {v['com_sqft_central']:,.0f} sqft of commercial "
        f"space was added, roughly {v['com_sqft_central']/v['com_stock_sqft']:.0%} of "
        f"today's ~{v['com_stock_sqft']/1e6:.1f}M sqft stock, costing about "
        f"{m(v['com_cost_central'])}/yr at RKG's $219 per employee. Treating all "
        f"non-residential growth as commercial gives an upper bound of "
        f"{m(v['com_cost_upper'])}. Either way it is small beside new homes "
        f"({m(v['home_cost'])}) and far below the other drivers.",
        "",
        "## Non-personnel spending",
        "",
        "From the Town's own object-class actuals (services, supplies, utilities, "
        "capital outlay, other), General Fund including schools:",
        "",
        "| Window | Measure | Start | End | Growth/yr | Boston CPI/yr |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in v["np_rows"]:
        c = f"{r['cpi_cagr']*100:.2f}%" if r["cpi_cagr"] is not None else "n/a"
        lines.append(f"| FY{r['fy_start']}-{r['fy_end']} | {r['measure']} | {m(r['start'])} "
                     f"| {m(r['end'])} | {r['cagr']*100:.2f}% | {c} |")
    lines += [
        "",
        "Non-personnel spending grew at or below local inflation, depending on the "
        "end year; FY2023 to FY2024 alone moved it 15%, mostly services. The 'Other' "
        "line grew from $0.8M to $2.8-4.9M and looks like a change in what the Town "
        "books there, so it is shown both ways. Either way, non-personnel is not a "
        "source of above-inflation growth, which is what the tree's CPI assumption for "
        "it takes for granted.",
        "",
        "Only three years are used. The Financial Plans' multi-year class tables for "
        "FY2014-FY2018 repeat values across differently labelled columns (the FY2020 "
        "plan's FY2016 column is the FY2018 plan's FY2015 column, for example), so "
        "those years were not trusted.",
        "",
        "## Estimates and judgment calls, in order of how much they matter",
        "",
        f"1. **Pension normal cost in FY2011 is carried back two years** ({m(v['nc0'])}) "
        "from the 1/1/2014 valuation's FY2013 employer normal cost ($3.43M, 5.48% of "
        "payroll) by wage inflation and town headcount. The first version of this "
        "script estimated $4.87M by deflating FY2025, which missed the rise in normal "
        "cost as a share of payroll (5.48% to 7.71%). That rise is now its own "
        "component under Pay & costs above inflation. The 1/1/2010 valuation would pin "
        "FY2011 exactly; the remaining error is a few hundred thousand dollars.",
        "2. **Growth-driven town staffing uses RKG's rates, department share only.** "
        f"RKG's $1,371/home includes $262 of benefits, debt and insurance; only the "
        f"{RKG_DEPT_SHARE:.0%} that is department budgets is used here, because benefits "
        "for added staff are counted under Benefits. The first version used the full "
        "$1,371 and so counted those benefits twice. RKG puts 88% of the department "
        "share in police and fire; Brookline's actual added town positions FY2011-25 "
        "were in other departments (public safety FTE fell by 5). It is an allocation, "
        "not an observation.",
        f"3. **Students from new homes** use the model's {STUDENTS_PER_NEW_HOME} per "
        f"home, giving {v['new_home_students']:,.0f}, which happens to equal net "
        f"enrollment change ({v['en0']:,.0f} to {v['en1']:,.0f}). That coincidence "
        "hides the real path: enrollment rose to 7,855 by FY2019, far beyond what new "
        "homes could supply, then fell with COVID. School staff rose with it and "
        "fell only part way. Of the staff added beyond enrollment, about "
        f"{v['ratio_rise']:.0f} FTE came while enrollment was rising (FY2011-19) and "
        f"about {v['ratio_after']:.0f} FTE is staff retained after it fell "
        "(FY2019-25), measured separately in each sub-window. A Town/Schools count "
        "of 10 developments of 8+ units built since 2015 (ERSC report, PDF p.567) "
        "found 0.03-0.56 enrolled students per unit in Fall 2025, simple average "
        "about 0.21.",
        f"4. **School personnel share ({v['ps']:.0%}) is derived**, not published: FY2011 "
        "General Fund personnel actuals minus town-department personnel, over school "
        "spending. FY2024 on the same basis gives about 83%. Added school staff are "
        f"priced at ${v['cost_per_school_staff']:,.0f} (FY2025 pay, salary only). The "
        "first version priced them at total school spending per staff member "
        "(~$116K), which included non-personnel costs.",
        "5. **Town FTE crosses the unvalidated FY2020/21 seam** (+18.5 FTE), which "
        "sits inside 'Staffing levels'.",
        "6. **Group health residual includes retirees**, who are about half of plan "
        "subscribers (1,659 of 3,390 in FY2025) and do not scale with active headcount.",
        "7. **Commercial split uses one year** (FY2026) of the commercial/personal "
        "property mix.",
        "8. **The pay benchmark is national.** BLS does not publish the ECI by state. "
        "QCEW average pay for local government grew 3.40%/yr in Massachusetts and "
        "3.65%/yr nationally over 2014-2024 (`qcew_local_gov_pay_ma_us_2014_24.csv`), "
        "so the national benchmark does not understate Massachusetts pay growth.",
        "",
        "## What this is not",
        "",
        "Not causal, and not a forecast. It is an accounting of where the money went, "
        "with each piece measured against an outside benchmark where one exists. "
        "Phase D would turn it into a forecast.",
        "",
    ]
    METHOD_OUT.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
