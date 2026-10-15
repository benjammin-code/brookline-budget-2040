"""
Police and fire workload, FY2003-2025, from the Town's own Financial Plans.

Each Financial Plan's department pages carry a "Performance / Workload
Indicators" table with two actual years (the columns alternate actual and
estimate). Sixteen plans, FY2006-FY2027, give most years. Values below are
transcribed from those tables; `scripts/` has no parser for them because the
layout changes from plan to plan and several plans repeat one year's values
under another year's label, which a parser would silently accept.

Rules used:
  - Only ACTUAL columns are used, never estimates.
  - Where two plans report the same year, they must agree; where they do, the
    value is marked `confirmed`.
  - Where the same set of values appears under two different years (a copy
    carried into the wrong column), both years are marked `duplicate` and left
    out of trend calculations.
  - FY2019-23 gaps (added 2026-10-10) come from the FY2021-FY2025 budgets, which
    exist only as OpenGov "stories" with the tables as images; copies are in
    data/fire_reports/opengov_images/ and each value was checked against them.
    Reported fire totals are used throughout; the components sum to 97-99% of them.

Housing units: Census April 2010 (26,448) and April 2020 (27,961), linear
between, extended at the 2010-20 pace (151/yr) outside it.

Run from `scripts/`:  python3 public_safety_workload.py
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "output" / "public_safety_workload_fy03_25.csv"
METHOD = ROOT / "output" / "public_safety_workload_methodology.md"

# fiscal_year: (police_related_calls, self_initiated_police, fire_total_responses,
#               medical_emergencies, source, flag)
DATA = {
    2003: (56957, None, 6583, 3360, "FY2006 plan", ""),
    2004: (62684, None, 7128, 3370, "FY2006 plan", ""),
    2005: (63481, None, 7250, 3675, "FY2008 plan", ""),
    2006: (66445, None, 7687, 4007, "FY2008 plan", ""),
    2007: (71721, None, 7701, 4001, "FY2010 plan", ""),
    2008: (65671, None, 7246, 3465, "FY2010 plan", ""),
    2009: (66817, None, 7485, 4105, "FY2012 plan", ""),
    2010: (64772, None, 7567, 4132, "FY2012 plan", "fire duplicate: same values shown as FY2012 in FY2014/FY2015 plans"),
    2011: (68937, None, 8463, 5117, "FY2014 plan", ""),
    2012: (69318, None, 7567, 4132, "FY2014, FY2015 plans", "fire duplicate: same values shown as FY2010 in FY2012 plan; police confirmed"),
    2013: (75596, None, 7347, 3681, "FY2015, FY2016 plans", "confirmed"),
    2014: (75525, 20907, 7191, 3737, "FY2016, FY2017 plans", "fire confirmed"),
    2015: (75525, 25204, 7780, 3969, "FY2017, FY2018 plans", "police duplicate: 75,525 also shown as FY2014; fire confirmed"),
    2016: (72708, 25463, 7685, 3838, "FY2018, FY2019 plans", "confirmed"),
    2017: (72012, 25319, 8053, 4550, "FY2019, FY2020 plans", "confirmed"),
    2018: (67117, 26657, 8298, 4530, "FY2020 plan", ""),
    2019: (68505, 26657, 8523, 3954, "OpenGov FY2022 budget (Fire, Police); police repeated in FY2024, FY2025",
           "police self-initiated equals FY2018's 26,657, likely carried over"),
    2020: (59611, 30622, 7980, 3859, "FY2023 plan; OpenGov FY2022 budget", "fire total from OpenGov FY2022"),
    2021: (52978, 23541, 7862, 3797, "FY2023, FY2026 plans; OpenGov FY2024 budget",
           "fire total as reported (components sum to 7,787)"),
    2022: (56167, 22524, 9089, 4227, "FY2026 plan; OpenGov FY2024, FY2025 budgets",
           "fire total as reported (components sum to 9,027); the FY2025 OpenGov table repeats FY2021's 7,862 here, not used"),
    2023: (50000, 26000, 9358, 4579, "FY2026, FY2027 plans; OpenGov FY2025 budget",
           "police figures are round numbers (50,000 and 26,000) labelled actual; fire confirmed"),
    2024: (52529, 19871, 9976, 4739, "FY2026, FY2027 plans", "confirmed"),
    2025: (55619, 26197, 10491, 5060, "FY2027 plan", ""),
}


def units(fy):
    return 26448 + (27961 - 26448) / 10 * (fy - 2010)


def cagr(a, b, n):
    return (b / a) ** (1 / n) - 1


def main():
    rows = []
    for fy, (pol, selfi, fire, med, src, flag) in sorted(DATA.items()):
        u = units(fy)
        rows.append(dict(fiscal_year=fy, police_related_calls=pol, self_initiated_police_calls=selfi,
                         fire_total_responses=fire, medical_emergencies=med,
                         housing_units_est=round(u),
                         fire_responses_per_1000_units=round(fire / u * 1000, 1) if fire else None,
                         medical_per_1000_units=round(med / u * 1000, 1) if med else None,
                         police_calls_per_1000_units=round(pol / u * 1000, 1) if pol else None,
                         source=src, flag=flag))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    ok = lambda fy, col, kind: (DATA[fy][col] is not None and
                                not ("duplicate" in DATA[fy][5] and kind in DATA[fy][5]))
    print("Growth rates (clean years only):")
    windows = [("fire total responses", 2, "fire", [(2003, 2018), (2013, 2018), (2018, 2025), (2013, 2025)]),
               ("medical emergencies", 3, "fire", [(2003, 2018), (2013, 2025), (2021, 2025)]),
               ("police-related calls", 0, "police", [(2003, 2013), (2013, 2018), (2016, 2024)])]
    for label, col, kind, ws in windows:
        for a, b in ws:
            if ok(a, col, kind) and ok(b, col, kind):
                g = cagr(DATA[a][col], DATA[b][col], b - a)
                print(f"  {label:22s} FY{a}-FY{b}: {DATA[a][col]:>6,} -> {DATA[b][col]:>6,}  "
                      f"{g*100:+5.2f}%/yr   (housing units {cagr(units(a), units(b), b-a)*100:+.2f}%/yr)")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
