"""
What does a new housing unit actually add to town (non-school) spending?
A cross-town test using every Massachusetts municipality, FY2011 to FY2021.

RKG's $1,371 per home (of which $1,109 is department budgets) is an average-cost
allocation: it takes the budget lines judged to vary with households and divides
by the number of households. Brookline's own history can't test it well, because
one town over one period can't separate growth from everything else that
happened. 351 towns can, at least roughly: towns that added more housing than
others, did their department budgets grow by more, and by how much per unit?

## Data

- Housing units and population, April 2010 and April 2020: Census PL 94-171
  redistricting files, geographic header (HU100, POP100), county subdivisions
  (SUMLEV 060). Downloaded to data/census_cache/ (the Census API now needs a key;
  the raw files don't).
- Spending: DOR Schedule A General Fund expenditures by function, FY2011 and
  FY2021 (data/revenue & expenditures all MA/). FY2011 is the first clean year
  after the FY2010 reclassification; April 2010 and April 2020 census dates line
  up with the start of FY2011 and the end of FY2020, so FY2021 is the first fiscal
  year fully after the second count.
- Non-residential new growth value, FY2012-2021, from the DOR new growth file,
  as a control for commercial growth. It includes personal property.

## Model

    d_spend_i = a * spend2011_i + b * d_units_i + c * d_nonres_i + e_i

a absorbs growth common to all towns (inflation, pay settlements) in proportion
to each town's starting budget. b is the added spending per added housing unit,
in FY2021 dollars, which is the number to compare with RKG. Estimated three ways:
unweighted, per existing unit (every variable divided by 2010 units, so small and
large towns count comparably), and without Boston. 95% intervals from a town-level
bootstrap (2,000 draws).

## Controls (printed)

  1. Inject a known $2,000 per unit into every town's spending change and
     confirm b rises by $2,000.
  2. Shuffle d_units across towns and confirm b collapses toward zero.

## What it can't do

It is a cross-section, not an experiment. Towns that add housing differ in other
ways (wealth, density, growth pressure), and those differences can move spending
too. The result is evidence about the typical Massachusetts town, of which
Brookline is one unusual example.

Run from `scripts/`:  python3 cross_town_marginal_cost.py
"""

import csv
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
CENSUS = ROOT / "data" / "census_cache"
DOR = ROOT / "data" / "revenue & expenditures all MA"
NG_FILE = ROOT / "data" / "2026 MA state new growth for all towns 20 years.xlsx"
OUT_CSV = ROOT / "output" / "cross_town_marginal_cost_fy11_21.csv"
TOWNS_CSV = ROOT / "output" / "cross_town_panel_fy11_21.csv"
METHOD_OUT = ROOT / "output" / "cross_town_marginal_cost_methodology.md"

Y0, Y1 = 2011, 2021
DEPT = ["General Government", "Public Safety", "Public Works", "Human Services",
        "Culture and Recreation"]
RKG_DEPT_PER_UNIT_FY25 = 1_109.0
RKG_PS_PER_UNIT_FY25 = 448.0 + 532.0
# ECI total compensation, state and local, fiscal-year means (price_indices_annual.csv)
ECI_FY21 = (143.65 + 146.85) / 2
ECI_FY25 = (167.7 + 174.1055) / 2
RNG = np.random.default_rng(20260928)


def norm(name):
    n = name.lower().replace("-", " ").strip()
    n = re.sub(r"\s+(town city|city|town)$", "", n)
    return re.sub(r"\s+", " ", n)


def census():
    c10, c20 = {}, {}
    for line in open(CENSUS / "pl2010" / "mageo2010.pl", encoding="latin-1"):
        if line[8:11] == "060":
            c10[norm(line[226:316].strip())] = (int(line[318:327]), int(line[327:336]))
    for line in open(CENSUS / "pl2020" / "mageo2020.pl", encoding="latin-1"):
        f = line.rstrip("\n").split("|")
        if f[2] == "060":
            c20[norm(f[87])] = (int(f[90]), int(f[91]))
    return c10, c20


def dor(year):
    x = pd.read_excel(DOR / f"GenFundExpenditures{year}.xlsx", header=0)
    x.columns = [str(c).strip() for c in x.columns]
    x["key"] = x["Municipality"].map(lambda s: norm(str(s)))
    for c in DEPT + ["Total Expenditures"]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x.set_index("key")


def nonres_ng():
    d = pd.read_excel(NG_FILE, sheet_name="data", header=1)
    d.columns = ["code", "muni", "fy", "resv", "resa", "totv", "tota", "respct", "pyll", "pct"]
    d = d[pd.to_numeric(d["fy"], errors="coerce").between(Y0 + 1, Y1)]
    d["nonres"] = pd.to_numeric(d["totv"]) - pd.to_numeric(d["resv"])
    d["key"] = d["muni"].map(lambda s: norm(str(s)))
    return d.groupby("key")["nonres"].sum()


def ols(y, X):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b


def fit(df, ycol, weight_by_units=False, drop=()):
    d = df[~df.index.isin(drop)]
    y = d[f"d_{ycol}"].to_numpy(float)
    X = np.column_stack([d[f"{ycol}_0"], d["d_units"], d["d_nonres"]]).astype(float)
    if weight_by_units:
        w = d["units_0"].to_numpy(float)
        y, X = y / w, X / w[:, None]
    b = ols(y, X)
    boots = []
    n = len(y)
    for _ in range(2000):
        i = RNG.integers(0, n, n)
        boots.append(ols(y[i], X[i])[1])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return b, lo, hi, n


def main():
    c10, c20 = census()
    s0, s1 = dor(Y0), dor(Y1)
    ng = nonres_ng()
    rows = []
    miss = []
    for key in s0.index:
        if key not in s1.index or key not in c10 or key not in c20 or key not in ng.index:
            miss.append(key)
            continue
        r = dict(key=key, units_0=c10[key][1], units_1=c20[key][1],
                 pop_0=c10[key][0], pop_1=c20[key][0], d_nonres=ng[key])
        r["dept_0"] = s0.loc[key, DEPT].sum()
        r["dept_1"] = s1.loc[key, DEPT].sum()
        r["ps_0"] = s0.loc[key, "Public Safety"]
        r["ps_1"] = s1.loc[key, "Public Safety"]
        rows.append(r)
    df = pd.DataFrame(rows).set_index("key")
    df = df[(df.dept_0 > 0) & (df.dept_1 > 0)]
    df["d_units"] = df.units_1 - df.units_0
    df["d_dept"] = df.dept_1 - df.dept_0
    df["d_ps"] = df.ps_1 - df.ps_0

    print("=" * 78)
    print("DATA")
    print("=" * 78)
    print(f"  towns matched {len(df)} of {len(s0)}; unmatched: {sorted(miss)[:12]}"
          f"{' ...' if len(miss) > 12 else ''}")
    b = df.loc["brookline"]
    print(f"  Brookline: units {b.units_0:,} -> {b.units_1:,} ({b.d_units:+,}), "
          f"dept spend ${b.dept_0/1e6:.1f}M -> ${b.dept_1/1e6:.1f}M")
    print(f"  statewide units {df.units_0.sum():,} -> {df.units_1.sum():,} "
          f"({df.d_units.sum()/df.units_0.sum():+.1%})")
    print()

    # --------------------------------------------------------------- controls
    print("=" * 78)
    print("CONTROLS")
    print("=" * 78)
    base = fit(df, "dept")[0][1]
    inj = df.copy()
    inj["d_dept"] = inj["d_dept"] + 2000 * inj["d_units"]
    got = fit(inj, "dept")[0][1]
    print(f"  {'PASS' if abs(got - base - 2000) < 1 else 'FAIL'}  injected $2,000/unit "
          f"recovered as ${got - base:,.2f}")
    sh = df.copy()
    placebo = []
    for _ in range(50):
        sh["d_units"] = RNG.permutation(df["d_units"].to_numpy())
        placebo.append(ols(sh["d_dept"].to_numpy(float),
                           np.column_stack([sh.dept_0, sh.d_units, sh.d_nonres]).astype(float))[1])
    print(f"  {'PASS' if abs(np.median(placebo)) < abs(base) / 3 else 'CHECK'}  shuffled "
          f"housing units give a median of ${np.median(placebo):,.0f}/unit "
          f"(real: ${base:,.0f}/unit)")
    print()

    # --------------------------------------------------------------- results
    print("=" * 78)
    print(f"ADDED SPENDING PER ADDED HOUSING UNIT, FY{Y0}-FY{Y1}")
    print("  (FY2021 dollars; FY2025 dollars in brackets, scaled by the ECI)")
    print("=" * 78)
    to25 = ECI_FY25 / ECI_FY21
    out = []
    for ycol, label, rkg in (("dept", "All five town departments", RKG_DEPT_PER_UNIT_FY25),
                             ("ps", "Public safety only", RKG_PS_PER_UNIT_FY25)):
        for spec, kw in (("unweighted", {}), ("per existing unit", {"weight_by_units": True}),
                         ("unweighted, without Boston", {"drop": ("boston",)})):
            bb, lo, hi, n = fit(df, ycol, **kw)
            print(f"  {label:26s} {spec:28s} ${bb[1]:>7,.0f}  [95% ${lo:,.0f} to ${hi:,.0f}]  "
                  f"FY25 ${bb[1]*to25:,.0f}  vs RKG ${rkg:,.0f}   common growth {bb[0]:.1%}")
            out.append(dict(outcome=label, specification=spec, towns=n,
                            per_unit_fy21=round(bb[1]), ci_low_fy21=round(lo),
                            ci_high_fy21=round(hi), per_unit_fy25=round(bb[1] * to25),
                            rkg_fy25=rkg, common_growth=round(bb[0], 4),
                            nonres_coef_per_dollar=round(bb[2], 5)))
        print()
    # ---------------------------------------------- growth-rate (elasticity) form
    # The dollar forms above let the largest cities dominate: Boston, Worcester
    # and Cambridge added the most units and also grew budgets for many other
    # reasons. The growth-rate form treats each town as one observation:
    #   ln(spend1/spend0) = k + e * ln(units1/units0) + g * nonres_per_unit + u
    # e = 1 means spending rises in proportion to housing (average cost);
    # e = 0 means no response. Brookline's marginal cost = e x its spend per unit.
    # Towns under 500 units are dropped as too small for stable ratios.
    print("=" * 78)
    print("GROWTH-RATE FORM (each town one observation, towns >= 500 units)")
    print("=" * 78)
    d = df[df.units_0 >= 500]
    br = df.loc["brookline"]
    z = (d.d_nonres / d.units_0 / 1e4).to_numpy(float)
    x = np.log(d.units_1 / d.units_0).to_numpy(float)
    X = np.column_stack([np.ones(len(d)), x, z])
    for ycol, label, rkg in (("dept", "All five town departments", RKG_DEPT_PER_UNIT_FY25),
                             ("ps", "Public safety only", RKG_PS_PER_UNIT_FY25)):
        y = np.log(d[f"{ycol}_1"] / d[f"{ycol}_0"]).to_numpy(float)
        e = ols(y, X)[1]
        boots = [ols(y[i], X[i])[1] for i in (RNG.integers(0, len(y), len(y)) for _ in range(2000))]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        per_unit = br[f"{ycol}_1"] / br.units_1
        mc = e * per_unit * to25
        print(f"  {label:26s} elasticity {e:5.2f} [95% {lo:5.2f} to {hi:5.2f}]  x Brookline "
              f"${per_unit:,.0f}/unit (FY21) = ${mc:,.0f}/unit FY25 "
              f"[${lo*per_unit*to25:,.0f} to ${hi*per_unit*to25:,.0f}]  vs RKG ${rkg:,.0f}")
        out.append(dict(outcome=label, specification="growth-rate (elasticity) x Brookline spend per unit",
                        towns=len(d), per_unit_fy21=round(e * per_unit),
                        ci_low_fy21=round(lo * per_unit), ci_high_fy21=round(hi * per_unit),
                        per_unit_fy25=round(mc), rkg_fy25=rkg, common_growth=None,
                        nonres_coef_per_dollar=None))
    print()
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    df.to_csv(TOWNS_CSV)
    print(f"wrote {OUT_CSV.name}, {TOWNS_CSV.name}")
    return out


if __name__ == "__main__":
    main()
