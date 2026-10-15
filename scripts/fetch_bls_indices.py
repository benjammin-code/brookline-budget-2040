"""
Fetch and cache the external price indices Phase B needs.

Phase A measured cost per FTE. It cannot say how much of that is the wage
inflation every public employer faced and how much is Brookline-specific (step
progression, turnover, role mix), because nothing internal to the Town separates
them. That needs an index from outside the Town's own books.

## The series, with their titles verified rather than assumed

Fetched from FRED, which mirrors the BLS series under the same identifiers.

  CIU3010000000000I  ECI: Total compensation for State and local government
                     workers in All industries and occupations
  CIU3020000000000I  ECI: Wages and salaries, same worker group
  CIU3030000000000I  ECI: Benefits, same worker group
  CUURA103SA0        CPI-U: All Items in Boston-Cambridge-Newton, MA-NH (CBSA)

**The owner code was checked, not inferred, and the first guess was wrong.**
`CIU2010000000000I` looks like it should be the state-and-local series and is in
fact *Private industry workers*; the owner digit is position 4, and state and
local government is 3, not 2. Running Phase B against the private-industry index
would have produced a plausible, wrong residual with nothing to signal the error,
so each title above was read off its own series page before use.

## Why the ECI and not CPI

Municipal cost is mostly compensation, and compensation has not tracked consumer
prices. Deflating by CPI would attribute to "Brookline did something" what is
really "public-sector pay moved differently from grocery prices." Boston CPI is
fetched anyway, as context and for the non-personnel share of each bucket, where
a general price level is the more appropriate comparison.

## The limitation to state in the write-up

The ECI is national. It is not published for metro areas at this level of
industry detail, so a national state-and-local index is the closest available
match on *occupation mix*, which matters more than geography for this question.
If Massachusetts public-sector pay grew faster than the national average, the
Brookline-specific residual this produces is overstated by that difference. The
Boston CPI gives a partial read on how much that gap might be.

Uses curl rather than urllib because this machine's Python SSL store cannot
verify the certificate chain.

Run from `scripts/`:  python3 fetch_bls_indices.py
"""

import csv
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
CACHE = ROOT / "data" / "bls_cache"
OUT_CSV = ROOT / "output" / "price_indices_annual.csv"

SERIES = {
    "CIU3010000000000I": ("eci_total_comp", "quarterly",
                          "ECI: Total compensation, State and local government workers"),
    "CIU3020000000000I": ("eci_wages", "quarterly",
                          "ECI: Wages and salaries, State and local government workers"),
    "CIU3030000000000I": ("eci_benefits", "quarterly",
                          "ECI: Benefits, State and local government workers"),
    "CUURA103SA0": ("cpi_boston", "bimonthly",
                    "CPI-U: All Items, Boston-Cambridge-Newton MA-NH"),
}

# Observations per complete year. Boston CPI is published bimonthly (six
# times a year), not monthly - checked against the series rather than assumed,
# after a monthly assumption rejected every year from 1953 on.
PERIODS = {"quarterly": 4, "monthly": 12, "bimonthly": 6}


def fetch(series_id):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{series_id}.csv"
    if not path.exists():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        res = subprocess.run(["curl", "-s", "--max-time", "60", "-f", url],
                             capture_output=True, text=True)
        if res.returncode != 0 or res.stdout.lstrip().startswith("<"):
            raise SystemExit(f"Fetch failed for {series_id}")
        path.write_text(res.stdout)
    rows = list(csv.reader(path.read_text().splitlines()))
    return rows[1:]


def annualize(rows, per_year):
    """Annual mean. A year is only reported when every period is present, so no
    partial year is ever compared against a full one."""
    by_year = defaultdict(list)
    for r in rows:
        if len(r) < 2 or r[1] in ("", "."):
            continue
        by_year[int(r[0][:4])].append(float(r[1]))
    full = {y: sum(v) / len(v) for y, v in by_year.items() if len(v) == per_year}
    partial = {y: len(v) for y, v in by_year.items() if len(v) != per_year}
    return full, partial


def main():
    annual, titles = {}, {}
    for sid, (name, freq, title) in SERIES.items():
        rows = fetch(sid)
        full, partial = annualize(rows, PERIODS[freq])
        annual[name] = full
        titles[name] = title
        yrs = sorted(full)
        print(f"  {name:16s} {len(full):3d} complete years {yrs[0]}-{yrs[-1]}"
              + (f"   excluded as partial: {sorted(partial)}" if partial else ""))

    years = sorted(set.intersection(*[set(v) for v in annual.values()]))
    names = list(annual)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["calendar_year"] + names + [n + "_yoy" for n in names])
        for i, y in enumerate(years):
            row = [y] + [round(annual[n][y], 4) for n in names]
            row += [round(annual[n][y] / annual[n][years[i - 1]] - 1, 6) if i else ""
                    for n in names]
            w.writerow(row)
    print(f"\nWrote {OUT_CSV}  ({len(years)} years, {years[0]}-{years[-1]})")

    print("\n  Compound annual growth, and note how far apart these are:")
    for w0, w1 in [(years[0], years[-1]), (2011, 2020), (2021, 2025)]:
        if w0 not in years or w1 not in years:
            continue
        n = w1 - w0
        parts = "  ".join(f"{n_}={((annual[n_][w1]/annual[n_][w0])**(1/n)-1)*100:5.2f}%"
                          for n_ in names)
        print(f"    {w0}-{w1}:  {parts}")
    print("\n  Titles verified against each series page before use:")
    for n in names:
        print(f"    {n:16s} {titles[n]}")


if __name__ == "__main__":
    main()
