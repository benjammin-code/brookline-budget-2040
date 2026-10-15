"""What building permits already say about the next few years of new growth.

Taxable building permits (estimated cost, summed once per permit, by calendar year issued, on parcels
that are not mostly tax-exempt on the FY2025 roll: Town schools, fire stations, churches and the like
add no new growth) against the REAL ESTATE part of the certified new growth valuation three fiscal
years later. Business equipment (personal property) is part of certified new growth but is not built
under building permits, so it is taken out: its new growth tax for FY2022-FY2025 is the Board of
Assessors' share of the prior levy limit (classification hearings, as in new_growth_scenario_forecast),
turned into value at that year's commercial rate (commercial new growth tax over value, DLS); FY2026
is the hearing's own figure ($50,570,310 of value, $837,444 of tax). Fit: permits 2019-2023 against
real estate new growth FY2022-FY2026 (DLS new growth, data/2026 MA state new growth for all towns 20
years.xlsx). Applied to the permits since, that gives expected real estate new growth for FY2027 and
FY2028, compared with the base case's real estate new growth (its total less business equipment, which
keeps its own trend in both).

New growth is taxed at the prior year's rate; the conversion uses FY2026's ratio of real estate new
growth tax to value. The effect on the base case is the levy those dollars carry forward (2.5% a year),
FY2027 and FY2028 only, with new growth returning to the trend after that.

Writes output/permit_leading_indicator.json and .csv."""
import json
import statistics
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "output"
FIT_YEARS = range(2019, 2024)      # permit years whose new growth (FY2022-26) has a business-equipment split
PP_SHARE_OF_PRIOR_LIMIT = {2022: 0.002374, 2023: 0.002164, 2024: 0.002629, 2025: 0.002011}
PP_FY2026 = (50_570_310, 837_444)  # value, tax: FY2026 classification hearing, slide 6


def main():
    f = pd.read_csv(DATA / "permits_cache" / "foia_joined.csv", low_memory=False).drop_duplicates("RECORD ID")
    f["d"] = pd.to_datetime(f["DATE ISSUED"], errors="coerce")
    f["c"] = pd.to_numeric(f["Estimated Cost"], errors="coerce").fillna(0)
    roll = pd.read_csv(ROOT / "land-value-map/output/parcel_history_fy17_25.csv")
    r25 = roll[roll.fy == 2025].groupby("block_lot")[["tot_value", "exm_value"]].sum()
    exempt = set(r25[r25.exm_value > 0.5 * r25.tot_value].index)
    f["taxable"] = ~f.block_lot.isin(exempt)
    last = f.d.max()

    ng = pd.read_excel(DATA / "2026 MA state new growth for all towns 20 years.xlsx", sheet_name="data", header=None)
    ng = ng[ng[1].astype(str).str.strip() == "Brookline"]
    col = lambda k: pd.Series(ng[k].astype(float).values, index=ng[2].astype(int).values)
    val, applied, res_val, res_app, py_limit = col(5), col(6), col(3), col(4), col(8)
    pp_val, pp_tax = {2026: PP_FY2026[0]}, {2026: PP_FY2026[1]}
    for fy, sh in PP_SHARE_OF_PRIOR_LIMIT.items():
        com_rate = (applied[fy] - res_app[fy]) / (val[fy] - res_val[fy])
        pp_tax[fy] = sh * py_limit[fy]
        pp_val[fy] = pp_tax[fy] / com_rate
    re_val = {fy: val[fy] - pp_val[fy] for fy in pp_val}

    rows = []
    for y in range(2018, last.year + 1):
        a = f[f.d.dt.year == y]
        rows.append(dict(permit_year=y, all_permits=a.c.sum(), exempt_permits=a[~a.taxable].c.sum(),
                         taxable_permits=a[a.taxable].c.sum(), new_growth_fy=y + 3,
                         certified_valuation=val.get(y + 3), business_equipment=pp_val.get(y + 3),
                         real_estate_valuation=re_val.get(y + 3), partial_year=(y == last.year)))
    t = pd.DataFrame(rows)
    fit = t[t.permit_year.isin(FIT_YEARS)]
    ratios = (fit.real_estate_valuation / fit.taxable_permits).tolist()
    med, lo, hi = statistics.median(ratios), min(ratios), max(ratios)

    import new_growth_scenario_forecast as ngs
    import expense_driver_forecast as edf
    g = edf.chca_growth_frame("approved")
    g = g[g.scenario == "trend_continues"].set_index("fiscal_year")
    cols = ["new_growth_res_new_dollars", "new_growth_res_reno_dollars", "new_growth_com_new_dollars",
            "new_growth_com_reno_dollars", "new_growth_com_personal_property_dollars"]
    base_ng = g[cols[:4]].sum(axis=1)                      # real estate only; business equipment keeps its trend
    conv = (applied[2026] - pp_tax[2026]) / re_val[2026]   # tax per dollar of real estate new growth, FY2026
    out = dict(last_permit=str(last.date()), ratio_median=round(med, 3), ratio_min=round(lo, 3),
               ratio_max=round(hi, 3), conversion_fy2026=round(conv, 6), fit_years=[min(FIT_YEARS), max(FIT_YEARS)],
               certified=dict(fy=2026, valuation=float(val[2026]), applied=float(applied[2026]),
                              real_estate_valuation=float(re_val[2026]),
                              business_equipment_share={str(k): round(pp_val[k] / val[k], 3) for k in pp_val},
                              pct_of_prior_limit=round(float(applied[2026] / py_limit[2026]), 4)),
               years={})
    for fy in (2027, 2028):
        tx = float(t.loc[t.new_growth_fy == fy, "taxable_permits"].iloc[0])
        e = {k: tx * r for k, r in (("mid", med), ("low", lo), ("high", hi))}
        base = float(base_ng[fy])
        out["years"][str(fy)] = dict(taxable_permits=tx, expected_valuation=e,
                                     expected_applied={k: v * conv for k, v in e.items()},
                                     base_applied=base, base_valuation=base / conv,
                                     shortfall={k: base - v * conv for k, v in e.items()})
    # carried forward at 2.5% a year to FY2028 and FY2040
    for k in ("mid", "low", "high"):
        s27, s28 = out["years"]["2027"]["shortfall"][k], out["years"]["2028"]["shortfall"][k]
        out.setdefault("effect_fy2028", {})[k] = s27 * 1.025 + s28
        out.setdefault("effect_fy2040", {})[k] = s27 * 1.025 ** 13 + s28 * 1.025 ** 12
    ytd = t[t.partial_year]
    if len(ytd):
        days = (last - pd.Timestamp(year=last.year, month=1, day=1)).days + 1
        out["partial_year"] = dict(year=int(ytd.permit_year.iloc[0]), taxable_to_date=float(ytd.taxable_permits.iloc[0]),
                                   annualized=float(ytd.taxable_permits.iloc[0]) * 365 / days)
    t.to_csv(OUT / "permit_leading_indicator.csv", index=False)
    (OUT / "permit_leading_indicator.json").write_text(json.dumps(out, indent=1))
    y = out["years"]
    print(f"real estate ratio {med:.2f} ({lo:.2f}-{hi:.2f}); FY2027 expected ${y['2027']['expected_valuation']['mid']/1e6:.0f}M "
          f"vs base ${y['2027']['base_valuation']/1e6:.0f}M; FY2028 ${y['2028']['expected_valuation']['mid']/1e6:.0f}M "
          f"vs ${y['2028']['base_valuation']/1e6:.0f}M; FY2040 effect ${out['effect_fy2040']['mid']/1e6:.1f}M "
          f"(${out['effect_fy2040']['high']/1e6:.1f}M-${out['effect_fy2040']['low']/1e6:.1f}M)")


if __name__ == "__main__":
    main()
