"""
Pull Brookline's census blocks out of the 2010 and 2020 statewide summary files.

For each block: total population, children under 5, children 5 to 17, housing units,
occupied units, owner- and renter-occupied units.

Sources (URLs in data/SOURCES.md; the state zips are not kept, pass their folder as argv[1]):
  ma2010.sf1.zip   Census 2010 Summary File 1, Massachusetts
                   geo: mageo2010.sf1 (fixed width); P12 in segment 04 at data offset 144;
                   H3 occupancy and H4 tenure at the start of segment 44
  ma2020.dhc.zip   Census 2020 Demographic and Housing Characteristics File, Massachusetts
                   geo: mageo2020.dhc (pipe); P12 in segment 06 at data offset 144;
                   H1 at offset 0, H3 at 5, H10 tenure at 142 in segment 01

Writes data/demographics/blocks/brookline_blocks_{2010,2020}.csv. The town totals are
checked against the counts already in data/demographics (population 58,732 and 63,191).
"""

import csv
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data/demographics/blocks"
TOWN_POP = {2010: 58732, 2020: 63191}


def p12_cells(v):
    """Under 5 and 5-17 from the 49 P12 cells (male ages at 2-24, female at 26-48)."""
    assert v[1] + v[25] == v[0]
    return v[2] + v[26], v[3] + v[4] + v[5] + v[27] + v[28] + v[29]


def rows(z, name, sep, logrecs):
    with z.open(name) as f:
        for line in f:
            p = line.decode("latin-1").rstrip("\r\n").split(sep)
            if p[4] in logrecs:
                yield p[4], [int(x) if x.lstrip("-").isdigit() else x for x in p[5:]]


def blocks_2010(z):
    geo = {}
    with z.open("mageo2010.sf1") as f:
        for line in f:
            s = line.decode("latin-1")
            if s[8:11] == "101" and s[29:32] == "021" and s[36:41] == "09175":
                geo[s[18:25]] = "25021" + s[54:60] + s[61:65]
    out = {lr: {"geoid": g} for lr, g in geo.items()}
    for lr, d in rows(z, "ma000042010.sf1", ",", geo):
        out[lr]["pop"] = d[144]
        out[lr]["age0_4"], out[lr]["age5_17"] = p12_cells(d[144:193])
    for lr, d in rows(z, "ma000442010.sf1", ",", geo):
        out[lr].update(units=d[0], occupied=d[1], owner=d[4] + d[5], renter=d[6])
        assert d[1] == d[4] + d[5] + d[6]
    return out


def blocks_2020(z):
    geo = {}
    with z.open("mageo2020.dhc") as f:
        for line in f:
            p = line.decode("latin-1").split("|")
            if p[2] == "100" and p[14] == "021" and p[17] == "09175":
                geo[p[7]] = p[9]
    out = {lr: {"geoid": g} for lr, g in geo.items()}
    for lr, d in rows(z, "ma000062020.dhc", "|", geo):
        out[lr]["pop"] = d[144]
        out[lr]["age0_4"], out[lr]["age5_17"] = p12_cells(d[144:193])
    for lr, d in rows(z, "ma000012020.dhc", "|", geo):
        out[lr].update(units=d[0], occupied=d[6], owner=d[143], renter=d[151])
        assert d[6] == d[143] + d[151]
    return out


def main(src):
    OUT.mkdir(parents=True, exist_ok=True)
    for year, zname, fn in [(2010, "ma2010.sf1.zip", blocks_2010), (2020, "ma2020.dhc.zip", blocks_2020)]:
        with zipfile.ZipFile(Path(src) / zname) as z:
            b = fn(z)
        recs = sorted(b.values(), key=lambda r: r["geoid"])
        assert sum(r["pop"] for r in recs) == TOWN_POP[year], "block populations do not sum to the town"
        cols = ["geoid", "pop", "age0_4", "age5_17", "units", "occupied", "owner", "renter"]
        with open(OUT / f"brookline_blocks_{year}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(recs)
        tot = {k: sum(r[k] for r in recs) for k in cols[1:]}
        print(year, len(recs), "blocks", tot)


if __name__ == "__main__":
    main(sys.argv[1])
