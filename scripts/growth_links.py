"""Do new homes drive the budget? Five tests of how growth reaches revenue and costs.

    python3 scripts/growth_links.py

Written 2026-10-11 for the topic page "What new homes do to the budget, year by year"
(docs/site/pages/topic-growth-links.md). Each test answers one link a project-by-project
fiscal estimate assumes, using what actually happened:

  1. Revenue. Permitted construction cost (Town permit export, deduped on RECORD ID, every
     permit type) by calendar year against DOR certified new growth valuation three fiscal
     years later (see revenue()). Only the current permit system (mid-2017 on) carries a
     cost; the legacy export (2006-2017) has none, and permit counts do not track new growth
     (r about 0 over 16 years), so the town-wide fit rests on six permit years. The
     parcel-level check (parcel_timing()) is the better timing evidence: hundreds of jobs,
     each followed through the January 1 assessments after its permit.
  2. Town services. Homes against budgeted police and fire (Public Safety) and other Town
     department positions (expense_drivers_fte_panel_fy04_27.csv) and school staff (DESE),
     FY2010-FY2025. Homes are real counts only at the 2010 and 2020 Censuses; no annual count
     of all homes exists before FY2017, so the line between is drawn as an estimate. From the
     FY2017 roll on, the assessors record units per parcel; assessor_units() cleans them.
  3. Brookline enrollment. Kindergartners (DESE, district, by school year) against resident
     births five years earlier, and new housing units authorized (Census Bureau Building
     Permits Survey, annual place files with imputation, calendar years).
  4. Children per added home, across Massachusetts. Census 2010 and 2020 (PL 94-171): change
     in residents under 18 against change in housing units, for towns with 2,000+ homes.
     Growth-rate form (each town one observation), as in the cross-town spending test.
  5. Home sales. Arm's-length sales ($100,000 or more) of single-family homes and condos,
     from the sale date on every assessment roll FY2009-FY2026 (FY2022's sheet has no header
     row and is skipped; a home sold twice between the FY2021 and FY2023 rolls loses one
     sale). Against kindergartners per birth, same calendar year.

Read the limits in the methodology note before quoting a number from tests 4 and 5.
"""
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "output"
SALES_CACHE = DATA / "permits_cache" / "assessment_roll_sales.csv"

G = ["k_cnt"] + [f"g{i}_cnt" for i in range(1, 13)]


def ols(y, X, w=None):
    """Least squares with heteroskedasticity-robust (HC1) standard errors."""
    y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(y))] + [np.asarray(c, float) for c in X])
    w = np.ones(len(y)) if w is None else np.asarray(w, float)
    sw = np.sqrt(w)
    b = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]
    e = y - X @ b
    n, k = X.shape
    A = np.linalg.inv((X * w[:, None]).T @ X)
    S = (X * (w * e)[:, None]).T @ (X * (w * e)[:, None])
    se = np.sqrt(np.diag(A @ S @ A) * n / (n - k))
    return b, se


# ---------------------------------------------------------------- 1. revenue
def revenue():
    """Massachusetts values property as of January 1 before each fiscal year, and new growth is
    the value added since the previous January 1. So permits issued in calendar year y are
    built during y and y+1, valued on January 1 of y+2, and taxed as new growth in FY y+3,
    which begins in July of y+2. Of every 12-, 24- and 36-month window tested against that
    January 1 date (2026-10-11), the calendar year three fiscal years ahead gave the steadiest
    ratio; the fiscal-year alignments are kept in `fit` for comparison.
    Taxable property only (2026-10-12): permits on parcels mostly tax-exempt on the FY2025 roll
    (Town schools and fire stations, churches, colleges) add no new growth, and 2025's include
    the new Pierce School, so they are left out (as in permit_leading_indicator.py)."""
    f = pd.read_csv(DATA / "permits_cache" / "foia_joined.csv", low_memory=False).drop_duplicates("RECORD ID")
    r25 = pd.read_csv(ROOT / "land-value-map" / "output" / "parcel_history_fy17_25.csv")
    r25 = r25[r25.fy == 2025].groupby("block_lot")[["tot_value", "exm_value"]].sum()
    f = f[~f.block_lot.isin(set(r25[r25.exm_value > 0.5 * r25.tot_value].index))]
    d = pd.to_datetime(f["DATE ISSUED"], errors="coerce")
    c = pd.to_numeric(f["Estimated Cost"], errors="coerce")
    cy = c.groupby(d.dt.year).sum()
    fy = c.groupby(d.dt.year + (d.dt.month >= 7)).sum()
    ng = pd.read_excel(DATA / "2026 MA state new growth for all towns 20 years.xlsx", sheet_name="data", header=None)
    ng = ng[ng[1].astype(str).str.strip() == "Brookline"]
    ngv = pd.Series(ng[5].astype(float).values, index=ng[2].astype(int).values)   # total new growth valuation

    def stats(cost, years, lag):
        z = pd.DataFrame({"c": cost.reindex(years).values, "v": ngv.reindex([y + lag for y in years]).values}).dropna()
        q = z.v / z.c
        return dict(r=round(float(z.c.corr(z.v)), 2), n=len(z), ratio_median=round(float(q.median()), 2),
                    ratio_min=round(float(q.min()), 2), ratio_max=round(float(q.max()), 2))
    # calendar 2017 is half a year (the current system starts 2017-06); 2026 is not complete
    cal_years = list(range(2018, 2026))
    fit = {"calendar_plus3": stats(cy, cal_years, 3),
           "fiscal_plus1": stats(fy, list(range(2018, 2027)), 1),
           "fiscal_plus2": stats(fy, list(range(2018, 2027)), 2)}
    med = fit["calendar_plus3"]["ratio_median"]
    rows = []
    for y in cal_years:
        v = ngv.get(y + 3, np.nan)
        rows.append(dict(permit_calendar_year=y, permitted_cost=float(cy[y]), new_growth_fiscal_year=y + 3,
                         new_growth_valuation=float(v),
                         expected_from_permits=float(cy[y] * med) if np.isnan(v) else np.nan))
    return pd.DataFrame(rows), fit


def parcel_timing():
    """When a permitted job reaches the assessment roll, parcel by parcel. Parcels with exactly
    one building permit of $250,000 or more (2017-2025), issued July 2017 to December 2022 so
    at least two January 1 assessments follow; values FY2009-FY2026 net of the median growth
    of parcels with no permit of $20,000 or more. The FY2026 value (January 1, 2025) is taken
    as the job's full lift; a job counts as visible when that lift exceeds 10% of the value
    before the permit. Share of the lift on the first, second and third January 1 after issue,
    and the split by half of the year issued."""
    f = pd.read_csv(DATA / "permits_cache" / "foia_joined.csv", low_memory=False).drop_duplicates("RECORD ID")
    f["d"] = pd.to_datetime(f["DATE ISSUED"], errors="coerce")
    f["c"] = pd.to_numeric(f["Estimated Cost"], errors="coerce").fillna(0)
    f = f[f.block_lot.notna()]
    h = pd.read_csv(ROOT / "land-value-map" / "output" / "parcel_full_history_fy09_26.csv")
    v = h.pivot_table(index="block_lot", columns="fy", values="tot_value")
    quiet = v.index.difference(f.block_lot[f.c >= 20_000].unique())
    idx = (v.loc[quiet] / v.loc[quiet].shift(axis=1)).median().fillna(1).cumprod()
    big = f[f["RECORD TYPE"].isin(["Residential Building", "Commercial Building"]) & (f.c >= 250e3)]
    one = big.groupby("block_lot").size()
    cases = big[big.block_lot.isin(one[one == 1].index) & (big.d >= "2017-07-01") & (big.d < "2023-01-01")]
    rows = []
    for r in cases.itertuples():
        if r.block_lot not in v.index:
            continue
        s = v.loc[r.block_lot]
        f0 = r.d.year + 1                     # the last January 1 before the permit is valued for FY year+1
        if pd.isna(s.get(f0)) or s[f0] <= 0 or pd.isna(s.get(2026)):
            continue
        lift = s / idx * idx[f0] - s[f0]
        row = dict(block_lot=r.block_lot, issued=r.d.date(), record_type=r._2, permitted_cost=r.c,
                   value_before=s[f0], lift_fy2026=round(lift[2026]))
        for k in (1, 2, 3):
            row[f"share_jan1_{k}"] = round(lift[f0 + k] / lift[2026], 3) if lift[2026] > 0 else np.nan
        rows.append(row)
    z = pd.DataFrame(rows)
    z["visible"] = z.lift_fy2026 > 0.1 * z.value_before
    vis = z[z.visible].copy()
    vis["first_half_year"] = pd.to_datetime(vis.issued).dt.month <= 6
    def k50(r):
        return next((k for k in (1, 2, 3) if r[f"share_jan1_{k}"] >= 0.5), 4)
    vis["k50"] = vis.apply(k50, axis=1)
    months = [(pd.Timestamp(year=pd.Timestamp(i).year + k, month=1, day=1) - pd.Timestamp(i)).days / 30.44
              for i, k in zip(vis.issued, vis.k50)]
    fit = dict(cases=len(z), visible=int(z.visible.sum()),
               share_jan1_1=round(float(vis.share_jan1_1.median()), 2),
               share_jan1_2=round(float(vis.share_jan1_2.median()), 2),
               h1_first_jan1=round(float((vis[vis.first_half_year].k50 == 1).mean()), 2),
               h2_second_jan1=round(float((vis[~vis.first_half_year].k50 == 2).mean()), 2),
               months_to_half=round(float(np.median(months))))
    return z, fit


def parcel_timing_legacy():
    """The same test on the legacy permit system (2008 to mid-2017), which records no cost. Jobs
    are picked by wording instead (new building, addition, gut, renovation, dormer), on parcels
    with no other building permit from two years before to four years after; the lift is the
    value four January 1 assessments on, and a job counts when that lift exceeds 10%."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from permit_analysis import norm_street, leading_number, address_crosswalk
    g = pd.read_csv(DATA / "permits_cache" / "geotms.csv", low_memory=False).drop_duplicates("Permit_Number")
    g["d"] = pd.to_datetime(g["Date Issue"], errors="coerce")
    g["block_lot"] = (g.StNo.map(leading_number) + "|" + g.StName.map(norm_street)).map(address_crosswalk()["block_lot"])
    bld = g[(g.PermitType == "Building") & g.block_lot.notna()]
    h = pd.read_csv(ROOT / "land-value-map" / "output" / "parcel_full_history_fy09_26.csv")
    v = h.pivot_table(index="block_lot", columns="fy", values="tot_value")
    quiet = v.index.difference(bld.block_lot.unique())
    idx = (v.loc[quiet] / v.loc[quiet].shift(axis=1)).median().fillna(1).cumprod()
    words = bld.WorkDesc.astype(str).str.upper().str.contains(
        "NEW (?:SINGLE|TWO|THREE|DWELLING|HOUSE|HOME|BUILDING|CONSTRUCTION)|ADDITION|GUT|RENOVAT|DORMER|CONSTRUCT")
    sel = bld[words & (bld.d >= "2008-01-01") & (bld.d < "2017-07-01")]
    by_parcel = {b: grp.d for b, grp in bld.groupby("block_lot")}
    rows = []
    for r in sel.itertuples():
        f0, fe = r.d.year + 1, r.d.year + 5
        if r.block_lot not in v.index or f0 < 2009 or fe > 2026:
            continue
        s = v.loc[r.block_lot]
        if pd.isna(s.get(f0)) or pd.isna(s.get(fe)) or s[f0] <= 0:
            continue
        o = by_parcel[r.block_lot]
        o = o[o != r.d]
        if ((o > r.d - pd.DateOffset(years=2)) & (o < r.d + pd.DateOffset(years=4))).any():
            continue
        lift = s / idx * idx[f0] - s[f0]
        if lift[fe] <= 0.1 * s[f0]:
            continue
        sh = [lift[f0 + k] / lift[fe] for k in (1, 2, 3)]
        k50 = next((k for k, x in zip((1, 2, 3), sh) if x >= 0.5), 4)
        rows.append(dict(block_lot=r.block_lot, issued=r.d.date(), description=r.WorkDesc,
                         value_before=s[f0], lift_4_years_on=round(lift[fe]),
                         share_jan1_1=round(sh[0], 3), share_jan1_2=round(sh[1], 3), share_jan1_3=round(sh[2], 3),
                         k50=k50, months_to_half=round((pd.Timestamp(year=r.d.year + k50, month=1, day=1) - r.d).days / 30.44, 1)))
    z = pd.DataFrame(rows)
    m = pd.to_datetime(z.issued).dt.month
    y = pd.to_datetime(z.issued).dt.year
    fit = dict(visible=len(z), share_jan1_1=round(float(z.share_jan1_1.median()), 2),
               share_jan1_2=round(float(z.share_jan1_2.median()), 2),
               h1_first_jan1=round(float((z[m <= 6].k50 == 1).mean()), 2),
               months_to_half=round(float(z.months_to_half.median())),
               months_by_era={f"{a}-{b}": round(float(z[y.between(a, b)].months_to_half.median()))
                              for a, b in ((2008, 2011), (2012, 2014), (2015, 2017))})
    return z, fit


def assessor_units():
    """Housing units on each assessment roll FY2017-FY2025 (RES-UNITS summed per parcel; each
    roll is as of the January 1 before its fiscal year). Cleaned of changes that are records,
    not homes: hotels (rooms recorded as units), a condominium parking lot, a private school's
    dormitory, and any change of 15 or more units on a parcel whose value moved less than
    ordinary market growth would explain (first-time unit counts for exempt complexes in
    FY2021, later record fixes). Assisted living and nursing homes are counted separately
    (assisted_living_change), not as homes: they bring no school children, and one of them
    (615 Heath St) records swings with no construction permit. Rolls before FY2017 carry no
    unit field, and the FY2026 roll counts units on a different definition, so the series stops
    at FY2025."""
    h = pd.read_csv(ROOT / "land-value-map" / "output" / "parcel_history_fy17_25.csv")
    u = h.pivot_table(index="block_lot", columns="fy", values="res_units", aggfunc="sum").fillna(0)
    v = h.pivot_table(index="block_lot", columns="fy", values="tot_value", aggfunc="sum")
    d = h.sort_values("fy").groupby("block_lot").description.last().astype(str).str.strip()
    idx = (v / v.shift(axis=1)).median()
    dd = d.reindex(u.index)
    keep = ~dd.isin(["HOTEL", "CONDO PRK-LOT", "PSCHOOL"])
    care = dd.isin(["ASSTD LIVING", "NURSING HOME"])
    rows = []
    for fy in range(2018, 2026):
        du = u[fy] - u[fy - 1]
        g = (v[fy] / v[fy - 1]) / idx[fy]
        record_only = (du.abs() >= 15) & g.reindex(du.index).between(0.9, 1.12)
        net = du[keep & ~care & ~record_only].sum()
        rows.append(dict(roll_fiscal_year=fy, valued_january_1=fy - 1, raw_net_change=int(du.sum()),
                         net_new_homes=int(net), assisted_living_change=int(du[care].sum()),
                         removed_as_records=int(du[~care].sum() - net)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 2. town services
def services():
    """FY2010 (April 2010 Census) to FY2025. Homes are Census counts in 2010 and 2020 only;
    the years between are a straight line and the years after carry the 2010-20 pace, so
    `homes_is_census` marks the two real counts."""
    fte = pd.read_csv(OUT / "expense_drivers_fte_panel_fy04_27.csv").set_index("fiscal_year")
    h = pd.read_csv(OUT / "public_safety_workload_fy03_25.csv").set_index("fiscal_year").housing_units_est
    sch = pd.read_csv(OUT / "school_enrollment_staffing_fy05_25.csv").set_index("fiscal_year")
    rows = []
    for y in range(2010, 2026):
        rows.append(dict(fiscal_year=y, homes=round(float(h.loc[y])), homes_is_census=int(y in (2010, 2020)),
                         police_fire_positions=round(float(fte.loc[y, "public_safety"]), 1),
                         other_town_positions=round(float(fte.loc[y, "total"] - fte.loc[y, "public_safety"]), 1),
                         school_staff=round(float(sch.loc[y, "total_staff_fte"]), 1),
                         enrollment=int(sch.loc[y, "total_enrollment"])))
    out = pd.DataFrame(rows)
    # The assessment rolls' yearly count, January 2016 to January 2024, plotted in the fiscal
    # year that contains each January 1 (the FY y+1 roll is as of January 1 of y). Anchored to
    # the April 2020 Census count at January 2020, then stepped back and forward by the cleaned
    # change on each roll.
    au = assessor_units().set_index("valued_january_1").net_new_homes
    c20 = float(out.set_index("fiscal_year").homes[2020])
    def at(j):
        if j == 2020:
            return c20
        return c20 + au[(au.index > 2020) & (au.index <= j)].sum() if j > 2020 else c20 - au[(au.index > j) & (au.index <= 2020)].sum()
    out["homes_rolls"] = [round(at(y)) if au.index.min() - 1 <= y <= au.index.max() else None for y in out.fiscal_year]
    return out


# ---------------------------------------------------------------- 3. Brookline enrollment
def census_bps_brookline():
    units = {}
    for f in sorted((DATA / "census_bps").glob("ne*a.txt")):
        yr = int(f.name[2:6])
        for line in open(f, encoding="latin-1"):
            p = [x.strip() for x in line.split(",")]
            if len(p) > 27 and p[1] == "25" and p[16].lower() == "brookline town":
                units[yr] = sum(int(p[i]) for i in (18, 21, 24, 27))
    return units


def enrollment():
    d = pd.read_csv(DATA / "dese_enrollment" / "district_grade_enrollment.csv")
    d = d[d.dist_name == "Brookline"].set_index("sy").sort_index()
    b = pd.read_csv(OUT / "brookline_resident_births.csv").set_index("year").resident_births
    units = census_bps_brookline()
    rows = []
    for sy in range(2007, int(d.index.max()) + 1):
        fall = sy - 1
        k = float(d.loc[sy, "k_cnt"])
        movers = float(sum(d.loc[sy, G[g + 1]] - d.loc[sy - 1, G[g]] for g in range(12)))
        rows.append(dict(fall=fall, k12=int(d.loc[sy, G].sum()), kindergarten=int(k),
                         births_five_years_earlier=int(b.get(fall - 5)) if fall - 5 in b.index else None,
                         kindergartners_per_birth=round(k / b[fall - 5], 3) if fall - 5 in b.index else None,
                         net_movers_grades_1_12=int(movers), units_authorized=units.get(fall)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 4. children per added home
def _norm(n):
    n = n.lower().strip()
    return re.sub(r"\s+(town city|city|town)$", "", n)


def census_children(yr):
    C = DATA / "census_cache" / f"pl{yr}"
    geo, units = {}, {}
    if yr == 2010:
        for l in open(C / "mageo2010.pl", encoding="latin-1"):
            if l[8:11] == "060":
                geo[l[18:25]] = _norm(l[226:316])
        sep = ","
    else:
        for l in open(C / "mageo2020.pl", encoding="latin-1"):
            f = l.split("|")
            if f[2] == "060":
                geo[f[7]] = _norm(f[87])
        sep = "|"
    tot, adult = {}, {}
    for l in open(C / f"ma00001{yr}.pl", encoding="latin-1"):
        f = l.split(sep)
        if f[4] in geo:
            tot[geo[f[4]]] = int(f[5])
    for l in open(C / f"ma00002{yr}.pl", encoding="latin-1"):
        f = l.split(sep)
        if f[4] in geo:
            adult[geo[f[4]]] = int(f[5])
            # housing units, H1 total, follows P3 and P4 in segment 2
    return {k: tot[k] - adult[k] for k in tot}


def children():
    P = pd.read_csv(OUT / "cross_town_panel_fy11_21.csv").set_index("key")
    x = P[["units_0", "units_1", "d_units"]].assign(kids_0=pd.Series(census_children(2010)),
                                                    kids_1=pd.Series(census_children(2020))).dropna()
    x = x[x.units_0 >= 2000].copy()
    x["home_growth"] = x.d_units / x.units_0
    x["child_change"] = x.kids_1 / x.kids_0 - 1
    b, se = ols(x.child_change, [x.home_growth])
    kph = float((x.kids_0 / x.units_0).mean())
    res = dict(n=len(x), elasticity=round(float(b[1]), 2), elasticity_ci=[round(float(b[1] - 1.96 * se[1]), 2), round(float(b[1] + 1.96 * se[1]), 2)],
               intercept=round(float(b[0]), 3), children_per_existing_home=round(kph, 2),
               children_per_added_home=round(float(b[1]) * kph, 2),
               children_per_added_home_ci=[round(float(b[1] - 1.96 * se[1]) * kph, 2), round(float(b[1] + 1.96 * se[1]) * kph, 2)])
    # the same without Boston and weighted by homes, as a check that one city does not drive it
    m = x.index != "boston"
    b2, _ = ols(x.child_change[m], [x.home_growth[m]], x.units_0[m])
    res["children_per_added_home_check"] = round(float(b2[1]) * float(np.average(x.kids_0[m] / x.units_0[m], weights=x.units_0[m])), 2)
    # the same test on public school enrollment, single-town districts (DESE, fall 2009 and fall 2019)
    d = pd.read_csv(DATA / "dese_enrollment" / "district_grade_enrollment.csv")
    d["key"] = d.dist_name.str.lower().str.strip()
    d["k12"] = d[G].sum(axis=1)
    w = d.pivot_table(index="key", columns="sy", values="k12")
    e = x.join(w[[2010, 2020]].rename(columns={2010: "enroll_0", 2020: "enroll_1"}), how="inner").dropna(subset=["enroll_0", "enroll_1"])
    e = e[e.enroll_0 >= 300]
    be, see = ols(e.enroll_1 / e.enroll_0 - 1, [e.home_growth])
    sph = float((e.enroll_0 / e.units_0).mean())
    res["districts_n"] = len(e)
    res["students_per_existing_home"] = round(sph, 2)
    res["students_per_added_home"] = round(float(be[1]) * sph, 2)
    res["students_per_added_home_ci"] = [round(float(be[1] - 1.96 * see[1]) * sph, 2), round(float(be[1] + 1.96 * see[1]) * sph, 2)]
    x = x.join(e[["enroll_0", "enroll_1"]])
    bk = x.loc["brookline"]
    res["brookline"] = dict(homes_2010=int(bk.units_0), homes_2020=int(bk.units_1), children_2010=int(bk.kids_0), children_2020=int(bk.kids_1))
    res["brookline_children_from_added_homes"] = int(round(bk.d_units * res["children_per_added_home"], -1))
    return x, res


# ---------------------------------------------------------------- 5. home sales
ROLLS = [(2009, "FY2009%20Property%20Assessments.xls"), (2010, "FY2010%20Property%20Assessments.xls"),
         (2011, "FY2011%20Property%20Assessments.xls"), (2012, "FY2012%20Property%20Assessments.xls"),
         (2013, "FY2013%20Property%20Assessments.xls"), (2014, "FY-2014-Property-Assessments_201406261550560819_202008100928143178.xls"),
         (2015, "FY2015-Property-Assessments_201412310628028009_202008100946062419.xls"),
         (2016, "FY2016%20PROPERTY%20ASSESSMENTS_201811081055340878.xlsx"),
         (2020, "FY2020%20PROPERTY%20ASSESSMENTS_202001140708241175_202008101009167917.xlsx"),
         (2025, "FY2025 2ROPERTY ASSESSMENTS.xlsx"),
         (2026, "FY2026 Property Assessments_data update 2001.02.26_202603130814527665.xlsx")]
SHEETS = [(2017, "2026-04 Brookline assessments consolidated.xlsx", "FY17-ACTUAL"),
          (2018, "2026-04 Brookline assessments consolidated.xlsx", "FY18-ACTUAL"),
          (2019, "2026-04 Brookline assessments consolidated.xlsx", "FY19-ACTUAL"),
          (2021, "2026-04 Brookline assessments consolidated.xlsx", "FY21-ACTUAL"),
          (2023, "2026-04 Brookline assessments consolidated.xlsx", "FY23-ACTUAL"),
          (2024, "2026-01 Brookline assessment data analysis.xlsx", "FY24-ACTUAL")]
REN = {"SUBBLOCK": "PARCEL-ID", "Parcel ID": "PARCEL-ID", "Composite Land Use Code": "USECD",
       "Sale Date": "SALEDATE", "Sale Price": "SALEPRICE"}


def roll_sales():
    """Every (parcel, sale date) seen on any roll; slow, so cached."""
    if SALES_CACHE.exists():
        c = pd.read_csv(SALES_CACHE)
        c["sale_date"] = pd.to_datetime(c.sale_date, errors="coerce", format="mixed")
        return c
    frames = []
    for y, f in ROLLS:
        frames.append((y, pd.read_excel(DATA / f)))
    for y, f, s in SHEETS:
        frames.append((y, pd.read_excel(DATA / f, sheet_name=s)))
    keep = []
    for y, x in frames:
        x = x.rename(columns=REN)
        cols = ["PARCEL-ID", "USECD", "SALEDATE", "SALEPRICE"] + (["BEDROOMS"] if "BEDROOMS" in x.columns else [])
        x = x[cols].copy()
        x["roll"] = y
        keep.append(x)
    a = pd.concat(keep)
    a["parcel"] = a["PARCEL-ID"].astype(str).str.replace(r"\s+", "", regex=True).str.upper()
    a["sale_date"] = pd.to_datetime(a.SALEDATE, errors="coerce")
    a["price"] = pd.to_numeric(a.SALEPRICE, errors="coerce")
    a["use"] = pd.to_numeric(a.USECD, errors="coerce")
    use = a.sort_values("roll").groupby("parcel").use.last()
    bed = a.dropna(subset=["BEDROOMS"]).sort_values("roll").groupby("parcel").BEDROOMS.last() if "BEDROOMS" in a else pd.Series(dtype=float)
    s = a.dropna(subset=["sale_date"]).drop_duplicates(["parcel", "sale_date"])[["parcel", "sale_date", "price"]].copy()
    s["use"] = s.parcel.map(use)
    s["bedrooms"] = s.parcel.map(bed)
    s.to_csv(SALES_CACHE, index=False)
    return s


def sales(enr):
    s = roll_sales()
    s = s[(s.price >= 100_000) & s.use.isin([101, 102])].copy()
    s["year"] = s.sale_date.dt.year
    sf = s[s.use == 101].groupby("year").size()
    condo3 = s[(s.use == 102) & (s.bedrooms >= 3)].groupby("year").size()
    e = enr.set_index("fall")
    rows = [dict(year=y, single_family_sales=int(sf.get(y, 0)), condo_3bed_sales=int(condo3.get(y, 0)),
                 kindergartners_per_birth=e.kindergartners_per_birth.get(y)) for y in range(2009, int(e.index.max()) + 1)]
    r = pd.DataFrame(rows)
    fit = {}
    for lag in (0, 1, 2):
        z = pd.DataFrame({"x": sf.reindex(e.index - lag).values, "y": e.kindergartners_per_birth.values}, index=e.index)
        z = z[(z.index >= 2009 + lag) & (z.index != 2020)].dropna()
        fit[lag] = dict(r=round(float(z.x.corr(z.y)), 2), n=len(z))
    # Older children: net moves into grades 1-12 (each grade against the grade below a year
    # earlier) as a share of K-12, against sales the same year and the year before; the two
    # pandemic falls are left out. A sale moves the seller's children out as well as the
    # buyer's in, so this nets departures against arrivals.
    mv = e.net_movers_grades_1_12 / e.k12
    r["net_movers_grades_1_12"] = [e.net_movers_grades_1_12.get(y) for y in r.year]
    fit["movers"] = {}
    for lag in (0, 1):
        z = pd.DataFrame({"x": sf.reindex(e.index - lag).values, "y": mv.values}, index=e.index)
        z = z[(z.index >= 2009 + lag) & ~z.index.isin([2020, 2021])].dropna()
        fit["movers"][lag] = dict(r=round(float(z.x.corr(z.y)), 2), n=len(z))
    return r, fit


def main():
    rev, rev_fit = revenue()
    svc = services()
    enr = enrollment()
    kids, kid_fit = children()
    sal, sal_fit = sales(enr)
    pt, pt_fit = parcel_timing()
    pl, pl_fit = parcel_timing_legacy()
    pt_fit["legacy"] = pl_fit
    au = assessor_units()
    rev["basis"] = "Estimated Cost summed once per permit (RECORD ID) by calendar year issued; DLS certified total new growth valuation three fiscal years later; expected = permits x median ratio"
    svc["basis"] = "Town: budgeted FTE from Financial Plans (police and fire = Public Safety); schools: DESE staff FTE and enrollment; homes: Census 2010 and 2020, straight line between and +151 a year after"
    enr["basis"] = "DESE October enrollment; births = state birth reports, year of fall minus 5; units = Census BPS annual place file, new buildings only"
    kids["basis"] = "Census 2010 and 2020 PL 94-171: residents under 18 = total minus 18 and over; towns with 2,000+ homes in 2010"
    sal["basis"] = "Arm's-length sales ($100,000+) on assessment rolls FY2009-FY2026 (FY2022 skipped), deduped on parcel and sale date"
    rev.to_csv(OUT / "growth_links_revenue.csv", index=False)
    svc.to_csv(OUT / "growth_links_services.csv", index=False)
    enr.to_csv(OUT / "growth_links_enrollment.csv", index=False)
    kids.round(4).to_csv(OUT / "growth_links_children_by_town.csv")
    sal.to_csv(OUT / "growth_links_sales.csv", index=False)
    pt["basis"] = "One building permit of $250k+ on the parcel 2017-2025; values net of median unpermitted parcel growth; lift = FY2026 value (Jan 1, 2025) above the pre-permit value"
    au["basis"] = "Assessor RES-UNITS summed per parcel; hotels, a condo parking lot, a private school and 15+ unit changes without a matching value change removed"
    pt.to_csv(OUT / "growth_links_parcel_timing.csv", index=False)
    pl["basis"] = "Legacy permits 2008 to mid-2017, picked by wording; no other building permit on the parcel 2 years before to 4 after; lift = value four January 1 assessments on, net of median unpermitted growth"
    pl.to_csv(OUT / "growth_links_parcel_timing_legacy.csv", index=False)
    au.to_csv(OUT / "growth_links_assessor_units.csv", index=False)
    e = enr.dropna(subset=["kindergartners_per_birth"])
    pre = e[e.fall <= 2019]
    summary = dict(
        revenue_fit=rev_fit, parcel_timing=pt_fit,
        assessor_units=dict(first_jan1=int(au.valued_january_1.min()) - 1, last_jan1=int(au.valued_january_1.max()),
                            net=int(au.net_new_homes.sum()), per_year=round(float(au.net_new_homes.mean())),
                            raw=int(au.raw_net_change.sum()), min=int(au.net_new_homes.min()), max=int(au.net_new_homes.max())),
        children=kid_fit, sales_fit=sal_fit,
        kpb_min=round(float(pre.kindergartners_per_birth.min()), 2), kpb_max=round(float(pre.kindergartners_per_birth.max()), 2),
        movers_typical=int(pre.net_movers_grades_1_12.abs().median()),
        units_2006_2019_per_year=round(float(enr[(enr.fall >= 2006) & (enr.fall <= 2019)].units_authorized.mean())),
        k12_fall_2006=int(enr[enr.fall == 2006].k12.iloc[0]), k12_fall_2019=int(enr[enr.fall == 2019].k12.iloc[0]),
        k12_latest=int(enr.k12.iloc[-1]), latest_fall=int(enr.fall.iloc[-1]),
        units_2020_2025=int(enr[(enr.fall >= 2020) & (enr.fall <= 2025)].units_authorized.sum()),
        units_peak_year=int(enr.loc[enr.units_authorized.idxmax(), "fall"]), units_peak=int(enr.units_authorized.max()))
    # The chart's real estate view (permit_leading_indicator.py runs first): business equipment taken
    # out of certified new growth, so permits, what they point to and the base case are on one basis.
    # rows: [permit year, taxable permits $M, real estate new growth certified $M, expected $M, that FY, base case $M]
    pl = pd.read_csv(OUT / "permit_leading_indicator.csv")
    plj = json.loads((OUT / "permit_leading_indicator.json").read_text())
    revenue_re = []
    for r in pl[(pl.real_estate_valuation.notna() | pl.new_growth_fy.astype(str).isin(plj["years"].keys())) & ~pl.partial_year].itertuples():
        y = plj["years"].get(str(int(r.new_growth_fy)))
        revenue_re.append([int(r.permit_year), round(r.taxable_permits / 1e6, 1),
                           round(r.real_estate_valuation / 1e6, 1) if pd.notna(r.real_estate_valuation) else None,
                           round(y["expected_valuation"]["mid"] / 1e6, 1) if y else None, int(r.new_growth_fy),
                           round(y["base_valuation"] / 1e6, 1) if y else None])
    site = dict(
        revenue_re=revenue_re,
        revenue_re_ratio=[plj["ratio_min"], plj["ratio_max"]],
        revenue=[[int(r.permit_calendar_year), round(r.permitted_cost / 1e6, 1),
                  round(r.new_growth_valuation / 1e6, 1) if pd.notna(r.new_growth_valuation) else None,
                  round(r.expected_from_permits / 1e6, 1) if pd.notna(r.expected_from_permits) else None,
                  int(r.new_growth_fiscal_year)] for r in rev.itertuples()],
        services=[[int(r.fiscal_year), r.homes, r.homes_is_census, r.police_fire_positions, r.other_town_positions, r.school_staff, r.enrollment,
                   None if pd.isna(r.homes_rolls) else int(r.homes_rolls)] for r in svc.itertuples()],
        enrollment=[[int(r.fall), r.kindergarten, r.births_five_years_earlier, r.units_authorized, r.k12] for r in enr.itertuples()],
        towns=[[k, round(r.home_growth * 100, 1), round(r.child_change * 100, 1)] for k, r in kids.iterrows()],
        towns_fit=[kid_fit["intercept"], kid_fit["elasticity"]],
        sales=[[int(r.year), r.single_family_sales, r.kindergartners_per_birth] for r in sal.itertuples()],
        summary=summary)
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (float, np.floating)):
            return None if np.isnan(o) else float(o)
        return o
    (OUT / "growth_links.json").write_text(json.dumps(clean(site), allow_nan=False))
    print(json.dumps(summary, indent=1, default=float))
    print(f"wrote growth_links.json and eight growth_links_*.csv files")


if __name__ == "__main__":
    main()
