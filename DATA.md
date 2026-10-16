# Data in this repository

`data/SOURCES.md` is the full catalog of sources used in the project, with the document and page behind each figure. This file covers what's in `data/` here, what was changed before publishing, and what was left out.

## What `rebuild_all.py` reads

The rebuild reads only a small part of the original documents. The rest of its inputs are tables in `output/` that earlier scripts extracted from Town budget books, audits and state data. Those tables are included, so the rebuild runs from this repository as it is. The files in `data/` are:

| File | What it is |
|---|---|
| `2026 MA state new growth for all towns 20 years.xlsx` | New growth for every Massachusetts municipality over 20 years, from the Division of Local Services |
| `DLS_AvgSingleFamTaxBill.xlsx` | Average single-family tax bills by town, from the Division of Local Services |
| `bls_cache/CUURA103SA0.csv` | Boston-area consumer price index (CPI-U), monthly, from the Bureau of Labor Statistics |
| `census_bps/` | Census Bureau Building Permits Survey, annual place files for the Northeast, 1990 to 2025 |
| `census_cache/pl2010/`, `pl2020/` | 2010 and 2020 Census redistricting data (P.L. 94-171) for Massachusetts, town rows only (see below) |
| `demographics/acs5yr/` | American Community Survey 5-year tables for Massachusetts towns |
| `dese_enrollment/`, `dese_peers/` | Enrollment by district and grade, from the Massachusetts Department of Elementary and Secondary Education |
| `FY2026 Property Assessments….xlsx` | The Town Assessor's FY2026 property assessments (see below) |

## Changed before publishing

- **Property owners' names are blanked.** The FY2026 assessments list owners by name and mailing address. Those columns are kept but left empty, so the scripts run unchanged; none of them reads those columns.
- **The Census redistricting files are cut to town rows.** The originals are 55 to 110 MB each because they cover every census block. The scripts use only the town-level rows (summary level 060), so only those rows, and the matching records in the two data segments, are kept. The full files are on the Census Bureau's site under 2010 and 2020 "Redistricting Data (P.L. 94-171) Summary File", Massachusetts.
- **A few passages naming a specific development project are reworded** to describe it instead, as on the site.

## Left out

- **The building permit records.** The Town's Building Department supplied twenty years of permit records for this project, and they aren't published here. That leaves out the records themselves, the hand coding of how many homes each permit created or removed, and any output that lists individual permits. What remains are the results: homes added by year and type (`output/permit_homes_by_year.csv`, `output/permit_homes_mix.csv`) and the model's tables built from them. Three steps of `rebuild_all.py` read the records: the pace and mix of new homes, what permits say about the next two years, and how new homes show up in values and enrollment. In this copy they're skipped and their saved outputs are used, so the rest of the rebuild runs normally.
- **The original documents.** Budget books, audits, actuarial valuations, demographic studies and state reports, about 1.7 GB in all, are public but too large for this repository. `data/SOURCES.md` gives the Town or state address of each. They're needed only to rerun the extraction scripts whose results are already in `output/`.
- **One developer's project model** and the script and outputs built on it (`per_project_fiscal_impact`). It was shared privately.
- **The maps** at brooklinefuture.org/maps come from a separate parcel-level project that isn't in this repository. Three of its summary tables, which the forecast reads, are in `land-value-map/output/`.
- **Private working notes,** such as meeting notes and the author's decision log.
