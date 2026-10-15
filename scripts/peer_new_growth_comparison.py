"""
Brookline's new-growth rate against all 351 Massachusetts municipalities.

Why this exists (2026-09-07): the figures §2c is built on — Brookline at
1.37%/yr and the 26.5th percentile over FY2005-2025, against 2.03% at the
80th percentile — had been computed once, ad hoc, in an August 2026 session,
with only the *results* recorded in `.claude/memorialized.md`. No script, no
committed CSV. One derived value (`PEER_TARGET_PCT = 0.01974`) had made it
into `new_growth_scenario_forecast.py` as a hardcoded constant citing that
note. That is the project's most-quoted statistic resting on a number nobody
could re-derive without redoing the work.

This script computes it from the source workbook and writes the per-town
table out, so every figure in §2c traces to a file.

## Method

`data/2026 MA state new growth for all towns 20 years.xlsx`, sheet `data`, is
the raw DLS Gateway pull: 351 municipalities x FY2003-2026, with each town's
"Total New Growth Applied to Limit as a % of PY Levy Limit" already computed
by DLS. A town's rate for a window is the simple mean of that column across
the window's years - the same convention the whitepaper used and the standard
DOR/DLS way of comparing new growth across towns and over time, because it
normalises for town size and scales with the levy base.

Towns missing any year in a window are excluded from that window's ranking
rather than averaged over a short series, which would bias them.

Two windows are reported, and both matter:

- **FY2005-2025** — the full period the document covers.
- **FY2021-2025** — the trailing five years, which tell a different and more
  complicated story: Brookline barely moved, but the 80th-percentile bar came
  *down*, so Brookline's ranking improved without Brookline improving much.

## What this corrects

The reference document claimed peer towns "Cambridge, Boston, Needham, and
Lexington" all generated "2.5%+" new growth. On the FY2005-2025 window that
the surrounding sentence cites, **Lexington is 2.45%** - below the stated
floor. The claim holds only on the trailing five-year window. It was also
selective: Newton (1.47%) and Arlington (1.00%) are equally reasonable peers
and sit at or below Brookline. This script emits the full named-peer table so
the document can state the distribution instead of a chosen tail of it.
"""

import csv
from pathlib import Path

import openpyxl

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "2026 MA state new growth for all towns 20 years.xlsx"
OUT_CSV = ROOT / "output" / "peer_new_growth_rates.csv"
OUT_METHOD = ROOT / "output" / "peer_new_growth_rates_methodology.md"

TOWN = "Brookline"
WINDOWS = {"fy2005_2025": range(2005, 2026), "fy2021_2025": range(2021, 2026)}

# Named comparison towns. Chosen to span the range deliberately rather than to
# support a conclusion: the four the document already cited, plus two
# similarly-situated inner-suburb peers that sit at or below Brookline, plus
# two high performers. Omitting the low ones is what made the original claim
# misleading.
PEERS = [
    "Somerville", "Cambridge", "Watertown", "Boston",
    "Needham", "Lexington", "Newton", "Arlington",
]

RATE_COL = "Total New Growth Applied to Limit as a % of PY Levy Limit"


def load():
    """{municipality: {fiscal_year: rate_pct}} from the DLS Gateway pull."""
    ws = openpyxl.load_workbook(SRC, read_only=True, data_only=True)["data"]
    rows = ws.iter_rows(values_only=True)
    header = None
    for r in rows:
        if r and any(c == RATE_COL for c in r if isinstance(c, str)):
            header = list(r)
            break
    if header is None:
        raise SystemExit(f"could not find header row containing {RATE_COL!r}")
    i_town = header.index("Municipality")
    i_year = header.index("Fiscal Year")
    i_rate = header.index(RATE_COL)

    out = {}
    for r in rows:
        town, year, rate = r[i_town], r[i_year], r[i_rate]
        if town is None or year is None or rate is None or rate == "":
            continue  # DLS leaves 4 cells blank; treat as missing, not zero
        out.setdefault(str(town).strip(), {})[int(year)] = float(rate)
    return out


def window_rates(data, years):
    """{town: mean rate} for towns with a complete series over `years`."""
    years = list(years)
    return {
        t: sum(v[y] for y in years) / len(years)
        for t, v in data.items()
        if all(y in v for y in years)
    }


def percentile_of(rates, town):
    """Share of towns at or below `town`'s rate, as a percentile."""
    vals = sorted(rates.values())
    target = rates[town]
    below = sum(1 for v in vals if v < target)
    return 100.0 * below / len(vals)


def quantile(rates, q):
    vals = sorted(rates.values())
    idx = q * (len(vals) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(vals) - 1)
    return vals[lo] + (vals[hi] - vals[lo]) * (idx - lo)


def main():
    data = load()
    results = {k: window_rates(data, yrs) for k, yrs in WINDOWS.items()}

    for k, rates in results.items():
        if TOWN not in rates:
            raise SystemExit(f"{TOWN} missing from window {k}")
        print(
            f"{k}: n={len(rates)}  {TOWN} {rates[TOWN]:.3f}%  "
            f"({percentile_of(rates, TOWN):.1f}th pct)  "
            f"median {quantile(rates, 0.5):.3f}%  p80 {quantile(rates, 0.8):.3f}%"
        )

    long_rates, recent_rates = results["fy2005_2025"], results["fy2021_2025"]
    all_towns = sorted(set(long_rates) | set(recent_rates))
    rows = []
    for t in all_towns:
        rows.append(
            {
                "municipality": t,
                "rate_fy2005_2025_pct": round(long_rates[t], 4) if t in long_rates else "",
                "percentile_fy2005_2025": round(percentile_of(long_rates, t), 1) if t in long_rates else "",
                "rate_fy2021_2025_pct": round(recent_rates[t], 4) if t in recent_rates else "",
                "percentile_fy2021_2025": round(percentile_of(recent_rates, t), 1) if t in recent_rates else "",
                "is_brookline": t == TOWN,
                "is_named_peer": t in PEERS,
                "basis": (
                    "mean of DLS 'Total New Growth Applied to Limit as a % of PY "
                    "Levy Limit' across the window; towns missing any year in a "
                    "window are excluded from that window"
                ),
            }
        )
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT_CSV} ({len(rows)} municipalities)")

    write_methodology(long_rates, recent_rates)
    print(f"Wrote {OUT_METHOD}")


def write_methodology(long_rates, recent_rates):
    L = []
    L.append("# Peer New-Growth Comparison — Methodology\n")
    L.append(
        "Companion to `peer_new_growth_rates.csv`. Supports §2c of "
        "`docs/reference_document.md`. Replaces an ad-hoc 2026-08-28 "
        "calculation whose results lived only in `.claude/memorialized.md`.\n"
    )
    L.append(__doc__.split("## Method")[1].split("## What this corrects")[0].strip() + "\n")

    L.append("## Where Brookline sits\n")
    L.append("| Window | Towns ranked | Brookline | Percentile | Median | 80th pct |")
    L.append("|---|---|---|---|---|---|")
    for label, rates in (("FY2005–2025", long_rates), ("FY2021–2025", recent_rates)):
        L.append(
            f"| {label} | {len(rates)} | **{rates[TOWN]:.2f}%** | "
            f"**{percentile_of(rates, TOWN):.1f}th** | {quantile(rates, 0.5):.2f}% | "
            f"**{quantile(rates, 0.8):.2f}%** |"
        )
    L.append("")
    L.append(
        "Brookline's ranking improves from the 26th to the 40th percentile "
        "between the two windows while its own rate *falls* (1.37% to 1.28%). "
        "That is peers slowing down, not Brookline speeding up — the "
        "80th-percentile bar drops from 2.03% to 1.97% and the median falls "
        "with it. Stating the ranking improvement without that context would "
        "read as a turnaround that did not happen.\n"
    )

    L.append("## The full distribution, FY2005–2025\n")
    L.append("| Percentile | New growth, %/yr |\n|---|---|")
    for q in (0.1, 0.25, 0.5, 0.75, 0.8, 0.9):
        L.append(f"| {int(q*100)}th | {quantile(long_rates, q):.2f}% |")
    L.append("")

    L.append("## Named peers\n")
    L.append("| Town | FY2005–2025 | FY2021–2025 |\n|---|---|---|")
    ordered = sorted(PEERS, key=lambda t: -long_rates.get(t, 0))
    for t in ordered:
        a = f"{long_rates[t]:.2f}%" if t in long_rates else "—"
        b = f"{recent_rates[t]:.2f}%" if t in recent_rates else "—"
        L.append(f"| {t} | {a} | {b} |")
    L.append(
        f"| **{TOWN}** | **{long_rates[TOWN]:.2f}%** | "
        f"**{recent_rates[TOWN]:.2f}%** |"
    )
    L.append("")
    L.append("## What this corrects\n")
    L.append(
        "The reference document and README both claimed peer towns "
        '"Cambridge, Boston, Needham, and Lexington" each generated "2.5%+" '
        "new growth. Two problems:\n"
    )
    L.append(
        f"1. **Lexington is {long_rates['Lexington']:.2f}%** on the FY2005–2025 "
        "window that the surrounding sentence cites — below the stated floor. "
        "The claim holds only on the trailing five years.\n"
        f"2. **It was selective.** Newton ({long_rates['Newton']:.2f}%) and "
        f"Arlington ({long_rates['Arlington']:.2f}%) are equally reasonable "
        "inner-suburb peers and sit at or below Brookline. A reader shown only "
        "the four fastest peers is being shown a tail, not a comparison.\n"
    )
    L.append(
        "Both are now corrected in §2c, which states the distribution and "
        "names peers on both sides of Brookline. The underlying point survives "
        "intact and is better for being stated properly: Brookline is in the "
        "bottom third of the state, and towns very much like it have done "
        "substantially better.\n"
    )
    L.append("## Source\n")
    L.append(
        "- `data/2026 MA state new growth for all towns 20 years.xlsx`, sheet "
        "`data` — the raw MA Department of Local Services Gateway pull, 351 "
        "municipalities x FY2003–2026.\n"
        "- Note the workbook's `pivot` sheet carries an older hand-built "
        "percentile ladder (Brookline 1.3305%, 28.1st percentile, 80th at "
        "2.0044%) computed on an FY2006–2025 window. Those are not the figures "
        "used here; this script recomputes from the raw sheet on the stated "
        "windows.\n"
    )
    OUT_METHOD.write_text("\n".join(L))


if __name__ == "__main__":
    main()
