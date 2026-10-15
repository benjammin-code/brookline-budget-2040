"""
Massachusetts vs national local-government pay, BLS QCEW, 2014-2024.

The expense driver tree prices personnel growth with the national Employment
Cost Index for state and local government workers, because BLS does not publish
the ECI by state. This is the check on that choice: QCEW average annual pay for
local government (ownership code 3, all industries), Massachusetts (area 25000)
against the US (US000). Same measure on both sides, so the comparison is fair
even though QCEW average pay is not a fixed-weight index like the ECI (it moves
with the mix of jobs as well as with pay rates).

The QCEW open-data API serves 2014 onward; earlier years need the bulk files.
Caches to data/qcew_cache/ and will not re-fetch.

Run from `scripts/`:  python3 fetch_qcew_local_gov_pay.py
"""

import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
CACHE = ROOT / "data" / "qcew_cache"
OUT = ROOT / "output" / "qcew_local_gov_pay_ma_us_2014_24.csv"
YEARS = range(2014, 2025)
AREAS = {"25000": "ma", "US000": "us"}


def fetch(area, year):
    f = CACHE / f"{area}_{year}.csv"
    if not f.exists() or f.stat().st_size < 1000:
        CACHE.mkdir(parents=True, exist_ok=True)
        url = f"https://data.bls.gov/cew/data/api/{year}/a/area/{area}.csv"
        subprocess.run(["curl", "-s", "-m", "60", "-A", "Mozilla/5.0", url, "-o", str(f)],
                       check=True)
    return f


def main():
    rows = []
    for y in YEARS:
        row = {"year": y}
        for area, tag in AREAS.items():
            for r in csv.DictReader(open(fetch(area, y))):
                if (r["own_code"] == "3" and r["industry_code"] == "10"
                        and r["size_code"] == "0"):
                    row[f"{tag}_local_gov_avg_pay"] = int(r["avg_annual_pay"])
                    row[f"{tag}_local_gov_employment"] = int(r["annual_avg_emplvl"])
        rows.append(row)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    a, b = rows[0], rows[-1]
    n = b["year"] - a["year"]
    for tag in AREAS.values():
        g = (b[f"{tag}_local_gov_avg_pay"] / a[f"{tag}_local_gov_avg_pay"]) ** (1 / n) - 1
        print(f"  {tag.upper()} local government average pay {a['year']}-{b['year']}: "
              f"{g*100:.2f}%/yr")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
