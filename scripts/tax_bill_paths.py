"""
How a typical Brookline tax bill changes to FY2040 under four paths (the "your tax bill" page).

A typical home here is one that already exists in FY2026 and whose assessed value moves with
the town average. Its bill is its share of the town's total property tax, so it changes only
when that total changes or when new property arrives to share it:

    operating levy  L(y)  = the levy limit the revenue model forecasts (operating, no debt
                            exclusions); it grows 2.5% a year, plus new growth, plus overrides
    new property          = whatever L(y) gains beyond 2.5% and overrides: new growth, which is
                            taxed on its own value and so adds tax without raising anyone's bill
    existing share  s(y)  = s(y-1) * (1.025 L(y-1) + override step(y)) / L(y)
    typical bill    B(y)  = B(2026) * s(y) * (L(y) + DE(y)) / (L(2026) + DE(2026))

DE(y) is debt exclusion tax, a fixed dollar amount for each project. More new growth lowers
s(y), so existing homes carry a smaller share of the same debt exclusion dollars: faster growth
lowers a typical bill slightly even though it leaves the operating share unchanged.

Paths:
  base       the base case: the May 2026 override phases in, no further votes
  override   pay runs a point high (the largest single risk), and voters approve an override in
             the year the room runs out, sized so revenue covers spending through FY2040
  baker      the base case plus a debt exclusion for a Baker School project, illustrative:
             the same net cost as Pierce ($210M less $37M state reimbursement), borrowed for
             FY2031 at 4% over 30 years, level debt service
  growth     new growth at the peer rate (the fastest-growing fifth of Massachusetts towns), mix
             of homes and commercial space

Typical bills in FY2026 are the Town's medians (FY2027 Financial Plan, "Median Per Parcel
Values and Tax Bills"), which include the residential exemption for owner-occupied homes. The
rental apartment is the FY2026 roll's average per unit in apartment buildings of four or more
units (use codes 111 and 112: total FY2026 tax / residential units), which get no residential
exemption. Every type of home takes the same bill index, so the paths assume values rise at the
same rate for every type of home; from FY2018 to FY2026 they did not (single-family 59%,
condominiums 27%).

Run from scripts/:  python3 tax_bill_paths.py   -> output/tax_bill_paths.csv
"""
import csv
from pathlib import Path

import pandas as pd

import expense_driver_forecast as edf
from new_growth_scenario_forecast import MAY_2026_OVERRIDE_SCHEDULE

OUT = Path(__file__).parent.parent / "output" / "tax_bill_paths.csv"
YEARS = list(range(2026, 2041))
TAX_RATE_FY26 = 0.01024
EXEMPTION_FY26 = 354_974
MEDIANS_FY26 = {  # (median assessed value, median owner-occupied bill)
    "single_family": (2_396_400, 20_904),
    "two_family": (2_204_300, 18_937),
    "condo": (839_600, 4_963),
}
ROLL_FY26 = Path(__file__).parent.parent / "data" / \
    "FY2026 Property Assessments_data update 2001.02.26_202603130814527665.xlsx"
APARTMENT_CODES = (111, 112)  # apartment buildings, 4-8 units and more than 8
BAKER_NET_COST = 210e6 - 37e6
BAKER_RATE, BAKER_TERM, BAKER_FIRST_FY = 0.04, 30, 2031


def apartment_unit_fy26():
    """Average FY2026 value and tax per unit in apartment buildings of four or more units."""
    r = pd.read_excel(ROLL_FY26)
    a = r[pd.to_numeric(r["Composite Land Use Code"], errors="coerce").isin(APARTMENT_CODES)]
    units = a["Residential Units"].sum()
    return a["FY2026VALUE"].sum() / units, a["FY26 TAXES "].sum() / units, int(units), len(a)


def levy_paths(scenario):
    g = edf.chca_growth_frame("approved")
    g = g[g.scenario == scenario].set_index("fiscal_year")
    return ({y: float(g.loc[y, "property_tax_operating"]) for y in YEARS},
            {y: float(g.loc[y, "debt_exclusion_revenue"]) for y in YEARS})


def bill_index(L, DE, overrides, extra_de=None):
    extra_de = extra_de or {}
    s, idx = {2026: 1.0}, {2026: 1.0}
    base = L[2026] + DE[2026]
    for y in YEARS[1:]:
        s[y] = s[y - 1] * (1.025 * L[y - 1] + overrides.get(y, 0)) / L[y]
        idx[y] = s[y] * (L[y] + DE[y] + extra_de.get(y, 0)) / base
    return idx


def override_needed():
    """Pay one point higher: the override, voted for the year room first runs out and growing
    2.5% a year after, that keeps revenue at or above spending through FY2040."""
    data = edf.load()
    r = edf.run(dict(edf.BASE, pay=0.04), data, None)
    room = {y: float(r.loc[y, "surplus_deficit"]) for y in YEARS}
    first = next(y for y in YEARS if y >= 2028 and room[y] < 0)
    amount = max(-room[y] / 1.025 ** (y - first) for y in YEARS if y >= first)
    return first, amount


def main():
    L, DE = levy_paths("trend_continues")
    Lg, DEg = levy_paths("peer_target_balanced_mix")
    ov = dict(MAY_2026_OVERRIDE_SCHEDULE)
    first, amount = override_needed()
    pay = BAKER_NET_COST * BAKER_RATE / (1 - (1 + BAKER_RATE) ** -BAKER_TERM)
    baker = {y: pay for y in YEARS if y >= BAKER_FIRST_FY}
    # the added override raises the levy too: it is in L for the override path
    L_ov = {y: L[y] + (amount * 1.025 ** (y - first) if y >= first else 0) for y in YEARS}
    apt_value, apt_tax, apt_units, apt_buildings = apartment_unit_fy26()
    MEDIANS_FY26["apartment"] = (round(apt_value), round(apt_tax))
    paths = {
        "base": bill_index(L, DE, ov),
        # added to any May 2026 step that year, not in place of it (2026-10-14: with the first short
        # year FY2028, the dict merge had replaced the May override's FY2028 step)
        "override": bill_index(L_ov, DE, {**ov, first: ov.get(first, 0) + amount}),
        "baker": bill_index(L, DE, ov, baker),
        "growth": bill_index(Lg, DEg, ov),
    }
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["fiscal_year", "path", "bill_index", *[f"{k}_bill" for k in MEDIANS_FY26]])
        for name, idx in paths.items():
            for y in YEARS:
                w.writerow([y, name, round(idx[y], 5), *[round(b * idx[y]) for _, b in MEDIANS_FY26.values()]])
    with open(OUT.with_name("tax_bill_paths_notes.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "value"])
        w.writerow(["override_first_fy", first])
        w.writerow(["override_amount", round(amount)])
        w.writerow(["baker_annual_debt_service", round(pay)])
        w.writerow(["baker_first_fy", BAKER_FIRST_FY])
        w.writerow(["tax_rate_fy26", TAX_RATE_FY26])
        w.writerow(["exemption_fy26", EXEMPTION_FY26])
        w.writerow(["apartment_value_fy26", round(apt_value)])
        w.writerow(["apartment_tax_fy26", round(apt_tax)])
        w.writerow(["apartment_units", apt_units])
        w.writerow(["apartment_buildings", apt_buildings])
    for name, idx in paths.items():
        print(f"{name:9s} FY2030 {idx[2030]:.3f}  FY2035 {idx[2035]:.3f}  FY2040 {idx[2040]:.3f}  "
              f"({(idx[2040] ** (1 / 14) - 1) * 100:.2f}%/yr)")
    print(f"override: ${amount / 1e6:.1f}M from FY{first}; Baker debt service ${pay / 1e6:.1f}M/yr from FY{BAKER_FIRST_FY}")


if __name__ == "__main__":
    main()
