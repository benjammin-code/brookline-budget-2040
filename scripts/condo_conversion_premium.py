"""
How much does converting a building from rental to condominium raise its assessed value?

Prompted 2026-09-30 by the Town Assessor's remark (via Ben's colleagues) that condo use
bumps a building's valuation by about 20% over rental use, against the reference
document's cross-sectional finding that condos assess at about twice the value per
square foot of apartments (§3b). The cross-section compares different buildings; this
test holds the building fixed.

Method:
  1. Every parcel (block_lot) whose land-use class changes from 2-family, 3-family,
     apartment 4-8 or apartment 9+ in year y0 to condominium in y0+1, FY2009-2025
     (parcel_full_history_fy09_26.csv; FY2026 codes changed and are excluded).
  2. Premium = (value in y0+2 / value in y0) / (median same ratio for parcels that
     stayed in the original class over the same years) - 1. Two years after, so work
     around the conversion has reached the roll.
  3. Old buildings only (built 15+ years before the conversion; year built from the
     FY2017-25 CAMA records). Newer "conversions" are mostly new buildings finishing
     construction, where the pre-conversion value is a partial assessment.
  4. Permitted construction spending on the parcel from y0-2 to y0+1 (building permits,
     estimated cost, recorded from FY2017), as a share of the pre-conversion value.
  5. Control: apartment buildings that stayed apartments, by permit spend, FY2019-23.

Why apartments and 2-3 families differ: Massachusetts assessors value apartment buildings
(4+ units) on rental income; 2- and 3-family houses and condominiums on comparable
sales. Only the apartment conversions change valuation method.

Run from `scripts/`:  python3 condo_conversion_premium.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

import permit_analysis as pa

ROOT = Path(__file__).parent.parent
LV = ROOT / "land-value-map" / "output"
OUT = ROOT / "output" / "condo_conversion_premium.csv"
OUT_METHOD = ROOT / "output" / "condo_conversion_premium_methodology.md"
CLS = {"SINGLE FAMILY": "SF", "101": "SF", "ONE FAMILY H": "SF", "CONDO": "CONDO", "102": "CONDO",
       "TWO FAMILY": "2F", "TWO FAM": "2F", "104": "2F", "THREE FAMILY": "3F", "105": "3F",
       "APT 4-8 UNIT": "APT48", "111": "APT48", "APTS 9+ UNIT": "APT9", "112": "APT9"}
RENTAL = ("2F", "3F", "APT48", "APT9")


def main():
    h = pd.read_csv(LV / "parcel_full_history_fy09_26.csv", dtype={"description": str, "block_lot": str})
    h["cls"] = h.description.str.strip().map(CLS).fillna("OTHER")
    V = h.pivot_table(index="block_lot", columns="fy", values="tot_value", aggfunc="first")
    C = h.pivot_table(index="block_lot", columns="fy", values="cls", aggfunc="first")
    cama = pd.read_csv(LV / "parcel_history_fy17_25.csv", dtype={"block_lot": str})
    year_built = cama[cama.year_built > 1700].groupby("block_lot").year_built.median()
    permits = pa.load_permits()
    permits = permits[permits.block_lot.notna() & permits.is_building & (permits.cost > 0)]

    def base(cls, y0):
        ok = (C[y0] == cls) & (C[y0 + 2] == cls) & V[y0].gt(0) & V[y0 + 2].gt(0)
        return float(np.median(V.loc[ok, y0 + 2] / V.loc[ok, y0]))

    rows = []
    for bl, row in C.iterrows():
        seq = row.dropna()
        for (y0, c0), (y1, c1) in zip(seq.items(), list(seq.items())[1:]):
            if not (c0 in RENTAL and c1 == "CONDO" and y1 == y0 + 1 and y0 + 2 <= 2025):
                continue
            if C.at[bl, y0 + 2] != "CONDO" or not V.at[bl, y0] > 0:
                continue
            spend = permits[(permits.block_lot == bl) & permits.fy.between(y0 - 2, y0 + 1)].cost.sum() \
                if y0 >= 2019 else np.nan
            rows.append(dict(block_lot=bl, last_rental_fy=int(y0), from_class=c0,
                             year_built=year_built.get(bl, np.nan),
                             value_before=V.at[bl, y0], value_2yr_after=V.at[bl, y0 + 2],
                             class_baseline_ratio=round(base(c0, y0), 4),
                             premium=round(V.at[bl, y0 + 2] / V.at[bl, y0] / base(c0, y0) - 1, 4),
                             permit_spend_share=round(spend / V.at[bl, y0], 4) if spend == spend else np.nan))
    d = pd.DataFrame(rows)
    d["group"] = np.where(d.from_class.isin(["APT48", "APT9"]), "apartment 4+ units", "2-3 family")
    d["old_building"] = (d.last_rental_fy - d.year_built) >= 15
    d.to_csv(OUT, index=False)

    lines = []
    old = d[d.old_building]
    for g, x in old.groupby("group"):
        q = x.premium
        lines.append(f"| {g} | {len(x)} | {q.median():+.0%} | {q.quantile(.25):+.0%} to {q.quantile(.75):+.0%} |")
    low = old[(old.permit_spend_share < 0.05)]
    for g, x in low.groupby("group"):
        lines.append(f"| {g}, permit spend under 5% of value | {len(x)} | {x.premium.median():+.0%} | |")

    # control: apartments that stayed apartments
    ctrl = []
    for y0 in range(2019, 2024):
        ok = C[y0].isin(["APT48", "APT9"]) & C[y0 + 2].isin(["APT48", "APT9"]) & V[y0].gt(0)
        b = np.median(V.loc[ok, y0 + 2] / V.loc[ok, y0])
        sp = permits[permits.fy.between(y0 - 2, y0 + 1)].groupby("block_lot").cost.sum()
        for bl in V.index[ok]:
            ctrl.append(dict(share=sp.get(bl, 0) / V.at[bl, y0], prem=V.at[bl, y0 + 2] / V.at[bl, y0] / b - 1))
    ctrl = pd.DataFrame(ctrl)
    big = ctrl[ctrl.share > 0.25]
    lines.append(f"| control: apartments staying apartments, permit spend over 25% | {len(big)} | "
                 f"{big.prem.median():+.0%} | |")
    table = "\n".join(lines)
    print(table)

    OUT_METHOD.write_text(__doc__.strip() + f"""

## Result (old buildings, value two years after vs. unconverted peers)

| Group | n | Median premium | Middle half |
|---|---|---|---|
{table}

Converting an old apartment building to condominiums raised its assessed value by a
median of about 80%, far above the ~20% the Assessor cited and close to, but below, the
reference document's cross-sectional ~2x per square foot. Heavy renovation without
conversion adds little (control row), so the jump is the change of valuation method,
not the construction. Two- and three-family houses, valued on sales either way, rose
about 14-25%, near the Assessor's figure.

## Limits

- 20 old apartment conversions in 17 years; 4 of them have both permit data and near-zero
  spend (median about +68%). Small sample.
- Permits join by street address (85% of permits match); unmatched renovation would be
  counted as zero spend.
- No new apartment building converted in the window, so the Assessor's ~20% for new,
  high-rent buildings is untested here. The premium plausibly depends on how far the
  building's rents sit below what its units would sell for, which is widest in older,
  lower-rent buildings.
""")
    print(f"wrote {OUT.name}, {OUT_METHOD.name}")


if __name__ == "__main__":
    main()
