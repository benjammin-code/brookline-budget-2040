"""
Existing-vs-new-property tax split, FY2005-2025 - a historical, real-data
extension of `data/FY27-FY29 Brookline property tax & impact of new
growth.xlsx`'s "Property tax: existing vs new properties" table (that
sheet's rows 29-46, forward-looking FY26-31 with assumed new growth).
Built 2026-09-01 per Ben's request, following an exchange correcting an
earlier claim about how an unchanged parcel's tax should grow relative to
the town levy - see the conversation this session for the derivation.

Answers, with 21 years of real data instead of a 5-year projection:
"how much would an existing (as of FY2005) property's tax bill have grown
by, each year, if none of it came from new construction?" - the actual
mechanism is that new growth, overrides, and debt exclusions all land
differently on an "existing" cohort vs. a "new" (built since the base
year) cohort, because overrides/debt-exclusions are fixed dollar amounts
spread across ALL taxpayers by value share, while new growth's own
dollar contribution is entirely captured by the new construction itself.

Allocation method (reverse-engineered from the Excel file's real numbers,
confirmed by checking FY2027's new-property override share $78,424 of
$9,852,330 total against that cohort's $2.5M of $314.07M share of the
total levy limit - matches to the decimal): override, debt exclusion,
and excess capacity are each split between the "existing" and "new"
cohorts in proportion to each cohort's share of that year's levy limit
BEFORE the item being split is added (i.e., value share). Only the levy
limit itself (2.5% + new growth + override + excess capacity) compounds
forward into next year's base - debt exclusion does NOT compound (it's
recomputed fresh each year from the actual bond schedule, dollar-matched,
outside the 2.5% cap), matching real Prop 2.5 mechanics.

Base year: FY2005 (this project's data floor). Everything that existed as
of FY2005 is "existing" for the entire window; every year's new_growth
dollar figure (real, from `brookline_historical_financials_fy05_25.csv`)
permanently joins the "new" cohort from that year forward, which then
itself compounds at 2.5%/yr plus further new growth plus its own pro-rata
share of subsequent overrides/debt exclusions - exactly mirroring how the
Excel file tracks its own FY27-29 "new property" cohort.

Bug found and fixed while building this: `excess_capacity` (the gap
between the town's ALLOWED levy limit and what it actually chose to
raise that year) does NOT reduce the levy limit that carries forward -
MA Prop 2.5 preserves unused capacity rather than losing it. Confirmed
directly: FY2016's allowed levy limit (prior + 2.5% + new growth +
override, deliberately excluding that year's -$1,465,000 excess capacity)
equals FY2017's reported `prior_levy_limit` to the dollar; subtracting
excess capacity first (the original, wrong version of this script)
produced a growing reconciliation gap that hit -$12.6M by FY2025.
Fixed by tracking two figures per cohort per year: an "allowed levy
limit" that compounds forward untouched by excess capacity, and an
"actual tax" (allowed levy limit + that year's excess-capacity share +
debt-exclusion share) that's this year's real headline number but does
NOT itself carry forward.
"""
import csv

BASE_YEAR = 2005
IN_PATH = 'output/brookline_historical_financials_fy05_25.csv'
OUT_PATH = 'output/existing_vs_new_property_tax_fy05_25.csv'


def main():
    with open(IN_PATH) as f:
        rows = {int(r['fiscal_year']): r for r in csv.DictReader(f)}

    years = sorted(y for y in rows if y >= BASE_YEAR)

    def num(y, key):
        return float(rows[y][key])

    out_rows = []
    existing_allowed = None  # "allowed" levy limit - compounds forward, untouched by excess capacity
    new_allowed = None
    new_cumulative_growth_dollars = 0.0

    for y in years:
        levy_limit_allowed = num(y, 'prior_levy_limit') + num(y, 'increase_2_5pct') + \
            num(y, 'new_growth') + num(y, 'override')
        town_total_tax = levy_limit_allowed + num(y, 'excess_capacity') + num(y, 'debt_exclusions')

        if y == BASE_YEAR:
            existing_allowed = levy_limit_allowed
            new_allowed = 0.0
            existing_excess_cap = num(y, 'excess_capacity')
            new_excess_cap = 0.0
            existing_debt_excl = num(y, 'debt_exclusions')
            new_debt_excl = 0.0
        else:
            existing_pre = existing_allowed * 1.025
            new_pre = new_allowed * 1.025 + num(y, 'new_growth')
            new_cumulative_growth_dollars += num(y, 'new_growth')
            total_pre = existing_pre + new_pre
            existing_share = existing_pre / total_pre if total_pre else 0.0
            new_share = 1 - existing_share

            existing_allowed = existing_pre + num(y, 'override') * existing_share
            new_allowed = new_pre + num(y, 'override') * new_share
            existing_excess_cap = num(y, 'excess_capacity') * existing_share
            new_excess_cap = num(y, 'excess_capacity') * new_share
            existing_debt_excl = num(y, 'debt_exclusions') * existing_share
            new_debt_excl = num(y, 'debt_exclusions') * new_share

        existing_total_tax = existing_allowed + existing_excess_cap + existing_debt_excl
        new_total_tax = new_allowed + new_excess_cap + new_debt_excl
        reconciliation_diff = (existing_total_tax + new_total_tax) - town_total_tax

        out_rows.append({
            'fiscal_year': y,
            'existing_allowed_levy_limit': round(existing_allowed),
            'existing_excess_capacity_share': round(existing_excess_cap),
            'existing_debt_exclusion_share': round(existing_debt_excl),
            'existing_total_tax': round(existing_total_tax),
            'new_allowed_levy_limit': round(new_allowed),
            'new_excess_capacity_share': round(new_excess_cap),
            'new_debt_exclusion_share': round(new_debt_excl),
            'new_total_tax': round(new_total_tax),
            'new_cumulative_growth_dollars': round(new_cumulative_growth_dollars),
            'town_total_tax_reported': round(town_total_tax),
            'reconciliation_diff': round(reconciliation_diff),
        })

    for i, r in enumerate(out_rows):
        prior = out_rows[i - 1] if i > 0 else None
        r['existing_pct_growth_yoy'] = None if prior is None else round(
            r['existing_total_tax'] / prior['existing_total_tax'] - 1, 5)
        r['existing_pct_growth_from_base'] = round(
            r['existing_total_tax'] / out_rows[0]['existing_total_tax'] - 1, 5)
        r['town_pct_growth_yoy'] = None if prior is None else round(
            r['town_total_tax_reported'] / prior['town_total_tax_reported'] - 1, 5)
        r['town_pct_growth_from_base'] = round(
            r['town_total_tax_reported'] / out_rows[0]['town_total_tax_reported'] - 1, 5)

    fieldnames = list(out_rows[0].keys())
    with open(OUT_PATH, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)
    print(f'wrote {OUT_PATH}: {len(out_rows)} rows, base year FY{BASE_YEAR}')
    print()
    print(f'{"FY":>6} {"Existing tax":>14} {"Exist YoY":>10} {"New tax":>12} {"Town tax":>14} {"Town YoY":>10} {"Recon diff":>10}')
    for r in out_rows:
        yoy_e = f'{r["existing_pct_growth_yoy"]:.2%}' if r['existing_pct_growth_yoy'] is not None else '   -'
        yoy_t = f'{r["town_pct_growth_yoy"]:.2%}' if r['town_pct_growth_yoy'] is not None else '   -'
        print(f'{r["fiscal_year"]:>6} {r["existing_total_tax"]:>14,} {yoy_e:>10} '
              f'{r["new_total_tax"]:>12,} {r["town_total_tax_reported"]:>14,} {yoy_t:>10} '
              f'{r["reconciliation_diff"]:>10,}')

    n = len(out_rows) - 1
    existing_cagr = (out_rows[-1]['existing_total_tax'] / out_rows[0]['existing_total_tax']) ** (1 / n) - 1
    town_cagr = (out_rows[-1]['town_total_tax_reported'] / out_rows[0]['town_total_tax_reported']) ** (1 / n) - 1
    print()
    print(f'FY{BASE_YEAR}->FY{years[-1]} ({n} years):')
    print(f'  Existing-property tax CAGR: {existing_cagr:.3%}')
    print(f'  Town total tax CAGR:        {town_cagr:.3%}')
    print(f'  New cumulative growth $ by FY{years[-1]}: ${out_rows[-1]["new_cumulative_growth_dollars"]:,.0f} '
          f'({out_rows[-1]["new_total_tax"]:,.0f} in current-year tax)')


if __name__ == '__main__':
    main()
