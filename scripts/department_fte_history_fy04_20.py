"""
Town department headcount, FY2004-2020 (General Fund only) - extends
department_fte_annual_history.py's FY2021-2027 series back to 2004,
using historical Financial Plans not previously in this project's `data/`
folder.

Added 2026-09-02 (Ben: "I'd love town FTEs back to 2005 - I think there
has been some concern about actual staffing levels"). Found and fetched
from the Town's Budget Central archive (brooklinema.gov/851/Budget-
Central, which goes back to FY2001): the FY2006, FY2008, FY2010, FY2012,
FY2015, FY2018, and FY2020 Financial Plans each carry the same kind of
"Full-Time Equivalent (FTE) Positions Funded" table as the modern plans -
just in the pre-OpenGov format, with GENERAL FUND and NON-GENERAL FUND
reported separately rather than as one "All Positions" table.

## Scope: General Fund only, not "All Positions"

`department_fte_annual_history.py`'s FY2021-2027 series is "All
Positions" (General Fund + Capital/Grants/Enterprise-funded). This file
uses **General Fund only** - the metric consistently available across
every historical document - which turns out to be the SAME concept the
modern plans report as **"Net General Funded Positions"** (verified: the
FY2026 and FY2027 Financial Plans' own "Net General Funded Positions"
rows agree exactly for every overlapping year, FY2023-2026). So this
script's FY2004-2020 series and that same "Net General Funded Positions"
metric for FY2022-2027 form one genuinely continuous, same-scope 24-year
series - see `read_modern_net_general_fund()` below.

**FY2021 has a real gap**: no available document reports "Net General
Funded Positions" for FY2021 specifically (the FY2025 Plan's own
Capital/Grants breakdown is only for its own current year, FY2025; the
FY2026 Plan's earliest column is FY2022). Left blank, not estimated.

## Verification and a real, more significant finding than the FY2025
## discontinuity already found in the FY2021-2027 series

Each document's own top-level department rows were checked against its
own stated GENERAL FUND TOTAL (see `verify_doc()`) - all pass exactly.
**Two structural things had to be caught before that check would even
work**: "Finance" and "Public Works" are themselves SUBTOTAL header rows
in every one of these documents (Finance = Comptroller + Purchasing +
Assessor + Treasurer/Collector; Public Works = Administration +
Engineering/Transportation + Highway + Sanitation + Parks and Open
Space) - summing the sub-lines AND the header would double-count. Caught
by first assuming a flat list and finding the computed total didn't
match the stated total by exactly the value of one sub-total row.

**A real, disclosed limitation, more significant than the FY2025
recommended-vs-settled gap already found**: comparing the SAME year
(FY2015) as reported by two DIFFERENT later documents (FY2018 Plan says
680.01; FY2020 Plan says 676.39) shows they don't agree with each other
either - not just with the FY2015 Plan's own original figure (677.69).
Tracing the department-level cells shows real reclassification, not just
refinement, between documents (HR, IT, Finance, Town Clerk, Planning,
Building, Health, and the Human Relations/DEICR row all differ). This
project's usual "prefer the latest available document" rule is still
applied here (consistent with the rest of this project), but the
resulting FY2004-2020 department-level cells should be read as
reasonably solid *category and townwide trends*, not exact-to-the-tenth
figures for any single department in any single older year - a real,
different (and larger) kind of noise than the cleaner FY2021-2027 series.

**A larger, more important version of the same thing at FY2006-2007,
worth calling out on its own, not buried in the general caveat above.**
The FY2006 and FY2008 Plans - two documents published close in time -
agree with each other on FY2006 and FY2007 (GENERAL FUND TOTAL 679.80/
682.08 and 680.69 respectively). The FY2010 and FY2012 Plans - published
later - agree with EACH OTHER on the same two years, but at meaningfully
higher levels (705.52 for FY2006, 702.73 for FY2007) - roughly +23-25
FTE, not the few-FTE noise seen elsewhere. Tracing which departments
moved: Library (+9.6, 43.74→53.33), Public Works (+7.5, 138.50→146.01),
and Police (+5.8, 173.00→178.79) account for almost all of it, all
jumping together at the same document boundary. This has the signature
of a scope/counting-methodology change made once (probably introduced in
the FY2010 Plan, whose own budget message discusses a hiring freeze and
retirement-incentive program that year - a plausible trigger for revising
how positions are counted) and then carried forward consistently by
every later document, rather than 23 real positions actually being added
in one year and then found later. **Not resolved or picked a side on
here** - both pairs of documents are internally consistent with
themselves, and this project has no independent way to determine which
convention is "more correct" for FY2006-2007 specifically. Flagged
directly rather than silently smoothed into the trend line - a reader
looking at the FY2004-2009 portion of this series should read the
FY2006 uptick as **likely a reporting-convention change, not a real
staffing event**, until/unless a document explaining the change is
found.

## Two departments that changed identity mid-series

- **Planning absorbed "Economic Development"** as its own line
  sometime around FY2009 - the FY2006/FY2008 Plans still show it
  separately; every later plan folds it into Planning. Merged into
  `planning` for FY2004-2005 (the only years not covered by any later,
  already-merged document); the "prefer latest" rule handles FY2006-2008
  automatically since later documents already show it merged.
- **The same table row is "Human Relations/Youth Resources" through
  ~FY2013, then "Diversity, Inclusion and Cmty Relations" (DEICR) from
  ~FY2015 on** (per the FY2018 Plan's own footnote: "In FY14, FTEs were
  accounted for in the Dept. of Health and Human Services"). Kept as two
  separate canonical fields (`human_relations_youth`, `deicr`), each
  populated only in the years it was that department, rather than forcing
  one continuous row across an actual identity change.

Outputs:
  ../output/town_fte_general_fund_fy04_27.csv       (headline: one number/year)
  ../output/department_fte_general_fund_fy04_20.csv  (department detail)
  ../output/department_fte_category_fy04_20.csv      (5-category rollup)
  ../output/department_fte_history_fy04_20_notes.md
"""
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_TOTAL_CSV = ROOT / "output/town_fte_general_fund_fy04_27.csv"
OUT_DEPT_CSV = ROOT / "output/department_fte_general_fund_fy04_20.csv"
OUT_CAT_CSV = ROOT / "output/department_fte_category_fy04_20.csv"
NOTES_FILE = ROOT / "output/department_fte_history_fy04_20_notes.md"

CATEGORY = {
    "select_board": "general_government", "human_resources": "general_government",
    "information_technology": "general_government", "finance": "general_government",
    "legal": "general_government", "advisory": "general_government",
    "town_clerk": "general_government", "planning": "general_government",
    "building": "general_government", "deicr": "general_government",
    "police": "public_safety", "fire": "public_safety",
    "public_works": "public_works",
    "library": "culture_recreation", "recreation": "culture_recreation",
    "health": "human_services", "veterans": "human_services",
    "coa": "human_services", "human_relations_youth": "human_services",
}
CATEGORY_LABELS = {
    "general_government": "General Government", "public_safety": "Public Safety",
    "public_works": "Public Works", "human_services": "Human Services",
    "culture_recreation": "Culture & Recreation",
}
DEPT_KEYS = list(CATEGORY.keys())

# Each doc: (name, years, {dept: [values]}, stated_general_fund_total, all_funds_total)
# Source: brooklinema.gov/851/Budget-Central, each fiscal year's own
# "Financial Plan (Complete Document)" PDF, "FULL-TIME EQUIVALENT (FTE)
# POSITIONS FUNDED" section. All top-level rows only (Finance and Public
# Works are subtotal headers - see module docstring).
DOCS = [
    dict(name="FY2006 Plan", years=[2004, 2005, 2006], all_funds=[742.54, 740.01, 742.26],
         stated_total=[684.15, 679.52, 679.80], dept=dict(
        select_board=[7.53, 7.53, 7.53], human_resources=[5.00, 5.00, 5.00],
        information_technology=[14.50, 11.50, 11.50], finance=[32.55, 32.55, 32.30],
        legal=[6.20, 6.20, 6.20], advisory=[0.50, 0.50, 0.50], town_clerk=[6.00, 6.00, 6.50],
        planning=[10.33 + 1.81, 10.33 + 1.93, 10.33 + 1.96],  # merged w/ Economic Development
        police=[173.00, 173.00, 173.00], fire=[168.00, 168.00, 168.00],
        building=[34.55, 34.55, 34.55], public_works=[138.80, 138.50, 138.50],
        library=[42.20, 42.20, 42.20], health=[12.35, 11.90, 11.90],
        veterans=[2.00, 2.00, 2.00], coa=[12.43, 11.83, 11.83],
        human_relations_youth=[2.30, 2.00, 2.00], recreation=[14.10, 14.00, 14.00],
        deicr=[0, 0, 0],
    )),
    dict(name="FY2008 Plan", years=[2006, 2007, 2008], all_funds=[744.86, 742.78, 731.96],
         stated_total=[682.08, 680.69, 669.77], dept=dict(
        select_board=[7.53, 7.00, 7.00], human_resources=[5.00, 5.00, 5.00],
        information_technology=[11.50, 11.50, 11.50], finance=[32.30, 31.63, 31.21],
        legal=[6.41, 6.64, 6.64], advisory=[1.00, 1.00, 1.00], town_clerk=[6.50, 6.00, 6.00],
        planning=[10.33 + 1.96, 11.33 + 2.00, 11.33 + 2.00],
        police=[173.00, 173.00, 171.00], fire=[168.00, 168.00, 166.00],
        building=[34.55, 33.17, 33.17], public_works=[138.50, 138.50, 135.00],
        library=[43.74, 44.16, 43.16], health=[11.93, 11.93, 11.93],
        veterans=[2.00, 2.00, 2.00], coa=[11.83, 11.83, 11.83],
        human_relations_youth=[2.00, 2.00, 2.00], recreation=[14.00, 14.00, 12.00],
        deicr=[0, 0, 0],
    )),
    dict(name="FY2010 Plan", years=[2006, 2007, 2008, 2009, 2010],
         all_funds=[782.56, 779.47, 771.41, 769.12, 755.34],
         stated_total=[705.52, 702.73, 692.07, 689.37, 675.70], dept=dict(
        select_board=[7.53, 7.00, 7.00, 7.00, 6.53], human_resources=[5.00] * 5,
        information_technology=[11.40] * 5, finance=[32.10, 31.43, 31.01, 30.43, 30.43],
        legal=[6.41, 6.64, 6.64, 6.64, 6.53], advisory=[0.35] * 5,
        town_clerk=[6.50, 6.00, 6.00, 6.00, 6.00],
        planning=[12.29, 13.33, 13.33, 13.33, 11.86],
        police=[178.79, 178.79, 177.78, 178.78, 177.30],
        fire=[168.00, 168.00, 168.00, 168.00, 161.00],
        building=[34.55, 33.17, 33.17, 33.41, 33.01],
        public_works=[146.01, 146.01, 139.86, 135.86, 134.86],
        library=[53.33, 53.75, 52.75, 52.75, 52.75],
        health=[13.43, 12.03, 11.83, 11.83, 11.83],
        veterans=[2.00] * 5, coa=[11.83, 11.83, 11.95, 12.59, 11.85],
        human_relations_youth=[2.00, 2.00, 2.00, 2.00, 1.00],
        recreation=[14.00, 14.00, 12.00, 12.00, 12.00], deicr=[0] * 5,
    )),
    dict(name="FY2012 Plan", years=[2007, 2008, 2009, 2010, 2011, 2012],
         all_funds=[779.47, 771.46, 768.20, 752.66, 750.59, 751.13],
         stated_total=[702.73, 692.07, 689.40, 675.97, 672.60, 671.57], dept=dict(
        select_board=[7.00, 7.00, 7.00, 6.53, 6.53, 6.48], human_resources=[5.00] * 6,
        information_technology=[11.40] * 6,
        finance=[31.43, 31.01, 30.43, 30.43, 30.43, 29.22],
        legal=[6.64, 6.64, 6.64, 6.53, 6.53, 6.53], advisory=[0.35] * 6,
        town_clerk=[6.00] * 6, planning=[13.33, 13.33, 13.33, 12.10, 12.33, 12.33],
        police=[178.79, 177.78, 178.78, 177.30, 178.30, 178.30],
        fire=[168.00, 168.00, 168.00, 161.00, 161.00, 161.00],
        building=[33.17, 33.17, 33.41, 33.01, 31.93, 31.93],
        public_works=[146.01, 139.86, 135.86, 134.86, 131.86, 131.29],
        library=[53.75, 52.75, 52.75, 52.75, 51.75, 51.75],
        health=[12.03, 11.83, 11.83, 11.83, 11.83, 12.83],
        veterans=[2.00] * 6, coa=[11.83, 11.95, 12.62, 11.88, 12.36, 12.16],
        human_relations_youth=[2.00, 2.00, 2.00, 1.00, 1.00, 1.00],
        recreation=[14.00, 12.00, 12.00, 12.00, 12.00, 12.00], deicr=[0] * 6,
    )),
    dict(name="FY2015 Plan", years=[2010, 2011, 2012, 2013, 2014, 2015],
         all_funds=[746.69, 744.39, 743.90, 745.30, 749.10, 751.16],
         stated_total=[676.26, 672.66, 671.45, 674.39, 676.39, 677.69], dept=dict(
        select_board=[6.53, 6.53, 6.48, 6.48, 6.48, 6.48],
        human_resources=[5.00, 5.00, 5.00, 5.00, 5.00, 5.98],
        information_technology=[11.40] * 6, finance=[30.43, 30.43, 29.04, 29.04, 29.04, 29.16],
        legal=[6.53] * 6, advisory=[0.35, 0.35, 0.35, 0.35, 0.40, 0.40],
        town_clerk=[6.00, 6.00, 6.00, 6.00, 6.00, 5.00],
        planning=[12.39, 12.39, 12.39, 12.60, 12.60, 12.80],
        police=[177.30, 178.30, 178.30, 178.30, 178.30, 178.30],
        fire=[161.00] * 6, building=[33.01, 31.93, 31.93, 32.93, 33.42, 35.42],
        public_works=[134.86, 131.86, 131.29, 132.58, 133.08, 133.08],
        library=[52.75, 51.75, 51.75, 51.75, 51.75, 51.75],
        health=[11.83, 11.83, 12.83, 12.83, 14.62, 14.62],
        veterans=[2.00] * 6, coa=[11.88, 12.36, 12.16, 12.60, 12.77, 12.77],
        human_relations_youth=[1.00, 1.00, 1.00, 1.00, 0.00, 0.00],
        recreation=[12.00, 12.00, 12.00, 12.00, 12.00, 11.00], deicr=[0] * 6,
    )),
    dict(name="FY2018 Plan", years=[2013, 2014, 2015, 2016, 2017, 2018],
         all_funds=[745.30, 749.10, 753.63, 754.76, 753.98, 754.48],
         stated_total=[674.39, 676.39, 680.01, 682.14, 678.62, 678.37], dept=dict(
        select_board=[6.48] * 6, human_resources=[5.00, 5.00, 5.98, 5.98, 5.98, 5.98],
        information_technology=[11.40, 11.40, 12.40, 12.00, 12.00, 12.00],
        finance=[29.04, 29.04, 29.16, 30.22, 30.22, 30.22], legal=[6.53] * 6,
        advisory=[0.35, 0.40, 0.40, 0.40, 0.40, 0.40], town_clerk=[6.00, 6.00, 5.50, 5.50, 5.50, 5.50],
        planning=[12.60, 12.60, 12.80, 12.80, 11.80, 11.80],
        police=[178.30, 178.30, 178.30, 179.30, 179.30, 179.30],
        fire=[161.00, 161.00, 161.00, 161.00, 160.00, 160.00],
        building=[32.93, 33.42, 35.42, 35.42, 36.90, 36.90],
        public_works=[132.58, 133.08, 133.08, 133.38, 130.38, 130.38],
        library=[51.75, 51.75, 51.75, 51.75, 51.75, 51.50],
        health=[12.83, 14.62, 12.62, 12.62, 12.62, 12.62],
        veterans=[2.00] * 6, coa=[12.60, 12.77, 12.87, 13.04, 13.04, 13.04],
        human_relations_youth=[1.00, 0.00, 0, 0, 0, 0],
        deicr=[0, 0, 2.72, 2.72, 2.72, 2.72],
        recreation=[12.00, 12.00, 11.00, 11.00, 11.00, 11.00],
    )),
    dict(name="FY2020 Plan", years=[2015, 2016, 2017, 2018, 2019, 2020],
         all_funds=[749.10, 753.63, 756.31, 755.48, 763.51, 769.19],
         stated_total=[676.39, 680.01, 683.69, 680.69, 685.69, 687.37], dept=dict(
        select_board=[6.48] * 6, human_resources=[5.00, 5.98, 5.78, 5.78, 5.78, 5.78],
        information_technology=[11.40, 12.40, 12.40, 12.40, 12.40, 12.40],
        finance=[29.04, 29.16, 30.22, 30.22, 31.22, 31.22], legal=[6.53, 6.53, 6.53, 6.53, 7.03, 7.71],
        advisory=[0.40] * 6, town_clerk=[6.00, 5.50, 5.50, 5.50, 5.50, 5.50],
        planning=[12.60, 12.80, 12.80, 11.80, 13.00, 13.00],
        police=[178.30, 178.30, 179.30, 180.30, 180.80, 180.80],
        fire=[161.00, 161.00, 161.00, 160.00, 160.00, 160.00],
        building=[33.42, 35.42, 35.90, 36.90, 36.61, 37.61],
        public_works=[133.08, 133.08, 133.38, 130.38, 130.38, 130.38],
        library=[51.75, 51.75, 51.75, 51.75, 52.84, 52.84],
        health=[14.62, 12.62, 12.62, 12.62, 12.62, 12.62],
        veterans=[2.00] * 6, coa=[12.77, 12.87, 13.91, 13.91, 13.91, 13.91],
        human_relations_youth=[0, 0, 0, 0, 0, 0],
        deicr=[0.00, 2.72, 2.72, 2.72, 2.72, 2.72],
        recreation=[12.00, 11.00, 11.00, 11.00, 12.00, 12.00],
    )),
]

# "Net General Funded Positions" from the modern (FY2025-2027) Financial
# Plans - the SAME scope as this file's "GENERAL FUND TOTAL." Verified:
# FY2026 and FY2027 Plans agree exactly on every overlapping year
# (FY2023-2026). FY2021 has no available figure in this scope (see
# module docstring) - left out.
MODERN_NET_GENERAL_FUND = {
    2022: 708.49, 2023: 712.04, 2024: 714.53, 2025: 682.99, 2026: 675.63, 2027: 663.96,
}


def verify_doc(doc):
    for i, y in enumerate(doc["years"]):
        computed = round(sum(doc["dept"][k][i] for k in DEPT_KEYS), 2)
        stated = doc["stated_total"][i]
        assert abs(computed - stated) < 0.02, \
            f"{doc['name']} FY{y}: computed {computed} != stated {stated}"


def main():
    for doc in DOCS:
        verify_doc(doc)
    print(f"All {len(DOCS)} historical documents verified against their own stated GENERAL FUND TOTAL.")

    # Merge: prefer the latest-published document available for each year
    # (same rule used throughout this project - a later document reflects
    # more settled/reclassified data than an earlier one's same-year figure).
    all_years = sorted({y for doc in DOCS for y in doc["years"]})
    merged_dept = {k: {} for k in DEPT_KEYS}
    merged_source = {}
    for doc in DOCS:  # DOCS is already in chronological order - later overwrites earlier
        for i, y in enumerate(doc["years"]):
            for k in DEPT_KEYS:
                merged_dept[k][y] = doc["dept"][k][i]
            merged_source[y] = doc["name"]

    # Department-level output
    dept_rows = []
    for y in all_years:
        row = dict(fiscal_year=y, source=merged_source[y])
        for k in DEPT_KEYS:
            row[k] = merged_dept[k][y]
        row["general_fund_total"] = round(sum(merged_dept[k][y] for k in DEPT_KEYS), 2)
        dept_rows.append(row)
    with open(OUT_DEPT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["fiscal_year", "source"] + DEPT_KEYS + ["general_fund_total"])
        w.writeheader()
        w.writerows(dept_rows)
    print(f"Wrote {OUT_DEPT_CSV} ({len(dept_rows)} years x {len(DEPT_KEYS)} departments)")

    # Category rollup
    cat_rows = []
    for y in all_years:
        row = dict(fiscal_year=y)
        for cat in CATEGORY_LABELS:
            row[cat] = round(sum(merged_dept[k][y] for k in DEPT_KEYS if CATEGORY[k] == cat), 2)
        cat_rows.append(row)
    with open(OUT_CAT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["fiscal_year"] + list(CATEGORY_LABELS.keys()))
        w.writeheader()
        w.writerows(cat_rows)
    print(f"Wrote {OUT_CAT_CSV}")

    # Headline: one continuous General-Fund-FTE-total series, FY2004-2027
    total_rows = []
    for y in all_years:
        total_rows.append(dict(fiscal_year=y, general_fund_fte_total=round(sum(merged_dept[k][y] for k in DEPT_KEYS), 2),
                                source=merged_source[y]))
    for y in sorted(MODERN_NET_GENERAL_FUND):
        total_rows.append(dict(fiscal_year=y, general_fund_fte_total=MODERN_NET_GENERAL_FUND[y],
                                source="Net General Funded Positions, FY2026/FY2027 Financial Plans"))
    total_rows.sort(key=lambda r: r["fiscal_year"])
    with open(OUT_TOTAL_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["fiscal_year", "general_fund_fte_total", "source"])
        w.writeheader()
        w.writerows(total_rows)
    print(f"Wrote {OUT_TOTAL_CSV} ({len(total_rows)} years)")
    print("  NOTE: FY2021 has no available General-Fund-only figure in any source document - gap, not estimated.")

    first, last = total_rows[0], total_rows[-1]
    n_years = last["fiscal_year"] - first["fiscal_year"]
    cagr = (last["general_fund_fte_total"] / first["general_fund_fte_total"]) ** (1 / n_years) - 1
    print(f"  FY{first['fiscal_year']}: {first['general_fund_fte_total']:.2f} -> "
          f"FY{last['fiscal_year']}: {last['general_fund_fte_total']:.2f} "
          f"({cagr:+.2%}/yr over {n_years} years)")

    write_notes(dept_rows, total_rows)
    print(f"Wrote {NOTES_FILE}")


def write_notes(dept_rows, total_rows):
    lines = []
    lines.append("# Town General Fund FTE History, FY2004-2027\n")
    lines.append(
        "Source: `data/FY2006/2008/2010/2012/2015/2018/2020-Financial-Plan.pdf` (fetched from the "
        "Town's Budget Central archive, brooklinema.gov/851/Budget-Central, which goes back to FY2001) "
        "plus the \"Net General Funded Positions\" row already used in the FY2026/FY2027 Financial Plans "
        "for FY2022-2027. Added 2026-09-02 (Ben: \"I'd love town FTEs back to 2005 - I think there has "
        "been some concern about actual staffing levels\"). See this script's own module docstring for "
        "the full verification methodology, the Finance/Public Works subtotal-header discovery, and a "
        "real, disclosed finding: unlike the cleaner FY2021-2027 series, department-level figures for "
        "older years show genuine reclassification between documents (not just recommended-vs-settled "
        "refinement) - treat category/townwide trends as solid, individual older-year department figures "
        "as approximate.\n"
    )
    lines.append("## Headline: General Fund FTE total, FY2004-2027\n")
    lines.append("| Fiscal Year | General Fund FTE | Source |")
    lines.append("|---:|---:|---|")
    for r in total_rows:
        lines.append(f"| FY{r['fiscal_year']} | {r['general_fund_fte_total']:.2f} | {r['source']} |")
    lines.append("")
    first, last = total_rows[0], total_rows[-1]
    n_years = last["fiscal_year"] - first["fiscal_year"]
    cagr = (last["general_fund_fte_total"] / first["general_fund_fte_total"]) ** (1 / n_years) - 1
    lines.append(
        f"**FY{first['fiscal_year']}→FY{last['fiscal_year']}: {first['general_fund_fte_total']:.2f} → "
        f"{last['general_fund_fte_total']:.2f} FTE ({cagr:+.2%}/yr over {n_years} years).** FY2021 has no "
        "available figure in this scope (General Fund only) - no source document reports it; left as a "
        "gap rather than estimated.\n"
    )
    lines.append(
        "**Read the FY2006 uptick (679.52 → 705.52) with real caution - likely a reporting-convention "
        "change, not a staffing event.** The FY2006/FY2008 Plans agree with each other on FY2006-2007; the "
        "FY2010/FY2012 Plans (published later) agree with each other too, but ~23-25 FTE higher for the "
        "SAME years. Library (+9.6), Public Works (+7.5), and Police (+5.8) account for almost all of it, "
        "jumping together at the same document boundary - the signature of a scope/counting change (the "
        "FY2010 Plan's own budget message discusses a hiring freeze and retirement-incentive program that "
        "year), not 23 real positions added in one year. Not resolved here - both document pairs are "
        "internally consistent with themselves; see this script's module docstring for the full reasoning.\n"
    )
    lines.append(
        "## What this deliberately does not do\n\n"
        "- **General Fund only, not \"All Positions\"** - see `department_fte_annual_history.py`'s "
        "FY2021-2027 series for the broader (Capital/Grants/Enterprise-inclusive) scope; the two datasets "
        "are complementary, not merged, since exact department-level reconciliation between the two scopes "
        "isn't cleanly available for every year.\n"
        "- **No pre-FY2004 data** - FY2004 is the earliest year with a complete department table in any "
        "document currently fetched; the archive's FY2001-2003 entries only had Long Range Financial Plan "
        "and CIP documents, not the full Program Budget with an FTE table, at least among what's been "
        "checked so far.\n"
        "- **Older-era department-level figures carry more real noise than the modern series** - see the "
        "FY2015 example in the module docstring (680.01 vs. 676.39 across two different later documents).\n"
    )
    with open(NOTES_FILE, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
