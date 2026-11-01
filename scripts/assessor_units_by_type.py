"""Net new homes on each assessment roll, FY2018-FY2026 (valued Jan 1 2017 - Jan 1 2025),
cleaned of record changes and non-household units, and split by project type.

The source for growth_links.assessor_units() (since 2026-10-31), plus a type split. Rules:
  * excluded uses: hotels, private-school dorms, the condo parking lot (spaces entered as units),
    hospitals, and exempt institutional residences (charitable/religious/educational land-use
    codes 9xx other than 970 Housing Authority, e.g. Ronald McDonald House, a benevolent
    association's elder residence). Assisted living / nursing are reported separately.
  * record-only: a change of 15+ units on a parcel whose value moved within 0.9-1.12x of the
    roll's median parcel value change (units first entered or corrected, nothing built).
  * FY2021 recount of "multiple houses" lots: all ~70 went from 1 to 2 units (second house on
    the lot now counted) with flat value; treated as record only (+73).
  * the rest is kept, including demolitions (negative), and typed by what the parcel is now.

FY2018-25 come from land-value-map/output/parcel_history_fy17_25.csv (block-lot level).
FY2026 comes from the raw FY2025 and FY2026 rolls matched record by record (99.9% of parcel
IDs match). The FY2026 roll's `Num_units` field equals FY2025's RES-UNITS on unchanged records;
its `Residential Units` field is a different, narrower count and is not used.

Changed 2026-10-31 from the earlier growth_links rules (FY2018-25 only, 900 net): exempt
institutional residences (CHARITABLE, +18) and LODGING are excluded, and the FY2021 multi-house
recount (+73) is removed, so FY2018-25 now totals 809; the FY2026 roll adds 273. Uses are judged
by each parcel's latest FY2018-25 description.

Outputs: output/assessor_new_units_by_type_fy18_26.csv (year x type)
         output/assessor_unit_changes_detail_fy18_26.csv (every parcel change with its treatment)
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "output"

TYPE_BY_DESC = {
    "SINGLE FAMILY": "Single-family",
    "TWO FAMILY": "2-3 family", "THREE FAMILY": "2-3 family", "MULT HOUSES": "2-3 family",
    "CONDO": "Condo",
    "APT 4-8 UNIT": "Apartments 4-8",
    "APTS 9+ UNIT": "Apartments 9+",
    "RES/COMM": "Mixed use", "COMM/RES": "Mixed use", "COMMERCIAL": "Mixed use",
    "AUTHORITIES": "Public / affordable", "AFFORD-MULTI-UNITS": "Public / affordable",
    "AFFORD-CONDOS": "Public / affordable",
}
TYPE_BY_LU = {101: "Single-family", 104: "2-3 family", 105: "2-3 family", 109: "2-3 family",
              102: "Condo", 111: "Apartments 4-8", 112: "Apartments 9+", 13: "Mixed use",
              31: "Mixed use", 970: "Public / affordable"}
EXCL_DESC = {"HOTEL", "CONDO PRK-LOT", "PSCHOOL", "CHARITABLE", "HOSPITAL", "LODGING"}
CARE_DESC = {"ASSTD LIVING", "NURSING HOME"}
CARE_LU = {125, 304}


def excl_lu(lu):
    return lu in (300, 305, 121) or (900 <= lu < 1000 and lu != 970)


def rolls_fy18_25():
    h = pd.read_csv(ROOT / "land-value-map" / "output" / "parcel_history_fy17_25.csv")
    u = h.pivot_table(index="block_lot", columns="fy", values="res_units", aggfunc="sum").fillna(0)
    v = h.pivot_table(index="block_lot", columns="fy", values="tot_value", aggfunc="sum")
    desc = h.pivot_table(index="block_lot", columns="fy", values="description", aggfunc="last")
    last = h.sort_values("fy").groupby("block_lot").description.last().astype(str).str.strip()
    idx = (v / v.shift(axis=1)).median()
    rows = []
    for fy in range(2018, 2026):
        du = u[fy] - u[fy - 1]
        for bl in du[du != 0].index:
            g = (v.loc[bl, fy] / v.loc[bl, fy - 1]) / idx[fy]
            if last[bl] in CARE_DESC:
                st = "assisted living / nursing"
            elif last[bl] in EXCL_DESC:
                st = "excluded use"
            elif abs(du[bl]) >= 15 and 0.9 <= g <= 1.12:
                st = "record only"
            elif fy == 2021 and last[bl] == "MULT HOUSES" and 0.9 <= g <= 1.12:
                st = "record only"  # FY2021 recount: every multi-house lot went 1 -> 2 units, value flat
            else:
                st = "kept"
            now = str(desc.loc[bl, fy]).strip()
            t = TYPE_BY_DESC.get(last[bl]) or TYPE_BY_DESC.get(now) or "Other"
            rows.append(dict(roll_fy=fy, valued_jan1=fy - 1, parcel=bl, description=last[bl],
                             units_change=int(du[bl]), value_ratio_vs_median=round(g, 2) if pd.notna(g) else None,
                             treatment=st, project_type=t))
    return pd.DataFrame(rows)


def roll_fy26():
    a = pd.read_excel(DATA / "FY2025 2ROPERTY ASSESSMENTS.xlsx")
    b = pd.read_excel(DATA / "FY2026 Property Assessments_data update 2001.02.26_202603130814527665.xlsx")
    a["v25"] = a[["RESTOTLVAL", "COMTOTLVAL", "EXMTOTLVAL"]].sum(axis=1)
    m = a[["PARCEL-ID", "DESCRIPTION", "RES-UNITS", "v25"]].merge(
        b[["Parcel ID", "Composite Land Use Code", "Num_units", "FY2026VALUE", "Year Built",
           "Street Number", "Street Name"]], left_on="PARCEL-ID", right_on="Parcel ID", how="outer")
    m["rec"] = m["Parcel ID"].fillna(m["PARCEL-ID"])
    m["bl"] = m.rec.str.split("-").str[:2].str.join("-")
    for c in ["RES-UNITS", "Num_units", "v25", "FY2026VALUE"]:
        m[c] = m[c].fillna(0)
    m["du"] = m.Num_units - m["RES-UNITS"]
    rec_ratio = (m.FY2026VALUE / m.v25.where(m.v25 > 0))
    idx = rec_ratio[(m["PARCEL-ID"].notna()) & (m["Parcel ID"].notna())].median()
    blk = m.groupby("bl").agg(du=("du", "sum"), v25=("v25", "sum"), v26=("FY2026VALUE", "sum"))
    blk["g"] = (blk.v26 / blk.v25) / idx
    # Work at block-lot level (as FY2018-25 do) so a two-family split into condo records nets
    # out; describe each parcel by its record with the largest unit change (ties: largest gain).
    m = m.assign(absdu=m.du.abs()).sort_values(["absdu", "du"], ascending=False)
    rep = m[m.du != 0].groupby("bl").first()
    rows = []
    for bl, r in rep.iterrows():
        if blk.loc[bl].du == 0:
            continue
        lu = r["Composite Land Use Code"]
        lu = int(lu) if pd.notna(lu) else None
        d = str(r.DESCRIPTION).strip() if pd.notna(r.DESCRIPTION) else ""
        bk = blk.loc[bl]
        if d in CARE_DESC or lu in CARE_LU:
            st = "assisted living / nursing"
        elif d in EXCL_DESC or (lu is not None and excl_lu(lu)):
            st = "excluded use"
        elif abs(bk.du) >= 15 and 0.9 <= bk.g <= 1.12:
            st = "record only"
        else:
            st = "kept"
        t = TYPE_BY_LU.get(lu) or TYPE_BY_DESC.get(d) or "Other"
        addr = f"{int(r['Street Number'])} {r['Street Name']}" if pd.notna(r["Street Number"]) else ""
        rows.append(dict(roll_fy=2026, valued_jan1=2025, parcel=bl, description=d or f"LU {lu}",
                         units_change=int(bk.du), value_ratio_vs_median=round(bk.g, 2) if pd.notna(bk.g) else None,
                         treatment=st, project_type=t, address=addr,
                         year_built=int(r["Year Built"]) if pd.notna(r["Year Built"]) else None))
    return pd.DataFrame(rows)


def changes():
    """Every parcel's unit change on each roll FY2018-26, with its treatment and project type."""
    return pd.concat([rolls_fy18_25(), roll_fy26()], ignore_index=True)


def main():
    det = changes()
    det.to_csv(OUT / "assessor_unit_changes_detail_fy18_26.csv", index=False)
    k = det[det.treatment == "kept"]
    tab = k.pivot_table(index=["roll_fy", "valued_jan1"], columns="project_type", values="units_change",
                        aggfunc="sum", fill_value=0)
    order = ["Single-family", "2-3 family", "Condo", "Apartments 4-8", "Apartments 9+", "Mixed use",
             "Public / affordable", "Other"]
    tab = tab.reindex(columns=[c for c in order if c in tab.columns])
    tab["Net new homes"] = tab.sum(axis=1)
    side = det.pivot_table(index=["roll_fy", "valued_jan1"], columns="treatment", values="units_change",
                           aggfunc="sum", fill_value=0)
    tab["Assisted living / nursing (not counted)"] = side.get("assisted living / nursing", 0)
    tab["Removed: records / excluded uses"] = side.get("record only", 0) + side.get("excluded use", 0)
    tab["Raw change"] = det.groupby(["roll_fy", "valued_jan1"]).units_change.sum()
    tab = tab.reset_index()
    tab.to_csv(OUT / "assessor_new_units_by_type_fy18_26.csv", index=False)
    pd.set_option("display.width", 250)
    print(tab.to_string(index=False))
    print("\nTotals:", tab.drop(columns=["roll_fy", "valued_jan1"]).sum().to_dict())
    print("\nFY2026 changes:")
    print(det[det.roll_fy == 2026].query("abs(units_change) >= 2").sort_values("units_change").to_string(index=False))


if __name__ == "__main__":
    main()
