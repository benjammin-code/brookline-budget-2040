# Brookline population by age: sources, parsing and checks

Outputs built by `scripts/brookline_population_by_age.py` (re-runnable; reads only files under
`data/demographics/`):

- `output/brookline_population_by_age.csv`: columns `year, source, age_group, population, is_projection, grouping`
- `output/brookline_resident_births.csv`: columns `year, resident_births, source, note`

Geography throughout: Brookline town, Norfolk County, MA. County subdivision GEOID 2502109175
(state 25, county 021, cousub 09175); DOR/UMDI municipal code 046.

## How to read the population CSV

`grouping` was added beyond the five requested columns because the file mixes overlapping age
groups. Filter on it before summing anything:

| grouping | age_group values | notes |
|---|---|---|
| `total` | `total` | all ages |
| `five_year` | `0-4`, `5-9`, ... `80-84`, `85+` (18 groups) | sums exactly to `total` for every year/source (asserted in the script) |
| `summary` | `under 5`, `5-17`, `18-24`, `5-14`, `5-19`, `25-44`, `45-64`, `65-74`, `75-84`, `85+`, `65+`, `75+` | overlapping rollups; never sum these |

`5-17` and `18-24` exist only for Census and ACS rows. UMDI publishes five-year groups only, so the
15-19 group cannot be split at 17/18 without an assumption; UMDI rows carry `5-14` and `5-19`
instead, and Census/ACS rows carry those too for like-for-like comparison. No interpolated 5-17
value is stored in the CSV.

`year` is the census year, the projection year, or the **end year** of an ACS 5-year period (the
period is spelled out in `source`).

## Sources

### Census 2000 Summary File 1, table P12 (Sex by Age), 100% data
- Files: `https://www2.census.gov/census_2000/datasets/Summary_File_1/Massachusetts/mageo_uf1.zip`
  (geographic header) and `.../ma00002_uf1.zip` (data file 02).
- Segment layout from `0README_SF1.txt` in the same directory (saved): file 02 holds matrices P6 to P18.
- Brookline record: SUMLEV 060, LOGRECNO 0078543 (geo line saved as `census2000_sf1/brookline_2000_geo.txt`;
  it carries state 25, county 021, cousub 09175).
- P12 starts at data cell 121 of file 02. This offset was confirmed two ways: (1) the Census API
  group metadata for P006 to P011 (73+8+17+7+15+1 = 121 cells, fetched keyless from
  `https://api.census.gov/data/2000/dec/sf1/groups/P006.json` etc.); (2) a scan of the row for the
  only 49-cell window whose male and female cells sum to their subtotals and to the total.
- Cell labels (P012001 to P012049) confirmed from `https://api.census.gov/data/2000/dec/sf1/groups/P012.json`
  (saved as `census2000_sf1/p12_2000.json`).
- Total 57,107.

### Census 2010 Summary File 1, table P12
- File: `https://www2.census.gov/census_2010/04-Summary_File_1/Massachusetts/ma2010.sf1.zip` (196 MB;
  not kept in Dropbox, only the Brookline rows were extracted). README saved as `census2010_sf1/0README_SF1_v2.pdf`.
- Brookline record: SUMLEV 060, LOGRECNO 0110482 (geo line saved).
- P12 is in data file 04 at data cell 144. Confirmed by: P10 (71 cells) and P11 (73 cells) precede it
  per API metadata; the first cell of file 04 (48,324) equals Brookline's 18+ population computed
  independently from P12 (58,732 minus 10,408 under 18), which is the P10 universe; and the
  sex/age sum checks pass.
- Labels confirmed from `https://api.census.gov/data/2010/dec/sf1/groups/P12.json` (saved).
- Total 58,732, matching the known 2010 count.

### Census 2020 Demographic and Housing Characteristics File (DHC), table P12
- File: `https://www2.census.gov/programs-surveys/decennial/2020/data/demographic-and-housing-characteristics-file/Massachusetts/ma2020.dhc.zip`
  (201 MB; not kept, Brookline rows extracted). Pipe-delimited.
- Segment map: `table_segments_dhc.csv` from `.../demographic-and-housing-characteristics-file/2020_dhc_sas_example.zip`
  (saved as `census2020_dhc/table_segments_dhc.csv`): segment 6 holds P10 (71), P11 (73), P12 (49), so
  P12 starts at data cell 144.
- Geo header field order from the same zip's `read_sumfile_2020.sas`. Brookline record: SUMLEV 060,
  GEOCOMP 00, LOGRECNO 0000315, GEOID 0600000US2502109175, POP100 63,191.
- Labels confirmed from `https://api.census.gov/data/2020/dec/dhc/groups/P12.json` (saved).
- Total 63,191, matching the known 2020 count; segment 6's first cell (50,969) equals the 18+
  population implied by P12.
- Caveat: 2020 DHC cells include Census disclosure-avoidance noise. At a town of 63,000 this is
  small for the broad groups but can be visible in single cells.

### ACS 5-year estimates, table B01001 (Sex by Age)
- 2020-2024: `https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b01001.dat`
  (national file; Brookline row `GEO_ID = 0600000US2502109175` extracted). Column meanings from
  `.../2024/table-based-SF/documentation/ACS20245YR_Table_Shells.txt` (B01001 excerpt saved); GEO_ID
  confirmed as "Brookline town, Norfolk County, Massachusetts" in `Geos20245YR.txt`.
- 2015-2019: `https://www2.census.gov/programs-surveys/acs/summary_file/2019/prototype/5YRData/acsdt5y2019-b01001.dat`
  (Census's table-based prototype for 2019). Column meanings from `.../2019/prototype/ACS2019_Table_Shells.csv`.
- Both rows pass the same sex/age sum checks. Totals: 59,180 (2015-2019) and 63,266 (2020-2024).
- These are survey estimates with margins of error (90%), computed here by root-sum-of-squares of the
  published cell MOEs (an approximation Census documents for aggregating cells):

| group | 2015-2019 | 2020-2024 |
|---|---|---|
| under 5 | 2,880 ± 356 | 2,916 ± 416 |
| 5-17 | 8,155 ± 559 | 8,916 ± 800 |
| 65+ | 9,460 ± 666 | 9,986 ± 802 |
| 75+ | 4,116 ± 471 | 4,661 ± 562 |
| 85+ | 1,178 ± 250 | 1,211 ± 253 |

### UMDI Vintage 2024 population projections (current series)
- Page: `https://www.umass.edu/donahue/research-and-data/massachusetts-population-estimates-program/population-projections`
- Age/sex file: `https://www.umass.edu/donahue/media/2443/download?attachment`
  (`UMDI_V2024_Long-Term_Population_Projections_MCD,_County,_RPA,_State_Age_Sex_detail_2010-2050.xlsx`), sheet
  `CityTown Age 2010-2050`, rows `Municipality = Brookline`, columns 2010, 2020, 2025 ... 2050.
- Totals file: `.../media/2441/download?attachment`; methodology: `.../media/2445/download?attachment` (all saved).
- Brookline totals: 63,082 (2025), 63,508 (2030), 63,854 (2035), 64,167 (2040), 64,272 (2045), 64,473 (2050).
- The 2010 and 2020 columns equal the Census P12 counts group-for-group (asserted in the script), so
  they are not repeated in the CSV. The methodology report (pp. 31-33) lists the municipalities whose
  2020 launch population was adjusted for child undercount or census challenges; Brookline is not one
  of them.
- Method in brief (from the report): cohort-component; town-level fertility 2012-2022 and mortality
  2012-2022 (2020 excluded) from MA DPH; migration from 2010-2020 residual net migration and
  2012-2019 ACS regional gross migration; town results controlled to regional projections. It is a
  status-quo demographic model and does not include housing pipeline effects.

### UMDI-DOT Vintage 2018 projections (superseded; kept for comparison)
- Files: `http://pep.donahue-institute.org/publications/AgeSexDetails_UMDI-DOT_V2018.xlsx` (sheet
  `CityTown_Age`, `MCD Name = BROOKLINE`), `.../CityTownTotals_UMDI-DOT_V2018.xlsx`,
  `.../UMDI-DOT.V2018_Methodology.pdf` (all saved). Found via the archived UMDI page
  (web.archive.org snapshot 20220119045158 of pep.donahue-institute.org); the files are still served directly.
- Launched from Census 2010 (its 2010 column equals Census P12, asserted). Projected Brookline at
  65,693 for 2020 against an actual count of 63,191, and 79,442 for 2040 against V2024's 64,167.

## Resident births (`brookline_resident_births.csv`)

- 2015 to 2022: MA DPH, *Massachusetts Births [year]*, table "Birth Characteristics: Occurrence and
  Resident Births, Massachusetts Municipalities" (Table 15 in the 2015 and 2016 reports, Table 17 from
  2017 on), column "Resident Births: Number of Births". Resident births include births to Brookline
  residents that occur out of state (report definitions section). Reports were retrieved from Wayback
  Machine copies of `https://www.mass.gov/doc/<year>-birth-report[-0]/download`, because mass.gov
  returns HTTP 403 to scripted requests; each file's own title page was checked for its year. Saved in
  `data/demographics/births/`.
  Values: 2015 609, 2016 605, 2017 594, 2018 571, 2019 581, 2020 487, 2021 491, 2022 482.
- 1980 to 2014: MA DOR Division of Local Services Municipal Databank, "Number of Resident Births"
  (`https://dls-gw.dor.state.ma.us/reports/rdPage.aspx?rdReport=Number_of_Resident_Births`, municipality
  code 046), which covers 1980-2017. Saved as an HTML response.
- Cross-checks: DLS matches the DPH-sourced births in the NESDEC enrollment forecast
  (`data/NESDEC-Enrollment-Forecast.pdf`) for 2008-2014 exactly. DLS disagrees with DPH for 2015
  (DLS 666, DPH 609; DPH used). DLS 1996 (808) is far outside its neighbors (600, 599) and has not
  been checked against a DPH report; it is flagged in the `note` column.
- NESDEC's table uses 459 for 2022 marked provisional; the final DPH figure is 482. NESDEC's 2023+
  values are its own estimates.
- 2023 and 2024 DPH reports exist on mass.gov but no archived copy was retrievable; not included.
- The NESDEC "~660 to ~500" statement compares its 2008-2017 average (about 659) with a projected
  average; the recorded series shows roughly 690 per year over 2008-2013, 590 over 2015-2019, and
  about 485 over 2020-2022.

## Raw files kept vs. not kept

The three decennial summary-file zips (about 200 MB each) and the national ACS `.dat` files (about
190-200 MB each) were downloaded to a scratch directory and not copied into Dropbox. The exact
Brookline rows, geo header lines, and layout documentation needed to reproduce every number are
saved under `data/demographics/`. Re-downloading from the URLs above and grepping for the LOGRECNO /
GEO_ID values listed reproduces the extracts.
