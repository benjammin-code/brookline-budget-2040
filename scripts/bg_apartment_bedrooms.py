"""
Apartments by bedrooms in each Brookline block group: the Census survey's count of all homes by
bedrooms, less the homes whose bedrooms the assessor records (houses, condominiums, two- and
three-family houses). What is left is apartments and other homes the assessor records without
bedrooms.

Also gives each block group's share of ALL homes with 3+ bedrooms straight from the survey,
which does not undercount large apartments the way the assessor-based share does.

Inputs:
  data/demographics/acs5yr/brookline_bg_b25041_2024.txt   ACS 2020-2024, table B25041
      (bedrooms, all housing units), Brookline's 44 block groups, with margins of error
  FY2020 assessor records, placed on 2020 blocks as in scripts/block_children_per_home.py
  output/block_children_bg.csv                              2020 children per home

The two sources differ in date (assessor values as of January 2019; survey 2020-2024) and the
survey's block-group margins are wide (often +/-50 homes a cell), so a block group's residual
can come out negative; those are clipped to zero and counted.

Writes output/bg_apartment_bedrooms.csv.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import block_children_per_home as B  # noqa: E402

ROOT = Path(__file__).parent.parent
ACS = ROOT / "data/demographics/acs5yr/brookline_bg_b25041_2024.txt"
OUT = ROOT / "output/bg_apartment_bedrooms.csv"
BINS = ["0", "1", "2", "3", "4", "5+"]


def acs():
    a = pd.read_csv(ACS, sep="|", dtype={"GEO_ID": str})
    a["bg"] = a.GEO_ID.str[-12:]
    out = pd.DataFrame({"bg": a.bg, "acs_homes": a.B25041_E001})
    for i, b in enumerate(BINS, start=2):
        out[f"acs_{b}"] = a[f"B25041_E00{i}"]
        out[f"acs_{b}_moe"] = a[f"B25041_M00{i}"]
    return out


def assessor():
    idx = B.parcel_index()
    cen, polys = B.blocks(2020)
    h = B.assessor_homes(2020, idx)
    h["bg"] = [cen.geoid[i][:12] for i in B.to_block([idx[0][p] for p in h.pid], polys)]
    h = h.dropna(subset=["bedrooms"])
    per = (h.bedrooms / h.units).round().clip(upper=5).astype(int)
    h["bin"] = per.map(lambda b: "5+" if b >= 5 else str(b))
    t = h.pivot_table(index="bg", columns="bin", values="units", aggfunc="sum").reindex(columns=BINS).fillna(0)
    t.columns = [f"assessor_{c}" for c in t.columns]
    return t.reset_index()


def main():
    df = acs().merge(assessor(), on="bg", how="left").fillna(0)
    for b in BINS:
        raw = df[f"acs_{b}"] - df[f"assessor_{b}"]
        df[f"apt_{b}"] = raw.clip(lower=0)
        df[f"apt_{b}_negative"] = (-raw).clip(lower=0)
    bg = pd.read_csv(ROOT / "output/block_children_bg.csv", dtype={"bg": str})
    bg = bg[bg.year == 2020][["bg", "homes", "children_5_17", "children_per_home", "share_3plus_br"]]
    df = df.merge(bg.rename(columns={"homes": "census_homes_2020", "share_3plus_br": "assessor_share_3plus"}), on="bg")
    df["acs_share_3plus"] = (df.acs_3 + df.acs_4 + df["acs_5+"]) / df.acs_homes
    df.to_csv(OUT, index=False)

    tot = df.sum(numeric_only=True)
    print(f"{len(df)} block groups; survey homes {int(tot.acs_homes):,}, census 2020 homes {int(tot.census_homes_2020):,}")
    print("bedrooms   survey   assessor   apartments (clipped)   clipped away")
    for b in BINS:
        print(f"{b:>4}  {int(tot[f'acs_{b}']):>9,} {int(tot[f'assessor_{b}']):>9,} {int(tot[f'apt_{b}']):>12,} {int(tot[f'apt_{b}_negative']):>12,}")
    apt = sum(tot[f"apt_{b}"] for b in BINS)
    big = tot.apt_3 + tot.apt_4 + tot["apt_5+"]
    print(f"apartments and other: {int(apt):,}, of which 3+ bedrooms {int(big):,} ({big / apt:.0%})")
    print(f"correlation with children per home: survey 3+ share {df.children_per_home.corr(df.acs_share_3plus):.2f}, "
          f"assessor 3+ share {df.children_per_home.corr(df.assessor_share_3plus):.2f}")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
