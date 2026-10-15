"""The base case's new-homes inputs, measured from Brookline's own permits and assessment rolls
(method A, Ben 2026-10-12). Writes output/new_homes_parameters.json and a readable CSV.

  Pace      net new homes a year, building permits issued 2016-2025 (output/permit_homes_by_year.csv,
            coded by hand), without assisted living, which is its own category.
  Mix       net new homes by type over the same permits, each demolition assigned to the project that
            replaced it (output/permit_homes_mix.csv). A house replaced by a house is renovation, not a
            new home; a house replaced by a two-family adds one.
  Value     assessed value each type adds per net new home, on the new-growth basis: each project
            parcel's market-adjusted increase on every roll after its permit, increases only (state
            new growth counts a parcel's increase over its prior-year assessment and is never reduced
            by a demolition: IGR FY2021 section II.A, data/DLS new growth guidelines (IGR).pdf; DLS,
            Understanding and Analyzing New Growth Part 1), in FY2026 dollars. Projects permitted
            2015-2022, so most are fully on the FY2026 roll.
            Age-restricted homes: the two taxable buildings measured (one still rising), times the taxable share of the type's homes (the Housing Authority's senior building's 115
            belong to the Housing Authority and pay no tax).
  Forecast  the homes the forecast adds are apartments and condominiums (small multifamily, mixed use
            and condominium buildings), in their 2016-2025 proportions (Ben, 2026-10-12): age-restricted
            homes are not forecast (one nearly finished building is seeking to drop its restriction), and
            houses and conversions, mostly rebuilds, behave like renovation. The full measured mix is kept
            for reference.
  Children  0.2442 school children per forecast home (RKG's per-bedroom rates applied to recent new
            homes' bedrooms).

The forecast keeps total residential new growth at its trend rate (it has held at 0.8-1.0% of the
levy whether 41 or 180 homes a year were built; renovation fills in). The new-homes share of that
total is set so FY2026 carries the pace at the blended value: share = homes x value x tax rate /
(trend rate x FY2025 levy limit)."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
PACE_YEARS = (2016, 2025)
VALUE_PERMITS = ("2015-01-01", "2023-01-01")
STUDENTS_PER_HOME_OTHER = 0.2442
GROUPS = {"APTS": "apartments", "SENIOR_APTS": "age_restricted", "MULTI": "small_multifamily",
          "MIXED": "small_multifamily", "CONDO": "small_multifamily", "SF": "houses", "2-3F": "houses",
          "DEMO": "houses", "CONV": "conversions", "ADU": "conversions", "SENIOR_LIVING": "assisted_living"}
LABELS = {"apartments": "Apartment buildings", "age_restricted": "Age-restricted apartments",
          "small_multifamily": "Small multifamily, mixed use and condominiums",
          "conversions": "Conversions and accessory units", "houses": "Houses (single, two, three-family)",
          "assisted_living": "Assisted living"}
FORECAST_TYPES = ("apartments", "small_multifamily")
AGE_TAXABLE = {"078-08": 62, "079-20": 54}      # two age-restricted buildings
AGE_EXEMPT_HOMES = 115                           # the Housing Authority's senior building


def main():
    k = pd.read_csv(OUT / "permit_homes_coded.csv", low_memory=False)
    k = k[k.status == "coded"].copy()
    k["grp"] = k.type.map(GROUPS)
    by_year = pd.read_csv(OUT / "permit_homes_by_year.csv").set_index("year")
    yrs = by_year.loc[PACE_YEARS[0]:PACE_YEARS[1]]
    pace = float(yrs.net_excluding_assisted_living.mean())

    MIXG = {"Apartment buildings (rental, mostly 40B)": "apartments", "Age-restricted apartments": "age_restricted",
            "Condominiums and small multifamily": "small_multifamily", "Conversions, splits and accessory units": "conversions",
            "Single-family and two- or three-family": "houses", "Assisted living": "assisted_living"}
    mx = pd.read_csv(OUT / "permit_homes_mix.csv")
    mx = mx[mx.period == f"{PACE_YEARS[0]}-{PACE_YEARS[1]}"]
    m = pd.Series({MIXG[g]: float(n) for g, n in zip(mx.group, mx.net)})
    assisted = float(m.get("assisted_living", 0))
    m = m.drop("assisted_living", errors="ignore")
    mix = (m / m.sum()).to_dict()

    # value on the new-growth basis, FY2026 dollars
    f = pd.read_csv(ROOT / "land-value-map/output/parcel_full_history_fy09_26.csv")
    v = f.pivot_table(index="block_lot", columns="fy", values="tot_value", aggfunc="sum")
    step = (v / v.shift(axis=1)).median()
    to26 = step.loc[::-1].cumprod().shift(1, fill_value=1.0).loc[::-1]   # value of a year-y dollar in FY2026
    k["issued"] = pd.to_datetime(k.issued)
    proj = k[k.block_lot.notna()].groupby("block_lot").agg(first=("issued", "min"), net=("net", "sum"),
                                                            grp=("grp", lambda x: x.mode().iloc[0]))

    def gross(b, first):
        f0 = first.year + 1
        s = 0.0
        for y in range(max(f0 + 1, 2010), 2027):
            a, p = v.loc[b].get(y), v.loc[b].get(y - 1)
            if pd.notna(a) and pd.notna(p):
                s += max(a - p * step[y], 0.0) * to26[y]
        return s
    proj = proj[proj.index.isin(v.index)]
    proj["value26"] = [gross(b, r["first"]) for b, r in proj.iterrows()]
    sel = proj[(proj["first"] >= VALUE_PERMITS[0]) & (proj["first"] < VALUE_PERMITS[1]) & (proj.net > 0)]
    val = (sel.groupby("grp").value26.sum() / sel.groupby("grp").net.sum()).to_dict()
    age = sum(proj.loc[b, "value26"] for b in AGE_TAXABLE if b in proj.index) / sum(AGE_TAXABLE.values())
    age_homes = m.get("age_restricted", 0)
    val["age_restricted"] = age * (age_homes - AGE_EXEMPT_HOMES) / age_homes
    counts = sel.groupby("grp").agg(projects=("net", "size"), homes=("net", "sum")).to_dict("index")
    counts["age_restricted"] = dict(projects=len(AGE_TAXABLE), homes=sum(AGE_TAXABLE.values()))

    fmix = {g: mix[g] / sum(mix[t] for t in FORECAST_TYPES) for g in FORECAST_TYPES}
    blended = sum(fmix[g] * val[g] for g in fmix)
    children = STUDENTS_PER_HOME_OTHER
    # homes on permits issued 2010-2024 (on the roll by about FY2025), without assisted living
    fy11_25 = float(by_year.loc[2010:2024].net_excluding_assisted_living.sum())
    out = dict(pace_homes_per_year=round(pace, 1), pace_years=list(PACE_YEARS),
               assisted_living_homes_in_pace_years=assisted,
               mix={g: round(s, 4) for g, s in mix.items()},
               forecast_mix={g: round(x, 4) for g, x in fmix.items()},
               value_per_net_home_fy2026={g: round(x, -3) for g, x in val.items()},
               value_sample=counts, blended_value_per_net_home_fy2026=round(blended, -3),
               students_per_home_blended=round(children, 4), students_per_home_other=STUDENTS_PER_HOME_OTHER,
               homes_permitted_2010_2024=fy11_25,
               homes_by_period={f"{a}-{b}": round(float(by_year.loc[a:b].net_excluding_assisted_living.mean()), 1)
                                for a, b in ((2008, 2015), (2016, 2025), (2008, 2025))})
    (OUT / "new_homes_parameters.json").write_text(json.dumps(out, indent=2))
    rows = [dict(type=LABELS[g], share_of_new_homes=round(mix[g], 3), value_per_net_home_fy2026=round(val[g], -3),
                 projects_measured=counts.get(g, {}).get("projects"), homes_measured=counts.get(g, {}).get("homes"))
            for g in sorted(mix, key=lambda g: -mix[g])]
    pd.DataFrame(rows).to_csv(OUT / "new_homes_parameters.csv", index=False)
    print(f"pace {pace:.1f}/yr; blended ${blended:,.0f}/home; children {children:.4f}/home; "
          f"homes permitted 2010-24 {fy11_25:.0f}")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
