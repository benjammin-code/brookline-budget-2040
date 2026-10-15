# What produces the Town's ~5.3%/yr school cost growth? Research notes

Prepared 2026-09-29. Question: the Town's FY2027-FY2031 Long Range Financial Plan (LRFP, Jan 13, 2026)
grows the Schools line from $142.8M (FY26) to $185.1M (FY31), a 5.33%/yr CAGR, while this project's
driver-based forecast grows schools about 3.1%/yr. Which assumptions produce 5.3%?

Conventions in this file:
- **[Source]** marks what a document states, with a quote or table and a page reference. Page numbers are
  PDF page numbers unless marked "printed p."
- **[Inference]** marks my own arithmetic or interpretation. Arithmetic is reproducible from the source
  numbers shown.
- Local copies of everything cited are in `data/` or `data/psb_budget/` (file list at the end).

---

## 1. Headline findings

1. **The LRFP's school line isn't a Town model. It's the PSB's own forecast, spliced from two vintages.**
   [Source + Inference] Every LRFP school figure matches a PSB document to the dollar:
   - FY27 $152,745,067, FY28 $158,371,400 and FY29 $165,663,919 are the PSB's **December 18, 2025
     "Expenditure History and Forecast"** (`2025_PSB_forecast_spreadsheet.pdf`, p.1).
   - FY30 $177,265,426 and FY31 $185,135,639 are the PSB's **November 13, 2025 "5 Year Expenditure
     Forecast (FY27-FY31)"** (`2025-11_PSB_5yr_budget_projection.pdf`, p.1). That forecast describes
     itself as "preliminary estimates of PSB costs prior to any analysis for potential efficiencies".
   - The Town's February FY2027 Financial Plan states the method: "Projections for the Schools are based
     on their February budget presentation" (FY2027 Financial Plan, PDF p.26). Its LRFP table (PDF p.28)
     still carries the same Nov 13 FY30 and FY31 figures ($177,265,426 and $185,135,639).
2. **Because the FY31 endpoint is the Nov 13 pre-efficiency number, the 5.33% CAGR is exactly the Nov 13
   forecast's CAGR.** [Inference] $142.79M to $185.14M over 5 years is 5.331%/yr, and the Nov 13 series has
   the same endpoints. The Dec 18 figures only change the interior years.
3. **The splice adds a $3.1M step up in FY30.** [Inference] The Nov 13 FY29 figure is $168,775,413; the
   Dec 18 FY29 is $165,663,919. The LRFP goes from the Dec FY29 value straight to the Nov FY30 value, so its
   FY29 to FY30 jump is +$11.60M (+7.0%). The Nov series' own growth in that year is +$8.49M (+5.0%). If
   FY30 and FY31 grew at the Nov 13 rates from the Dec FY29 base, FY31 would be about $181.7M and the
   5-yr CAGR 4.94%, not 5.33%.
4. **What the PSB forecast assumes** (Nov 13 assumptions page, quoted in section 3):
   - flat staffing and flat enrollment
   - step and lane at the FY26 build ($1.88M + $0.17M a year)
   - the contractual 1% BEU raise at the start of FY27
   - out-of-district (OOD) tuition +4%/yr
   - Circuit Breaker revenue growing in step with tuition
   - about a 20% reset when each transportation contract is renewed
   - FY27 includes putting back $1.94M of recurring OOD tuition that FY26 had pushed onto the Circuit
     Breaker fund
5. **Wages are about 4.0-4.4 points of the 5-7% annual growth.** [Source numbers, Inference on shares] In
   the Dec 18 forecast, wages (125.0M to 131.3M to 137.7M to 144.1M) grow 5.05%, 4.85% and 4.64% with
   staffing held constant. The PSB finance deputy described this at the 2/26/26 School Committee meeting:
   "salary increases for PSB employees were forecast at 5% per year ... with no increase in FTEs" (ERSC
   Final Report, PDF p.53).
   - Step plus lane ($2.04M) is 1.63% of FY26 wages. The rest of the ~5% (about 3.2-3.4 points a year) is
     cost-of-living (COLA) and other wage assumptions that the PSB documents don't itemize.
6. **Health insurance and pensions are not in the school line.** [Source] Under the Town-School
   Partnership, benefits are "above the line" shared costs. The FY27 Financial Plan says the formula
   "allocates to PSB 59% of general fund revenue remaining after shared expenses like health care are
   accounted for" (PDF p.17). The PSB's own account list has only "Insurance/Benefits" of about $52K.
   **The 5.3% is salaries plus non-personnel only.** For comparability, this project's 3.1% should also
   exclude benefits.

---

## 2. The Town LRFP (FY27-FY31, January 13, 2026): what it says about schools

File: `data/FY27-FY31-Long-Range-Financial-Plan.pdf` (33 slides; PDF page = slide number).

- p.2 (Summary): "Schools assumed structural deficit: $13.5M ... Does not include efficiencies/proposals
  expected 12/18 from School Dep't ... School Cost pressures: Collective Bargaining, Special Education,
  Benefits".
- p.3 (Primary Assumptions): wage and inflation assumptions are listed only for the Town side ("1.5%
  Collective Bargaining increases in FY27, 2% in FY28"). **The slide gives no school-specific COLA, step,
  special education, transportation, enrollment or position assumptions.**
- p.5 (forecast table):

| | FY26 | FY27 | FY28 | FY29 | FY30 | FY31 |
|---|---:|---:|---:|---:|---:|---:|
| Schools | 142,792,591 | 152,745,067 | 158,371,400 | 165,663,919 | 177,265,426 | 185,135,639 |
| YoY % [Inference] | | 6.97% | 3.68% | 4.60% | 7.00% | 4.44% |
| Total School Surplus/(Deficit) | 0 | (10,772,704) | (16,358,740) | (24,370,530) | (30,487,003) | (36,038,925) |

- p.18 (Town/School Split): after non-departmental fixed costs, the School share of available revenue for
  FY27 is $141,993,405 (58.9%). [Inference] $152,745,067 minus the $10,772,704 FY27 school deficit equals
  $141,972,363, which is roughly this allocation. So the school deficit is the PSB forecast minus the
  formula allocation.
- p.18 footnote: "FY26 directs year 3 override funds to school budget, reflects reduction to School R&M."

**ARPA/ESSER:** the LRFP's "ARPA ends Dec. 2026" (p.2) refers to Town ARPA programs (for example Senior
Medical Transit), not schools. [Source] The school federal-relief cliff was already absorbed in FY24: "Loss
of ESSER and ARP Funds $5,639,984" (AdvCom Schools Subcommittee write-up, Spring 2023, PDF p.3). In FY27
the only grant-loss item the PSB lists is "Anticipated loss of Title II, III, and IV Grants ($277,126)"
(FY27 Proposed Budget, p.15; hearing slides p.6).

---

## 3. The PSB forecasts behind the LRFP

### 3a. Nov 13, 2025 5-Year Expenditure Forecast (`2025-11_PSB_5yr_budget_projection.pdf`, p.1)

| | FY26 Budget | FY27 | FY28 | FY29 | FY30 | FY31 |
|---|---:|---:|---:|---:|---:|---:|
| Expense Total | 142,792,591 | 155,644,237 | 161,394,753 | 168,775,413 | 177,265,426 | 185,135,639 |
| Change | 5,944,972 | 12,851,646 | 5,750,516 | 7,380,660 | 8,490,013 | 7,870,213 |
| % (as printed) | | 9% | 4% | 5% | 5% | 4% |

Stated assumptions (verbatim):
- "These are preliminary estimates of PSB costs prior to any analysis for potential efficiencies or items to
  be recommended for restoration or improvement."
- "Wages: Assumption: Staffing levels remain constant, enroll remains flat"
- "Assumption: Steps/Lanes are based on FY26 budget build estimate of $1,877,7771 [sic] (Steps) and
  $165,711 (Lanes)"
- "Note: FY27 begins with a 1% increase in wages for BEU staff that was agreed to as part of the FY24-FY26
  contract settlement"
- "OSS Tution: Assumption: Circuit Breaker revenue increases at the same rate as OOD tuition expenses.
  Assumption: Students remain in their current placement and the tuition rates will increase by 4%
  annually."
- "Note: $1,943,064 of the FY26 CB fund balance was used to balance the FY26 Budget. These expenses are
  included in the OOD tuition line in FY27"
- "Transportation: Assumption: Student's requiring transportation service remains constant. Note: Special
  Education transportation contract expires at the end of FY29. Note: Regular Education transportation
  contract expires at the end of FY28. Note: Price adjustments typically accompany the start of a new
  contract. The adjustment is estimated to be 20%."

**Not stated anywhere in the forecast documents:** the COLA percentage assumed for FY27 onward (beyond the
1% BEU carryover), any breakage or turnover offset, and how FY30 and FY31 were built.

### 3b. Dec 18, 2025 Expenditure History and Forecast (`2025_PSB_forecast_spreadsheet.pdf`, p.1)

| Account | FY23 Exp | FY24 Exp | FY25 Exp | FY26 Budget | FY27 Est | FY28 Est | FY29 Est |
|---|---:|---:|---:|---:|---:|---:|---:|
| Wages | 109,337,905 | 113,597,645 | 118,434,424 | 125,011,799 | 131,329,084 | 137,700,378 | 144,090,409 |
| Out of District Tuition | 3,934,981 | 4,588,068 | 4,939,295 | 2,968,628 | 5,204,521 | 4,023,346 | 4,184,280 |
| Transportation | 2,978,772 | 5,298,974 | 5,022,805 | 5,247,618 | 6,414,416 | 6,547,183 | 6,950,771 |
| Leased Computers | 40,000 | 936,912 | 1,037,401 | 853,135 | 1,300,000 | 1,339,000 | 1,379,170 |
| Online Books, Subscriptions & Tools | 612,661 | 709,073 | 1,143,162 | 1,296,150 | 1,818,864 | 1,873,430 | 1,929,633 |
| Professional/Technical Services | 1,867,072 | 3,052,001 | 2,665,994 | 2,828,406 | 2,421,359 | 2,494,000 | 2,568,820 |
| Claims & Settlements | 1,699,391 | 647,243 | 883,215 | 1,423,679 | 1,073,530 | 1,115,271 | 1,158,682 |
| (all other lines, see file) | | | | | | | |
| **Expense Total** | 123,726,143 | 131,031,804 | 136,847,619 | 142,792,591 | 152,745,067 | 158,371,400 | 165,663,919 |
| % change | | 5.90% | 4.44% | 4.34% | 6.97% | 3.68% | 4.60% |

Footnotes (verbatim): "*Transportation expenses are understated in the FY25 operating budget by $866,894,
expense funded through revolving fund balances." and "** Tuition expenses are understanded [sic] in the
FY26 operating budget by $1,943,064 (1.4%); expense funded through the Circuit Breaker revolving fund."

**[Inference] Contribution to total growth, percentage points of the prior-year total:**

| Component | FY27 | FY28 | FY29 |
|---|---:|---:|---:|
| Wages (staff flat) | +4.42 (wages +5.05%) | +4.17 (+4.85%) | +4.03 (+4.64%) |
| OOD tuition (net of Circuit Breaker offset) | +1.57 | -0.77 | +0.10 |
| Transportation | +0.82 (+22.2%) | +0.09 | +0.25 (+6.2%) |
| All other non-personnel | +0.16 | +0.20 | +0.21 |
| **Total** | **6.97** | **3.68** | **4.60** |

- The FY27 OOD jump is mostly the $1.94M Circuit Breaker put-back, which is 1.36 pts of the 6.97%.
- The FY28 drop reflects the Circuit Breaker fund balance recovering. The PSB budget book projects the fund
  balance at $5,068,888 for FY28 (FY27 Proposed Budget p.34, Fig. 2c-5), and the OOD line is net of that
  offset.

### 3c. Later vintages, each lower than the one the LRFP used

[Source] FY27 Budget Overview slides, 2/5/26, p.19 ("FY27 Preliminary Forecast to Proposed Budget"):

| Date | FY27 Budget | Increase | % |
|---|---:|---:|---:|
| Nov 13, 2025 Forecast | 155,644,237 | 12,851,646 | 9.00% |
| Dec 17, 2025 Forecast | 152,745,067 | 9,952,476 | 6.97% |
| Jan 22, 2026 Budget | 151,265,410 | 8,472,819 | 5.93% |
| Feb 5, 2026 Budget | 150,898,826 | 8,106,235 | 5.68% |

[Source] Feb 26, 2026 update (slides p.5; ERSC appendix PDF p.170; override slides p.15):

| | FY26 | FY27 | FY28 | FY29 |
|---|---:|---:|---:|---:|
| PSB Budget 02.26.26 | 142,792,591 | 149,801,901 (+4.91%) | 155,314,303 (+3.68%) | 162,571,740 (+4.67%) |
| Town allocation 03.13.26 | 142.8M | 145.3M (+1.73%) | 145.2M (-0.06%) | 144.6M (-0.37%) |
| Funding gap (= Schools override) | | 4.5M | 5.6M | 7.8M (total 17.9M) |

- [Inference] The Feb 26 path is 4.42%/yr over FY26-29, or 3.95%/yr if the FY26 base is restated to
  include the $1.94M Circuit Breaker-funded tuition. The Dec 18 path the LRFP used is 5.08%/yr, or 4.61%/yr
  on the restated base.
- The School Committee adopted $149,801,901 on 3/19/26 (vote slide, p.9).
- The Feb FY2027 Financial Plan LRFP table (PDF p.28) shows Schools FY27 $144,533,296 (the no-override
  allocation), then $157,010,424, $165,264,178, $177,265,426 and $185,135,639. FY30 and FY31 are still the
  Nov 13 values.

**The PSB's own framing of FY27 growth** (FY27 Proposed Budget, p.20): "The FY27 proposed funding request is
$150,898,826, representing a 5.68% increase ... In FY26, an additional $1,943,064 (1.36%) of recurring
costs was funded using one-time revenue (structural deficit) ... The remaining variance of $6,163,235 ...
constitutes a 4.3% increase in overall cost." The Feb 26 version: "The remaining $5,066,246 ... constitutes
a 3.55% increase in overall cost" (ERSC PDF p.170).

---

## 4. Salary rate: COLA and step/lane

### Contract terms

**[Source] Terms of the 2020-2026 BEU agreement (reported May 17, 2022, NBC Boston):** "6% increase in all
wages and stipends, followed by 8% increase over the period of Sept. 2023 through August 2026, with an
additional 1% in August 2026. These raises are in addition to the contractual 'steps' ..."

**[Source] FY26 COLA and the grid** (ERSC, PDF p.62-63): "The 2023 to 2026 contract between the Brookline
School Committee (BSC) and the Brookline Educators Union (BEU) included a nominal 2.75% cost of living
increase effective on September 1, 2025 ... about 52% Brookline educators ... are on PSB's 'Step & Lane'
grid ... for someone with a Master's degree, this amounts to an effective 6.7% ... salary increase."

ERSC table of effective FY25 to FY26 raises for individuals moving one step (PDF p.63):

| Step/lane | FY25 | FY26 (next step) | % increase |
|---|---:|---:|---:|
| Step 1/2, Bachelor's | 60,514 | 65,358 | 8.0% |
| Step 1/2, Master's | 67,437 | 72,569 | 7.6% |
| Step 6/7, Master's | 83,388 | 88,957 | 6.7% |
| Step 10/11, Master's | 96,150 | 102,066 | 6.2% |
| Step 14/15, Master's | 109,504 | 115,638 | 5.6% |
| Step 14/15, Doctorate | 119,558 | 125,886 | 5.3% |

[Inference] These are raises for individuals moving a step, not payroll growth. Only about half the staff
move a step each year, and retirements and replacements offset part of it.

### Step and lane cost

[Source] FY26 Level Service Cost Drivers (`FY26_level_service_cost_drivers.pdf`, p.1):

| Driver (FY25 to FY26 level service) | $ |
|---|---:|
| Employee Raises: COLA 2.75% (All Employees) | 3,255,971 |
| Employee Raises: Step, Lane, Principals Adj. (Steps 1,877,771; Lanes 165,711; Principals 65,000) | 2,108,482 |
| Salary Structural Deficit: Extra Compensation | 730,660 |
| Salary Structural Deficit: Grants (IDEA, SEL, Health, Title 1 moving to operating) | 1,806,022 |
| Salary Structural Deficit: New FY25 Staff | 296,580 |
| Minor Adjustments | 122,860 |
| Breakage | -500,000 |
| **Total Salary Expense Drivers** | **7,820,575** |
| OOD Tuition | 1,293,567 |
| OSS Settlements | 313,920 |
| OSS Transportation | 696,085 |
| OSS Professional/Technical Services | 239,755 |
| OSS Online Books, Subscriptions & Tools | 60,950 |
| Non-Salary all other changes | 461,719 |
| **Total Non-Salary Expense Drivers** | **3,065,996** |
| **Total** | **10,886,571** |

[Inference] A 2.75% COLA cost $3.26M, so 1 point of COLA is about $1.18M on the FY26 base. Step plus lane
of $2.04M is about 1.7 points on the same base, or 1.63% of FY26 budgeted wages ($125.0M).

### What the forecast wage path implies

- **[Source]** ERSC PDF p.53: "Even though only 52% of PSB educators remain on the 'steps and lanes' grid,
  salary increases for PSB employees were forecast at 5% per year by Dr. Susan Givens at the 2/26/26 School
  Committee meeting, with no increase in FTEs." Footnote 28 (PDF p.63-64): "PSB has not provided an
  explanation of the computations underlying its wage forecasts, although Dr. Givens estimated wage
  increases of 5% with no FTE changes, and an increase of 3.78% ($3.35 million) in Professional Staff wages
  (not including benefit cost increases) for FY 27 ... even with FTE reductions."
- **[Inference]** The Dec 18 wage growth (5.05%, 4.85%, 4.64%) is roughly 1.5-1.6 points of step and lane
  plus about 3.2-3.4 points of other rate increases (COLA assumptions for new contracts, the 1% BEU
  carryover in FY27, and possibly other items). **The PSB's COLA assumption for FY28 and later isn't
  published.** I can't split the 3.2-3.4 points further from the documents.
- **[Source] Bargaining status:**
  - All three BEU contracts expired Aug 31, 2026 (Brookline.News, "Brookline educator contracts expire as
    negotiations continue").
  - In March 2026 the School Committee counter-offered "a 1.5% salary increase for members of all three
    union's bargaining units," estimated at "$1.7 million more than continuing current contracts"
    (Brookline.News, Mar 14, 2026). The BEU has proposed cutting the salary schedule from 17 steps to 12.
  - The PSB override slides (p.9) say: "All (6) union contracts currently in bargaining".
  - Other PSB units: FY25 MOAs with AFSCME units and a 2023-26 paraprofessional contract exist on the PSB
    and BEU sites; not analyzed here.
- **[Source] Actual FY27 budget wages:** salary subtotal $125,011,798 (FY26) to $129,828,274 (FY27
  proposed, 2/5/26), +3.85%, with 19.7 fewer FTE (FY27 Proposed Budget p.21).
- **Could not verify:** the Unit A CBA salary appendix. The copy saved in `data/psb_budget/` is a scanned
  80-page PDF with no text layer. Its table of contents (PDF p.3) lists "3.1 Salary Schedules in Appendix A
  and B" and "3.2 Longevity"; the appendix itself was not read.

---

## 5. Staffing

[Source] The forecast holds staffing flat: "Staffing levels remain constant, enroll remains flat" (Nov 13
forecast). The budgets actually reduce FTE.

FTE by function, all funds (FY27 Proposed Budget p.19, Fig. 1f-3; ERSC appendix PDF p.172-173):

| Functional area | FY24 | FY25 | FY26 | FY27 proposed | FY24-26 change |
|---|---:|---:|---:|---:|---:|
| Special Education | 365.2 | 374.8 | 389.0 | 386.1 | +23.8 |
| BEEP (Pre-K) | 40.7 | 56.7 | 54.1 | 54.1 | +13.4 |
| General Education K-12 | 810.4 | 802.7 | 790.9 | 773.7 | -19.5 |
| Total Building Staff | 1,216.3 | 1,234.2 | 1,234.0 | 1,213.9 | +17.7 |
| District Admin | 236.3 | 229.3 | 218.4 | 216.4 | -17.9 |
| **Total Staffing** | **1,452.6** | **1,463.5** | **1,452.4** | **1,430.3** (after 2/26 cuts) | -0.2 |

Enrollment vs DESE FTE, excluding custodial and food service (ERSC appendix PDF p.172; override slides
p.13):

| Year | Enrollment | FTE |
|---|---:|---:|
| 19-20 | 7,777 | 1,378.4 |
| 20-21 | 6,791 | 1,348.2 |
| 21-22 | 6,928 | 1,299.4 |
| 22-23 | 7,060 | 1,270.77 |
| 23-24 | 7,195 | 1,265.8 |
| 24-25 | 7,023 | 1,249.4 |
| 25-26 | 6,948 | 1,264.1 |
| 26-27 (proj.) | 6,923 | 1,242.0 |

- FY27 changes: net -22.1 FTE. Of these, "2.9 are special education, 2.0 are district admin, and 17.2 are
  general education K-12" (ERSC PDF p.36).
- 152.3 FTE are funded by special revenue (36.7 grants, 118.6 revolving) (FY27 FAQs 2/12/26, p.2).
- **Planned position additions:** "In FY28, PSB anticipates the need to restore a position to OTL
  administration as well as the Communications Specialist role" (FY27 FAQs 2/26/26, p.4). Separately,
  "There are currently no plans to move any positions funded by special revenue funds onto the operating
  budget" (same, p.5).
- **Enrollment basis differs from NESDEC.** [Source] PSB plans with Cropper-McKibben's 2023 forecast, which
  shows a low in 2026-27 and then a rise to 7,444 by 2033-34 (ERSC appendix PDF p.173-174). This is the
  opposite direction from NESDEC's decline to 6,127. PSB's FY27 budget assumes 6,989 students (-42).

[Inference] Because the forecast holds staff flat, it builds in no savings from enrollment decline. The
actual FY27 budget cut 22.1 FTE, which is about 1.5% of staff. Nothing in the forecast mechanism responds
to NESDEC's roughly -13% decline.

---

## 6. Special education, out-of-district tuition, Circuit Breaker, transportation

- **OOD counts** (FY27 Proposed Budget p.33, Fig. 2c-3), OOD / settlement agreements / total:

| Year | Out of District | Settlement Agreements | Total |
|---|---:|---:|---:|
| FY23 | 68 | 12 | 80 |
| FY24 | 60 | 24 | 84 |
| FY25 | 60 | 26 | 86 |
| FY26 | 66 | 15 | 81 |
| FY27 (budget) | 60 | 10 | 70 |

- **Tuition, gross of Circuit Breaker** (p.34, Fig. 2c-4): total tuition $7.82M (FY23), $8.51M (FY24),
  $9.49M (FY25), $10.59M (FY26), $10.18M (FY27).
  - Circuit Breaker reimburses "75% of costs exceeding the annual per-student claim threshold, which for FY26
    is $53,431" (p.33).
  - The PSB says OOD tuition "in FY 26 was $10.6 million and is budgeted at $10.2 million for FY27,
    including the impact of DESE approved price increases" (AdvCom FY27 write-up, packet PDF p.15-16).
  - AdvCom footnote: "DESE allows increases that exceed 2.5%, with some years seeing tuition increases as
    high as 14%."
- **The $1.94M Circuit Breaker item is one-time in nature.**
  - [Source] "During the FY26 Budget process, PSB was unable to close the gap between the budget and the
    Town's revenue allocation and moved $1,943,064 of OOD Tuition expenses to the Circuit Breaker Revolving
    Fund, thus causing the decrease in the OOD Tuition line in FY26 and an unusual increase in OOD tuition
    in FY27" (FY27 Proposed Budget p.33).
  - FY26 closing report (`FY26_budget_closing_summary.pdf`, p.2): "we underspent Circuit Breaker by $1.4
    Million. Thus, the net savings in OOD Tuitions is approximately $1 Million. This eliminates our
    structural gap in that fund."
- **Transportation.**
  - [Source] FY27 Proposed Budget p.34-35: the SPED transportation increase of $848,287 "reflects
    restoration of full funding ($522,565) as well as contractual rate increases ($233,711) and increases in
    service ($92,011)."
  - FY25 SPED transportation was underfunded by $865,894 and covered from revolving funds.
  - SPED riders rose from 132 (FY23) to 177 (FY25 and FY26 budget) (`FY26_sped_transportation.pdf`).
  - Contract resets are forecast at about 20% (Nov 13 note).
- **In-district SPED direct cost** (ERSC PDF p.69-70, from DESE 2023-24): $34,951,114 total, or $30,130
  per in-district IEP student across 1,160 students.
  - The AdvCom write-up records the PSB saying it sees "an increase in students identified with autism ...
    more students with higher level of need" (packet PDF p.18).
  - Asked whether the financial plan builds in assumptions for rising acuity, the PSB answered with
    training needs; no quantified assumption was given (same page).

---

## 7. Other non-personnel and one-time items

- **[Source]** FY27 restorations and additions (FY27 Proposed Budget p.15; hearing slides p.4-6):
  - Director of Data and Information Systems (restored)
  - professional and curriculum development: Education/Training rises from $78,998 to $361,457
  - computer leases, deferred in FY26
  - OTL copier leases, "unintentionally omitted from FY26"
  - K-8 math curriculum renewal ($265,000)
  - Google Workspace ($54,000)
  - FF&E of $75K moved from CIP to operating
  - transportation and stipends as "structural deficit" restorations
- **[Source]** Online subscriptions: $1.30M to $1.82M (+$0.52M) in FY27 (p.21).
- **[Inference]** In the Dec 18 forecast, "all other non-personnel" grows about 3%/yr after FY27 (+2.4%,
  +3.1%, +3.4%), close to CPI. The FY27 non-wage jump is concentrated in the OOD put-back, the
  transportation restoration and rate increase, and tech and curriculum items.

---

## 8. The override: what the school portion was said to fund

- [Source] Override Guide (brooklinema.gov/3590): Schools $17,944,439 over FY27-29. The Schools portion will
  "fund the current level of performance after the cuts and efficiencies proposed in the Superintendent's
  budget"; YES "Maintains core PSB Staff levels & programs"; NO means "Loss of major school programs".
- [Source] PSB override slides (`override_PSB_asks_slides.pdf`):
  - p.15: the $17.9M equals the FY27-29 gap between PSB Budget 02.26.26 and the Town allocation.
  - p.22: "No new programs are included or projected for the 27-29 period."
  - p.9: "PSB projected to receive a total of $1.8 M in additional funding over the next 3 years (average
    ~$600 K/year)."
- [Source] PSB summary (ERSC PDF p.170): "If PSB did not have a rolling structural deficit of $1,943,064
  and the Town revenue allocation was consistent with prior year averages ... the funding gap would be
  minimal, requiring a minimal override."
- Outcome: passed May 5, 2026, 8,859 to 5,826 (Boston.com, May 11, 2026).
- ERSC condition #2, adopted into the AdvCom packet (PDF p.22): "Create an approach through which the
  Schools manage wage expenses to a level approaching projected year-over-year revenue growth, including
  considering caps on wage increases or other creative contractual terms."
- The Mar 29, 2026 Town-PSB MOA item 9 says: "Bargain in good faith with all units with an aim toward
  establishing sustainable financial stability and retention."

[Inference] The override closes the gap between about 4.4%/yr PSB budget growth (Feb 26 path) and near-zero
allocation growth, which was squeezed by above-the-line health insurance. It funds continuation, not
expansion, and is sized off the Feb 26 path. That path is lower than the Dec/Nov path the January LRFP used.

---

## 9. Decomposition of the ~5.3%/yr (FY26 to FY31, +$42.34M)

[Inference throughout. Built only from the source numbers above; the unitemized residual is labeled as
such.]

| Piece | Approx. $ over 5 yrs | Approx. pts of 5.33% CAGR | Basis |
|---|---:|---:|---|
| Step + lane (grid movement at ~$2.04M/yr, staff flat) | ~10.2M | ~1.4-1.6 | Nov 13 assumption |
| Other wage rate increases (1% BEU carryover in FY27 + unpublished COLA assumptions FY28-31) | ~21M | ~2.5-2.9 | Residual of Dec 18 wage path (~5%/yr) after step/lane |
| Staffing changes | 0 | 0 | Forecast holds staff flat; no enrollment-driven reductions |
| OOD tuition put-back ($1.94M, one-time accounting restoration) | 1.94M | ~0.27 | FY26 base understated per PSB |
| OOD tuition trend (4%/yr on net line) | small | ~0.1 | Dec 18: net OOD $5.2M to $4.2M FY27-29 |
| Transportation (FY27 restoration + rate + service; ~20% resets at FY29 and FY30 renewals) | ~2-3M | ~0.3-0.4 | Dec 18 FY26-29 +$1.70M; FY30-31 not itemized |
| Other non-personnel (~3%/yr, plus FY27 restorations of tech, curriculum, PD) | ~2M | ~0.3 | Dec 18 |
| Splice artifact (Dec FY29 to Nov FY30 level mismatch) | 3.11M | ~0.4 | Section 1, finding 3 |

The rows are approximate and overlap. The FY30-31 years in particular can't be itemized, because the Nov 13
forecast only gives totals.

**Compared with this project's 3.1% forecast:**
- The wage assumption differs by about 1.6-2 points a year: PSB ~5% vs 3.0% pay + 0.4 drift.
- The one-time Circuit Breaker put-back and the splice together add about 0.7 points to the Town's CAGR.
- Transportation resets and restorations add a few tenths.
- Neither forecast cuts staff for enrollment decline.

---

## 10. Classification: policy choice, contractual commitment, or external cost

| Assumption | Classification | Notes |
|---|---|---|
| 1% BEU raise at start of FY27 (8/31/2026) | Contractual (settled) | Part of the 2020-26 agreement |
| Step/lane movement (~$2.0M/yr) | Contractual structure, renegotiable | Grid is in the CBA. Contracts expired 8/31/26. Whether steps continue in the status quo under an expired contract is a legal question I didn't resolve. BEU has proposed shortening the grid. |
| COLA for FY28+ (implicit ~3%+) | Policy / bargaining outcome | Not contractual yet. The SC's own March 2026 offer was 1.5% for one year. |
| Flat staffing despite enrollment decline | Policy choice | PSB class-size guidelines (22 K-2, 25 3-8) and program choices; the FY27 budget actually cut 22.1 FTE |
| Special education staffing growth (+23.8 FTE FY24-26) | Mix: legal mandate (IEPs) + policy (build in-district programs to avoid OOD) | PSB says in-district programs keep the OOD rate low (5.1% of SWD) |
| OOD tuition rates (+4%/yr) | External | Rates set/approved by DESE (Operational Services Division) |
| Circuit Breaker reimbursement | External (state appropriation) | Assumed to grow with tuition |
| $1.94M Circuit Breaker put-back in FY27 | One-time accounting / base correction | Largely resolved in FY26 close |
| Transportation contract resets (~20%) | External market price, contract timing | Renewal dates FY28 (reg ed), FY29 (SPED) |
| Restorations (Data Director, PD, tech leases, curriculum) | Policy choice | Small dollars |
| FY30-31 values from the Nov 13 pre-efficiency forecast | Forecasting artifact | Not an assumption anyone defended; the Town reused them unchanged |
| Health insurance (12%/yr) | Excluded from school line | Hits the allocation, not the school cost line |

---

## 11. Open items not resolvable from these documents

- The PSB's COLA assumption for FY28-FY31, and whether the Dec 18 wage path includes breakage.
- How FY30 and FY31 in the Nov 13 forecast were built (only totals are published).
- The Unit A salary schedule appendix: the CBA PDF is scanned, and I didn't OCR it.
- The outcome of the 2026 BEU successor contract (still in negotiation as of September 2026).

---

## Files (data/psb_budget/ unless noted)

**Forecasts and budget drafts**
- `2025-11_PSB_5yr_budget_projection.pdf` (Nov 13, 2025 forecast)
- `2025_PSB_forecast_spreadsheet.pdf` (Dec 18, 2025 forecast)
- `FY2027_proposed_budget.pdf` (Superintendent's FY27 budget book, 109 pp)
- `FY27_budget_slides_2026-02-05.pdf`, `FY27_budget_hearing_slides.pdf`, `FY27_budget_update_hearing.pdf`
- `FY27_budget_FAQs_hearing.pdf`, `FY27_budget_FAQs_2026-02-26.pdf`, `FY27_budget_slides_2026-02-26.pdf`
- `FY27_failed_override_impacts.pdf`, `FY27_budget_presentation_vote.pdf`
- `FY27-29_PSB_budget_summary.pdf`
- `FY27-31_budget_guidelines_*.pdf`, `FY27_budget_guidelines_voted.pdf`

**FY26 budget and actuals**
- `FY26_level_service_budget.pdf`, `FY26_level_service_cost_drivers.pdf`, `FY26_sped_transportation.pdf`
- `FY26_initial_budget_request.pdf`, `FY26_initial_budget_slides.pdf`
- `FY26_budget_closing_summary.pdf`, `FY26_superintendent_financial_update.pdf`
- `FY25_budget_close_report.pdf`

**Override, oversight and contracts**
- `override_PSB_asks_slides.pdf`, `override_summary_onepage.pdf`, `Town_PSB_supplemental_MOA_2026.pdf`
- `AdvCom_Schools_Subcommittee_writeup_spring2023.pdf`, `AdvCom_Schools_Subcommittee_writeup_spring2024.pdf`
- `AdvCom_Schools_Subcommittee_FY27_writeup_draft_2026-04-28_packet.pdf`
- `BEU_UnitA_CBA_2023-2026.pdf` (scanned)

**Also cited from `data/`**
- `FY27-FY31-Long-Range-Financial-Plan.pdf`, `FY2027-Financial-Plan.pdf`,
  `ERSC Final Report FINAL 031326.pdf`

Note: `FY27_budget_request_final.pdf` has no text layer and was not used.
