"""
FY2027 budget as adopted by the May 26, 2026 Annual Town Meeting (Article 8),
after the May 5, 2026 operating override passed.

Source: "Reports of Select Board and Advisory Committee, Combined Reports, May 26,
2026 Annual Town Meeting", FY2027 BUDGET - TABLE 1 MAY 2026, "FY27 FINAL BUDGET"
column (data/Combined-Reports-May-2026-ATM.pdf; Town DocumentCenter View/62447).
The Advisory Committee recommended Favorable Action 22-0-0.

The February FY2027 Financial Plan was a no-override budget (Town departments
$101.26M, School Department $144.53M), so it is not the budget being spent.

The driver forecast (expense_driver_forecast.py) uses these as its FY2027 levels
and applies drivers from FY2028. The revenue forecasts use the FY2027 free cash,
other available funds and budgeted local receipts, which the adopted budget fixes.
"""

# Expenditures
TOWN_DEPARTMENTS = 103_486_124      # "Subtotal Town"
SCHOOLS = 149_801_900               # School Department (School Committee)
PENSIONS = 41_167_421
GROUP_HEALTH = 46_364_204
OPEB = 4_931_980
TOTAL_EMPLOYEE_BENEFITS = 99_123_428
OTHER_BENEFITS = TOTAL_EMPLOYEE_BENEFITS - PENSIONS - GROUP_HEALTH - OPEB
BORROWING = 49_425_313              # all debt service, excluded and within-levy
SUBTOTAL_GENERAL = 15_614_820       # reserves, stabilization, insurance, audit; includes
                                    # the new Override Stabilization Fund ($3,568,303)
OVERRIDE_STABILIZATION_FUND = 3_568_303
# Assumed drawn down evenly over the three following budgets to smooth the override's
# phase-in (Ben, 2026-09-29: "I believe that's how it is intended to be used"; not
# confirmed in Town documents). Added to other available funds in FY2028-2030.
OVERRIDE_STABILIZATION_DRAW = {y: OVERRIDE_STABILIZATION_FUND / 3 for y in (2028, 2029, 2030)}
SPECIAL_APPROPRIATIONS = 22_409_889  # revenue-financed capital
NON_APPROPRIATED = 10_792_034
TOTAL_EXPENDITURES = 450_668_508

# Revenues
PROPERTY_TAXES = 359_304_829        # includes the override and debt exclusions
LOCAL_RECEIPTS = 37_633_556         # budgeted
STATE_AID = 26_693_757
FREE_CASH = 18_280_805
OTHER_AVAILABLE_FUNDS = 8_755_561
TOTAL_REVENUE = 450_668_507

# School staffing change in the adopted budget: "22.1 net fewer FTE than FY26"
# (FY27-29 PSB budget summary, data/psb_budget/FY27-29_PSB_budget_summary.pdf).
SCHOOL_FTE_CHANGE_FROM_FY26 = -22.1

# Excluded debt service in FY2027 (FY2027 Financial Plan debt table; also the
# Town's FY27-31 LRFP): the within-levy share of BORROWING is the remainder.
EXCLUDED_DEBT_SERVICE = 35_379_833
WITHIN_LEVY_DEBT = BORROWING - EXCLUDED_DEBT_SERVICE
VOCATIONAL_EDUCATION = 15_000
OTHER_NONDEPT = SUBTOTAL_GENERAL + SPECIAL_APPROPRIATIONS + NON_APPROPRIATED + VOCATIONAL_EDUCATION

assert abs((TOWN_DEPARTMENTS + SCHOOLS + 15_000 + TOTAL_EMPLOYEE_BENEFITS + BORROWING
            + SUBTOTAL_GENERAL + SPECIAL_APPROPRIATIONS + NON_APPROPRIATED) - TOTAL_EXPENDITURES) < 5, \
    "FY2027 lines must add to the adopted total (the $15,000 is the non-school education line)"
