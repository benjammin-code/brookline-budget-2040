"""
The cost of growth, in one place.

One set of per-home, per-employee and per-student costs shared by the town-wide
driver forecast (expense_driver_forecast.py), the per-project calculator
(per_project_fiscal_impact.py) and the per-home breakeven test
(housing_unit_breakeven.py). Before 2026-09-29 the per-project calculator used
RKG's average-cost figures ($1,371 a home, $15,572 a student) grown at hardcoded
trend rates, while the forecast used its own, so the two disagreed by
construction (README item 6).

The models stay separate: a project's impact is not summed into the forecast,
because town-wide the levy is the input and the tax rate the output. What is
shared is the inputs.

Sources:
  Town services per home   $660 (FY2025 $) of Town department cost,
                           cross_town_marginal_cost.py (350 towns, range $230 to
                           $1,109), plus benefits at RKG's ratio ($262 per
                           $1,109), grown with Town pay (3%, the Town's target)
  Town services per        RKG's $219 per commercial employee, department share
    commercial employee    only ($1,109 / $1,371), plus the same benefit loading
  Cost per added student   the driver forecast's marginal cost:
                           marginal_cost_per_student.csv (FY2027 $16,236; model
                           nominal FY2034 and FY2040), log-linear between points
  Full average per pupil   DESE all-in, FY2024 $26,683, grown 3%/yr (alternative)
  Children per home        0.2442 per forecast new home (RKG bedroom schedule for a known unit
                           mix); the forecast adds apartments and condominiums, not age-restricted
                           homes (new_homes_parameters.py)
"""

import csv
from pathlib import Path

_OUT = Path(__file__).parent.parent / "output"

PAY = 0.03                                   # Town pay target, base case
TOWN_COST_PER_HOME_FY25 = 660.0
TOWN_COST_PER_HOME_RANGE_FY25 = (230.0, 1_109.0)
TOWN_BENEFIT_LOADING = 262.0 / 1_109.0
TOWN_COST_PER_EMPLOYEE_FY25 = 219.0 * (1_109.0 / 1_371.0)

# Planning and permitting staff (added 2026-10-07). FY2027 recommended General Fund
# budgets (FY2027 Financial Plan): Planning & Community Development $1,384,996, Building
# Code Enforcement $892,085, Building Administration $316,790. Building's other divisions
# maintain Town and school buildings and are left out. Growth scenarios faster than the
# trend add this cost in proportion to the extra real-estate new growth, as building
# permit revenue already does; slower growth does not cut it.
PERMITTING_COST_FY27 = 1_384_996 + 892_085 + 316_790
# Public safety (added 2026-10-10, Ben). The town-wide forecast models police and fire
# explicitly instead of through the per-home charge:
#   - The cross-town estimate puts about $234 of the $663 per home in public safety
#     (cross_town_marginal_cost_methodology.md, growth-rate form). The forecast drops that
#     share from the per-home charge and adds fire in steps instead, so growth is not
#     charged twice. The per-project calculator and the per-home test keep the full $660,
#     the smoothed equivalent of the steps for a single project.
#   - A new fire company when homes reach the level at which Brookline's 161 firefighters
#     (2020, the date of the peer counts; 160 in the FY2027 budget) per 1,000 homes falls to the median of 21 nearby cities and towns (5.16, 2020 Census
#     homes, public_safety_staffing_peers.csv): 161 / 5.16 x 1,000 = about 31,200 homes.
#     Cost: the Fire Department's own costing of a South Brookline ladder company, 20
#     firefighters at $123,639 (health included, pension excluded) plus $565,512 of overtime
#     at current leave rates, $3,038,292 a year (FY24-25 Fire overtime and leave memo,
#     revised 2025-03-11, p.7), taken as FY2025 dollars. The ladder truck ($1.5-2M) is capital.
#   - Restoring staffing to earlier budgeted levels, an Explorer lever: police from 128 sworn
#     (FY2027) to 136 (FY2018-20) and fire from 160 (FY2027) to 168 (FY2004), 16 positions at the
#     memo's $123,639 each.
#   - Police (Ben, 2026-10-11): no police step in the base case. Police calls fell about 4% a
#     year FY2016-24 and Brookline's 128 officers (FBI 2019; also the FY2027 budget) per 1,000
#     homes, 4.58, is near the same peers' median of 4.42 (19 of the 21 report), so the peer test
#     gives no separate threshold. The base case instead keeps police's part of the $234 in the
#     per-home charge and drops only fire's part. The split follows RKG's FY2025 per-household
#     figures for Brookline, police $448 and fire $532 (cross_town_marginal_cost_methodology.md):
#     police about $107, fire about $127.
#   - Police growing with homes, an Explorer lever: officers kept at the peer median of 4.42 per
#     1,000 homes once Brookline's 128 falls to it (about 29,000 homes), one officer at a time,
#     each at the memo's $123,639; the per-home charge then drops police's part too.
#   Housing stock: 28,718 homes in FY2025 (public_safety_workload_fy03_25.csv, 2020 Census
#   plus about 151 a year), the same basis as the peer comparison.
TOWN_COST_PER_HOME_PS_SHARE = 234.0 / 663.0
HOMES_FY2025 = 28_718
FIRE_COMPANY_HOMES = round(161 / 5.16 * 1000, -2)
FIRE_COMPANY_FIREFIGHTERS = 20
FIRE_COMPANY_COST_FY25 = 3_038_292
PS_POSITION_COST_FY25 = 123_639
POLICE_BUDGET_FY27 = 128
FIRE_BUDGET_FY27 = 160
FIRE_COMPANY_OVERTIME_FY25 = 565_512   # the company's own overtime, inside FIRE_COMPANY_COST_FY25
PS_RESTORE_POSITIONS = {"police": 136 - POLICE_BUDGET_FY27, "fire": 168 - FIRE_BUDGET_FY27}
PS_SHARE_POLICE = 448.0 / (448.0 + 532.0)      # police part of the public safety share
POLICE_PEER_PER_1000_HOMES = 4.42
SQFT_PER_EMPLOYEE = 200.0
import json as _json
STUDENTS_PER_HOME = _json.loads((_OUT / "new_homes_parameters.json").read_text())["students_per_home_blended"]
AVERAGE_STUDENT_COST_FY24 = 26_682.66
RKG_SAC_TIERS = [(0, 0.0), (1, 0.0), (2, 0.25), (3, 0.35)]


def _student_path():
    with open(_OUT / "marginal_cost_per_student.csv") as f:
        rows = {r["component"]: float(r["value"]) for r in csv.DictReader(f)}
    return {2027: rows["total"], 2034: rows["model, nominal FY2034"],
            2040: rows["model, nominal FY2040"]}


STUDENT_COST = _student_path()


def student_cost(year, growth=None):
    """Marginal cost of one added student in `year`, nominal dollars: the driver
    forecast's own path, or a constant growth rate from FY2027 if given."""
    if growth is not None:
        return STUDENT_COST[2027] * (1 + growth) ** (year - 2027)
    pts = sorted(STUDENT_COST)
    a, b = (pts[0], pts[1]) if year <= pts[1] else (pts[1], pts[2])
    return STUDENT_COST[a] * (STUDENT_COST[b] / STUDENT_COST[a]) ** ((year - a) / (b - a))


def average_student_cost(year):
    return AVERAGE_STUDENT_COST_FY24 * 1.03 ** (year - 2024)


def town_cost_per_home(year, per_home_fy25=TOWN_COST_PER_HOME_FY25, pay=PAY):
    return per_home_fy25 * (1 + TOWN_BENEFIT_LOADING) * (1 + pay) ** (year - 2025)


def town_cost_per_employee(year, pay=PAY):
    return TOWN_COST_PER_EMPLOYEE_FY25 * (1 + TOWN_BENEFIT_LOADING) * (1 + pay) ** (year - 2025)


def children_for_bedrooms(bedrooms):
    """RKG's bedroom-tiered school-age children per unit, interpolated, with the
    2BR-to-3BR slope extended beyond 3BR."""
    if bedrooms <= 0:
        return 0.0
    if bedrooms >= 3:
        return 0.35 + (bedrooms - 3) * (0.35 - 0.25)
    for (x0, y0), (x1, y1) in zip(RKG_SAC_TIERS, RKG_SAC_TIERS[1:]):
        if x0 <= bedrooms <= x1:
            return y0 + (y1 - y0) * (bedrooms - x0) / (x1 - x0)


if __name__ == "__main__":
    for y, v in STUDENT_COST.items():
        assert abs(student_cost(y) - v) < 0.5, "student cost path misses its own points"
    for y in (2026, 2027, 2034, 2040):
        print(f"FY{y}: town services/home ${town_cost_per_home(y):,.0f}, per employee "
              f"${town_cost_per_employee(y):,.0f}, added student ${student_cost(y):,.0f}, "
              f"full average ${average_student_cost(y):,.0f}")
