"""Why the Census counts more homes than permits explain: the Census against the assessors' rolls.

    python3 scripts/census_vs_roll_units.py

Two checks (2026-10-29, Ben asked why the 2010-2020 Census gain of 1,513 homes is so far above the
about 350 that permits from 2009-2018 add up to; see output/permit_homes_methodology.md):

1. Houses, two- and three-families and condominiums, January 2010 against January 2019 (FY2011 and
   FY2020 rolls). Rolls before FY2017 carry no unit field, so apartment buildings can't be counted in
   2010; these property types can: a house is 1 (its OCCUPANCY), a two- or three-family its OCCUPANCY,
   a condominium 1 per record. Converting a two-family to condominiums leaves the count unchanged.
2. All homes, the April 2020 Census against the January 2020 roll (FY2021, RES-UNITS), by Census block:
   each parcel is placed in the 2020 block holding its representative point. Hotels, inns, a private
   school's dormitory, nursing homes, assisted living, a hospital, fraternities, rooming houses and
   condominium parking are left out of the roll's count, as the Census counts them as group quarters
   or not at all.

Writes output/census_vs_roll_units_2020_by_tract.csv and prints both checks.
"""
import json
import warnings
from pathlib import Path

import pandas as pd
from shapely.geometry import shape
from shapely.strtree import STRtree

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
SMALL = {"101": "occ", "104": "occ", "105": "occ", "109": "occ", "102": "one"}
NOT_HOMES = ["HOTEL", "INN", "PSCHOOL", "NURSING HOME", "ASSTD LIVING", "HOSPITAL", "CONDO PRK-LOT",
             "CONDO PARK", "FRATERNITY", "LODGING"]


def small_units(path, unit_col=None):
    r = pd.read_excel(path)
    uc = r.USECD.astype(str).str[:3]
    occ = sum(pd.to_numeric(r[f"OCCUPANCY-{i}"], errors="coerce").fillna(0) for i in (1, 2, 3))
    out = {}
    for code, how in SMALL.items():
        sel = uc == code
        out[code] = int(sel.sum()) if how == "one" else int(occ[sel].sum())
    return out


a = small_units(ROOT / "data/FY2011%20Property%20Assessments.xls")
b = small_units(ROOT / "data/FY2020%20PROPERTY%20ASSESSMENTS_202001140708241175_202008101009167917.xlsx")
print("Houses, 2-3 families, condominiums (use code: Jan 2010 -> Jan 2019):")
for k in SMALL:
    print(f"  {k}: {a[k]:,} -> {b[k]:,}")
print(f"  total {sum(a.values()):,} -> {sum(b.values()):,}, change {sum(b.values()) - sum(a.values()):+,}")

parcels = json.loads((ROOT / "data/gis/brookline_parcels_2026-07-10.geojson").read_text())["features"]
blocks = json.loads((ROOT / "data/demographics/blocks/brookline_blocks_2020.geojson").read_text())["features"]
geoms = [shape(f["geometry"]) for f in blocks]
tree = STRtree(geoms)
rows = []
for f in parcels:
    p = f["properties"]
    try:
        pt = shape(f["geometry"]).representative_point()
    except Exception:
        continue
    hit = [i for i in tree.query(pt) if geoms[i].contains(pt)]
    if hit:
        rows.append((f"{p['BLOCK']}-{p['LOT']}", blocks[hit[0]]["properties"]["GEOID"]))
where = pd.DataFrame(rows, columns=["block_lot", "geoid"]).drop_duplicates("block_lot")

h = pd.read_csv(ROOT / "land-value-map/output/parcel_history_fy17_25.csv")
roll = h[h.fy == 2021].copy()
roll["desc"] = roll.description.astype(str).str.strip()
roll["homes"] = roll.res_units.where(~roll.desc.isin(NOT_HOMES), 0)
roll = roll.merge(where, on="block_lot", how="left")
census = pd.read_csv(ROOT / "data/demographics/blocks/brookline_blocks_2020.csv", dtype={"geoid": str})
d = census.set_index("geoid")[["units"]].join(roll.groupby("geoid").homes.sum()).fillna(0)
d["tract"] = d.index.str[5:9]          # tracts split in 2020 (4002.01/.02 ...) are put back together
t = d.groupby("tract")[["units", "homes"]].sum().astype(int)
t["census_minus_roll"] = t.units - t.homes
t = t.rename(columns={"units": "census_2020_units", "homes": "roll_jan2020_homes"})
t.to_csv(ROOT / "output/census_vs_roll_units_2020_by_tract.csv")
print(f"\nApril 2020 Census {int(d.units.sum()):,} homes; January 2020 roll {int(roll.homes.sum()):,} "
      f"({int(roll[roll.geoid.isna()].homes.sum())} not placed in a block); "
      f"Census higher by {int(d.units.sum() - roll.homes.sum()):,}")
print(t.to_string())
