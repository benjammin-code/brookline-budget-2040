# Children per home from census blocks, 2010 and 2020

Built by `scripts/block_children_per_home.py` (2026-10-28). Sources and download links in
`data/SOURCES.md`, "Census blocks, 2010 and 2020".

## Method

- Every Census block in Brookline (680 in 2010, 553 in 2020) gives children aged 5 to 17 and
  housing units. Every assessor record for a house, condominium or two- or three-family house
  (FY2010 and FY2020 files, the closest to each census) is placed on a block through its parcel.
- Apartments and other homes (apartment buildings, mixed-use buildings, Housing Authority,
  rooming houses) are the block's census housing units less the assessor's homes there.
- Children per home of each kind come from fitting each block's children to its homes of each
  kind (non-negative least squares, no constant). Ranges are the 10th to 90th percentiles of
  500 refits on resampled block groups.

## Results: children 5-17 per home (all schools, public and private)

| Kind of home | 2010 | 2020 | Homes in 2020 |
|---|---|---|---|
| Houses (single-family) | 0.66 | 0.72 | 4,732 |
| Two- and three-family units | 0.47 | 0.60 | 2,868 |
| Condominiums | 0.11 | 0.18 | 9,712 |
| Apartments and other | 0.14 | 0.18 | 10,753 |
| All homes (census) | 0.272 | 0.328 | 27,961 |

Condominiums by bedrooms, 2020: 0-1 bedroom 0.06 (0.00-0.16), 2 bedrooms 0.24 (0.17-0.30),
3+ bedrooms 0.34 (0.21-0.47). 2010: 0.01, 0.17, 0.21.

Houses by bedrooms cannot be separated: houses of every size sit together in the same blocks,
so the fit swings between them (at block-group level 1-3 bedroom houses come out above 1.0 and
4-bedroom houses at zero). Use the combined house figure.

## 2010 to 2020

- Children 5-17 rose from 7,199 to 9,159 (+27%) while homes rose from 26,448 to 27,961 (+6%).
- Applying 2010's per-home rates to 2020's homes gives 7,004 children, no more than 2010's own
  fit (7,011). The change in which homes Brookline has explains none of the rise; more children
  in each kind of home explains all of it.
- In the 11 block groups whose homes changed by 3% or less, children per home went from 0.256
  to 0.296.
- Across the 44 block groups, the change in children fits 0.30 per added home (range 0.14-0.52)
  plus an 18% rise on the children already there (14%-25%).

## From children to public school students

Brookline's K-12 enrollment was 6,212 in October 2009 and 7,506 in October 2019 (DESE). It
includes about 500 METCO and materials-fee students (the 2023 Cropper study's figure; not
known for 2009 or 2019). Public school students who live in Brookline are about 79% of the
census's children 5-17 in 2010 and 76% in 2020, or 86% and 82% if no students are removed.
At 76%-82%, 2020's figures are: apartments 0.14-0.15 public students a home, two-bedroom
condominiums 0.18-0.20, three-bedroom condominiums 0.26-0.28, an added home 0.23-0.25.

## Bedrooms and the scatter

- Assessor homes with 3+ bedrooms, counting apartments as smaller, are 32% of homes in 2020.
  The American Community Survey (2015-19) puts all 3+ bedroom homes at 42%. Only part of the
  gap is large apartments (about 16% of rented apartments in the microdata, Brookline, Dedham
  and Milton, 2020-24); most is residents reporting more bedrooms than the assessor records
  (scripts/bg_apartment_bedrooms.py). Corrected 2026-10-28: an earlier version said roughly a
  quarter of apartments had 3+ bedrooms.
- Across block groups, children per home tracks the share of 3+ bedroom homes closely
  (correlation 0.89 to 0.90) and the share of owner-occupied homes nearly as closely (0.77 to
  0.83). The two move together, so block groups cannot say which one matters.

## Cautions

- The 2020 block counts carry the Census Bureau's privacy noise. It averages out over hundreds of
  blocks but makes single blocks unreliable. 2010 used swapping, which is milder.
- April 2020: college students were counted at their college housing (dormitories are not housing
  units) and some families may have left town early in the pandemic.
- Existing homes are not new homes. Older homes turn over to families over decades; the
  per-added-home figure is the closest to a new-home rate but includes conversions and
  renovations as well as new buildings, and its range is wide.
- About 750 condominium units each year are placed by nearest house number on the street.
