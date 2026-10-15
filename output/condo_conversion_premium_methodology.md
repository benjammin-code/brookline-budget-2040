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

## Result (old buildings, value two years after vs. unconverted peers)

| Group | n | Median premium | Middle half |
|---|---|---|---|
| 2-3 family | 233 | +25% | +11% to +60% |
| apartment 4+ units | 20 | +82% | +54% to +109% |
| 2-3 family, permit spend under 5% of value | 28 | +14% | |
| apartment 4+ units, permit spend under 5% of value | 4 | +69% | |
| control: apartments staying apartments, permit spend over 25% | 18 | +6% | |

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
