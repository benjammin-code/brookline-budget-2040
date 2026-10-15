"""
Reference document Part 4 support: on the driver forecast (expense_driver_forecast.py),
how much more new growth, or how much slower spending growth, would close the FY2040
balance without the May 2026 override's revenue.

This replaces base_case_decomposition.py's break-even solve, which ran on the older
trend_corrected forecast. Nothing is reimplemented: each trial adds a scenario to
new_growth_scenario_forecast through its EXTRA_SCENARIOS hook and reruns the real
driver model. Growth costs come with it: added homes bring the $660 town cost and
their students, so a housing-led lift has to be larger than a renovation-led one.

Channels solved (each a sustained lift in new growth, % of prior-year levy):
  renovation   residential renovation only (no added service cost)
  proportional all five categories scaled together (the trend mix)
  housing      new residential units only

Also reported: the uniform cut in annual spending growth from FY2028 that closes the
same gap, and the path of the balance under each solve.

Run from `scripts/`:  python3 driver_forecast_breakeven.py
"""

import csv
from pathlib import Path

import expense_driver_forecast as edf
import new_growth_scenario_forecast as ngs

OUT = Path(__file__).parent.parent / "output" / "driver_forecast_breakeven.csv"
Y = 2040
TREND = (ngs.TREND_RES_NEW_PCT, ngs.TREND_RES_RENO_PCT, ngs.TREND_COM_NEW_PCT,
         ngs.TREND_COM_RENO_PCT, ngs.TREND_COM_PP_PCT)
T_TOTAL = sum(TREND)


def params(channel, lift):
    rn, rr, cn, cr, pp = TREND
    if channel == "renovation":
        return (rn, rr + lift, cn, cr, pp)
    if channel == "housing":
        return (rn + lift, rr, cn, cr, pp)
    k = (T_TOTAL + lift) / T_TOTAL
    return tuple(x * k for x in TREND)


def run_with(channel, lift, data):
    ngs.EXTRA_SCENARIOS = {"solve": {"params": params(channel, lift), "label": "solve"}}
    edf._GROWTH_CACHE.clear()
    try:
        return edf.run(dict(edf.BASE, growth="solve"), data, None)
    finally:
        ngs.EXTRA_SCENARIOS = {}
        edf._GROWTH_CACHE.clear()


def bisect(f, lo, hi, iters=40):
    flo = f(lo)
    for _ in range(iters):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    data = edf.load()
    base = edf.run(edf.BASE, data, None)
    # control: a zero lift reproduces the base case
    ctrl = run_with("proportional", 0.0, data)
    assert abs(ctrl.loc[Y, "surplus_deficit"] - base.loc[Y, "surplus_deficit"]) < 1, "control failed"
    gap = base.loc[Y, "surplus_deficit_ex_override"]
    print(f"Base FY{Y}: with override ${base.loc[Y,'surplus_deficit']/1e6:+.1f}M, "
          f"without its revenue ${gap/1e6:+.1f}M; trend new growth {T_TOTAL:.3%}/yr")
    rows = []
    for ch in ("renovation", "proportional", "housing"):
        # with no FY2040 gap to close (2026-10-14: once retiree health is paid off), no lift is needed
        lift = (bisect(lambda x: run_with(ch, x, data).loc[Y, "surplus_deficit_ex_override"], 0.0, 0.03)
                if gap < 0 else 0.0)
        # what a tenth of a point of added growth through this channel is worth in FY2040, run directly
        # and averaged over the lift to the peer rate (2026-10-15): costs come in steps, and a single
        # tenth through housing alone crosses the fire company step (about 31,200 homes) in FY2039,
        # which made the first tenth alone read as a loss of $3.8M while the full lift gains $6.0M
        peer_lift = ngs.PEER_TARGET_PCT - T_TOTAL
        tenth = ((run_with(ch, peer_lift, data).loc[Y, "surplus_deficit"] - base.loc[Y, "surplus_deficit"])
                 / (peer_lift / 0.001))
        df = run_with(ch, lift, data)
        low_y = df.surplus_deficit_ex_override.loc[2028:].idxmin()
        homes = df.cum_res_units.loc[Y] - base.cum_res_units.loc[Y]
        print(f"  {ch:12s} lift {lift*100:+.3f} pt -> total {T_TOTAL+lift:.3%}/yr; "
              f"extra homes by FY{Y} {homes:,.0f}; lowest ex-override year FY{low_y} "
              f"${df.surplus_deficit_ex_override.loc[low_y]/1e6:+.1f}M")
        rows.append(dict(solve=f"new growth via {ch}", lift_pct_points=round(lift * 100, 4),
                         total_new_growth_pct=round((T_TOTAL + lift) * 100, 4),
                         extra_homes_by_fy2040=round(homes), fy2040_per_tenth=round(tenth), lowest_year=int(low_y),
                         lowest_balance_ex_override=round(df.surplus_deficit_ex_override.loc[low_y]),
                         **{f"ex_override_fy{y}": round(df.surplus_deficit_ex_override.loc[y])
                            for y in (2028, 2029, 2031, 2035, 2040)}))
    # spending growth: uniform cut from FY2028 that closes the FY2040 gap
    sp = base.operating_expenditure
    n = Y - edf.ANCHOR_YEAR
    g0 = (sp.loc[Y] / sp.loc[edf.ANCHOR_YEAR]) ** (1 / n) - 1
    g1 = ((sp.loc[Y] + gap) / sp.loc[edf.ANCHOR_YEAR]) ** (1 / n) - 1
    rev_x = base.operating_revenue - base.may_2026_override_value
    r0 = (rev_x.loc[Y] / rev_x.loc[edf.ANCHOR_YEAR]) ** (1 / n) - 1
    print(f"  spending growth FY{edf.ANCHOR_YEAR}-{Y}: {g0:.3%}/yr; closing the gap needs {g1:.3%} "
          f"({(g1-g0)*100:+.3f} pt). Revenue without the override grows {r0:.3%}/yr "
          f"(wedge {(g0-r0)*100:.3f} pt)")
    rows.append(dict(solve="spending growth cut", lift_pct_points=round((g1 - g0) * 100, 4),
                     total_new_growth_pct="", extra_homes_by_fy2040="", fy2040_per_tenth="", lowest_year="",
                     lowest_balance_ex_override="",
                     **{f"ex_override_fy{y}": "" for y in (2028, 2029, 2031, 2035, 2040)}))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
