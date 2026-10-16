"""General Fund utilities spending, FY2006-FY2027, against Boston-area inflation.

Utilities for school buildings are paid on the Town side of the budget (the School Department's
budget has no utilities line; the FY2027 Financial Plan's budget message lists "utility use" among the
School costs the Town carries), so this line covers all Town and school buildings plus
streetlights and the other departments.

Sources, all Town Financial Plans in data/:
  FY2006-FY2018 actuals: "Recommended Operating Budget Summary - Totals by Expenditure
    Classification", Utilities row; each year from the latest plan that reports it as an actual
    (FY2010, FY2014, FY2016, FY2018, FY2019 and FY2020 plans).
  FY2018: the FY2020 plan's table labels its actual columns FY2016-FY2018, but its first two
    values repeat the FY2018 plan's FY2015-FY2016 actuals, so the labels look shifted. The FY2018
    figure is read from the column before the FY2019 budget; treat it as less certain.
  FY2019-FY2022: no plan prints a General Fund total, so each is the sum of the OpenGov
    department-group tables (Administration & Finance, Public Safety, Public Works, Cultural,
    Human and Leisure Services, Schools) in the plan two years later. FY2019 (FY2021 plan, p.II-4
    to II-5) and FY2020 (FY2022 plan, pp.5-7) groups include enterprise and revolving funds, so
    water and sewer (FY2019 only), golf and recreation-revolving utilities are subtracted, from
    those funds' summaries in the FY2022 plan (pp.8-10). FY2021 (FY2023 plan, pp.44-46) and
    FY2022 (FY2024 plan, pp.55-57) groups are General Fund only. Check: the same method
    reproduces the General Fund budget totals printed in the FY2021, FY2022 and FY2024 plans
    to within $2,000. FY2019 has no Schools utilities line (about $62,000 in FY2020).
  FY2023-FY2024 actuals and FY2025-FY2027 budgets: "General Fund" by-category tables of the
    FY2025, FY2026 and FY2027 plans.
Writes output/utilities_history.csv. Boston CPI-U (BLS CUURA103SA0), fiscal-year averages.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ACTUAL = {2006: 3958631, 2007: 4547667, 2008: 4756101, 2009: 4983079, 2010: 4706602,
          2011: 4988426, 2012: 4925165, 2013: 5021550, 2014: 5201588, 2015: 5117633,
          2016: 4752138, 2017: 4284239, 2018: 4391645,
          2019: 1708 + 3158481 + (1217989 - 111321) + 239434 + 105720 + (340017 - 72532 - 88198),
          2020: 833 + 2746626 + 1025420 + 231841 + 90171 + (324799 - 82573 - 96325) + 61941,
          2021: 471 + 3144650 + 1026123 + 212221 + 78290 + 142463 + 6046,
          2022: 741 + 3751761 + 1063469 + 260885 + 93197 + 164754 + 7329,
          2023: 5952331, 2024: 5701380}
BUDGET = {2025: 6242063, 2026: 6350445, 2027: 6971238}
SOURCE = {**{y: "Financial Plan expenditure-classification summary, actual" for y in range(2006, 2018)},
          2018: "FY2020 Financial Plan, actual (column labels look shifted)",
          2019: "FY2021 Financial Plan department groups, less enterprise and revolving funds",
          2020: "FY2022 Financial Plan department groups, less golf and recreation revolving",
          2021: "FY2023 Financial Plan department groups (General Fund)",
          2022: "FY2024 Financial Plan department groups (General Fund)",
          2023: "FY2025 Financial Plan, General Fund by category, actual",
          2024: "FY2026 Financial Plan, General Fund by category, actual",
          2025: "FY2026 Financial Plan, budget", 2026: "FY2026 Financial Plan, recommended",
          2027: "FY2027 Financial Plan, General Fund by fund and category, budget"}

c = pd.read_csv(ROOT / "data" / "bls_cache" / "CUURA103SA0.csv", parse_dates=["observation_date"]).dropna()
c["fy"] = c.observation_date.dt.year + (c.observation_date.dt.month >= 7)
cpi = c.groupby("fy").CUURA103SA0.mean()

rows = [{"fiscal_year": y, "utilities": v, "basis": "actual" if y in ACTUAL else "budget",
         "boston_cpi_fy_avg": round(cpi.get(y, float("nan")), 1), "source": SOURCE[y]}
        for y, v in sorted({**ACTUAL, **BUDGET}.items())]
pd.DataFrame(rows).to_csv(ROOT / "output" / "utilities_history.csv", index=False)


def cagr(a, b, x, y):
    return (y / x) ** (1 / (b - a)) - 1


for a, b in [(2006, 2024), (2011, 2024), (2011, 2019), (2019, 2024), (2021, 2024)]:
    print(f"FY{a}-FY{b}: utilities {cagr(a, b, ACTUAL[a], ACTUAL[b]):+.1%} a year, "
          f"Boston CPI {cagr(a, b, cpi[a], cpi[b]):+.1%}")
print(f"FY2024 actual to FY2027 budget: {cagr(2024, 2027, ACTUAL[2024], BUDGET[2027]):+.1%} a year")
for r in (0.04, 0.06):   # forecast grows non-staff costs 2.5% a year
    print(f"utilities at {r:.0%} from FY2027: FY2040 ${BUDGET[2027] * ((1 + r) ** 13 - 1.025 ** 13) / 1e6:.1f}M worse")
