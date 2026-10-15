"""
Town balance sheet: full liability inventory (FY2024 actual, from the
Statement of Net Position) plus a FY2025-2040 forecast for the three
liabilities that dominate it - Long-term Debt, Net Pension Liability, Net
OPEB Liability (together 94.6% of FY2024's $914.4M total liabilities) -
plus a simple treatment of everything else.

Added 2026-09-02 (Ben: "if possible I'd like to also forecast the town's
balance sheet, specific debt, health & pension liabilities, other
liabilities... so we can make sure we understand how those are growing or
shrinking"). This is a genuinely different kind of model from every other
script in this project - a STOCK (balance) forecast, not a FLOW (annual
revenue/expense) forecast, so it stands alone rather than feeding into
baseline_expense_forecast.py's pipeline.

## FY2024 full liability inventory (Statement of Net Position, p.33)

| Category | Current | Noncurrent | Total |
|---|---:|---:|---:|
| Long-term debt (bonds + direct financing) | $27,851,910 | $465,201,345 | $493,053,255 |
| Net OPEB liability | (embedded above) | $201,475,979 | $201,475,979 |
| Net pension liability | (embedded above) | $170,723,706 | $170,723,706 |
| Compensated absences | $7,811,661 | $2,409,909 | $10,221,570 |
| Warrants/accrued payroll/tax refunds/accrued interest/other | $23,884,073 | - | $23,884,073 |
| Unearned revenue | $12,053,392 | $308,400 | $12,361,792 |
| Workers' compensation | $142,800 | $1,897,200 | $2,040,000 |
| Landfill closure | $40,000 | $560,000 | $600,000 |
| **TOTAL LIABILITIES** | **$71,783,836** | **$842,576,539** | **$914,360,375** |

The big three (Debt, OPEB, Pension) get real, individually-reasoned
forecasts below. Everything else ("Other," ~$38.8M) is small, mostly
short-term working-capital items with no obvious long-run growth story -
held flat except Compensated Absences/Workers' Comp, which scale with
headcount and get the same 3.0%/yr payroll-growth proxy already used for
post-2031 pension Normal Cost (benefits_category_forecast.py).

## Long-term Debt: real amortization + the known projected pipeline, nothing further

**Existing debt** (issued as of 6/30/2024, governmental funds - the
General Fund's own share, $452,126,200 par + $1,647,802 direct financing
= $453,774,002): amortizes down using the REAL, contractual principal
schedule from the FY2024 Audited Financial Statements (Note 7, p.71-72) -
no assumption needed, these payments are already fixed. Schedule runs to
FY2049; this forecast uses FY2025-2040.

**Known projected new debt** (from the FY27-31 LRFP's own debt exclusion
table, `data/FY27-FY31-Long-Range-Financial-Plan.pdf` p.9 - the same
source this project's revenue-side `debt_exclusion_revenue` forecast
already uses): 4 specific tranches the Town has already told the public
to expect - Fire Station Renovations 3rd ($18.5M), 4th ($9M), and 5th
($10M) borrowings, and Pierce School's 3rd borrowing ($77M) - inferred
issuance years from when each tranche's debt service first appears in
that table (FY2026 for Fire Station 3rd and Pierce 3rd, FY2027 for Fire
Station 4th, FY2028 for Fire Station 5th). **No real amortization
schedule exists yet for unissued bonds** - approximated as level-principal
over 20 years (roughly matching the term of Brookline's existing bond
portfolio, most of which runs ~20-25 years from issuance) - an explicit,
flagged simplification.

**A real, named gap, not silently omitted**: Pierce School's own total
authorization is $190,916,000 (per the same audited note's "authorized
and unissued debt" table) - far more than the $77M 3rd-borrowing tranche
already reflected in the LRFP's near-term schedule. The remaining
~$113.9M is real, already-authorized, near-certain future Town debt that
isn't in this forecast - consistent with this project's "keep what we
have" convention (don't assume specific NOT-yet-scheduled borrowing), but
worth knowing this forecast is a floor, not a ceiling, for debt.

**FY2032-2040**: no further new borrowing assumed, matching this
project's baseline convention everywhere else (Phase 1's revenue
forecast, Phase 3's debt_service line) - a real simplification, likely to
understate actual future debt given Brookline's own pattern of a new
debt exclusion roughly every 1.5-2 years since 2015 (already documented
in baseline_revenue_forecast_fy26_40_methodology.md).

## Net Pension Liability: the real, exact schedule - no modeling needed

`data/Brookline-Retirement-System-2024-Actuarial-Valuation.pdf`, p.27,
"Funding schedule" table, column (6) - the real, audited unfunded
liability at the beginning of each fiscal year, FY2025-2031, declining to
**exactly $0 by FY2031** (statutory full funding). FY2032-2040 held at
$0 - the same "no actuarial experience modeled" boundary this project
already drew explicitly (Ben, 2026-08-30: forecasting the liability
BALANCE itself, as opposed to the funding schedule, is "a big scope" -
parked). This assumes no future investment losses or benefit
enhancements reopen a new unfunded liability; a real, flagged
simplification, not a prediction that this can never happen again.

**A small, real, unreconciled discontinuity at the FY2024→FY2025
boundary, disclosed rather than smoothed over**: the FY2024 actual
($170,723,706) is a GASB 68 "Net Pension Liability" (from the audit);
the FY2025 figure ($173,231,820) is the actuarial valuation's own
"Unfunded Actuarial Accrued Liability" (funding-schedule basis) - two
legitimate but methodologically different measures (different discount
rates/asset-smoothing conventions are standard between GASB reporting
and funding-schedule actuarial work), producing a real ~$2.5M (1.47%)
apparent "increase" at the boundary that isn't a real one-year change,
just a change of measurement basis. Not merged or hidden - flagged here
so it isn't mistaken for a forecasting error.

## Net OPEB Liability: a real mechanical roll-forward (revised 2026-09-02)

**First version of this script held OPEB flat, and Ben pushed back
directly: "wouldn't the liability grow if we're not paying it down?" -
right, and "flat" was quietly assuming accrual and paydown exactly
offset each other, an assumption that needed to be shown, not asserted.**
This version builds the real mechanism instead, using two tracked stocks
- the gross Total OPEB Liability and the Trust's own Plan Fiduciary Net
Position - both anchored on real FY2024 audited figures
(`data/FY2024-Audited-Financial-Statements.pdf`, p.103, "Schedule of
Changes in the Town's Net OPEB Liability"):

    Total OPEB Liability(y) = Total OPEB Liability(y-1)
        + Service Cost(y) + Interest(y) - Benefit Payments(y)
    Trust Balance(y) = Trust Balance(y-1)
        + Trust Contributions(y) + Investment Return(y)
    Net OPEB Liability(y) = Total OPEB Liability(y) - Trust Balance(y)

- **Service Cost** and **Benefit Payments** grow at the same 3.0%/yr
  payroll-growth proxy used elsewhere in this project (Normal Cost,
  compensated absences), from their real FY2024 actuals ($8,509,485 and
  $12,388,461).
- **Interest** = prior year's Total OPEB Liability × the OPEB discount
  rate. The rate itself is backed out from real data, not assumed:
  FY2024's actual interest ($19,572,147) ÷ FY2023's actual liability
  ($281,241,121) = **6.96%** - within 0.06 points of the actuarially
  disclosed 6.9% rate (audit narrative, "the discount rate is now 6.9%,
  down from 7.0%"), confirming the mechanism is sound.
- **Trust Contributions** = `benefits_category_forecast.py`'s own OPEB
  series (the real FY2026-2031 Town schedule, including the FY2031
  pension→OPEB redirect to ~$43.0M/yr, held flat after) - the same
  number already modeled on the expense side, reused here for
  consistency rather than re-derived.
- **Investment Return** = prior year's Trust Balance × the same 6.96%
  rate (an assumed return equal to the discount rate - standard
  actuarial practice when a plan is assumed to earn its discount rate).
- **What's still not modeled**: actuarial assumption/experience changes
  (the single largest driver of the real historical volatility - e.g.
  FY2023's real $59.8M assumption-driven liability drop) - genuinely
  unpredictable, and modeling them would be the same "big scope" Ben
  already parked for the pension liability balance (2026-08-30). This
  roll-forward is the *expected*, no-surprises trajectory, not a
  confident point forecast - real results will differ, plausibly by
  tens of millions, from actuarial gains or losses this doesn't attempt
  to predict.

**A real, flagged data gap found while building this**: the audit's own
FY2024 Trust Contribution ($0, an anomaly - see below) doesn't match the
Town's own FY2024 budgeted "Retiree Group Health Trust Fund" figure
($4,681,980, from the FY2026 Financial Plan) - a real, unreconciled
timing or definitional gap between when a contribution is budgeted and
when it's actually deposited into the trust, not resolved here. This
model uses the Town's own budgeted figures (the same ones already
trusted throughout `benefits_category_forecast.py`), not the audit's
$0 actual for that one year.

**A real, worth-noting emergent finding, not a bug**: once the FY2031
funding redirect lands, Trust Contributions (~$43.0M/yr) very quickly
exceed the ongoing accrual (Service Cost + Interest, growing modestly
from ~$28M) by a wide margin - the roll-forward has the Net OPEB
Liability reach $0 within a few years of FY2031 and go net-positive
(the trust "overfunded") well before FY2040. **This is very unlikely to
happen in reality** - a Town wouldn't keep depositing $43M/yr into an
already-fully-funded OPEB trust any more than it keeps paying the full
pre-2031 pension ADC after the pension itself is fully funded (which is
exactly why pension contributions drop sharply at that point). The
$43.0M/yr OPEB contribution figure is itself flagged in
`benefits_category_forecast.py`'s own methodology as "no documented
schedule exists past the handoff year" - this emergent overfunding
result is a real signal that figure would likely be revised down once
OPEB itself approaches full funding, not a literal prediction that the
Town will overfund the trust by tens of millions. **This forecast floors
Net OPEB Liability at $0** once the roll-forward would otherwise go
negative, rather than reporting a nonsensical negative liability - a
simplification, flagged, not a hidden clamp.

Outputs:
  ../output/balance_sheet_liabilities_forecast_fy25_40.csv
  ../output/balance_sheet_liabilities_forecast_fy25_40_methodology.md
"""
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_CSV = ROOT / "output/balance_sheet_liabilities_forecast_fy25_40.csv"
METHOD_FILE = ROOT / "output/balance_sheet_liabilities_forecast_fy25_40_methodology.md"

FORECAST_YEARS = list(range(2025, 2041))

# --- FY2024 Statement of Net Position (June 30, 2024), governmental +
# business-type combined unless noted. Source: data/FY2024-Audited-
# Financial-Statements.pdf, p.33 ---
FY2024_SNAPSHOT = dict(
    net_pension_liability=170_723_706,
    net_opeb_liability=201_475_979,
    long_term_debt_total=493_053_255,   # current $27,851,910 + noncurrent $465,201,345
    compensated_absences=10_221_570,     # current $7,811,661 + noncurrent $2,409,909
    workers_compensation=2_040_000,      # current $142,800 + noncurrent $1,897,200
    landfill_closure=600_000,            # current $40,000 + noncurrent $560,000
    unearned_revenue=12_361_792,         # current $12,053,392 + noncurrent $308,400
    other_current=23_884_073,            # TOTAL column: warrants $9,902,144 + accrued payroll $3,236,891 +
                                          # tax refunds $4,520,062 + accrued interest $4,085,016 + other
                                          # liabilities $2,139,960 - verified: all current liabilities sum
                                          # to exactly $71,783,836, the audit's own stated total (a $114,658
                                          # transcription error caught here: an earlier draft used the
                                          # governmental-only column for 3 of these 5 lines instead of Total)
)

# --- Real, exact pension unfunded liability schedule (beginning-of-year),
# FY2025-2031. Source: Brookline-Retirement-System-2024-Actuarial-
# Valuation.pdf, p.27, "Funding schedule" table, column (6). ---
PENSION_UNFUNDED_LIABILITY = {
    2025: 173_231_820, 2026: 153_723_184, 2027: 130_124_564, 2028: 101_929_039,
    2029: 68_576_803, 2030: 29_450_101, 2031: 0,
}

# --- Existing (as of 6/30/2024) governmental bonds payable + direct
# financing: real principal amortization schedule, FY2025-2040 slice.
# Source: FY2024-Audited-Financial-Statements.pdf, p.71 (bonds) + p.72
# (direct financing). ---
EXISTING_DEBT_PRINCIPAL = {
    2025: 21_382_950 + 1_479_047, 2026: 21_172_930 + 168_755, 2027: 21_182_920,
    2028: 21_582_930, 2029: 21_152_980, 2030: 21_148_030, 2031: 21_593_110,
    2032: 21_275_350, 2033: 19_995_000, 2034: 19_770_000, 2035: 19_995_000,
    2036: 20_435_000, 2037: 20_755_000, 2038: 21_240_000, 2039: 21_335_000,
    2040: 21_800_000,
}
EXISTING_DEBT_BALANCE_FY2024 = 452_126_200 + 1_647_802  # par bonds + direct financing, governmental

# --- Known projected new debt (LRFP debt exclusion table, p.9): amount,
# assumed issuance FY (inferred from when its debt service first appears),
# amortized level-principal over an assumed 20-year term (no real schedule
# exists yet - see module docstring). ---
PROJECTED_NEW_DEBT = [
    dict(name="Fire Station 3rd borrowing", amount=18_500_000, issue_year=2026, term=20),
    dict(name="Fire Station 4th borrowing", amount=9_000_000, issue_year=2027, term=20),
    dict(name="Fire Station 5th borrowing", amount=10_000_000, issue_year=2028, term=20),
    dict(name="Pierce School 3rd borrowing", amount=77_000_000, issue_year=2026, term=20),
]
PIERCE_AUTHORIZED_UNISSUED_BEYOND_3RD = 190_916_000 - 77_000_000  # real, flagged, not modeled

PAYROLL_GROWTH_PROXY = 0.030  # same rate used for post-2031 pension Normal Cost

# --- Net OPEB Liability roll-forward. Source: FY2024-Audited-Financial-
# Statements.pdf, p.103, "Schedule of Changes in the Town's Net OPEB
# Liability." Discount rate backed out from real data: FY2024 actual
# interest ($19,572,147) / FY2023 actual Total OPEB Liability
# ($281,241,121) = 6.96%, matching the audit's disclosed ~6.9% rate. ---
OPEB_FY2024_ACTUALS = dict(
    service_cost=8_509_485,
    interest=19_572_147,
    benefit_payments=12_388_461,
    total_opeb_liability=301_751_680,
    plan_fiduciary_net_position=100_275_701,
)
OPEB_DISCOUNT_RATE = 0.0696
OPEB_CAT_CSV = ROOT / "output/benefits_category_forecast_fy26_40.csv"
OPEB_FY2025_CONTRIBUTION = 5_415_980  # real FY2025 actual (benefits_category_forecast.py's ACTUALS dict)


def build_debt_balance():
    balance = {2024: EXISTING_DEBT_BALANCE_FY2024}
    for y in FORECAST_YEARS:
        balance[y] = balance[y - 1] - EXISTING_DEBT_PRINCIPAL.get(y, 0)

    new_debt_balance = {y: 0.0 for y in [2024] + FORECAST_YEARS}
    for tranche in PROJECTED_NEW_DEBT:
        annual_principal = tranche["amount"] / tranche["term"]
        for y in FORECAST_YEARS:
            if y < tranche["issue_year"]:
                continue
            years_paid = y - tranche["issue_year"] + 1
            outstanding = max(0.0, tranche["amount"] - annual_principal * years_paid)
            new_debt_balance[y] += outstanding

    total = {y: balance[y] + new_debt_balance[y] for y in FORECAST_YEARS}
    return balance, new_debt_balance, total


def build_pension_liability():
    out = {}
    for y in FORECAST_YEARS:
        out[y] = PENSION_UNFUNDED_LIABILITY.get(y, 0.0)  # $0 for FY2032-2040
    return out


def read_opeb_contributions():
    contributions = {2025: OPEB_FY2025_CONTRIBUTION}
    with open(OPEB_CAT_CSV) as f:
        for row in csv.DictReader(f):
            contributions[int(row["fiscal_year"])] = float(row["opeb_retiree_trust"])
    return contributions


def build_opeb_liability():
    contributions = read_opeb_contributions()
    total_liability = {2024: OPEB_FY2024_ACTUALS["total_opeb_liability"]}
    trust_balance = {2024: OPEB_FY2024_ACTUALS["plan_fiduciary_net_position"]}
    net = {}
    for y in FORECAST_YEARS:
        n = y - 2024
        service_cost = OPEB_FY2024_ACTUALS["service_cost"] * (1 + PAYROLL_GROWTH_PROXY) ** n
        benefit_payments = OPEB_FY2024_ACTUALS["benefit_payments"] * (1 + PAYROLL_GROWTH_PROXY) ** n
        interest = total_liability[y - 1] * OPEB_DISCOUNT_RATE
        total_liability[y] = total_liability[y - 1] + service_cost + interest - benefit_payments
        investment_return = trust_balance[y - 1] * OPEB_DISCOUNT_RATE
        trust_balance[y] = trust_balance[y - 1] + contributions[y] + investment_return
        net[y] = max(0.0, total_liability[y] - trust_balance[y])
    return net


def build_other_liabilities():
    comp_absences, workers_comp, landfill, unearned, other_current = {}, {}, {}, {}, {}
    comp_absences[2024] = FY2024_SNAPSHOT["compensated_absences"]
    workers_comp[2024] = FY2024_SNAPSHOT["workers_compensation"]
    for y in FORECAST_YEARS:
        comp_absences[y] = comp_absences[y - 1] * (1 + PAYROLL_GROWTH_PROXY)
        workers_comp[y] = workers_comp[y - 1] * (1 + PAYROLL_GROWTH_PROXY)
        landfill[y] = FY2024_SNAPSHOT["landfill_closure"]
        unearned[y] = FY2024_SNAPSHOT["unearned_revenue"]
        other_current[y] = FY2024_SNAPSHOT["other_current"]
    return comp_absences, workers_comp, landfill, unearned, other_current


def main():
    existing_debt, new_debt, total_debt = build_debt_balance()
    pension = build_pension_liability()
    opeb = build_opeb_liability()
    comp_absences, workers_comp, landfill, unearned, other_current = build_other_liabilities()

    rows_out = []
    for y in FORECAST_YEARS:
        row = dict(
            fiscal_year=y,
            long_term_debt_existing=round(existing_debt[y]),
            long_term_debt_new_projected=round(new_debt[y]),
            long_term_debt_total=round(total_debt[y]),
            net_pension_liability=round(pension[y]),
            net_opeb_liability=round(opeb[y]),
            compensated_absences=round(comp_absences[y]),
            workers_compensation=round(workers_comp[y]),
            landfill_closure=round(landfill[y]),
            unearned_revenue=round(unearned[y]),
            other_current_liabilities=round(other_current[y]),
        )
        row["total_liabilities"] = sum(
            row[k] for k in row if k not in ("fiscal_year", "long_term_debt_existing", "long_term_debt_new_projected")
        )
        rows_out.append(row)

    fieldnames = list(rows_out[0].keys())
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)
    print(f"Wrote {OUT_CSV}")

    fy2024_total = sum(FY2024_SNAPSHOT.values())
    print(f"FY2024 actual total liabilities (from audit): ${fy2024_total:,.0f}")
    print(f"FY2025 forecast total: ${rows_out[0]['total_liabilities']:,.0f}")
    print(f"FY2040 forecast total: ${rows_out[-1]['total_liabilities']:,.0f}")
    print(f"  of which: debt ${rows_out[-1]['long_term_debt_total']:,.0f}, pension "
          f"${rows_out[-1]['net_pension_liability']:,.0f}, OPEB (roll-forward, floored at $0) "
          f"${rows_out[-1]['net_opeb_liability']:,.0f}")
    opeb_zero_year = next((r["fiscal_year"] for r in rows_out if r["net_opeb_liability"] == 0), None)
    if opeb_zero_year:
        print(f"  NOTE: OPEB roll-forward reaches $0 (floored) by FY{opeb_zero_year} - see methodology "
              f"doc's 'emergent finding' section.")

    write_methodology(rows_out, fy2024_total)
    print(f"Wrote {METHOD_FILE}")


def write_methodology(rows_out, fy2024_total):
    lines = []
    lines.append("# Town Balance Sheet — Liabilities Forecast (FY2025-2040) — Methodology\n")
    lines.append(
        "Companion to `balance_sheet_liabilities_forecast_fy25_40.csv`. See this script's own module "
        "docstring for the full FY2024 liability inventory (from the Statement of Net Position) and the "
        "reasoning behind each category's forecast. Summary table below; full reasoning is in the docstring "
        "since it's genuinely different per category, not one formula applied five times.\n"
    )
    lines.append("## FY2024 actual (audited) vs. this forecast's endpoints\n")
    lines.append("| Category | FY2024 actual | FY2025 forecast | FY2031 (pension→$0, debt/OPEB milestones) | FY2040 forecast |")
    lines.append("|---|---:|---:|---:|---:|")
    r25, r31, r40 = rows_out[0], next(r for r in rows_out if r["fiscal_year"] == 2031), rows_out[-1]
    lines.append(f"| Long-term Debt | ${493_053_255:,.0f} | ${r25['long_term_debt_total']:,.0f} | "
                  f"${r31['long_term_debt_total']:,.0f} | ${r40['long_term_debt_total']:,.0f} |")
    lines.append(f"| Net Pension Liability | ${170_723_706:,.0f} | ${r25['net_pension_liability']:,.0f} | "
                  f"${r31['net_pension_liability']:,.0f} | ${r40['net_pension_liability']:,.0f} |")
    lines.append(f"| Net OPEB Liability (mechanical roll-forward, floored at $0 - see below) | "
                  f"${201_475_979:,.0f} | ${r25['net_opeb_liability']:,.0f} | "
                  f"${r31['net_opeb_liability']:,.0f} | ${r40['net_opeb_liability']:,.0f} |")
    lines.append(f"| Compensated Absences | ${10_221_570:,.0f} | ${r25['compensated_absences']:,.0f} | "
                  f"${r31['compensated_absences']:,.0f} | ${r40['compensated_absences']:,.0f} |")
    lines.append(f"| Workers' Compensation | ${2_040_000:,.0f} | ${r25['workers_compensation']:,.0f} | "
                  f"${r31['workers_compensation']:,.0f} | ${r40['workers_compensation']:,.0f} |")
    lines.append(f"| Other (unearned revenue, landfill, warrants, etc.) | "
                  f"${12_361_792 + 600_000 + 23_884_073:,.0f} | "
                  f"${r25['unearned_revenue']+r25['landfill_closure']+r25['other_current_liabilities']:,.0f} | "
                  f"${r31['unearned_revenue']+r31['landfill_closure']+r31['other_current_liabilities']:,.0f} | "
                  f"${r40['unearned_revenue']+r40['landfill_closure']+r40['other_current_liabilities']:,.0f} |")
    lines.append(f"| **TOTAL LIABILITIES** | **${fy2024_total:,.0f}** | **${r25['total_liabilities']:,.0f}** | "
                  f"**${r31['total_liabilities']:,.0f}** | **${r40['total_liabilities']:,.0f}** |\n")
    lines.append(
        "**The headline shape**: total liabilities fall sharply through FY2031 (pension liability retiring "
        "to $0, existing debt amortizing down, OPEB liability shrinking as the FY2031 funding redirect kicks "
        "in) even before any of the real uncertainty (new Pierce borrowing beyond the known $77M tranche) is "
        "factored in - the pension payoff alone removes $173.2M. **This should be read as the most "
        "defensible floor for total liabilities, not a confident point forecast** - the debt side is a real "
        "known-floor (new Pierce borrowing beyond $77M is real, authorized, and not included), and the OPEB "
        "roll-forward doesn't model actuarial assumption/experience changes, the largest real driver of its "
        "historical volatility.\n"
    )
    lines.append("## What this deliberately does not do\n")
    lines.append(
        "- **OPEB roll-forward doesn't model actuarial assumption/experience changes** - the largest real "
        "driver of historical volatility (e.g. FY2023's real $59.8M assumption-driven liability drop) - see "
        "module docstring for the full mechanism and its floor-at-$0 treatment once the FY2031 funding "
        "redirect drives the trust past full funding.\n"
        "- **No new Town debt beyond the 4 already-known projected tranches.** Pierce School alone has "
        f"${PIERCE_AUTHORIZED_UNISSUED_BEYOND_3RD:,.0f} of real, already-authorized borrowing capacity "
        "beyond the $77M 3rd tranche this forecast includes - a real, near-certain future addition to Town "
        "debt not modeled here.\n"
        "- **No assumption about future investment returns/losses affecting the pension liability post-"
        "FY2031**, or any future benefit enhancements reopening a new unfunded liability.\n"
        "- **New debt tranches' amortization (20yr level-principal) is an approximation** - no real "
        "amortization schedule exists yet for bonds not yet issued.\n"
        "- **\"Existing debt\" is a combined total, not separated by debt-exclusion vs. regular "
        "(non-excluded) status** - and no future regular/non-excluded borrowing is modeled at all for "
        "FY2032-2040 (only the 4 known debt-exclusion tranches above), consistent with this project's "
        "existing 'not yet exploited: the 6.6%-of-net-revenue CIP policy' open item on the revenue side.\n"
    )
    lines.append("## Sources\n")
    lines.append(
        "- `data/FY2024-Audited-Financial-Statements.pdf` p.33 (Statement of Net Position), p.71-73 "
        "(debt service requirements, changes in long-term liabilities)\n"
        "- `data/Brookline-Retirement-System-2024-Actuarial-Valuation.pdf` p.27 (pension funding schedule)\n"
        "- `data/FY27-FY31-Long-Range-Financial-Plan.pdf` p.9 (projected debt exclusion tranches)\n"
    )
    with open(METHOD_FILE, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
