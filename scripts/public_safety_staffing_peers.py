"""
Police officers and firefighters per 1,000 residents: Brookline against peer towns, and
how public-safety staffing scales with population across Massachusetts.

Ben's question (2026-10-04): do we have enough public-safety resources, and will they
grow if the town's population grows?

Sources (saved in data/public_safety/):
  Police  FBI, Crime in the United States 2019, Table 78, Massachusetts: full-time law
          enforcement officers by city (fbi_cius2019_table78_massachusetts.xls). 2019 is
          the last year before the FBI's switch to incident-based reporting left large
          gaps in Massachusetts coverage, and before COVID-era attrition.
  Fire    U.S. Fire Administration, National Fire Department Registry, Massachusetts
          download (usfa_registry_ma.raw): career, volunteer and paid-per-call firefighters
          as last self-reported by each department (not dated per department).
  People  2020 Census redistricting files (data/census_cache/pl2020): population,
          housing units and land area for each city and town.

Outputs:
  output/public_safety_staffing_peers.csv      every matched town, with ratios
  output/public_safety_staffing_scaling.csv    regression of staffing on size and density
  output/public_safety_staffing_methodology.md

Run from `scripts/`:  python3 public_safety_staffing_peers.py
"""

import csv
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
PS = ROOT / "data" / "public_safety"
OUT = ROOT / "output"
PEERS = ["Brookline", "Newton", "Cambridge", "Somerville", "Arlington", "Watertown", "Needham",
         "Lexington", "Belmont", "Wellesley", "Medford", "Boston"]


def norm(name):
    n = str(name).lower().replace("-", " ").strip()
    n = re.sub(r"\s+(town city|city|town)$", "", n)
    n = re.sub(r"\s+(fire department|fire dept\.?|fire rescue|fire & ems|fire and ems|fire)\b.*$", "", n)
    return re.sub(r"\s+", " ", n).strip()


def census():
    rows = {}
    for line in open(ROOT / "data" / "census_cache" / "pl2020" / "mageo2020.pl", encoding="latin-1"):
        f = line.rstrip("\n").split("|")
        if f[2] == "060":
            rows[norm(f[87])] = dict(pop2020=int(f[90]), housing_units=int(f[91]),
                                     land_sq_mi=int(f[84]) / 2_589_988.11)
    return rows


def police():
    x = pd.read_excel(PS / "fbi_cius2019_table78_massachusetts.xls", header=None, skiprows=5)
    x = x.iloc[:, :5]
    x.columns = ["city", "fbi_pop2019", "le_employees", "officers2019", "civilians"]
    x = x[pd.to_numeric(x.officers2019, errors="coerce").notna()]
    x["town"] = x.city.map(lambda c: norm(re.sub(r"\d+$", "", str(c))))
    return x.groupby("town").agg(officers2019=("officers2019", "sum"),
                                 fbi_pop2019=("fbi_pop2019", "sum")).to_dict("index")


def fire():
    f = pd.read_csv(PS / "usfa_registry_ma.raw", dtype=str, skipinitialspace=True)
    f.columns = [c.strip() for c in f.columns]
    f = f[f["Organization Type"].str.startswith("Local", na=False)]
    num = lambda c: pd.to_numeric(f[c], errors="coerce").fillna(0)
    f = f.assign(career=num("Active Firefighters - Career"),
                 volunteer=num("Active Firefighters - Volunteer") + num("Active Firefighters - Paid per Call"),
                 stations=num("Number Of Stations"),
                 town=f["HQ city"].map(norm))
    return f.groupby("town").agg(career_ff=("career", "sum"), volunteer_ff=("volunteer", "sum"),
                                 stations=("stations", "sum"), dept=("Fire dept name", "first"),
                                 dept_type=("Dept Type", "first")).to_dict("index")


def ols(y, X):
    X = np.c_[np.ones(len(X)), X]
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ b
    s2 = resid @ resid / (len(y) - X.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    r2 = 1 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))
    return b, se, r2


def main():
    c, p, fr = census(), police(), fire()
    rows = []
    for town, cc in c.items():
        r = dict(town=town.title(), **cc)
        r["density"] = cc["pop2020"] / cc["land_sq_mi"] if cc["land_sq_mi"] else np.nan
        if town in p:
            r.update(officers2019=p[town]["officers2019"],
                     officers_per_1000=1000 * p[town]["officers2019"] / cc["pop2020"])
        if town in fr:
            r.update(career_ff=fr[town]["career_ff"], volunteer_ff=fr[town]["volunteer_ff"],
                     stations=fr[town]["stations"], fire_dept_type=fr[town]["dept_type"],
                     career_ff_per_1000=1000 * fr[town]["career_ff"] / cc["pop2020"])
        rows.append(r)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "public_safety_staffing_peers.csv", index=False)

    peers = d[d.town.isin(PEERS)].set_index("town").loc[PEERS]
    print(peers[["pop2020", "density", "officers2019", "officers_per_1000", "career_ff",
                 "career_ff_per_1000", "stations", "fire_dept_type"]].round(2).to_string())

    # how staffing scales with size and density, towns of 10,000+
    scal = []
    big = d[d.pop2020 >= 10_000]
    for lab, col, extra in (("police officers", "officers2019", None),
                            ("career firefighters (mostly-career departments)", "career_ff", "career")):
        x = big[big[col] > 0].copy()
        if extra:
            x = x[x.fire_dept_type.isin(["Career"]) & (x.volunteer_ff <= 0.1 * x.career_ff)]
        y = np.log(x[col].astype(float))
        for spec, X in (("population only", np.log(x[["pop2020"]].values)),
                        ("population and density", np.log(x[["pop2020", "density"]].values))):
            b, se, r2 = ols(y.values, X)
            scal.append(dict(staff=lab, spec=spec, n=len(x), elasticity_pop=round(b[1], 3),
                             se_pop=round(se[1], 3),
                             elasticity_density=round(b[2], 3) if len(b) > 2 else "",
                             r2=round(r2, 3)))
            # Brookline's residual: actual vs predicted
            bk = x[x.town == "Brookline"]
            if len(bk):
                Xb = np.log(bk[["pop2020", "density"]].values if len(b) > 2 else bk[["pop2020"]].values)
                pred = np.exp(b[0] + Xb @ b[1:])[0]
                scal[-1].update(brookline_actual=int(bk[col].iloc[0]), brookline_predicted=round(pred))
    s = pd.DataFrame(scal)
    s.to_csv(OUT / "public_safety_staffing_scaling.csv", index=False)
    print(s.to_string())


if __name__ == "__main__":
    main()
