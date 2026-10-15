"""
Brookline against its neighbors on births, families and family-sized housing, for the enrollment
page's "Is the drop in births unique to Brookline?" section and the technical page "Why families
settle elsewhere" (README item 11).

Inputs (all already in the project; see each producing script for provenance):
  output/ma_resident_births_by_town_2005_2023.csv   parse_town_births.py (DPH annual birth reports)
  data/dese_peers/enrollment_selectedpops_t8td-gens.csv   school_peer_comparison.py (DESE, sy = spring year)
  output/ma_towns_acs_profile.csv                   town_comparison_acs.py (ACS 5-year, 2015-19 and 2020-24)
  output/family_housing_by_town.csv                 family_housing_by_town.py (MassGIS assessor tables)
  data/DLS_AvgSingleFamTaxBill.xlsx                 DLS Databank "Average Single Family Tax Bill", FY2010-26
  land-value-map/output/parcel_full_history_fy09_26.csv   Brookline's own assessment rolls

Brookline is not in the DLS single-family series before FY2022 (towns with a residential exemption
are left out). Our own rolls give a single-family average about 21% above the DLS figure in every
overlap year (FY2022-26: 1.20 to 1.22; DLS counts about 4,580 parcels against our 4,200), so they are
used only for the year-to-year change: Brookline FY2010-21 = DLS FY2022 x (roll FYyyyy / roll FY2022).

Kindergarten per birth: fall 2025 kindergarten (DESE sy=2026) / resident births in 2020, the year
most of that class was born. Regional districts are skipped; the town's own district is used.

Writes output/families_by_town.json (read by site_facts.js) and output/families_by_town.csv.
    python3 families_by_town.py
"""
import json
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

GROUPS = {
    "Brookline": ["Brookline"],
    "Neighboring cities and inner suburbs": ["Cambridge", "Somerville", "Newton", "Watertown", "Arlington", "Belmont"],
    "Family suburbs": ["Lexington", "Wellesley", "Needham", "Winchester", "Concord", "Wayland", "Sudbury", "Weston"],
}
EARLY, LATE = range(2005, 2010), range(2019, 2024)
PEERS = ["Brookline", "Cambridge", "Somerville", "Watertown", "Arlington", "Newton", "Belmont",
         "Winchester", "Needham", "Wellesley", "Wayland", "Lexington"]


def births():
    b = pd.read_csv(OUT / "ma_resident_births_by_town_2005_2023.csv")
    wide = b.pivot_table(index="year", columns="town", values="resident_births", aggfunc="sum")
    series = {"Massachusetts": wide.sum(axis=1)}
    for g, towns in GROUPS.items():
        series[g] = wide[towns].sum(axis=1)
    index = {k: [[int(y), round(v / s.loc[list(EARLY)].mean() * 100, 1)] for y, v in s.items()] for k, s in series.items()}
    raw = {k: [[int(y), int(v)] for y, v in s.items()] for k, s in series.items()}
    early, late = wide.loc[list(EARLY)].mean(), wide.loc[list(LATE)].mean()
    chg = (late / early - 1)[early >= 200].sort_values()
    state = series["Massachusetts"].loc[list(LATE)].mean() / series["Massachusetts"].loc[list(EARLY)].mean() - 1
    grp = {k: s.loc[list(LATE)].mean() / s.loc[list(EARLY)].mean() - 1 for k, s in series.items()}
    return wide, index, raw, chg, state, grp


def k_per_birth(wide):
    e = pd.read_csv(ROOT / "data/dese_peers/enrollment_selectedpops_t8td-gens.csv", dtype=str)
    e = e[(e.org_type == "District") & (e.sy == "2026")].set_index("dist_name")
    return {t: int(e.loc[t, "k_cnt"]) / wide.loc[2020, t] for t in PEERS if t in e.index}, \
           {t: int(e.loc[t, "k_cnt"]) for t in PEERS if t in e.index}


def children_per_home():
    """ACS 2020-24: children 5-17 per housing unit, and per unit with 3+ bedrooms (B01001, B25041);
    DESE fall 2025 K-12 (no PK) for the share of school-age children in the public schools."""
    import town_comparison_acs as acs
    b1, bd = acs.load("b01001", 2024), acs.load("b25041", 2024)
    inv = {v: k for k, v in acs.names().items()}
    e = pd.read_csv(ROOT / "data/dese_peers/enrollment_selectedpops_t8td-gens.csv", dtype=str)
    e = e[(e.org_type == "District") & (e.sy == "2026")].set_index("dist_name")
    out = {}
    for t in PEERS:
        a, u = b1[inv[t]], bd[inv[t]]
        kids = sum(a[f"B01001_{c:03d}"] + a[f"B01001_{c + 24:03d}"] for c in (4, 5, 6))
        homes, big = u["B25041_001"], sum(u[f"B25041_{n:03d}"] for n in (5, 6, 7))
        k12 = sum(int(e.loc[t, c]) for c in ["k_cnt"] + [f"g{i}_cnt" for i in range(1, 13)])
        out[t] = {"homes": round(homes), "kids5_17": round(kids), "big_homes": round(big), "public_k12": k12,
                  "kids_per_home": round(kids / homes, 3), "big_share": round(big / homes, 3),
                  "kids_per_big_home": round(kids / big, 3), "public_per_big_home": round(k12 / big, 3),
                  "public_share": round(k12 / kids, 3)}
    return out


def single_family_values():
    d = pd.read_excel(ROOT / "data/DLS_AvgSingleFamTaxBill.xlsx")
    d.columns = [c.strip() for c in d.columns]
    v = d.pivot_table(index="Fiscal Year", columns="Municipality", values="Average Single-Family Value")
    h = pd.read_csv(ROOT / "land-value-map/output/parcel_full_history_fy09_26.csv", dtype={"description": str})
    h = h[h.description.str.strip().isin(["101", "SINGLE FAMILY", "ONE FAMILY H"])]
    roll = h.groupby("fy").tot_value.mean()
    overlap = (roll.loc[2022:2026] / v.loc[2022:2026, "Brookline"])
    spliced = v["Brookline"].copy()
    for fy in range(2010, 2022):
        spliced.loc[fy] = v.loc[2022, "Brookline"] * roll.loc[fy] / roll.loc[2022]
    v["Brookline"] = spliced
    return v, overlap


def main():
    wide, index, raw, chg, state, grp = births()
    kpb, kcount = k_per_birth(wide)
    acs = pd.read_csv(OUT / "ma_towns_acs_profile.csv")
    acs24, acs19 = acs[acs.period == "2020-2024"].set_index("town"), acs[acs.period == "2015-2019"].set_index("town")
    hous = pd.read_csv(OUT / "family_housing_by_town.csv").set_index("town")
    sfv, overlap = single_family_values()
    cph = children_per_home()

    rows = []
    for t in PEERS:
        h = hous.loc[t] if t in hous.index else None
        rows.append({
            "town": t, "births_0509": round(wide.loc[list(EARLY), t].mean()), "births_1923": round(wide.loc[list(LATE), t].mean()),
            "births_change": round(chg.get(t, wide.loc[list(LATE), t].mean() / wide.loc[list(EARLY), t].mean() - 1), 3),
            "k_fall2025": kcount.get(t), "births_2020": int(wide.loc[2020, t]), "k_per_birth": round(kpb[t], 2) if t in kpb else None,
            "hh_with_children": round(acs24.loc[t, "hh_with_children_pct"], 3), "single_family": round(acs24.loc[t, "single_family_pct"], 3),
            "three_plus_bedroom": round(acs24.loc[t, "three_plus_bedroom_pct"], 3), "age25_34": round(acs24.loc[t, "age25_34_pct"], 3),
            "family_sized_share": None if h is None else round(h.family_sized_pct, 3),
            "median_sale_family_sized": None if h is None else int(h.median_sale_family_sized),
            "housing_roll_fy": None if h is None else int(h.fiscal_year),
            **cph[t],
        })
    towns = pd.DataFrame(rows)
    towns.to_csv(OUT / "families_by_town.csv", index=False)
    rank = list(chg.index).index("Brookline") + 1
    sf = {t: [[int(fy), round(sfv.loc[fy, t])] for fy in range(2010, 2027) if pd.notna(sfv.loc[fy, t])]
          for t in ["Brookline", "Lexington", "Newton", "Wellesley", "Needham", "Arlington"] if t in sfv.columns}
    corr = towns.dropna(subset=["k_per_birth", "family_sized_share"])
    out = {
        "birthsIndex": index, "birthsRaw": raw, "groups": GROUPS,
        "change": {"state": round(state, 3), **{k: round(v, 3) for k, v in grp.items()}},
        "brooklineRank": rank, "townsRanked": len(chg),
        "towns": json.loads(towns.to_json(orient="records")),
        "sfValue": sf, "rollOverDls": [round(x, 3) for x in overlap.tolist()],
        "corr_kpb_family_share": round(corr.k_per_birth.corr(corr.family_sized_share), 2),
        "corr_kpb_price": round(corr.k_per_birth.corr(corr.median_sale_family_sized), 2),
        "corr_kpb_acs_3br": round(towns.k_per_birth.corr(towns.three_plus_bedroom), 2),
        "corr_kpb_children": round(towns.k_per_birth.corr(towns.hh_with_children), 2),
        "brookline_hist": {"hh_with_children_2019": round(acs19.loc["Brookline", "hh_with_children_pct"], 3),
                            "hh_with_children_2024": round(acs24.loc["Brookline", "hh_with_children_pct"], 3)},
    }
    (OUT / "families_by_town.json").write_text(json.dumps(out))
    print(towns[["town", "births_change", "k_per_birth", "family_sized_share", "median_sale_family_sized", "hh_with_children"]].to_string(index=False))
    print("change:", out["change"], "rank", rank, "of", len(chg))
    print("corr K/birth vs family-sized share", out["corr_kpb_family_share"], "vs price", out["corr_kpb_price"],
          "vs households with children", out["corr_kpb_children"])
    print("roll / DLS overlap", out["rollOverDls"])
    for t, s in sf.items():
        print(t, s[0], s[-1], f"{s[-1][1] / s[0][1] - 1:+.0%}")


if __name__ == "__main__":
    main()
