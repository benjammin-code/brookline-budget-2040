# Why did Brookline "police-related calls" fall? Research notes

Prepared 2026-09-29. Question: why did the Financial Plan workload row "Police-related Calls" fall from about 75,600 (FY2013) and 67,000 to 73,000 (FY2016-18) to about 53,000 (FY2021) and 52,529 / 55,619 (FY2024 / FY2025)?

## Sources used

- **FP YYYY** is the Town Financial Plan text at `scratchpad/fp/fpYYYY.txt`. Page labels are the printed footers, such as "IV-48" or "Section 4I Police 66". The FY2023 plan text is OCR and noisy.
- **AR YYYY** is the Brookline Police Year-End Report for calendar year YYYY. **MY YYYY** is the Mid-Year Report covering January to June. All are downloaded to `data/police_reports/` (`BPD_year_end_YYYY.pdf/.txt` and `BPD_mid_year_YYYY.pdf/.txt`) from the index at https://police.brooklinema.gov/147/Annual-Reports (DocumentCenter IDs 323, 324, 541, 816, 989, 1083, 1148, 1363, 1431, 1521, 1581, 1695, 2166). Page numbers are PDF page numbers.
- Other sources:
  - Advisory Committee Public Safety Subcommittee, FY23 Police Budget report, 2022-03-09 (`AdvCom_PublicSafety_FY23_Police_Budget.pdf`).
  - Select Board Committee on Policing Reforms Final Report, 2021 (`Policing_Reforms_Committee_Final.pdf`).
  - Task Force to Reimagine Policing Final Report, 2021 (`TaskForce_Reimagine_Policing_Final.pdf`).
  - PERF Police Chief position profile, 2018 (`PERF_Brookline_chief_profile.pdf`).
- Units: the Financial Plan uses **fiscal years** (July to June). The police reports use **calendar years**.

## Headline finding

The Financial Plan series combines two different measures, and I have not found an official statement explaining either break.

1. **Through about FY2015, the Financial Plan (FP) row tracked the Dispatch Center's count of police calls *received*.** That count was about 75K. In the same years, the Chief's annual-report count of police **CAD entries** was about 95K to 100K. For example:
   - The FY2013 FP figure is 75,596.
   - The 2013 Dispatch "Police Calls" figure is 74,529 (AR 2013 p.66).
   - The Chief's 2013 CAD figure is 100,431 (AR 2013 p.16).
2. **From FY2017 or FY2018 onward, the FP row matches the annual reports' police CAD-entry count, re-cut to fiscal years.** I reconstructed each fiscal year from the second half of one calendar year plus the first half of the next, using AR and MY figures:

   | FY | Reconstruction from AR / MY | FP figure |
   |---|---|---|
   | FY2020 | (67,849 − 35,428) + 27,190 = **59,611** | **59,611** (exact) |
   | FY2021 | 27,052 + 25,988 = 53,040 | 52,978 |
   | FY2018 | 36,558 + 30,672 = 67,230 | 67,117 |
   | FY2024 | 31,780 + 21,665 = 53,445 | 52,529 |
   | FY2025 | 31,772 + 23,501 = 55,273 | 55,619 |

   This is my own reconstruction. No source states it.
3. **The police CAD count itself fell 26% from CY2015 to CY2016**, from 93,553 to 69,215 (AR 2016 p.18). The first half of 2016 was already down 29.9% (MY 2016 p.15). No report explains the drop. The report text describing what is counted is unchanged boilerplate. The same 2016 report also carries two other figures: "Police Calls 74,149" and "CAD Entries 83,970" (AR 2016 p.63).
4. **After the definitions line up, there is a real step down around 2020.** Police CAD entries were 71,044 in 2017, 68,141 in 2018 and 67,849 in 2019. They fell to 54,242 in 2020 and stayed between 51.8K and 55.3K through 2024. In CY2025 they fell to 44,092. That 2025 drop is concentrated in the second half of the year: 20,591 entries, against 31,772 in the second half of 2024. It is unexplained and will depress FY2026.

## (a) Year-by-year counts

### Police CAD entries / calls for service (police reports, calendar year)

| CY | Police CAD entries (Chief's count) | Source | Dispatch "Police Calls" / other | Source |
|---|---|---|---|---|
| 2012 | 99,069 | AR 2013 p.16 | | |
| 2013 | 100,431 | AR 2013 p.16 | 74,529 "Police Calls ... received" | AR 2013 p.66 |
| 2014 | 95,891 | AR 2014 p.13 | 101,594 "Police Computer Aided Dispatch Entries" | AR 2014 p.55 |
| 2015 | 93,553 | AR 2015 p.16 | "CAD Entries: 99,522 / Police Calls: 93,553" | AR 2015 p.48 |
| 2016 | 69,215 ("down 26%") | AR 2016 p.18 | "CAD Entries 83,970 / Police Calls 74,149" | AR 2016 p.63 |
| 2017 | 71,044 | AR 2017 p.16 | "CAD Entries: 79,244 / Police Calls: 71,044" | AR 2017 p.62 |
| 2018 | 68,141, plus 8,354 fire/EMS assists | AR 2018 p.17 | 76,495 total police and fire CAD | AR 2018 p.37 |
| 2019 | 67,849 | AR 2019 p.39 (Dispatch section) | 78,288 total incl. 10,439 fire | AR 2020 p.22 table |
| 2020 | 54,242 | AR 2020 p.22 | 63,806 total | AR 2020 p.22 |
| 2021 | 55,269 | AR 2021 p.20 | 66,233 total | AR 2021 p.20 |
| 2022 | 52,242 | AR 2022 p.19 | 63,186 total | AR 2022 p.19 |
| 2023 | 51,761 | AR 2023 p.23 | 61,640 total | AR 2023 p.23 |
| 2024 | 53,437 | AR 2024 p.24 | 63,505 total | AR 2024 p.24 |
| 2025 | 44,092 | AR 2025 p.25 | 54,660 total | AR 2025 p.25 |

Caveats:

- The "Calls for Service" column in the AR comparison tables (AR 2020 to AR 2025) mixes definitions. It shows police-only figures for 2016-2018 (69,215 / 71,044 / 68,141) and police plus fire/EMS totals from 2019 (78,288 onward).
- AR 2020 p.22 lists 54,242 police, 9,564 fire and 4,095 EMS. Those sum to 67,901, not the stated 63,806. The 4,095 EMS calls appear to be a subset of fire.

Mid-year (January to June) police CAD entries:

| Half-year | Entries | Source |
|---|---|---|
| H1 2013 | 51,099 | MY 2014 p.18 |
| H1 2014 | 51,379 | MY 2014 p.18 |
| H1 2015 | 51,166 | MY 2015 p.15 |
| H1 2016 | 35,824 | MY 2016 p.15 |
| H1 2017 | 34,486 | MY 2017 p.18 |
| H1 2018 | 30,672 | MY 2018 p.14 |
| H1 2019 | 35,428 | MY 2019 p.17 |
| H1 2020 | 27,190 | MY 2020 p.17 |
| H1 2021 | 25,988 | MY 2021 p.17 |
| H1 2023 | 19,981 | MY 2023 p.21 |
| H1 2024 | 21,665 | MY 2024 p.23 |
| H1 2025 | 23,501 | MY 2025 p.24 |

Before 2023 the halves split roughly evenly. For 2023 and 2024, the implied second half (about 31.8K) is much larger than the first half (20K to 22K). This could be a data-entry or reporting lag, but no source says so.

### Financial Plan workload rows (fiscal year, "Actual" columns only)

| FY | Police-related | Self-initiated | Moving violations | Arrests | Source |
|---|---|---|---|---|---|
| FY2003 | 56,957 | | | | FP2006 IV-49 |
| FY2004 | 62,684 | | 21,439 | | FP2006 IV-49 |
| FY2005 | 63,481 | | 19,623 | 755 | FP2008 IV-48 |
| FY2006 | 66,445 | | 18,863 | 931 | FP2008 IV-48 |
| FY2007 | 71,721 | | 16,672 | 846 | FP2010 IV-48 |
| FY2008 | 65,671 | | 16,217 | 637 | FP2010 IV-48 |
| FY2009 | 66,817 | | 14,854 | 611 | FP2012 IV-48 |
| FY2010 | 64,772 | | 19,971 | 189 (as printed; likely an error) | FP2012 IV-48 |
| FY2011 | 68,937 | | 25,413 | 858 | FP2014 IV-46 |
| FY2012 | 69,318 | | 25,503 | 949 | FP2014 / FP2015 IV-46 |
| FY2013 | 75,596 | | 25,876 | 934 | FP2015 IV-46 |
| FY2014 | 75,525 | 20,907 (first year, "NEW") | 22,418 | 837 | FP2016 IV-48 |
| FY2015 | 75,525 (identical to FY2014; likely a carried-over value) | 25,204 | 20,851 | 714 | FP2017 IV-48 |
| FY2016 | 72,708 | 25,463 | 18,847 | 561 | FP2018 IV-48 |
| FY2017 | 72,012 | 25,319 | 15,051 | 399 | FP2019 IV-47 |
| FY2018 | 67,117 | 26,657 | 11,063 | 294 | FP2020 IV-49 |
| FY2019 | not available (FP2021 and FP2022 not in hand) | | | | |
| FY2020 | 59,611 | 30,622 | about 8,051 (OCR ambiguous) | n/a | FP2023 Sec 4I p.66 |
| FY2021 | 52,978 | 23,541 | 2,945 | n/a | FP2023 Sec 4I p.66 |
| FY2022 | not available | | | | |
| FY2023 | 50,000 (round number in an "Actual" column; treat as suspect) | 26,000 (also round) | 2,522 | 185 | FP2026 Sec 4I p.175 |
| FY2024 | 52,529 | 19,871 | 4,421 | 232 | FP2026 p.175; FP2027 Police p.198 |
| FY2025 | 55,619 | 26,197 | 6,101 | n/a | FP2027 Police p.198 |

Note on the FY2023 figures: the FP2026 table header reads "ACTUAL FY2023", but 50,000 and 26,000 look like estimates.

### Police reports: enforcement and other indicators (calendar year)

| CY | Moving violations | Arrests | Part A crimes | 911 calls (inbound) | Case numbers assigned | Source |
|---|---|---|---|---|---|---|
| 2012 | 22,119 | 916 | | | | AR 2013 / AR 2014 |
| 2013 | 24,799 | 888 | | 12,951 | | AR 2013 p.66; AR 2014 p.13 |
| 2014 | 21,714 | 756 | | 14,107 | 6,487 | AR 2014 p.13, p.55 |
| 2015 | 19,481 | 635 | 926 | 12,183 | 6,703 | AR 2015 p.16, p.48-49 |
| 2016 | 16,298 | 448 | 686 / 700* | 12,001 | 6,030 | AR 2016 p.18, p.63-64 |
| 2017 | 14,938 | 360 | 739 | 12,336 | 6,018 | AR 2017 p.16, p.61-62 |
| 2018 | 9,271 | 290 | 721 | 15,047 (in plus out) | | AR 2018 p.17, p.37 |
| 2019 | 13,745 | 343 | 608 | 18,198 | 6,248 | AR 2019 p.19, p.39 |
| 2020 | 3,400 | 206 | 778 | | | AR 2020 p.4, p.19, p.22 |
| 2021 | 4,358 | 109 | 647 | | | AR 2021 p.20 |
| 2022 | 2,800 | 134 | 802 | | | AR 2022 p.19 |
| 2023 | 3,019 | 236 | 810 | | | AR 2023 p.23 |
| 2024 | 5,088 | 243 (244 in AR 2025) | 764 | 19,772 | | AR 2024 p.24, p.29 |
| 2025 | 4,650 | 313 | 739 | 18,590 | | AR 2025 p.25, p.30 |

\* AR 2016 narrative says 686 crimes; the AR 2020 comparison table says 700.

## (b) Relevant facts and quotes

### Counting and definitions

- **AR 2013 p.16:** "During 2013, there were 100,431 police calls entered into the CAD system. This number includes activities such as service calls, 911 responses, self-initiated police activity, traffic enforcement and posts, prisoner processes, services of papers/warrants, admin/report writing, town building checks and community policing activities and excludes activities such as out of services and reporting on/off duty."
  - The same wording is repeated through AR 2017.
- **AR 2013 p.66 (Dispatch Supervisor):** "Below are the statistics covering the Calendar Year 2013 for the number of Police, Fire, Ambulance/Medical, and 911 Calls that were received by the Brookline Public Safety Dispatch Center. Police Calls: 74,529".
- **AR 2016 p.18:** "During 2016, there were 69,215 police calls entered into the CAD system. ... For 2016, calls for service are down 26% from the 93,553 calls in 2015."
  - No explanation is given.
- **MY 2016 p.15:** "In the first half of 2016, there were 35,824 police calls entered into the CAD system ... calls for service are down 29.9% from the 51,166 calls in the first half of 2015."
- **AR 2016 p.63:** the Dispatch table shows "CAD Entries 83,970 / Police Calls 74,149 / Fire Calls 7,948 / Ambulance/Medical Calls 4,323 / 911 Calls 12,001".
- **AR 2016 p.31:** "...people seeking assistance in the ~75K calls for service we respond to annually."
- **AR 2018 p.17:** "In addition to police related calls, a police unit is dispatched to assist on all fire and medical related calls, which accounts for an additional 8,354 calls."
- **AR 2020 p.22:** "In 2020, there were 63,806 calls for service entered into the Brookline Police Department's computer-aided dispatch system. Of these, 54,242 were police related calls for service..."
  - From 2020 onward the headline total includes fire/EMS.
- **FP2016 IV-48:** "Self-Initiated Police Calls NEW".
  - The separate self-initiated row starts with FY2014 data (20,907).
- **Policing Reforms Committee Final Report p.57, footnote 49:** "Officers notified dispatch that they are called off on traffic stops 5871 times (which is a little less than half of all stops). These figures do not include all of the stops."
  - So traffic stops generate CAD entries, but only about half are logged.

### CAD / RMS system history (no replacement found)

- **AR 2013:** charts are labeled "Data source: Larimore RMS".
- **FP2016 VII-34 (CIP):** "The current Computer Aided Dispatch (CAD) system ... is now 10 years old and is in need of either a significant upgrade or replacement." The plan funds a $75,000 CAD study.
- **FP2017 IV-47:** "a needs assessment on our computer aided dispatch system".
- **FP2018 IV-47:** "To prepare and train all personnel for the updated Computer Aided Dispatch (CAD) platform provided by CAD Vendor Larimore."
- **FP2018 VII-36 (CIP):** "CAD SYSTEM UPGRADE ... update our (Larimore) Public Safety programs ... Because of the need to upgrade the CAD portion during this fiscal year, funds in the amount of approximately $65,000.00 have been appropriated..."
- **FP2019 IV-46 (FY2018 accomplishments):** "Implemented the Larimore CAD system upgrade enabling many new functions and system changes to enhance reliability and effectiveness of the CAD for all Dispatchers and Officers."
  - The same page reports that "Next Generation 911 was implemented."
- **AR 2018 p.37:** the Dispatch Center "since March of 2017, has been utilizing the State's Next Generation 911 system" and "the State 911 Department's Wireless Direct Program continued to be a success ... the Town of Brookline received many more calls for service directly as opposed to the traditional standard for wireless 911 transfers."
- **FP2024 Sec 4I p.58 and FP2025 p.75:** "Incorporate 209A/258E orders in Larimore" and "Larimore Server Upgrade ... allow us to utilized the SQL Database for expanded reports".
  - Larimore was still in use in FY2024-25.
- **FP2027 Police p.183 (FY27 objective):** "Technology Upgrades: Secure CIP funding for CAD/RMS procurement".
  - A new CAD/RMS has not yet been procured.
- **Dispatch "CAD entries" narrative figures in the FP** (police and fire combined, year ambiguous):

  | Source | Figure |
  |---|---|
  | FP2015 | "more than 100,000 service calls" |
  | FP2017 IV-47 | 103,955 |
  | FP2018 IV-47 | 99,522 |
  | FP2019 IV-46 | 81,827 |
  | FP2020 IV-48 | 80,633 |
  | FP2023 | "more than 80,000" |

### Staffing

- **AdvCom Public Safety Subcommittee FY23 report p.2:** authorized versus sworn officers:

  | Date | Authorized | Sworn | Below authorized |
  |---|---|---|---|
  | 11/2018 | 138 | 130 | 8 |
  | 1/2020 | 139 | 125 | 14 |
  | 3/2022 | 135 | 116 | 19 |

  - The same page says: "Since 2011, 26 officers have left the department for other employment, with a majority leaving within the last 18 months."
  - Also: "Acting Chief Allen ... managed to reduce the shortfall of officers by backfilling, essentially taking specialty officers (detectives, etc.) and moving them to patrol."
- **AdvCom report p.4:** "In 2019 only 10 of 15 positions in the Dispatch Center were filled". It also quotes the Chief Dispatcher, 2022-03-07: "The dispatch operation currently operates below minimum staffing levels ... handles approximately 80,000 call entries per year".
- **FP2024 Sec 4I p.53 (FY2023 accomplishments):** "Managed all essential services of the Police Department and emergency response despite the lowest staffing levels the department has ever experienced."
- **AR 2025 p.26:** "The Brookline Police Department is currently 16 below the authorized strength, with additional strain from long-term injuries, four known pending retirements, and two sworn employees on long-term military deployments."
- **FP2027 Police p.183:** "Maintain full sworn complement (target: 101 officers)".
- **PERF profile p.2 (2018):** "currently employs 136 sworn officers" and "In 2017, BPD handled 71,000 calls for service, 15,000 moving violations ... and 360 arrests."

### COVID and enforcement policy

- **AR 2020 p.4:** "The decrease in arrests was partly due to a change in Department operating procedures, where due to the COVID-19 pandemic, officers were encouraged to seek court action rather than place individuals under arrest."
- **AR 2020 p.47:** "Because of the COVID pandemic, the Department's enforcement levels were significantly reduced for a significant part of the first half of the year. Traffic accidents were also reduced by half because of the lack of motorists on the road."
  - The same passage adds that the Select Board "voted to suspend parking regulations and enforcement for two months."
- **AR 2018 p.4:** the decline in arrests "represents our commitment to divert youth from the criminal justice system when practicable and also to work with residents in crisis to get them the help they need."
- **AR 2016 p.6:** "Last year, our field interview classification system was revamped to focus on field interrogations."
  - FP field interrogations went from 2,139 (FY2014) to 37 (FY2016).
- **Task Force to Reimagine Policing Final Report (2021), p.5 and p.11:** found "disturbing patterns in traffic stops" and recommended "a Home Rule petition to permit traffic enforcement by civilians."
  - I found no evidence in the police reports or FPs that civilian traffic enforcement was implemented.

### Clinician / CIT (co-response, not diversion)

- **AR 2018 p.43:** "In 2018, members of the CIT responded to approximately 1,100 calls for service that involved someone with a known or recognized mental health issue".
- **AR 2021 p.44:** "It is estimated that approximately 1,500 of our calls for service involved someone experiencing some form of mental health crisis". The grant-funded social worker "responds on scene when requested by officers".
- **AR 2022 p.29:** "Officers responded to approximately 2,160 calls for service related to mental health or substance use".
- **AR 2023 p.34:** about 2,625 such calls. **AR 2024 p.35:** about 2,711. **AR 2025 p.36:** about 1,240.
- **FP2023 Sec 4I p.60:** "Continue to integrate our clinician into calls for service".
- **FP2025 p.74:** "Expand the Family Services Unit to include the addition of an evening shift social worker to assist officers as a co-responder to calls for service."
- **FP2027 Police p.184:** "Secured grant funding to hire a clinician for co-response during an 'impact shift'".

## (c) Assessment

**What the sources state**

- The "police calls" definition printed in the reports did not change from 2013 to 2019.
- Nevertheless, the police CAD count fell 26% in 2016, and no report explains it.
- The department stayed on Larimore CAD throughout. It upgraded the system in FY2018 and is only now seeking funds for a new CAD/RMS.
- COVID cut enforcement in 2020.
- Sworn staffing fell from 130 (2018) to 116 (2022) and was still 16 below authorized strength in 2025.
- The clinician program co-responds with officers. It does not replace them.

**My inferences, in order of confidence**

1. **The FP series is spliced, so the FY2013 to FY2016-18 decline is mostly a definition artifact.**
   - The pre-2016 FP figures (about 75K) match the Dispatch "calls received" count, not the roughly 100K CAD-entry count.
   - From about FY2017 the FP figures match the CAD-entry count almost exactly on a fiscal-year basis.
   - The real CY2015 to CY2016 drop in CAD entries (−24K) is too large and too abrupt (already −30% in January-June 2016) to be behavioral. Crime, 911 volume and case numbers were flat.
   - It is roughly the size of the "self-initiated" activity the FP began reporting separately (about 21K to 25K). So I believe a counting or recording change occurred at the start of 2016. One possibility is that certain administrative or self-initiated entry types stopped being counted, even though the boilerplate description stayed the same.
   - This is inference. No source confirms it. The BPD Crime Analysis Unit or the Chief Dispatcher could confirm.
2. **The about 20% step down around 2020 (68K in 2018-19 to 52K-55K in 2020-24) is real, and it looks officer-side rather than public-side.**
   - Evidence against a drop in public demand: 911 calls rose from about 12K to 13K (2013-17) to about 18K to 20K (2019-25). Part of that rise is state routing changes (Wireless Direct, NG911), so it is not clean evidence of more public demand. Part A crime was flat to up (608 in 2019 against 760 to 810 in 2022-24).
   - Evidence for less officer-initiated work: moving violations fell about 75% (13,745 to 3,400) and have not recovered past about 5K. Arrests fell about 70% by 2021. Sworn strength fell and patrol was backfilled from specialty units.
   - Rough arithmetic: the Reforms Committee found about half of traffic stops are logged in CAD. On that basis, the drop in traffic stops alone could plausibly account for several thousand of the roughly 14K lost annual entries. This is an order-of-magnitude inference, not a measured decomposition.
   - The FP "self-initiated" row does not show a matching collapse (30,622 in FY2020; 19,871 to 26,197 in FY2024-25). So what that row measures, and whether it overlaps with "police-related calls", is unresolved.
3. **Diversion to other responders explains little or none of the decline.**
   - Brookline's model is officer-plus-clinician co-response. Reports describe "Officers responded to" the mental-health calls.
   - The mental-health call volume (1.1K to 2.7K a year) is small next to the decline.
   - I found no non-police response program (CAHOOTS-style or civilian traffic enforcement) in operation.
4. **The CY2025 drop (53,437 to 44,092) is unexplained.**
   - It falls entirely in July-December 2025.
   - It could be staffing (AR 2025: 16 below authorized strength), a recording change, or a data issue. It needs checking before FY2026 figures are used.

**Data-quality flags**

- FY2014 and FY2015 are both 75,525 in the FP.
- The FY2023 "Actuals" (50,000 and 26,000) are round numbers.
- FY2010 arrests are printed as 189.
- The AR comparison tables switch from police-only to police-plus-fire in 2019.
- In AR 2020 the fire and EMS components do not add up to the stated total.
- The 2023-24 first-half and second-half splits are lopsided.
- FP2021 and FP2022 (FY2019 and FY2022 actuals) were not available.

**Suggested next step:** ask BPD (Crime Analysis Unit or the Chief Dispatcher) for Larimore CAD counts by call type and by initiation source (citizen versus officer) for 2014-2025. Also ask what changed in how CAD entries were counted in January 2016.
