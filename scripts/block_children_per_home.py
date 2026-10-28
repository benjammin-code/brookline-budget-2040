"""
School-age children per home in Brookline, by kind of home and bedrooms, from census blocks.

The Census counts children by age on every block (2010: 680 Brookline blocks, 2020: 553). The
assessor's records say what homes stand on each block: houses with their bedrooms, condominiums
with theirs, two- and three-family houses. Apartment buildings are recorded as whole buildings
without bedrooms, so apartments are what is left: the Census's housing units on the block minus
the homes the assessor records there. Fitting children 5-17 on each block to the number of each
kind of home gives children per home of each kind. Doing it for 2010 and 2020 shows how those
rates moved.

Inputs:
  data/demographics/blocks/brookline_blocks_{2010,2020}.csv     scripts/census_block_extract.py
  data/demographics/blocks/brookline_blocks_{2010,2020}.geojson TIGERweb block outlines
  data/FY2010%20Property%20Assessments.xls                      assessor, January 1, 2009 values
  data/FY2020%20PROPERTY%20ASSESSMENTS_...xlsx                   assessor, January 1, 2019 values
  data/gis/brookline_parcels_2026-07-10.geojson                 parcel outlines, to place records

Placing assessor records on blocks: the parcel's own outline; else the condominium's main lot
(same block and lot); else the same street address; else the nearest house number on the same
street (flagged; about 750 condominium units each year, whose lots were renumbered after 2020).
A record goes to the block holding a point inside its parcel.

Children are all children 5 to 17 counted by the Census, in public, private or no school.
The 2020 block counts carry the Census Bureau's privacy noise; it averages out over many blocks
but makes any one block's count unreliable.

Writes:
  output/block_children_rates.csv     children per home by kind of home, 2010 and 2020, with
                                      bootstrap ranges (resampling block groups)
  output/block_children_blocks.csv    every block: census counts and assessor homes by kind
  output/block_children_bg.csv        block groups on 2020 lines, both years, for the scatter
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = Path(__file__).parent.parent
BLK = ROOT / "data/demographics/blocks"
ASSESS = {
    2010: ROOT / "data/FY2010%20Property%20Assessments.xls",
    2020: ROOT / "data/FY2020%20PROPERTY%20ASSESSMENTS_202001140708241175_202008101009167917.xlsx",
}
PARCELS = ROOT / "data/gis/brookline_parcels_2026-07-10.geojson"
OUT = ROOT / "output"

HOUSE, MULTI, CONDO = {101, 109}, {104, 105}, {102, 108}
KINDS = ["house_1-3br", "house_4br", "house_5+br", "two_three_family", "condo_0-1br",
         "condo_2br", "condo_3+br", "apartment_other"]
BOOT = 500


def parcel_index():
    feats = [f for f in json.load(open(PARCELS))["features"] if f["properties"]["PARCELID"]]
    pts, by_id, by_lot, by_addr, by_street = {}, {}, {}, {}, defaultdict(list)
    for f in feats:
        p = f["properties"]
        pid = p["PARCELID"]
        pts[pid] = shape(f["geometry"]).representative_point()
        by_id[pid] = pid
        by_lot.setdefault("-".join(pid.split("-")[:2]), pid)
        if p["PAR_ADD_NO_1"] and p["PAR_ADD_ST_1"]:
            st = p["PAR_ADD_ST_1"].strip()
            by_addr.setdefault((int(p["PAR_ADD_NO_1"]), st), pid)
            by_street[st].append((int(p["PAR_ADD_NO_1"]), pid))
    return pts, by_id, by_lot, by_addr, by_street


def place(r, idx):
    pts, by_id, by_lot, by_addr, by_street = idx
    pid = str(r["PARCEL-ID"]).replace(" ", "")
    if pid in by_id:
        return pid, "parcel"
    lot = by_lot.get("-".join(pid.split("-")[:2]))
    if lot:
        return lot, "main lot"
    try:
        no, st = int(r["ADDNO1"]), str(r["ADDST1"]).strip()
    except (TypeError, ValueError):
        return None, None
    if (no, st) in by_addr:
        return by_addr[(no, st)], "address"
    cand = [(abs(n - no) + (0 if n % 2 == no % 2 else 1000), p) for n, p in by_street.get(st, [])]
    if cand and min(cand)[0] <= 20:
        return min(cand)[1], "nearest number"
    return None, None


def assessor_homes(year, idx):
    """One row per home the assessor records: kind, bedrooms, parcel point."""
    d = pd.read_excel(ASSESS[year])
    d = d[d.USECD.isin(HOUSE | MULTI | CONDO)].copy()
    bed_cols = [c for c in d.columns if re.fullmatch(r"BEDROOMS-\d", c)]
    occ_cols = [c for c in d.columns if re.fullmatch(r"OCCUPANCY-\d", c)]
    d["bldg_bed"] = d[bed_cols].sum(axis=1, min_count=1)
    d["occ"] = d[occ_cols].sum(axis=1, min_count=1)
    homes = []
    for _, r in d.iterrows():
        pid, how = place(r, idx)
        if pid is None:
            continue
        use = int(r.USECD)
        if use in CONDO:
            n, bed = 1, r.BEDROOMS
        elif use == 101:
            n, bed = 1, r["BEDROOMS-1"]
        else:  # 109 several houses on a lot, 104 two-family, 105 three-family
            n = int(r.occ) if r.occ and r.occ > 0 else {104: 2, 105: 3}.get(use, 1)
            bed = r.bldg_bed / n if pd.notna(r.bldg_bed) else np.nan
        if use in MULTI:
            kind = "two_three_family"
        elif use in CONDO:
            kind = "condo_0-1br" if bed <= 1 else "condo_2br" if bed == 2 else "condo_3+br"
        else:
            kind = "house_1-3br" if bed <= 3 else "house_4br" if bed == 4 else "house_5+br"
        homes.append({"pid": pid, "how": how, "kind": kind, "units": n,
                      "bedrooms": bed * n if pd.notna(bed) else np.nan,
                      "big": n if pd.notna(bed) and bed >= 3 else 0})
    return pd.DataFrame(homes)


def blocks(year):
    c = pd.read_csv(BLK / f"brookline_blocks_{year}.csv", dtype={"geoid": str})
    gj = json.load(open(BLK / f"brookline_blocks_{year}.geojson"))
    geom = {f["properties"]["GEOID"]: shape(f["geometry"]) for f in gj["features"]}
    c = c[c.geoid.isin(geom)].reset_index(drop=True)
    return c, [geom[g] for g in c.geoid]


def to_block(points, polys):
    tree = STRtree(polys)
    out = []
    for p in points:
        hit = [i for i in tree.query(p) if polys[i].contains(p)]
        out.append(hit[0] if hit else tree.nearest(p))
    return out


def fit(df):
    X = df[KINDS].to_numpy(float)
    y = df["age5_17"].to_numpy(float)
    return nnls(X, y)[0]


def bootstrap(df, rng):
    groups = df.groupby("bg").indices
    keys = list(groups)
    draws = []
    for _ in range(BOOT):
        pick = rng.choice(len(keys), len(keys))
        rows = np.concatenate([groups[keys[i]] for i in pick])
        draws.append(fit(df.iloc[rows]))
    return np.percentile(draws, [10, 90], axis=0)


def main():
    idx = parcel_index()
    pid_pt = idx[0]
    rng = np.random.default_rng(2026)
    bg2020_c, bg2020_poly = blocks(2020)
    bg_tree_polys = bg2020_poly
    per_block, rates, notes = [], [], {}
    for year in (2010, 2020):
        cen, polys = blocks(year)
        homes = assessor_homes(year, idx)
        homes["blk"] = to_block([pid_pt[p] for p in homes.pid], polys)
        notes[year] = homes.groupby("how").units.sum().to_dict()
        agg = homes.pivot_table(index="blk", columns="kind", values="units", aggfunc="sum").fillna(0)
        extra = homes.groupby("blk")[["bedrooms", "big"]].sum()
        nbed = homes.dropna(subset=["bedrooms"]).groupby("blk").units.sum().rename("units_with_bedrooms")
        df = cen.join(agg).join(extra).join(nbed).fillna(0)
        for k in KINDS[:-1]:
            if k not in df:
                df[k] = 0.0
        known = df[KINDS[:-1]].sum(axis=1)
        df["assessor_homes"] = known
        df["apartment_other"] = (df.units - known).clip(lower=0)
        df["over"] = (known - df.units).clip(lower=0)
        # common geography: the 2020 block group holding each block's interior point
        reps = [p.representative_point() for p in polys]
        bgi = to_block(reps, bg_tree_polys)
        df["bg"] = [bg2020_c.geoid[i][:12] for i in bgi]
        df["year"] = year
        use = df[df.units > 0]
        est = fit(use)
        lo, hi = bootstrap(use, rng)
        homes_k = use[KINDS].sum()
        for k, e, l, h in zip(KINDS, est, lo, hi):
            rates.append({"year": year, "kind": k, "children_5_17_per_home": round(e, 3),
                          "low_10pct": round(l, 3), "high_90pct": round(h, 3), "homes": int(homes_k[k])})
        town = use.age5_17.sum() / use.units.sum()
        rates.append({"year": year, "kind": "all homes (census)", "children_5_17_per_home": round(town, 3),
                      "low_10pct": "", "high_90pct": "", "homes": int(use.units.sum())})
        print(f"\n{year}: {len(cen)} blocks, {int(cen.units.sum()):,} homes, "
              f"{int(cen.age5_17.sum()):,} children 5-17, {town:.3f} per home")
        print("  assessor homes placed by", notes[year])
        print(f"  assessor homes {int(known.sum()):,}; apartments and other {int(df.apartment_other.sum()):,}; "
              f"assessor homes beyond the census count on their block {int(df.over.sum()):,}")
        for k, e, l, h in zip(KINDS, est, lo, hi):
            print(f"  {k:<18} {e:6.3f}  ({l:.3f}-{h:.3f})  homes {int(homes_k[k]):>6,}")
        per_block.append(df)

    allb = pd.concat(per_block)
    cols = ["year", "geoid", "bg", "pop", "age0_4", "age5_17", "units", "occupied", "owner", "renter",
            *KINDS, "assessor_homes", "over", "bedrooms", "units_with_bedrooms", "big"]
    allb[cols].to_csv(OUT / "block_children_blocks.csv", index=False)
    with open(OUT / "block_children_rates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rates[0]))
        w.writeheader()
        w.writerows(rates)

    bg = allb.groupby(["year", "bg"]).agg(
        homes=("units", "sum"), children_5_17=("age5_17", "sum"), owner=("owner", "sum"),
        occupied=("occupied", "sum"), bedrooms=("bedrooms", "sum"),
        units_with_bedrooms=("units_with_bedrooms", "sum"), homes_3plus_br=("big", "sum"),
        apartments_other=("apartment_other", "sum")).reset_index()
    bg["children_per_home"] = (bg.children_5_17 / bg.homes).round(3)
    bg["avg_bedrooms_known"] = (bg.bedrooms / bg.units_with_bedrooms).round(2)
    bg["share_3plus_br"] = (bg.homes_3plus_br / bg.homes).round(3)
    bg["owner_share"] = (bg.owner / bg.occupied).round(3)
    bg["apartment_share"] = (bg.apartments_other / bg.homes).round(3)
    bg.to_csv(OUT / "block_children_bg.csv", index=False)
    print("\nwrote output/block_children_rates.csv, block_children_blocks.csv, block_children_bg.csv")


if __name__ == "__main__":
    main()
