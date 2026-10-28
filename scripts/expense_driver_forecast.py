"""
Phase D: a driver-based General Fund expense forecast, FY2026-2040.

The driver tree (expense_drivers_tree.py) explained FY2011-25 spending growth as
quantity x price for each budget line. This runs the same structure forward, so
every line of the forecast rests on a named assumption instead of a trend rate.
Plan and Ben's decisions: docs/forecast_phase_d_plan.md.

## Basis

Operating basis, matching the revenue side (base_case_decomposition.py,
`as_legislated`): Town budget levels, excluded debt left out on both sides
because it is matched dollar for dollar by the debt-exclusion tax.

  - FY2026 is the Town's FY2026 budget (town_own_forecast_fy26_31.csv), for the
    balanced-budget check. Levels start from the FY2027 budget adopted by Town
    Meeting in May 2026 (fy2027_adopted.py). The state's Schedule A measures
    actual spending, which runs below budget (the gap comes back as free cash,
    which the revenue forecast counts), so Schedule A levels would not pair with
    the revenue side.
  - Growth from FY2028 comes from the drivers.
  - Pensions, retiree health (OPEB), debt and other non-departmental lines use
    published Town schedules through FY2031, where they exist.

## Lines

  Town departments   = FY2027 budget x [personnel share x pay index x FTE index
                       + non-personnel share x CPI index] + growth costs
  Schools            = FY2027 budget x [personnel share x pay index x staff index
                       + non-personnel share x CPI index x enrollment index]
                       staff: the staffing rule (base: half as fast as enrollment falls)
  Group health       = FY2027 budget x subscriber index x premium index
                       subscribers, weighted by cost: actives follow total FTE,
                       retirees their own trend
  Pensions           = Town schedule to FY2031 (full funding FY2030), then the
                       normal cost growing at pay + 0.65 point (the actuary's
                       payroll growth and mortality adjustment)
  OPEB               = Town schedule to FY2031 (includes the pension-to-OPEB
                       shift), then $43.0M a year until the liability is paid off
  Other benefits     = Town schedule to FY2031, then all payroll, Town and schools
  Within-levy debt   = the FY2027 Financial Plan's capital funding table
                       (p.384) to FY2032, then 3.5%/yr (capital policy ties
                       capital spending to revenue)
  Other non-dept     = the existing forecast's series (CIP, reserves,
                       non-appropriated), which are policy lines

## Base-case assumptions (Ben, 2026-09-28)

  Pay growth 3.0%/yr (Town's bargaining target) for Town staff. CPI 2.5%/yr.
  School staff fall half as fast as enrollment (Ben, 2026-10-14; see BASE).
  Enrollment: NESDEC October 2023 projection, scaled to the October 2025 actual,
    extended to FY2040 by carrying its own grade-to-grade ratios forward.
  Health premiums: Town's 12%/yr for FY2028-29, then 8%/yr (between the
    6.5% 25-year average and the recent 10-12%; Ben, 2026-09-28).
  Pay: Town staff 3.0%; school pay 0.7 point above it (3.7%, the middle of the
    3.3-4.1% range the School Department's FY2026 budget build gives at the
    2.75% contract raise) and Public Safety 0.5 point above (3.5%), plus the
    fire contract's new steps from FY2028 and four police positions refilled.
  Town cost of a new home: $660 (FY2025 $), from cross_town_marginal_cost.py.
  OPEB: follows the Town's schedule, including the FY2031 shift.
  Growth: new_growth_scenarios `trend_continues`.

## Growth by type

Each type of new growth brings tax revenue (new_growth_scenarios) and, for
some types, service cost:

  new residential units  -> town services ($660/home) + students (0.2442/home)
  residential renovation -> revenue only
  new commercial space   -> town services per employee (1 per 200 sqft,
                            RKG $219 x department share)
  commercial renovation  -> revenue only
  personal property      -> revenue only
  CHCA                   -> 266 homes + ~963 employees, ramped FY2032-34

NESDEC's projection already contains students from trend-level housing (its
grade ratios come from years when Brookline added ~150 homes a year), so the
forecast adds only students from homes above the trend scenario's count. The
growth-type table, which asks what each type costs in full, counts all of them.

Run from `scripts/`:  python3 expense_driver_forecast.py
"""

import csv
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
OUT = ROOT / "output"
YEARS = list(range(2026, 2041))

# ------------------------------------------------------------------ inputs
TOWN = OUT / "town_own_forecast_fy26_31.csv"
BASE_EXP = OUT / "baseline_expense_forecast_fy26_40.csv"
BASE_CASE = OUT / "base_case_decomposition_fy26_40.csv"
GROWTH = OUT / "new_growth_scenarios_fy26_40.csv"
FTE_PANEL = OUT / "expense_drivers_fte_panel_fy04_27.csv"
HIST = OUT / "brookline_historical_financials_fy05_25.csv"
SALARY = OUT / "department_fte_salary_by_category_fy19_fy26.csv"
TREE = OUT / "expense_drivers_tree_fy11_25.csv"

OUT_LINES = OUT / "expense_driver_forecast_fy26_40.csv"
OUT_TORNADO = OUT / "expense_driver_forecast_sensitivity_fy40.csv"
OUT_TYPES = OUT / "expense_driver_forecast_growth_types.csv"
OUT_RECON = OUT / "expense_driver_forecast_reconciliation.csv"
OUT_PS = OUT / "public_safety_projection_fy27_40.csv"
OUT_BIRTHS = OUT / "enrollment_births_basis.csv"   # births behind the enrollment path, for the pages
METHOD = OUT / "expense_driver_forecast_methodology.md"

# NESDEC, "The Public Schools of Brookline, Brookline, MA", 10/31/2023
# (data/NESDEC-Enrollment-Forecast.pdf), PK-12 by school year. Grade detail
# below is used to extend past 2033-34.
NESDEC_PK12 = {2024: 7024, 2025: 7013, 2026: 6880, 2027: 6774, 2028: 6585,
               2029: 6506, 2030: 6464, 2031: 6365, 2032: 6303, 2033: 6217, 2034: 6127}
# NESDEC projected enrollment by grade, PK, K, 1..12, school years 2023-24 to
# 2033-34 (FY2024-FY2034), transcribed from the report's projection table.
NESDEC_GRADES = {
    2024: [256, 472, 520, 527, 544, 537, 511, 519, 471, 511, 570, 522, 551, 513],
    2025: [256, 491, 486, 532, 527, 549, 537, 486, 516, 469, 509, 577, 522, 556],
    2026: [257, 412, 506, 498, 532, 532, 549, 511, 484, 513, 467, 515, 577, 527],
    2027: [257, 415, 424, 518, 498, 537, 532, 522, 508, 482, 511, 473, 515, 582],
    2028: [258, 388, 427, 434, 518, 503, 537, 506, 519, 505, 480, 517, 473, 520],
    2029: [258, 438, 400, 437, 434, 523, 503, 511, 503, 516, 503, 486, 517, 477],
    2030: [259, 429, 451, 410, 437, 438, 523, 478, 508, 500, 514, 509, 486, 522],
    2031: [259, 416, 442, 462, 410, 441, 438, 497, 476, 505, 498, 521, 509, 491],
    2032: [260, 417, 428, 453, 462, 414, 441, 417, 495, 474, 503, 504, 521, 514],
    2033: [260, 417, 430, 438, 453, 467, 414, 419, 415, 493, 472, 509, 504, 526],
    2034: [260, 423, 430, 440, 438, 458, 467, 394, 417, 413, 491, 478, 509, 509],
}
NESDEC_K_LATE = 423   # K held at NESDEC's last projected value (births ~495-500/yr)

# Births (2026-10-08, Ben): NESDEC's 10/31/2023 forecast estimated births for 2023 onward
# (report p.7: 2023 518, 2024 507, 2025 492, 2026 493, 2027 494, 2028 501; 2020 actual 487,
# which matches MA DPH's resident count, so the definitions agree). Actual births came in far
# lower: 422 in 2023 (MA DPH Table 17) and 443 in 2024 (Town Clerk, 2024 Annual Town Report
# p.37); NESDEC's 2022 figure was provisional (459) and DPH's final count is 482. NESDEC turns
# births into kindergarten at a steady ratio (~0.846), so each cohort born 2022 or later is rescaled by actual / NESDEC-estimated births, in every grade it reaches by
# FY2034, and kindergarten after FY2034 by the same ratio against NESDEC's ~501. Births not yet
# counted (2025 on) are held at the 2022-24 average (Ben, 2026-10-09: three years smooths a low
# 2023; national births were flat in 2024-25), continuing the observed level.
NESDEC_BIRTHS = {2020: 487, 2021: 491, 2022: 459, 2023: 518, 2024: 507, 2025: 492, 2026: 493,
                 2027: 494, 2028: 501}
BIRTHS_ACTUAL = {2022: 482, 2023: 422, 2024: 443}   # 2022: DPH final (NESDEC had 459 provisional)
BIRTHS_AHEAD = (BIRTHS_ACTUAL[2022] + BIRTHS_ACTUAL[2023] + BIRTHS_ACTUAL[2024]) / 3   # 2025 onward
NESDEC_GRADES_PUBLISHED = {y: row[:] for y, row in NESDEC_GRADES.items()}
NESDEC_PK12_PUBLISHED = dict(NESDEC_PK12)


def _birth_factor(b):
    if b < 2022:
        return 1.0
    return BIRTHS_ACTUAL.get(b, BIRTHS_AHEAD) / NESDEC_BIRTHS[b]


for _y, _row in NESDEC_GRADES.items():   # index 0 is PK; index n+1 is grade n (K = 0)
    for _n in range(13):
        _f = _birth_factor(_y - 6 - _n)   # kindergarten in FY y was born in y - 6
        if _f != 1.0:
            _row[_n + 1] = round(_row[_n + 1] * _f)
    NESDEC_PK12[_y] = sum(_row)
NESDEC_K_LATE = round(NESDEC_K_LATE * BIRTHS_AHEAD / NESDEC_BIRTHS[2028])
ACTUAL_OCT_2025 = 6949  # PSB October 1, 2025 (brookline.news report; FY2026)
# PSB October 1, 2026 count (SIMS submission to DESE; PSB Enrollment Report, 10/28/2026, slide 4):
# BEEP 232 + K-8 4,436 + BHS 2,165 = 6,833 for SY2026-27 (FY2027), excluding 56 out-of-district
# students and 15 early-childhood students under 3, as DESE counts it. Replaced the September 11
# count (6,889: BEEP 252 + K-8 4,458 + BHS 2,177) on 2026-10-27.
ACTUAL_OCT_2026 = 6833
# Cropper-McKibben 2023 forecast, PK-12, school years 2026-27 to 2033-34
# (FY2027-FY2034): the projection the School Department plans with
# (FY27-29 PSB budget summary, Table 7; override slides p.14). It bottoms out in
# 2027-28 and rises toward pre-pandemic levels. Its misses so far: -0.6%
# (2024-25), -0.3% (2025-26), +1.2% (2026-27 October 1 count).
CM_PK12 = {2027: 6917, 2028: 6886, 2029: 6933, 2030: 7050, 2031: 7118, 2032: 7245,
           2033: 7344, 2034: 7444}

# Growth-type cost inputs
# shared with the per-project calculator and the per-home test (cost_assumptions.py)
from cost_assumptions import (TOWN_COST_PER_HOME_FY25 as COST_PER_HOME_FY25,
                              TOWN_COST_PER_EMPLOYEE_FY25 as RKG_COM_DEPT_PER_EMP_FY25,
                              TOWN_BENEFIT_LOADING, STUDENTS_PER_HOME,
                              SQFT_PER_EMPLOYEE as SQFT_PER_EMP, PERMITTING_COST_FY27,
                              TOWN_COST_PER_HOME_PS_SHARE, HOMES_FY2025, FIRE_COMPANY_HOMES,
                              FIRE_COMPANY_FIREFIGHTERS, FIRE_COMPANY_COST_FY25,
                              PS_POSITION_COST_FY25, PS_RESTORE_POSITIONS,
                              PS_SHARE_POLICE, POLICE_BUDGET_FY27, POLICE_PEER_PER_1000_HOMES,
                              FIRE_BUDGET_FY27, FIRE_COMPANY_OVERTIME_FY25)
# Chestnut Hill Commercial Area (CHCA). The five fiscal-impact scenarios (ERSC
# report pp.551-555; "Fiscal Impact Model" tab of Ben's revenue workbook) are
# different building programs, not different valuations of one program:
#   City Realty 1/2/3: 668 / 424 / 388 homes, 184k / 213k / 51k sqft office+retail,
#                      200 / 225 / 152 hotel rooms
#   RKG:               265 homes, 74k sqft office+retail, 100 rooms
# The approved plan (Town Meeting May 2026) is 266 homes and a 200-room hotel with
# over half the floor area commercial. The "approved" estimate prices that program
# from the scenarios' own rates: RKG's residential tax per home (265 homes ->
# $1,841,088), City Realty 1's commercial and personal property tax (the only
# scenario with the approved 200 rooms; its 184k sqft of office and retail is
# consistent with the >50% commercial requirement), rooms tax for 200 rooms and
# RKG's motor-vehicle excise per home. Commercial square footage is the unknown.
CHCA_UNITS = 266
CHCA_STUDENTS_PER_UNIT = 0.126    # high-rise, studio/1BR-heavy (a recent rental project)
CHCA_EMPLOYEES = (79_000 + 105_000) / 200 + 200 * 500 / 2_300   # City Realty 1 program
CHCA_REVENUE = {   # (property tax at stabilization, local receipts at stabilization, residential share
                   # of the property tax), FY2025 dollars; the revenue model indexes them to entry
    "approved": (round(266 * 1_841_088 / 265) + 2_696_433, 762_120 + round(266 * 99_375 / 265),
                 round(266 * 1_841_088 / 265) / (round(266 * 1_841_088 / 265) + 2_696_433)),
    "cr_avg": (5_408_241, 917_905, 3_030_198 / 5_408_241),
    "rkg": (3_158_174, 480_435, 1_841_088 / 3_158_174),
    "in_trend": (0, 0, 0.0),
}
_GROWTH_CACHE = {}


def chca_growth_frame(chca):
    """new_growth_scenario_forecast rerun with the chosen CHCA amounts, written to
    a scratch file so the committed Phase 2 output is untouched."""
    if chca not in _GROWTH_CACHE:
        import contextlib, io, tempfile
        import new_growth_scenario_forecast as ngs
        prop, lr, res_share = CHCA_REVENUE[chca]
        saved = (ngs.CHCA_PROPERTY_TAX_AT_STABILIZATION, ngs.CHCA_LOCAL_RECEIPTS_AT_STABILIZATION,
                 ngs.CHCA_PROPERTY_TAX_RES_SHARE, ngs.OUT_FILE)
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False).name
        try:
            (ngs.CHCA_PROPERTY_TAX_AT_STABILIZATION, ngs.CHCA_LOCAL_RECEIPTS_AT_STABILIZATION,
             ngs.CHCA_PROPERTY_TAX_RES_SHARE) = prop, lr, res_share
            ngs.OUT_FILE = tmp
            saved_extra = ngs.EXTRA_SCENARIOS
            ngs.EXTRA_SCENARIOS = {**ngs.homes_scenarios(), **saved_extra}   # the new-homes switch
            meth = getattr(ngs, "METHODOLOGY_FILE", None)
            with contextlib.redirect_stdout(io.StringIO()):
                if meth is not None:
                    ngs.METHODOLOGY_FILE = tmp + ".md"
                ngs.main()
            _GROWTH_CACHE[chca] = pd.read_csv(tmp)
        finally:
            (ngs.CHCA_PROPERTY_TAX_AT_STABILIZATION, ngs.CHCA_LOCAL_RECEIPTS_AT_STABILIZATION,
             ngs.CHCA_PROPERTY_TAX_RES_SHARE, ngs.OUT_FILE) = saved
            ngs.EXTRA_SCENARIOS = saved_extra
            if meth is not None:
                ngs.METHODOLOGY_FILE = meth
    return _GROWTH_CACHE[chca]
LEVY_GROWTH = 1.025

# Base case = Brookline's FY2011-25 record (Ben, 2026-09-28: a large-surplus
# base would not be credible). School staff fall half as fast as enrollment, as from FY2019 to
# FY2025 (enrollment -10.6%, staff -5.0%; Ben, 2026-10-14; was held at FY2027); Public Safety pay runs 0.5 pt above the 3.0% target
# (Ben, 2026-10-14; was 1.5 pt): its FY2011-25 average per position was about 3.3%, and the
# FY2021-25 surge came mostly from one-time stipends and new steps, the agreed ones counted
# separately (FIRE_STEPS_FY28, POLICE_REFILL); health premiums settle at 8%,
# between the 6.5% 25-year average and recent 10-12%.
# School pay: 0.7 pt above the target, 3.7% (Ben, 2026-10-05; was 0.4 pt, the
# FY2011-25 record). The middle of the range the School Department's own budget
# arithmetic gives at the 2.75% contract raise: its FY2026 level-service build
# prices steps (1.6% of payroll) and degree-column moves (0.1%) against budgeted
# turnover savings (0.4%), about 4.1% per position at constant staffing; FY2025's
# actual turnover savings ran about 1% of payroll more, about 3.3%.
BASE = dict(
    pay=0.030, pay_ps_premium=0.005, school_pay_drift=0.007, cpi=0.025, ratio_mode="half",
    enroll_mode="nesdec", migration=0.0, premium_near=0.12, premium_long=0.08, cost_per_home=COST_PER_HOME_FY25,
    growth="trend_continues", pension_slip=0, opeb_redirect=True, opeb_hold=True, sch_np_extra=0.0,
    chca="approved", fire_step=True, ps_restore=False, police_step=False, capital_full=True,
)
# Public safety (Ben, 2026-10-10): staffing held at the FY2027 budget (police 128 sworn,
# fire 160); vacancies below budget come back as free cash, which the revenue side counts.
# Fire adds a company in steps (cost_assumptions.py) and the per-home charge drops fire's part
# of its public safety share; police keep theirs. Restoring police and fire to earlier levels
# (ps_restore) and police growing with homes at the peer ratio (police_step) are levers.
FIRE_OVERTIME_FY27 = 1_136_457 + 800_000   # FY2027 Fire overtime budget plus override (FP2027 pp.214-217; ATM May 2026 p.71)
SCHOOL_PERSONNEL_SHARE = 0.83   # derived, FY2024 basis (expense_drivers_tree.py notes)
# Share of the school budget that varies with enrollment. RKG's FY2025
# "incremental school budget" was 67% of the total, set with Town staff
# (ERSC Appendix C). The other third (buildings, administration, leadership)
# grows with prices only.
SCHOOL_VARIABLE_SHARE = 0.67
# A student from growth who fills an open seat (fill_capacity) costs the middle tier: an open seat
# plus special education at the district average, about $7,760 in FY2027
# (special_education_cost_per_student.py; Ben, 2026-10-27). Was the non-personnel $2,497 alone.
FILL_SEAT_COST_FY27 = 7758
# Select Board capital policy: 6.6% of prior-year net revenue from revenue (4.5% debt, 2.1% cash);
# FY2027 Financial Plan p.352 and p.459
CIP_POLICY_SHARE = 0.066
# The policy's net revenue also leaves out non-appropriated items (state assessments and the like):
# $10,792,034 in FY2027, growing 2.38% a year to $12,137,664 in FY2032 (FY2027 Financial Plan p.384).
NON_APPROP_FY27, NON_APPROP_GROWTH = 10_792_034, 0.0238
# Non-departmental lines grown by Town policy (Ben, 2026-10-14), instead of held flat after FY2031.
# Reserve fund: 1% of the prior year's net revenue (Reserve Policies, ATM May 2026 Combined Reports
# pp.8-8 to 8-9), from FY2028. General non-departmental (mostly stabilization and liability fund
# deposits, whose targets are shares of revenue): the Town plan to FY2031, then with net revenue.
# Non-appropriated (MBTA and county, capped at 2.5% by law; overlay): the Town plan to FY2031,
# then 2.38% a year, the Town plan's own rate.
RESERVE_FUND_SHARE = 0.01
# Public safety commitments already agreed. Fire: new 3% steps after 5 and 10 years from June 30,
# 2027, estimated at $909,471 (ERSC Final Report, March 2026, pp.108-109). Police: six positions held
# open to fund the contract are refilled with the override, two in FY2027 and two more in each of the
# next two years (Advisory Committee report, May 2026 Combined Reports p.8-19).
# Free cash uses already in the spending lines: the deposits are 80% of general non-departmental
# (FY2027: stabilization $3.50M, liability $2.18M, housing trust $1.07M of $8.48M without the override
# fund), and a quarter of the reserve fund's 1% (Free Cash Policies, May 2026 Combined Reports p.8-8).
FC_DEPOSIT_SHARE = (3_500_000 + 2_182_237 + 1_070_667) / (15_614_820 - 3_570_679 - 3_568_303)
FC_RESERVE_SHARE = 0.0025
FIRE_STEPS_FY28 = 909_471
# Retiree health (OPEB), paid down like the pension (Ben, 2026-10-14): from FY2031 the Town pays the
# plan's $43.0M a year into the trust, on top of retirees' premiums, until the net liability is paid
# off; after that the deposit stops and the money is free. The liability is rolled forward from the
# FY2024 audit (pp.83-85, RSI p.103): total liability $301,751,680, trust $100,275,701, service cost
# $8,509,485 and benefits paid $12,388,461 in FY2024, 6.90% interest. Service cost and benefits grow
# with premiums (benefits also with retirees, RETIREE_GROWTH, 0.92% a year). When premiums grow faster than the
# actuary's trend, the liability rises by the difference (the audit: one point more trend is +$53M).
OPEB_RATE = 0.069
# Health plan split (Ben, 2026-10-14): weighted by cost, not headcount. Retirees are 49% of subscribers
# but many are on cheaper Medicare supplement plans: the FY2024 audit's retiree benefit payments
# ($12,388,461) were 36% of FY2024 group health spending ($34,756,062, FY2026 Financial Plan). Retiree
# subscribers grew 1,459 (FY2011, FY2012 Plan) to 1,659 (FY2025, FY2027 Plan), 0.92% a year.
HEALTH_RETIREE_COST_SHARE = 0.36
RETIREE_GROWTH = (1659 / 1459) ** (1 / 14) - 1
OPEB_TREND = {2025: 0.1072, 2026: 0.0586, 2027: 0.0571, 2028: 0.055, 2029: 0.0525, 2030: 0.05125,
              2031: 0.05, 2032: 0.04875, 2033: 0.0475, 2034: 0.04625}   # the actuary's, Medicare and
OPEB_TREND_LONG = 0.045                                                  # non-Medicare averaged


# The liability follows the actuary's own healthcare trend (Ben, 2026-10-14). Until then it used the
# group health budget's growth (10.1%, 8.9%, 11.4% in FY2025-27, then the base case's premiums) and
# added the gap over the actuary's trend as a yearly loss. That budget growth includes more people on
# the plan and active employees' costs, not what retirees' coverage costs: the audits show the
# liability at $292M in FY2017 and $302M in FY2024, and benefits paid up about 1% a year. With the
# gap term the liability reached about $380M by FY2027 and was never paid off before FY2040; on the
# actuary's trend it is paid off in the mid-2030s. Flagged for a deeper look (retiree cost record,
# the next valuation). The premium settings still move the group health line, not this liability.
def opeb_trend(y):
    return OPEB_TREND.get(y, OPEB_TREND_LONG)


def opeb_start():
    """Total liability, trust, service cost and benefits at June 30, 2027, rolled forward from the
    FY2024 audit on the actuary's trend (deposits as budgeted)."""
    tol, assets, sc, ben = 301_751_680, 100_275_701, 8_509_485, 12_388_461
    for y, dep in [(2025, 5_431_980), (2026, 4_931_980), (2027, 4_931_980)]:
        gm = opeb_trend(y)
        sc *= 1 + gm
        ben *= (1 + gm) * (1 + RETIREE_GROWTH)
        tol = tol * (1 + OPEB_RATE) + sc - ben
        assets = assets * (1 + OPEB_RATE) + dep
    return round(tol), round(assets), round(sc), round(ben)   # to the dollar, as the Explorer page carries them


OPEB_START = opeb_start()
POLICE_REFILL = {2028: 2, 2029: 4}
# Pensions after FY2031 (2026-10-14, from the independent review): the employer normal cost grows with
# the system's payroll. The actuary projects it at 3.5% payroll growth plus 0.15% for mortality
# improvement (2024 valuation, funding schedule notes); with the Town's 3.0% pay target that is pay
# plus 0.65 point, so the pay setting still moves it. Until now it grew with Town pay alone, 3.0%.
PENSION_NC_PREMIUM = 0.0065
# Pension full funding slipping N years (the "slip" setting): FY2030's last catch-up payment, the Town
# plan's FY2030 pension less that year's normal cost, is instead paid in N+1 level installments over
# FY2030 to FY2030+N, at the system's 6.8% assumed return. The rest of the money the plan sets aside
# for pensions and retiree health in those years goes to retiree health, as the plan does after
# FY2030 (or stays in the budget when the pension savings are kept). Until 2026-10-14 the setting kept
# paying the whole FY2030 contribution, about $45M a year, though only $29.45M was left unfunded.
PENSION_RATE = 0.068
# School staff, FY2026: DESE's count as the School Department reports it (FY27-29 PSB budget summary,
# Table 4: 1,264.1 in 2025-26, 1,242.0 projected for 2026-27 after the 22.1 net reduction). Until
# 2026-10-14 the model used October 2025 enrollment over FY2025's 5.62 students per staff (1,236.4),
# a different base from the one the 22.1 was measured on.
SCHOOL_STAFF_FY26 = 1264.1
# FY2031 general non-departmental and non-appropriated, read from the Town plan (were typed)
_town31 = pd.read_csv(TOWN).set_index(["category", "subcategory"])["2031"]
NONDEPT_GENERAL_FY31 = float(_town31[("expenditure", "nondept_general")])
NON_APPROP_FY31 = float(_town31[("expenditure", "non_appropriated")])
RATIO_NOW, RATIO_FY2019 = 5.62, 7855 / 1315.8
ANCHOR_YEAR = 2027   # levels from the adopted FY2027 budget; drivers from FY2028


def load():
    town = pd.read_csv(TOWN).set_index(["category", "subcategory"])
    tsch = {int(c): town[c] for c in town.columns}
    be = pd.read_csv(BASE_EXP)
    be = be[be.scenario == "trend_corrected"].set_index("fiscal_year")
    bc = pd.read_csv(BASE_CASE)
    bc = bc[(bc.run == "as_legislated")].set_index("fiscal_year")
    gr = pd.read_csv(GROWTH)
    fte = pd.read_csv(FTE_PANEL).set_index("fiscal_year")
    hist = pd.read_csv(HIST).set_index("fiscal_year")
    sal = pd.read_csv(SALARY).set_index("category")
    return tsch, be, bc, gr, fte, hist, sal


MIGRATION_FROM = 2027   # families moving in, the lever: compounds from the FY2027 count on


def nesdec_grades():
    """NESDEC's grades (PK, K-12) FY2027-FY2040, births-adjusted and not yet scaled: its own table to
    FY2034, then each grade advanced a year by NESDEC's grade-to-grade ratios, averaged over its
    projected years, with kindergarten held at NESDEC's last value (births-adjusted)."""
    for y, row in NESDEC_GRADES.items():   # control: the table's rows sum to its PK-12 totals
        assert sum(row) == NESDEC_PK12[y], (y, sum(row), NESDEC_PK12[y])
    ratios = []
    for gi in range(1, 13):   # K..11 -> 1..12
        rs = [NESDEC_GRADES_PUBLISHED[y + 1][gi + 1] / NESDEC_GRADES_PUBLISHED[y][gi] for y in range(2024, 2034)]
        ratios.append(sum(rs) / len(rs))
    rows = {y: NESDEC_GRADES[y][:] for y in range(2027, 2035)}
    g = NESDEC_GRADES[2034][:]
    for y in range(2035, 2041):
        k12 = g[1:]
        g = [g[0]] + [NESDEC_K_LATE] + [k12[i] * ratios[i] for i in range(12)]
        rows[y] = g
    return rows


def migration_years(y, gi):
    """Years of the families-moving-in lever a class in grade gi (K = 0) has had by FY y: every year
    since FY2027, or since birth for children born later (kindergarten in FY y was born in y - 6),
    so kindergartners per birth move with it."""
    return max(y - max(MIGRATION_FROM, y - 6 - gi), 0)


def enrollment_by_exponent():
    """The base-case enrollment path split by how many years of the lever each child has had:
    {n: {fiscal year: students}}. Enrollment at a migration rate m is the sum of students x (1 + m)^n.
    FY2026 and FY2027 are actual counts (n = 0); later years are NESDEC's grades scaled to the FY2027
    count (6,833 vs NESDEC's 6,774, +0.9%). PK is held level, so n = 0."""
    scale = ACTUAL_OCT_2026 / NESDEC_PK12[2027]
    out = {n: {} for n in range(14)}
    for y in range(2026, 2041):
        for n in out:
            out[n][y] = 0.0
    out[0][2026], out[0][2027] = ACTUAL_OCT_2025, ACTUAL_OCT_2026
    for y, row in nesdec_grades().items():
        if y <= MIGRATION_FROM:
            continue
        out[0][y] += row[0] * scale
        for gi in range(13):
            out[migration_years(y, gi)][y] += row[gi + 1] * scale
    return out


def enrollment_path(migration=0.0):
    """NESDEC PK-12, scaled to the October 2026 count and extended to FY2040, with families moving in
    changed by `migration` a year (net share of each class, beyond what NESDEC assumes)."""
    parts = enrollment_by_exponent()
    return {y: sum(parts[n][y] * (1 + migration) ** n for n in parts) for y in parts[0]}


def index_path(rate, first_growth_year=2027, rates=None):
    idx, v = {}, 1.0
    for y in YEARS:
        if y >= first_growth_year:
            v *= 1 + (rates.get(y, rate) if rates else rate)
        idx[y] = v
    return idx


def run(a, data, growth_frame):
    """FY2026: the Town's FY2026 budget. FY2027: the budget adopted by Town
    Meeting in May 2026 (fy2027_adopted.py). FY2028 on: FY2027 levels moved by
    the drivers."""
    import fy2027_adopted as A
    tsch, be, bc, gr, fte, hist, sal = data
    T = lambda cat, sub, y: float(tsch[y][(cat, sub)])
    gr = chca_growth_frame(a.get("chca", "approved"))
    g = gr[gr.scenario == a["growth"]].set_index("fiscal_year")
    gt = gr[gr.scenario == "trend_continues"].set_index("fiscal_year")
    chca_on = 0.0 if a.get("chca", "approved") == "in_trend" else 1.0
    Y0 = ANCHOR_YEAR

    ip = lambda rate, rates=None: index_path(rate, first_growth_year=Y0 + 1, rates=rates)
    W = ip(a["pay"])
    Wdep = ip(a["pay"] + a.get("dept_pay_adj", 0.0))
    Wps = ip(a["pay"] + a.get("dept_pay_adj", 0.0) + a["pay_ps_premium"])
    Wsch = ip(a["pay"] + a["school_pay_drift"])
    C = ip(a["cpi"])
    Cnp = ip(a["cpi"] + a["sch_np_extra"])
    prem = ip(a["premium_long"], rates={2028: a["premium_near"], 2029: a["premium_near"]})
    w25 = (1 + a["pay"]) ** (Y0 - 2025)   # FY2025-dollar inputs to FY2027
    ps25 = (1 + a["pay"] + a.get("dept_pay_adj", 0.0) + a["pay_ps_premium"]) ** (Y0 - 2025)

    # ---- growth quantities, counted from FY2028 (the FY2027 budget already
    # serves the town as it is)
    cum = lambda col, frame: (frame[col].cumsum() - frame[col].cumsum().loc[Y0]).clip(lower=0)
    units, units_trend, sqft = cum("implied_res_new_units", g), cum("implied_res_new_units", gt), \
        cum("implied_com_new_sqft", g)
    # real-estate new growth (what building permits are charged on), for planning and
    # permitting staff in scenarios faster than the trend
    RE_NG = ["new_growth_res_new_dollars", "new_growth_res_reno_dollars",
             "new_growth_com_new_dollars", "new_growth_com_reno_dollars"]
    permit_ratio = (g[RE_NG].sum(axis=1) / gt[RE_NG].sum(axis=1)).to_dict()
    import new_growth_scenario_forecast as _ngs
    chca_ramp = {y: chca_on * _ngs.chca_ramp_share(y) for y in YEARS}
    # homes in town each year (FY2025 count plus every home added since), for the fire step
    stock = {y: HOMES_FY2025 + float(g["implied_res_new_units"].loc[:y].sum()) + CHCA_UNITS * chca_ramp[y]
             for y in YEARS}
    fire_step = a.get("fire_step", True)
    police_step = a.get("police_step", False)
    per_home = a["cost_per_home"] * (1 - TOWN_COST_PER_HOME_PS_SHARE * (
        ((1 - PS_SHARE_POLICE) if fire_step else 0.0) + (PS_SHARE_POLICE if police_step else 0.0)))
    restore_n = sum(PS_RESTORE_POSITIONS.values()) if a.get("ps_restore") else 0

    # ---- departmental personnel shares (FY2019 salary shares on FY2025 spend)
    cats = [("General Government", "exp_general_government"), ("Public Safety", "exp_public_safety"),
            ("Public Works", "exp_public_works"), ("Human Services", "exp_human_services"),
            ("Culture & Recreation", "exp_culture_recreation")]
    pers = {c: hist.loc[2025, col] * sal.loc[c, "salary_budget_fy19"] / hist.loc[2019, col]
            for c, col in cats}
    dep25 = sum(hist.loc[2025, col] for _, col in cats)
    pD = sum(pers.values()) / dep25
    psD = pers["Public Safety"] / sum(pers.values())

    town_fte = {y: (fte.loc[2027, "total"] if y >= 2027 else fte.loc[2026, "total"]) for y in YEARS}
    enroll = enrollment_path(a.get("migration", 0.0))
    if a["enroll_mode"] == "cm":
        sc = ACTUAL_OCT_2026 / CM_PK12[2027]
        enroll = {y: (ACTUAL_OCT_2025 if y == 2026 else CM_PK12[min(y, 2034)] * sc) for y in YEARS}
    e0 = enroll[Y0]
    if a["enroll_mode"] == "flat":
        enroll = {y: (enroll[y] if y <= Y0 else e0) for y in YEARS}
    extra = {y: max(units[y] - units_trend[y], 0) * STUDENTS_PER_HOME
             + CHCA_UNITS * chca_ramp[y] * CHCA_STUDENTS_PER_UNIT for y in YEARS}
    E = {y: enroll[y] + extra[y] for y in YEARS}
    staff26 = SCHOOL_STAFF_FY26
    staff0 = staff26 + A.SCHOOL_FTE_CHANGE_FROM_FY26          # FY2027 adopted
    ratio0 = e0 / staff0                                       # FY2027 students per staff
    ratio = {}
    for y in YEARS:
        if a["ratio_mode"] == "partial":
            target = ratio0 + (RATIO_FY2019 - ratio0) / 3
            step = min(max((y - Y0) / 5, 0), 1)
            ratio[y] = ratio0 + (target - ratio0) * step
        else:
            ratio[y] = ratio0
    # "keep": no cuts as the NESDEC decline happens, but students from growth
    # above trend (and CHCA) are still staffed at the FY2027 ratio.
    # "half": total school staff move half as fast as enrollment (the FY2019-25
    # pattern: enrollment -10.6%, staff -5.0%). Only the variable share v moves, so
    # the variable part moves 0.5 / v as fast; students from growth are staffed in full.
    # "fill_capacity" with "half" (2026-10-14): half the decline's seats stay open (staff cover
    # the other half), so students from growth are staffed only beyond those seats.
    # "fill_capacity" (keep mode): students from growth above trend fill the
    # seats the NESDEC decline leaves in classes kept at the FY2027 level, so staff are
    # added only once total enrollment is back above FY2027 (Ben's choice of capacity
    # level, 2026-10-06; FY2027 K-8 classes already had ~945 seats open at the School
    # Committee's class-size guidelines, AdvCom Schools write-up, April 2026).
    if a.get("fill_capacity") and a["ratio_mode"] == "keep":
        staff_var = {y: staff0 + max(E[y] - e0, 0) / ratio0 for y in YEARS}
    elif a.get("fill_capacity") and a["ratio_mode"] == "half":
        staff_var = {y: staff0 + (0.5 / SCHOOL_VARIABLE_SHARE) * min(enroll[y] - e0, 0) / ratio0
                     + max(enroll[y] - e0, 0) / ratio0
                     + max(extra[y] - 0.5 * max(e0 - enroll[y], 0), 0) / ratio0 for y in YEARS}
    elif a["ratio_mode"] == "half":
        # half as fast on the way down only; a rise is staffed as "hold" does (2026-10-14: the
        # FY2019-25 evidence is about a decline, and FY2011-19 staff rose faster than students)
        staff_var = {y: staff0 + extra[y] / ratio0
                     + (0.5 / SCHOOL_VARIABLE_SHARE) * min(enroll[y] - e0, 0) / ratio0
                     + max(enroll[y] - e0, 0) / ratio0 for y in YEARS}
    else:
        staff_var = {y: (staff0 + extra[y] / ratio0 if a["ratio_mode"] == "keep" else E[y] / ratio[y])
                     for y in YEARS}
    # students from growth left unstaffed by fill_capacity; the enrollment index charges them the
    # non-personnel cost per student, and the schools line adds the rest of FILL_SEAT_COST_FY27
    if a.get("fill_capacity") and a["ratio_mode"] == "keep":
        unstaffed = {y: max(min(extra[y], e0 - enroll[y]), 0.0) for y in YEARS}
    elif a.get("fill_capacity") and a["ratio_mode"] == "half":
        unstaffed = {y: min(extra[y], 0.5 * max(e0 - enroll[y], 0.0)) for y in YEARS}
    else:
        unstaffed = {y: 0.0 for y in YEARS}
    fill_add = FILL_SEAT_COST_FY27 - A.SCHOOLS * (1 - SCHOOL_PERSONNEL_SHARE) * SCHOOL_VARIABLE_SHARE / e0
    staff = {y: (staff0 * (1 - SCHOOL_VARIABLE_SHARE) + SCHOOL_VARIABLE_SHARE * staff_var[y])
             * (1 + a.get("school_staff_growth", 0.0)) ** max(y - Y0, 0)
             for y in YEARS}
    staff[2026] = staff26

    ob_town = lambda yy: T("benefits_detail", "total", yy) - sum(
        T("benefits_detail", s_, yy) for s_ in ("pensions", "group_health", "retiree_group_health_opeb"))
    reg = lambda yy: T("expenditure", "nondept_debt_service", yy) - T("revenue", "debt_exclusion", yy)
    fte_tot0 = town_fte[Y0] + staff0
    # payroll of all staff, Town and schools, weighted by FY2027 pay: what payroll-linked benefits
    # (Medicare, workers' compensation, unemployment) follow after FY2031 (2026-10-14; was Town pay)
    w_town, w_sch = A.TOWN_DEPARTMENTS * pD, A.SCHOOLS * SCHOOL_PERSONNEL_SHARE
    payroll = {y: (w_town * (psD * Wps[y] + (1 - psD) * Wdep[y]) * town_fte[y] / town_fte[Y0]
                   + w_sch * Wsch[y] * staff[y] / staff0) / (w_town + w_sch) for y in YEARS if y >= Y0}
    # pensions after FY2031 and the slip setting's installments
    nc_growth = a["pay"] + PENSION_NC_PREMIUM
    pen31 = T("benefits_detail", "pensions", 2031)
    pen_plan = lambda yy: T("benefits_detail", "pensions", yy) if yy <= 2031 else pen31 * (1 + nc_growth) ** (yy - 2031)
    slip = a["pension_slip"]
    nc30 = pen31 / (1 + nc_growth)
    slip_pay = ((T("benefits_detail", "pensions", 2030) - nc30)
                / sum((1 + PENSION_RATE) ** -k for k in range(slip + 1))) if slip else 0.0

    rows = {}
    for y in YEARS:
        if y == 2026:   # the Town's FY2026 budget, for the balanced-budget check
            rows[y] = dict(departmental_base=T("expenditure", "departmental_town", 2026),
                           departmental_growth=0.0, schools=T("expenditure", "schools", 2026),
                           group_health=T("benefits_detail", "group_health", 2026),
                           growth_staff_benefits=0.0, pensions=T("benefits_detail", "pensions", 2026),
                           opeb=T("benefits_detail", "retiree_group_health_opeb", 2026),
                           other_benefits=ob_town(2026), debt_within_levy=reg(2026),
                           other_nondept=float(be.loc[2026, "other_nondept"]),
                           enrollment=E[y], school_staff=staff26, town_fte=town_fte[y],
                           cum_res_units=0.0, cum_com_sqft=0.0, homes_total=stock[y],
                           fire_company=0.0, ps_restore_cost=0.0, ps_added_positions=0.0,
                           police_added=0.0, police_added_cost=0.0,
                           ps_personnel=float("nan"))
            continue
        # town departments
        pay_mix = psD * Wps[y] + (1 - psD) * Wdep[y]
        dep_base = A.TOWN_DEPARTMENTS * (pD * pay_mix * town_fte[y] / town_fte[Y0] + (1 - pD) * C[y])
        emp = sqft[y] / SQFT_PER_EMP + CHCA_EMPLOYEES * chca_ramp[y]
        homes = units[y] + CHCA_UNITS * chca_ramp[y]
        dep_growth = (homes * per_home + emp * RKG_COM_DEPT_PER_EMP_FY25) * w25 * W[y]
        if y > Y0:
            dep_growth += PERMITTING_COST_FY27 * max(permit_ratio[y] - 1, 0) * W[y]
        # a fire company once homes reach the threshold; its cost already carries health
        # insurance, so it takes no benefit loading below
        company = (FIRE_COMPANY_COST_FY25 * ps25 * Wps[y]
                   if fire_step and y > Y0 and stock[y] >= FIRE_COMPANY_HOMES else 0.0)
        restore = restore_n * PS_POSITION_COST_FY25 * ps25 * Wps[y] if y > Y0 else 0.0
        # commitments already agreed (Ben, 2026-10-14): the fire contract's new 5- and 10-year steps
        # from FY2028, and the four police positions still to be refilled, two in FY2028 and two in
        # FY2029 (already counted when police are restored to earlier staffing)
        restore += (FIRE_STEPS_FY28 * Wps[y] / Wps[2028] if y >= 2028 else 0.0) + (
            0.0 if a.get("ps_restore") else
            POLICE_REFILL.get(min(y, 2029), 0) * PS_POSITION_COST_FY25 * ps25 * Wps[y])
        # police kept at the peer ratio, one officer at a time, also health included
        # (against the budget plus the refilled positions, 2026-10-14)
        police_n = (max(np.floor(stock[y] * POLICE_PEER_PER_1000_HOMES / 1000 + 1e-9) - POLICE_BUDGET_FY27
                        - POLICE_REFILL.get(min(y, 2029), 0), 0)
                    if police_step and y > Y0 else 0.0)
        police = police_n * PS_POSITION_COST_FY25 * ps25 * Wps[y]
        dep_base += restore
        dep_growth += company + police
        # schools
        v = SCHOOL_VARIABLE_SHARE
        sch = A.SCHOOLS * (SCHOOL_PERSONNEL_SHARE * Wsch[y] * staff[y] / staff0
                           + (1 - SCHOOL_PERSONNEL_SHARE) * Cnp[y] * ((1 - v) + v * E[y] / e0)) \
            + unstaffed[y] * fill_add * Wsch[y] / Wsch[Y0]
        # group health
        fte_tot = town_fte[y] + staff[y]
        subs = ((1 - HEALTH_RETIREE_COST_SHARE) * fte_tot / fte_tot0
                + HEALTH_RETIREE_COST_SHARE * (1 + RETIREE_GROWTH) ** (y - Y0))
        gh = A.GROUP_HEALTH * subs * prem[y]
        growth_benefits = (dep_growth - company - police) * TOWN_BENEFIT_LOADING
        # pensions: adopted FY2027, Town schedule FY2028-31, then the normal cost growing with payroll
        pen = A.PENSIONS if y == Y0 else pen_plan(y)
        # OPEB
        if y == Y0:
            opeb = A.OPEB
        elif y <= 2030 or (y == 2031 and a["opeb_redirect"]):
            opeb = T("benefits_detail", "retiree_group_health_opeb", min(y, 2031))
        elif a["opeb_redirect"]:
            opeb = T("benefits_detail", "retiree_group_health_opeb", 2031)
        else:
            opeb = T("benefits_detail", "retiree_group_health_opeb", 2030) + 0.25e6 * (y - 2030)
        if slip and 2030 <= y <= 2030 + slip:
            pen_slip = (nc30 if y == 2030 else pen_plan(y)) + slip_pay
            if a["opeb_redirect"]:
                opeb += pen - pen_slip   # the rest of the set-aside goes to retiree health
            pen = pen_slip
        # the liability, rolled forward; the deposit stops once it is paid off
        if y == Y0:
            o_tol, o_a, o_sc, o_b = OPEB_START
        elif y > Y0:
            gm = opeb_trend(y)   # the actuary's trend, not the premium settings (see opeb_trend)
            o_sc *= 1 + gm
            o_b *= (1 + gm) * (1 + RETIREE_GROWTH)
            o_tol = o_tol * (1 + OPEB_RATE) + o_sc - o_b
            o_dep = min(opeb, max(o_tol - o_a * (1 + OPEB_RATE), 0.0))
            # once paid off, the trust is held at the liability (2026-10-14): benefits are paid outside it,
            # so left alone it would overshoot; the premiums it could then pay are not counted as room
            o_a = min(o_a * (1 + OPEB_RATE) + o_dep, o_tol)
            # what the payoff frees is a decision, not room (Ben, 2026-10-15): in the base case the
            # budget keeps the planned deposit after the payoff; opeb_hold=False counts it as room
            if not (a["opeb_hold"] and a["opeb_redirect"]):
                opeb = o_dep
        opeb_net = o_tol - o_a if y >= Y0 else float("nan")
        opeb_held = opeb - o_dep if y > Y0 else 0.0   # planned deposit not needed once paid off
        # other benefits
        if y == Y0:
            oth_b = A.OTHER_BENEFITS
        elif y <= 2031:
            oth_b = ob_town(y)
        else:
            oth_b = ob_town(2031) * payroll[y] / payroll[2031]
        # debt and other non-departmental
        # debt: the Town's capital funding table (FY2027 Financial Plan p.384) through FY2032
        cip_debt = lambda yy: float(be.loc[yy, "debt_service_regular"])
        debt = A.WITHIN_LEVY_DEBT if y == Y0 else (cip_debt(y) if y <= 2032 else cip_debt(2032) * 1.035 ** (y - 2032))
        other = A.OTHER_NONDEPT if y == Y0 else float(be.loc[y, "other_nondept"])
        net_rev = lambda yy: float(g.loc[yy, "total_revenue"] - g.loc[yy, "debt_exclusion_revenue"]
                                   - g.loc[yy, "free_cash"]) - NON_APPROP_FY27 * (1 + NON_APPROP_GROWTH) ** (yy - 2027)
        nd_policy = 0.0
        if y > Y0:   # the non-departmental lines by Town policy, in place of the plan's dollars held flat
            nd_policy += RESERVE_FUND_SHARE * net_rev(y - 1) - T("expenditure", "nondept_reserve_fund", min(y, 2031))
            if y > 2031:
                nd_policy += (NONDEPT_GENERAL_FY31 * (net_rev(y - 1) / net_rev(2030) - 1)
                          + NON_APPROP_FY31 * ((1 + NON_APPROP_GROWTH) ** (y - 2031) - 1))
        other += nd_policy
        # free cash by Town policy (Ben, 2026-10-14): it never pays for the operating budget. What is
        # left after the uses already counted (capital from free cash, the stabilization, liability and
        # housing deposits in general non-departmental, the free cash quarter of the reserve fund) goes
        # to capital up to 8% and to one-time uses, so it is spent here too. A shortfall trims capital.
        fc_left = 0.0
        if a.get("free_cash_policy", True) and y > Y0:
            gen = (T("expenditure", "nondept_general", y) if y <= 2031
                   else NONDEPT_GENERAL_FY31 * net_rev(y - 1) / net_rev(2030))
            fc_left = float(g.loc[y, "free_cash"]) - (float(be.loc[y, "cip_free_cash"])
                                                      + FC_DEPOSIT_SHARE * gen + FC_RESERVE_SHARE * net_rev(y - 1))
            other += fc_left
        # capital at the 6.6% policy from revenue (4.5% debt + 2.1% cash of the prior year's net
        # revenue), the base case from FY2028 (Ben, 2026-10-13: the Financial Plan, p.363, holds
        # the policy at 6% for FY2026-27 only). Off, capital stays at the Town's table's dollars.
        if a.get("capital_full") and y > Y0:
            net_prev = net_rev(y - 1)
            other += max(CIP_POLICY_SHARE * net_prev - debt - float(be.loc[y, "cip_revenue_financed"]), 0)
        rows[y] = dict(departmental_base=dep_base, departmental_growth=dep_growth, schools=sch,
                       group_health=gh, growth_staff_benefits=growth_benefits, pensions=pen,
                       opeb=opeb, other_benefits=oth_b, debt_within_levy=debt, other_nondept=other,
                       nondept_policy=nd_policy, free_cash_left=fc_left, opeb_net_liability=opeb_net, opeb_held=opeb_held,
                       enrollment=E[y], school_staff=staff[y], town_fte=town_fte[y],
                       cum_res_units=units[y], cum_com_sqft=sqft[y], homes_total=stock[y],
                       fire_company=company, ps_restore_cost=restore,
                       police_added=police_n, police_added_cost=police,
                       ps_personnel=A.TOWN_DEPARTMENTS * pD * psD * Wps[y] + restore + company + police,
                       ps_added_positions=(FIRE_COMPANY_FIREFIGHTERS if company else 0) + (restore_n if restore else 0) + police_n)
    df = pd.DataFrame(rows).T
    money = ["departmental_base", "departmental_growth", "schools", "group_health",
             "growth_staff_benefits", "pensions", "opeb", "other_benefits", "debt_within_levy",
             "other_nondept"]
    df["operating_expenditure"] = df[money].sum(axis=1)
    rev = g["total_revenue"] - g["debt_exclusion_revenue"]
    df["operating_revenue"] = rev.reindex(YEARS).to_numpy()
    df["surplus_deficit"] = df.operating_revenue - df.operating_expenditure
    ov = bc[bc.scenario == "trend_corrected"]["may_2026_override_value"].reindex(YEARS).to_numpy()
    df["may_2026_override_value"] = ov
    df["surplus_deficit_ex_override"] = df.surplus_deficit - ov
    return df


def growth_types(data, a):
    """Annual revenue and cost by type of growth, full cost (not net of NESDEC)."""
    tsch, be, bc, gr, fte, hist, sal = data
    import fy2027_adopted as A
    base = run(a, data, None)
    Y0 = ANCHOR_YEAR
    S0, gh0 = A.SCHOOLS, A.GROUP_HEALTH
    e0, staff0 = base.loc[Y0, "enrollment"], base.loc[Y0, "school_staff"]
    ratio0 = e0 / staff0
    fte_tot0 = base.loc[Y0, "town_fte"] + staff0
    W = index_path(a["pay"], first_growth_year=Y0 + 1)
    # schools at school prices, as in run(): school pay and school non-personnel prices (2026-10-14;
    # they had used Town pay and CPI, about 9% low by FY2040)
    Wsch = index_path(a["pay"] + a["school_pay_drift"], first_growth_year=Y0 + 1)
    Cnp = index_path(a["cpi"] + a["sch_np_extra"], first_growth_year=Y0 + 1)
    prem = index_path(a["premium_long"], first_growth_year=Y0 + 1,
                      rates={2028: a["premium_near"], 2029: a["premium_near"]})
    w25 = (1 + a["pay"]) ** (Y0 - 2025)
    out = []
    mode = a.get("chca", "approved")
    gr = chca_growth_frame(mode)
    chca_on = 0.0 if mode == "in_trend" else 1.0
    for scen in gr.scenario.unique():
        g = gr[gr.scenario == scen].set_index("fiscal_year")
        units = g["implied_res_new_units"].cumsum()
        sqft = g["implied_com_new_sqft"].cumsum()
        import new_growth_scenario_forecast as _ngs
        chca_ramp = {y: chca_on * _ngs.chca_ramp_share(y) for y in YEARS}
        for y in YEARS:
            # same basis as the forecast (FY2027 adopted levels)
            per_student = SCHOOL_VARIABLE_SHARE * (
                S0 * SCHOOL_PERSONNEL_SHARE / staff0 / ratio0 * Wsch[y]
                + S0 * (1 - SCHOOL_PERSONNEL_SHARE) / e0 * Cnp[y])
            gh_per_student = (gh0 * (1 - HEALTH_RETIREE_COST_SHARE) / fte_tot0 * prem[y] * SCHOOL_VARIABLE_SHARE / ratio0)
            town_home = a["cost_per_home"] * w25 * W[y] * (1 + TOWN_BENEFIT_LOADING)
            town_emp = RKG_COM_DEPT_PER_EMP_FY25 * w25 * W[y] * (1 + TOWN_BENEFIT_LOADING)

            def rev(col):
                return sum(g.loc[s, col] * LEVY_GROWTH ** (y - s) for s in YEARS if s <= y)

            types = {
                "New residential units": (rev("new_growth_res_new_dollars"),
                                          units[y] * (town_home + STUDENTS_PER_HOME * (per_student + gh_per_student))),
                "Residential renovation": (rev("new_growth_res_reno_dollars"), 0.0),
                "New commercial space": (rev("new_growth_com_new_dollars"),
                                         sqft[y] / SQFT_PER_EMP * town_emp),
                "Commercial renovation": (rev("new_growth_com_reno_dollars"), 0.0),
                "Personal property": (rev("new_growth_com_personal_property_dollars"), 0.0),
                "Chestnut Hill (CHCA)": (g.loc[y, "chca_property_tax_dollars"]
                                         + chca_on * _ngs.chca_local_receipts(y, CHCA_REVENUE[mode][1]),
                                         chca_ramp[y] * (CHCA_UNITS * (town_home + CHCA_STUDENTS_PER_UNIT
                                                                       * (per_student + gh_per_student))
                                                         + CHCA_EMPLOYEES * town_emp)),
            }
            for t, (r, c) in types.items():
                out.append(dict(growth_scenario=scen, fiscal_year=y, growth_type=t,
                                annual_revenue=round(r), annual_cost=round(c), net=round(r - c)))
    return pd.DataFrame(out)


def marginal_student_cost(data, a=None):
    """Cost of one added student, component by component, FY2027 dollars, and a
    numerical check against the full model (add 100 students, difference out).

    In the model an added student brings:
      staff      SCHOOL_VARIABLE_SHARE / (FY2027 students per staff) positions
                 (0.67 / 5.55 = 0.121, one position per 8.3 students), each at FY2027
                 school personnel cost per staff member (school budget x personnel
                 share / staff)
      non-pers.  the enrollment-linked share of non-personnel spending per pupil
                 (school budget x (1 - personnel share) / enrollment x 0.67)
      health     the active-staff share of FY2027 group health cost per FTE,
                 times the added positions
      other      payroll-linked benefits (Medicare etc.), from the model check
    """
    a = a or BASE
    tsch = data[0]
    import fy2027_adopted as A
    Y0 = ANCHOR_YEAR
    S26, gh26 = A.SCHOOLS, A.GROUP_HEALTH          # FY2027 adopted levels
    base = run(a, data, None)
    e26, staff26 = base.loc[Y0, "enrollment"], base.loc[Y0, "school_staff"]
    fte_tot26 = base.loc[Y0, "town_fte"] + staff26
    pos = SCHOOL_VARIABLE_SHARE / (e26 / staff26)
    cost_per_staff = S26 * SCHOOL_PERSONNEL_SHARE / staff26
    comp = {
        "positions per added student": pos,
        "salary cost per position": cost_per_staff,
        "staff": pos * cost_per_staff,
        "non-personnel": S26 * (1 - SCHOOL_PERSONNEL_SHARE) / e26 * SCHOOL_VARIABLE_SHARE,
        "health insurance": gh26 * (1 - HEALTH_RETIREE_COST_SHARE) / fte_tot26 * pos,
    }
    # numerical check: 100 more students once CHCA is fully ramped (FY2034)
    global CHCA_STUDENTS_PER_UNIT
    orig = CHCA_STUDENTS_PER_UNIT
    CHCA_STUDENTS_PER_UNIT = orig + 100 / CHCA_UNITS
    try:
        bump = run(a, data, None)
    finally:
        CHCA_STUDENTS_PER_UNIT = orig
    nominal = {y: (bump.loc[y, "operating_expenditure"] - base.loc[y, "operating_expenditure"]) / 100
               for y in (2034, 2040)}
    school_nominal = {y: (bump.loc[y, "schools"] - base.loc[y, "schools"]) / 100 for y in (2034, 2040)}
    # deflate FY2034 school line to FY2026 with the model's own indices
    W = index_path(a["pay"] + a["school_pay_drift"], first_growth_year=Y0 + 1)
    C = index_path(a["cpi"] + a["sch_np_extra"], first_growth_year=Y0 + 1)
    # (each component already includes its personnel / non-personnel share)
    school_fy26_from_model = school_nominal[2034] / (
        (W[2034] * comp["staff"] + C[2034] * comp["non-personnel"])
        / (comp["staff"] + comp["non-personnel"]))
    comp["other payroll-linked benefits"] = max(
        nominal[2034] - school_nominal[2034]
        - (bump.loc[2034, "group_health"] - base.loc[2034, "group_health"]) / 100, 0) / W[2034]
    comp["total"] = comp["staff"] + comp["non-personnel"] + comp["health insurance"] \
        + comp["other payroll-linked benefits"]
    comp["average school budget per pupil"] = S26 / e26
    comp["check: school line from model, FY2027 $"] = school_fy26_from_model
    comp["model, nominal FY2034"] = nominal[2034]
    comp["model, nominal FY2040"] = nominal[2040]
    return comp


def main():
    data = load()
    tsch, be, bc, gr, fte, hist, sal = data
    base = run(BASE, data, None)

    print("=" * 78)
    print("CONTROLS")
    print("=" * 78)
    # 1. FY2026 equals the Town's FY2026 operating budget
    town26 = float(tsch[2026][("expenditure", "total_expenditure")]) - float(tsch[2026][("revenue", "debt_exclusion")])
    gap = base.loc[2026, "operating_expenditure"] - base.loc[2026, "departmental_growth"] \
        - base.loc[2026, "growth_staff_benefits"] - town26
    print(f"  {'PASS' if abs(gap) < 1e5 else 'FAIL'}  FY2026 before growth equals the Town's FY2026 "
          f"operating budget: ${town26/1e6:.2f}M (gap ${gap:,.0f})")
    import fy2027_adopted as A
    adopted_op = A.TOTAL_EXPENDITURES - A.EXCLUDED_DEBT_SERVICE
    gap27 = base.loc[2027, "operating_expenditure"] - adopted_op
    print(f"  {'PASS' if abs(gap27) < 5 else 'FAIL'}  FY2027 equals the budget adopted by Town Meeting, "
          f"operating basis: ${adopted_op/1e6:.2f}M (gap ${gap27:,.0f})")
    # 2. sum-to-total
    money = ["departmental_base", "departmental_growth", "schools", "group_health",
             "growth_staff_benefits", "pensions", "opeb", "other_benefits", "debt_within_levy",
             "other_nondept"]
    st = (base[money].sum(axis=1) - base.operating_expenditure).abs().max()
    print(f"  {'PASS' if st < 1 else 'FAIL'}  lines sum to operating expenditure every year")
    # 3. one dial at a time moves only its lines
    alt = run(dict(BASE, premium_long=BASE["premium_long"] + 0.02), data, None)
    moved = [c for c in money if (alt[c] - base[c]).abs().max() > 1]
    print(f"  {'PASS' if moved == ['group_health'] else 'FAIL'}  changing the health premium "
          f"moves only {moved}")
    alt = run(dict(BASE, cost_per_home=1109), data, None)
    moved = [c for c in money if (alt[c] - base[c]).abs().max() > 1]
    print(f"  {'PASS' if set(moved) == {'departmental_growth', 'growth_staff_benefits'} else 'FAIL'}  "
          f"changing cost per home moves only {moved}")
    # 4. backcast: the method with perfect foresight of drivers, from the tree
    tree = pd.read_csv(TREE)
    res = tree[tree.group == "Pay & costs above/below inflation"].groupby("block")["dollars"].sum()
    print("  Backcast (tree run FY2011-25 with actual drivers, no leftover):")
    for blk, act in (("Town departments", 84.62e6), ("Schools", 146.45e6)):
        r = res.get(blk, 0)
        print(f"    {blk:18s} predicted ${(act - r)/1e6:6.1f}M vs actual ${act/1e6:6.1f}M "
              f"({-r/act:+.1%})")
    print()

    # 5. FY2027 against the Town's LRFP
    recon = []
    print("=" * 78)
    print("FY2027 AND FY2031 AGAINST THE TOWN'S OWN SCHEDULE")
    print("=" * 78)
    for y in (2027, 2031):
        mine = dict(departmental_town=base.loc[y, ["departmental_base", "departmental_growth"]].sum(),
                    schools=base.loc[y, "schools"],
                    benefits=base.loc[y, ["group_health", "growth_staff_benefits", "pensions", "opeb",
                                          "other_benefits"]].sum())
        for k, sub, cat in (("departmental_town", "departmental_town", "expenditure"),
                            ("schools", "schools", "expenditure"),
                            ("benefits", "nondept_benefits", "expenditure")):
            t = float(tsch[y][(cat, sub)])
            print(f"  FY{y} {k:18s} driver ${mine[k]/1e6:7.2f}M  Town ${t/1e6:7.2f}M  "
                  f"({mine[k]/t-1:+.1%})")
            recon.append(dict(fiscal_year=y, line=k, driver_forecast=round(mine[k]),
                              compare_to="Town LRFP", compare_value=round(t)))
    print()

    # 6. against the existing trend_corrected forecast
    print("=" * 78)
    print("AGAINST THE EXISTING trend_corrected FORECAST (operating basis)")
    print("=" * 78)
    for y in (2030, 2035, 2040):
        tc = bc.loc[y]
        tc = tc[tc.scenario == "trend_corrected"] if isinstance(tc, pd.DataFrame) else tc
        te = float(tc["operating_expenditure"].iloc[0] if isinstance(tc, pd.DataFrame) else tc["operating_expenditure"])
        print(f"  FY{y}: driver ${base.loc[y,'operating_expenditure']/1e6:7.1f}M  "
              f"trend_corrected ${te/1e6:7.1f}M  ({base.loc[y,'operating_expenditure']/te-1:+.1%})")
        recon.append(dict(fiscal_year=y, line="operating_expenditure",
                          driver_forecast=round(base.loc[y, "operating_expenditure"]),
                          compare_to="trend_corrected", compare_value=round(te)))
    b40 = be.loc[2040]
    cmp = [("Town departments", base.loc[2040, ["departmental_base", "departmental_growth"]].sum(), b40.departmental_town),
           ("Schools", base.loc[2040, "schools"], b40.schools),
           ("Benefits", base.loc[2040, ["group_health", "growth_staff_benefits", "pensions", "opeb",
                                        "other_benefits"]].sum(), b40.benefits),
           ("Within-levy debt", base.loc[2040, "debt_within_levy"], b40.debt_service_regular),
           ("Other non-dept", base.loc[2040, "other_nondept"], b40.other_nondept)]
    print("  FY2040 by line:")
    for k, mine, tc in cmp:
        print(f"    {k:18s} driver ${mine/1e6:7.1f}M  trend_corrected ${tc/1e6:7.1f}M  "
              f"diff ${(mine-tc)/1e6:+7.1f}M")
        recon.append(dict(fiscal_year=2040, line=k, driver_forecast=round(mine),
                          compare_to="trend_corrected", compare_value=round(tc)))
    print()

    # ------------------------------------------------------------ base result
    print("=" * 78)
    print("BASE CASE")
    print("=" * 78)
    for y in (2026, 2027, 2030, 2031, 2035, 2040):
        r = base.loc[y]
        print(f"  FY{y}: spending ${r.operating_expenditure/1e6:6.1f}M  revenue "
              f"${r.operating_revenue/1e6:6.1f}M  balance ${r.surplus_deficit/1e6:+6.1f}M "
              f"({r.surplus_deficit/r.operating_revenue:+.1%}), ex-override ${r.surplus_deficit_ex_override/1e6:+6.1f}M  "
              f"enrollment {r.enrollment:,.0f}  "
              f"school staff {r.school_staff:,.0f}")
    print()

    # ------------------------------------------------------------- sensitivity
    dials = [
        ("Capital held at the Town's capital table, about 6% (base: the 6.6% policy from FY2028)", dict(capital_full=False)),
        ("Pay growth +1 point for every group (base: Town 3.0%, schools 3.7%, Public Safety 3.5%)", dict(pay=0.04)),
        ("Pay growth -0.5 point for every group (Town 2.5%, schools 3.2%, Public Safety 3.0%)", dict(pay=0.025)),
        ("School staff follow enrollment down, ratio held (base: half as fast as enrollment)", dict(ratio_mode="hold")),
        ("School staff follow enrollment and ratio moves a third back to FY2019", dict(ratio_mode="partial")),
        ("School staff held at the FY2027 level as enrollment falls (base: half as fast, the FY2019-25 pattern)", dict(ratio_mode="keep")),
        ("Students from new homes fill existing seats until enrollment is back to FY2027 (base: staffed at the FY2027 ratio)", dict(fill_capacity=True)),
        ("New growth at the peer rate, housing-led, students fill existing seats", dict(growth="peer_target_residential_led", fill_capacity=True)),
        ("Enrollment flat at FY2027 (base: NESDEC decline)", dict(enroll_mode="flat")),
        ("Enrollment per Cropper-McKibben, the schools' forecast (base: NESDEC)", dict(enroll_mode="cm")),
        ("Families moving in: each class 0.35 point a year larger, the rate since COVID (base: NESDEC's rate)", dict(migration=0.0035)),
        ("Families moving in: each class 1 point a year larger (base: NESDEC's rate)", dict(migration=0.01)),
        ("Families moving in: each class 0.5 point a year smaller (base: NESDEC's rate)", dict(migration=-0.005)),
        ("Cropper-McKibben enrollment, staff follow it", dict(enroll_mode="cm", ratio_mode="hold")),
        ("School pay at PSB's forecast, about 5%/yr (base 3.7%)", dict(school_pay_drift=0.02)),
        ("School and Public Safety pay held to the 3.0% Town target (base 3.7% and 3.5%)", dict(school_pay_drift=0.0, pay_ps_premium=0.0)),
        ("Health premiums 6.5%/yr from FY2030 (base 8%)", dict(premium_long=0.065)),
        ("Health premiums 10%/yr from FY2030 (base 8%)", dict(premium_long=0.10)),
        ("Health premiums 4.5%/yr from FY2030, the actuary's long-run trend (base 8%)", dict(premium_long=0.045)),
        ("School non-personnel costs at inflation +2 points (base: inflation, 2.5%)", dict(sch_np_extra=0.02)),
        ("Inflation 3.5%/yr (base 2.5%)", dict(cpi=0.035)),
        ("Town cost per new home $1,109, RKG, with police and fire growing with every home (base $660 and a fire company step)", dict(cost_per_home=1109, fire_step=False)),
        ("Town cost per new home $230 (base $660)", dict(cost_per_home=230)),
        ("New growth at the peer rate, housing-led (base: recent trend)", dict(growth="peer_target_residential_led")),
        ("New growth at the peer rate, commercial-led (base: trend)", dict(growth="peer_target_commercial_led")),
        ("New growth at the peer rate, even mix (base: trend)", dict(growth="peer_target_balanced_mix")),
        ("Half the expected new homes built; renovation and commercial growth at trend", dict(growth="trend_homes_half")),
        ("No new homes built; renovation and commercial growth at trend", dict(growth="trend_homes_none")),
        ("Pension full funding slips 2 years (base: FY2030)", dict(pension_slip=2)),
        ("CHCA at City Realty average revenue (base: approved program)", dict(chca="cr_avg")),
        ("CHCA at RKG's revenue estimate", dict(chca="rkg")),
        ("CHCA already inside trend growth (not additive)", dict(chca="in_trend")),
        ("Pension savings not moved to OPEB in FY2031", dict(opeb_redirect=False)),
        ("Money freed by the retiree health payoff counted as room (base: held for a decision)", dict(opeb_hold=False)),
        ("Police and fire restored to earlier staffing, police 136 and fire 168 (base: FY2027 budget, 128 and 160)", dict(ps_restore=True)),
        ("No added fire company (base: a company at about 31,200 homes)", dict(fire_step=False)),
        ("Police grow with homes at the peer ratio, 4.42 officers per 1,000 homes (base: held at 128)", dict(police_step=True)),
    ]
    b40 = base.loc[2040]
    tor = []
    print("=" * 78)
    print(f"SENSITIVITY, FY2040 (base spending ${b40.operating_expenditure/1e6:.1f}M, "
          f"balance ${b40.surplus_deficit/1e6:+.1f}M)")
    print("=" * 78)
    for label, over in dials:
        full = run(dict(BASE, **over), data, None)
        r = full.loc[2040]
        ds = r.operating_expenditure - b40.operating_expenditure
        db = r.surplus_deficit - b40.surplus_deficit
        cum = (full.surplus_deficit - base.surplus_deficit).sum()
        print(f"  {label:50s} FY40 spending {ds/1e6:+7.1f}M  balance {db/1e6:+7.1f}M  "
              f"15-yr balance {cum/1e6:+8.1f}M")
        tor.append(dict(dial=label, fy2040_spending=round(r.operating_expenditure),
                        spending_change=round(ds), fy2040_balance=round(r.surplus_deficit),
                        balance_change=round(db), cumulative_balance_change_fy26_40=round(cum),
                        # FY2035 too, so the decisions chart can show timing beside FY2040 (2026-10-15)
                        balance_change_fy2035=round(full.loc[2035, "surplus_deficit"] - base.loc[2035, "surplus_deficit"])))
    print()

    ps = public_safety_projection(data, base)
    first = ps[(ps.scenario == "base") & (ps.fire_companies_added > 0)].fiscal_year
    print(f"  Fire company threshold {FIRE_COMPANY_HOMES:,.0f} homes: base case reaches it in "
          f"{('FY' + str(int(first.min()))) if len(first) else 'no year to FY2040'}; FY2040 homes "
          f"{base.loc[2040, 'homes_total']:,.0f}")
    no_step = run(dict(BASE, fire_step=False), data, None)
    d = (base.operating_expenditure - no_step.operating_expenditure)
    print(f"  Public safety change vs no step and the full $660: FY2040 spending {d.loc[2040]/1e6:+.2f}M")
    ps.to_csv(OUT_PS, index=False)
    print()

    msc = marginal_student_cost(data)
    print("=" * 78)
    print("COST OF ONE ADDED STUDENT (FY2027 dollars unless noted)")
    print("=" * 78)
    for k, v in msc.items():
        print(f"  {k:42s} {v:>12,.3f}" if k.startswith("positions") else f"  {k:42s} ${v:>11,.0f}")
    ok = abs(msc["check: school line from model, FY2027 $"] - (msc["staff"] + msc["non-personnel"])) < 1
    print(f"  {'PASS' if ok else 'FAIL'}  components match the full model's school line")
    print()
    with open(OUT / "marginal_cost_per_student.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["component", "value", "basis"])
        for k, v in msc.items():
            w.writerow([k, round(v, 4 if k.startswith("positions") else 0),
                        "nominal" if k.startswith("model, nominal") else "FY2027 dollars"])

    types = growth_types(data, BASE)
    print("=" * 78)
    print("GROWTH BY TYPE, FY2040, trend_continues (annual $)")
    print("=" * 78)
    t40 = types[(types.fiscal_year == 2040) & (types.growth_scenario == "trend_continues")]
    for _, r in t40.iterrows():
        print(f"  {r.growth_type:24s} revenue ${r.annual_revenue/1e6:6.2f}M  cost "
              f"${r.annual_cost/1e6:6.2f}M  net ${r.net/1e6:+6.2f}M")
    print()

    # --------------------------------------------------------------- write
    base.index.name = "fiscal_year"
    base.round(0).to_csv(OUT_LINES)
    pd.DataFrame(tor).to_csv(OUT_TORNADO, index=False)
    types.to_csv(OUT_TYPES, index=False)
    pd.DataFrame(recon).to_csv(OUT_RECON, index=False)
    births_basis(base).to_csv(OUT_BIRTHS, index=False)
    print(f"wrote {OUT_LINES.name}, {OUT_TORNADO.name}, {OUT_TYPES.name}, {OUT_RECON.name}")


def public_safety_projection(data, base):
    """Police and fire positions and personnel cost by year, for the base case, the
    restore lever and the peer-pace growth scenario. Positions are budgeted (funded)
    positions; the department can run below them, and the difference returns as free cash."""
    import fy2027_adopted as A
    runs = {"base": base,
            "restore_earlier_staffing": run(dict(BASE, ps_restore=True), data, None),
            "police_grow_with_homes": run(dict(BASE, police_step=True), data, None),
            "peer_pace_growth": run(dict(BASE, growth="peer_target_balanced_mix"), data, None)}
    W = index_path(BASE["pay"] + BASE["pay_ps_premium"], first_growth_year=ANCHOR_YEAR + 1)
    rows = []
    for name, df in runs.items():
        for y in YEARS:
            if y < ANCHOR_YEAR:
                continue
            r = df.loc[y]
            company = 1 if r.fire_company > 0 else 0
            # ps_restore_cost also carries the agreed fire steps and police refills, so test the scenario
            restored = name == "restore_earlier_staffing"
            refill = POLICE_REFILL.get(min(y, 2029), 0)
            rows.append(dict(
                scenario=name, fiscal_year=y, homes_total=round(r.homes_total),
                police_sworn=POLICE_BUDGET_FY27 + (PS_RESTORE_POSITIONS["police"] if restored else refill)
                + int(r.police_added),
                firefighters=FIRE_BUDGET_FY27 + (PS_RESTORE_POSITIONS["fire"] if restored else 0)
                + FIRE_COMPANY_FIREFIGHTERS * company,
                fire_companies_added=company,
                personnel_cost=round(r.ps_personnel), fire_company_cost=round(r.fire_company),
                restore_cost=round(r.ps_restore_cost), police_added_cost=round(r.police_added_cost),
                fire_overtime_budget=round(FIRE_OVERTIME_FY27 * W[y]
                                           + (FIRE_COMPANY_OVERTIME_FY25 * W[y] * (1 + BASE["pay"] + BASE["pay_ps_premium"])
                                              ** (ANCHOR_YEAR - 2025) if company else 0)),
                basis=f"Budgeted positions: police {POLICE_BUDGET_FY27} sworn and fire {FIRE_BUDGET_FY27} in the FY2027 budget; "
                      "personnel cost is the Public Safety share of Town department payroll grown at Public Safety "
                      f"pay ({BASE['pay'] + BASE['pay_ps_premium']:.1%}), plus "
                      f"the fire company once homes reach {FIRE_COMPANY_HOMES:,.0f}, the agreed fire steps and police refills (or the "
                      "restored positions), and any officers added "
                      f"to hold {POLICE_PEER_PER_1000_HOMES} per 1,000 homes; fire "
                      "overtime is the FY2027 budget plus override grown with pay, and the company's own overtime"))
    return pd.DataFrame(rows)


def births_basis(base):
    """Enrollment per birth: PK-12 enrollment over the births of the 13 years whose children are in
    K-12 (born y-18 to y-6). Rows for the schools page's table and the enrollment comparison."""
    b = pd.read_csv(OUT / "brookline_resident_births.csv").set_index("year")["resident_births"].to_dict()
    b.update(BIRTHS_ACTUAL)
    births = lambda y: b.get(y, BIRTHS_AHEAD)
    pool = lambda fy: sum(births(y) for y in range(fy - 18, fy - 5))
    hist_e = pd.read_csv(OUT / "school_enrollment_staffing_fy05_25.csv").set_index("fiscal_year")["total_enrollment"]
    today = float(hist_e[2025]) / pool(2025)                    # FY2025, the last DESE year in the series
    peak = sum(float(hist_e[fy]) / pool(fy) for fy in range(2016, 2020)) / 4   # FY2016-19, the 2010s peak
    rows = [dict(item="births_ahead", value=BIRTHS_AHEAD), dict(item="pool_fy2025", value=pool(2025)),
            dict(item="pool_fy2027", value=pool(2027)), dict(item="pool_fy2034", value=pool(2034)),
            dict(item="pool_fy2040", value=pool(2040)), dict(item="per_birth_today", value=today),
            dict(item="per_birth_peak", value=round(peak, 2)),
            dict(item="per_birth_base_fy2040", value=float(base.loc[2040, "enrollment"]) / pool(2040)),
            dict(item="per_birth_level_fy2040", value=ACTUAL_OCT_2026 / pool(2040)),
            dict(item="per_birth_cm_fy2034", value=CM_PK12[2034] / pool(2034))]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
