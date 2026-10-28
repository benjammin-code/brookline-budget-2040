"""
Children and public school students per home by kind of home, from the Census Bureau's
individual household records (American Community Survey public-use microdata, 2020-2024).

Unlike the census blocks (scripts/block_children_per_home.py), these records link each
household's home (building size, bedrooms, owned or rented, condominium fee) to its children's
ages and whether they attend public school. The catch is the area: the smallest one published
is PUMA 00902, which is Brookline, Dedham and Milton together (Brookline is about half its
population). The rates are for those three towns, not Brookline alone.

Kinds of home: four groups that do not overlap, each occupied home in exactly one, matched to
the assessor's groups as closely as the survey allows. The survey records building size (BLD),
owned or rented (TEN) and a monthly condominium fee (CONP), never how a building is legally owned.
  house                 one-unit building, detached or attached (BLD 02, 03), no condo fee,
                        owned or rented
  condo                 owner paying a condo fee (CONP > 0), any building, townhouses included.
                        Only owners have a fee recorded, so a rented condo is an apartment here
  owner, small building owner with no condo fee in a building of 2 to 4 homes (BLD 04, 05): the
                        owner's own unit in a two- or three-family, and two-unit condos whose
                        owners pay no regular fee
  apartment             rented home in a building of 2 or more (BLD 04-09): apartments, rented
                        condos, and the rented units of two- and three-families
  other                 the few left: owners with no fee in buildings of 5 or more (likely
                        cooperatives), mobile homes
Vacant homes have no owner or renter, so they belong to no group; they count only in "all homes".

Children: people aged 5 to 17. Public school students: enrolled in public school (SCH 2) in
kindergarten to grade 12 (SCHG 02-14), any age. Rates are per occupied home; the "all homes"
rows also count vacant homes, as the census block rates do. Ranges are 90% intervals from the
survey's 80 replicate weights (standard error = sqrt(4/80 * sum of squared deviations)).

Inputs:  data/demographics/pums/pums_2020_24_puma00902_{households,persons}.csv
Writes:  output/pums_children_per_home.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
PUMS = ROOT / "data/demographics/pums"
OUT = ROOT / "output/pums_children_per_home.csv"
REP = [f"WGTP{i}" for i in range(1, 81)]


def load():
    h = pd.read_csv(PUMS / "pums_2020_24_puma00902_households.csv", dtype={"SERIALNO": str, "BLD": str})
    p = pd.read_csv(PUMS / "pums_2020_24_puma00902_persons.csv", dtype={"SERIALNO": str})
    h = h[h.TYPEHUGQ == 1].copy()  # housing units, not dormitories or nursing homes
    p["child"] = p.AGEP.between(5, 17)
    p["public"] = (p.SCH == 2) & p.SCHG.between(2, 14)
    p["private"] = (p.SCH == 3) & p.SCHG.between(2, 14)
    kids = p.groupby("SERIALNO")[["child", "public", "private"]].sum()
    h = h.join(kids, on="SERIALNO").fillna({"child": 0, "public": 0, "private": 0})
    h["occupied"] = h.TEN.notna()
    h["owner"] = h.TEN.isin([1, 2])
    h["condo"] = h.owner & (h.CONP.fillna(0) > 0)
    h["bldg"] = h.BLD.map({"02": "house", "03": "house", "04": "2-4 units", "05": "2-4 units",
                           "06": "5+ units", "07": "5+ units", "08": "5+ units", "09": "5+ units"})
    small, big = h.BLD.isin(["04", "05"]), h.BLD.isin(["06", "07", "08", "09"])
    h["kind"] = np.select(
        [~h.occupied, h.condo, h.BLD.isin(["02", "03"]), h.owner & small, ~h.owner & (small | big)],
        ["vacant", "condo", "house", "owner, small building", "apartment"], default="other")
    h["beds"] = h.BDSP.clip(upper=4).map({0: "0-1 br", 1: "0-1 br", 2: "2 br", 3: "3 br", 4: "4+ br"})
    return h


def rate(df, col):
    est = (df[col] * df.WGTP).sum() / df.WGTP.sum()
    reps = np.array([(df[col] * df[w]).sum() / df[w].sum() for w in REP])
    se = np.sqrt(4 / 80 * ((reps - est) ** 2).sum())
    return est, se


def row(name, df):
    r = {"kind": name, "records": len(df), "homes_weighted": int(df.WGTP.sum())}
    for col, label in [("child", "children_5_17"), ("public", "public_k12")]:
        e, se = rate(df, col)
        r[f"{label}_per_home"] = round(e, 3)
        r[f"{label}_low"] = round(max(e - 1.645 * se, 0), 3)
        r[f"{label}_high"] = round(e + 1.645 * se, 3)
    c, pub = (df.child * df.WGTP).sum(), (df.public * df.WGTP).sum()
    r["public_share_of_children"] = round(pub / c, 3) if c else ""
    return r


def main():
    h = load()
    occ = h[h.occupied]
    rows = [row("all homes, including vacant", h), row("occupied homes", occ)]
    kinds = ["house", "condo", "owner, small building", "apartment", "other"]
    for k in kinds:
        rows.append(row(k, occ[occ.kind == k]))
    beds = ["0-1 br", "2 br", "3 br", "4+ br"]
    for k in kinds[:4]:
        for b in beds:
            rows.append(row(f"{k}, {b}", occ[(occ.kind == k) & (occ.beds == b)]))
    # the schedule the forecast write-up uses: every occupied home by bedrooms, then owned and rented
    for b in beds:
        rows.append(row(f"all occupied, {b}", occ[occ.beds == b]))
    for t, m in [("owned", occ.owner), ("rented", ~occ.owner)]:
        for b in beds:
            rows.append(row(f"{t}, {b}", occ[m & (occ.beds == b)]))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    pd.set_option("display.width", 200)
    print(out[["kind", "records", "homes_weighted", "children_5_17_per_home", "children_5_17_low",
               "children_5_17_high", "public_k12_per_home", "public_share_of_children"]].to_string(index=False))
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
