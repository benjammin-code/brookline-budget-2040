"""
What a family-sized home costs, town by town: houses and condominiums with six or more rooms.

Bedrooms are not recorded statewide, so "family-sized" is six or more rooms. Checked against
Brookline's own assessor export, which records bedrooms: of Brookline's single-family homes and
condominiums, "6+ rooms" matches "3+ bedrooms" for 92.5% of homes (it catches 95% of 3+ bedroom
homes, and 91% of the homes it flags have 3+ bedrooms).

Source: MassGIS Standardized Assessors' Parcels, one assessing table per town, from
  https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/l3parcels/L3_SHP_M<id>_<TOWN>.zip
(the *Assess*.dbf table is kept in data/gis/massgis_l3_assess/; vintages differ by town, see the
fiscal_year column). Fields used: USE_CODE (101 single-family, 102 condominium), NUM_ROOMS,
RES_AREA, TOTAL_VAL, LS_DATE / LS_PRICE (the most recent sale only).

Sales: the most recent sale recorded on each home, 2023-2025, at least $100,000 and at least half
the assessed value (to drop family transfers and other non-market sales).

Writes output/family_housing_by_town.csv. Run from scripts/:  python3 family_housing_by_town.py
"""
import csv
import glob
import statistics as st
import struct
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "gis" / "massgis_l3_assess"
OUT = ROOT / "output" / "family_housing_by_town.csv"


def read_dbf(path):
    with open(path, "rb") as f:
        hdr = f.read(32)
        n = struct.unpack("<I", hdr[4:8])[0]
        hl, rl = struct.unpack("<HH", hdr[8:12])
        fields = []
        while True:
            d = f.read(32)
            if d[0] == 0x0D:
                break
            fields.append((d[:11].split(b"\0")[0].decode(), chr(d[11]), d[16]))
        f.seek(hl)
        for _ in range(n):
            rec = f.read(rl)
            if not rec or rec[:1] == b"*":
                continue
            pos, r = 1, {}
            for name, t, ln in fields:
                v = rec[pos:pos + ln].decode("latin-1").strip()
                pos += ln
                if t in "NF":
                    try:
                        v = float(v) if v else None
                    except ValueError:
                        v = None
                r[name] = v
            yield r


def q(vals, p):
    vals = sorted(vals)
    return vals[int(p * (len(vals) - 1))] if vals else None


def main():
    rows = []
    for path in sorted(glob.glob(str(SRC / "*Assess*.dbf"))):
        recs = [r for r in read_dbf(path) if (r["USE_CODE"] or "")[:3] in ("101", "102")]
        town = path.split("/")[-1]
        fam = [r for r in recs if (r["NUM_ROOMS"] or 0) >= 6]
        sold = [r for r in fam if (r["LS_DATE"] or "")[:4] in ("2023", "2024", "2025")
                and (r["LS_PRICE"] or 0) >= 100_000 and r["LS_PRICE"] >= 0.5 * (r["TOTAL_VAL"] or 0)]
        sold_sf = [r["LS_PRICE"] for r in sold if r["USE_CODE"][:3] == "101"]
        sold_co = [r["LS_PRICE"] for r in sold if r["USE_CODE"][:3] == "102"]
        prices = [r["LS_PRICE"] for r in sold]
        city = recs[0]["CITY"] if recs and recs[0].get("CITY") else town
        rows.append(dict(
            town=(recs[0].get("CITY") or town).title(), source_table=town, fiscal_year=int(recs[0]["FY"] or 0),
            homes_houses_and_condos=len(recs), family_sized=len(fam),
            family_sized_pct=round(len(fam) / len(recs), 3),
            family_sized_condos=sum(1 for r in fam if r["USE_CODE"][:3] == "102"),
            median_assessed_family_sized=round(st.median(r["TOTAL_VAL"] for r in fam)),
            sales_2023_25=len(sold), median_sale_family_sized=round(st.median(prices)) if prices else None,
            p25_sale_family_sized=round(q(prices, 0.25)) if prices else None,
            median_sale_house_6plus=round(st.median(sold_sf)) if sold_sf else None, house_sales=len(sold_sf),
            median_sale_condo_6plus=round(st.median(sold_co)) if sold_co else None, condo_sales=len(sold_co),
        ))
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT.name}: {len(rows)} towns")


if __name__ == "__main__":
    main()
