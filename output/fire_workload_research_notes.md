# Brookline fire workload, structure, overtime and station costs: research notes

Prepared 2026-10-10. This file fills gaps left by `public_safety_workload_methodology.md`,
`public_safety_staffing_methodology.md` and `police_calls_research_notes.md`. It does not
change any existing CSV, script or page; the corrected and new values below are for whoever
next updates `public_safety_workload_fy03_25.csv`.

Each figure is tagged **[stated]** (the source says it) or **[inference]** (my arithmetic or
reading). Downloaded sources are in `data/fire_reports/`.

## Sources and how they were reached

- **FP YYYY** is the Town Financial Plan PDF already in `data/` (`FY20YY-Financial-Plan.pdf`).
  Page numbers are PDF page numbers (printed page labels in brackets where useful).
- **OpenGov FY21 / FY22 / FY24 / FY25.** The FY2021 and FY2022 budgets exist only as OpenGov
  "stories", where the workload tables are images. Archived copies of these images are in
  `data/fire_reports/opengov_images/`. They were downloaded from `stories.opengov.com/brooklinema/uploads/...`.
  The pages that embed them are:
  - FY22 Fire https://stories.opengov.com/brooklinema/published/yc9nyvr63
  - FY22 Police https://stories.opengov.com/brooklinema/published/tchZLggpu
  - FY21 Fire https://stories.opengov.com/brooklinema/published/jdUUm35Rc
  - FY24 Fire https://stories.opengov.com/brooklinema/published/AhrinmUlU0N
  - FY24 Police https://stories.opengov.com/brooklinema/published/Bt6-Dad5FJ
  - FY25 Fire https://stories.opengov.com/brooklinema/published/cvXzEp70lz2
  - FY25 Police https://stories.opengov.com/brooklinema/published/9uneWDZL8e

  The FY24 and FY25 PDF plans leave these tables out, which is why the earlier pass missed them.
- **Fire OT memo.** Charlie Young (Asst. Town Administrator for Finance) to Chas Carey (Town Administrator),
  "Updated FY24-25 Fire Department Overtime and Leave Memo", revised 2025-03-11.
  brooklinema.gov `DocumentCenter/View/57796`, retrieved via the Wayback Machine snapshot of 2026-03-18.
  Saved as `Brookline_FY25_Fire_Leave_OT_Memo_2025-03-11.pdf`.
- **AdvCom FY23 Fire CIP.** Advisory Committee Capital Subcommittee, "FY 23 Fire Department CIP
  Requests", 2022-03-29. `DocumentCenter/View/30296`, Wayback snapshot of 2022-12-21. Saved as
  `Brookline_Fire_Dept_FY23_CIP.pdf` (3 pages).
- **ZBA 2014.** Zoning Board of Appeals hearing transcript, 2014-12-01 (a large housing development), with
  testimony from Fire Chief Paul Ford. `DocumentCenter/View/6730`, Wayback snapshot of 2024-07-20.
  Saved as `Brookline_ZBA_2014-12-01_a large housing development_transcript.pdf`.
- **ATM May 2026.** Combined Reports for the May 26, 2026 Annual Town Meeting (`data/Combined-Reports-May-2026-ATM.pdf`).
- **Station pages.** Fire station pages on brooklinema.gov, Wayback snapshots from February to April 2026.
  Text is saved in `data/fire_reports/station_pages/`.
- **BPD MY 2026.** Brookline Police Mid-Year Report 2026, police.brooklinema.gov `DocumentCenter/View/2234`.
  Saved as `data/fire_reports/BPD_mid_year_2026.pdf`. It is new since the police notes were written.
- **Access.** brooklinema.gov returns HTTP 403 to curl and WebFetch, and the browser extension was not
  connected. Everything from that domain therefore came through Wayback snapshots, and anything not
  archived could not be retrieved.

## 1. Fire Department structure today

| Item | Value | Source |
|---|---|---|
| Stations | 5 | FP2027 p.211 [printed 199] [stated]; USFA registry (161 career, 5 stations) |
| Front-line companies | 7: "five engine companies and two ladder trucks" | FP2027 p.211 [stated] |
| Minimum per company | 4 firefighters ("minimum staffing of four firefighters") | FP2027 p.211 [stated] |
| Minimum on duty per day | 29 firefighters | Fire OT memo p.2 [stated] |
| Shift groups | 4 | Fire OT memo p.2, footnote 1 and p.6 [stated]; see note below |
| Budgeted FTE | 161 in FY2023-26; 160 in FY2027 (−1 in Prevention) | FP2027 p.218 [stated] |
| Ambulance | Contracted (Coastal Ambulance, earlier Fallon): 2 ALS 24/7 plus 1 BLS at peak hours | FP2027 p.211 [stated] |
| ISO rating | Class 1 | FP2027 p.213 [stated] |

FY2027 FTE by rank (FP2027 p.218):

| Rank | FTE |
|---|---:|
| Chief | 1 |
| Chief of Operations | 1 |
| Deputy Chief | 6 |
| Captain | 9 |
| Lieutenant | 23 |
| Firefighter | 113 |
| Civilian/other | 7 |

**Minimum staffing and groups.** The memo states "The Fire Department staffs at a minimum of 29
firefighters per day." Footnote 1 bases this on "the Town's number of firefighter groups", each
staffed at four per apparatus.

- 7 companies × 4 = 28, plus 1 on-duty deputy chief = 29. **[inference]** The memo does not give
  this breakdown.
- **Four groups [stated by implication]:** p.6 describes "four firefighters, or one per group".
  Also p.6: an added firefighter "would work two shifts per week with three days off in between".
- The shift length (24-hour tours) is not stated in any source I retrieved. **[unverified]**

**Stations and apparatus.** From the station pages (Wayback, 2026). The page apparatus lists may lag
actual assignments, and they still name Fallon rather than Coastal ambulances.

| Station | Address | Apparatus listed |
|---|---|---|
| 1 (Brookline Village) | 140 Washington St | E1 Engine; L2 Ladder; Heavy Rescue 1; C2 Deputy Chief car; service and maintenance trucks |
| 4 (Route 9 at Reservoir Rd) | 827 Boylston St | E4 "Quint" engine/ladder; Squad 1; decon trailer; ice/water rescue; ALS ambulance; reserve E-11 |
| 5 (Coolidge Corner) | 49 Babcock St | Q5 "Quint" engine/ladder; T1 Ladder "Tower"; reserve RE5 |
| 6 (Hammond St, south) | 962 Hammond St | E6 Engine; training division cars (training facility on site) |
| 7 (Washington Square) | 665 Washington St | E3 Engine; ALS ambulance |

- Fire headquarters is in the Public Safety Building, 350 Washington St.
- Front-line count: 5 engines (E1, E3, E4, Q5, E6) and 2 ladders (L2, T1) = 7. This matches the Financial Plan. **[inference]**
- Reserves (AdvCom FY23 Fire CIP p.1) [stated]:
  - The department "keeps an average of three engines in reserve, housing them at Stations 4, 5, and 6. Currently there are four."
  - Replacement policy: engines every 17 years, ladders every 20.
- Per-station staffing (AdvCom FY23 Fire CIP p.2) [stated]: "between 4-5 personnel and 9-11 personnel (with or without 2-3 paramedics)".

**The "flexible staffing model"** (FP2027 pp.34-35, Override section) [stated]:

- **The proposal.** The Town would keep its full complement of firefighters per shift, but would let
  "some or all apparatuses to operate with three firefighters instead of the current recommended minimum of four".
- **Why.** The plan's case:
  - It says most Metro Boston communities except Boston allow three-person staffing, including Cambridge and Somerville.
  - It estimated that flexible staffing "would have effectively" eliminated the overtime deficit.
- **The dispute.** The union filed an unfair labor practice charge. The Town then withdrew the model
  "under intense pressure from the public" and returned to four per apparatus.
- **FY26 outlook.** FY26 overtime is projected to exceed budget by $800,000. That amount went into the
  FY27 override ($1.71M fire item: $800K overtime plus $910K contract "tail" from FY28).
- **If FY28 costs go unfunded.** The plan warns of having to "close a company or station, removing one
  engine company from regular service, and/or laying off up to 20 firefighters."

**The model's numbers** (Fire OT memo p.2) [stated]:

- It would lower the daily minimum from 29 to 22 "in line with other similar surrounding communities".
- FY24 overtime shifts: 1,358 under current minimums against 35 at the lower level.
- Estimated savings: $1,627,078 a year, about 78% of overtime.
- Press reports gave the floor as 23 and savings as at least $1.5M (Patch, NBC Boston). These are secondary
  sources and are not used here; the memo's 22 is the primary figure.

**Advisory Committee position** (ATM May 2026 report p.71) [stated]:

- The Town Administrator "has no immediate intention to pursue it".
- AdvCom disputes that it supported the withdrawal ("decidedly not the case").
- Article 5 added $860,000 to the FY2026 Fire budget for overtime.
- The FY2027 Fire budget is $21,063,066, including $800,000 from the override.

**Cost of one more company** (Fire OT memo p.7, "Future Considerations – South Brookline Ladder Truck") [stated]:

- A ladder company in South Brookline would need 20 firefighters, costing $2,472,780. That is
  $123,639 each, including health insurance but excluding pension.
- Plus $565,512 of overtime at current leave rates, for a total of $3,038,292 a year.
- A new ladder truck "will cost between $1.5 million to $2 million fully equipped."
- AdvCom FY23 Fire CIP p.3 also says "An additional company ... translates into hiring 20 additional firefighters."
- The Chief would put a South Brookline ladder at Station 4. Station 4 is being rebuilt as a two-company station. [stated]

## 2. Workload by station or unit, and response times

**No per-station or per-company run counts were found in any public source.** The Financial
Plans report department totals only. The station-renovation documents and the 2014 ZBA
transcript speak qualitatively:

- Chief Ford (ZBA 2014 p.34) [stated]: comparing South Brookline's runs "versus Engine 1 in the
  Village or Engine 5 in Coolidge Corner, you'd see a vast difference".
- AdvCom FY23 Fire CIP p.3 cites a **2019 IAFF analysis**. It found that a ladder at Station 4 would
  improve "6-minute ladder response capabilities in South Brookline". The analysis itself was not found online. **[not retrieved]**

Response-time statements [stated]:

| Source | Statement |
|---|---|
| FP2027 p.213; FP2023 p.171; OpenGov FY22 Fire | "Responded to over 95% of calls in fewer than 4 minutes, exceeding NFPA 1710" (FY21, FY22, FY26 accomplishments) and 100% of structure fires with a full first-alarm assignment |
| Workload tables, every year FY2018-2027 | Average response time to emergency incidents "<4:00" (calendar year); FY2026-27 estimates "<4.50" |
| ZBA 2014 pp.6-7 (Chief Ford) | Town-wide, the first engine arrives within 4 minutes 95% of the time; full first alarm within 8 minutes "over 90 percent" |

ZBA 2014 detail for a large housing development (south) [stated]:

- Engine 6 would meet 4 minutes.
- The second engine would arrive in about 6-7 minutes.
- The third engine and first truck would arrive in more than 8 minutes.

**Still missing.** Response-time distributions (90th percentile by station), unit-hour utilization, and
runs per company. These exist only in the department's CAD/RMS. MFIRS (MA DFS) incident files are not
published by community in a downloadable form I could find. The most direct route is a records request
to BFD for incident counts by responding unit for 2015-2025 and the 2019 IAFF analysis.

## 3. Gaps in `public_safety_workload_fy03_25.csv`

### Fire, fiscal-year totals (Fire "Performance / Workload Indicators")

| FY | Box | Still | Medical | Total responses | Source | CSV now |
|---|---:|---:|---:|---:|---|---|
| 2018 | 707 | 4,492 | 4,530 | 8,298 | OpenGov FY21 Fire PI1 | 8,298 (agrees) |
| **2019** | 594 | 3,860 | 3,954 | **8,523** | OpenGov FY21 PI1 and FY22 Fire PI p.1 | blank |
| **2020** | 514 | 3,503 | 3,859 | **7,980** | OpenGov FY22 Fire PI p.1 | blank ("not reported") |
| 2021 | 388 | 3,602 | 3,797 | **7,862** | OpenGov FY24 Fire PI p.1 | 7,787 (sum of components) |
| 2022 | 319 | 4,481 | 4,227 | **9,089** | OpenGov FY24 Fire PI p.1 | 9,027 (sum of components) |
| 2023 | 234 | 4,493 | 4,579 | 9,358 | OpenGov FY25 Fire PI p.1; FP2027 | 9,358 (agrees) |

All [stated]. Notes:

- FY2021 and FY2022 now have reported totals. Both are 1% above the component sums, which matches the
  97-99% pattern already noted.
- **Data-quality flag.** The FY25 OpenGov table shows FY2022 total = 7,862, which is identical to the
  FY2021 total and inconsistent with its own FY2022 components (319 + 4,481 + 4,227 = 9,027).
  Treat 9,089 (FY24 table) as the FY2022 figure. **[inference]**
- FY2020 (7,980) is the pandemic low. FY2019 (8,523) is the pre-COVID peak.
- Implication [inference]: the FY2018-25 growth is 8,298 → 10,491, about 3.4% a year, unchanged. The
  path is 8,298, 8,523, 7,980, 7,862, 9,089, 9,358, 9,976, 10,491. The dip-and-rebound is COVID.
  Growth from FY2019 (pre-COVID) to FY2025 is about 3.5% a year.

The police Dispatch rows carry a different "Fire-related Calls" series, so the two should not be mixed:

| FY | Fire-related calls | Source |
|---|---:|---|
| 2018 | 8,298 | OpenGov FY22 Police PI p.1 |
| 2019 | 8,523 | same |
| 2020 | 5,926 | same |
| 2021 | 7,862 | OpenGov FY24/FY25 Police PI p.2 |
| 2022 | 10,944 | same |
| 2023 | 12,000 (round, labelled "Actual") | OpenGov FY25 Police PI p.2 |

For FY2018-19 these equal the Fire Department totals. After that they diverge, so this is not the same
measure. **[inference]**

### Police, fiscal-year "Police-related Calls" (Financial Plan Dispatch rows)

| FY | Police-related | Self-initiated | E-911 | Source | Status |
|---|---:|---:|---:|---|---|
| **2019** | **68,505** | 26,657 | 17,571 | OpenGov FY22 Police PI p.1; repeated in FY24 and FY25 PI p.2 | [stated] |
| 2020 | 59,611 | 30,622 | 18,552 | same | [stated]; matches CSV |
| 2021 | 52,978 | 23,541 | 15,172 | OpenGov FY24 PI p.2 | [stated]; matches CSV |
| **2022** | **56,167** | 22,524 | 19,391 | OpenGov FY24 and FY25 PI p.2 (FY25 column header "COMPLETE July 1, 2021 - June 30, 2022 ACTUAL") | [stated] |
| **2023** | **50,000** (round) | 26,000 (round) | 19,491 | OpenGov FY25 PI p.2, header "COMPLETE ... ACTUAL"; also FP2026 | [stated] but suspect |

Flags:

- **FY2019 self-initiated = 26,657 is identical to FY2018.** It is probably a carried-over value. **[inference]**
- **The FY2019 figure does not match a calendar-year re-cut.**
  - Using the police notes' method: (CY2018 68,141 − H1 2018 30,672) + H1 2019 35,428 = 72,897, about 4,400 above the reported 68,505. **[inference]**
  - So the FP series may not be a clean CAD re-cut in FY2019, unlike FY2020 (exact match).
  - Note also that 68,505 is close to CY2018's 68,141.
- **FY2023 alternative estimate [inference, unverified]:**
  - Assume the FY2022 figure (56,167) is an exact re-cut, as FY2020 was.
  - Then H1 2022 = 56,167 − (55,269 − 25,988) = 26,886.
  - FY2023 = (CY2022 52,242 − 26,886) + H1 2023 19,981 = **45,337**.
  - The 2022 mid-year report is not posted (the BPD index skips from 2021 to 2023), so H1 2022 cannot be checked.
  - The FY2019 mismatch above shows the re-cut assumption can fail. Treat 45,337 as a rough cross-check on the round 50,000, not a replacement.
- **Calendar vs fiscal.** The BPD year-end CAD counts in `data/police_reports/` are **calendar years**:
  2019 67,849; 2022 52,242; 2023 51,761. They are already tabulated in `police_calls_research_notes.md`.
  The Financial Plan rows above are **fiscal years** (July-June).
- **New: H1 2026** (BPD MY 2026 p.22) [stated]: "there were 23,036 calls for service entered into the
  ... computer-aided dispatch system. Of these, 23,036 were police related calls for service, and 5,670
  were fire and emergency medical service (EMS) related".
  - The report is internally inconsistent: police plus fire cannot both equal the total.
  - If 23,036 is the all-call total, police-related = 17,366. Then FY2026 ≈ H2 2025 20,591 + 17,366 = **37,957**.
  - If 23,036 is police-only, FY2026 ≈ **43,627**.
  - Either way, FY2026 will be far below FY2025 (55,619). **[inference]**
  - The same report says BPD is 18 officers below authorized strength (p.23).

## 4. Fire overtime: budget vs actual

Fire Department overtime account (510300), all divisions unless noted:

| FY | Budget | Actual | Over budget | Reserve Fund transfer | Source |
|---|---:|---:|---:|---:|---|
| 2017 | 288,503 | n/a | | | FP2018 p.158 (510300 line item, FY2017 budget column) [stated, budget only] |
| 2018 | 587,222 | n/a | | | FP2018 p.158 (FY2018 request column) [stated, budget only] |
| 2019 | 610,946 | n/a | | | FP2020 p.163 (510300, FY2019 budget column) [stated, budget only] |
| 2020 | 610,946 | 719,011 | ~108K | | FP2020 p.163 (budget); OpenGov FY22 Fire line items (actual) |
| 2021 | 723,476 | 1,375,259 | 651,783 | none listed (FY21 STM raised OT budget) | Fire OT memo p.1 Fig.1; FP2023 p.171 |
| 2022 | 725,477 | 2,780,993 | 2,055,516 | 1,490,357 | Fire OT memo Fig.1; FP2024 p.198 |
| 2023 | 725,477 | 1,896,059 | 1,170,582 | 816,000 | Fire OT memo Fig.1; FP2025 p.207 |
| 2024 | 792,747 | 2,073,965 | 1,281,218 | 934,159 | Fire OT memo Fig.1; FP2026 p.186 |
| 2025 | 1,092,747 | 1,962,175 (FP2027, sum of divisions; Firefighting alone 1,902,096) | ~870K | 746,197 (projected) | FP2027 pp.214-217; memo projected 2,061,819 |
| 2026 | 1,092,747 (FP2026) / 1,136,457 (FP2027 restated, sum of divisions) | projected ~$800K over | | ATM Art. 5 added $860,000 | FP2027 p.35; ATM May 2026 p.71 |
| 2027 | 1,136,457 plus $800,000 override | | | | FP2027 pp.214-217; ATM p.71 |

Notes:

- **FY2018-19 actuals were not found.** FP2027 p.34 says the shortfall "first began when contractual
  obligations around vacation and personal leave use changed in FY18". The pre-FY2021 plans in hand show
  only budgets for 510300.
- **FY2020.** The OpenGov FY22 line item shows FY20 actual 719,011 against an FY21 budget of 723,477, so the
  deficit before FY2021 looks small. Check this against FY2019-20 Reserve Fund transfers before relying on it. **[inference]**
- **Leave drivers** (memo pp.2-3) [stated]:
  - Total leave tours: 2,454 (FY18) → 3,590 (FY25 projected), up 40%.
  - Injured leave: 371 → 977, up 150%.
  - Sick leave: 502 → 871, up 62%.
  - Per firefighter: 16.25 → 23.62 tours.
- **Contract terms** (memo p.3) [stated]:
  - The contract requires granting at least five vacation/admin leave tours a day.
  - In FY24, 82% of leave (2,133 tours) was "other obligated leave".
- **Firefighter cost and break-even** (memo p.6) [stated]:
  - Marginal cost of one firefighter: $123,639 a year, including $23,715 health insurance and excluding pension.
  - The memo argues adding firefighters costs more than the overtime it saves:
    four firefighters (one per group) cost $494,956 and would save at most $406,555.

## 5. New fire station costs and apparatus

**Brookline's own project** [stated unless marked]:

- **Debt exclusion vote.** November 2022 ballot Question 5, to renovate all stations and reconstruct
  Station 5 at 49 Babcock St. Passed 13,794 to 5,830 (MA Election Statistics,
  https://electionstats.state.ma.us/ballot_questions/view/7414/).
- **2022 estimate.** AdvCom FY23 Fire CIP p.2: "currently estimated to cost $60,000,000", including
  about 17.5% soft costs and about $10M for "Net Zero Ready" features.
  - Station 5 (built 1965) was judged unsuitable for renovation: more than $3M would not reach parity.
  - The project will run 5-7 years, with stations vacated in turn.
- **Current budget.** FP2027 CIP (p.403) lists "Fire Station Renovations 65,000,000" among
  authorized/debt-excluded projects.
  - ATM May 2026 p.28, capital status as of 2026-03-16: revised budget $64,680,182; expended $4,841,868;
    encumbered $9,550,528; available $50,287,786.
- **Progress.** ATM May 2026 p.71: Station 4 renovation expected to come in $500,000 under budget, and
  Station 1 "over $3,000,000 under estimates".
- **Sequence** (FP2027 p.212):
  - FY26: Station 4 under way; Station 1 plans final; Station 5 feasibility study commissioned.
  - FY27: finish Station 1 and begin construction of the new Station 5.
- **No standalone cost** for the new Station 5 was found. **[missing]**

**Brookline apparatus in the FY2027-32 CIP** (FP2027 pp.399, 407) [stated]:

| Item | Amount |
|---|---|
| Engine 3 replacement | $1,500,000 (General Fund bond, FY2032) |
| Engines 5 and 6 replacement | $3,000,000 (future years) |
| "(3) replacement Engines 3,5,6" | "@ $1.5 million each for electric vehicles" |
| Fire apparatus rehab, FY26-FY30 | Engine 5 $375K; Rescue 1 $125K; Ladder 2 $500K; Engine 6 $350K; Ladder 3 $500K; Ladder 1 $550K |
| SCBA replacement | $1,250,000 |

Earlier engine replacements for comparison:

- Engine 1: $725,000 estimate (AdvCom FY23 CIP, 2022); now $700,000 bond (FP2027 p.403).
- Ladder truck: "$1.5 million to $2 million fully equipped" (Fire OT memo p.7).

**Other Massachusetts towns.** A delegated research pass collected these figures. I re-checked the
Bedford, Chelmsford, Carlisle, Plymouth and Citygate figures against the saved PDFs; I did not re-open the rest.
Saved PDFs are in `data/fire_reports/`. A few town sites returned 403, so some figures rest on weaker evidence;
each row says how its cost was sourced.

| Town / station | Vote or completion | Cost (type) | Bays / sq ft | Source | Verification |
|---|---|---|---|---|---|
| Bedford Fire HQ, 139 The Great Road | STM 6/11/2024; completion 12/2026 | $32,293,976, current total project budget ($22.8M construction contract) | bays n/a / 23,141 sf | OPM (PMA) report Aug-Sep 2026, bedfordma.gov DocumentCenter/View/7144, PDF p.5 (budget), p.3 (size) | primary, re-checked |
| Chelmsford Stations 3 (rebuild) + 5 (new, 295 Acton Rd) | Fall TM Oct 2024 Art. 16; debt exclusion passed 11/5/2024 | $25M for both; Station 5 alone $12.38M (modular) to $13.92M (stick-built), consultant estimates escalated to 2026 | n/a | chelmsfordma.gov DocumentCenter/View/18694, p.5 ($25M) and p.22 (Station 5); electionstats view/11637 | primary, re-checked |
| Northborough new station, 61-65 West Main St | STM 10/7/2024 Art. 2; debt exclusion passed 11/5/2024 | $41,364,992, appropriation not to exceed | n/a | electionstats view/11647 (vote) | vote primary; **dollar figure only from a search excerpt of town minutes (site 403)** |
| Westwood Fire Station 1 (rebuild) | ATM 5/19/2025 Art. 14; debt exclusion **failed** 6/3/2025 and 9/9/2025 | $38.1M requested (bid-backed); $39.5M estimate 9/2024 | n/a | town project page | **search excerpt only (site 403)** |
| Natick West Natick Station 4 | Fall 2018 TM Art. 15; debt exclusion passed 11/6/2018 | $15.56M appropriation; $12.344M construction award (3/2019) | ~17,000 sf per Patch (secondary) | natickma.gov bids.aspx?bidID=365; electionstats view/7329 | primary |
| Medford Fire HQ | debt exclusion **failed** 11/5/2024 | ~$30M | n/a | electionstats view/11660 (vote) | **cost from student press only; unverified** |
| Needham Public Safety Bldg + Station 2 | debt exclusion passed 11/6/2018 | $69,995,000 for police + fire HQ + Station 2 combined; not separable | Station 2 23,203 sf (search excerpt) | electionstats view/7330 | **combined cost from a secondary summary** |
| Lexington Fire HQ, 45 Bedford St | debt exclusion 12/4/2017; completed ~2020 | ~$15.2M | 26,000 sf (architect); bays conflict (6 vs 10) | Firehouse magazine (secondary) | **unverified; town Laserfiche blocked** |

[inference] Recent (2024-26 dollars) full-size metro-area headquarters stations run about $32-41M total
project cost. Bedford is about $1,395 per sq ft. A smaller single-company substation runs about
$12-14M (Chelmsford Station 5 estimate). 2018-era projects cost roughly half that. Two of five
recent debt-exclusion votes failed (Medford, Westwood). For comparison, Brookline's $60-65M covers four
renovations plus one new station.

**Apparatus (primary town documents):**

| Item | Town / date | Cost | Source |
|---|---|---|---|
| Engine | Carlisle, 5/18/2025 ATM Art. 3 | "over $1.2 million" (up from $975K borrowed in 2024); about 3-year delivery | carlislema.gov DocumentCenter/View/7182 p.3 (re-checked) |
| Engine | Stow, FY26 capital request (minutes 3/6/2025) | $1.1M rough estimate | stow-ma.gov minutes |
| 105-ft aerial (Ladder 3) | Framingham, FY2026 capital request | $1,949,976 | framinghamma.gov DocumentCenter/View/53084 pp.1, 3, 7 |
| 100-ft tower ladder | Plymouth, FY26 TM request 10/9/2024 | $2,283,467; lead time "approaching 48 months" | plymouth-ma.gov DocumentCenter/View/7185 p.1 (re-checked) |
| 75-ft quint | Plymouth, FY23 Fall TM, 8/2022 | $1,496,853 | plymouth-ma.gov DocumentCenter/View/2242 |

[inference] Engines cost about $1.1-1.5M (Brookline's own CIP uses $1.5M for an electric engine) and
aerials about $1.5-2.3M, consistent with the Brookline memo's "$1.5 million to $2 million"; lead times are 3-4 years.

## 6. Workload thresholds for adding a company

**No formal standard sets a workload trigger for adding a company.**

- **NFPA 1710 (2020 ed.)** sets response-time objectives, not workload. Its targets [as summarized by
  secondary sources; standard text not read]:
  - 240 s travel time for the first engine.
  - 360 s travel time for the second company.
  - Full first alarm within 480 s (8 minutes, as Chief Ford described it at ZBA 2014 p.7).
  - All measured at 90% of incidents.
  - NFPA has since consolidated 1710/1720/1730 into NFPA 1750 (2026 ed.); check the current edition before citing 1710.
- **ISO Fire Suppression Rating Schedule** (isomitigation.com, "criteria for deployment analysis of companies"):
  - Full credit for a first-due engine within 1.5 road miles and a ladder/service company within 2.5 road miles.
  - A ladder is needed where there are 5 or more buildings of 3+ stories or 35+ ft. This threshold is quoted via a *Fire Engineering* column, not read in ISO's own text.
  - These are distance and risk triggers. Brookline holds ISO Class 1.

**Consultant and practitioner rules of thumb** (unit-hour utilization, UHU, is the share of on-duty time a unit is committed):

| Threshold | Source | Notes |
|---|---|---|
| UHU should not exceed 30% across the workday for a 24-hour crew; 40-50% for dedicated short-shift units | Citygate Associates, *LAFD Standards of Cover Analysis, Vol. 1 Technical Report*, June 2023, Sec. 5, p.92 (PDF p.104) | re-checked; saved |
| Commitment factor 0.16-0.24 "ideal", 0.25 "system stress", 0.30 "not sustainable" | J. Powers, "How Busy Is Busy?", *Fire Engineering*, 1 May 2016 | trade article |
| ~13% UHU = overtasked; above 10% a unit can't meet its 90th-percentile target (citing Scottsdale FD 2015) | D. Munsey, USFA Executive Fire Officer paper, 2018 (apps.usfa.fema.gov/pdf/efop/efo247258.pdf), p.3, p.21 | saved |
| 3,000-3,200 responses a year = "busy" (TriData, Portland, 2006); 15 calls per shift (~5,475 a year) triggers resources (ICMA, Las Vegas, 2012); a single-unit station with 3,500 calls can't meet 90% (Riverside FD SOC, 2017) | cited in Munsey 2018, pp.15, 21 | **secondary citations; underlying reports not read** |
| A Massachusetts engine running 3,058-3,267 responses a year had only ~7% UHU (~12 min a run) | Manitou Inc., *Rockland (MA) Fire Department Response Time Study*, Oct 2021, §4.4, pp.48-49 | saved |
| IAFF/IAFC 25-30% UHU planning threshold | Charlotte County, FL planning document | **unverified against IAFF/IAFC primary text** |

**Brookline comparison [inference only; no per-unit data exists to test it]:**

- FY2025's 10,491 department responses spread over 7 companies average about 1,500 runs per company.
- That assumes one unit per incident, so it understates runs: box alarms send several companies, and medical calls send one.
- Even so, the average is about half the 3,000-run "busy" marker.
- At Rockland's ~12 minutes a run, ~1,500 runs is roughly 3-4% UHU, far below the 25-30% thresholds.
- Busy companies (Engine 1, Engine 5, per Chief Ford's 2014 testimony) will run well above the average, and medical growth concentrates there.
- Testing this properly needs unit-level CAD data from BFD.
- On this evidence, Brookline's company count is set by coverage and response-time geography (NFPA/ISO), not by workload saturation. The South Brookline ladder question is a coverage question.

## What is still missing

1. Runs by station or company, unit-hour utilization, and 90th-percentile response times by station.
   No public source has them; a BFD records request is needed. The 2019 IAFF South Brookline analysis was also not retrieved.
2. Fire overtime actuals for FY2018-2019, and Reserve Fund transfers before FY2022.
3. Shift length and the exact on-duty composition of the 29 (my 28 + 1 deputy is an inference).
4. FY2023 police-related calls: the official "actual" is a round 50,000. BPD's 2022 mid-year report is not posted.
5. A cost estimate for the new Station 5 alone.
