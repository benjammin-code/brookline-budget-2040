# Data Sources

A live catalog of every external data source used in this project, kept current as
sources are added rather than reconstructed at the end — this is the bibliography
for whatever we eventually publish. If you add or pull a new file into `data/`,
add an entry here in the same pass.

Every entry needs the public URL the file was downloaded from, so published work can link
its primary sources. For a file someone else supplied, ask where it came from; if it has no
public link, say so in the entry (and find a public copy before citing it).

## Property assessment & parcel data

Full sourcing detail (MassGIS, Town GIS FeatureServer, Assessor CAMA extracts,
parcel-ID reconciliation) is documented in `../land-value-map/METHODOLOGY.md` §1 —
not duplicated here. Files:

- `2026-01 Brookline assessment data analysis.xlsx` — Ben's own parcel-ID
  crosswalk between CAMA and GIS schemes ("all years data" tab).
- `2026-04 Brookline assessments consolidated.xlsx` — consolidated multi-year
  Assessor extract.
- `FY2020%20PROPERTY%20ASSESSMENTS_....xlsx` — Town Assessor FY2020 CAMA extract
  (added 2026-08-27).
- `FY2025 2ROPERTY ASSESSMENTS.xlsx` — Town Assessor FY2025 CAMA extract
  (added 2026-08-30, Ben; sic on the filename — Town's own typo). Full
  175-column schema, same as the FY17-24 extracts above — extends
  `land-value-map`'s classification pipeline through FY2025.
- `FY2026 Property Assessments_data update 2001.02.26_202603130814527665.xlsx`
  — Town Assessor FY2026 extract (added 2026-08-30, Ben). Narrower
  33-column schema — has Year Built and Total Finished Area (an
  improvement over the existing FY26 "lighter extract" tab) but still
  missing DESCRIPTION/GRADE/CONDITION and the residential/commercial value
  split. **Not yet used** — left out of the classification pipeline for
  now (Ben's call, 2026-08-30); see `land-value-map/METHODOLOGY.md` §3c.
- `gis/brookline_parcels_2026-07-10.geojson` — Brookline Town GIS Parcels
  FeatureServer (`services1.arcgis.com/Oknk0tvfHOElpgGU/.../Parcels/FeatureServer/0`),
  pulled 2026-07-10.
  Carries a real `LAND_VALUE`/`BLDG_VALUE` split per parcel — used by
  `land-value-map/scripts/land_vs_building_value.py` (added 2026-09-07) to
  establish that **building value is 60% of Brookline's taxable base
  ($20.0B of $33.2B)**, which is the correct denominator for §3d's
  reinvestment comparison. Caveat carried in that script: this file's
  `TOT_VALUE` undercounts condominiums ($0.68B against $10.36B in the CAMA
  roll), because a condo master parcel does not carry its units' summed
  value — the same gap documented for §3b's per-square-foot work. Condo
  land/building is therefore apportioned from the CAMA total at the GIS
  condo records' own 71.7% building share, which is the one assumption in
  that file.

## Town financial history (levy, revenue, expenditure)

- **`Brookline property tax revenue over 20 years.xlsx`** — Ben-built model,
  actual (not budget) levy-limit history FY2005–2026 plus the Town's own
  FY27–31 forecast. Its `sources` tab cites the specific Town Financial
  Plan / Long-Range Financial Plan document backing each fiscal year, all
  from brooklinema.gov's DocumentCenter archive:
  | Years covered | Document | URL |
  |---|---|---|
  | FY2005–06 | FY2006–FY2010 Long-Range Financial Plan | `DocumentCenter/View/5723` |
  | FY2007 | FY2007–FY2012 Long-Range Financial Plan | `DocumentCenter/View/5556` |
  | FY2007–08 | FY10 plan, Section III Revenue | `DocumentCenter/View/5747` |
  | FY2009–10 | FY12 plan, Section III Revenue | `DocumentCenter/View/5482` |
  | FY2011–12 | FY14 plan, Section III Revenue | `DocumentCenter/View/5426` |
  | FY2013–14 | FY16 plan, Section III Revenue | `DocumentCenter/View/7065` |
  | FY2015–16 | FY18 plan, Section III Revenue | `DocumentCenter/View/11165` |
  | FY2017–18 | FY20 plan, Section III Revenue | `DocumentCenter/View/18632` |
  | FY2019–21 | FY23 Budget (final) | `DocumentCenter/View/29074` |
  | FY2022–23 | FY2025 Financial Plan | `DocumentCenter/View/48355` |
  | FY2024–25 | FY2027 Financial Plan | `DocumentCenter/View/61643` |
  | FY2026–31 (forecast) | FY27–31 Long-Range Financial Plan (presented to Advisory Committee 1/13/26) | `DocumentCenter/View/60730` |

  Full document index: [Budget Central](https://www.brooklinema.gov/851/Budget-Central)
  (Financial Plans FY01–27, Long-Range Financial Plans FY01–31, Audited
  Financial Statements FY01–24, CIP, bond/rating docs, special reports).

- **`FY27-FY29 Brookline property tax & impact of new growth.xlsx`** —
  Ben-built model: confirmed override amounts (FY27 $9,852,330 / FY28
  $5,602,871 / FY29 $7,799,238) and an existing-vs-new-property tax burden
  decomposition. Sources: FY27–31 Long-Range Financial Plan p.8
  (`DocumentCenter/View/60730`); [FY 2027-2029 Override
  Guide](https://www.brooklinema.gov/3590/FY-2027-2029-Override-Guide) for the
  override amounts. Includes a [video walkthrough](https://youtu.be/80Tal2ew2iM).
  **The Override Guide page itself (read in full 2026-08-28, not just cited
  secondhand) confirms**: this is the final, official ballot structure — a
  single combined Town+Schools override question (not two separate
  questions), permanent (not phased-in like Brookline's historical norm,
  per the page's own text), 3-year total $23,254,439 split $5,310,000
  Town / $17,944,439 Schools. The Town's $5.31M ask is identical to the
  Feb 2026 Financial Plan's preliminary proposal; the Schools' ask was
  refined down from a preliminary $19,842,217 (Feb 12 School Committee
  estimate) to the final $17,944,439 — a real ~$1.9M (9.6%) reduction.
  The exact year-by-year Town-vs-Schools split isn't stated on this page
  (only 3-year totals per recipient and per-year totals combined) — not
  yet confirmed from any source.

- **`data/brookline_overrides_debt_exclusions_history.csv`** — hand-
  transcribed 2026-08-28 from
  [affordablebrookline.com/past-overrides](https://www.affordablebrookline.com/past-overrides):
  full history of both operating overrides (1995, 2009, 2016, 2019, 2024)
  and debt exclusions (2000 x2, 2016, 2019, 2021, 2022, 2024, 2025), with
  vote dates, yes/no counts, purpose, and department. **Cross-validated**:
  4 of the 5 operating-override dollar amounts (all except 1995, which
  predates our data) match our own `override` column in
  `output/brookline_historical_financials_fy05_25.csv` exactly (FY2009
  $6,200,000; FY2016 $7,665,000; FY2019 $6,575,425; FY2024 $11,983,367).
  **Caveat**: the page gives no dollar amounts for debt exclusions
  (purpose/department/vote only) — for those, our own `debt_exclusions`
  column (the Schedule A/levy-history model) is the only $ source, and it's
  a *cumulative* annual levy add-on across all currently-active exclusions,
  not a per-project authorization amount, so individual project costs
  can't be cleanly isolated from it. Debt exclusions have been frequent
  recently — a new one roughly every 1.5-2 years since 2015, almost always
  school-building-driven (Devotion, HS, Driscoll, Pierce) plus one general-
  government exception (Newbury College land, 2022) — a pattern flagged
  in the Phase 1 baseline forecast's methodology doc as a real limitation
  of assuming zero *new* debt exclusions past FY2031.

## MA DLS (Division of Local Services) statewide data

- **`2026 MA state new growth for all towns 20 years.xlsx`** — all 351 MA
  municipalities, FY2003–2026, new-growth value and % applied to the levy
  limit. Pulled via DLS Gateway
  (`dls-gw.dor.state.ma.us/reports/rdPage.aspx?rdReport=NewGrowth.NewGrowth_dash_v2_test`).
- **`revenue & expenditures all MA/GenFundRevenues{YYYY}.xlsx`** and
  **`GenFundExpenditures{YYYY}.xlsx`** — Schedule A general-fund revenue/
  expenditure by function, all 351 municipalities, one file per (fiscal year
  × Revenues/Expenditures). Pulled via DLS Gateway
  (`dlsgateway.dor.state.ma.us/reports/rdPage.aspx?rdReport=ScheduleA.GenFund_MAIN`).
  Note: that report's fiscal-year selector only allows one year per export
  despite its checkbox styling — confirmed by testing, no bulk multi-year
  export exists. General Fund scope (excludes Enterprise funds). **Complete
  as of 2026-08-28: FY2005–2025, all 42 files (21 years × Revenues/
  Expenditures), validated — no gaps, consistent file sizes, Brookline
  present and trending sensibly in every year.**
  Background: [Revenue and Expenditure Data](https://www.mass.gov/service-details/revenue-and-expenditure-data),
  [DLS Databank Reports](https://www.mass.gov/collections/DLS-databank-reports).

## MA DLS personnel & benefits data

- **`revenue & expenditures all MA/{YYYY} FTEs and salaries.xls`** — Schedule A
  Personnel Expenditures, all 351 municipalities, Total Employees and Total
  Salaries & Wages, one file per fiscal year, FY2005–2025 (21 files,
  complete). Pulled via DLS Gateway
  (`dls-gw.dor.state.ma.us/reports/rdPage.aspx?rdReport=ScheduleA.PesonnelExpenditures.PersonnelExpenditures`
  — note the "Pesonnel" typo is in DLS's own URL). Old `.xls` format, needs
  `xlrd` (not `openpyxl`) to read. Validated: Brookline FY2025 = 3,593
  employees, $171,782,997 total salaries & wages.
- **`revenue & expenditures all MA/health_exp 2005-2025.xlsx`** — Schedule A
  Health Insurance Expenditures, all municipalities, wide format (one column
  per fiscal year FY2005–2026, 2026 not yet reported). Pulled via DLS
  Gateway
  (`dls-gw.dor.state.ma.us/reports/rdPage.aspx?rdReport=ScheduleA.HealthInsurance.HealthInsExpenditures`).
  Validated: Brookline health insurance spend grew $17.4M (FY2005) →
  $43.7M (FY2025), a real driver worth isolating in the Phase 3/4
  fixed-vs-variable expense model.

- **`revenue & expenditures all MA/RevBySource 2005-2025.xlsx`** — DOR
  Recap-Sheet-based Revenue by Source: Tax Levy, State Aid, Local Receipts,
  All Other, each with and without Enterprise & CPA funds, all
  municipalities, FY2005–2025 (complete). Pulled via DLS Gateway
  (`dls-gw.dor.state.ma.us/reports/rdPage.aspx?rdReport=RevenueBySource.RBS.RevbySourceMAIN`).
  Validated: Brookline's "Tax Levy" column matches the levy-history file's
  `total_levy` almost to the dollar every year — strong cross-validation.
  Its "Local Receipts" figure is a single lump category (not split into
  excise/hotel/meals/PILOT) and is the Recap Sheet's **estimated** Local
  Receipts (confirmed — see the Local Receipts Act-vs-Est entry below),
  not the actual. Don't use this column as a real trend line on its own.
- **`revenue & expenditures all MA/LocalReciptesActVsEst {YYYY}.xls`** —
  category-level Local Receipts, Estimate vs. Actual, 34 distinct receipt
  types (Motor Vehicle Excise, Meals, Room, Cannabis, Penalties & Interest,
  PILOT, Building Permits, Investment Income, etc.), FY2017–2025 (complete
  — DLS Gateway only supports this report back to 2017). Pulled via DLS
  Gateway
  (`dls-gw.dor.state.ma.us/reports/rdPage.aspx?rdReport=TaxRateRecap.PAGE3.LocalReceiptsAct_vs_Est`).
  **Confirms `RevBySource`'s "Local Receipts" column is the Recap Sheet's
  conservative estimate, not the actual** — the sum of this file's
  Estimate column matches `RevBySource`'s Local Receipts exactly every
  year checked. Brookline's actual Local Receipts have run 18–48% above
  the estimate every year FY2017–2025, and the gap has been widening, not
  flat. Folded into `consolidate_financials.py`'s output as
  `local_receipts_est_total` / `local_receipts_act_total` (FY2017-2025
  only, blank for earlier years) plus a separate category-level file,
  `output/brookline_local_receipts_detail_fy17_25.csv`.

## Town's own budget/forecast documents (revenue & expense category detail)

- **`FY2027-Financial-Plan.pdf`** — the full annual Financial Plan (466pp),
  sourced from [Budget Central](https://www.brooklinema.gov/851/Budget-Central)
  (`DocumentCenter/View/61643`). References an OpenGov interactive version
  at stories.opengov.com/brooklinema — not yet explored, may be easier to
  parse than the PDF for future years. Key exhibits found (see
  `.claude/memorialized.md`, 2026-08-28 entry, for full detail and page
  numbers): a "Detailed Revenue Summary" table (p.81) with FY23-27
  actual/budget for every revenue sub-category (Property Taxes, Local
  Receipts split into MVE/Local Option Taxes/Licenses/Fines/PILOTs/Refuse
  Fee/etc., State Aid split into General Gov't Aid/School Aid/etc., Free
  Cash split by use); and a "Non-Departmental Benefits" breakdown (p.79)
  that fully decomposes the Schedule A "Fixed Costs" black box into
  Pensions, Group Health, Retiree Group Health (OPEB), Life Insurance,
  Workers Comp, Medicare Tax. Also resolves the earlier CAFR-actual-vs-levy
  property tax question: this document's own footnote states its "Property
  Tax Actual" figures ARE the total levy, not GAAP-recognized collections —
  confirming the CAFR's higher figure is a different (modified-accrual)
  accounting concept, not extra collected dollars.
- **`FY2025-Financial-Plan.pdf`** and **`FY2026-Financial-Plan.pdf`** —
  prior-year editions of the same annual Financial Plan, added 2026-08-30
  (Ben, from [Budget Central](https://www.brooklinema.gov/851/Budget-Central),
  `DocumentCenter/View/48355` and `/54192`). Initial pass (2026-08-30)
  checked for anything not already captured via `FY2027-Financial-
  Plan.pdf`: the FY2026 edition's own "Median Per Parcel Values and Tax
  Bills" table extends the Residential/Commercial Tax Rate history two
  years further back — otherwise found consistent with, not additive to,
  FY2027's edition, and concluded "no unaudited actuals found beyond
  what's already sourced from the audited statements."
  **That conclusion was revised 2026-09-02**, once actually read for the
  "Personnel Benefits Detailed" table each edition carries (same page/
  format as FY2027's own, p.330 and p.296 respectively) — each edition's
  own "ACTUAL" column is a **real, fiscal-year-basis actual** for the
  prior year, not previously extracted: FY2025's edition gives FY2023
  actuals (Pensions $30,553,078, Group Health $33,971,831, OPEB
  $4,431,980, plus Group Life/Medical Disabilities/Medicare/Workers Comp/
  Public Safety IOD/Unemployment/Non-Contributory Retirement); FY2026's
  gives FY2024 actuals (Pensions $33,103,579, Group Health $34,756,062,
  OPEB $4,681,980, same sub-categories). Combined with FY2027's own FY2025
  actuals, this gives a real 3-year actual-basis window for every benefits
  sub-category — used directly in `scripts/benefits_category_forecast.py`
  (see `output/benefits_category_forecast_fy26_40_methodology.md`).
  FY2027's own p.334 "RATE CHANGE" table (Group Health budgeted $ change,
  FY2001-2027) was also used there for a 25-year Group Health
  reconstruction — see that methodology doc for the full accuracy caveat.
- **`FY2006-Financial-Plan.pdf`, `FY2008-`, `FY2010-`, `FY2012-`,
  `FY2015-`, `FY2018-`, `FY2020-Financial-Plan.pdf`** — seven historical
  Financial Plans, added 2026-09-02 (Ben: "I'd love town FTEs back to
  2005 - I think there has been some concern about actual staffing
  levels"), fetched from [Budget Central](https://www.brooklinema.gov/851/Budget-Central)
  (which archives back to FY2001; `DocumentCenter/View/5565`, `/5708`,
  `/5690`, `/5479`, `/5334`, `/12368`, `/18641` respectively). Each
  carries the same "Full-Time Equivalent (FTE) Positions Funded" table
  as the modern plans, in the pre-OpenGov format (GENERAL FUND and
  NON-GENERAL FUND reported separately, trailing 3-6 year windows).
  Together these seven give real, overlapping annual coverage FY2004-
  2020 — see `scripts/department_fte_history_fy04_20.py` and `output/
  department_fte_history_fy04_20_notes.md` for the full build, including
  two real structural findings caught along the way: "Finance" and
  "Public Works" are themselves subtotal-header rows in every one of
  these documents (double-counting risk if summed naively with their own
  sub-departments), and a genuine ~23-25 FTE discontinuity at the
  FY2006-2007 boundary between the FY2006/2008 Plans and the FY2010/2012
  Plans (Library, Public Works, and Police account for nearly all of
  it) — flagged as likely a reporting-convention change (the FY2010
  Plan's own budget message describes a hiring freeze and retirement-
  incentive program that year), not a real one-year staffing jump.
- **`FY27-FY31-Long-Range-Financial-Plan.pdf`** — the Town's own 5-year
  forecast (33-slide deck presented to Advisory Committee, Jan 2026),
  sourced from `DocumentCenter/View/60730`. **The single most directly
  useful document found for Phase 1/3** — it's essentially a rough draft
  of the "baseline Town-wide financial scenario" this project's Phase 1
  aims to build, just only to FY2031 not FY2040. Extracted in full to
  `output/town_own_forecast_fy26_31.csv`: FY26-31 revenue and expenditure
  by category, the Town's own cumulative surplus/deficit projection
  (-$42.7M by FY31, -9.2% of operating revenue), Town-vs-School split of
  that deficit (Town -$6.7M, Schools -$36.0M by FY31 — schools are the
  dominant driver), full Benefits sub-category detail through FY31, and a
  bond-by-bond debt exclusion schedule. See memorialized.md for the key
  assumptions (flat $2.5M/yr new growth, 12% health insurance FY27-29,
  pension funding schedule reaching full funding in 2030) and a real
  structural nuance: pension appropriations drop sharply after reaching
  full funding in FY2030, with that funding largely redirected to OPEB —
  a naive trend extrapolation of either line alone would badly misproject
  post-2030.

- **`FY2024-Audited-Financial-Statements.pdf`** (and prior-year editions
  `FY2021-` / `FY2022-Audited-Financial-Statements.pdf`) — the Town's
  annual audited financial statements. Already used for net pension/OPEB
  *liability* history (see `.claude/memorialized.md`, 2026-08-30). Used
  again 2026-09-02 for a different, GASB-required exhibit within the same
  document — the **Schedule of Contributions** (p.96 for pensions, p.104
  for OPEB, FY2024 edition): a real, audited annual *contribution* $
  history, not just the liability balance. Pension contributions,
  calendar-year basis, CY2014-2023 (10 years); OPEB contributions,
  fiscal-year basis, FY2017-2024 (8 years). The pension series
  independently cross-validates the Financial Plan's own narrative anchor
  ("$9.9M in FY07 to $37M in FY25") — both imply ~7.2-7.3%/yr, despite
  being differently-based (calendar vs. fiscal year) and independently
  sourced. Used in `scripts/benefits_category_forecast.py` — see that
  script's own methodology doc.

## Town committee reports & planning documents

- **`2030 Brookline Roadmap_Final.pdf`** — Town of Brookline Draft 2030
  Roadmap, approved by the Select Board May 19, 2026 (developed
  July 2025-May 2026 via department-head/Select Board interviews and
  four workshops, facilitated by the Consensus Building Institute). The
  Select Board's own 7-goal, 5-year strategic plan with KPIs; added to
  the project 2026-09-04. **Goal 3 ("Increase the Town's fiscal
  health and stability")** is the most directly relevant section — its
  own framing ("a structural deficit driven by rising fixed costs,
  limited revenue growth under Proposition 2-1/2... and growing service
  demands") closely echoes this project's own Part 2 finding. Names the
  Expenditures & Revenues Study Committee (ERSC) directly and leaves its
  future as a standing committee an open Select Board decision (3.A.1/
  3.A.2). Sets a real, citable KPI — **$15M-$20M of new growth revenue
  between FY26 and FY30** — checked against this project's own Phase 2
  scenarios 2026-09-04: `trend_continues` implies $23.9M and the
  peer-target scenarios $35.2M over the same window, both above the
  Town's own stated target (see `.claude/memorialized.md`, 2026-09-04).
  Strategy 3.B ("increase revenue through development" — streamlined
  permitting, a 5-year economic development plan) is the Roadmap's own
  version of this project's still-unmodeled "permitting/zoning reform"
  lever; 3.C ("revenue from non-development sources" — local-option
  taxes, fee/fine review, PILOT agreements, personal-property
  assessment gaps) connects to the local-receipts-growth finding in
  Part 2; 3.D.3 (revising the Unfunded Liabilities Policy to set a real
  OPEB full-funding deadline) and the "AAA bond rating maintained" KPI
  connect directly to `scripts/balance_sheet_liabilities_forecast.py`.
- **`ERSC Final Report FINAL 031326.pdf`** — Town of Brookline Expenditures
  and Revenues Study Committee Final Report, March 13, 2026. Contains RKG
  Associates' Town-wide marginal fiscal-impact model (~pp. 540–560),
  department FTE/salary history (p. 106), the Town/School fixed-cost split
  table (p. 30), the FY27–29 override recommendation and PSB MOU conditions,
  and the Economic Development Plan pipeline (pp. 137–157). Public source per
  the levy-history file's citation: brooklinema.gov `DocumentCenter/View/61986`.
  (An earlier attempt to pull the RKG section via a CivicClerk file-stream
  link resolved to the wrong document — a Feb 2020 Advisory Committee
  meeting notice — and was abandoned in favor of this full report, which
  Ben sourced directly.)
- **`2019-09-09-School-Building-Facility-Planning-Staff-Notes.pdf`** —
  Brookline Public Schools internal "Staff NOTES – PRIVILEDGED" DRAFT,
  authored by the Deputy Superintendent for Administration and Finance,
  dated 2019-09-04/09 (two draft dates appear across pages). Sourced from
  a Brookline K-8 finalsite.net resources link, provided by Ben
  2026-08-28. **Important caveats**: this is a 6+ year old internal draft
  staff memo, not a current or Town-adopted facilities master plan — it
  post-dates the failed May 2019 debt exclusion override and documents the
  resulting "no new funding" contingency planning. Treat as historical
  context and a lead worth verifying against something more current, not
  as the Town's current position.
  - **Baker School**: "We anticipate that by 2028 the Baker School will
    reach its current lifecycle and require renovation and/or expansion,
    especially if enrollment continues to climb or flattens out at a
    higher level than the capacity the district has available" (p.8).
    Originally built as a 3-section school, operating as 4-section. As of
    this document, "The School Committee has not discussed the Baker
    School renovation/expansion beyond the above" (p.9) — i.e. no funding
    plan or debt exclusion had been developed for Baker at the time of
    writing, unlike Pierce and Driscoll which already had named projects
    underway.
  - **Other schools, as of 2019**: "Currently all schools, with the
    exceptions of Coolidge Corner School and Heath, are experiencing
    overcrowding" (p.9). Named facility projects in progress at the time:
    Pierce (5-section rebuild, MSBA Statement of Interest, debt exclusion
    vote then expected May 2021), Driscoll (4-section expansion,
    submitted for Nov 2019 Town Meeting), Old Lincoln School (reopening as
    a 2-section school), Baldwin (repurposed to a BEEP center), and a
    "TBD 9th school" site search among four candidates (Newbury College,
    Pine Manor College, Maimonides, Old Lincoln). Runkle and Lawrence show
    overcrowding-related capacity deficits in the document's inventory
    table (p.13) but no named building project, similar to Baker's
    situation at the time.
  - **Cross-check against what's actually happened since**: per
    `data/brookline_overrides_debt_exclusions_history.csv`, Driscoll
    (2021), Newbury College land (2022), and Pierce (2024) have all since
    gotten debt exclusions — i.e. 3 of the 4 in-progress-or-candidate
    projects named in this 2019 memo have since been resolved via the
    ballot mechanism it anticipated. **Baker has not** — no debt exclusion
    for Baker appears anywhere in that history through FY2025. Combined
    with the document's own "by 2028" lifecycle estimate (now only ~2
    years out from today), this makes Baker a plausible candidate for
    "the next" debt exclusion, directly relevant to the Phase 1
    baseline-forecast debt-exclusion discussion — see
    `.claude/memorialized.md`, 2026-08-28. **Not confirmed** — this
    document is old and informal; whether the Town currently has any
    active Baker planning, timeline, or funding discussion is unverified
    and worth checking against a current source (a current CIP or
    facilities master plan, if one exists) rather than relying on this
    2019 memo alone.
- **`Brookline Public Schools Construction History.pdf`** — build/renovation
  year table for all 9 K-8 + high school buildings, provided by Ben
  2026-08-28, AI-generated (Gemini) from mostly secondary sources
  (Wikipedia, "Buildings of New England," Brookline Historical Society,
  MDS Architects — not primary Town documents). Ben asked that it be
  checked for accuracy; **spot-checked, not exhaustively verified**:
  - **Cross-checked against sources this project already has**: Driscoll
    ("2020s complete teardown and new building") and Pierce ("2024-2027
    ongoing full fossil-fuel-free rebuild") both line up with the known
    2021 and 2024 debt exclusions in
    `data/brookline_overrides_debt_exclusions_history.csv` — consistent.
  - **Baker School claim independently corroborated via a live web
    search** (2026-08-28): built 1936, renovated 1938 and 1958, nothing
    since — matches this document. A search for any current Baker
    building-committee, MSBA Statement of Interest, or CIP activity found
    nothing specific to Baker; the one active-sounding hit (the B-SPACE
    committee) turned out to be a 2013-era, now-archived committee whose
    "Expand in Place" recommendation is the same strategy the 2019 staff
    memo (see entry above) said was "built out" by 2019 — not current. A
    December 2024 Brookline School Committee meeting record (119pp,
    `record524-withattachments.pdf`) mentions Baker only for
    interim-principal and French-teacher-hiring items, nothing about
    facilities — i.e., **no active Baker building project surfaces in the
    most recent primary-source document checked**, consistent with (not
    proof of, but not contradicting) the "no funding plan yet" status the
    2019 memo described.
  - **Not independently verified**: the other 7 schools' exact years
    (Runkle, Lawrence, Roland Hayes/Heath, Lincoln, Ridley/Devotion, BHS)
    — plausible and internally consistent with what's otherwise known, but
    sourced only from Wikipedia/secondary sites, not cross-checked against
    a Town primary source the way Driscoll/Pierce/Baker were.
  - **Net read**: this document, combined with the 2019 memo and the
    Dec 2024 negative-evidence check, meaningfully strengthens (two
    independent sources, five years apart, both pointing the same way)
    rather than merely repeats the "Baker is the most likely next school
    building project" read — but still short of confirmation from a
    current, authoritative Town planning document.
- **`2026-05 Brookline long-term planning framework.pdf`** — pre-project
  pitch deck to Town stakeholders, May 2026.
- **`FY2021-Audited-Financial-Statements.pdf`**, **`FY2022-Audited-
  Financial-Statements.pdf`**, and **`FY2024-Audited-Financial-
  Statements.pdf`** — Town of Brookline audited financial statements
  (CAFR), sourced from
  [Budget Central](https://www.brooklinema.gov/851/Budget-Central)
  (`DocumentCenter/View/29702`, `/41470`, and `/61644` respectively).
  Used to precisely decompose the FY2021→FY2022 jump in Schedule A's
  "Taxes" line — see `.claude/memorialized.md` (2026-08-28 entry) for the
  full reconciliation. The General Fund "Schedule of Revenues,
  Expenditures and Changes in Fund Balance – Budget and Actual" (p. 82–83
  of each) is the key exhibit: it breaks the Schedule A "Taxes" bucket
  into its exact components (real estate/personal property tax, motor
  vehicle excise, hotel/motel tax, meals/marijuana excise, penalties &
  interest, PILOT) at actual-dollar precision, and confirmed ARPA federal
  relief was tracked in a separate fund, not the General Fund (MD&A,
  p. 19). **FY2024 is the most recent audited financial statement
  available** (added 2026-08-30, Ben) — its Letter of Transmittal is
  dated January 28, 2026, ~19 months after the FY2024 fiscal year end
  (June 30, 2024); at that lag, FY2025's audit (year end June 30, 2025)
  would not be expected to publish until roughly early 2027, consistent
  with no FY2025 audited statements existing on Budget Central as of
  2026-08-30. **FY2024's own Required Supplementary Information gives
  multi-year net pension liability (Town's proportionate share, Dec
  2014–2023, 10 years) and net OPEB liability (FY2017–2024, 8 years,
  full roll-forward: service cost, interest, assumption changes, benefit
  payments, investment income) tables** — see `.claude/memorialized.md`,
  2026-08-30 entry, for the full extracted series; this is the richest
  liability-history source found so far, well beyond the FY2021/2022-only
  2-year window used for the original OPEB brief. The full Audited
  Financial Statements series covers FY2001–2024 on Budget Central; only
  FY2021, FY2022, and FY2024 pulled so far (FY2023 not yet pulled — the
  FY2024 statement's own comparative/multi-year schedules cover most of
  what it would add).


## Residential exemption (owner-occupied) research (web sources)

Confirming whether Brookline's residential exemption (MGL c.59 §5C) needs
to be modeled for new-growth revenue forecasting — see `.claude/
memorialized.md` (2026-08-30) for the full finding (it doesn't, revenue-neutral
by design, confirmed directly by the Town's own memo below).

- [Residential Exemptions | Brookline, MA](https://www.brooklinema.gov/161/Residential-Exemptions) —
  program overview, eligibility, FY2026 dollar exemption ($354,974).
- [Town of Brookline, 2024.11.27 Tax Classification Summary Memo](https://brookline.news/wp-content/uploads/2024/12/2024.11.27-Tax-Classification-Summary-Memo.pdf) —
  Town Administrator Charles Carey's memo to the Select Board; the
  authoritative source for "these mechanisms merely shift tax burdens...
  they do not raise revenues," Brookline's exemption rate (20%, one of 18
  MA communities, second-lowest of 10 in Greater Boston region), and the
  separate Residential Factor/CIP-shift mechanism (1.75x max commercial
  multiplier, distinct from the residential exemption).
- Brookline's raw assessment workbook (`data/2026-04 Brookline assessments
  consolidated.xlsx`, `RESEXEMPT` field, FY17-24) — primary-source
  confirmation of participation rate and its declining trend (59.4% FY17
  -> 55.2% FY23), and (joined to the land-value-map classifier's
  new-construction events) that new construction specifically runs more
  non-owner-occupied (59.7%) than the existing stock.

## Pension actuarial valuation (the real funding-schedule source)

- **`Brookline-Retirement-System-2024-Actuarial-Valuation.pdf`** — Town of
  Brookline Contributory Retirement System, Actuarial Valuation and
  Review as of January 1, 2024 (added 2026-08-30, Ben asked directly
  whether we could find the Town's actual liability-balance forecast to
  2030). Sourced from mass.gov
  (`www.mass.gov/doc/brookline-retirement-board-valuation-report-2024/download`)
  — Massachusetts public pension valuation reports (prepared by Segal,
  regulated by PERAC) are filed with the state and published there, not
  on Brookline's own Budget Central page. This is the actual document
  that sets the Town's pension funding schedule — the Financial Plan's
  "full funding in 2030" claim traces directly to this report, not to a
  Town-internal projection. **Its "Funding schedule" table (p.26) gives
  the real year-by-year projected path**, not just the funding-schedule
  contribution dollars already extracted elsewhere:

  | FY | Employer Normal Cost | Amortization payment | Total ADC | Unfunded liability (start of year) |
  |---|---|---|---|---|
  | 2025 | $7,307,785 | $29,782,072 | $37,089,857 | $173,231,820 |
  | 2026 | $7,588,981 | $32,412,430 | $40,001,411 | $153,723,184 |
  | 2027 | $7,880,948 | $35,260,574 | $43,141,522 | $130,124,564 |
  | 2028 | $8,184,098 | $38,344,033 | $46,528,131 | $101,929,039 |
  | 2029 | $8,498,857 | $41,681,732 | $50,180,589 | $68,576,803 |
  | 2030 | $8,825,666 | $29,938,470 | $38,764,136 | $29,450,101 |
  | 2031 | $9,164,987 | $0 | $9,164,987 | $0 |

  FY2031's ADC is **entirely** Normal Cost, $0 amortization — direct,
  precise confirmation that the "large decrease in FY31" the Financial
  Plan mentions is the amortization payment dropping to zero, not the
  Normal Cost (ongoing cost of newly-earned benefits) going away. Assumed
  rate of return: 6.80% (lowered from 6.90% in this valuation). Next
  formal valuation: January 1, 2026 (biennial). **No equivalent
  Town-published year-by-year liability-balance projection exists for
  OPEB** — OPEB isn't subject to the same PERAC-mandated full-funding
  schedule pension is (the Town funds it voluntarily), so there's no
  analogous document to look for.

## Personal property research (Town classification hearing presentations)

Investigating whether "commercial new growth" in this project's model
conflates real estate with personal property (business equipment,
furniture, fixtures) - see `.claude/memorialized.md` (2026-08-30) for the
full finding (yes, substantially - personal property is 61% of pooled
FY22-25 CIP new-growth tax dollars, more than commercial real estate).

- [Town of Brookline FY2022 Tax Classification Hearing Presentation](https://brooklinema.gov/DocumentCenter/View/28076/FY2022_Classification_Hearing_Presentation)
- [Town of Brookline FY2023 Tax Classification Hearing Presentation](https://brooklinema.gov/DocumentCenter/View/37282/FY2023-Classification-Hearing-Presentation)
- [Town of Brookline FY2024 Tax Classification Hearing Presentation](https://brooklinema.gov/DocumentCenter/View/46707/FY2024-Classification-Hearing-Presentation-Online)
- [Town of Brookline FY2025 Tax Classification Hearing Presentation](https://www.brooklinema.gov/DocumentCenter/View/53636/FY2025-Classification-Hearing-Presentation---Revised)

Each has a "Value Comparison" slide (Residential/Commercial/Industrial/
Personal Property/Total, prior FY vs. current FY) and a "New Growth" slide
(Single Family Permits/Res. Condominiums/Multi-Family & Apts./Commercial/
Personal Property/Total, each with $ value growth and $ tax growth) -
these are the Board of Assessors' own authoritative class-level totals,
cross-validated exactly against `classify.py`'s `DOR_CIP_VALUE` dict
(Commercial + Personal Property new-growth value sums to the same figure
for both FY2022 and FY2025, the two years checked).


## Town building permit history (Building Department, 2026-09-15)

Supplied directly by the Town Building Department on request. Two exports
from two successive permitting systems, together covering 20 years:

- `data/Copy of GeoTMSData_1.xlsx` — legacy GeoTMS system, 68,354 rows,
  2006-01-04 to 2018-06-07 (effectively ends 2017-06). Fields: issue date,
  permit type, permit number, work description, address, status, owner and
  contractor/applicant location. **No construction-cost field.**
- `data/Copy of FOIA_BuildingWParcelv3_1.xlsx` — current system, 58,907
  rows, 2017-06-12 to 2026-09-08. Adds **`Estimated Cost`** (the
  self-reported construction value the permit fee is assessed on) and
  **`TOTAL INVOICED`** (the fee charged).

Handling notes that matter for any citation drawn from these: the current
export **repeats each permit once per contact row** (58,907 rows are 51,854
distinct permits, one id appearing 26 times; cost is consistent within an
id, so deduping on `RECORD ID` is safe). Despite the `BuildingWParcel`
filename there is **no parcel identifier** — the eight unnamed columns are
contractor address fields — so parcels are joined by street address via the
FY2026 assessment roll, matching 85.2% of permits and 81.9% of permit
dollars, with the unmatched remainder concentrated in large rental
complexes (Gerry Rd, which has zero rows in the roll, plus Thornton Rd,
Independence Dr, Sherman Rd). `Estimated Cost` is self-reported by the
applicant, which adds variance to any value-per-permit-dollar ratio built
on it.

Analysis: `scripts/permit_analysis.py` (read its header first). Findings
are in `.claude/memorialized.md` under 2026-09-15, and the fee-schedule
corroboration is worth noting here as a source in its own right: the
**median permit pays exactly $20.00 per $1,000** in every year FY2018–FY2026,
and the increase to $21 shows month by month across the FY2027 boundary
(2026-06 $20.00, 07 $20.10, 08 $20.63, 09 $21.00). That is primary
transactional confirmation of a rate change previously sourced only to a
dated alert on `brooklinema.gov/172/Building-Department`, while the Town's
own fee-schedule page still showed the old $20 rate.

## Housing pipeline (Planning Department, October 2026)

`data/Brookline Housing Active Development Pipeline 2026-10-15.xlsx` — every
project adding homes that the Town's web pages show as under construction,
permitted, in review or awaiting a zoning vote, compiled 10/15/2026 from the
Town's Chapter 40B, Site Plan Review, Major Impact Project and Zoning Board
pages and the Building Department's permit portal, with corrections from the
Planning Department the same day. Gross and net new homes, stage, permit path
and housing type per project; a sheet of small Zoning Board cases; and projects
completed 2023–2026. Completion dates in the file are rough estimates except
where the Town or a developer published one, and existing homes removed are
blank (counted as 0) where the Town doesn't state them. Not republished, since
it lists projects by name; used in totals only, for the 2,400 homes article
(`articles/2400-homes/pipeline.py`), together with the Housing Plan 2024's
Table 1.1 (Chapter 40B approvals 2014–2023) for how earlier approvals turned out.


## School seats map sources (October 2026)

Used by `school-seats-map/` (private working map; method in `school-seats-map/METHODOLOGY.md`):

- `data/Superintendent Report_9.16.26.pdf`, last two pages: K-8 sections and average class size by school
  and grade, September 11, 2026, and the class-size guidelines.
- `data/ERSC Schools Subcommittee packet 2025-12-01 (space and capacity).pdf` (49 pages; CivicClerk fileId
  27360): Cliff Brown's space and capacity analysis for the Expenditures and Revenues Study Committee's
  Schools Subcommittee: floor plans of each K-8 building with room uses (pp. 8-43), the draft "School
  Capacity Information" table with past PSB capacity figures (p. 44), and open seats by section as of
  March 6, 2025 (pp. 45-46). Minutes: `data/ERSC Schools Subcommittee minutes 2025-12-01.pdf` (fileId 27290).
- `data/Pierce School FAS presentation 2022-02 (educational program).pdf`: the Pierce design's educational
  program against the MSBA standard (p. 3); from the Wayback Machine copy of the PSB site.
- `data/GIS-CoreSchoolDistricts11x17_202608131433147293.pdf` and
  `data/GIS-SchoolDistrictsWithBufferZones11X17_202608131428193893.pdf`: the Town GIS maps of the K-8
  districts and buffer zones, August 13, 2026 (Ben added them 2026-10-17). From the Town's Schools page,
  https://www.brooklinema.gov/723/Schools: core districts
  https://www.brooklinema.gov/DocumentCenter/View/28438/Core-School-Districts---11x17 and districts with
  buffer zones https://www.brooklinema.gov/DocumentCenter/View/28437/School-Districts-and-Buffer-Zones---11X17
  (links may serve a newer version of the map).
- District boundaries: the Town's hosted ArcGIS layer (URL in the methodology), saved in
  `school-seats-map/data/`.
- Public links (found and md5-checked against the local copies 2026-10-25, unless noted):
  - Superintendent's Report 9/16/26: https://brooklinema.portal.civicclerk.com/event/16515/files/attachment/18920
    (CivicClerk attachment 18920; linked from https://www.psbma.org/district/school-committee/meeting-materials).
    The cost-of-a-student article links a Google Drive copy instead.
  - ERSC Schools Subcommittee packet 12/1/2025: https://brooklinema.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=27360,plainText=false)
    (portal: https://brooklinema.portal.civicclerk.com/event/14550/files/agenda/27360); minutes: https://brooklinema.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=27290,plainText=false).
  - Pierce FAS presentation 2022-02: https://web.archive.org/web/20240701060858/https://www.brookline.k12.ma.us/cms/lib/MA01907509/Centricity/Domain/722/Pierce%20FAS%20Meeting%20Presentation%20-%20FINAL.pdf
    (the 20230207 capture is truncated). Its p. 2 is the source of "plus 48 Pre-K".
  - Pierce project page ("4-sections per grade plus 3 BEEP classrooms"): https://www.psbma.org/district-projects/pierce-school-building-project
  - MSBA Pierce memo (dated Feb 18, 2022, for the March 2, 2022 Board meeting; design enrollment 725 K-8, no pre-K figure):
    https://www.massschoolbuildings.org/sites/default/files/edit-contentfiles/About_Us/Board_Meetings/2022_Board/3_2_2022/1.%20Brookline_Pierce_PS%20Memo_Final.pdf
  - Driscoll Schematic Design Report, May 22, 2019 (four sections; not saved locally):
    https://resources.finalsite.net/images/v1745567888/brooklinek12maus/khmgvwifrsh6qizorcha/1_driscollsdreport.pdf;
    project page (36 classrooms): https://www.psbma.org/district-projects/driscoll-school-building-project
  - Devotion/Ridley MSBA memo, Nov 12, 2014 (design enrollment 1,010 K-8; not saved locally):
    https://www.massschoolbuildings.org/sites/default/files/edit-contentfiles/About_Us/Board_Meetings/2014_Board/11_19_14/Brookline_Devotion_PS_11_19_14.pdf;
    "5-section school ... 1,050 students" (with pre-K): PSB Internal School Facility Assessment Summary, archived:
    https://web.archive.org/web/20201124125105/https://www.brookline.k12.ma.us/cms/lib/MA01907509/Centricity/Domain/62/Internal%20School%20Facility%20Assessment%20Summary.pdf
  - AdvCom FY27 write-up: attachment 15590 above is the 37-page write-up; the local 39-page file adds a 2-page agenda.

## Development Look-Ahead (Planning Department, Select Board workshop 2026-06-16)

`data/Development Look-Ahead June 2026.pdf` — "Potential Development
Opportunities," presented to the Select Board June 16, 2026. Sixteen slides,
mostly priority-setting; three carry figures used here. Two slides carry the
Town's own printed corrections, both noted on the slides themselves (slide 5's
Coolidge Corner box omitted "JFK"; slide 6's box read "40 Kent St." where it
should have read the Kent/Webster lots, 20 and 32 Kent St.).

- **Slide 7, "Estimated FY26 Net Fiscal Revenue Impact"** — annual net fiscal
  impact by use type for recent development projects: condominium
  $13,000–$16,000 per home, apartment $1,750–$5,400 per home, 1 & 2 Brookline
  Place $7,300 per 1,000 sqft of building, hotels $7,000–$22,700 per 1,000
  sqft. Both residential rows are explicitly labelled **"no deduction for
  pre-development value"**, so they are gross of the tax the parcel already
  paid, not incremental.
- **Slide 8, "Estimated $25-28 Million for Future Override"** — the same
  impacts converted into the quantity needed over three years to fill a
  $25–28M override: 1,563–2,154 condos, 4,630–16,000 apartments, 10–11 office
  campuses of the 1 & 2 Brookline Place type, or 14–16 hotels.
- **Slide 9, "Building Permits for Net New Homes"** — net new units by
  calendar year: 2022 = 252, 2023 = 190, 2024 = 57, three-year total 499.

Verified 2026-09-22: every figure on slide 8 reproduces exactly from slide 7's
impacts and the $25–28M range (low dollars over high impact to high dollars
over low impact). Reverse-engineering slide 7 through this project's own
marginal-cost constants implies $1.62M–$1.91M of assessed value per condo,
$478k–$835k per apartment, and $492/sqft for 1 & 2 Brookline Place, the last
within 5% of this project's independently derived `COM_VALUE_PER_SQFT` of
$518.

Two cautions for anyone citing this deck. The hotel row's top end implies
about $1,389/sqft of assessed value, roughly 2.8x the town-wide taxable
commercial average, which is more than the property tax alone comfortably
supports; the rooms excise is the likely additional component, and it is a
local receipt rather than levy-limit capacity. And the third column
(impact per sqft of land) cannot be cross-multiplied with the second: the
apartment row's endpoints imply 2,917 and 557 sqft of land per unit, so each
row's two ranges come from different underlying projects.

Slide 9 is used in `scripts/new_growth_scenario_forecast.py` as the physical
denominator behind `RES_VALUE_PER_UNIT` (see that script's docstring) — it is
the only net-new-housing count available that does not depend on the
assessment roll's unit-count field, which carries recording changes that make
a roll-derived count unusable for this purpose.

## School enrollment & staffing history (DESE)

- **`output/school_enrollment_staffing_fy05_25.csv`** — added 2026-09-02,
  expanded same day (Ben: what's driving school budget growth → is there
  a real year-by-year series or just a few spot-checked years? → do we
  have total school employee count, and what else is available?). Pulled
  directly from the Massachusetts Department of Elementary and Secondary
  Education's own School and District Profiles site
  (profiles.doe.mass.edu), which publishes one stable, year-specific page
  per district per fiscal year (a `fycode` URL parameter, e.g.
  `?orgcode=00460000&orgtypecode=5&fycode=2015` = Brookline's 2014-15
  school year) — not an API, but a real per-year scrape via
  `scripts/fetch_school_staffing_history.py`, FY2005-2025, 21 years, five
  series:
  - **Total enrollment** — `profiles/student.aspx`, "Enrollment by
    Gender" table's Total row. FY2005+.
  - **Teacher FTE** — `profiles/teacher.aspx`, "Total # of Teachers
    (FTE)" row. FY2005+. **Teachers only, not total district staff** -
    see the next bullet for that.
  - **Total staff FTE (all district employees)** —
    `profiles/teacher.aspx?...&leftNavId=817` ("Staffing Data by Race,
    Ethnicity, Gender by FTE," the "FTE Count" row) - found by tracing
    the exact URL the ERSC report's own Table 5 footnote cited, then
    independently confirmed: this report's FY24-25 figure (1,249.4)
    matches ERSC's Table 5 FY24-25 entry exactly. **This is the real
    "total school employees" series** teacher.aspx alone understates
    (FY19-20: 1,378.4 total vs. 645.8 teachers-only, same year). Only
    available FY2008+ ("No Data Reported" for FY2005-2007, confirmed
    directly, not a scrape gap). One flagged discrepancy: ERSC's own
    Table 5 footnote says FY22-23's DESE figure (1,270.77) is itself
    wrong ("a request for correction was submitted and never completed
    by DESE") - this project's independently-scraped FY22-23 figure
    (1,345.8) differs from ERSC's, consistent with ERSC's own caveat that
    the underlying DESE figure for that one year is unreliable.
  - **Selected Populations (4 metrics in one fetch)** —
    `profiles/student.aspx?...&leftNavId=305`: Students with Disabilities
    %, English Learners %, Low Income %, First Language Not English % of
    enrollment. FY2005+, though Low Income % has a real gap FY2015-2021
    (DESE reporting-methodology transition, not a scrape failure - "High
    Needs," a newer composite metric, appears only after that gap).
    **Students with Disabilities % here uses a different DESE
    methodology than the Indicator-5 IEP count below and the two series
    don't agree closely** (e.g. FY2005: 18.4% here vs. no Indicator-5
    data published that year at all) - both are kept, not reconciled,
    since they're genuinely different DESE definitions.
  - **Students with IEPs (raw count, Indicator 5)** —
    `gis/sped_map.aspx`, "Enrolled students with IEPs" row. FY2007+ (not
    FY2005-2006, confirmed directly).

  **Real findings**: enrollment grew 31% from FY2005 to its actual peak
  (FY2019, 7,855 - not FY2019-20/7,777 as an earlier spot-check implied;
  FY2019-20 was already down slightly from the true FY2019 peak), then
  fell 12.2% in a single year (FY2021, 7,855→6,891) before partially
  stabilizing (~7,020-7,060 by FY23-25). **Total staff FTE grew *faster*
  than enrollment through the growth phase** (968.4→1,378.4, FY2008-2020,
  +42.3% vs. enrollment's +26.1% over the same window) but then **fell
  almost exactly in proportion to enrollment's own decline**
  (1,378.4→1,249.4, -9.4%, vs. enrollment's -9.7%, FY2020-2025) - a much
  more precise, and less alarming, picture than teacher-FTE-alone
  suggested (teachers specifically fell disproportionately, -19.3% over
  the same window, while total staff barely diverged from enrollment at
  all - meaning it's specifically classroom-teacher headcount that was
  cut hardest post-COVID, not overall district staffing, which tracked
  enrollment closely in both directions once the fuller total-staff
  figure is used instead of teachers alone).

- **`output/school_spending_by_category_fy09_25.csv`,
  `output/school_teacher_salary_fy09_25.csv`,
  `output/school_staff_by_role_fy09_25.csv`** — added 2026-09-02 (Ben:
  "please also try to find a high level breakdown of the budget between
  categories"). Pulled via `scripts/fetch_school_budget_categories.py`
  from the Massachusetts Education-to-Career Research and Data Hub's
  "District Expenditures by Spending Category" dataset
  (educationtocareer.data.mass.gov, dataset `er3w-dyti`) — a genuine
  Socrata open-data API (`/resource/er3w-dyti.json?dist_code=00460000`),
  not a page scrape, one call returns all years/categories for Brookline
  at once. This is DESE's own End-of-Year Financial Report function
  categorization (Administration, Guidance/Counseling/Testing,
  Instructional Leadership, Instructional Materials/Equipment/Tech,
  Insurance/Retirement/Other, Operations & Maintenance, Other Teaching
  Services, Professional Development, Pupil Services, Teachers) - the
  same categories DESE uses statewide, so directly peer-comparable if
  ever wanted. FY2009-2025 (17 years - DESE's own dataset start point,
  4 years short of this project's FY2005 floor elsewhere). Category $
  sum to "Total In-District Expenditures" (confirmed: FY2025 sum $27,587
  vs. reported $27,589, $2 rounding); "Total Expenditures" additionally
  includes out-of-district special-education placements, not broken out
  further. Average Teacher Salary only available FY2018+ within this
  dataset (blank FY2009-2017 - a real gap, not a scrape failure).
  See `output/school_budget_drivers_summary.md` for the full synthesis:
  Pupil Services (+151.4%), Guidance (+105.4%), Benefits (+102.5%), and
  Other Teaching Services (+96.2%) all grew far faster than the 70.0%
  blended total FY2009-2025, while Professional Development actually
  *fell* 29.2% - and Special Education Instructional Support FTE more
  than doubled (+117.4%) over the same window.

## Credit ratings

- **MA DLS Municipal Bond Ratings database** —
  `dlsgateway.dor.state.ma.us/reports/rdPage.aspx?rdReport=DLS_bond_ratings`
  (Moody's only; export to Excel rather than reading the paginated page).
  Confirms **Brookline Aaa continuously 2006–2026**, and that only **14**
  Massachusetts communities hold a Moody's Aaa. **Three traps, all verified
  2026-09-13 — read before reusing this source:** (1) column years lag actual
  rating actions by up to two years (Sharon's July 2013 downgrade appears in
  the "2015" column), so never date an action from a column header; (2)
  Moody's Massachusetts coverage fell from **245 rated communities in 2011 to
  119 in 2026**, so an apparent downgrade is frequently a *withdrawal* or a
  stale value — Brockton (Oct 2024) and Holyoke (Oct 2024) are confirmed
  withdrawals; (3) the April 2010 global-scale recalibration lifted most local
  GOs about two notches, so any comparison spanning 2010 shows phantom
  upgrades.
- **Moody's credit opinion, Town of Brookline, 2026-02-23** —
  `brooklinema.gov/DocumentCenter/View/50252/Moodys-Rating-Report-2-23-24`.
  Aaa/stable. Names two credit challenges directly relevant to this project:
  "below-average available reserves as a % of revenue for the rating
  category" (**23.1%** against a Aaa median of **61.7%**) and "elevated
  leverage… due to recent large capital projects including schools"
  (long-term liabilities 308% of revenue vs. a 263% median; fixed costs 17.0%
  vs. 11.6%). Explicit downgrade trigger: **"decline in available reserves to
  below 20% of revenue."**
  **Note:** S&P's AAA on Brookline is last confirmed February 2021 and was not
  verifiable for 2022–2026 — always name the agency, since S&P's AAA is far
  more common in Massachusetts than Moody's Aaa and towns holding both often
  market themselves as simply "AAA-rated."

## Prior Town committee reports

- **`BFAC Report FINAL 2020-02-05.pdf`** — Brookline Fiscal Advisory
  Committee, Final Report, **February 5, 2020** (135pp, 18 recommendations,
  chaired by David Kirshner). Retrieved 2026-09-13 from
  brooklinema.gov/DocumentCenter/View/21168. **Note the date**: the file is
  titled "February-5-Final-BFAC-Report" on the Town site and is six years
  old — it predates COVID, both recent overrides, the ERSC report and the
  2030 Roadmap.
  Most useful material: the constraint on its own charge (p2 — "BFAC was
  concurrently told not to examine cost reduction opportunities," which its
  own reproduced charge at p74 arguably contradicts by asking "What steps
  should the Town take to control year-over-year increases in expenses?");
  the AAA-rating frame and the cost of a downgrade (~$2.4–2.5M PV per $100M
  25-yr borrowing, pp3/18); Appendix G's estimate that **465,000 sq ft** of
  new commercial development would service the debt on a $100M school
  (p100); Table 3's ranking of Brookline against twelve peer AAA
  communities (p23); and Chart 1, which preserves the Town's **December
  2019** long-range forecast and is therefore scoreable against actuals.
  **Two headline findings are no longer true** — see `.claude/memorialized.md`
  2026-09-13 on reserves. **Cite carefully**: the report contains at least
  eight internal inconsistencies and at least one arithmetic error (PSB
  growth of 115% over FY05–FY20 reported as "8% per year"; compounded it is
  5.2%).

## Whitepaper / public framing

- [How does construction impact Brookline's town finances?](https://www.brooklinefuture.org/post/how-does-construction-impact-brookline-s-town-finances) —
  Ben's original whitepaper; thesis and peer-town framing this project extends.

## Expense driver tree sources (added 2026-09-28)

- `Brookline-Retirement-System-2014-Actuarial-Valuation.pdf` — Town DocumentCenter
  View/6540. Prior-valuation column gives FY2013 employer normal cost $3,432,407
  (5.48% of payroll). Used for the FY2011 normal cost in `expense_drivers_tree.py`.
- `qcew_cache/` — BLS QCEW open-data API (`data.bls.gov/cew/data/api/{year}/a/area/{25000|US000}.csv`),
  2014-2024, local government (own_code 3) average annual pay. Fetched by
  `scripts/fetch_qcew_local_gov_pay.py`.
- ERSC Final Report (already listed) p.567: Town/Schools chart of enrolled K-12
  students per unit in 8+ unit developments built since 2015, Fall 2025.

## 2030 Roadmap, current web copy and Goal 3 tracker (downloaded 2026-09-29)
- `data/2030_Roadmap_web.pdf`: Town DocumentCenter View/63347, linked from https://www.brooklinema.gov/4102/2030-Roadmap. Same text as `2030 Brookline Roadmap_Final.pdf` (word-level diff: formatting and page labels only; "Draft" removed from the title).
- `data/2030_Roadmap_Goal3_Tracker.html`: DocumentCenter View/63172, "2030 Roadmap Tracker Public - Goal 3 Action Tracking" (Excel published as HTML). Lists each Goal 3 action with departments and a start date (7/1/27 to 7/1/30); the status bar is empty. The page says the tracker is updated quarterly (March, June, September, December).


## Births by municipality (added 2026-10-06)

- `data/MA-DPH-2020-Birth-Report.docx`, `data/MA-DPH-2023-Birth-Report.docx`: Massachusetts Department of Public Health, Registry of Vital Records and Statistics, "Massachusetts Births 2020" and "Massachusetts Births 2023", from https://www.mass.gov/lists/annual-massachusetts-birth-reports (downloaded through Chrome; mass.gov returns 403 to scripts). Table 17, resident births by municipality, parsed to `output/ma_resident_births_by_town_2020_2023.csv` (351 towns; 2023 total matches the state's 67,068). Brookline: 487 (2020, matches the earlier series), 422 (2023). The 2024 report was not yet published in October 2026.

## School Department enrollment report and the ERSC enrollment draft (2025-26)

- `data/School Committee minutes 2025-11-06 (PSB Enrollment Report).pdf` (107 pages): minutes of
  the November 6, 2025 School Committee meeting, with the "PSB Enrollment Report" slides (about
  pp. 70-80; the standalone slide file's link is broken). Summer new-student registrations by
  prior school (out of state, Massachusetts public, Massachusetts private), withdrawals, and the
  FY2027 projection; the minutes record staff saying there was "nothing tangible to observe" yet
  from federal policy on in-migration. Nothing on family income or size. From
  brooklinema.api.civicclerk.com, fileId 27220.
- `data/ERSC Schools Subcommittee packet 2026-03-02 (enrollment draft).pdf` (6 pages): the
  Expenditures and Revenues Study Committee Schools Subcommittee's draft section on enrollment
  forecasting; Brookline third among DESE peer districts for student turnover, attributed to
  international graduate students and professionals on short assignments. fileId 30325.
- Checked 2026-10-16 for a reported School Department analysis of new arrivals' income and family
  size; neither document has one.

## Cropper-McKibben, Public Schools of Brookline Demographic Study 2023 (revised 04/03/2024)
- File: `data/Cropper_McKibben_PSB_Demographic_Study_2023.pdf` (57 pages), downloaded 2026-10-06 from
  https://www.psbma.org/fs/resource-manager/view/e33b9111-f183-4cb8-8bd2-10748ca98a3e
  (linked from the PSB FY27-29 budget summary, footnote 2; the 2019 study is footnote 1:
  https://www.psbma.org/fs/resource-manager/view/dd07d2e0-d914-4898-b25e-00eb975e567f).
- The forecast the School Department plans with; its Pre-K-12 totals are the model's CM_PK12
  (PSB FY27-29 summary Table 7). Exec summary: rise from new apartments, empty-nest turnover,
  in-migration of young households; assumes ~1,500 new units 2020-2034; resident TFR 1.07.
- Also: `data/McKibben_Brookline_Demographic_Study_2020-02-06.pdf`, the Feb 2020 presentation of the 2019 study.

## Debt and the CPA surcharge (added 2026-10-08, Ben)

- `Brookline_GO_Bonds_2025_Official_Statement.pdf` — official statement for the $106.3M General
  Obligation Municipal Purpose Loan of 2025 Bonds (dated 6/17/2025), from EMMA. p.17: this issue's
  principal by fund (exempt $97.8M, Pierce and fire stations, level debt service to 2050); p.55:
  annual debt service on all debt outstanding at 6/30/2024 to FY2049, with $405.9M of $466.4M
  principal excluded from Prop 2½ (the schedule itself is not split). Also lists every debt
  exclusion vote and the Devotion borrowings (2016-2018).
- `Brookline_CPA_and_Exemption_page_2026-10.pdf` — Assessors' CPA page: surcharge is 1% of the
  net tax after the residential and personal exemptions (worked FY2026 example: $1M home, $66.05);
  no $100,000 value exemption; income-based exemptions for low-income owners and
  low/moderate-income seniors.
- `Brookline_CPA_Funding_page_2026-10.pdf` — CPA program page: adopted May 4, 2021; FY25-27
  awards $16.65M across 37 projects.

## Births, 2024 (added 2026-10-08, Ben)

- `Brookline_2024_Annual_Town_Report.pdf` — Town of Brookline 2024 Annual Report. Town Clerk's
  "Vital Statistics" box (report p.37): **443 births** in 2024 (also 337 deaths, 270 marriages).
  This is the Town Clerk's count; DPH's resident-birth count for 2024 (not yet published) may
  differ slightly in definition. DPH counted 422 resident births in 2023.

## Brookline Housing Plans, 2023 and 2024 (added 2026-10-11)

`data/Brookline Housing Plan 2023-03-15.pdf` and `data/Brookline Housing Plan 2024 (state-approved
2024-11-12).pdf` (brooklinema.gov DocumentCenter 40164 and 53784; the site blocks scripted
downloads, Ben saved them). The 2024 plan's Table 1.1, "Brookline's Chapter 40B History,
2016-Present" (DPCD "Chapter 40B Status" page as of 2024-02-21), lists 19 approved comprehensive
permits totalling 1,221 homes: 396 built, 473 under construction, 352 not built. The text's "over
1,200 new units would have been added to the SHI" is that total, built and unbuilt. The 2023
plan's 1,248 counts SHI-eligible units in approved permits (the Housing Authority's senior building counted at 115 with its 60
existing). Neither is a backlog of unbuilt homes.

## Peer practice in long-term planning (added 2026-10-11)

Standards (GFOA, DLS FMRB, ICMA Financial Trend Monitoring System, Moody's), what Newton,
Arlington, Lexington and Palo Alto do, public budget tools, and a list of metrics the
standards track against what the site tracks: `docs/research_long_term_planning_practice.md`.
Background only; several items were read in secondary summaries and are marked so there.

## New growth rules and the permit count (added 2026-10-12)

- `data/DLS new growth guidelines (IGR).pdf` — DLS Informational Guideline Release, FY2021 guidelines
  for determining the levy limit increase for tax base growth. Section II.A: new growth is the increase
  in each parcel's assessment over the prior year from physical, unit or status changes; not reduced by
  decreases elsewhere.
- `data/DLS Understanding and Analyzing New Growth Part 1.pdf` — DLS article: a demolished building's
  loss of value does not reduce new growth; new growth is multiplied by the prior year's tax rate.
- `output/permit_homes_coded.csv`, `output/permit_homes_by_year.csv`, `output/permit_homes_mix.csv`,
  `output/permit_homes_methodology.md` — every Town building permit 2008-2025 that could create or
  remove a home, read and coded by hand from `data/permits_cache/` (foia_joined.csv, geotms.csv).

## Fiscal impact methods literature (added 2026-10-12)

`docs/research_fiscal_impact_methods.md` — when project-level fiscal impact models hold and when they
don't (Burchell & Listokin 1978; Paulsen 2014; Kotchen & Schulte 2009; Edwards & Huddleston 2010;
Kotval & Mullin; TischlerBise; Ladd; MAPC; Rapoza & Goodman), each entry marked read / abstract /
secondary / not read. Check entries not marked "read" before citing them publicly.

## School Department budget documents (`psb_budget/`, saved 2026-09-29)

About 35 Public Schools of Brookline budget files (FY25 to FY28 budget reports, guidelines,
slides, FAQs, Advisory Committee write-ups). Download URLs below were recovered on 2026-10-24
from the command that fetched them on 2026-09-29; files without one still need theirs.

- `FY26_sped_transportation.pdf`: one page exported from a Google Sheet, "FY26 Budget by Account
  Description", table "Special Ed-RSC Transportation" with FY23-FY26 budgets and student counts;
  FY26 total $4,479,950 for 177 students, including foster care and McKinney-Vento transportation.
  Cited in the cost-of-a-new-student article.
  https://www.psbma.org/fs/resource-manager/view/c27fd510-112b-419a-9dfa-8f85910eee4a
- `FY26_budget_closing_summary.pdf`: https://brooklinema.portal.civicclerk.com/event/16545/files/attachment/18374
- `AdvCom_Schools_Subcommittee_FY27_writeup_draft_2026-04-28_packet.pdf`: https://brooklinema.portal.civicclerk.com/event/16301/files/attachment/15590
- `2025-11_PSB_5yr_budget_projection.pdf`: https://www.psbma.org/fs/resource-manager/view/a06303c8-fe91-4656-93b2-b9184567fc6f
- `2025_PSB_forecast_spreadsheet.pdf`: https://www.psbma.org/fs/resource-manager/view/f85ff545-1e3c-4a9b-b413-d709361b904f
- `FY27-31_budget_guidelines_3rd_draft.pdf`: https://www.psbma.org/fs/resource-manager/view/a9762442-8107-4e14-8b70-f05d3dbc9001
- `FY27-31_budget_guidelines_v1.pdf`: https://www.psbma.org/fs/resource-manager/view/e05da75d-b812-4721-8346-87101ecf8127
- `FY27_budget_guidelines_voted.pdf`: https://www.psbma.org/fs/resource-manager/view/bb4af822-778b-44b4-89ae-43617af8f80c
- `FY2027_proposed_budget.pdf`: https://www.psbma.org/fs/resource-manager/view/9302441c-da76-4b5e-978b-bbf53e0b5f44
- `FY27_budget_slides_2026-02-05.pdf`: https://brooklinema.portal.civicclerk.com/event/14953/files/attachment/10830
- `FY27_budget_hearing_slides.pdf`: https://brooklinema.portal.civicclerk.com/event/14954/files/attachment/10976
- `FY27_budget_update_hearing.pdf`: https://brooklinema.portal.civicclerk.com/event/14954/files/attachment/10977
- `FY27_budget_FAQs_hearing.pdf`: https://brooklinema.portal.civicclerk.com/event/14954/files/attachment/10974
- `FY27_budget_slides_2026-02-26.pdf`: https://brooklinema.portal.civicclerk.com/event/15013/files/attachment/14183
- `FY27_budget_FAQs_2026-02-26.pdf`: https://brooklinema.portal.civicclerk.com/event/15013/files/attachment/14181
- `FY27_failed_override_impacts.pdf`: https://brooklinema.portal.civicclerk.com/event/14115/files/attachment/14307
- `FY27_budget_presentation_vote.pdf`: https://brooklinema.portal.civicclerk.com/event/14117/files/attachment/14725
- `FY27_budget_request_final.pdf`: https://brooklinema.portal.civicclerk.com/event/14116/files/attachment/14753
- `FY26_budget_updates_2026-06.pdf`: https://brooklinema.portal.civicclerk.com/event/16397/files/attachment/16248
- `FY26_superintendent_financial_update.pdf`: https://brooklinema.portal.civicclerk.com/event/14122/files/attachment/16252
- `FY26_level_service_budget.pdf`: https://www.psbma.org/fs/resource-manager/view/e7f8d2c2-80ac-492e-9120-19c18190d89b
- `FY26_level_service_cost_drivers.pdf`: https://www.psbma.org/fs/resource-manager/view/93545760-ec69-4987-b7c8-976d8ff60f70
- `FY26_initial_budget_request.pdf`: https://www.psbma.org/fs/resource-manager/view/8fba38ef-ed79-4f7b-9adc-3c45bd2e93c9
- `FY26_initial_budget_slides.pdf`: https://www.psbma.org/fs/resource-manager/view/f5beb09f-2819-4637-add2-4581f5c7e02e
- `FY25_deficit_funding_plan.pdf`: https://www.psbma.org/fs/resource-manager/view/2a9f206e-3166-4e7c-abb6-9f3c3cae92f0
- `FY25_budget_close_report.pdf`: https://www.psbma.org/fs/resource-manager/view/b1229118-9bac-4e94-911b-bee795005cf2
- `FY26_Q1_budget_report.pdf`: https://www.psbma.org/fs/resource-manager/view/da5505a9-2e31-448f-b1ef-66fe31078fad
- `FY26_budget_by_cost_center.pdf`: https://www.psbma.org/fs/resource-manager/view/6632d143-835a-4546-a154-68e2c14a2e51

## School enrollment and sections history (added 2026-10-25)

- `dese_enrollment/school_grade_enrollment.csv`: DESE enrollment by school and grade, Brookline schools,
  1994-2026 (school year = the spring it ends; each year is the October 1 count, so the latest, 2026, is October 1, 2025, a year before the Superintendent's September 2026 report). Education-to-Career data hub, "Enrollment: Grade,
  Race/Ethnicity, Gender, and Selected Populations",
  https://educationtocareer.data.mass.gov/resource/t8td-gens.csv?dist_code=00460000&org_type=School
- `psb_history/2017-01-09_9th_school_feasibility_kickoff.pdf`: PSB, 9th school feasibility phase kickoff,
  January 9, 2017; p. 10, "Our Schools Have Already Grown", intended vs. current sections per grade by school
  (Baker 3 vs. 4 1/2); p. 14, 2015-16 class sizes (average 21, 254 rooms) and the 2020-21 projection (average 24). Original link is dead since the move to psbma.org; archived copy:
  https://web.archive.org/web/20240424113341/https://www.brookline.k12.ma.us/cms/lib/MA01907509/Centricity/Domain/722/Feasibility_Phase_%20Kickoff_Meeting_01.09.2017.pdf
- `psb_history/2016-10-07_enrollment_report_and_boundary_update.pdf`: PSB enrollment projections and boundary
  update, October 7, 2016 ("2 modular classrooms added at Baker"). Archived:
  https://web.archive.org/web/2024/https://www.brookline.k12.ma.us/cms/lib/MA01907509/Centricity/Domain/722/2016_10_07_Enrollment_Report_and_Boundary_Update.pdf
- `psb_history/2016_preliminary_enrollment_projection.pdf`: PSB Enrollment Working Group, 2016 Preliminary
  Enrollment Projection (March 30, 2017): enrollment by school and grade, FY17 actual. Archived:
  https://web.archive.org/web/2024/https://www.brookline.k12.ma.us/cms/lib/MA01907509/Centricity/Domain/4/2016%20Enrollment%20Report.pdf

## Comprehensive plan (added 2026-10-25, Ben)

- Draft actions, October 13, 2026: https://www.brooklinema.gov/DocumentCenter/View/63508/1013-Comp-Plan-Draft-Actions-
  (Ben's link; the source of the goal of 1,600 to 2,400 new homes by 2035 cited in the listserv reply). Not saved
  locally: brooklinema.gov returns a Cloudflare 403 to scripts, so the wording and page aren't checked here.

## Special education (added 2026-10-26)

- `dese_sped/direct-expenditure-trends.xlsx`: DESE RADAR, Direct Special Education Expenditures, FY08 to FY25
  (file dated May 12, 2026; page updated July 29, 2026): https://www.doe.mass.edu/research/radar/direct-expenditure-trends.xlsx
  (linked from https://www.doe.mass.edu/research/radar/). Brookline FY2025: in-district teaching $28.52M, other
  instructional $4.72M, in-district transportation $2.51M; out-of-district $10.17M (tuition to Mass. non-public
  and out-of-state schools $8.52M, Mass. public schools and collaboratives $0.08M, out-of-district transportation
  $1.57M); total operating $203.9M. All funds; PSB's FY2026 General Fund report shows only $3.0M of
  out-of-district tuition.
  FY2024's in-district total, $34.95M, matches the ERSC report's figure.
- `dese_sped/circuit-breaker-fy2025-reimbursement.xlsx`: DESE, FY2025 Circuit Breaker reimbursement (FY2024 claims),
  https://www.doe.mass.edu/finance/circuitbreaker/payments/fy2025-reimbursement.xlsx. Brookline $4,942,020 total
  (including a $607,145 supplemental payment, July 2025).
- `dese_sped/circuit-breaker-fy2026-reimbursement.xlsx`: DESE, FY2026 final Circuit Breaker reimbursement listing
  (FY2025 claims; updated June 8, 2026), https://www.doe.mass.edu/finance/circuitbreaker/payments/fy2026-reimbursement.xlsx.
  Brookline: 72 eligible students, $10,888,938 eligible cost, $5,237,567 reimbursement. Used by
  `scripts/special_education_cost_per_student.py` (the middle tier of an added student's cost).
- DESE End of Year Report instructions (FY2024 printing), Schedule 4: special education spending covers
  instructional services (2000) and tuition (9000), including Circuit Breaker spending; benefits (5000) are reported
  separately. https://www.doe.mass.edu/finance/accounting/eoy/ (read 2026-10-26; not saved).
- Students with disabilities share, DESE school and district profiles, Selected Populations: 18.6% in 2024-25,
  18.0% in 2025-26. https://profiles.doe.mass.edu/profiles/student.aspx?orgcode=00460000&orgtypecode=5&leftNavId=305&fycode=2025
  (not saved locally; read from the page).
- Students with disabilities share by year, Brookline and the state, 1994-2026 (school year = the spring it ends):
  Education-to-Career data hub, the same dataset as school_grade_enrollment.csv, queried 2026-10-27 with
  `$select=sy,org_name,total_cnt,swd_cnt,swd_pct` and `$where=(dist_code='00460000' AND org_type='District') OR org_name='State'`,
  https://educationtocareer.data.mass.gov/resource/t8td-gens.csv (not saved locally).

## PSB enrollment report, October 2026 (added 2026-10-26)

- `data/psb_enrollment/Oct 2026 PSB enrollment data.pdf` (Ben saved it; copy also at the project root):
  Public Schools of Brookline, "PSB Enrollment Report," School Committee, October 28, 2026, 18 slides.
  https://brooklinema.portal.civicclerk.com/event/16519/files/attachment/19828
  October 1, 2026 SIMS counts by school and grade (K-8 4,436; BHS 2,165; BEEP 232; total 6,833 excluding
  56 out-of-district and 15 under-3 students), class-size averages by school and grade, FY27 projection vs.
  actual, Cropper/NESDEC comparison, and the district's FY28 projection (6,737 including out-of-district
  and pre-K; K-8 4,338; BHS 2,102). The by-school totals on slide 4 for Driscoll, Hayes, Ridley and Runkle
  do not equal their grade cells (they sum to 4,536); the grade cells sum to the printed 4,436, so use
  the grade cells.

## Census blocks, 2010 and 2020 (added 2026-10-28)

Used by `scripts/block_children_per_home.py` (children 5-17 per home by kind of home).

- `data/demographics/blocks/brookline_blocks_{2010,2020}.csv`: Brookline's blocks (680 in 2010, 553 in 2020)
  pulled by `scripts/census_block_extract.py` from the statewide summary files, downloaded 2026-10-28 and
  deleted after extraction (Ben approved the downloads):
  - Census 2010 Summary File 1, Massachusetts, `ma2010.sf1.zip` (196 MB):
    https://www2.census.gov/census_2010/04-Summary_File_1/Massachusetts/ma2010.sf1.zip
    (P12 sex by age in segment 04; H3 occupancy and H4 tenure in segment 44)
  - Census 2020 Demographic and Housing Characteristics File, Massachusetts, `ma2020.dhc.zip` (201 MB):
    https://www2.census.gov/programs-surveys/decennial/2020/data/demographic-and-housing-characteristics-file/Massachusetts/ma2020.dhc.zip
    (P12 in segment 06; H1, H3 and H10 tenure in segment 01)
  Block totals match the town: 58,732 and 63,191 people; 26,448 and 27,961 housing units.
  The Census API (api.census.gov) now requires a key, which is why the full files were used.
- `data/demographics/blocks/brookline_blocks_{2010,2020}.geojson`: block outlines from the Census TIGERweb
  service, queried 2026-10-28 (Norfolk County tracts beginning 40, then trimmed to Brookline's blocks):
  https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/10/query
  and https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/18/query
  with `where=STATE='25' AND COUNTY='021' AND TRACT LIKE '40%'`, `outSR=4326`, `f=geojson`.

## Owners by age of householder, 2000, 2010 and 2020 (added 2026-10-28)

Used by `scripts/householder_age_turnover.py` (how many homes older owners leave each decade).

- `data/demographics/householder_age_tenure_2000_2020.csv`: Brookline town, owner and renter households by
  age of householder, extracted by the same script from the statewide files (downloaded 2026-10-28, Ben
  approved; deleted after extraction):
  - Census 2000 Summary File 1, Massachusetts, table H16, geography file and segment 37:
    https://www2.census.gov/census_2000/datasets/Summary_File_1/Massachusetts/mageo_uf1.zip and
    https://www2.census.gov/census_2000/datasets/Summary_File_1/Massachusetts/ma00037_uf1.zip
  - Census 2010 Summary File 1, table H17, segment 44 (the `ma2010.sf1.zip` above)
  - Census 2020 DHC, table H13, segment 02 (the `ma2020.dhc.zip` above)
  Occupied homes: 25,594 (2000), 25,092 (2010), 26,525 (2020).

## Census survey microdata, 2020-2024 (added 2026-10-28)

Used by `scripts/pums_children_per_home.py`. Downloaded 2026-10-28 (Ben asked for it); only PUMA 00902 kept.

- `data/demographics/pums/pums_2020_24_puma00902_{households,persons}.csv`: American Community Survey 2020-2024
  5-year public-use microdata, Massachusetts housing and person files, filtered to PUMA 00902 (Brookline,
  Dedham and Milton; all five years are coded to 2020 PUMAs), selected columns only.
  https://www2.census.gov/programs-surveys/acs/data/pums/2024/5-Year/csv_hma.zip (20 MB) and
  https://www2.census.gov/programs-surveys/acs/data/pums/2024/5-Year/csv_pma.zip (50 MB).
  `ACS2020_2024_PUMS_README.pdf` is from csv_hma.zip.
- PUMA membership: 2020 tract-to-PUMA file,
  https://www2.census.gov/geo/docs/maps-data/data/rel2020/2020_Census_Tract_to_2020_PUMA.txt
  (Brookline tracts 4001-4012 with Dedham 4021-4025 and Milton 4161-4164). The 2010 file,
  https://www2.census.gov/geo/docs/maps-data/data/rel/2010_Census_Tract_to_2010_PUMA.txt, put Brookline with
  Newton in PUMA 03400; not used.
- `data/demographics/acs5yr/brookline_bg_b25041_2024.txt`: ACS 2020-2024 5-year table-based summary file, table
  B25041 (bedrooms, all housing units), Brookline's 44 block groups (GEO_ID 1500000US2502140...), with margins
  of error. Downloaded 2026-10-28 (37 MB national file, deleted after filtering):
  https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b25041.dat

