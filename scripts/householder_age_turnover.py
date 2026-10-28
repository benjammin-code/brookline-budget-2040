"""
Will more family-sized homes turn over to families as Brookline's owners age? Owner households by
age of householder in the 2000, 2010 and 2020 Censuses give how many owners of each age leave over a
decade; applied to 2020's ages, they say how many homes older owners will leave in the 2020s and
2030s against the 2000s and 2010s. The Census Bureau's household survey records (Brookline, Dedham
and Milton, 2020-2024) say how many of those homes have 3+ bedrooms and how many public school
students the households moving into such homes bring.

Census tables (Brookline town, all owner-occupied homes; the decennial Census has no bedrooms):
  2000 Summary File 1, H16  tenure by age of householder   ma00037_uf1.zip, segment 37, cells 116-134
  2010 Summary File 1, H17  tenure by age of householder   ma2010.sf1.zip, segment 44, cells 119-139
  2020 DHC, H13             tenure by age of householder   ma2020.dhc.zip, segment 02, cells 102-122
Each table was found by its structure (occupied = owners + renters, each the sum of its age groups) and
checked against the town's occupied homes. The counts are written to
data/demographics/householder_age_tenure_2000_2020.csv; the state files are not kept (argv[1] is
their folder, to re-extract; without it the saved counts are used).

A cohort's "exit" is net: owners of an age group in one Census against owners ten years older in the
next. Owners who arrive at older ages, and households whose householder changes (a spouse, an adult
child), are netted in. It measures homes passing from one age group's owners, not deaths or sales.

Writes output/householder_age_turnover.csv, output/householder_age_turnover.json (for the site's chart) and prints the decade comparison.
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
SAVED = ROOT / "data/demographics/householder_age_tenure_2000_2020.csv"
OUT = ROOT / "output/householder_age_turnover.csv"
PUMS = ROOT / "data/demographics/pums"
GROUPS = ["15-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75-84", "85+"]


def num(x):
    try:
        return float(x)
    except ValueError:
        return -1.0


def extract(src):
    """Owners and renters by age of householder, Brookline town, from the three state files."""
    src, rows = Path(src), []
    # 2000: logical record of Brookline town (summary level 060) from the geography file
    z = zipfile.ZipFile(src / "2000/mageo_uf1.zip")
    lr = next(s[18:25] for s in (l.decode("latin-1") for l in z.open("mageo.uf1"))
              if s[8:11] == "060" and s[31:34] == "021" and s[36:41] == "09175")
    z = zipfile.ZipFile(src / "2000/ma00037_uf1.zip")
    v = next([num(x) for x in p[5:]] for p in (l.decode("latin-1").rstrip().split(",") for l in z.open("ma00037.uf1"))
             if p[4] == lr)[116:135]
    rows += [(2000, "owner", g, v[2 + i]) for i, g in enumerate(GROUPS)]
    rows += [(2000, "renter", g, v[11 + i]) for i, g in enumerate(GROUPS)]
    # 2010 and 2020 have nine age groups (55-59 and 60-64 separately); combined to 55-64
    for year, zf, geo, seg, sep, at, pick in [
            (2010, "2010/ma2010.sf1.zip", "mageo2010.sf1", "ma000442010.sf1", ",", 119,
             lambda s: s[18:25] if s[8:11] == "060" and s[29:32] == "021" and s[36:41] == "09175" else None),
            (2020, "2020/ma2020.dhc.zip", "mageo2020.dhc", "ma000022020.dhc", "|", 102,
             lambda s: (lambda p: p[7] if p[2] == "060" and p[14] == "021" and p[17] == "09175" else None)(s.split("|")))]:
        z = zipfile.ZipFile(src / zf)
        lr = next(r for r in (pick(l.decode("latin-1")) for l in z.open(geo)) if r)
        v = next([num(x) for x in p[5:]] for p in (l.decode("latin-1").rstrip().split(sep) for l in z.open(seg))
                 if p[4] == lr)[at:at + 21]
        assert v[0] == v[1] + v[11] and v[1] == sum(v[2:11]) and v[11] == sum(v[12:21]), year
        for t, o in (("owner", 2), ("renter", 12)):
            a = v[o:o + 9]
            rows += [(year, t, g, x) for g, x in zip(GROUPS, a[:4] + [a[4] + a[5]] + a[6:])]
    df = pd.DataFrame(rows, columns=["year", "tenure", "age_of_householder", "households"])
    df.households = df.households.astype(int)
    df.to_csv(SAVED, index=False)
    return df


def pums_big_homes():
    """Survey: share of older owners' homes with 3+ bedrooms; what recent arrivals to such homes bring."""
    h = pd.read_csv(PUMS / "pums_2020_24_puma00902_households.csv", dtype={"SERIALNO": str})
    p = pd.read_csv(PUMS / "pums_2020_24_puma00902_persons.csv", dtype={"SERIALNO": str})
    h = h[(h.TYPEHUGQ == 1) & h.TEN.notna()].copy()
    age = p[p.RELSHIPP == 20].set_index("SERIALNO").AGEP.rename("hage")
    p["pub"] = (p.SCH == 2) & p.SCHG.between(2, 14)
    p["under5"] = p.AGEP < 5
    k = p.groupby("SERIALNO")[["pub", "under5"]].sum()
    h = h.join(age, on="SERIALNO").join(k, on="SERIALNO").fillna({"pub": 0, "under5": 0})
    own = h.TEN.isin([1, 2])
    w = lambda d, x=None: (d.WGTP * (1 if x is None else x)).sum()
    old = h[own & (h.hage >= 55)]
    arr = h[(h.BDSP >= 3) & (h.MV <= 2)]   # moved in within about two years
    big = h[h.BDSP >= 3]
    # public students per 3+ bedroom home by years since the household moved in (MV codes 1-5)
    by_tenure = {k: w(big[big.MV.isin(c)], big[big.MV.isin(c)].pub) / w(big[big.MV.isin(c)])
                 for k, c in {"0-1": [1, 2], "2-4": [3], "5-9": [4], "10-19": [5]}.items()}
    leaving = old[old.BDSP >= 3]
    return {
        "by_tenure": by_tenure,
        "by_tenure_records": {k: int(big.MV.isin(c).sum()) for k, c in {"0-1": [1, 2], "2-4": [3], "5-9": [4], "10-19": [5]}.items()},
        "older_owner_records": len(leaving),
        "older_owners_3plus_pub_per_home": w(leaving, leaving.pub) / w(leaving),
        "older_owners_in_3plus_br": w(old[old.BDSP >= 3]) / w(old),
        "arrivals_pub_per_home": w(arr, arr.pub) / w(arr),
        "arrivals_under5_per_home": w(arr, arr.under5) / w(arr),
        "all_3plus_pub_per_home": w(h[h.BDSP >= 3], h[h.BDSP >= 3].pub) / w(h[h.BDSP >= 3]),
        "arrival_records": len(arr),
    }


def main():
    df = extract(sys.argv[1]) if len(sys.argv) > 1 else pd.read_csv(SAVED)
    o = df[df.tenure == "owner"].pivot(index="age_of_householder", columns="year", values="households").reindex(GROUPS)
    o.loc["75+"] = o.loc["75-84"] + o.loc["85+"]
    # decade retention: owners aged a in year t against owners aged a+10 in t+10 (75+ against 85+)
    nxt = {"35-44": "45-54", "45-54": "55-64", "55-64": "65-74", "65-74": "75-84", "75+": "85+"}
    keep = pd.DataFrame({t: {a: o.loc[b, t + 10] / o.loc[a, t] for a, b in nxt.items()} for t in (2000, 2010)})
    keep["average"] = keep.mean(axis=1)
    print("Owner households by age of householder, Brookline\n", o.astype(int).to_string(), "\n")
    print("Share of each owner age group still owning ten years later (net)\n", keep.round(3).to_string(), "\n")

    # homes older owners leave each decade: actual for the 2000s and 2010s, projected for the 2020s and 2030s
    old = ["55-64", "65-74", "75+"]
    exits = {f"{t}s": sum(o.loc[a, t] * (1 - keep.loc[a, t]) for a in old) for t in (2000, 2010)}
    ages2020 = {a: o.loc[a, 2020] for a in old + ["45-54"]}
    exits["2020s"] = sum(ages2020[a] * (1 - keep.loc[a, "average"]) for a in old)
    ages2030 = {"55-64": ages2020["45-54"] * keep.loc["45-54", "average"],
                "65-74": ages2020["55-64"] * keep.loc["55-64", "average"],
                "75+": ages2020["65-74"] * keep.loc["65-74", "average"] + ages2020["75+"] * keep.loc["75+", "average"]}
    exits["2030s"] = sum(ages2030[a] * (1 - keep.loc[a, "average"]) for a in old)

    s = pums_big_homes()

    # for the site's chart: owners by age in each Census and projected for 2030, and the decade rates
    proj = {"45-54": o.loc["35-44", 2020] * keep.loc["35-44", "average"],
            "55-64": ages2030["55-64"], "65-74": ages2030["65-74"],
            "75-84": ages2020["65-74"] * keep.loc["65-74", "average"],
            "85+": ages2020["75+"] * keep.loc["75+", "average"]}
    r = keep["average"]
    proj40 = {"55-64": proj["45-54"] * r["45-54"], "65-74": proj["55-64"] * r["55-64"],
              "75-84": proj["65-74"] * r["65-74"], "85+": (proj["75-84"] + proj["85+"]) * r["75+"]}
    flows = {
        "owners": {str(t): {a: int(o.loc[a, t]) for a in ["45-54", "55-64", "65-74", "75-84", "85+"]} for t in (2000, 2010, 2020)},
        "projected_2030": {a: round(v) for a, v in proj.items()},
        "projected_2040": {a: round(v) for a, v in proj40.items()},   # no 45-54: it would need 2030's 35-44
        "still_owning": {str(t): {a: round(keep.loc[a, t], 3) for a in ["45-54", "55-64", "65-74", "75+"]} for t in (2000, 2010)},
        "still_owning_average": {a: round(keep.loc[a, "average"], 3) for a in ["45-54", "55-64", "65-74", "75+"]},
        "students_by_years_in_home": {k: round(v, 3) for k, v in s["by_tenure"].items()},
        "students_by_years_in_home_records": s["by_tenure_records"],
        "students_older_owners_leaving": round(s["older_owners_3plus_pub_per_home"], 3),
        "older_owners_leaving_records": s["older_owner_records"],
    }
    (ROOT / "output/householder_age_turnover.json").write_text(json.dumps(flows, indent=1))
    rows = []
    for dec, n in exits.items():
        big = n * s["older_owners_in_3plus_br"]
        rows.append({"decade": dec, "kind": "actual" if dec in ("2000s", "2010s") else "projected",
                     "older_owner_exits": round(n), "per_year": round(n / 10),
                     "of_which_3plus_br": round(big), "3plus_br_per_year": round(big / 10)})
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False), "\n")
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in s.items() if k != "by_tenure"})
    print("public students per 3+ bedroom home by years since moving in:",
          {k: round(v, 2) for k, v in s["by_tenure"].items()})

    # Students in FY2040 from turnover above today's pace. The forecast's grade ratios come from recent
    # years, so the pace of the early 2020s is already in them; only the increase after that is extra.
    # Annual pace: each decade's per-year figure at its midpoint, straight line between, extended to 2040.
    mid = {2005: rows[0]["3plus_br_per_year"], 2015: rows[1]["3plus_br_per_year"],
           2025: rows[2]["3plus_br_per_year"], 2035: rows[3]["3plus_br_per_year"]}
    pace = lambda y: np.interp(y, list(mid), list(mid.values()), right=None) if y <= 2035 else \
        mid[2035] + (mid[2035] - mid[2025]) / 10 * (y - 2035)
    base_year = 2024   # center of the years behind the grade ratios
    dep = s["older_owners_3plus_pub_per_home"]
    net = lambda t: (s["by_tenure"]["0-1"] if t <= 1 else s["by_tenure"]["2-4"] if t <= 4
                     else s["by_tenure"]["5-9"] if t <= 9 else s["by_tenure"]["10-19"]) - dep
    extra = {y: pace(y) - pace(base_year) for y in range(2026, 2040)}
    students = sum(n * net(2039 - y) for y, n in extra.items())   # moved in during year y, counted fall 2039
    print(f"\nextra turnover homes 2026-2039: {sum(extra.values()):.0f}; "
          f"extra public students in FY2040: {students:.0f} (net of {dep:.2f} students in the homes they leave)")
    # the same sum by when the home changed hands, as the topic page's table shows it
    for first, last in ((2026, 2029), (2030, 2034), (2035, 2037), (2038, 2039)):
        ys = range(first, last + 1)
        print(f"  changed hands {first}-{last}: {sum(extra[y] for y in ys):.0f} extra homes x "
              f"{net(2039 - first):.2f} = {sum(extra[y] * net(2039 - y) for y in ys):.0f} students")
    print("  extra students by fiscal year:", {f + 1: round(sum(extra[y] * net(f - y) for y in range(2026, f + 1)))
                                               for f in range(2029, 2040)})

    # the "Families moving in" setting that gives the same FY2040 change
    sys.path.insert(0, str(ROOT / "scripts"))
    import expense_driver_forecast as edf
    byn = edf.enrollment_by_exponent()
    e40 = lambda m: sum(v[2040] * (1 + m) ** n for n, v in byn.items())
    lo, hi = -0.01, 0.02
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if e40(m) - e40(0) < students else (lo, m)
    print(f"matching setting: {m * 100:+.2f} point a year (FY2040 {e40(0):.0f} -> {e40(m):.0f})")
    print("wrote", OUT.relative_to(ROOT), "and", SAVED.relative_to(ROOT))


if __name__ == "__main__":
    main()
