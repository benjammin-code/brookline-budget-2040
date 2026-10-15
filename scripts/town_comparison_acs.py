"""
Census ACS 5-year estimates for every Massachusetts town, two periods (2015-19 and 2020-24), for
the Brookline-versus-Lexington comparison (why families settle where they do).

Source: the Census Bureau's table-based summary files, one national file per table:
  2020-24  https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-<table>.dat
  2015-19  https://www2.census.gov/programs-surveys/acs/summary_file/2019/prototype/5YRData/acsdt5y2019-<table>.dat
Column meanings from the table shells in the same directories. Only Massachusetts county
subdivisions (GEO_ID 0600000US25...) are kept, plus the state row (0400000US25).

Writes data/demographics/acs5yr/ma_towns_<table>_<year>.csv (estimate columns only) and
output/ma_towns_acs_profile.csv (derived measures per town and period). The national files are
downloaded to a temporary folder and not kept.

Run from scripts/:  python3 town_comparison_acs.py
"""
import csv
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
SAVE = ROOT / "data" / "demographics" / "acs5yr"
URL = {2024: "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-{t}.dat",
       2019: "https://www2.census.gov/programs-surveys/acs/summary_file/2019/prototype/5YRData/acsdt5y2019-{t}.dat"}
TABLES = ["b01001", "b25077", "b25064", "b25003", "b25041", "b25024", "b11005", "b19013", "b07001", "b25031"]


def fetch(table, year, tmp):
    out = SAVE / f"ma_towns_{table}_{year}.csv"
    if out.exists():
        return out
    dat = Path(tmp) / f"{table}_{year}.dat"
    subprocess.run(["curl", "-s", "-f", "-o", str(dat), URL[year].format(t=table)], check=True)
    with open(dat) as fh, open(out, "w", newline="") as fo:
        head = fh.readline().rstrip("\n").split("|")
        keep = [i for i, h in enumerate(head) if i == 0 or "_E" in h]
        w = csv.writer(fo)
        w.writerow([head[i] for i in keep])
        for line in fh:
            if line.startswith(("0600000US25", "0400000US25")):
                parts = line.rstrip("\n").split("|")
                w.writerow([parts[i] for i in keep])
    dat.unlink()
    return out


def load(table, year):
    with open(SAVE / f"ma_towns_{table}_{year}.csv") as fh:
        rows = list(csv.DictReader(fh))
    return {r["GEO_ID"]: {k.replace("_E", "_"): float(v) if v not in ("", None) else None
                          for k, v in r.items() if k != "GEO_ID"} for r in rows}


def names():
    """GEO_ID -> town name, from the 2024 geography file (downloaded once, small rows kept)."""
    f = SAVE / "ma_towns_geos_2024.csv"
    if not f.exists():
        url = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/documentation/Geos20245YR.txt"
        txt = subprocess.run(["curl", "-s", "-f", url], check=True, capture_output=True, text=True).stdout
        with open(f, "w", newline="") as fo:
            w = csv.writer(fo); w.writerow(["GEO_ID", "name"])
            for line in txt.splitlines():
                parts = line.split("|")
                if len(parts) > 41 and parts[40].startswith(("0600000US25", "0400000US25")):
                    w.writerow([parts[40], parts[41].split(",")[0].replace(" town", "").replace(" city", "").replace(" Town", "")])
    return {r["GEO_ID"]: r["name"] for r in csv.DictReader(open(f))}


def profile(year):
    T = {t: load(t, year) for t in TABLES}
    out = {}
    for g in T["b01001"]:
        a, b = T["b01001"][g], lambda t, n: T[t].get(g, {}).get(f"{t.upper()}_{n:03d}")
        pop = a["B01001_001"]
        if not pop or pop < 1000 or g not in T["b07001"]:   # unpopulated areas and the smallest towns
            continue
        age = lambda cells: sum(a[f"B01001_{c:03d}"] + a[f"B01001_{c + 24:03d}"] for c in cells)
        mob = T["b07001"].get(g, {})
        kids_1_17 = mob["B07001_002"] + mob["B07001_003"]
        kids_from_outside = sum(mob[f"B07001_{base + k:03d}"] for base in (49, 65, 81) for k in (1, 2))
        a30_44 = sum(mob[f"B07001_{c:03d}"] for c in (7, 8, 9))
        a30_44_outside = sum(mob[f"B07001_{base + k:03d}"] for base in (49, 65, 81) for k in (6, 7, 8))
        hu = b("b25041", 1)
        out[g] = dict(
            population=pop, under5_pct=age([3]) / pop, age5_17_pct=age([4, 5, 6]) / pop,
            age25_34_pct=age([11, 12]) / pop, age35_44_pct=age([13, 14]) / pop, age65plus_pct=age(range(20, 26)) / pop,
            hh_with_children_pct=b("b11005", 2) / b("b11005", 1),
            median_home_value=b("b25077", 1), median_gross_rent=b("b25064", 1), median_hh_income=b("b19013", 1),
            owner_pct=b("b25003", 2) / b("b25003", 1),
            single_family_pct=(b("b25024", 2) + b("b25024", 3)) / b("b25024", 1),
            three_plus_bedroom_pct=(b("b25041", 5) + b("b25041", 6) + b("b25041", 7)) / hu,
            kids_moved_in_from_outside_county_pct=kids_from_outside / kids_1_17,
            adults30_44_moved_in_from_outside_county_pct=a30_44_outside / a30_44,
        )
    return out


def main():
    with tempfile.TemporaryDirectory() as tmp:
        for t in TABLES:
            for y in (2019, 2024):
                fetch(t, y, tmp)
    nm = names()
    rows = []
    for year in (2019, 2024):
        for g, d in profile(year).items():
            rows.append(dict(period=f"{year - 4}-{year}", geo_id=g, town=nm.get(g, g), **d))
    out = ROOT / "output" / "ma_towns_acs_profile.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {out.name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
