"""
Phase 1: "Keep what we have" baseline General Fund revenue forecast, FY2026-2040.

No new overrides and no new-growth policy change (that's Phase 2, layered on
top of this). Two scenarios, FY2026-2040:

  A. "town_assumptions" - the Town's own published FY26-31 Long-Range
     Financial Plan forecast (`output/town_own_forecast_fy26_31.csv`),
     unmodified, then mechanically extended to FY2040 at the growth rates
     the Town's own FY26-31 figures imply. Represents the Town's stated
     planning assumptions taken at face value, long-run.
  B. "trend_corrected" - our own trend-based assumptions applied for the
     ENTIRE FY2026-2040 window, not just after FY2031. Ben flagged
     (2026-08-28 review) that anchoring on the Town's FY2031 figure and
     only diverging afterward meant scenario B was silently taking the
     Town's own (documented-conservative) FY26-31 numbers as truth for 6
     of the 15 forecast years - inconsistent with what "trend_corrected"
     is supposed to represent. Fixed: this scenario now builds State Aid
     and Local Receipts directly from the last known actual (FY2025) using
     trailing actual growth rates, for every year FY2026-2040. Property
     Tax uses a "delta" method instead (see below) so it doesn't lose the
     already-legislated FY27-29 override and known committed debt-exclusion
     schedule baked into the Town's own figures - those are decided facts,
     not assumptions, and should stay identical across both scenarios.

Property tax levy mechanics use the actual Prop 2.5 formula:
  levy(t) = levy(t-1) * 1.025 + new_growth(t)
New growth is expressed as a **percentage of the prior year's levy**
rather than a flat dollar amount for `trend_corrected` (Ben, 2026-08-28 -
"we found a historical percent growth number, why use an absolute
amount?"). This is the standard DOR/DLS convention for comparing new
growth across towns and over time - it's what the project's own founding
whitepaper uses ("New growth only averaged 1.3%/yr... 25th percentile
statewide... 2.1%/yr = 80th percentile"). A flat dollar figure doesn't
scale as the levy base grows, so it implicitly assumes new growth becomes
a *smaller* share of the levy every year - not supported by the FY2005-25
data, where the annual %(new growth / prior levy limit) has stayed
roughly flat (~1.1-1.4%), not trended down, even as the dollar levy nearly
tripled.
  A: $2.5M/yr flat        - the Town's own LRFP assumption, taken verbatim
                              (that's literally how the Town phrased its
                              planning assumption - a dollar figure, not a
                              %, so town_assumptions keeps it as stated)
  B: 1.277%/yr of prior levy - trailing 5-year actual average (FY2021-2025
                              `new_growth`/`prior_levy_limit`); 21-year
                              actual average is 1.367%/yr, close enough to
                              matter little either way and consistent with
                              the whitepaper's cited 1.3%/yr

For FY2026-2031, `trend_corrected` computes a "delta" series - the
cumulative extra levy from substituting scenario B's new-growth assumption
for the Town's $2.5M/yr - and adds it to the Town's own published figures,
so the known committed override/debt-exclusion dollars (which we can't
otherwise decompose out of the Town's single published total) stay
identical to `town_assumptions` while only the new-growth assumption
differs:
  diff(t) = diff(t-1) * 1.025 + (1.277% * town_property_tax(t-1) - $2,500,000), diff(2025) = 0
  trend_corrected_property_tax(t) = town_property_tax(t) + diff(t)   [t = 2026-2031]
For FY2032-2040, `trend_corrected` switches to a clean geometric formula
on its own prior-year total (no Town figure or delta involved once past
FY2031):
  trend_corrected_property_tax(t) = trend_corrected_property_tax(t-1) * (1.025 + 1.277%)
`town_assumptions` keeps using the Town's own flat $2.5M/yr for
FY2032-2040 too, since that scenario is explicitly "take the Town's stated
assumption at face value." Both connect continuously at the FY2031/2032
boundary - no discontinuity.

State Aid and Local Receipts (`trend_corrected` only) are extended
directly from the FY2025 actual at a trailing actual CAGR, for all of
FY2026-2040 - no Town figures involved at all in this scenario for these
two lines:
  State Aid:      FY2025 actual (`recap_state_aid`) x (1 + CAGR)^n,
                   CAGR from FY2015-2025 (10yr, smooths state-budget noise)
  Local Receipts:  FY2025 actual (`local_receipts_act_total`) x (1 + CAGR)^n,
                   CAGR from FY2019-2025 (skips the FY2020-21 COVID dip)

Free Cash and Other Available Funds are identical in both scenarios: the
Town's own FY26-31 figures, held flat at the FY2031 level for FY2032-2040.
No defensible trend basis exists for either (fund-balance draws, not an
organically growing revenue source) - this is a "keep what we have"
simplification, not an oversight, and is called out explicitly rather than
silently applied.

Sources: see ../data/SOURCES.md and ../.claude/memorialized.md
Outputs:
  ../output/baseline_revenue_forecast_fy26_40.csv  (the forecast, with the
    exact assumption applied to each row baked in as columns, so the file
    is self-explanatory without cross-referencing this script)
  ../output/baseline_revenue_forecast_fy26_40_methodology.md  (prose
    explanation + sourcing for every assumption)
"""
import csv
from pathlib import Path
import pandas as pd

from new_growth_scenario_forecast import (
    res_tax_rate, com_tax_rate,
    appreciated_res_value_per_unit, appreciated_com_value_per_sqft,
    chca_property_tax as _chca_property_tax, chca_local_receipts as _chca_local_receipts,
    chca_property_tax_increment as _chca_property_tax_increment, chca_value_index as _chca_value_index,
    CHCA_CONSTRUCTION_START_YEAR, CHCA_FULL_STABILIZATION_YEAR,
    CHCA_PROPERTY_TAX_RKG, CHCA_LOCAL_RECEIPTS_RKG,
    building_permit_revenue, meals_tax_organic, meals_tax_from_new_commercial,
    MEALS_TAX_2019, MEALS_TAX_2025, BUILDING_PERMITS_2025_ACTUAL,
    MEALS_TAX_ORGANIC_CAGR, MEALS_TAX_INTENSITY_PER_SQFT, BUILDING_PERMIT_RATE,
    BUILDING_PERMIT_RATE_FY2027, BUILDING_PERMIT_RATE_INCREASE_FY,
    building_permit_rate, BUILDING_PERMIT_RATE_ACTUAL_COLLECTIONS,
    TREND_RES_NEW_PCT, TREND_RES_RENO_PCT, TREND_COM_NEW_PCT,
    TREND_COM_RENO_PCT, TREND_COM_PP_PCT,
    apply_may_2026_override,
)

# Chestnut Hill Commercial Area (CHCA) - added 2026-08-29 to both scenarios
# identically (a real, now-confirmed, specific project - zoning approved by
# Town Meeting 217-20, May 28-29, 2026 - not part of either scenario's
# trend/Town assumptions, so it's layered on top of both the same way known
# committed overrides/debt exclusions already are). Full sourcing/timeline
# in new_growth_scenario_forecast.py's module docstring and CHCA_* constants.
#
# **Uses the RKG scenario specifically, not the CR-average** (Ben,
# 2026-08-30): the ERSC report's Appendix has 5 RKG-modeled scenarios - 3
# from the developer (City Realty), 1 from EDAB, 1 from RKG itself (the
# independent consultant). EDAB and RKG both came in noticeably more
# conservative than City Realty's own scenarios. Ben's call: use RKG's
# single independent scenario for this "keep what we have" baseline (the
# more conservative, less-developer-optimistic figure fits the baseline's
# framing), and reserve the City Realty average for
# `new_growth_scenario_forecast.py`'s own scenarios instead (see that
# script's CHCA constants block for the full 5-scenario table).
# CHCA_PROPERTY_TAX_RKG ($3,158,174 - res + com property tax, RKG scenario
# only) is the portion that counts toward the Prop 2.5 levy limit;
# CHCA_LOCAL_RECEIPTS_RKG ($480,435 - rooms tax + motor vehicle excise,
# same scenario) is a separate revenue line that doesn't count toward the
# levy limit at all - each stream goes to its correct line below. Both
# return the cumulative *level* for year y, not a per-year increment -
# added directly wherever a year's figure is computed independently (each
# TOWN_YEARS figure, and every year of trend_corrected's CAGR-based
# local_receipts), but only the year-over-year *increment* where the
# computation is chained (EXTEND_YEARS' property-tax recursion, and
# town_assumptions' chained local_receipts CAGR) - the prior year's level
# is already embedded there, so adding the full level again every year
# would double-count it.


# RKG's residential share of its property tax, for indexing each entry to its year's value
# (2026-10-14; see new_growth_scenario_forecast.py's CHCA_DOLLAR_YEAR note)
CHCA_RES_SHARE_RKG = 1_841_088 / CHCA_PROPERTY_TAX_RKG


def chca_increment(year):
    """This year's entry at its own year's value (the increment, for chained levy recursions)."""
    import new_growth_scenario_forecast as _n
    share = _n.chca_ramp_share(year) - _n.chca_ramp_share(year - 1)
    return share * CHCA_PROPERTY_TAX_RKG * _chca_value_index(year, CHCA_RES_SHARE_RKG) if share else 0.0


def chca_revenue(year):
    """The level: each year's entry carried forward with the levy's 2.5%."""
    return sum(chca_increment(s) * 1.025 ** (year - s) for s in range(CHCA_CONSTRUCTION_START_YEAR, year + 1))


def chca_local_receipts(year):
    return _chca_local_receipts(year, CHCA_LOCAL_RECEIPTS_RKG)


def chca_local_receipts_increment(year):
    return chca_local_receipts(year) - chca_local_receipts(year - 1)

# Physical translation of trend_corrected's new-growth $ into implied
# units/sqft (added 2026-08-29, Ben: "can we retroactively make the
# baseline forecast match this format so we can say, in the baseline, how
# much gets built or renovated?"). Purely additive/informational - does
# NOT change property_taxes or any other $ figure below, which stay
# exactly as already reviewed/memorialized. Decomposes the *existing*
# new-growth $ each year using the same 5 trend-category shares Phase 2
# uses (imported directly rather than re-derived, so there's one source
# of truth) - residential new/reno, commercial new/reno, and commercial
# personal property (split out 2026-08-30 - see
# new_growth_scenario_forecast.py's module docstring/Personal Property
# section). New-construction dollars are converted to physical counts via
# the same appreciated $/unit and $/sqft Phase 2 uses, so the two scripts'
# physical framing is consistent even though this one doesn't change the
# underlying $ math.
_TREND_TOTAL_PCT = (TREND_RES_NEW_PCT + TREND_RES_RENO_PCT + TREND_COM_NEW_PCT
                     + TREND_COM_RENO_PCT + TREND_COM_PP_PCT)


def decompose_new_growth(new_growth_total_dollars):
    """Splits one year's blended new-growth $ into the same 5 categories Phase 2 uses."""
    res_new_dollars = new_growth_total_dollars * TREND_RES_NEW_PCT / _TREND_TOTAL_PCT
    res_reno_dollars = new_growth_total_dollars * TREND_RES_RENO_PCT / _TREND_TOTAL_PCT
    com_new_dollars = new_growth_total_dollars * TREND_COM_NEW_PCT / _TREND_TOTAL_PCT
    com_reno_dollars = new_growth_total_dollars * TREND_COM_RENO_PCT / _TREND_TOTAL_PCT
    com_pp_dollars = new_growth_total_dollars * TREND_COM_PP_PCT / _TREND_TOTAL_PCT
    return res_new_dollars, res_reno_dollars, com_new_dollars, com_reno_dollars, com_pp_dollars


def implied_units_and_sqft(year, new_growth_total_dollars):
    res_new_dollars, _, com_new_dollars, _, _ = decompose_new_growth(new_growth_total_dollars)
    units = res_new_dollars / (appreciated_res_value_per_unit(year) * res_tax_rate(year))
    sqft = com_new_dollars / (appreciated_com_value_per_sqft(year) * com_tax_rate(year))
    return units, sqft


TOWN_FORECAST_FILE = "../output/town_own_forecast_fy26_31.csv"
HISTORICAL_FILE = "../output/brookline_historical_financials_fy05_25.csv"
OUT_FILE = "../output/baseline_revenue_forecast_fy26_40.csv"
METHODOLOGY_FILE = "../output/baseline_revenue_forecast_fy26_40_methodology.md"

FORECAST_YEARS = list(range(2026, 2041))
TOWN_YEARS = list(range(2026, 2032))
ANCHOR_YEAR = 2031
EXTEND_YEARS = list(range(2032, 2041))

NEW_GROWTH_TOWN = 2_500_000

# --- Sensitivity hooks (added 2026-09-06) ---
# Both default to None/True, i.e. exactly the behaviour above, so running this
# script directly produces byte-identical output to before. They exist so
# `base_case_decomposition.py` can re-run this same model - not a
# reimplementation of it - under two counterfactuals the reference document
# needs: (1) the May 2026 override never having passed, to separate the
# structural gap from the override that currently closes it, and (2) a
# different sustained new-growth rate, to solve for what rate closes that
# structural gap on its own. Set them on the module, not by editing here.
NEW_GROWTH_PCT_TREND_OVERRIDE = None  # e.g. 0.013815 to force a rate
# FY2026 new growth as certified by the state (DLS new growth report, data/2026 MA state new growth
# for all towns 20 years.xlsx), read by certified_new_growth() below.
# Added 2026-10-13 (Ben): the trend window moves to FY2022-26 now that FY2026 is certified, and FY2026
# itself uses the certified figure rather than the trend.
NG_FILE = Path(__file__).resolve().parents[1] / "data" / "2026 MA state new growth for all towns 20 years.xlsx"


def certified_new_growth(fy, col=6):
    """(new growth applied, prior-year levy limit) for Brookline in `fy`, from the DLS report; col=4 gives
    residential new growth applied instead of the total."""
    import pandas as pd
    ng = pd.read_excel(NG_FILE, sheet_name="data", header=None)
    r = ng[(ng[1].astype(str).str.strip() == "Brookline") & (pd.to_numeric(ng[2], errors="coerce") == fy)].iloc[0]
    return float(r[col]), float(r[8])
INCLUDE_MAY_2026_OVERRIDE = True      # False = the pre-vote counterfactual


def read_town_forecast():
    """Returns {subcategory: {year: value}} for revenue rows, FY2026-2031."""
    out = {}
    with open(TOWN_FORECAST_FILE) as f:
        for row in csv.DictReader(f):
            if row["category"] != "revenue":
                continue
            out[row["subcategory"]] = {y: float(row[str(y)]) for y in range(2026, 2032)}
    if INCLUDE_MAY_2026_OVERRIDE:
        out["property_taxes"] = apply_may_2026_override(out["property_taxes"])
    return out


def read_historical():
    with open(HISTORICAL_FILE) as f:
        return {int(row["fiscal_year"]): row for row in csv.DictReader(f)}


def cagr(start, end, years):
    return (end / start) ** (1 / years) - 1


def main():
    town = read_town_forecast()
    hist = read_historical()

    # --- Trailing-actual rates for Scenario B, all anchored on FY2025 actuals ---
    # New growth as % of prior-year levy limit (the standard DOR/DLS
    # convention for comparing new growth across towns and over time -
    # it's what the whitepaper's own "1.3%/yr, 25th percentile statewide"
    # framing uses) rather than a flat dollar amount. A flat dollar figure
    # doesn't scale as the levy base grows, so it implicitly assumes new
    # growth becomes a *smaller* share of the levy every year - not
    # supported by the data (the % has stayed roughly stable, not trended
    # down, over FY2005-2025).
    new_growth_pct_all = [float(hist[y]["new_growth"]) / float(hist[y]["prior_levy_limit"])
                          for y in range(2005, 2026)]
    ng26, lim26 = certified_new_growth(2026)
    new_growth_pct_recent = [float(hist[y]["new_growth"]) / float(hist[y]["prior_levy_limit"])
                             for y in range(2022, 2026)] + [ng26 / lim26]
    # residential and the rest each averaged and rounded to 0.001 point, as the scenario script and the workbook do
    lim = {y: float(hist[y]["prior_levy_limit"]) for y in range(2022, 2026)}
    res_recent = [float(hist[y]["res_new_growth_applied"]) / lim[y] for y in range(2022, 2026)] + [certified_new_growth(2026, col=4)[0] / lim26]
    res_avg = sum(res_recent) / 5
    new_growth_pct_trend = round(res_avg, 5) + round(sum(new_growth_pct_recent) / 5 - res_avg, 5)
    new_growth_pct_21yr = sum(new_growth_pct_all) / len(new_growth_pct_all)
    if NEW_GROWTH_PCT_TREND_OVERRIDE is not None:
        new_growth_pct_trend = NEW_GROWTH_PCT_TREND_OVERRIDE

    state_aid_2025 = float(hist[2025]["recap_state_aid"])
    state_aid_cagr_actual = cagr(float(hist[2015]["recap_state_aid"]), state_aid_2025, 10)
    import new_growth_scenario_forecast as _ngs   # the Town's FY2026-27, then 2.5%/yr (Ben, 2026-10-14)
    ngs_state_aid = _ngs.state_aid_path(town, FORECAST_YEARS)

    # Local receipts actual only available FY2017+; use FY2019-2025 to skip
    # the FY2020-21 COVID dip as an anchor point.
    local_receipts_2025 = float(hist[2025]["local_receipts_act_total"])
    local_receipts_cagr_actual = cagr(float(hist[2019]["local_receipts_act_total"]),
                                       local_receipts_2025, 6)
    # Meals tax and building permits pulled out and modeled separately (see
    # new_growth_scenario_forecast.py's MEALS_TAX_*/BUILDING_PERMIT_* for
    # full sourcing) for trend_corrected specifically - town_assumptions
    # keeps the simpler CAGR-only treatment, consistent with it not getting
    # the implied-units/sqft physical decomposition either (Town's flat $
    # figure isn't broken out by type). The residual base has both the
    # FY2025 meals-tax level AND building-permits level subtracted before
    # extending at the (still meals-tax-inclusive, since permits aren't
    # cleanly separable pre-FY2023) ex-meals CAGR - same approximation as
    # new_growth_scenario_forecast.py.
    # Investment income is set aside too and held flat (Ben, 2026-10-14; see
    # new_growth_scenario_forecast.py's INVESTMENT_INCOME_*).
    local_receipts_2025_residual, local_receipts_cagr_ex_meals = _ngs.local_receipts_residual(hist)

    # --- Town's own implied FY26-31 rates for Scenario A ---
    state_aid_cagr_town = cagr(town["state_aid"][2026], town["state_aid"][ANCHOR_YEAR], 5)
    local_receipts_cagr_town = cagr(town["local_receipts"][2026], town["local_receipts"][ANCHOR_YEAR], 5)

    print(f"New growth: Town assumption ${NEW_GROWTH_TOWN:,.0f}/yr flat | "
          f"trend_corrected uses {new_growth_pct_trend:.3%}/yr of prior-year levy "
          f"(trailing 5yr actual, FY22-26; 21yr actual avg {new_growth_pct_21yr:.3%}/yr)")
    print(f"State aid: Town-implied CAGR (FY26-31) {state_aid_cagr_town:.2%} | "
          f"trend_corrected extends FY25 actual (${state_aid_2025:,.0f}) at "
          f"{state_aid_cagr_actual:.2%} CAGR (FY15-25 actual)")
    print(f"Local receipts: Town-implied CAGR (FY26-31) {local_receipts_cagr_town:.2%} | "
          f"trend_corrected extends FY25 actual (${local_receipts_2025:,.0f}) at "
          f"{local_receipts_cagr_actual:.2%} CAGR (FY19-25 actual)")

    # Property tax "delta" series for trend_corrected's FY2026-2031:
    # cumulative extra levy from substituting a %-of-prior-year-base new
    # growth assumption for the Town's flat $2.5M/yr, applied to the
    # OPERATING (levy-limit-only) base - see the debt exclusion carve-out
    # below for why this is now levy-limit-only rather than the combined
    # total the way an earlier version of this script computed it.
    prior_base = {2025: float(hist[2025]["total_levy"]) - float(hist[2025]["debt_exclusions"])}
    prior_base.update({y: town["property_taxes"][y] - town["debt_exclusion"][y] for y in TOWN_YEARS})
    prop_tax_diff = {2025: 0.0}
    ng_trend_dollars = {}
    for y in range(2026, 2032):
        # the rate applies to this forecast's own levy (the Town's plus the difference so far), not the
        # Town's alone (2026-10-13, Ben: the Town's levy carries only its $2.5M of new growth)
        ng_trend_dollars[y] = ng26 if y == 2026 else new_growth_pct_trend * (prior_base[y - 1] + prop_tax_diff[y - 1])
        # the Town plan's FY2026 levy already carries the certified figure (fixed 2026-10-14)
        prop_tax_diff[y] = prop_tax_diff[y - 1] * 1.025 + (0.0 if y == 2026 else ng_trend_dollars[y] - NEW_GROWTH_TOWN)

    # Debt exclusion carve-out (added 2026-08-30, Ben: "let's carve out the
    # debt exclusions in detail so we can focus on operating revenue").
    # Sourced directly, bond-by-bond, from the Town's own FY27-31 LRFP
    # (`data/FY27-FY31-Long-Range-Financial-Plan.pdf`, "PROPERTY TAXES" and
    # "DEBT EXCLUSION" tables) - the Town's own levy build-up literally
    # separates "SUB-TOTAL ANNUAL LEVY LIMIT" from "Debt Exclusion (Debt
    # Service Costs)" before summing to "ANNUAL LEVY", which is exactly
    # `town["property_taxes"]`. Extracted into `output/town_own_forecast_
    # fy26_31.csv`'s new `debt_exclusion` row. A debt exclusion is, by MA
    # Prop 2.5 statute, a dollar-for-dollar match to a specific bond's
    # annual debt service - it's added to the levy OUTSIDE the 2.5% cap,
    # not subject to it, and expires when the bond retires. **This is a
    # real correctness fix, not just a presentational change**: the
    # previous version of this script grew the *combined* prop_tax total
    # at the 2.5%+new-growth rate for FY2032-2040, which implicitly
    # compounded the embedded debt-exclusion dollars at that rate too -
    # wrong, since excluded amounts aren't subject to the 2.5% cap and
    # don't organically grow (if anything they gently decline as bonds
    # retire, absent new exclusions). Now: `debt_exclusion_revenue` is
    # held flat at the FY2031 level for FY2032-2040 in both scenarios
    # (no new debt exclusions assumed, consistent with the rest of this
    # model), and only `property_tax_operating` (the levy-limit-only
    # component) grows at the statutory/trend rate. `property_taxes`
    # (total) = `property_tax_operating` + `debt_exclusion_revenue`.
    debt_exclusion = dict(town["debt_exclusion"])
    for y in EXTEND_YEARS:
        debt_exclusion[y] = debt_exclusion[ANCHOR_YEAR]

    TOWN_ASSUM = "Town's own FY26-31 LRFP figure, as published"
    FLAT = "held flat at FY2031 Town figure (no defensible trend basis; identical in both scenarios)"
    DEBT_EXCL_NOTE_TOWN = TOWN_ASSUM + " (bond-by-bond, LRFP p.7-8)"
    DEBT_EXCL_NOTE_FLAT = ("held flat at FY2031 Town figure - no new debt exclusions assumed "
                            "(same policy as the rest of this baseline); real excluded debt actually "
                            "declines as bonds retire, not modeled here for lack of maturity-date data")

    rows = []
    for scenario in ("town_assumptions", "trend_corrected"):
        levy_limit, state_aid, local_receipts = {}, {}, {}
        other_funds = dict(town["other_available_funds"])
        free_cash = dict(town["free_cash"])
        import fy2027_adopted as _fy27
        other_funds[2027] = _fy27.OTHER_AVAILABLE_FUNDS   # adopted FY2027 budget, not the Jan LRFP
        for _y, _d in _fy27.OVERRIDE_STABILIZATION_DRAW.items():   # FY2027 deposit drawn over 3 yrs
            other_funds[_y] += _d
        for y in EXTEND_YEARS:
            other_funds[y] = other_funds[ANCHOR_YEAR]
            free_cash[y] = free_cash[ANCHOR_YEAR]

        if scenario == "town_assumptions":
            for y in TOWN_YEARS:
                levy_limit[y] = town["property_taxes"][y] - debt_exclusion[y] + chca_revenue(y)
                state_aid[y] = town["state_aid"][y]
                local_receipts[y] = town["local_receipts"][y] + chca_local_receipts(y)
            for y in EXTEND_YEARS:
                levy_limit[y] = levy_limit[y - 1] * 1.025 + NEW_GROWTH_TOWN + chca_increment(y)
                state_aid[y] = state_aid[y - 1] * (1 + state_aid_cagr_town)
                local_receipts[y] = (local_receipts[y - 1] * (1 + local_receipts_cagr_town)
                                      + chca_local_receipts_increment(y))
        else:
            for y in TOWN_YEARS:
                levy_limit[y] = town["property_taxes"][y] - debt_exclusion[y] + prop_tax_diff[y] + chca_revenue(y)
            for y in EXTEND_YEARS:
                levy_limit[y] = levy_limit[y - 1] * (1.025 + new_growth_pct_trend) + chca_increment(y)
            cumulative_new_com_sqft = 0.0
            for y in FORECAST_YEARS:
                n = y - 2025
                state_aid[y] = ngs_state_aid[y]
                this_year_ng = ng_trend_dollars[y] if y in TOWN_YEARS else levy_limit[y - 1] * new_growth_pct_trend
                _, _, com_new_y, _, _ = decompose_new_growth(this_year_ng)
                cumulative_new_com_sqft += com_new_y / (appreciated_com_value_per_sqft(y) * com_tax_rate(y))
                permits_y = building_permit_revenue(*decompose_new_growth(this_year_ng)[:4], year=y)
                lr_residual = local_receipts_2025_residual * (1 + local_receipts_cagr_ex_meals) ** n
                local_receipts[y] = (lr_residual + meals_tax_organic(y)
                                      + meals_tax_from_new_commercial(cumulative_new_com_sqft)
                                      + permits_y + chca_local_receipts(y)
                                      + _ngs.INVESTMENT_INCOME_FLAT)

        prop_tax = {y: levy_limit[y] + debt_exclusion[y] for y in FORECAST_YEARS}
        actual_receipts = dict(local_receipts)
        if scenario == "trend_corrected":
            # Receipts budgeted as the Town budgets them; last year's excess
            # arrives as this year's free cash (revenue_cash_cycle.py).
            import revenue_cash_cycle as rcc
            base_total = {y: prop_tax[y] + state_aid[y] + other_funds[y] for y in FORECAST_YEARS}
            local_receipts, free_cash = rcc.apply(FORECAST_YEARS, actual_receipts,
                                                  free_cash, base_total)

        for y in FORECAST_YEARS:
            extended = y in EXTEND_YEARS
            total = prop_tax[y] + state_aid[y] + local_receipts[y] + other_funds[y] + free_cash[y]

            chca_dollars = chca_revenue(y)
            chca_lr_dollars = chca_local_receipts(y)
            chca_note = (f"+ CHCA property tax ${chca_dollars:,.0f} (Chestnut Hill Commercial "
                         f"Area, City Realty - zoning approved May 2026, ramping "
                         f"FY{CHCA_CONSTRUCTION_START_YEAR}-{CHCA_FULL_STABILIZATION_YEAR})"
                         if chca_dollars > 0 else "+ CHCA property tax $0 (not yet ramping)")
            chca_lr_note = (f"+ CHCA local receipts (rooms tax + MV excise) ${chca_lr_dollars:,.0f}"
                             if chca_lr_dollars > 0 else "+ CHCA local receipts $0 (not yet ramping)")

            if scenario == "town_assumptions":
                levy_note = ((f"2.5% statutory + ${NEW_GROWTH_TOWN:,.0f}/yr new growth") if extended
                             else TOWN_ASSUM + " (levy limit only, i.e. Town's ANNUAL LEVY minus Debt Exclusion)"
                             ) + f"; {chca_note}"
                sa_note = (f"{TOWN_ASSUM}, extended at {state_aid_cagr_town:.2%} CAGR" if extended
                           else TOWN_ASSUM)
                lr_note = ((f"{TOWN_ASSUM}, extended at {local_receipts_cagr_town:.2%} CAGR" if extended
                           else TOWN_ASSUM) + f"; {chca_lr_note}")
            else:
                this_year_ng = ng_trend_dollars[y] if not extended else levy_limit[y - 1] * new_growth_pct_trend
                implied_units, implied_sqft = implied_units_and_sqft(y, this_year_ng)
                physical_note = (f"implies ~{implied_units:,.0f} new res. units + "
                                  f"~{implied_sqft:,.0f} sqft new commercial (plus renovation/other) "
                                  "at Phase 2 conversion factors")
                levy_note = (
                    (f"Town's own FY26-31 levy-limit figure + cumulative delta from "
                    f"{new_growth_pct_trend:.3%}/yr new growth on prior-year levy limit "
                    f"(~${ng_trend_dollars[y]:,.0f} this year, vs. Town's flat "
                    f"${NEW_GROWTH_TOWN:,.0f}/yr); {physical_note}"
                    if not extended else
                    f"2.5% statutory + {new_growth_pct_trend:.3%}/yr new growth on prior-year "
                    f"levy limit (~${levy_limit[y-1]*new_growth_pct_trend:,.0f} this year); "
                    f"{physical_note}")
                    + f"; {chca_note}")
                sa_note = (f"Town's FY2026 and adopted FY2027 figures, then {_ngs.STATE_AID_GROWTH:.1%}/yr (the Town plan's "
                           f"rate; FY15-25 actual was {state_aid_cagr_actual:.2%} including FY2019's one-year rise)")
                permits_note_y = building_permit_revenue(*decompose_new_growth(this_year_ng)[:4], year=y)
                lr_note = (f"residual (ex-meals, ex-permits, ex-investment income, held flat) FY2025 actual x "
                           f"{local_receipts_cagr_ex_meals:.2%} CAGR (FY19-25 actual) + meals tax organic "
                           f"({MEALS_TAX_ORGANIC_CAGR:.2%}/yr) + meals tax from cumulative new commercial "
                           f"sqft (${MEALS_TAX_INTENSITY_PER_SQFT:.4f}/sqft) + building permits "
                           f"${permits_note_y:,.0f} ({building_permit_rate(y):.2%} of new-growth value), "
                           f"not Town's figure; {chca_lr_note}")

            debt_excl_note = DEBT_EXCL_NOTE_TOWN if not extended else DEBT_EXCL_NOTE_FLAT
            prop_tax_note = f"= property_tax_operating + debt_exclusion_revenue; {levy_note}"
            other_note = free_note = FLAT if extended else TOWN_ASSUM
            if scenario == "trend_corrected":
                lr_note = (f"budgeted at {rcc.BUDGET_RATIO:.1%} of forecast actual collections "
                           f"(${actual_receipts[y]:,.0f}; the Town's FY2025 practice); actual = {lr_note}")
                free_note = (TOWN_ASSUM + " (already certified/budgeted)"
                             if y in rcc.KNOWN_FREE_CASH_YEARS else
                             f"prior-year excess receipts + {rcc.OTHER_SURPLUS_SHARE:.2%} of prior-year "
                             "revenue (other surplus, FY2022-25 average); revenue_cash_cycle.py")

            if scenario == "trend_corrected":
                implied_units_col, implied_sqft_col = round(implied_units), round(implied_sqft)
            else:
                implied_units_col = implied_sqft_col = "n/a - Town's flat $ figure not decomposed by type"

            rows.append([
                scenario, y,
                round(prop_tax[y]), prop_tax_note,
                implied_units_col, implied_sqft_col,
                round(chca_dollars),
                round(state_aid[y]), sa_note,
                round(local_receipts[y]), lr_note,
                round(other_funds[y]), other_note,
                round(free_cash[y]), free_note,
                round(total),
                round(levy_limit[y]), levy_note,
                round(debt_exclusion[y]), debt_excl_note,
            ])

    with open(OUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scenario", "fiscal_year",
            "property_taxes", "property_tax_assumption",
            "implied_res_new_units", "implied_com_new_sqft", "chca_property_tax_dollars",
            "state_aid", "state_aid_assumption",
            "local_receipts", "local_receipts_assumption",
            "other_available_funds", "other_available_funds_assumption",
            "free_cash", "free_cash_assumption",
            "total_revenue",
            "property_tax_operating", "property_tax_operating_assumption",
            "debt_exclusion_revenue", "debt_exclusion_revenue_assumption",
        ])
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUT_FILE}")
    total_cagrs = {}
    fy26_totals = {}
    for scenario in ("town_assumptions", "trend_corrected"):
        r26 = next(r for r in rows if r[0] == scenario and r[1] == 2026)
        r40 = next(r for r in rows if r[0] == scenario and r[1] == 2040)
        total_cagrs[scenario] = cagr(r26[15], r40[15], 14)
        fy26_totals[scenario] = r26[15]
        print(f"{scenario}: FY26 total ${r26[15]:,.0f} -> FY40 total ${r40[15]:,.0f} "
              f"(implied CAGR {total_cagrs[scenario]:.2%})")

    # Compounding-effect headline numbers: the property-tax-only gap between
    # the two new-growth assumptions, isolated from every other scenario
    # difference (both scenarios share the same 2.5% statutory mechanic and
    # the same known committed overrides/debt exclusions - this gap is
    # purely the new-growth assumption's compounding effect).
    prop_tax_by_scenario = {"town_assumptions": {}, "trend_corrected": {}}
    for r in rows:
        prop_tax_by_scenario[r[0]][r[1]] = r[2]
    prop_tax_gap = {y: prop_tax_by_scenario["trend_corrected"][y] - prop_tax_by_scenario["town_assumptions"][y]
                     for y in FORECAST_YEARS}
    cumulative_gap = {}
    running = 0
    for y in FORECAST_YEARS:
        running += prop_tax_gap[y]
        cumulative_gap[y] = running
    print(f"\nNew-growth compounding effect (property tax only, trend_corrected vs. "
          f"town_assumptions): FY26 annual gap ${prop_tax_gap[2026]:,.0f} -> FY40 annual gap "
          f"${prop_tax_gap[2040]:,.0f}; cumulative FY26-40 ${cumulative_gap[2040]:,.0f}")

    # Quantify the debt-exclusion compounding-bug fix (see the debt_exclusion
    # carve-out comment above): what FY2040's debt exclusion would have been
    # if it had kept compounding at the trend_corrected rate instead of
    # being correctly held flat, for the methodology doc.
    debt_excl_fy31 = debt_exclusion[ANCHOR_YEAR]
    debt_excl_fy40_if_uncorrected = debt_excl_fy31 * (1.025 + new_growth_pct_trend) ** 9
    debt_excl_fix_magnitude = debt_excl_fy40_if_uncorrected - debt_excl_fy31

    write_methodology(new_growth_pct_trend, new_growth_pct_21yr, state_aid_cagr_town,
                       state_aid_cagr_actual, local_receipts_cagr_town, local_receipts_cagr_actual,
                       state_aid_2025, local_receipts_2025, total_cagrs, fy26_totals,
                       prop_tax_gap, cumulative_gap, debt_excl_fy31, debt_excl_fy40_if_uncorrected,
                       debt_excl_fix_magnitude)
    print(f"Wrote methodology doc to {METHODOLOGY_FILE}")


def write_methodology(ng_pct_trend, ng_pct_21yr, sa_cagr_town, sa_cagr_actual,
                       lr_cagr_town, lr_cagr_actual, sa_2025, lr_2025,
                       total_cagrs, fy26_totals, prop_tax_gap, cumulative_gap,
                       debt_excl_fy31, debt_excl_fy40_if_uncorrected, debt_excl_fix_magnitude):
    doc = f"""# Baseline Revenue Forecast (FY2026-2040) — Assumptions & Methodology

Companion to `baseline_revenue_forecast_fy26_40.csv`. Every `*_assumption`
column in that file states exactly what was applied to that cell - "Town's
own FY26-31 LRFP figure, as published" where we didn't touch it, or the
specific rate/formula where we did. This doc explains where each of those
numbers comes from.

## Scope

This is Phase 1: a "keep what we have" baseline — no new voter overrides,
no new-growth policy change (e.g. upzoning). Those are separate, later
phases (5 and 2 respectively). It answers "what happens to revenue if
nothing changes," not "what should the Town do."

## Two scenarios, both spanning the full FY2026-2040 window

- **town_assumptions**: the Town's own published FY2026-2031 LRFP figures,
  unmodified, then mechanically extended to FY2040 at the growth rates
  those figures themselves imply. Takes the Town's stated planning
  assumptions at face value, long-run.
- **trend_corrected**: our own trend-based assumptions, applied for the
  *entire* FY2026-2040 window — **not** anchored on the Town's FY2031
  figure with divergence starting only afterward. An earlier draft of this
  model did anchor that way, which meant `trend_corrected` was silently
  taking the Town's own (documented-conservative) numbers as truth for 6
  of the 15 forecast years. Ben caught this in review (2026-08-28) and
  asked for the Town's numbers to not be treated as ground truth for
  FY2026-2031 either — fixed, as described below.

## Property Tax — new growth as a % of prior levy, not a flat dollar amount

Uses the actual Massachusetts Proposition 2½ levy-limit formula rather
than a fitted trend line:

    levy(t) = levy(t-1) * 1.025 + new_growth(t)

`new_growth(t)` is expressed as a **percentage of the prior year's levy**
for `trend_corrected`, not a flat dollar amount (Ben, 2026-08-28: "we
found a historical percent growth number - can't we use that? why would
we want to use an absolute number?"). This is the standard DOR/DLS
convention for comparing new growth across towns and over time, and it's
what this project's own founding whitepaper uses ("New growth only
averaged 1.3%/yr... 25th percentile statewide... 2.1%/yr = 80th
percentile"). A flat dollar figure has a hidden implication worth naming:
held constant while the levy base grows, it makes new growth a *shrinking*
share of the levy every year — not supported by the data. The annual
%(`new_growth`/`prior_levy_limit`) over FY2005-2025 has stayed roughly in
the 1.1-1.4% band with no clear trend, even as the dollar levy nearly
tripled ($120M -> $313M).

- **town_assumptions**: **$2,500,000/yr flat**, the Town's own LRFP
  assumption, kept exactly as the Town itself stated it — this scenario is
  explicitly "take the Town's stated assumption at face value," and the
  Town's own planning document states a dollar figure, not a percentage,
  so we don't convert it.
- **trend_corrected**: **{ng_pct_trend:.3%}/yr of the prior year's levy** —
  trailing 5-year actual average (FY2021-2025, `new_growth` /
  `prior_levy_limit` from `output/brookline_historical_financials_fy05_25.csv`).
  The 21-year actual average is {ng_pct_21yr:.3%}/yr — close enough not to
  matter much, and consistent with the whitepaper's cited ~1.3%/yr.

**FY2026-2031**: we now have the Town's own year-by-year debt exclusion
schedule (see "Debt exclusion carve-out" below), so both scenarios build
the levy-limit-only base as `property_taxes(t) - debt_exclusion(t)`
(the May 2026 operating override is added into `property_taxes(t)` before
this split — see "May 2026 override correction" below for why it isn't
already there — but still isn't separately decomposed from ordinary 2.5%
statutory growth, only from debt exclusions specifically). `trend_corrected`
adds a **delta** on top of that levy-limit base:

    diff(t) = diff(t-1) * 1.025 + ({ng_pct_trend:.3%} * town_levy_limit(t-1) - $2,500,000), diff(2025) = 0
    trend_corrected_levy_limit(t) = town_levy_limit(t) + diff(t)        [t = 2026-2031]
    trend_corrected_property_tax(t) = trend_corrected_levy_limit(t) + debt_exclusion(t)

This is mathematically exact for this window (not an approximation): since
both scenarios' levy-limit formulas share the same known override
additions in any given year, those terms cancel out of the difference
between the two scenarios' levy-limit paths, leaving only the new-growth
substitution's compounding effect — which is exactly what `diff(t)`
computes.

**FY2032-2040**: `trend_corrected` switches to a clean geometric formula
on its own prior-year **levy-limit** total (no Town figure or delta
involved once past FY2031, since there's no more known-committed-facts
ambiguity to protect against):

    trend_corrected_levy_limit(t) = trend_corrected_levy_limit(t-1) * (1.025 + {ng_pct_trend:.3%})
    trend_corrected_property_tax(t) = trend_corrected_levy_limit(t) + debt_exclusion(t)   [debt_exclusion held flat, see below]

`town_assumptions` keeps running `levy_limit(t-1)*1.025 + $2,500,000` for
FY2032-2040 too, then adds the same flat `debt_exclusion(t)`. Both connect
continuously at the FY2031/2032 boundary — no discontinuity, even though
the two scenarios use different formula shapes before and after it.

## May 2026 override correction

Added 2026-09-01, caught by Ben asking directly why this forecast turned to
a deficit so quickly given the May 2026 override had already passed. It
hadn't been included — a real gap, not a design choice. `town_own_forecast_
fy26_31.csv` is a faithful transcription of `data/FY27-FY31-Long-Range-
Financial-Plan.pdf`, presented to the Advisory Committee **2026-01-13**,
four months **before** the override vote (2026-05-05). Checked directly
against that source (slide 8, "PROPERTY TAXES" table): its own "General
Override" line in the levy build-up is blank for every year FY2026-2031 —
this document exists to make the case *for* the override (its own Summary
slide: "Town structural deficit: $2.9M... Schools assumed structural
deficit: $13.5M"), not to reflect its passage. An earlier draft of this
methodology doc claimed the override was "already embedded" in the Town's
levy-limit base — that was wrong, unverified against the primary source.

Both scenarios now add the override in via `apply_may_2026_override()`
(`new_growth_scenario_forecast.py`), applied to `property_taxes` before
the debt-exclusion split below, so it flows identically into both
`town_assumptions` and `trend_corrected` — the same treatment as CHCA and
the debt-exclusion schedule (a decided fact by this project's own "today,"
not a hypothetical future policy lever). Year-by-year amounts (FY2027
$9,852,330 / FY2028 $5,602,871 / FY2029 $7,799,238, from Ben's own
`FY27-FY29 Brookline property tax & impact of new growth.xlsx`, cross-
sourced against the Override Guide's $23,254,439 3-year total) are
"permanent, not phased-out" per the Override Guide — each tranche, once
added, compounds at 2.5%/yr forever after, same as every other historical
override in this project's FY2005-2025 model.

## Debt exclusion carve-out — `property_taxes` = `property_tax_operating` + `debt_exclusion_revenue`

Added 2026-08-30 (Ben: "let's carve out the debt exclusions in detail so
we can focus on operating revenue" — debt exclusions were creating
confusion about what's really "operating" revenue vs. earmarked capital
funding). Sourced bond-by-bond from the Town's own FY27-31 LRFP
(`data/FY27-FY31-Long-Range-Financial-Plan.pdf`, "PROPERTY TAXES" and
"DEBT EXCLUSION" tables, pages 7-8 of that deck) — the Town's own levy
build-up already separates these two components before summing to the
"ANNUAL LEVY" figure that is `town["property_taxes"]`:

| | FY2026 | FY2027 | FY2028 | FY2029 | FY2030 | FY2031 |
|---|---|---|---|---|---|---|
| Sub-total Annual Levy Limit | \\$303,957,721 | \\$314,072,665 | \\$324,424,482 | \\$335,035,094 | \\$345,910,971 | \\$357,058,746 |
| Debt Exclusion (Debt Service) | \\$28,596,860 | \\$35,379,833 | \\$36,013,706 | \\$36,726,580 | \\$36,720,980 | \\$36,720,930 |
| **Annual Levy (= property_taxes)** | \\$332,554,581 | \\$349,452,499 | \\$360,438,187 | \\$371,761,674 | \\$382,631,951 | \\$393,779,676 |

The underlying LRFP bond-by-bond schedule is itself detailed — Florida
Ruffin Ridley School (2015, 2 borrowings), High School (2018, 4
borrowings), Driscoll School (2019 original + 2021 geothermal), Newbury
College (2020), Fire Station renovations (2023, 2 actual + 3 projected
future borrowings), Pierce School Construction (2024, 2 actual + 1
projected $77M future borrowing) — extracted here at the annual-total
level (`output/town_own_forecast_fy26_31.csv`'s new `debt_exclusion` row),
not bond-by-bond, since the annual total is what the property-tax and
debt-service sides of this model actually need.

By Massachusetts Proposition 2½ statute, a debt exclusion is a
**dollar-for-dollar match** to a specific bond's annual debt service: it's
added to the levy *outside* the 2.5% annual cap (not subject to it), and
it expires when the bond retires — legally distinct from the ordinary levy
limit, which grows 2.5%/yr plus new growth indefinitely.

**This carve-out is a real correctness fix, not just a presentational
one.** The previous version of this script grew the *combined* property
tax total (levy limit + embedded debt exclusion) at the 2.5%+new-growth
rate for FY2032-2040 — which silently compounded the debt-exclusion
dollars at that rate too. That's wrong: excluded amounts aren't subject to
the 2.5% cap and don't organically grow with the tax base; if anything
they gently *decline* as bonds retire (absent new exclusions, which this
"keep what we have" baseline already doesn't assume). Quantified: holding
FY2031's \\${debt_excl_fy31:,.0f} debt exclusion flat through FY2040 (the
corrected treatment) vs. letting it compound at `trend_corrected`'s
{ng_pct_trend:.3%}+2.5% rate for 9 more years (the old, incorrect
behavior) would have produced \\${debt_excl_fy40_if_uncorrected:,.0f} by
FY2040 — **\\${debt_excl_fix_magnitude:,.0f} of phantom property tax
revenue** that this fix removes.

**Now**: `debt_exclusion_revenue` is held flat at the FY2031 level for
FY2032-2040, identical in both scenarios (no new debt exclusions assumed —
the same policy this model already applies on the expense side for
`debt_service`, see `baseline_expense_forecast_fy26_40_methodology.md`).
`property_tax_operating` (the levy-limit-only component) is what actually
grows at the statutory/new-growth rate. `property_taxes` (the total,
unchanged from before) = `property_tax_operating` + `debt_exclusion_revenue`.

This resolves, in the direction Ben's question suggested, the "recommended
next step" flagged in an earlier draft of this doc (bond-by-bond
amortization detail) — we now have the annual bond-by-bond total through
FY2031, though not each bond's individual maturity/retirement date, so
`debt_exclusion_revenue` still can't be modeled as *declining* post-FY2031
(only held flat) without more data.

## Why this matters: new growth compounds — a small rate difference becomes a large gap

Isolating just the new-growth assumption's effect on property tax (both
scenarios share the same 2.5% statutory mechanic and the same known
committed overrides/debt exclusions, so this gap is purely the new-growth
difference, nothing else):

| Fiscal Year | trend_corrected − town_assumptions (annual) | Cumulative since FY2026 |
|---|---|---|
| FY2026 | ${prop_tax_gap[2026]:,.0f} | ${cumulative_gap[2026]:,.0f} |
| FY2030 | ${prop_tax_gap[2030]:,.0f} | ${cumulative_gap[2030]:,.0f} |
| FY2035 | ${prop_tax_gap[2035]:,.0f} | ${cumulative_gap[2035]:,.0f} |
| FY2040 | ${prop_tax_gap[2040]:,.0f} | ${cumulative_gap[2040]:,.0f} |

In year one, the gap between the Town's $2,500,000/yr assumption and the
trailing-actual {ng_pct_trend:.3%}/yr rate is barely noticeable
(${prop_tax_gap[2026]:,.0f}). By FY2040 it's **${prop_tax_gap[2040]:,.0f}
of additional annual property tax revenue** from that one assumption
alone, and **${cumulative_gap[2040]:,.0f} cumulatively** over the
15-year window — because new growth doesn't just add revenue in the year
it happens, it permanently raises the levy base that the next year's 2.5%
statutory increase (and the year after's new growth) compounds on top of.
This is the same mechanism the founding whitepaper's thesis rests on
(new growth at the 80th percentile vs. the 25th percentile would likely
have avoided four historical overrides) — it's just more visible here
because the forecast window is long enough for the compounding to show up
as a large, striking number rather than a small annual difference. Directly
useful for public communication: "getting new growth right" isn't a
one-time, modest-sounding win — it's a structural lever whose payoff grows
every year it's sustained.

## Physical translation — how much actually gets built, in `trend_corrected`

Added 2026-08-29 (Ben: "can we retroactively make the baseline forecast
match this format so we can say, in the baseline, how much gets built or
renovated?"). Two new columns, `implied_res_new_units` and
`implied_com_new_sqft`, decompose `trend_corrected`'s existing new-growth
$ figure each year into physical counts — **purely additive**, this does
not change `property_taxes` or any other dollar figure above, which are
identical to what's already reported and memorialized.

The decomposition uses the same 5-category trend shares established for
Phase 2 (`scripts/new_growth_scenario_forecast.py` — see that script's
module docstring for full sourcing): residential new construction
({TREND_RES_NEW_PCT:.4%}/yr) and renovation ({TREND_RES_RENO_PCT:.4%}/yr),
commercial new construction ({TREND_COM_NEW_PCT:.4%}/yr, structurally
near-undetectable — see `land-value-map/METHODOLOGY.md` Section 3b),
commercial renovation ({TREND_COM_RENO_PCT:.4%}/yr), and commercial
personal property ({TREND_COM_PP_PCT:.4%}/yr — business equipment/
furniture/fixtures, split out from what used to be one blended "other"
bucket once the Town's own Tax Classification Hearing data confirmed it's
a distinct, now-dominant share of commercial new growth — see the
Personal Property entry below). New-construction dollars are converted to
units/sqft via the same appreciated $/unit ($430,000 in FY2026,
recalibrated 2026-09-22 from $324,000, growing 4.96%/yr) and $/sqft ($518 in FY2026, growing 1.28%/yr) Phase 2 uses.

`town_assumptions` is **not** decomposed this way — the Town's own $2.5M/yr
figure is a flat planning assumption they never broke out by construction
type, so inventing a split for it would be fabricating detail the source
doesn't have.

A real, worth-noting finding from this: the implied unit count *declines*
over the forecast window (172 units/yr in FY2026 → 153/yr by FY2040), even
as the dollar total keeps growing. That's because residential values
appreciate (4.96%/yr) faster than the new-growth dollar total compounds
(~2.5% statutory + 1.277% new growth, roughly 3.8%/yr blended) — so fewer
physical units are needed each year to sustain the same dollar contribution
as the ones already assumed get more valuable. Not a claim about actual
future construction pace, just what the dollar assumption implies if held
to this physical translation.

## Personal property: split out of "commercial," its own trend

Added 2026-08-30 (Ben: does commercial assessed value include non-land/
non-building property, and does it matter?). Confirmed via the Town's own
FY2022-2025 Tax Classification Hearing presentations (Board of Assessors)
that the "commercial" trailing rate used throughout this project is
actually DOR's **CIP** total (Commercial + Industrial + Personal Property
combined - Industrial is negligible). Personal property (business
equipment/furniture/fixtures, tracked in a wholly separate roll from the
parcel-level real estate data this project otherwise uses) has grown from
36.4% to 86.3% of CIP new-growth tax dollars over four straight years, as
real commercial real estate growth collapsed (full table and sourcing:
`scripts/new_growth_scenario_forecast.py`'s Personal Property section).
It's driven by business/equipment activity, not construction, so it gets
its own trend rate (**{TREND_COM_PP_PCT:.4%}/yr**, far more stable
year-to-year than real commercial's) and stays fixed at that rate in
`trend_corrected` - it's not construction-driven, so it isn't part of the
physical-translation columns above.

## Chestnut Hill Commercial Area (CHCA)

Added 2026-08-29, identically to both scenarios. Zoning approved by Town
Meeting 217-20, May 28-29, 2026 (City Realty, 1280-1330 Boylston St - see
`scripts/new_growth_scenario_forecast.py` module docstring for full
project detail). Uses RKG's own independent scenario specifically (not the
City Realty average - see the import comment above for why: EDAB and RKG
both came in more conservative than the developer's 3 scenarios, and a
conservative, independent figure fits this baseline's "keep what we have"
framing better than the developer's own numbers), from the ERSC report
Appendix (p.551-555) - Ben's transcription in `data/Brookline property tax
revenue over 20 years.xlsx`, "Fiscal Impact Model" tab. Split across two
revenue lines: **${CHCA_PROPERTY_TAX_RKG:,} in property tax** (residential
+ commercial real/personal property tax - the only portion that counts
toward the Prop 2.5 levy limit) and **${CHCA_LOCAL_RECEIPTS_RKG:,}
in local receipts** (local rooms tax + motor vehicle excise - a separate
revenue category, doesn't count toward the levy limit at all). Both ramp
on the same straight-line schedule, FY{CHCA_CONSTRUCTION_START_YEAR}-
{CHCA_FULL_STABILIZATION_YEAR} (construction "not planned to begin until
2028" at the earliest per the developer; no public building-by-building
phasing found, so the ramp shape is a stated assumption, not sourced
phasing).

## State Aid & Local Receipts — `trend_corrected` ignores the Town's figures entirely

These two lines don't have a "known committed facts" component analogous
to a legislated override, so `trend_corrected` doesn't need the delta
method — it simply extends the last known **actual** figure (FY2025)
forward at a trailing actual CAGR, for all of FY2026-2040, without
reference to the Town's own forecast at all:

- **State Aid** (the exception, changed 2026-10-14): the Town's FY2026 figure and the
  adopted FY2027 budget's, then **2.5%/yr**, the rate in the Town's own long-range plan.
  The trailing FY2015-2025 rate ({sa_cagr_actual:.2%}/yr, from ${sa_2025:,.0f} in FY2025)
  includes FY2019's one-year 8.6% rise; without it the rate is about 3.0%, FY2019-25 2.0%,
  FY2005-25 1.9%. Ben chose the conservative rate. `town_assumptions` instead uses the Town's own
  FY2026-2031 figures unmodified, extended at **{sa_cagr_town:.2%}/yr**
  (the rate those figures themselves imply) for FY2032-2040.
- **Local Receipts**: FY2025 actual `local_receipts_act_total`
  (${lr_2025:,.0f}) grown at **{lr_cagr_actual:.2%}/yr** (trailing actual
  CAGR FY2019-2025 — FY2019, not FY2015, is the anchor specifically to
  skip the FY2020-2021 COVID dip). `town_assumptions` instead uses the
  Town's own FY2026-2031 figures unmodified, extended at
  **{lr_cagr_town:.2%}/yr** for FY2032-2040. **Why not correct the Town's
  own figure instead of ignoring it?** An earlier draft did exactly that —
  scaled the Town's FY26-31 figure up by the actual-vs-estimate ratio
  (~140%) rather than building fresh from the FY2025 actual. Superseded:
  building directly from the actual base is simpler, doesn't require a
  separate correction-factor concept, and is consistent with how State Aid
  is now handled too. (For reference: we still have hard evidence — the
  DLS Local Receipts Actual-vs-Estimate file — that actual Local Receipts
  have run 18-48% above the Recap Sheet estimate every year FY2017-2025,
  which is *why* trend_corrected doesn't use the Town's figure here at
  all; the Town's own Financial Plan confirms this is deliberate
  conservative budgeting policy, not a forecasting miss.)

## Local receipts beyond CHCA: building permits and meals tax

Added 2026-08-30 (Ben: new commercial/residential construction generates
new local receipts too, not just via CHCA specifically), `trend_corrected`
only - same reasoning as the physical-translation columns above,
`town_assumptions`' flat $ figure isn't decomposed by type. Full sourcing
in `scripts/new_growth_scenario_forecast.py`'s module docstring.

- **Building permits**: applied to the four *real estate* new-growth
  categories (res-new, res-reno, com-new, com-reno) - personal property is
  excluded (equipment purchases don't need a building permit; see the
  Personal Property entry below). Ben confirmed permits are pulled for
  renovation too, charged as a % of construction cost, at
  **{BUILDING_PERMIT_RATE:.2%}** of new-growth *value* (not levy-applied
  $) through FY2026, rising to **{BUILDING_PERMIT_RATE_FY2027:.2%}** from
  FY{BUILDING_PERMIT_RATE_INCREASE_FY} on. The $20-per-$1,000 rate comes
  from the Town's own fee schedule
  (brooklinema.gov/183/Permit-Fee-Schedule, effective 2022-07-18), and the
  increase to "$21 / $1,000 of estimated cost, with specific exceptions"
  from a dated notice on brooklinema.gov/172/Building-Department effective
  July 1, 2026 - the first day of FY2027 (found 2026-09-04; the dedicated
  fee-schedule page still showed the old rate at that date, so it isn't
  reliable on its own). No residential/commercial or new-vs-renovation
  distinction. Cross-checked against actual collections
  (DOR's itemized local-receipts data, `data/revenue & expenditures all MA/
  LocalReciptesActVsEst {{year}}.xls`, pooled across the only 3 years
  it's cleanly separated - FY23-25, a DOR reporting-format change limits
  this): {BUILDING_PERMIT_RATE_ACTUAL_COLLECTIONS:.2%}, running somewhat
  below the statutory rate. A one-time fee tied to that year's
  construction activity, not a persistent levy-base addition.
- **Meals tax**: split into an organic trend (**{MEALS_TAX_ORGANIC_CAGR:.2%}/yr**,
  FY19-25 actual - inflation/spending growth at existing restaurants) plus
  an increment tied to cumulative new commercial sqft built since the
  forecast start, at **${MEALS_TAX_INTENSITY_PER_SQFT:.4f}/sqft/yr** (a
  citywide average intensity, not a restaurant-specific rate - restaurants
  are almost always tenants inside larger mixed-use/retail-classified
  buildings, not their own assessed class, so no clean way to isolate a
  restaurant share of new commercial sqft from parcel data). Room tax is
  *not* generalized this way - hotels are the outlier commercial type
  (room tax grew 11.3%/yr FY17-25 vs. 5.5%/yr for meals tax), and is
  already handled correctly for CHCA (the one real hotel project in this
  forecast) via its own project-specific figures.

Both are pulled out of the generic Local Receipts trend before extending
the rest, to avoid double-counting each one's own historical growth twice.

## New debt exclusions beyond the known schedule — still assumed at $0, FY2026-2040

The "Debt exclusion carve-out" section above covers the *known, committed*
schedule (now precisely decomposed, bond-by-bond total, through FY2031).
Beyond that known schedule, this model still assumes **zero new debt
exclusions** are authorized FY2026-2040 - stated explicitly rather than
left as a silent gap, per the same logic as excluding new operating
overrides: both require a townwide ballot vote, so neither belongs in a
"keep what we have" baseline.

This is a real, likely-understating simplification worth flagging. Per
`data/brookline_overrides_debt_exclusions_history.csv`
(affordablebrookline.com/past-overrides, cross-validated 2026-08-28 against
this project's own override history - 4 of 5 operating-override dollar
amounts match exactly), Brookline has authorized a **new** debt exclusion
roughly every 1.5-2 years since 2015: Edward Devotion School (2016), High
School renovations (2019), Driscoll School (2021), Newbury College land
(2022), Pierce School (2024), Fire Station (2025). If that cadence
continues, actual property tax revenue (and debt service, on the expense
side) would run higher than either scenario shown here. We don't attempt
to model that continuation quantitatively — no dated schedule of *specific
future* projects exists (see the Baker School note below for the one real
candidate found so far).

**A specific, real candidate for "the next one"**: a 2019 internal BPS
staff memo (`data/2019-09-09-School-Building-Facility-Planning-Staff-Notes.pdf`,
an old informal draft, not a current Town-adopted plan) projected the
Baker School would reach the end of its lifecycle "by 2028" and require
renovation/expansion, with no funding plan yet identified at that writing —
unlike Pierce and Driscoll, which have since both gotten debt exclusions
(2024 and 2021 respectively). Baker has not. Worth verifying against a
current source before relying on it further — see
`.claude/memorialized.md`, 2026-08-28.

## Free Cash & Other Available Funds — identical in both scenarios

No defensible trend basis: these are fund-balance draws (prior-year
turnback, reserve appropriations), not an organically growing revenue
source. Both scenarios use the Town's own FY2026-2031 figures, held flat
at the FY2031 level for FY2032-2040. This is a simplification, not a
forecast — flagged here rather than given a fake trend line, and it's the
one place the two scenarios remain identical throughout the whole horizon
by design, not by omission.

## What this deliberately excludes

- **New voter overrides (operating or debt exclusion)** — by design. This
  baseline shows what happens *without* one; sizing the resulting gap
  against expense growth is Phase 5's job. See the debt-exclusions section
  above for why this is flagged as a likely-understating simplification,
  not a neutral one.
- **New-growth acceleration from policy change** (upzoning, permitting
  reform) — Phase 2's job, layered on top of this baseline. Chestnut Hill
  Commercial Area is the one exception: it's a real, now-confirmed,
  specific project (not a policy-change scenario), so it's included in
  both scenarios here directly — see the CHCA section above.
- **Expense side entirely** — this file is revenue-only. Phase 3 (baseline
  expenses) and Phase 4 (marginal expense impact of new growth) are
  separate, not-yet-built pieces.

## Sanity check

The Town's own FY2026-2031 figures imply total expenditure growing at a
4.85% CAGR — well above either revenue scenario here
({total_cagrs['town_assumptions']:.2%} / {total_cagrs['trend_corrected']:.2%}). That
directionally matches, rather than contradicts, the growing structural
deficit the Town's own LRFP already shows (mostly school-driven). It's not
independent validation of the *forecast* method, but it does confirm the
model isn't producing revenue growth that's implausibly out of step with
what the Town itself expects on the expense side over the years we can
directly check.

Note `trend_corrected`'s FY2026 total (${fy26_totals['trend_corrected']:,.0f})
is now higher than `town_assumptions`'s (${fy26_totals['town_assumptions']:,.0f})
even in FY2026 itself, since State Aid and Local Receipts are built from
FY2025 actuals rather than the Town's own FY2026 figure. This is expected,
not a bug — it's the direct consequence of fixing the FY2026-2031
treatment per Ben's review comment above.

## Sources

- `data/FY27-FY31-Long-Range-Financial-Plan.pdf` (Town's own forecast, FY2026-2031 base)
- `output/brookline_historical_financials_fy05_25.csv` (trailing actuals, FY2005-2025)
- `data/SOURCES.md` (full external-source catalog)
- `.claude/memorialized.md`, 2026-08-28 entries (decision log, incl. the
  Town's-forecasts-run-conservative cross-cutting theme this model builds on)
"""
    with open(METHODOLOGY_FILE, "w") as f:
        f.write(doc)


if __name__ == "__main__":
    main()
