"""
Phase 3: "Keep what we have" baseline General Fund expense forecast, FY2026-2040.

No marginal expense impact of new growth (that's Phase 4, layered on top of
this) and no policy changes to service levels. Two scenarios, FY2026-2040,
for each of 5 expenditure categories:

  A. "town_assumptions" - the Town's own published FY26-31 Long-Range
     Financial Plan forecast (`output/town_own_forecast_fy26_31.csv`),
     unmodified, then mechanically extended to FY2040 at the growth rate
     those FY26-31 figures themselves imply.
  B. "trend_corrected" - the Town's own FY26-31 figures for FY2026-2031
     (same as A - see "Why both scenarios share the Town's FY26-31 base"
     below for why this isn't built independently from DLS Schedule A the
     way Phase 1's State Aid/Local Receipts were), then diverges starting
     FY2032, extended instead at a trailing-actual CAGR computed from 21
     years of Schedule A history (`brookline_historical_financials_fy05_25.csv`).

The 5 categories, and which treatment each gets:

  - **departmental_town** (Town operating departments, ex-schools):
    `town_assumptions` unchanged (single blended figure, as below).
    `trend_corrected` (added 2026-09-02, Ben: "break apart the
    departmental single blended CAGR... keep it simple") is
    `departmental_category_forecast.py`'s sum of Schedule A's own 5
    functional categories (General Government, Public Safety, Public
    Works, Human Services, Culture & Recreation), each own-trended
    (trailing-5yr - no window-selection complexity needed here, unlike
    schools/benefits, since none of these 5 rates is an outlier). FY2026-
    2031 is a pure decomposition of the Town's own known aggregate by
    FY2025 share (ties out exactly, not an independent re-estimate);
    FY2032-2040 is where the 5 categories' own rates diverge from a
    single blended rate. **Run `departmental_category_forecast.py`
    before this script** - same pattern as schools/benefits.
  - **schools**: `town_assumptions` unchanged (as above). `trend_corrected`
    (added 2026-09-02, Ben: "build the category-level schools forecast")
    is no longer a single blended Schedule-A CAGR - it's the sum of
    `schools_category_forecast.py`'s 9 separately-trended DESE function
    categories (Teachers, Pupil Services, Benefits-excluded-since-that's-
    modeled-separately-below, etc.), applied for the FULL FY2026-2040
    window, not just FY2032-2040 - see that script's own module docstring
    for the two real methodological choices behind it (Schedule-A-vs-DESE
    scope reconciliation, and why it deliberately uses 16-year not
    trailing-5yr rates). **Run `schools_category_forecast.py` before this
    script** - it reads that output directly.
  - **benefits**: `town_assumptions` unchanged (single combined total, as
    below). `trend_corrected` (added 2026-09-02, Ben: "do the same
    disaggregation... for the big benefits bucket") is no longer a single
    blended total either - `benefits_category_forecast.py` models
    Pensions, Group Health, OPEB, and Other separately, resolving what
    "The pension/OPEB handoff" section below originally called a
    necessary compromise ("trending pensions or OPEB separately past
    FY2031 would produce nonsense... so trend the combined total
    instead") - now solvable properly because that script uses the
    Town's own real FY26-31 schedule (where pensions collapsing to
    Normal Cost and OPEB's redirect are already known facts, not trended
    guesses) plus each category's own real historical data for the
    FY2032-2040 extension. **Run `benefits_category_forecast.py` before
    this script** - it reads that output directly, same pattern as schools.
  - **debt_service** and **other_nondept** (nondept_general +
    special_appropriations_cip + nondept_reserve_fund + non_appropriated,
    combined): **identical in both scenarios**, Town's own FY26-31 figures
    then held flat at the FY2031 level for FY2032-2040 - no defensible
    trend basis for either (see their sections below), same treatment
    Phase 1 gave Free Cash/Other Available Funds on the revenue side.

## The pension/OPEB handoff - why benefits is trended as one combined total

Brookline's pension system reaches full funding in FY2030. Once a pension
plan is fully funded, required Town contributions fall sharply - and by
GASB/actuarial practice that freed funding capacity gets redirected into
the Town's *other* unfunded liability, retiree health insurance (OPEB) -
so OPEB jumps in the same year pensions crash:

    FY2029      FY2030      FY2031
    Pensions:            $47.8M      $44.1M      $7.3M
    OPEB:                 $5.7M       $5.9M      $43.0M
    Combined benefits:  $121.4M     $122.3M     $127.8M

Trending pensions or OPEB *separately* past FY2031 would produce nonsense
(pensions trending toward zero/negative, OPEB trending at an explosive
rate) - neither is a real growth trend, just a one-time structural
reallocation between two liabilities. The combined total grows smoothly
throughout (~5-7%/yr) because the underlying economics - total cost of
pensions + retiree health + group health - didn't change, only the
internal split did. So FY2032-2040 trends the combined `nondept_benefits`
total only; the CSV doesn't carry pension/OPEB sub-lines (those are in
`town_own_forecast_fy26_31.csv`'s `benefits_detail` rows for FY26-31 if
needed).

**Pension correction, fixed 2026-08-30**: the pension figures in
`town_own_forecast_fy26_31.csv` are transcribed from the FY2027 Financial
Plan, which explicitly states it's still built on the **January 1, 2022**
actuarial valuation - not the newer January 1, 2024 valuation
(`data/Brookline-Retirement-System-2024-Actuarial-Valuation.pdf`, Segal,
filed with PERAC/published via mass.gov), whose real funding schedule
differs: **+5.1% for FY26-29, -12.1% for FY30, +26.0% for FY31** vs. the
Town's own published figure. Ben's direction: update *this project's own*
forecast with the corrected numbers, but leave `town_own_forecast_fy26_
31.csv` itself untouched as a faithful transcription of what the Town
actually published (its own `result` surplus/deficit rows are also built
on the stale figure, and correctly re-deriving those needs the Town/School
TSP split formula, which isn't confirmed precisely enough to safely edit
that file in place). So: **`town_assumptions` keeps the Town's own
(stale) pension figure for FY2026-2031, unmodified** - consistent with
that scenario's whole premise, taking the Town's stated numbers at face
value. **`trend_corrected` swaps in `PENSION_ADC_2024_VALUATION` for
FY2026-2031** - the same "this project's own, corrected" role that
scenario already plays for property tax new-growth/state aid/local
receipts elsewhere. Only the pension sub-line changes; group health, OPEB,
and the other `nondept_benefits` components stay exactly as published.
FY2032-2040 for both scenarios is otherwise unchanged - `trend_corrected`
compounds its Schedule A trailing CAGR off the *corrected* FY2031 base,
so the correction carries forward automatically. See `.claude/
memorialized.md`, 2026-08-30 entries, for the full comparison table.

## Why both scenarios share the Town's FY26-31 base for departmental/schools/benefits

Phase 1 built `trend_corrected` State Aid and Local Receipts entirely
independently of the Town's figures, for the *whole* FY2026-2040 window,
because DLS Schedule A actuals and the Town's own published actuals are
the same underlying accounting for revenue - no scope mismatch. That's
NOT true on the expense side. Checked directly: the Town's own FY2026
total expenditure ($419,608,131) is **15.06% above** DLS Schedule A's
FY2025 actual total expenditure ($364,676,155) - a one-year jump far
outside the ~5%/yr the Town's own FY26-31 figures otherwise imply
(4.85% CAGR) and outside Schedule A's own 20-year historical total CAGR
(3.92%-5.11% depending on window). This isn't real one-year expense
growth - it's a scope/timing difference between the two sources (e.g. the
Town's forecast may reflect newly-effective debt service or an override
not yet in the FY2025 Schedule A actual). Building `trend_corrected`
independently from Schedule A for FY2026-2031 the way Phase 1 did for
state aid would silently import that ~15% phantom jump as if it were a
one-year trend-vs-Town divergence, which it isn't. So instead:
departmental/schools/benefits use the Town's own (identical, real,
adopted-budget) FY26-31 figures in *both* scenarios, and only diverge
starting FY2032, using Schedule A's trailing-actual CAGR as the
independent basis for `trend_corrected` from that point on - the same
"anchor on known facts, diverge only in the rate applied afterward"
principle Phase 1 used for property tax's delta method, just without
needing an explicit delta series since there's no known-committed-dollars
component to preserve here.

## debt_service_regular and special_appropriations_cip (inside other_nondept): the 6.6% CIP policy, FY2032-2040 (revised 2026-09-02)

**Where these actually sit in the Town's budget** (Ben, 2026-09-02: "where
does the non-debt exclusion dept repayment and non-dept CIP expenditure
sit in the budget?"), from the FY2027 Financial Plan's own Program Budget
structure: all of debt service, reserve fund, special appropriations,
non-appropriated funds, and benefits are booked under the single
**Non-Departmental** budget classification (as opposed to the ~18
individual department budgets) - specifically "Non-Departmental - Debt
Service" (p.338 - $49.4M FY27, the excluded AND non-excluded/regular
portions combined in one appropriation line, not separated in the actual
budget book; the split shown here is only disclosed in the LRFP/CIP
planning tables, Section VII) and "Non-Departmental - Special
Appropriations" (p.384 - $21.7M FY27, which bundles the CIP pay-as-you-go
cash component with other special-appropriation items, e.g. trust fund
deposits).

**debt_service**: Schedule A's own history shows this line is far too
lumpy/bond-driven to support a simple trend - CAGR is wildly window-
dependent (15.08% over FY2020-25, 14.46% over FY2015-25, but only 5.17%
over FY2005-25), because it moves in step changes when individual bonds
are authorized, not smoothly. Phase 1 explicitly assumes **zero new debt
exclusions** authorized FY2026-2040 (a "keep what we have" baseline can't
assume a new townwide ballot vote), so `debt_service_excluded` stays held
flat at FY2031 post-2031, consistent with that. But `debt_service_regular`
- the non-excluded, "tax-supported CIP" portion - has a real, known,
*formulaic* basis the Town itself uses (see below), so as of 2026-09-02
it's no longer held flat.

**The 6.6% CIP policy, applied to `debt_service_regular` for FY2032-2040**
(Ben: "should we tackle the 6.6%-of-net-revenue CIP policy open item?"):
the Town's own CIP Financing Policy requires 6.6% of prior-year Net
Revenue be dedicated to the CIP each year, split **4.5% for debt-financed
CIP and 2.1% for pay-as-you-go CIP** (`data/FY2027-Financial-Plan.pdf`,
p.352 - two separately-targeted components, not one blended rate, since
they land in different budget lines). Net Revenue = Total Revenue − Debt
Exclusions − Free Cash − Non-Appropriations (the small HCA/Opioid
Stabilization Fund subtraction, ~$300-350K/yr, is omitted as immaterial).

**The rate actually applied is not the stated 4.5% target - it's the
Town's own realized rate, checked directly rather than assumed.**
Computed `debt_service_regular ÷ prior-year Net Revenue` for each of the
5 real FY2027-2031 years (using the Town's own published revenue and
debt figures): **3.93%, 3.69%, 3.94%, 3.83%, 3.84% - averaging 3.85%**, a
real and persistent ~0.7 percentage-point gap below the stated 4.5%
target, not noise or a single-year anomaly. This mirrors a finding
already in this same policy: FY2027 itself uses a reduced 6.0% *combined*
rate, not 6.6%, "to provide relief to the operating budget," per the
Financial Plan's own text - the Town's stated CIP policy is consistently
an aspirational ceiling it doesn't fully fund, not a rate it actually
hits. Consistent with this project's standing convention of trusting
trailing-actual behavior over a stated target/aspiration (the same logic
Phase 1/3 already apply everywhere else), `debt_service_regular` =
**3.85% × prior-year Net Revenue** for FY2032-2040 - not 4.5%. FY2032-2040
uses each *scenario's own* revenue forecast
(`baseline_revenue_forecast_fy26_40.csv`) to compute Net Revenue (using
the Town's own revenue path only to compute the 3.85% rate itself, since
that's what the Town's real figures were actually measured against), so
`debt_service_regular` now genuinely diverges between `town_assumptions`
and `trend_corrected` post-2031 - a real, meaningful difference, since a
higher/lower revenue outlook literally changes the Town's own CIP debt
capacity under this rate.

**`special_appropriations_cip` - revised 2026-09-02, now also formula-
grown, after a Non-Departmental budget deep-dive (Ben: "let's dig into
the non-departmental budget") corrected an earlier, wrong conclusion.**
The prior version of this script found `special_appropriations_cip`
(inside `other_nondept`) matches the Town's own **"Non-Departmental -
Special Appropriations"** line exactly ($20,045,169 FY2026, $21,671,104
FY2027) and, seeing the FY2027 CIP funding table's "Revenue Financed"
(pay-as-you-go) figure was only $7,438,594 - about a third of that - it
concluded the rest was unrelated non-CIP appropriations and left the
whole line flat. **That conclusion was wrong.** The FY2027 Financial
Plan's own Expenditures overview (p.20/13) states directly: "the direct
appropriations to fund capital projects will be $21,323,327" for FY27 -
matching Revenue Financed ($7,438,594) + Free Cash for CIP ($12,384,732)
+ Overlay Surplus ($1,500,000) almost exactly ($21,323,326, a $1 rounding
gap). Add the small Opioid Settlement Fund carve-out ($347,777, the same
figure as the Net Revenue calc's "HCA/Opioid Stab Fund" line) and it ties
out to the stated $21,671,104 exactly. **So this field is nearly ALL
CIP-related after all** - just funded through three sources (the 2.1%
policy slice, a real chunk of Free Cash, and a small one-time Overlay
Surplus item), not narrowly the 2.1% slice alone. Since it's genuinely
capital/CIP-driven, it gets the same treatment as `debt_service_regular`:
a realized (not stated) trailing rate against prior-year Net Revenue,
computed from the same LRFP-sourced FY2027-2031 series (**6.58%, 6.43%,
6.13%, 6.06%, 6.08% - averaging 6.26%**), applied for FY2032-2040.

**A separate, real, disclosed finding from the same dig, not reconciled**:
the LRFP deck (`data/FY27-FY31-Long-Range-Financial-Plan.pdf`, presented
Jan 2026 - the source for `town_own_forecast_fy26_31.csv`, including this
field) projected FY2027 `special_appropriations_cip` at $23,556,095; the
FY2027 Financial Plan's own later, more detailed Program Budget shows the
actual adopted FY2027 figure is $21,671,104 - a real ~$1.9M/8% gap. This
is an 18-month-ahead planning projection vs. the actual adopted budget
for the same year, not an error in either document (the same kind of
provisional-vs-settled gap already found and disclosed in the FY2025
department-FTE numbers, see `department_fte_annual_history.py`). Per this
project's standing convention, `town_own_forecast_fy26_31.csv` stays an
unmodified transcription of the LRFP (not silently corrected to the
newer Program Budget figures) - so the realized-rate calculation above,
and `town_assumptions` generally, both still reflect the LRFP's own
(slightly higher) figures, consistent with the rest of that scenario.

## The real, formally-approved CIP and Free Cash Policy targets (2026-09-02, later same day)

Ben asked a direct clarifying question that surfaced a real correction:
"CIP is set in the forecast at 6.26% of prior year's general fund
revenue and includes servicing debt (both excluded and not)... is that
right?" - **no**, on both points, and tracing down the real numbers
(`data/FY2027-Financial-Plan.pdf` p.459, "TOWN OF BROOKLINE FISCAL
POLICIES, As approved by the Select Board on September 17, 2024" - the
authoritative version, superseding narrative-text figures like "7.5%" or
"8.1%" found in other parts of the same document, which describe
specific-year computed *outcomes*, not the codified target) gave a
cleaner, more precise picture than the single blended 6.26% rate this
script was using:

- **Excluded debt is never part of this at all** - it's funded
  dollar-for-dollar by dedicated debt-exclusion tax revenue, outside the
  2.5% levy cap and outside the CIP policy entirely. `debt_service_
  excluded` already reflects this; it was never part of `debt_service_
  regular` or `special_appropriations_cip`.
- **The codified CIP targets**: Debt-Financed **4.5%** + Tax-Financed/
  Revenue-Financed (paygo) **2.1%** = combined **6.61%** of prior-year
  Net Revenue - this is the "core" policy, funded from ordinary
  operating revenue.
- **Free Cash then tops that combined total up to a floor of not less
  than 8%** ("Capital Improvement Program (CIP) — Remaining Free Cash
  shall be dedicated to the CIP so that total CIP funding... is not less
  than 8%") - a real, second, *formal* tier of the same policy, not ad
  hoc extra spending, though genuinely a different, less predictable
  funding source (Free Cash is a certified budget-performance residual,
  not a trend-following revenue line - see the Free Cash section below).

**The full Free Cash Policy priority order** (same appendix, p.458-459 -
"Free Cash shall not be used for Operating Budget purposes"), useful
context even where not directly modeled:
1. Appropriated Budget Reserve - 0.25% of prior-year Net Revenue (the
   other 0.75% of the 1% Reserve target comes from the Property Tax
   Levy directly, not Free Cash - already embedded in ordinary revenue,
   not a separate Free Cash draw)
2. Unreserved Fund Balance/Stabilization Fund - top up to ≥20% of
   revenue if below that level
3. Liability/Catastrophe Fund - top up to its 1%-of-prior-year-Net-
   Revenue target
4. **Capital Improvement Program** - remaining Free Cash, to reach the
   8% combined floor
5. Affordable Housing Trust Fund - 15% of *remaining* Free Cash, if its
   balance is below $5M
6. Special Use - whatever's left, for pension/OPEB trust funds or other
   one-time uses

**Why the Liability/Catastrophe Fund isn't modeled as a formula despite
being formally in this order**: unlike the CIP targets (a recurring
*flow*, i.e. "fund this much every year"), the Liability Fund's target is
a *stock* - "maintain a fund balance equivalent to 1% of Net Revenue."
Its annual Free-Cash contribution is whatever's needed to close the gap
between the fund's actual balance and that target, which requires
tracking the fund's balance over time (contributions, investment
earnings, draws) - this project has no data on that balance's history.
Checked directly: the FY27 contribution was $2,182,237 (0.61% of FY26 Net
Revenue), well under a naive "1% every year" reading, confirming it's a
top-up amount, not a flat annual percentage - so it stays folded into
the flat, unmodeled `nondept_general` line rather than given a wrong
formula.

## trend_corrected's real CIP decomposition, FY2027-2032 (2026-09-02)

Given the real policy targets above, `trend_corrected` - this project's
own best-grounded estimate throughout, per its standing "don't treat the
Town's near-term figures as ground truth" principle already applied to
schools/benefits/departmental - now uses the FY2027 Financial Plan's own
real, single-source "6.6% CIP FUNDING POLICY" table (p.384, FY2027-2032)
directly for `debt_service_regular` and three new, separately-exposed
columns (`cip_revenue_financed`, `cip_free_cash`, `cip_overlay_surplus`)
instead of one blended proxy rate - genuinely better, more current data
than the LRFP-sourced lump this project's `town_assumptions` scenario
still (correctly, per its own "faithful transcription" convention)
carries. FY2026 has no real table data yet and falls back to the LRFP
lump (same as `town_assumptions` for that one year only); FY2033-2040
extends each of the three components at its own realized 6-year average
against prior-year Net Revenue (**debt 3.95%** vs. the 4.5% target,
**revenue-financed 2.30%** vs. 2.1%, **free-cash-to-CIP 2.90%** - combined
**9.15%**, above the Town's 8% floor - Overlay Surplus is explicitly
one-time and held at $0 for the extension, not trended). `town_
assumptions` is unchanged - still the LRFP-sourced lump for FY2026-2031,
its own (different) realized-rate extension for FY2032-2040.

## Free Cash: what it is, and why it's still held flat

Ben asked directly: "what is [Free Cash]? the surplus after we subtract
all expenses from revenue?" - close, but the real definition is more
specific (`data/FY2027-Financial-Plan.pdf` p.120): Free Cash is **the
portion of General Fund surplus revenue that's unrestricted and
available for appropriation, certified as of July 1 each year by the
Commonwealth's Department of Revenue (DOR)**. It's generated when actual
operating results beat budget - actual revenue exceeding estimates
and/or actual spending coming in under appropriation - adjusted for
changes in uncollected property taxes and any operating deficits. So:
favorable budget-vs-actual variance plus turned-back appropriations,
DOR-certified, not literally "this year's total revenue minus this
year's total expenses."

**No, the Town doesn't have an explicit target *level* for Free Cash
itself** - it's inherently a residual of how conservatively the Town
budgets and how much departments underspend, not something budgeted to a
number. What *does* have real, codified targets are its **downstream
uses** - the Stabilization Fund (≥20% of revenue), the Liability Fund
(1% of Net Revenue), and the CIP floor (8% of Net Revenue) - see the
Free Cash Policy priority order above. `free_cash` itself
(`baseline_revenue_forecast.py`) stays held flat at the FY2031 level for
FY2032-2040 in both scenarios, as before - still the right call given
what it actually is: not an organically growing revenue source, but a
certified, backward-looking measure of budget performance with no
defensible growth trend of its own.

**other_nondept** (nondept_general + special_appropriations_cip +
nondept_reserve_fund + non_appropriated): checked whether Schedule A's
`intergov_assessments`/`other_expenditures` lines could serve as a trend
basis for the whole bucket - they can't. Those two Schedule A lines sum to
$7.96M (FY2025 actual), while the Town's own equivalent residual
categories sum to $43.68M (FY2026) - a completely different scope
(Schedule A's standardized categories don't capture the Town's own
Capital Improvement Program appropriations or reserve-fund detail the
same way). `special_appropriations_cip` now has its own real formulaic
basis (above); the other three sub-lines (`nondept_general`, `nondept_
reserve_fund`, `non_appropriated`) - real detail on what's inside them
found via the same Non-Departmental dig: mostly trust-fund transfers
(Stabilization, Liability Insurance, Affordable Housing), Property
Insurance, the Reserve Fund appropriation itself, and MBTA/county
assessments - still have no comparable independent trend source, so they
stay held flat at FY2031, identical in both scenarios, same as before.

## Category tags for Phase 4 (fixed vs. variable, informational only)

Not modeled here - Phase 4's marginal-expense-impact-of-new-growth model
is where "does this category grow with new development" actually matters.
Tagged here as metadata only, so Phase 4 doesn't have to re-derive it:

  - departmental_town: discretionary (staffing/operational choices)
  - schools: semi-fixed (largely enrollment/contract-driven, real
    discretion in program scope)
  - benefits: fixed (contractual/actuarial - pension/OPEB/health rates
    aren't a Town year-to-year choice)
  - debt_service: fixed (bond payment obligations, fixed once issued)
  - other_nondept: discretionary (CIP and reserve-fund appropriations are
    policy choices)

Sources: see ../data/SOURCES.md and ../.claude/memorialized.md
Outputs:
  ../output/baseline_expense_forecast_fy26_40.csv  (the forecast, with the
    exact assumption applied to each cell baked in as columns, so the file
    is self-explanatory without cross-referencing this script)
  ../output/baseline_expense_forecast_fy26_40_methodology.md  (prose
    explanation + sourcing for every assumption)
"""
import csv

TOWN_FORECAST_FILE = "../output/town_own_forecast_fy26_31.csv"
REVENUE_FORECAST_FILE = "../output/baseline_revenue_forecast_fy26_40.csv"
HISTORICAL_FILE = "../output/brookline_historical_financials_fy05_25.csv"
SCHOOLS_CATEGORY_FILE = "../output/schools_category_forecast_fy26_40.csv"
BENEFITS_CATEGORY_FILE = "../output/benefits_category_forecast_fy26_40.csv"
DEPARTMENTAL_CATEGORY_FILE = "../output/departmental_category_forecast_fy26_40.csv"
OUT_FILE = "../output/baseline_expense_forecast_fy26_40.csv"
METHODOLOGY_FILE = "../output/baseline_expense_forecast_fy26_40_methodology.md"

FORECAST_YEARS = list(range(2026, 2041))
TOWN_YEARS = list(range(2026, 2032))
ANCHOR_YEAR = 2031
EXTEND_YEARS = list(range(2032, 2041))

OTHER_NONDEPT_SUBCATS = ["nondept_general", "special_appropriations_cip",
                          "nondept_reserve_fund", "non_appropriated"]

TOWN_ASSUM = "Town's own FY26-31 LRFP figure, as published (identical in both scenarios - see methodology doc)"
FLAT = "held flat at FY2031 Town figure (no defensible independent trend; identical in both scenarios)"

# --- 6.6% CIP Financing Policy, added 2026-09-02 (Ben: "should we tackle
# the 6.6%-of-net-revenue CIP policy open item?"). Source: FY2027
# Financial Plan p.352 ("a total of 6.6% of the prior year's net revenue
# be dedicated to the CIP, with 4.5% targeted for debt and 2.1% targeted
# for pay-as-you-go") and p.384's own "6.6% CIP FUNDING POLICY" table.
# See module docstring for the full reasoning, including the real,
# disclosed simplification of using the stated target split rather than
# an empirically-averaged one. ---
CIP_POLICY_PCT_DEBT = 0.045
CIP_FORMULA_NOTE = ("6.6% CIP Financing Policy: {pct:.2%} of prior-year Net Revenue "
                     "(Total Revenue - Debt Exclusions - Free Cash - Non-Appropriations), "
                     "per FY2027 Financial Plan p.352/384 - see methodology doc")

# --- Real, formally-approved CIP/Free Cash Policy targets, added
# 2026-09-02 (Ben: "let's build those formulas... and let's figure out
# how to forecast free cash"). Source: FY2027 Financial Plan p.459,
# "TOWN OF BROOKLINE FISCAL POLICIES, As approved by the Select Board on
# September 17, 2024" - the authoritative version, superseding the
# narrative-text figures (7.5%, 8.1%) found elsewhere in the same
# document, which describe specific-year computed OUTCOMES, not the
# codified target. The codified targets: Debt-Financed 4.5%, Tax-
# Financed/Revenue-Financed (paygo) 2.1%, combined 6.61%, of prior-year
# Net Operating Revenue; Free Cash then tops the combined total up to a
# floor of not less than 8% ("Capital Improvement Program (CIP) —
# Remaining Free Cash shall be dedicated to the CIP so that total CIP
# funding as a percent of the prior year's net revenue is not less than
# 8%"). See module docstring for the full Free Cash Policy priority order
# and why the Liability/Catastrophe Fund (a STOCK/balance target, not a
# recurring flow) isn't modeled here despite being formally part of that
# order - no fund-balance history available to track it properly.
CIP_POLICY_PCT_TOTAL_WITH_FREE_CASH = 0.08

# Real, per-year CIP funding breakdown, FY2027-2032 - the FY2027
# Financial Plan's own "6.6% CIP FUNDING POLICY" table (p.384), a single,
# self-consistent, real (not blended-from-a-different-vintage) source for
# all three components together. Used for trend_corrected's debt_service_
# regular/special_appropriations_cip FY2027-2032 (this project's own best
# estimate, per its standing "don't treat the Town's near-term figures as
# ground truth for trend_corrected" principle - same reasoning already
# applied to schools/benefits/departmental) - NOT used for town_
# assumptions, which stays a faithful, unmodified transcription of the
# LRFP (town_own_forecast_fy26_31.csv) throughout, per this project's
# standing convention.
CIP_FUNDING_TABLE = {
    2027: dict(debt=13_985_479, revenue_financed=7_438_594, free_cash=12_384_732, overlay=1_500_000),
    2028: dict(debt=14_367_683, revenue_financed=10_186_128, free_cash=10_034_894, overlay=0),
    2029: dict(debt=16_096_302, revenue_financed=9_207_977, free_cash=10_904_662, overlay=0),
    2030: dict(debt=16_462_008, revenue_financed=9_623_797, free_cash=11_536_390, overlay=0),
    2031: dict(debt=17_594_808, revenue_financed=9_292_699, free_cash=12_186_467, overlay=0),
    2032: dict(debt=17_514_813, revenue_financed=10_109_080, free_cash=13_123_183, overlay=0),
}


def read_revenue_forecast(scenario):
    """Returns {year: dict(total_revenue, debt_exclusion_revenue, free_cash)}
    FY2026-2040 for one scenario, from baseline_revenue_forecast.py's own
    output - used to compute Net Revenue for the 6.6% CIP policy formula."""
    out = {}
    with open(REVENUE_FORECAST_FILE) as f:
        for row in csv.DictReader(f):
            if row["scenario"] != scenario:
                continue
            y = int(row["fiscal_year"])
            out[y] = dict(total_revenue=float(row["total_revenue"]),
                          debt_exclusion_revenue=float(row["debt_exclusion_revenue"]),
                          free_cash=float(row["free_cash"]))
    if not out:
        raise ValueError(f"No rows found for scenario={scenario!r} in {REVENUE_FORECAST_FILE}")
    return out


def read_town_forecast():
    """Returns {subcategory: {year: value}} for expenditure rows, FY2026-2031."""
    out = {}
    with open(TOWN_FORECAST_FILE) as f:
        for row in csv.DictReader(f):
            if row["category"] != "expenditure":
                continue
            out[row["subcategory"]] = {y: float(row[str(y)]) for y in range(2026, 2032)}
    return out


def read_town_debt_exclusion():
    """Returns {year: value} for the revenue-side debt_exclusion row, FY2026-2031."""
    with open(TOWN_FORECAST_FILE) as f:
        for row in csv.DictReader(f):
            if row["category"] == "revenue" and row["subcategory"] == "debt_exclusion":
                return {y: float(row[str(y)]) for y in range(2026, 2032)}
    raise ValueError("debt_exclusion row not found in " + TOWN_FORECAST_FILE)


def read_schools_category_forecast():
    """Returns {year: total_schools_category_sum} FY2026-2040, from
    schools_category_forecast.py's own output - the sum of 9 separately-
    trended DESE function categories, replacing trend_corrected's schools
    line. Run that script first; this raises clearly if its output is
    missing rather than silently falling back to the old blended-CAGR
    method."""
    try:
        with open(SCHOOLS_CATEGORY_FILE) as f:
            return {int(r["fiscal_year"]): float(r["total_schools_category_sum"]) for r in csv.DictReader(f)}
    except FileNotFoundError:
        raise FileNotFoundError(
            f"{SCHOOLS_CATEGORY_FILE} not found - run schools_category_forecast.py first "
            "(it produces the category-level schools total this script's trend_corrected scenario now uses)."
        )


def read_benefits_category_forecast():
    """Returns {year: total_benefits_category_sum} FY2026-2040, from
    benefits_category_forecast.py's own output - Pensions/Group Health/
    OPEB/Other, each modeled separately, replacing trend_corrected's
    benefits line. Run that script first."""
    try:
        with open(BENEFITS_CATEGORY_FILE) as f:
            return {int(r["fiscal_year"]): float(r["total_benefits_category_sum"]) for r in csv.DictReader(f)}
    except FileNotFoundError:
        raise FileNotFoundError(
            f"{BENEFITS_CATEGORY_FILE} not found - run benefits_category_forecast.py first "
            "(it produces the category-level benefits total this script's trend_corrected scenario now uses)."
        )


def read_departmental_category_forecast():
    """Returns {year: total_departmental_category_sum} FY2026-2040, from
    departmental_category_forecast.py's own output - Schedule A's 5
    functional categories, each modeled separately, replacing
    trend_corrected's departmental line. Run that script first."""
    try:
        with open(DEPARTMENTAL_CATEGORY_FILE) as f:
            return {int(r["fiscal_year"]): float(r["total_departmental_category_sum"]) for r in csv.DictReader(f)}
    except FileNotFoundError:
        raise FileNotFoundError(
            f"{DEPARTMENTAL_CATEGORY_FILE} not found - run departmental_category_forecast.py first "
            "(it produces the category-level departmental total this script's trend_corrected scenario now uses)."
        )


def read_town_pensions():
    """Returns {year: value} for the benefits_detail,pensions row, FY2026-2031 -
    the Town's own (2022-actuarial-valuation-basis) pension figure, used to
    compute the correction below."""
    with open(TOWN_FORECAST_FILE) as f:
        for row in csv.DictReader(f):
            if row["category"] == "benefits_detail" and row["subcategory"] == "pensions":
                return {y: float(row[str(y)]) for y in range(2026, 2032)}
    raise ValueError("benefits_detail,pensions row not found in " + TOWN_FORECAST_FILE)


# Real pension funding schedule, Actuarial Valuation and Review as of
# January 1, 2024 (Segal, Brookline Contributory Retirement System, filed
# with PERAC / published via mass.gov - NOT the same basis as the Town's
# own published FY26-31 figures above, which the FY2027 Financial Plan
# states are still built on the January 1, 2022 valuation). Total
# Actuarially Determined Contribution (ADC) by fiscal year, "Funding
# schedule" table, p.26 - see `data/SOURCES.md` and `.claude/
# memorialized.md` (2026-08-30) for the full table and sourcing.
PENSION_ADC_2024_VALUATION = {
    2026: 40_001_411, 2027: 43_141_522, 2028: 46_528_131,
    2029: 50_180_589, 2030: 38_764_136, 2031: 9_164_987,
}


def read_historical():
    with open(HISTORICAL_FILE) as f:
        return {int(row["fiscal_year"]): row for row in csv.DictReader(f)}


def cagr(start, end, years):
    return (end / start) ** (1 / years) - 1


def main():
    town = read_town_forecast()
    hist = read_historical()
    schools_category = read_schools_category_forecast()
    benefits_category = read_benefits_category_forecast()
    departmental_category = read_departmental_category_forecast()

    other_nondept_town = {y: sum(town[c][y] for c in OTHER_NONDEPT_SUBCATS) for y in TOWN_YEARS}

    # Pension correction (added 2026-08-30, Ben: "update in our own forecast
    # but keep the town's numbers in the baseline") - town_own_forecast_fy26_
    # 31.csv stays an untouched transcription of the Town's own published
    # (2022-valuation-basis) pension figure; trend_corrected uses the real
    # 2024 valuation's ADC instead. As of 2026-09-02 this swap happens
    # entirely inside benefits_category_forecast.py (which imports
    # PENSION_ADC_2024_VALUATION directly, same constant, same correction) -
    # this script no longer computes it itself, since trend_corrected's
    # whole benefits line is now that script's cited output. `read_town_
    # pensions()` above is kept only in case a future script wants the
    # Town's own (stale) pension figure directly.

    dept_cols = ["exp_general_government", "exp_public_safety", "exp_public_works",
                 "exp_human_services", "exp_culture_recreation"]

    def sched_dept(y):
        return sum(float(hist[y][c]) for c in dept_cols)

    def sched_school(y):
        return float(hist[y]["exp_education"])

    def sched_benefits(y):
        return float(hist[y]["exp_fixed_costs"])

    # --- Town-implied FY26-31 rates (Scenario A, FY2032-2040) ---
    dept_cagr_town = cagr(town["departmental_town"][2026], town["departmental_town"][ANCHOR_YEAR], 5)
    school_cagr_town = cagr(town["schools"][2026], town["schools"][ANCHOR_YEAR], 5)
    benefits_cagr_town = cagr(town["nondept_benefits"][2026], town["nondept_benefits"][ANCHOR_YEAR], 5)

    # --- Trailing-actual Schedule A rates (Scenario B, FY2032-2040) ---
    # Trailing 5yr primary, consistent with Phase 1/2's convention; 10/20yr
    # cited in the methodology doc as a cross-check, not used directly.
    dept_cagr_trend = cagr(sched_dept(2020), sched_dept(2025), 5)
    school_cagr_trend = cagr(sched_school(2020), sched_school(2025), 5)
    benefits_cagr_trend = cagr(sched_benefits(2020), sched_benefits(2025), 5)

    dept_cagr_trend_10yr = cagr(sched_dept(2015), sched_dept(2025), 10)
    dept_cagr_trend_20yr = cagr(sched_dept(2005), sched_dept(2025), 20)
    school_cagr_trend_10yr = cagr(sched_school(2015), sched_school(2025), 10)
    school_cagr_trend_20yr = cagr(sched_school(2005), sched_school(2025), 20)
    benefits_cagr_trend_10yr = cagr(sched_benefits(2015), sched_benefits(2025), 10)
    benefits_cagr_trend_20yr = cagr(sched_benefits(2005), sched_benefits(2025), 20)

    # Scope-mismatch finding (see module docstring) - printed for visibility,
    # documented in the methodology doc.
    town_fy26_total = sum(town[c][2026] for c in
                           ("departmental_town", "schools", "nondept_benefits",
                            "nondept_debt_service") ) + other_nondept_town[2026]
    sched_fy25_total = float(hist[2025]["exp_total_expenditures"])
    scope_jump = town_fy26_total / sched_fy25_total - 1

    print(f"Departmental: Town-implied CAGR (FY26-31) {dept_cagr_town:.2%} | "
          f"Schedule A trailing CAGR (FY20-25 actual) {dept_cagr_trend:.2%} "
          f"(10yr {dept_cagr_trend_10yr:.2%}, 20yr {dept_cagr_trend_20yr:.2%})")
    print(f"Schools: Town-implied CAGR (FY26-31) {school_cagr_town:.2%} | "
          f"Schedule A trailing CAGR (FY20-25 actual) {school_cagr_trend:.2%} "
          f"(10yr {school_cagr_trend_10yr:.2%}, 20yr {school_cagr_trend_20yr:.2%})")
    print(f"Benefits: Town-implied CAGR (FY26-31) {benefits_cagr_town:.2%} | "
          f"Schedule A trailing CAGR (FY20-25 actual) {benefits_cagr_trend:.2%} "
          f"(10yr {benefits_cagr_trend_10yr:.2%}, 20yr {benefits_cagr_trend_20yr:.2%})")
    print(f"Scope check: Town FY2026 total (${town_fy26_total:,.0f}) is "
          f"{scope_jump:.2%} above Schedule A FY2025 actual total "
          f"(${sched_fy25_total:,.0f}) - why departmental/schools/benefits "
          f"share the Town's FY26-31 base in both scenarios (see methodology doc)")

    # Excluded debt: zero new debt exclusions assumed FY2026-2040 (Phase 1's
    # own revenue-side assumption) - held flat at FY2031, identical in both
    # scenarios, same as always.
    debt_excluded_base = read_town_debt_exclusion()
    for y in EXTEND_YEARS:
        debt_excluded_base[y] = debt_excluded_base[ANCHOR_YEAR]

    # 6.6% CIP policy: the Town's stated debt-financed target is 4.5% of
    # prior-year Net Revenue, but its own real FY2027-2031 figures never
    # actually hit that - checked directly (see module docstring), the 5
    # real ratios run 3.69%-3.94%, averaging 3.85%, a real and persistent
    # ~0.7pp gap from the stated target, not noise. Uses town_assumptions'
    # own revenue path as the denominator (what the Town itself measured
    # its own figures against), consistent with this project's standing
    # "trailing actual beats stated target/aspiration" convention (same
    # logic as the FY27 6.0%-not-6.6% finding). This realized rate, not
    # the stated 4.5%, is what's applied for FY2032-2040 below.
    town_assum_revenue = read_revenue_forecast("town_assumptions")
    town_non_approp_flat = town["non_appropriated"][ANCHOR_YEAR]
    town_net_revenue = {y: town_assum_revenue[y]["total_revenue"] - town_assum_revenue[y]["debt_exclusion_revenue"]
                            - town_assum_revenue[y]["free_cash"] - town_non_approp_flat
                         for y in TOWN_YEARS}
    realized_ratios = [(town["nondept_debt_service"][y] - debt_excluded_base[y]) / town_net_revenue[y - 1]
                        for y in TOWN_YEARS[1:]]
    cip_debt_pct_realized = sum(realized_ratios) / len(realized_ratios)
    print(f"6.6% CIP policy check: stated debt-financed target {CIP_POLICY_PCT_DEBT:.2%} vs. Town's own "
          f"realized FY27-31 average {cip_debt_pct_realized:.2%} (individual years: "
          + ", ".join(f"{r:.2%}" for r in realized_ratios) + ") - using the realized rate for FY2032-2040.")

    # special_appropriations_cip, town_assumptions basis only (LRFP-
    # sourced, kept for that scenario's FY2032-2040 extension - see
    # module docstring's Non-Departmental budget deep-dive for why this
    # field is overwhelmingly CIP-related, not narrowly the 2.1% slice).
    paygo_realized_ratios = [town["special_appropriations_cip"][y] / town_net_revenue[y - 1]
                              for y in TOWN_YEARS[1:]]
    cip_paygo_pct_realized = sum(paygo_realized_ratios) / len(paygo_realized_ratios)
    print(f"special_appropriations_cip check (town_assumptions basis): Town's own realized FY27-31 "
          f"average {cip_paygo_pct_realized:.2%} of prior-yr Net Revenue (individual years: "
          + ", ".join(f"{r:.2%}" for r in paygo_realized_ratios) + ")")

    # trend_corrected's own, better-sourced CIP decomposition (added
    # 2026-09-02) - realized rates computed directly from CIP_FUNDING_
    # TABLE's real 6 years (FY2027-2032), each component against its own
    # prior-year Net Revenue (town_assumptions basis - what the Town's own
    # table was measured against; verified to match this project's own
    # Net Revenue computation exactly).
    cip_table_years = sorted(CIP_FUNDING_TABLE)
    debt_ratios = [CIP_FUNDING_TABLE[y]["debt"] / town_net_revenue[y - 1] for y in cip_table_years]
    revfin_ratios = [CIP_FUNDING_TABLE[y]["revenue_financed"] / town_net_revenue[y - 1] for y in cip_table_years]
    freecash_ratios = [CIP_FUNDING_TABLE[y]["free_cash"] / town_net_revenue[y - 1] for y in cip_table_years]
    cip_debt_pct_tc = sum(debt_ratios) / len(debt_ratios)
    cip_revfin_pct_tc = sum(revfin_ratios) / len(revfin_ratios)
    cip_freecash_pct_tc = sum(freecash_ratios) / len(freecash_ratios)
    print(f"trend_corrected CIP decomposition (FY27-32 Financial Plan table, realized 6yr avg vs. "
          f"stated target): debt {cip_debt_pct_tc:.2%} (target 4.5%), revenue-financed "
          f"{cip_revfin_pct_tc:.2%} (target 2.1%), free-cash-to-CIP {cip_freecash_pct_tc:.2%} "
          f"(target: tops combined total to {CIP_POLICY_PCT_TOTAL_WITH_FREE_CASH:.0%}) - "
          f"combined {cip_debt_pct_tc + cip_revfin_pct_tc + cip_freecash_pct_tc:.2%}")

    rows = []
    for scenario in ("town_assumptions", "trend_corrected"):
        dept = dict(town["departmental_town"])
        school = dict(town["schools"])
        benefits = dict(town["nondept_benefits"])

        # debt_service_regular and special_appropriations_cip: the 6.6% CIP
        # policy, FY2032-2040 (added 2026-09-02 - see module docstring).
        # Net Revenue uses THIS scenario's own revenue forecast, so the two
        # scenarios now genuinely diverge post-2031, not just carry an
        # identical flat line.
        revenue = read_revenue_forecast(scenario)
        non_approp_flat = town["non_appropriated"][ANCHOR_YEAR]
        net_revenue = {y: revenue[y]["total_revenue"] - revenue[y]["debt_exclusion_revenue"]
                          - revenue[y]["free_cash"] - non_approp_flat
                       for y in FORECAST_YEARS}

        debt_excluded = dict(debt_excluded_base)
        debt_regular = {y: town["nondept_debt_service"][y] - debt_excluded[y] for y in TOWN_YEARS}
        other_subcats = {c: dict(town[c]) for c in OTHER_NONDEPT_SUBCATS}
        cip_revfin = {y: None for y in FORECAST_YEARS}
        cip_freecash = {y: None for y in FORECAST_YEARS}
        cip_overlay = {y: None for y in FORECAST_YEARS}

        if scenario == "trend_corrected":
            # This scenario's own, better-sourced CIP decomposition (added
            # 2026-09-02) - real FY2027-2032 data from CIP_FUNDING_TABLE
            # (the FY2027 Financial Plan's own table), each component
            # extended at its own realized rate for FY2033-2040. FY2026
            # has no real table data - falls back to the LRFP lump (same
            # as town_assumptions for that one year only).
            for y in cip_table_years:  # 2027-2032
                debt_regular[y] = CIP_FUNDING_TABLE[y]["debt"]
                cip_revfin[y] = CIP_FUNDING_TABLE[y]["revenue_financed"]
                cip_freecash[y] = CIP_FUNDING_TABLE[y]["free_cash"]
                cip_overlay[y] = CIP_FUNDING_TABLE[y]["overlay"]
                other_subcats["special_appropriations_cip"][y] = cip_revfin[y] + cip_freecash[y] + cip_overlay[y]
            for y in range(2033, 2041):
                debt_regular[y] = cip_debt_pct_tc * net_revenue[y - 1]
                cip_revfin[y] = cip_revfin_pct_tc * net_revenue[y - 1]
                cip_freecash[y] = cip_freecash_pct_tc * net_revenue[y - 1]
                cip_overlay[y] = 0  # one-time/non-recurring by nature - not extended
                other_subcats["special_appropriations_cip"][y] = cip_revfin[y] + cip_freecash[y] + cip_overlay[y]
            for y in EXTEND_YEARS:
                other_subcats["nondept_general"][y] = town["nondept_general"][ANCHOR_YEAR]
                other_subcats["nondept_reserve_fund"][y] = town["nondept_reserve_fund"][ANCHOR_YEAR]
                other_subcats["non_appropriated"][y] = non_approp_flat
        else:
            for y in EXTEND_YEARS:
                debt_regular[y] = cip_debt_pct_realized * net_revenue[y - 1]
                other_subcats["special_appropriations_cip"][y] = cip_paygo_pct_realized * net_revenue[y - 1]
                other_subcats["nondept_general"][y] = town["nondept_general"][ANCHOR_YEAR]
                other_subcats["nondept_reserve_fund"][y] = town["nondept_reserve_fund"][ANCHOR_YEAR]
                other_subcats["non_appropriated"][y] = non_approp_flat

        debt = {y: debt_excluded[y] + debt_regular[y] for y in FORECAST_YEARS}
        other = {y: sum(other_subcats[c][y] for c in OTHER_NONDEPT_SUBCATS) for y in FORECAST_YEARS}
        paygo_cip = {y: other_subcats["special_appropriations_cip"][y] for y in FORECAST_YEARS}

        if scenario == "town_assumptions":
            for y in EXTEND_YEARS:
                dept[y] = dept[y - 1] * (1 + dept_cagr_town)
                school[y] = school[y - 1] * (1 + school_cagr_town)
                benefits[y] = benefits[y - 1] * (1 + benefits_cagr_town)
        else:
            # dept/schools/benefits: category-level builds
            # (departmental_category_forecast.py / schools_category_forecast.py
            # / benefits_category_forecast.py), for the FULL FY2026-2040
            # window. See each script's own methodology doc for the full
            # reasoning; departmental's FY2026-2031 is a pure decomposition
            # of the Town's own known aggregate (matches it exactly), only
            # schools/benefits independently diverge from the Town's
            # near-term figures too (per the "don't treat the Town's own
            # near-term figures as ground truth for trend_corrected"
            # principle Phase 1's revenue forecast already established,
            # 2026-08-28).
            for y in FORECAST_YEARS:
                dept[y] = departmental_category[y]
                school[y] = schools_category[y]
                benefits[y] = benefits_category[y]

        for y in FORECAST_YEARS:
            extended = y in EXTEND_YEARS
            total = dept[y] + school[y] + benefits[y] + debt[y] + other[y]

            if scenario == "town_assumptions":
                dept_note = f"Town-implied CAGR {dept_cagr_town:.2%}/yr (FY26-31 Town figures)" if extended else TOWN_ASSUM
                school_note = f"Town-implied CAGR {school_cagr_town:.2%}/yr (FY26-31 Town figures)" if extended else TOWN_ASSUM
                benefits_note = (f"Town-implied CAGR {benefits_cagr_town:.2%}/yr (FY26-31 Town figures, "
                                  "combined total - see pension/OPEB handoff note in methodology doc)"
                                  if extended else TOWN_ASSUM)
            else:
                dept_note = ("Category-level build: 5 Schedule A functional categories (General Government, "
                              "Public Safety, Public Works, Human Services, Culture & Recreation), each own-"
                              "trended (trailing-5yr) - see departmental_category_forecast_fy26_40_"
                              "methodology.md. FY2026-2031 is a decomposition of the Town's own known "
                              "aggregate by FY2025 share (ties out exactly); FY2032-2040 is where each "
                              "category's own rate diverges from a single blended rate.")
                school_note = ("Category-level build: sum of 9 DESE function categories, each grown at its "
                                "own 16yr trailing CAGR from the real FY2025 Schedule A anchor - see "
                                "schools_category_forecast_fy26_40_methodology.md (not the Town's FY26-31 "
                                "figure, even for FY2026-2031 - trend_corrected is this project's own "
                                "independent estimate throughout, same principle as Phase 1's revenue forecast)")
                benefits_note = ("Category-level build: Pensions (real 2024 ADC schedule through FY2031, "
                                  "then 3.0%/yr payroll-growth proxy), Group Health (25yr reconstructed "
                                  "trend), OPEB (Town's real FY26-31 schedule incl. the pension/OPEB "
                                  "handoff, held flat FY2032-2040), Other (Town-implied CAGR) - see "
                                  "benefits_category_forecast_fy26_40_methodology.md")

            debt_note = TOWN_ASSUM if not extended else (
                "debt_service_excluded + debt_service_regular (both below)")
            other_note = (TOWN_ASSUM if not extended else
                          "special_appropriations_cip (below, now formula-grown) + nondept_general/"
                          "reserve_fund/non_appropriated held flat at FY2031 (no defensible independent "
                          "trend for those three)")
            debt_excluded_note = ((TOWN_ASSUM + " (bond-by-bond, LRFP p.7-8; dollar-for-dollar match to "
                                    "debt_exclusion_revenue in baseline_revenue_forecast_fy26_40.csv)")
                                   if not extended else
                                   "held flat at FY2031 - no new debt exclusions assumed (matches revenue side)")

            if scenario == "trend_corrected" and y in cip_table_years:
                debt_regular_note = (f"Real FY2027 Financial Plan CIP funding table (p.384) - Net Debt "
                                      f"Financed, FY{y}")
                revfin_note = f"Real FY2027 Financial Plan CIP funding table (p.384) - Revenue Financed, FY{y}"
                freecash_note = f"Real FY2027 Financial Plan CIP funding table (p.384) - Free Cash for CIP, FY{y}"
                overlay_note = f"Real FY2027 Financial Plan CIP funding table (p.384) - Overlay Surplus, FY{y}"
            elif scenario == "trend_corrected" and extended:
                debt_regular_note = (CIP_FORMULA_NOTE.format(pct=cip_debt_pct_tc) +
                                      " (realized FY27-32 average from the real CIP funding table, not the "
                                      "stated 4.5% target)")
                revfin_note = (CIP_FORMULA_NOTE.format(pct=cip_revfin_pct_tc) +
                                " (realized FY27-32 average, target 2.1%)")
                freecash_note = (CIP_FORMULA_NOTE.format(pct=cip_freecash_pct_tc) +
                                  f" (realized FY27-32 average - Free Cash's own CIP allocation; combined with "
                                  f"debt+revenue-financed this tops the total to the Town's real "
                                  f"{CIP_POLICY_PCT_TOTAL_WITH_FREE_CASH:.0%} CIP funding target - see Free "
                                  f"Cash Policy in methodology doc)")
                overlay_note = "held at $0 - Overlay Surplus is explicitly one-time/non-recurring, not extended"
            elif scenario == "trend_corrected":  # FY2026, no real table data yet
                debt_regular_note = TOWN_ASSUM + " minus debt_service_excluded (no real CIP table for FY2026 yet)"
                revfin_note = freecash_note = overlay_note = "not decomposed - no real CIP table data for FY2026"
            else:  # town_assumptions
                debt_regular_note = (TOWN_ASSUM + " minus debt_service_excluded" if not extended else
                                      CIP_FORMULA_NOTE.format(pct=cip_debt_pct_realized) +
                                      f" (Town's own realized FY27-31 average, not the stated "
                                      f"{CIP_POLICY_PCT_DEBT:.1%} policy target - LRFP basis, see methodology doc)")
                revfin_note = freecash_note = overlay_note = "not decomposed in this scenario - see trend_corrected"

            paygo_note = (TOWN_ASSUM if (scenario == "town_assumptions" and not extended) else
                          "revenue_financed + free_cash + overlay (all below)" if scenario == "trend_corrected"
                          else CIP_FORMULA_NOTE.format(pct=cip_paygo_pct_realized) +
                          " (Town's own realized FY27-31 average, LRFP basis - this field is nearly all CIP "
                          "direct appropriations, not a narrow pay-as-you-go slice - see methodology doc's "
                          "Non-Departmental budget deep-dive)")

            def fmt(v):
                return round(v) if v is not None else ""

            rows.append([
                scenario, y,
                round(dept[y]), dept_note,
                round(school[y]), school_note,
                round(benefits[y]), benefits_note,
                round(debt[y]), debt_note,
                round(other[y]), other_note,
                round(total),
                round(debt_excluded[y]), debt_excluded_note,
                round(debt_regular[y]), debt_regular_note,
                round(paygo_cip[y]), paygo_note,
                fmt(cip_revfin[y]), revfin_note,
                fmt(cip_freecash[y]), freecash_note,
                fmt(cip_overlay[y]), overlay_note,
            ])

    with open(OUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scenario", "fiscal_year",
            "departmental_town", "departmental_town_assumption",
            "schools", "schools_assumption",
            "benefits", "benefits_assumption",
            "debt_service", "debt_service_assumption",
            "other_nondept", "other_nondept_assumption",
            "total_expenditure",
            "debt_service_excluded", "debt_service_excluded_assumption",
            "debt_service_regular", "debt_service_regular_assumption",
            "special_appropriations_cip", "special_appropriations_cip_assumption",
            "cip_revenue_financed", "cip_revenue_financed_assumption",
            "cip_free_cash", "cip_free_cash_assumption",
            "cip_overlay_surplus", "cip_overlay_surplus_assumption",
        ])
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUT_FILE}")
    total_cagrs, fy26_totals, fy40_totals = {}, {}, {}
    for scenario in ("town_assumptions", "trend_corrected"):
        r26 = next(r for r in rows if r[0] == scenario and r[1] == 2026)
        r40 = next(r for r in rows if r[0] == scenario and r[1] == 2040)
        total_cagrs[scenario] = cagr(r26[12], r40[12], 14)
        fy26_totals[scenario] = r26[12]
        fy40_totals[scenario] = r40[12]
        print(f"{scenario}: FY26 total ${r26[12]:,.0f} -> FY40 total ${r40[12]:,.0f} "
              f"(implied CAGR {total_cagrs[scenario]:.2%})")

    write_methodology(dept_cagr_town, school_cagr_town, benefits_cagr_town,
                       dept_cagr_trend, school_cagr_trend, benefits_cagr_trend,
                       dept_cagr_trend_10yr, dept_cagr_trend_20yr,
                       school_cagr_trend_10yr, school_cagr_trend_20yr,
                       benefits_cagr_trend_10yr, benefits_cagr_trend_20yr,
                       scope_jump, town_fy26_total, sched_fy25_total,
                       sched_benefits(2025), town["nondept_benefits"][2026],
                       total_cagrs, fy26_totals, fy40_totals,
                       debt_excluded[2026], debt_regular[2026], debt[2026],
                       min(debt_regular[y] for y in TOWN_YEARS),
                       max(debt_regular[y] for y in TOWN_YEARS))
    print(f"Wrote methodology doc to {METHODOLOGY_FILE}")


def write_methodology(dept_cagr_town, school_cagr_town, benefits_cagr_town,
                       dept_cagr_trend, school_cagr_trend, benefits_cagr_trend,
                       dept_cagr_trend_10yr, dept_cagr_trend_20yr,
                       school_cagr_trend_10yr, school_cagr_trend_20yr,
                       benefits_cagr_trend_10yr, benefits_cagr_trend_20yr,
                       scope_jump, town_fy26_total, sched_fy25_total,
                       sched_benefits_2025, town_benefits_2026,
                       total_cagrs, fy26_totals, fy40_totals,
                       debt_excluded_2026, debt_regular_2026, debt_2026,
                       debt_regular_min, debt_regular_max):
    doc = f"""# Baseline Expense Forecast (FY2026-2040) — Assumptions & Methodology

Companion to `baseline_expense_forecast_fy26_40.csv`. Every `*_assumption`
column in that file states exactly what was applied to that cell. This doc
explains where each number comes from.

## Scope

This is Phase 3: a "keep what we have" baseline expense forecast — no
marginal expense impact of new growth (Phase 4, e.g. the per-pupil cost of
new students from new housing) and no service-level policy changes. It
answers "what happens to costs if nothing changes," to be combined with
Phase 1's revenue forecast in Phase 5's synthesis.

## Two scenarios

- **town_assumptions**: the Town's own published FY2026-2031 LRFP figures,
  unmodified, then mechanically extended to FY2040 at the growth rate those
  figures themselves imply, category by category.
- **trend_corrected**: **for departmental_town, schools, and benefits**,
  uses the Town's own FY2026-2031 figures too (see "Why both scenarios
  share the Town's FY26-31 base" below — deliberately different from how
  Phase 1 treated State Aid/Local Receipts), then diverges starting
  FY2032, using a trailing-actual CAGR from 21 years of DLS Schedule A
  history instead of the Town-implied rate. **For debt_service and
  other_nondept**, identical to `town_assumptions` for the entire window —
  no independent trend basis exists for either (see below).

## Why both scenarios share the Town's FY26-31 base for departmental/schools/benefits

Phase 1 built `trend_corrected` State Aid and Local Receipts entirely
independently of the Town's own figures, for the whole FY2026-2040 window
— defensible there because DLS Schedule A actuals and the Town's own
published actuals are the same underlying revenue accounting, no scope
mismatch. That doesn't hold on the expense side. Checked directly: the
Town's own FY2026 total expenditure (${town_fy26_total:,.0f}) is
**{scope_jump:.2%} above** Schedule A's FY2025 actual total
(${sched_fy25_total:,.0f}) — a one-year jump far outside the ~5%/yr the
Town's own FY26-31 figures otherwise imply (4.85% CAGR, per Phase 1's
sanity check) or Schedule A's own 20-year total CAGR (3.92%-5.11%
depending on window). **Since resolved (2026-08-30) on the revenue side**:
most of this isn't a scope mismatch at all, but a real, known, one-time
jump in debt-exclusion revenue — `debt_exclusions` grew from $22.0M
(FY2025 actual) to ${debt_excluded_2026:,.0f} (FY2026), a real +29.9%
increase as Pierce School and Fire Station debt service came online (see
the "Excluded vs. regular debt service carve-out" section below) — which
alone accounts for the large majority of the gap. Building `trend_corrected`
independently from Schedule A for FY2026-2031 the way Phase 1 did for
Schedule A for FY2026-2031 the way Phase 1 did for state aid would
silently import that phantom jump as if it were a real trend-vs-Town
divergence. So departmental/schools/benefits use the Town's own (real,
adopted) FY26-31 figures identically in both scenarios, and only diverge
starting FY2032 — same "anchor on known facts, diverge only in the rate
applied going forward" principle Phase 1 used for property tax's delta
method, just without needing an explicit delta series since there's no
known-committed-dollars component to preserve here.

## Departmental (Town operating departments, ex-schools)

Schedule A categories: general_government + public_safety + public_works +
human_services + culture_recreation.

- **town_assumptions** (FY2032-2040): **{dept_cagr_town:.2%}/yr**, the
  Town's own implied rate, FY2026-2031.
- **trend_corrected**: no longer a single rate — 5 Schedule A functional
  categories, each own-trended (trailing-5yr), see
  departmental_category_forecast_fy26_40_methodology.md. For reference,
  the single blended rate this replaced was **{dept_cagr_trend:.2%}/yr**
  (trailing 5-year actual, FY2020-2025; cross-check 10yr
  {dept_cagr_trend_10yr:.2%}/yr, 20yr {dept_cagr_trend_20yr:.2%}/yr —
  growth had been accelerating in recent years relative to the 20-year
  average across the blend). Unlike Schools/Benefits, this decomposition
  doesn't move the total much — none of the 5 categories' own rates is
  an outlier from the old blended figure, so this mostly sharpens which
  category (Public Safety, at 51% of the total and the fastest-growing
  of the five) is really driving departmental growth, not the top-line
  number.

## Schools

Schedule A category: education.

- **town_assumptions**: unchanged from before — Town's own FY26-31
  figures, then extended at the Town-implied rate ({school_cagr_town:.2%}/yr)
  for FY2032-2040.
- **trend_corrected** (added 2026-09-02, replacing the single blended CAGR
  below): **no longer a single trend rate at all** — it's the sum of
  `schools_category_forecast.py`'s 9 separately-trended DESE function
  categories (Teachers, Pupil Services, Guidance, Administration, etc.,
  each grown at its own 16-year trailing CAGR), for the *full*
  FY2026-2040 window, not just FY2032-2040. See that script's own
  methodology doc for the full reasoning — including why it uses each
  category's real DESE-sourced growth rate instead of Schedule A's single
  blended figure, and why it deliberately doesn't use this project's
  usual trailing-5yr convention for these specific categories (several
  show a 2-4x acceleration between their 5-year and 16-year rates, large
  enough that compounding the elevated recent rate for 15 more years
  would be a real, named forecasting risk rather than a defensible point
  estimate).

  For reference, the single blended Schedule A CAGR this replaced was
  **{school_cagr_trend:.2%}/yr** (trailing 5-year actual, FY2020-2025;
  10yr {school_cagr_trend_10yr:.2%}/yr, 20yr {school_cagr_trend_20yr:.2%}/yr)
  — this project's own general trailing-5yr convention would have picked
  the *lower* 5-year rate here specifically because school cost growth
  looked (on this single blended measure) to have decelerated somewhat
  from its post-2015 pace. The category-level build below shows that
  aggregate deceleration was masking real, ongoing acceleration in
  several specific categories (Pupil Services, Guidance, Administration)
  offset by slower growth in the largest category (Teachers) — exactly
  the kind of thing a single blended CAGR can't see.

## Benefits (pensions, group health, OPEB, and related)

Schedule A category: fixed_costs (confirmed to be the same underlying
category as the Town's own `nondept_benefits` line — FY2025 Schedule A
fixed_costs, ${sched_benefits_2025:,.0f} vs. FY2026 Town nondept_benefits,
${town_benefits_2026:,.0f}, comparable magnitude one year apart per
Phase 0's reconciliation).

**The pension/OPEB handoff.** Brookline's pension system reaches full
funding in FY2030. Once fully funded, required Town pension contributions
fall sharply — and by GASB/actuarial practice that freed funding capacity
gets redirected into the Town's other unfunded liability, retiree health
insurance (OPEB) — so OPEB jumps in the same year pensions crash:

| | FY2029 | FY2030 | FY2031 |
|---|---|---|---|
| Pensions | \\$47.8M | \\$44.1M | **\\$7.3M** |
| OPEB (retiree health) | \\$5.7M | \\$5.9M | **\\$43.0M** |
| **Combined benefits total** | \\$121.4M | \\$122.3M | \\$127.8M |

Naively trending pensions or OPEB *separately* past FY2031 with a single
same-shaped rate would produce nonsense — pensions crashing toward
zero/negative, OPEB exploding at an implausible rate — since neither
sub-line's pre-2031 rate reflects a real ongoing trend, just a one-time
structural reallocation between two liabilities. That's why
`town_assumptions` still trends the **combined `nondept_benefits` total
only** here (a defensible workaround for a scenario built on Town-implied
rates, which has no independent basis to model pensions/OPEB separately
anyway).

**`trend_corrected` (added 2026-09-02) does model them separately** —
`benefits_category_forecast.py` decomposes into Pensions, Group Health,
OPEB, and Other, using the real, already-known Town schedule for
FY2026-2031 (so the handoff shown in the table above is a known fact,
not a trended guess) and each category's *own* real historical data and
structural logic for FY2032-2040 (Pensions: FY2031's Normal-Cost-only
base at a 3.0%/yr payroll-growth proxy, since the pre-2031 rate reflects
paying down a liability that's gone by FY2031; OPEB: held flat at the
post-redirect FY2031 level, no documented schedule exists past the
handoff; Group Health: its own real ~6.5%/yr trend, independent of the
pension story entirely). See `benefits_category_forecast_fy26_40_
methodology.md` for the full reasoning, sourcing, and a direct
before/after comparison — the decomposed FY2040 total lands about 15.8%
below what the old combined-CAGR approach would have produced, almost
entirely because that approach was implicitly compounding the one-time
OPEB redirect at the same rate as everything else, which it has no
documented reason to do.

**Pension correction, fixed 2026-08-30**: the pension figures in
`town_own_forecast_fy26_31.csv` are transcribed from the FY2027 Financial
Plan, which states it's still built on the January 1, 2022 actuarial
valuation — not the newer January 1, 2024 valuation
(`data/Brookline-Retirement-System-2024-Actuarial-Valuation.pdf`, Segal,
via mass.gov/PERAC), whose real funding schedule differs: +5.1% for
FY26-29, -12.1% for FY30, +26.0% for FY31. Per Ben's direction, this
project's own forecast is updated with the corrected figures while
`town_own_forecast_fy26_31.csv` itself stays an untouched transcription
of what the Town actually published (its own surplus/deficit rows are
also built on the stale figure, and correctly re-deriving those needs the
Town/School TSP split formula, not confirmed precisely enough to safely
edit that file). So: **`town_assumptions` keeps the Town's own published
pension figure** for FY2026-2031, unmodified — consistent with that
scenario's premise. **`trend_corrected` uses the real 2024 valuation's
schedule** for FY2026-2031 instead — only the pension sub-line changes,
group health/OPEB/etc. stay as published. FY2032-2040 is otherwise
unchanged for both scenarios; `trend_corrected` compounds off the
*corrected* FY2031 base, so the fix carries forward automatically. See
`.claude/memorialized.md`, 2026-08-30 entries, for the full comparison
table.

- **town_assumptions** (FY2032-2040): **{benefits_cagr_town:.2%}/yr**,
  Town-implied combined-total rate, FY2026-2031 (this rate is well-behaved
  despite the underlying pension/OPEB handoff, precisely because it's
  computed on the combined total, not either sub-line).
- **trend_corrected**: no longer a single rate — see the category-level
  build described above. For reference, the single blended Schedule A
  rate this replaced was **{benefits_cagr_trend:.2%}/yr** (trailing
  5-year actual, FY2020-2025; cross-check 10yr {benefits_cagr_trend_10yr:.2%}/yr,
  20yr {benefits_cagr_trend_20yr:.2%}/yr — this had been the most
  consistently stable trend of the three categories across all three
  windows, and matched the README's already-cited "Fixed Costs... CAGR
  5.5% FY05-25" figure from Phase 0). That stability was real but masked
  the pension/OPEB composition shift entirely — see the category-level
  methodology doc for what it was hiding.

## debt_service — held flat post-FY2031, identical in both scenarios

Two independent reasons, not just one:

1. **Too lumpy to trend.** Schedule A's own debt_service history shows
   CAGR is wildly window-dependent — 15.08% over FY2020-25, 14.46% over
   FY2015-25, but only 5.17% over FY2005-25 — because it moves in step
   changes when individual bonds are authorized, not smoothly like an
   operating budget line. No single window is more "correct" than another;
   that instability itself is evidence there's no clean trend to extract.
2. **Model consistency with the revenue side.** Phase 1's revenue forecast
   explicitly assumes **zero new debt exclusions** authorized FY2026-2040
   (a "keep what we have" baseline can't assume a future townwide ballot
   vote). Debt service is the expense-side mirror of that same assumption
   — if no new debt-financed projects are assumed, debt service shouldn't
   get an independent growth trend either, or the model would be
   internally inconsistent (expenses implicitly assuming new bonds that
   revenue explicitly doesn't).

Bond-by-bond amortization detail (to model the *decline* as existing
bonds pay off, rather than holding flat) isn't available at the individual
bond-maturity level — flat-at-FY2031 is the honest placeholder — Town's
own FY2026-2031 figures (a real, committed bond schedule), then held at
the FY2031 level for FY2032-2040, identical in both scenarios (same
treatment Phase 1 gave Free Cash/Other Available Funds).

### Excluded vs. regular debt service carve-out

Added 2026-08-30 (Ben: "let's carve out the debt exclusions in detail so
we can focus on operating revenue and expenses"). `debt_service` above is
actually two different things mixed together, and now split into two new
columns:

- **`debt_service_excluded`** — the portion funded dollar-for-dollar by
  dedicated debt-exclusion property tax revenue (see
  `baseline_revenue_forecast_fy26_40.csv`'s `debt_exclusion_revenue`
  column — same figure, same source, by MA Prop 2.5 statute these must
  match exactly). Sourced bond-by-bond from the Town's own FY27-31 LRFP
  (`data/FY27-FY31-Long-Range-Financial-Plan.pdf`, "DEBT EXCLUSION" table):
  Florida Ruffin Ridley School, High School, Driscoll School, Newbury
  College, Fire Station renovations, Pierce School Construction.
- **`debt_service_regular`** = `debt_service` − `debt_service_excluded` —
  "tax-supported CIP" debt, funded from ordinary operating revenue (not
  earmarked), governed by the Town's internal fiscal policy requiring "at
  least 6.6% of the Town's [prior year's] net revenue" be dedicated to the
  Capital Improvement Program, split between this debt-financed component
  and a pay-as-you-go cash component (`special_appropriations_cip`, inside
  `other_nondept` below) — see `data/FY2027-Financial-Plan.pdf`, "Debt
  Service / Tax-Supported CIP" section. FY2026: ${debt_excluded_2026:,.0f}
  excluded / ${debt_regular_2026:,.0f} regular (of ${debt_2026:,.0f}
  total) — the regular component is smaller and notably more stable year
  to year (${debt_regular_min:,.0f}-${debt_regular_max:,.0f} across
  FY2026-2031) than the excluded component, consistent with it being a
  steady policy-driven allocation rather than lumpy bond-by-bond step
  changes.

Both sub-lines are held flat post-FY2031 for now, same as the combined
total — the 6.6%-of-net-revenue policy is a real, formulaic trend basis
that isn't yet exploited here (worth doing next: it would let
`debt_service_regular` + the CIP portion of `other_nondept` grow with
total net revenue instead of sitting flat, which is probably the single
best-targeted remaining improvement to this baseline).

## other_nondept (nondept_general + special_appropriations_cip + nondept_reserve_fund + non_appropriated) — held flat post-FY2031, identical in both scenarios

Checked whether Schedule A's `intergov_assessments` + `other_expenditures`
lines could serve as an independent trend basis for this combined
residual category — they can't. Those two Schedule A lines sum to $7.96M
(FY2025 actual), while the Town's own equivalent residual categories sum
to $43.68M (FY2026) — a completely different scope. Schedule A's
standardized statewide categories don't capture the Town's own Capital
Improvement Program appropriations or reserve-fund detail the same way,
so there's no clean actual-history series to trend from. Same treatment
as debt_service: Town's own FY2026-2031 figures, held flat at the FY2031
level for FY2032-2040, identical in both scenarios.

This combines four distinct Town budget lines that are individually more
policy-driven than trend-driven (the Capital Improvement Program
specifically is a discrete, Town-Meeting-approved multi-year plan, not an
organic growth process) — a real simplification, flagged rather than
silently applied, same as debt_service.

## Category tags for Phase 4 (informational only, not modeled here)

Phase 4's marginal-expense-impact-of-new-growth model is where "does this
category grow with new development" actually matters. Tagged here so
Phase 4 doesn't have to re-derive it:

| Category | Tag | Why |
|---|---|---|
| departmental_town | discretionary | staffing/operational choices |
| schools | semi-fixed | largely enrollment/contract-driven, real discretion in program scope |
| benefits | fixed | contractual/actuarial - pension/OPEB/health rates aren't a Town year-to-year choice |
| debt_service | fixed | bond payment obligations, fixed once issued |
| other_nondept | discretionary | CIP and reserve-fund appropriations are policy choices |

## What this deliberately excludes

- **Marginal expense impact of new growth** (e.g. per-pupil cost of new
  students from new housing, additional public-safety/public-works load
  from new development) — Phase 4's job, layered on top of this baseline.
  Includes resolving the disputed per-pupil marginal cost figure
  ($15,572 RKG/ERSC vs. $18,077.77 in the current fiscal impact model vs.
  ~$30K full average cost/student).
- **Service-level policy changes** — this is a "keep what we have"
  baseline, not a recommendation.
- **Revenue side entirely** — this file is expense-only. Combining with
  Phase 1's revenue forecast to size the override gap is Phase 5's job.

## Sanity check

FY2026 total expenditure: town_assumptions ${fy26_totals['town_assumptions']:,.0f},
trend_corrected ${fy26_totals['trend_corrected']:,.0f} (identical, as
expected — both scenarios share the Town's FY2026-2031 base, and only
diverge starting FY2032). By FY2040: town_assumptions
${fy40_totals['town_assumptions']:,.0f}, trend_corrected
${fy40_totals['trend_corrected']:,.0f} — implied FY2026-2040 CAGR is
{total_cagrs['town_assumptions']:.2%} (town_assumptions) vs.
{total_cagrs['trend_corrected']:.2%} (trend_corrected).

For reference, Phase 1's revenue forecast (`baseline_revenue_forecast_fy26_40.csv`)
implies a FY2026-2040 CAGR of 2.95% (town_assumptions) / 3.68%
(trend_corrected) — both expense scenarios here run well above that,
consistent with (not independent validation of, but not contradicting
either) the Town's own LRFP already showing a growing structural deficit.
Combining the two into an actual year-by-year surplus/deficit series, and
sizing the resulting override gap, is Phase 5's job — not attempted here.

## Sources

- `data/FY27-FY31-Long-Range-Financial-Plan.pdf` (Town's own forecast, FY2026-2031 base)
- `data/FY2027-Financial-Plan.pdf` p.79 (Non-Departmental Benefits detail, pension/OPEB/health)
- `output/brookline_historical_financials_fy05_25.csv` (Schedule A trailing actuals, FY2005-2025)
- `data/SOURCES.md` (full external-source catalog)
- `.claude/memorialized.md`, 2026-08-28/29/30 entries
"""
    with open(METHODOLOGY_FILE, "w") as f:
        f.write(doc)


if __name__ == "__main__":
    main()
