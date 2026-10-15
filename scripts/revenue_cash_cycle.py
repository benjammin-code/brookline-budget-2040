"""
The local-receipts / free-cash cycle, modeled the way the Town's books work.

Brookline budgets local receipts deliberately below what it expects to collect.
Actual collections ran $11-15M a year above the budget estimate in FY2022-25.
That excess, plus unspent appropriations and other revenue beating estimates,
is the year-end General Fund surplus, which the state certifies as free cash
and the Town appropriates in the budget two years later.

So in any year the Town's usable revenue includes:
  - this year's BUDGETED receipts (not actual collections), and
  - free cash from the surplus of TWO years earlier, which contains that
    year's excess receipts. The lag is two years: a year's surplus is
    certified the following July 1 and appropriated in the budget adopted the
    spring after (Brookline budget FY = DLS free-cash FY + 1; see
    reserves_and_free_cash_methodology.md). The FY2024 surplus ($24.4M) funded
    $21.3M of the FY2026 budget; the FY2025 surplus ($25.3M) funded $20.2M of
    FY2027. The rest stays in reserves.

An earlier version of the trend_corrected revenue forecast counted this year's
ACTUAL receipts and also the Town's free cash figure, so each year's excess was
counted twice: once as receipts and again in the next year's free cash. Check
that exposed it: FY2026 is an adopted balanced budget, and that version showed a
$13.2M surplus, nearly all of it the $12.1M receipts excess. (Ben Chostner's
framing, 2026-09-29: last year's excess should flow into this year's free cash.)

Parameters, both measured from the Town's own actuals
(brookline_historical_financials_fy05_25.csv, DLS Local Receipts Actual vs
Estimate and certified surplus):
  BUDGET_RATIO        budget estimate / actual receipts, FY2025 (the Town's
                      current practice; FY2022-25 range 0.68-0.75 raw), measured
                      with investment income at its flat forecast level
                      (see parameters())
  OTHER_SURPLUS_SHARE year-end surplus not explained by excess receipts, as a
                      share of that year's total revenue, FY2022-25 average.
                      Measured against Schedule A total revenues (taxes, state
                      aid, actual receipts and transfers in; no free cash), so it
                      is applied to the same total: property tax, state aid,
                      other available funds and ACTUAL receipts (2026-10-14; it
                      had been applied to a total with budgeted receipts and
                      free cash)
  APPROPRIATED_SHARE  free cash appropriated / surplus two years earlier,
                      FY2026-27 budgets (the rest is left in reserves)
"""

import csv
from pathlib import Path

HIST = Path(__file__).parent.parent / "output" / "brookline_historical_financials_fy05_25.csv"
KNOWN_FREE_CASH_YEARS = (2026, 2027)   # certified / budgeted by the Town already
# FY2027 as adopted by Town Meeting (fy2027_adopted.py) replaces the January LRFP
# figure for that year; budgeted receipts are also fixed by the adopted budget.
import fy2027_adopted as _fy27
ADOPTED_FREE_CASH = {2027: _fy27.FREE_CASH}
ADOPTED_BUDGETED_RECEIPTS = {2027: _fy27.LOCAL_RECEIPTS}


INVESTMENT_INCOME_EST_2025 = 790_593   # DLS itemized receipts, FY2025 estimate (brookline_local_receipts_detail_fy17_25.csv)


def parameters():
    with open(HIST) as f:
        h = {int(r["fiscal_year"]): r for r in csv.DictReader(f)}
    fl = lambda y, c: float(h[y][c])
    # Investment income is forecast flat (new_growth_scenario_forecast.INVESTMENT_INCOME_FLAT,
    # Ben 2026-10-14), so the ratio is measured with FY2025's interest swapped for that flat
    # level on both sides. Raw FY2025, $5.1M of interest collected against $0.8M budgeted
    # pulled the ratio down to 74.4%; applied to receipts without that interest it would
    # understate the budget and overstate free cash. On this basis it is 82.7%.
    import new_growth_scenario_forecast as ngs
    inv_flat = ngs.INVESTMENT_INCOME_FLAT
    ratio = ((fl(2025, "local_receipts_est_total") - INVESTMENT_INCOME_EST_2025 + inv_flat)
             / (fl(2025, "local_receipts_act_total") - ngs.INVESTMENT_INCOME_2025 + inv_flat))
    shares = []
    for y in range(2022, 2026):
        excess = fl(y, "local_receipts_act_total") - fl(y, "local_receipts_est_total")
        shares.append((fl(y, "general_fund_surplus") - excess) / fl(y, "rev_total_revenues"))
    town = {}
    with open(Path(__file__).parent.parent / "output" / "town_own_forecast_fy26_31.csv") as f:
        for r in csv.DictReader(f):
            if r["subcategory"] == "free_cash":
                town = {int(k): float(v) for k, v in r.items() if k.isdigit()}
    # FY2027 as adopted ($18.28M), not the January plan's $20.2M (2026-10-14)
    appr = [ADOPTED_FREE_CASH.get(y, town[y]) / fl(y - 2, "general_fund_surplus") for y in (2026, 2027)]
    return ratio, sum(shares) / len(shares), sum(appr) / len(appr)


BUDGET_RATIO, OTHER_SURPLUS_SHARE, APPROPRIATED_SHARE = parameters()


def _town_budgeted_receipts(year):
    with open(Path(__file__).parent.parent / "output" / "town_own_forecast_fy26_31.csv") as f:
        for r in csv.DictReader(f):
            if r["category"] == "revenue" and r["subcategory"] == "local_receipts":
                return float(r[str(year)])


# FY2026's budgeted receipts are fixed by its adopted budget too (the Town plan's FY2026
# column), so the adopted-budget control does not depend on the receipts forecast.
ADOPTED_BUDGETED_RECEIPTS[2026] = _town_budgeted_receipts(2026)


def apply(years, actual_receipts, town_free_cash, total_before_receipts_and_free_cash):
    """Return (budgeted_receipts, free_cash) dicts.

    actual_receipts: {year: forecast actual collections}
    town_free_cash: {year: Town figure} (used for KNOWN_FREE_CASH_YEARS)
    total_before_receipts_and_free_cash: {year: property tax + state aid +
        other available funds}, used to size last year's total revenue.
    """
    budgeted, free_cash, surplus = {}, {}, {}
    for y in years:
        budgeted[y] = ADOPTED_BUDGETED_RECEIPTS.get(y, actual_receipts[y] * BUDGET_RATIO)
        if y in KNOWN_FREE_CASH_YEARS or (y - 2) not in surplus:
            free_cash[y] = ADOPTED_FREE_CASH.get(y, town_free_cash[y])
        else:
            free_cash[y] = APPROPRIATED_SHARE * surplus[y - 2]
        revenues = total_before_receipts_and_free_cash[y] + actual_receipts[y]   # Schedule A basis
        surplus[y] = (actual_receipts[y] - budgeted[y]) + OTHER_SURPLUS_SHARE * revenues
    return budgeted, free_cash


if __name__ == "__main__":
    print(f"BUDGET_RATIO {BUDGET_RATIO:.3f}, OTHER_SURPLUS_SHARE {OTHER_SURPLUS_SHARE:.4f}, "
          f"APPROPRIATED_SHARE {APPROPRIATED_SHARE:.3f}")
