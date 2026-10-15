"""
Resident births by Massachusetts city and town, 2005-2023, from MA DPH's annual birth reports.

Each report has one table of "Occurrence and Resident Births" for every municipality (Table 33 in
2005, Table 22 and 49 for 2011 and 2012, Table 17 from 2019, and so on). Its rows read
`Community  Occurrence-births  Resident-births  ...`; the resident count (births to mothers who live
in the town, wherever the birth happened) is the second number. The PDF reports are read with
`pdftotext -layout`; the 2020 (also a PDF), 2022 and 2023 Word reports are read cell by cell.

Town names are matched to the 351 official names used in output/ma_resident_births_by_town_2020_2023.csv,
ignoring case, spaces and punctuation, with a few spelling variants mapped explicitly.

Writes output/ma_resident_births_by_town_2005_2023.csv (town, year, resident_births, source_file)
and prints validation: towns per year, the sum against the report's STATE TOTAL, Brookline against
output/brookline_resident_births.csv, year-to-year jumps over 25% for Boston, Newton and Lexington,
and 2020 and 2023 against the earlier parse.

Run from scripts/:  python3 parse_town_births.py
"""
import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
D, B = ROOT / "data", ROOT / "data" / "demographics" / "births"
OUT = ROOT / "output" / "ma_resident_births_by_town_2005_2023.csv"
SOURCES = {
    2005: D / "birth-report-2005.pdf", 2006: D / "birth-report-2006.pdf", 2007: D / "birth-report-2007.pdf",
    2008: D / "birth-report-2008.pdf", 2009: D / "birth-report-2009.pdf", 2010: D / "birth-report-10.pdf",
    2011: D / "birth-report-2011-2012.pdf", 2012: D / "birth-report-2011-2012.pdf",
    2013: D / "birth-report-2013.pdf", 2014: D / "birth-report-2014.pdf", 2015: D / "birth-report-2015.pdf",
    2016: D / "2016-birth-report.pdf", 2017: D / "2017-birth-report-updated.pdf",
    2018: D / "2018-birth-report-040122.pdf", 2019: D / "2019-birth-report-100422.pdf",
    2020: D / "2020-birth-report.pdf", 2021: B / "DPH_2021_Birth_Report.pdf",
    2022: B / "DPH_2022_Birth_Report.docx", 2023: D / "MA-DPH-2023-Birth-Report.docx",
}
CANON = [r["town"] for r in csv.DictReader(open(ROOT / "output" / "ma_resident_births_by_town_2020_2023.csv"))]
key = lambda s: re.sub(r"[^a-z]", "", s.lower())
VARIANTS = {"manchesterbythesea": "Manchester", "northattleboro": "North Attleborough",
            "mtwashington": "Mount Washington", "boxboro": "Boxborough", "foxboro": "Foxborough",
            "southboro": "Southborough", "marlboro": "Marlborough", "westboro": "Westborough",
            "northboro": "Northborough", "attleboro": "Attleboro", "newmarlboro": "New Marlborough"}
LOOKUP = {key(t): t for t in CANON}
for k, v in VARIANTS.items():
    LOOKUP.setdefault(k, v)
NUM_TOK = re.compile(r"^(--\d*|[\d,]+)$")
ABBREV = [(r"^E\.\s*", "East "), (r"^W\.\s*", "West "), (r"^N\.\s*", "North "), (r"^S\.\s*", "South "),
          (r"^MT\.\s*", "Mount "), (r"^NO\.\s*", "North ")]


def canon(name):
    n = re.sub(r"\(.*?\)", "", name).strip()          # "Aquinnah (Gay Head)" -> "Aquinnah"
    for pat, rep in ABBREV:
        n = re.sub(pat, rep, n, flags=re.I)
    if key(n) == "gayhead":
        n = "Aquinnah"
    return LOOKUP.get(key(n))


def to_int(s):
    return None if s.startswith("--") else int(s.replace(",", ""))


def split_line(line):
    """(text part, numeric tokens) of a table line; footnote markers stay as tokens."""
    toks = line.split()
    j = 0
    while j < len(toks) and not NUM_TOK.match(toks[j]):
        j += 1
    return " ".join(toks[:j]), toks[j:]


def parse_pdf(path, year):
    lines = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                           capture_output=True, text=True).stdout.splitlines()
    starts = []
    for i, l in enumerate(lines):
        if l.strip().upper().startswith("STATE TOTAL"):
            title = " ".join(lines[max(0, i - 15):i])
            if f"Municipalities: {year}" in title and "Resident" in title and "Occurrence" in title:
                after = [x.strip().upper() for x in lines[i + 1:i + 6] if x.strip()]
                if after and after[0].startswith("ABINGTON"):
                    starts.append(i)
    if len(starts) != 1:
        raise SystemExit(f"{year}: {len(starts)} candidate municipality tables in {path.name}")
    i0 = starts[0]
    state_nums = split_line(lines[i0].replace("TOTAL4", "TOTAL"))[1]
    state = to_int(state_nums[1])
    body = [l.strip() for l in lines[i0 + 1:] if l.strip()]
    out, k = {}, 0
    while k < len(body) and len(out) < 351:
        text, nums = split_line(body[k])
        if body[k].startswith("NOTES") and len(out) > 300:
            break
        nxt_text, nxt_nums = split_line(body[k + 1]) if k + 1 < len(body) else ("", [])
        if text and len(nums) < 4 and not nxt_text and nxt_nums:
            # numbers on the next line: either all of them, when the name line carries only footnote
            # markers, all the same digit (2010: "ABINGTON 7 7", "BRIMFIELD 7 7 7"), or the rest of a
            # row that ran over (2009 Douglas: "2 101 --7", then the other four columns)
            footnotes = len(set(nums)) <= 1
            nums, k = (nxt_nums if footnotes else nums + nxt_nums), k + 1
        elif text and not nums and nxt_text and len(nxt_nums) >= 4 and canon(text) is None \
                and canon(text + " " + nxt_text):
            # first word of a name on its own line, the rest with the numbers ("GREAT" / "BARRINGTON ...")
            text, nums, k = text + " " + nxt_text, nxt_nums, k + 1
        town = canon(text) if text else None
        if text and len(nums) >= 4 and town is None and nxt_text and not nxt_nums:
            town, k = canon(text + " " + nxt_text), k + 1   # name wrapped onto the next line
        if town and len(nums) >= 4 and town not in out:
            out[town] = to_int(nums[1])
        k += 1
    return out, state


def parse_docx(path, year):
    import docx
    doc = docx.Document(str(path))
    out, state = {}, None
    title = f"Occurrence and Resident Births, Massachusetts Municipalities: {year}"
    for t in doc.tables:
        if title not in " ".join(c.text for c in t.rows[0].cells):
            continue
        for row in t.rows:
            cells = [c.text.strip() for c in row.cells]
            if len(cells) < 3 or not NUM_TOK.match(cells[2].replace(" ", "") or "x"):
                continue
            if cells[0].upper().startswith("STATE TOTAL") and state is None:
                state = to_int(cells[2])
            town = canon(cells[0])
            if town and town not in out:
                out[town] = to_int(cells[2])
    return out, state


def main():
    rows, report = [], {}
    for year, path in SOURCES.items():
        data, state = (parse_docx if path.suffix == ".docx" else parse_pdf)(path, year)
        report[year] = (data, state, path.name)
        for town in CANON:
            if town in data:
                rows.append(dict(town=town, year=year, resident_births=data[town], source_file=path.name))
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["town", "year", "resident_births", "source_file"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT.name}: {len(rows)} rows\n")

    brook = {int(r["year"]): int(r["resident_births"]) for r in csv.DictReader(open(ROOT / "output" / "brookline_resident_births.csv"))}
    print("year  towns  missing  suppressed  sum     report  diff  Brookline (here / existing series)")
    for year, (data, state, name) in report.items():
        vals = [v for v in data.values() if v is not None]
        missing = [t for t in CANON if t not in data]
        print(f"{year}  {len(data):5d}  {len(missing):7d}  {sum(v is None for v in data.values()):10d}  {sum(vals):6d}  "
              f"{state or 0:6d}  {sum(vals) - (state or 0):+5d}  {data.get('Brookline')} / {brook.get(year)}"
              + (f"   missing: {missing[:6]}" if missing else ""))
    old = {(r["town"], y): int(r[f"resident_births_{y}"]) for r in csv.DictReader(open(ROOT / "output" / "ma_resident_births_by_town_2020_2023.csv"))
           for y in (2020, 2023) if r.get(f"resident_births_{y}")}
    for y in (2020, 2023):
        diffs = [(t, report[y][0].get(t), v) for (t, yy), v in old.items() if yy == y and report[y][0].get(t) != v]
        print(f"\n{y} against the earlier parse: {len(diffs)} differences {diffs[:8]}")
    for t in ("Boston", "Newton", "Lexington", "Brookline"):
        s = {y: report[y][0].get(t) for y in report}
        jumps = [(y, s[y - 1], s[y]) for y in s if y - 1 in s and s[y] and s[y - 1] and abs(s[y] / s[y - 1] - 1) > 0.25]
        print(f"{t}: jumps over 25%: {jumps or 'none'}")


if __name__ == "__main__":
    main()
