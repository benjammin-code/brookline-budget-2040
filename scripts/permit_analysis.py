"""Building-permit analysis: does permitted renovation show up in assessed value?

    python3 scripts/permit_analysis.py

Inputs (from the Town Building Department, received 2026-09-15):
  data/Copy of GeoTMSData_1.xlsx          legacy permit system, 2006-01 .. 2017-06
  data/Copy of FOIA_BuildingWParcelv3_1.xlsx  current system,  2017-06 .. 2026-09
Only the FOIA/current file carries `Estimated Cost`, so all dollar analysis is
FY2018-FY2026 (the nine complete fiscal years). That window aligns with the
land-value-map classifier's FY2017-2025 window, which is what makes the join useful.

Four things this file deliberately gets right, each learned by getting it wrong:

  - DEDUPE FIRST. The FOIA export repeats a permit once per contact row (58,907
    rows -> 51,854 permits, one id appearing 26 times). `Estimated Cost` is
    consistent within an id, so dropping duplicate ids is safe - but summing the
    raw export overstates construction volume by ~14%.

  - NEVER REPORT AGGREGATE EXCESS-VALUE-PER-PERMIT-DOLLAR. For permits under
    $25k the top 5 parcels of 1,795 account for more than the entire net excess
    ($90M of a $79M total), so the ratio is an outlier artifact - it reads as
    "$7.33 of value per $1 spent," which is nonsense. The trustworthy statistics
    are the MEDIAN growth factor and the SHARE of parcels beating their
    type-specific baseline.

  - STRATIFY THE BASELINE BY PROPERTY TYPE. A single town-wide baseline makes
    mid-size permits look value-destroying, because commercial parcels grew
    slower than residential over this window and hold most of the mid-size permits.

  - EXCLUDE UNIT-ADDING PARCELS when measuring renovation. Otherwise new
    construction leaks into the renovation estimate. Those parcels are the
    positive control instead (see below).

Validate any change with the positive control this script already runs: parcels
that added housing units must show a large detectable lift (1.82 vs 1.52). If
that check stops firing, the method is broken, not the data.

Known limitation: permits join to parcels by street address (no parcel id in the
export despite the filename). 85.2% of permits and 81.9% of permit dollars match.
The residual is concentrated in large rental complexes - Gerry Rd, Thornton Rd,
Independence Dr, Sherman Rd - where permits are filed per unit address but the
complex is assessed as a handful of parcels. Gerry Rd has zero rows in the
assessment roll. Renovation of large rental stock is therefore UNDER-counted here.
"""
import re
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "permits_cache"
OUT = ROOT / "land-value-map" / "output"
CACHE.mkdir(parents=True, exist_ok=True)

SUFFIX = {
    "ROAD": "RD", "STREET": "ST", "AVENUE": "AVE", "AV": "AVE", "PLACE": "PL",
    "DRIVE": "DR", "TERRACE": "TER", "TERR": "TER", "COURT": "CT", "LANE": "LN",
    "CIRCLE": "CIR", "BOULEVARD": "BLVD", "PARKWAY": "PKWY", "SQUARE": "SQ",
    "HIGHWAY": "HWY", "CRESCENT": "CRES",
}


def norm_street(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
    parts = re.sub(r"\s+", " ", s).strip().split()
    if parts and parts[-1] in SUFFIX:
        parts[-1] = SUFFIX[parts[-1]]
    return " ".join(parts)


def leading_number(x):
    m = re.match(r"\s*(\d+)", str(x))
    return m.group(1) if m else ""


def load_permits():
    """Deduped permit table with fiscal year, cost, and a parcel join."""
    src = CACHE / "foia.csv"
    if not src.exists():
        pd.read_excel(ROOT / "data" / "Copy of FOIA_BuildingWParcelv3_1.xlsx").to_csv(src, index=False)
    p = pd.read_csv(src, low_memory=False).drop_duplicates(subset=["RECORD ID"]).copy()
    p["issued"] = pd.to_datetime(p["DATE ISSUED"], errors="coerce")
    # MA fiscal year begins July 1
    p["fy"] = p["issued"].dt.year + (p["issued"].dt.month > 6).astype(int)
    p["cost"] = pd.to_numeric(p["Estimated Cost"], errors="coerce").fillna(0)
    p["invoiced"] = pd.to_numeric(p["TOTAL INVOICED"], errors="coerce")
    p["is_building"] = p["RECORD TYPE"].str.contains("Building", na=False)

    # street name: parse from JOB LOCATION, which is cleaner than STREET NAME
    # (that column sometimes retains the number range, e.g. "-  317 WASHINGTON STREET")
    def street(loc):
        s = str(loc).upper().split(",")[0]
        return norm_street(re.sub(r"^\s*[\d\-\s]+", "", s))

    p["street"] = [street(x) for x in p["JOB LOCATION"]]
    p["number"] = p["STREET NBR"].map(leading_number)
    p["key"] = p["number"] + "|" + p["street"]
    p["block_lot"] = p["key"].map(address_crosswalk()["block_lot"])
    return p


def address_crosswalk():
    """street number + name -> block_lot, from the FY2026 assessment roll."""
    cached = CACHE / "addr_crosswalk.csv"
    if cached.exists():
        return pd.read_csv(cached).set_index("key")
    a = pd.read_excel(
        ROOT / "data" / "FY2026 Property Assessments_data update 2001.02.26_202603130814527665.xlsx"
    )
    a["street"] = a["Street Name"].map(norm_street)
    a["number"] = a["Street Number"].map(leading_number)
    a["block_lot"] = a["Parcel ID"].astype(str).str.split("-").str[:2].str.join("-")
    a = a[a["number"] != ""]
    a["key"] = a["number"] + "|" + a["street"]
    xw = a.groupby("key").agg(
        block_lot=("block_lot", lambda s: s.mode().iloc[0]),
        n_bl=("block_lot", "nunique"),
    )
    xw.to_csv(cached)
    return xw


def fee_rate_check(p):
    """Positive control on the cost field: the Town charges a published rate per
    $1,000 of estimated cost, so the median implied rate should reproduce it."""
    b = p[p["is_building"] & (p["cost"] > 10_000) & (p["invoiced"] > 0)].copy()
    b["per_1000"] = b["invoiced"] / b["cost"] * 1000
    by_fy = b.groupby("fy")["per_1000"].agg(["median", "count"])
    by_month = (
        b[b["issued"] >= "2026-03-01"]
        .groupby(b["issued"].dt.to_period("M"))["per_1000"]
        .agg(["median", "count"])
    )
    return by_fy, by_month


def renovation_lift(p):
    """Growth of permitted vs unpermitted parcels, type-stratified, renovation only."""
    h = pd.read_csv(OUT / "parcel_history_fy17_25.csv")
    v1 = h[h["fy"] == 2017].set_index("block_lot")
    v2 = h[h["fy"] == 2025].set_index("block_lot")
    df = pd.DataFrame({
        "v17": v1["tot_value"], "v25": v2["tot_value"], "desc": v1["description"],
        "u17": v1["res_units"], "u25": v2["res_units"],
    }).dropna(subset=["v17", "v25"])

    # permit spend FY2018-2023 leaves >=2 years for it to reach the roll by FY2025
    pw = (p[p["block_lot"].notna() & p["fy"].between(2018, 2023)]
          .groupby("block_lot")
          .agg(permit_cost=("cost", "sum"), n_permits=("RECORD ID", "size")))
    df = df.join(pw).fillna({"permit_cost": 0, "n_permits": 0})
    df = df[df["v17"] > 50_000]
    df["f"] = df["v25"] / df["v17"]
    df["units_added"] = df["u25"] - df["u17"]

    # POSITIVE CONTROL: unit-adding parcels must show a clear lift
    control = df[df["units_added"] > 0]["f"].median()
    quiet = df[(df["units_added"] <= 0) & (df["n_permits"] == 0)]["f"].median()

    ren = df[df["units_added"] <= 0].copy()
    base = ren[ren["n_permits"] == 0].groupby("desc")["f"].agg(["median", "size"])
    ren = ren.join(base.rename(columns={"median": "base_f", "size": "base_n"}), on="desc")
    ren = ren[ren["base_n"] >= 20]  # only property types with a real control group
    ren["beat"] = ren["f"] > ren["base_f"] * 1.2

    bucket = pd.cut(ren["permit_cost"], [-1, 0, 25e3, 100e3, 500e3, 2e6, 1e9],
                    labels=["none", "<25k", "25-100k", "100-500k", "500k-2M", ">2M"])
    tab = ren.groupby(bucket, observed=True).apply(lambda g: pd.Series({
        "n": len(g),
        "median_growth": g["f"].median(),
        "baseline": g["base_f"].median(),
        "lift": g["f"].median() - g["base_f"].median(),
        "pct_beating_baseline": g["beat"].mean(),
        "permit_cost_M": g["permit_cost"].sum() / 1e6,
    }), include_groups=False)
    return tab, control, quiet, ren


def lag_curve(p):
    """Value trajectory around a large building permit, net of town-wide appreciation."""
    h = pd.read_csv(OUT / "parcel_history_fy17_25.csv")
    hv = h.pivot_table(index="block_lot", columns="fy", values="tot_value")
    big = (p[p["block_lot"].notna() & p["is_building"]
             & (p["cost"] >= 500e3) & p["fy"].between(2019, 2021)]
           .groupby(["block_lot", "fy"])["cost"].sum().reset_index()
           .sort_values("cost").drop_duplicates("block_lot", keep="last"))
    unpermitted = list(set(hv.index) - set(p["block_lot"].dropna().unique()))
    idx = hv.loc[unpermitted].median()
    idx = idx / idx.loc[2017]

    rows = []
    for _, r in big.iterrows():
        bl, fy0 = r["block_lot"], int(r["fy"])
        if bl not in hv.index:
            continue
        s = hv.loc[bl]
        if pd.isna(s.get(fy0)) or s.get(fy0, 0) <= 0:
            continue
        for k in range(-1, 5):
            if fy0 + k in s.index and pd.notna(s[fy0 + k]):
                rows.append({"k": k, "rel": (s[fy0 + k] / s[fy0]) / (idx[fy0 + k] / idx[fy0])})
    d = pd.DataFrame(rows).groupby("k")["rel"].agg(["count", "median"])
    d["yoy_lift_pp"] = (d["median"].diff() * 100).round(1)
    return d, len(big)


def main():
    p = load_permits()
    matched = p["block_lot"].notna()
    print(f"permits (deduped): {len(p):,}   matched to a parcel: {matched.sum():,} ({matched.mean():.1%})")
    print(f"permit dollars matched: {p.loc[matched,'cost'].sum()/p['cost'].sum():.1%}")

    by_fy, by_month = fee_rate_check(p)
    print("\n=== Fee-rate check (median $ invoiced per $1,000 of estimated cost) ===")
    print(by_fy.round(2).to_string())
    print("\nAround the FY2027 rate change ($20 -> $21 effective 2026-07-01):")
    print(by_month.round(2).to_string())

    tab, control, quiet, ren = renovation_lift(p)
    print(f"\n=== POSITIVE CONTROL: unit-adding parcels {control:.3f} vs quiet parcels {quiet:.3f} "
          f"-> {'DETECTED' if control > quiet * 1.15 else 'NOT DETECTED (method broken)'} ===")
    print("\n=== Assessed-value growth FY2017->FY2025 by permit spend (renovation only) ===")
    print(tab.round(3).to_string())

    d, n = lag_curve(p)
    print(f"\n=== Value trajectory around a >=$500k building permit (n={n} parcels) ===")
    print("k = fiscal years after issue; rel = value vs issue year, net of town-wide appreciation")
    print(d.round(3).to_string())

    tab.to_csv(CACHE / "renovation_lift_by_bucket.csv")
    d.to_csv(CACHE / "permit_value_lag_curve.csv")
    ren.to_csv(CACHE / "renovation_parcels.csv")
    print(f"\nwrote {CACHE}/renovation_lift_by_bucket.csv, permit_value_lag_curve.csv, renovation_parcels.csv")


if __name__ == "__main__":
    main()
