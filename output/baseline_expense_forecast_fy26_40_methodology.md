# Baseline Expense Forecast (FY2026-2040) — Assumptions & Methodology

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
Town's own FY2026 total expenditure ($419,608,130) is
**15.06% above** Schedule A's FY2025 actual total
($364,676,155) — a one-year jump far outside the ~5%/yr the
Town's own FY26-31 figures otherwise imply (4.85% CAGR, per Phase 1's
sanity check) or Schedule A's own 20-year total CAGR (3.92%-5.11%
depending on window). **Since resolved (2026-08-30) on the revenue side**:
most of this isn't a scope mismatch at all, but a real, known, one-time
jump in debt-exclusion revenue — `debt_exclusions` grew from $22.0M
(FY2025 actual) to $28,596,860 (FY2026), a real +29.9%
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

- **town_assumptions** (FY2032-2040): **2.96%/yr**, the
  Town's own implied rate, FY2026-2031.
- **trend_corrected**: no longer a single rate — 5 Schedule A functional
  categories, each own-trended (trailing-5yr), see
  departmental_category_forecast_fy26_40_methodology.md. For reference,
  the single blended rate this replaced was **3.77%/yr**
  (trailing 5-year actual, FY2020-2025; cross-check 10yr
  2.96%/yr, 20yr 1.78%/yr —
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
  figures, then extended at the Town-implied rate (5.33%/yr)
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
  **3.42%/yr** (trailing 5-year actual, FY2020-2025;
  10yr 4.77%/yr, 20yr 4.52%/yr)
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
fixed_costs, $89,361,296 vs. FY2026 Town nondept_benefits,
$90,794,899, comparable magnitude one year apart per
Phase 0's reconciliation).

**The pension/OPEB handoff.** Brookline's pension system reaches full
funding in FY2030. Once fully funded, required Town pension contributions
fall sharply — and by GASB/actuarial practice that freed funding capacity
gets redirected into the Town's other unfunded liability, retiree health
insurance (OPEB) — so OPEB jumps in the same year pensions crash:

| | FY2029 | FY2030 | FY2031 |
|---|---|---|---|
| Pensions | \$47.8M | \$44.1M | **\$7.3M** |
| OPEB (retiree health) | \$5.7M | \$5.9M | **\$43.0M** |
| **Combined benefits total** | \$121.4M | \$122.3M | \$127.8M |

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

- **town_assumptions** (FY2032-2040): **7.07%/yr**,
  Town-implied combined-total rate, FY2026-2031 (this rate is well-behaved
  despite the underlying pension/OPEB handoff, precisely because it's
  computed on the combined total, not either sub-line).
- **trend_corrected**: no longer a single rate — see the category-level
  build described above. For reference, the single blended Schedule A
  rate this replaced was **6.40%/yr** (trailing
  5-year actual, FY2020-2025; cross-check 10yr 5.79%/yr,
  20yr 5.53%/yr — this had been the most
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
  Service / Tax-Supported CIP" section. FY2026: $28,596,860
  excluded / $14,870,525 regular (of $43,467,385
  total) — the regular component is smaller and notably more stable year
  to year ($13,985,479-$17,594,808 across
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

FY2026 total expenditure: town_assumptions $419,608,130,
trend_corrected $429,919,228 (identical, as
expected — both scenarios share the Town's FY2026-2031 base, and only
diverge starting FY2032). By FY2040: town_assumptions
$799,006,264, trend_corrected
$706,929,697 — implied FY2026-2040 CAGR is
4.71% (town_assumptions) vs.
3.62% (trend_corrected).

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
