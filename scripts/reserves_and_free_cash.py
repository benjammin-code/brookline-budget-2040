"""
Brookline's reserves and free cash, with statewide context.

Why this exists (2026-09-13, Ben: "we should absolutely map out the reserves
over time"): the project had no reserve data at all. Reserves are one of the
three things that actually close a budget gap in practice, alongside overrides
and cuts, and they are what municipal credit ratings turn on. This assembles
the series from primary sources so the reference document can carry it.

Everything here is CITED data, not modelled. Nothing is derived from this
project's own forecasts.

## Four different things, which must not be conflated

1. **Unassigned general fund balance** - the GAAP residual after nonspendable,
   restricted, committed and assigned amounts. From the audited financial
   statements.
2. **Total general fund balance** - all five categories.
3. **Available fund balance** - Moody's term, meaning committed + assigned +
   unassigned. **For Brookline this equals total GF balance**, because the
   General Fund carries zero nonspendable, restricted and committed balances
   in every year from FY2016 on. This is the figure that belongs in any peer
   or rating comparison, and it is roughly 7.6 points higher than unassigned.
4. **Certified free cash** - the July 1 balance certified annually by the DLS
   Director of Accounts, after deductions the fund balance figures do not make.
   Roughly half to two-thirds of unassigned fund balance in Brookline's case.

## Two labelling traps

**Free cash year labels differ between DLS and the Town.** DLS labels free
cash by the fiscal year that *begins* on that July 1. Brookline's own budget
documents label the same dollars one year later, because the Town appropriates
them in the budget adopted the following spring. **Brookline budget FY = DLS
FY + 1.** The series below uses the DLS convention throughout and states the
as-of date explicitly so the ambiguity cannot propagate.

**GASB 54 broke the fund balance series at FY2011.** Before FY2011 there was
no "unassigned" category; the closest analogue is undesignated fund balance.
The apparent jump from $11.9M (FY2010) to $22.6M (FY2011) is a reclassification,
not a real change. Pre-FY2011 figures are carried here flagged as a different
basis, and **no trend line should cross that boundary.**

## Sources

- Fund balance FY2011-FY2024: Brookline Audited Financial Statements, the
  Governmental Funds balance sheet, General Fund column. Percentages use total
  General Fund revenues from the Statement of Revenues, Expenditures and
  Changes in Fund Balances. Reproduces the 2020 BFAC report's FY2014-FY2019
  figures to the cent.
- **There is no FY2025 audit.** Verified three ways as of 2026-09-13,
  including the Town's own statement in the FY2027 Financial Plan that FY25
  free cash was uncertified at printing. FY2024 is the most recent audited year.
- Certified free cash: MA DLS Databank, "Certified Free Cash as Percent of
  Budget," cross-checked against the signed DLS certification worksheets.
- Statewide free cash: same DLS report, summed across all municipalities.
  DLS publishes no statewide total itself; the FY2026 sum reconciles to the
  $2.88 billion DLS reported narratively in June 2026.

## The Town's own reserve policy

The FY2027 Financial Plan states two different targets. The narrative Free
Cash section gives 10% of revenue; the formal Reserve Policies in the Appendix
state **"no less than 20% of revenue, with a goal of accruing a balance that
falls within the median of Massachusetts Aaa rated communities,"** attributed
to changes in Moody's metrics. The Appendix policy is the governing text and
the narrative appears stale, so 20% is used here as the policy line.

Moody's February 2024 credit opinion names its own downgrade trigger as
available reserves falling below 20% of revenue, so the Town's policy and the
agency's trigger sit at the same number.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_CSV = ROOT / "output" / "reserves_and_free_cash.csv"
OUT_STATEWIDE = ROOT / "output" / "statewide_fiscal_context.csv"
OUT_METHOD = ROOT / "output" / "reserves_and_free_cash_methodology.md"

POLICY_FLOOR_PCT = 20.0          # Town's own Appendix policy, and Moody's trigger
MOODYS_AAA_MEDIAN_PCT = 61.7     # available fund balance, Moody's Aaa median, FY2022 basis

# --- Audited fund balance. GASB 54 basis from FY2011; undesignated before. ---
# (fiscal_year, gf_revenues, unassigned_or_undesignated, total_gf_balance, basis)
FUND_BALANCE = [
    (2005, 164_625_253, 11_601_326, 34_134_572, "pre-GASB54 undesignated"),
    (2006, 172_364_174, 12_093_785, 33_979_770, "pre-GASB54 undesignated"),
    (2007, 181_192_264, 13_823_065, 31_315_811, "pre-GASB54 undesignated"),
    # FY2008 unavailable: the posted audit is a scanned image with no text layer.
    (2009, 200_490_973, 12_604_133, 34_393_035, "pre-GASB54 undesignated"),
    (2010, 221_305_104, 11_883_429, 17_922_815, "pre-GASB54 undesignated"),
    (2011, 207_316_794, 22_555_076, 23_524_048, "GASB54 unassigned"),
    (2012, 214_335_236, 24_801_047, 26_011_676, "GASB54 unassigned"),
    (2013, 224_539_297, 25_833_833, 27_228_813, "GASB54 unassigned"),
    (2014, 231_681_263, 23_869_182, 26_119_762, "GASB54 unassigned"),
    (2015, 232_768_875, 22_575_235, 24_550_001, "GASB54 unassigned"),
    (2016, 250_639_214, 21_345_882, 28_845_026, "GASB54 unassigned"),
    (2017, 276_868_700, 23_389_047, 33_692_444, "GASB54 unassigned"),
    (2018, 292_694_224, 24_727_247, 35_714_611, "GASB54 unassigned"),
    (2019, 308_315_673, 26_644_817, 37_896_203, "GASB54 unassigned"),
    (2020, 330_590_974, 26_581_341, 40_441_167, "GASB54 unassigned"),
    (2021, 346_323_000, 29_546_526, 43_087_065, "GASB54 unassigned"),
    (2022, 360_568_660, 48_950_028, 62_365_358, "GASB54 unassigned"),
    (2023, 371_052_408, 62_448_328, 78_428_843, "GASB54 unassigned"),
    (2024, 391_949_512, 60_069_432, 89_795_433, "GASB54 unassigned"),
]

# --- Certified free cash, DLS fiscal-year convention (as of July 1 of prior FY close) ---
FREE_CASH = {
    2005: 4_606_534, 2006: 5_387_435, 2007: 3_814_792, 2008: 5_954_963,
    2009: 7_053_295, 2010: 4_590_079, 2011: 7_105_288, 2012: 7_086_413,
    2013: 9_654_859, 2014: 7_084_861, 2015: 7_569_881, 2016: 7_811_538,
    2017: 10_854_017, 2018: 11_151_363, 2019: 11_881_257, 2020: 14_392_269,
    2021: 13_001_890, 2022: 14_206_813, 2023: 22_787_495, 2024: 25_122_386,
    2025: 24_032_596, 2026: 21_094_133,
}

# --- Statewide context. Each row is sourced in the methodology doc. ---
STATEWIDE_FREE_CASH = {
    2017: 1_642_896_773, 2018: 1_710_818_696, 2019: 1_754_022_910,
    2020: 1_915_169_481, 2021: 1_950_974_770, 2022: 2_334_348_411,
    2023: 2_648_040_148, 2024: 2_758_210_481, 2025: 3_022_624_079,
    2026: 2_889_886_294,
}

# General (permanent) operating overrides only. Debt and capital exclusions are
# separate DLS series and are NOT included - they run 52-88 municipalities a
# year at 80-95% pass rates, i.e. they are the routine tool, not the
# exceptional one.
OVERRIDES = [
    # fy, municipalities, questions, requested, approved, pass_rate_pct
    (2017, 21, 26, 19_081_524, 3_900_000, 54),
    (2018, 18, 20, 12_100_000, 8_800_000, 60),
    (2019, 26, 44, 40_100_000, 31_400_000, 82),
    (2020, 26, 29, 35_900_000, 33_300_000, 76),
    (2021, 14, 21, 17_500_000, 10_700_000, 57),
    (2022, 14, 22, 28_300_000, 19_200_000, 86),
    (2023, 12, 22, 19_500_000, 6_800_000, 82),
    (2024, 34, 62, 70_300_000, 52_000_000, 74),
    (2025, 42, 51, 117_200_000, 48_200_000, 45),
    (2026, 57, 79, 165_000_000, 75_300_000, 46),
    (2027, 54, 84, 210_900_000, 126_500_000, 62),
]

# Municipalities within 0.5% of their levy limit, from DLS "Excess Levy
# Capacity and Override Capacity". Note: this is a DLS-derived figure, NOT
# from the MMA/Tufts report, which contains no such statistic.
AT_LEVY_LIMIT = {2010: 257, 2015: 166, 2020: 169, 2023: 148, 2024: 153, 2025: 173, 2026: 186}


def main():
    rows = []
    for fy, rev, unassigned, total, basis in FUND_BALANCE:
        rows.append(
            {
                "fiscal_year": fy,
                "gf_revenues": rev,
                "unassigned_fund_balance": unassigned,
                "unassigned_pct_of_revenue": round(100 * unassigned / rev, 2),
                "total_fund_balance": total,
                # For Brookline these are the same number - see the docstring.
                "available_fund_balance_moodys_basis": total,
                "available_pct_of_revenue": round(100 * total / rev, 2),
                "vs_policy_floor_pp": round(100 * total / rev - POLICY_FLOOR_PCT, 2),
                "certified_free_cash": FREE_CASH.get(fy, ""),
                "free_cash_pct_of_revenue": (
                    round(100 * FREE_CASH[fy] / rev, 2) if fy in FREE_CASH else ""
                ),
                "fund_balance_basis": basis,
                "note": (
                    "pre-GASB54; NOT continuous with later years"
                    if basis.startswith("pre")
                    else ""
                ),
            }
        )
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT_CSV} ({len(rows)} years)")

    sw = []
    for fy in sorted(set(STATEWIDE_FREE_CASH) | {o[0] for o in OVERRIDES} | set(AT_LEVY_LIMIT)):
        ov = next((o for o in OVERRIDES if o[0] == fy), None)
        sw.append(
            {
                "fiscal_year": fy,
                "statewide_certified_free_cash": STATEWIDE_FREE_CASH.get(fy, ""),
                "override_municipalities": ov[1] if ov else "",
                "override_questions": ov[2] if ov else "",
                "override_dollars_requested": ov[3] if ov else "",
                "override_dollars_approved": ov[4] if ov else "",
                "override_pass_rate_pct": ov[5] if ov else "",
                "municipalities_within_0_5pct_of_levy_limit": AT_LEVY_LIMIT.get(fy, ""),
            }
        )
    with open(OUT_STATEWIDE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sw[0].keys()))
        w.writeheader()
        w.writerows(sw)
    print(f"Wrote {OUT_STATEWIDE}")

    latest = rows[-1]
    print(
        f"FY{latest['fiscal_year']}: available fund balance "
        f"${latest['available_fund_balance_moodys_basis']/1e6:.1f}M = "
        f"{latest['available_pct_of_revenue']}% of revenue "
        f"({latest['vs_policy_floor_pp']:+.2f} pp vs the {POLICY_FLOOR_PCT}% policy floor); "
        f"unassigned {latest['unassigned_pct_of_revenue']}%"
    )
    write_methodology(rows, sw)
    print(f"Wrote {OUT_METHOD}")


def write_methodology(rows, sw):
    L = ["# Reserves and Free Cash — Methodology\n"]
    L.append(
        "Companion to `reserves_and_free_cash.csv` and "
        "`statewide_fiscal_context.csv`. All cited data; nothing modelled.\n"
    )
    L.append(__doc__.split("## Four different")[1].split("## Sources")[0].strip())
    L.append("\n## Brookline, audited\n")
    L.append("| FY | Unassigned | % rev | Available (= total GF) | % rev | vs 20% policy | Certified free cash |")
    L.append("|---|---|---|---|---|---|---|")
    for r in rows:
        if r["fund_balance_basis"].startswith("pre"):
            continue
        fc = f"${r['certified_free_cash']/1e6:.1f}M" if r["certified_free_cash"] else "—"
        L.append(
            f"| {r['fiscal_year']} | ${r['unassigned_fund_balance']/1e6:.1f}M | "
            f"{r['unassigned_pct_of_revenue']:.2f}% | "
            f"${r['available_fund_balance_moodys_basis']/1e6:.1f}M | "
            f"**{r['available_pct_of_revenue']:.2f}%** | "
            f"{r['vs_policy_floor_pp']:+.2f} pp | {fc} |"
        )
    L.append("")
    first_gasb = next(r for r in rows if not r["fund_balance_basis"].startswith("pre"))
    last = rows[-1]
    L.append(
        f"Available fund balance moved from **{first_gasb['available_pct_of_revenue']:.2f}%** of "
        f"revenue in FY{first_gasb['fiscal_year']} to **{last['available_pct_of_revenue']:.2f}%** in "
        f"FY{last['fiscal_year']}, and now sits "
        f"**{last['vs_policy_floor_pp']:+.2f} points** against the Town's own 20% policy floor. "
        f"Moody's Aaa median for the same measure is **{MOODYS_AAA_MEDIAN_PCT}%**, so Brookline "
        "meets its own standard and remains well below its rating peers. Both are true and "
        "they answer different questions.\n"
    )
    L.append("## Statewide context\n")
    L.append("| FY | Statewide free cash | Override munis | Requested | Approved | Pass rate | Munis at levy limit |")
    L.append("|---|---|---|---|---|---|---|")
    for r in sw:
        fc = f"${r['statewide_certified_free_cash']/1e9:.2f}B" if r["statewide_certified_free_cash"] else "—"
        req = f"${r['override_dollars_requested']/1e6:.1f}M" if r["override_dollars_requested"] else "—"
        app = f"${r['override_dollars_approved']/1e6:.1f}M" if r["override_dollars_approved"] else "—"
        pr = f"{r['override_pass_rate_pct']}%" if r["override_pass_rate_pct"] else "—"
        lim = r["municipalities_within_0_5pct_of_levy_limit"] or "—"
        L.append(
            f"| {r['fiscal_year']} | {fc} | {r['override_municipalities'] or '—'} | {req} | {app} | {pr} | {lim} |"
        )
    L.append("")
    L.append(
        "Statewide certified free cash fell **4.6%** in FY2026, which DLS "
        "described as the first decrease since the Great Recession. Override "
        "dollars requested rose roughly tenfold between FY2023 and FY2027 "
        "while the pass rate fell to 45-46% in FY2025 and FY2026. "
        "Municipalities within half a point of their levy limit went from 148 "
        "in FY2023 to 186 in FY2026.\n"
    )
    L.append(
        "For the other side of that picture: MMA and Tufts cSPA find that "
        "**nearly 200 of 351 municipalities have pursued zero overrides in the "
        "last fifteen years**, and that unrestricted state aid has fallen "
        "**25% in real terms since 2002**. Brookline's own state aid grew at "
        "1.9% a year over FY2005-2025 against operating costs at 3.65%, so the "
        "statewide pattern and the local one are the same pattern.\n"
    )
    L.append("## Sources\n")
    L.append(__doc__.split("## Sources")[1].split("## The Town's own")[0].strip() + "\n")
    L.append("## The Town's own reserve policy\n")
    L.append(__doc__.split("## The Town's own reserve policy")[1].strip() + "\n")
    OUT_METHOD.write_text("\n".join(L))


if __name__ == "__main__":
    main()
