---
slug: topic-forecast
path: forecast/topics/forecast
title: The forecast: method and results
layer: topic
question: How is the forecast built, and how does it compare with the Town's plan?
answer: The forecast starts from the FY2027 budget Town Meeting adopted and moves each part of it with what drives it, continuing Brookline's FY2011 to FY2025 record. It shows room every year to 2040 where the Town's plan shows a widening gap, and almost all of the difference is the override and school pay.
related: base-case, budget-to-2040, assumptions, explorer
updated: 2026-10-14
---

This is the technical companion to [the base case](@base-case) and [Will Brookline need another
override?](@budget-to-2040): every step between the Town's plan and the base case, the full set
of assumptions, the year-by-year result and how it was checked. Every assumption can be changed
in the [Forecast Explorer](@explorer).

## The Town's own forecast

Start where the Town starts. The FY2027–FY2031 Long-Range Financial Plan,
presented January 13, 2026, is a real, professional, published planning
document, and it is the right first stop for anyone asking where
Brookline's finances are heading. It shows a gap of **$42.7 million by
FY2031**. Adding the May 2026 override, which passed four months after the
plan was presented, and extending the plan's own figures mechanically to
FY2040 produces this:

| | FY2030 | FY2034 | FY2040 |
|---|---|---|---|
| Operating balance | {{fact:stress_bal_fy2030}} | {{fact:stress_bal_fy2034}} | **{{fact:stress_bal_fy2040}}** |
| Share of revenue | {{fact:stress_pct_fy2030}} | {{fact:stress_pct_fy2034}} | **{{fact:stress_pct_fy2040}}** |

A deficit that opens almost immediately and never stops widening, reaching
nearly a quarter of the budget by 2040, even with the override.

That deserves to be shown first, and taken seriously. It is also not the
forecast the rest of this document is built on, and the reason is worth
being careful about.

## Why this document's forecast differs

The Town's plan is not wrong. It is a budget forecast, and a budget
forecast is deliberately conservative, because being wrong in the
optimistic direction is far more costly than being wrong in the other.

This document builds its forecast differently. Instead of trending each
budget line forward, it starts from the FY2027 budget Town Meeting adopted in
May 2026 and moves it with the drivers [How Brookline got here](@spending) identified: how many staff,
what each costs, what prices and health premiums do, and how many homes,
students and square feet the town adds. Each assumption continues what
Brookline actually did from FY2011 to FY2025, unless a published schedule
says otherwise.

Running the Town's plan through the same model shows what its spending
lines assume. For Town departments, pay growth of only about 1.5% a year
with staff flat, below this forecast's 3.0%; on departments, the Town's plan
is the more optimistic of the two. For schools, either pay growing about
6.6% a year with staff flat, or staff rising to about 1,350 positions while
enrollment falls. Neither matches the record.

The school line explains most of the difference, and the reason is
documented rather than inferred. Every school figure in the Town's plan is
the School Department's own forecast, stitched from two versions: FY2027–29
from a December 2025 forecast, and FY2030–31 from a November 2025 forecast
the School Department labelled "preliminary estimates of PSB costs prior to
any analysis for potential efficiencies." Its stated assumptions are
"Staffing levels remain constant, enroll remains flat," with salaries
rising about 5% a year. The budget the School Department adopted in
February grows about 4% a year instead.

## From the Town's plan to the base case, step by step

The Town's plan ends in FY2031, so the walk compares the FY2031 balance, in
dollars a year (a deficit is negative, room positive). Start from the Town's
plan and apply each difference in turn:

| Step | What differs | Change | Running balance |
|---|---|---|---|
| Start | The Town's plan, FY2031 | | **−$42.7M** |
| 1. The override | Passed May 2026, four months after the Town's plan was presented. It phases in over three years ($9.9 million in FY2027, $5.6 million in FY2028, $7.8 million in FY2029), and each piece grows with the levy, so by FY2031 it is worth $27.3 million a year | +$27.3M | −$15.5M |
| 2. New growth | The Town's plan assumes a flat $2.5 million a year; the base case uses the same $2.5 million in FY2027, then continues Brookline's FY2022–26 rate, 1.23% of the levy a year, which grows as the levy does (about {{fact:walk_ng_fy2028}} in FY2028, rising to about {{fact:walk_ng_fy2031}} in FY2031), and adds Chestnut Hill from FY2032 | {{fact:walk_ng}} | {{fact:walk_run2}} |
| 3. Other revenue | Both budget local receipts well below what is collected. The difference is growth: the Town's plan grows budgeted receipts about 1.5% a year from FY2027; the base case lets collections grow at their FY2019–25 pace with investment income held flat (budgeted receipts about 1.3% a year) and returns each year's surplus as free cash two years later. By the Town's free cash policy, the free cash left after the capital and reserve uses already counted goes to capital and one-time uses, so the base case does not count it as room. Both grow state aid 2.5% a year. In FY2031: receipts {{fact:walk_rev_receipts}}, free cash {{fact:walk_rev_fc}}, state aid {{fact:walk_rev_sa}}, {{fact:walk_rev_fc_policy}} | {{fact:walk_rev}} | {{fact:walk_run3}} |
| 4. Schools | The Town's plan uses the School Department's pre-efficiency forecast, with salaries rising about 5% a year, enrollment flat and staffing held constant. The base case has salaries rising about 3.7% a year, enrollment following NESDEC's projected decline, and school staff falling half as fast as enrollment, as they did from FY2019 to FY2025. The 3.7% is the middle of the School Department's own arithmetic for the current contract | {{fact:walk_schools}} | {{fact:walk_run4}} |
| 5. Town departments | The Town's plan grows Town department spending slowly: matching it would take raises of only about 1.5% a year with staff flat. The base case uses 3.0% (3.5% for Public Safety, plus the fire steps and police positions already agreed), so on this step the base case is the more cautious one | {{fact:walk_town}} | {{fact:walk_run5}} |
| 6. Capital, reserves and other | The Town's plan carries higher capital lines than the six-year capital funding table the Town published later in the FY2027 Financial Plan, which follows the Select Board's policy of capital funding equal to 6.6% of the prior year's net revenue (4.5% for debt, 2.1% paid in cash). The table has less capital paid in cash and about $1 million more debt service. The base case uses the table's debt, and tops capital paid in cash up to 6.6% of its own revenue, which counts the override | {{fact:walk_capital}} | {{fact:walk_run6}} |
| 7. Other and rounding | Small differences, mostly in health insurance | {{fact:walk_other}} | {{fact:walk_end}} |
| End | The base case, FY2031 | | **{{fact:walk_end}}** |

**The two biggest differences are the override that passed and school pay.**
Together, steps 1 and 4 are {{fact:walk_override_schools}} of the {{fact:walk_gap}} between the
Town's plan and the base case. Schools are the real difference of view, and
they turn mostly on one number, school pay, and partly on whether staff
adjust as enrollment falls.

**How the override reaches $27.3 million by FY2031.** Voters approved three
steps, $9.85 million in FY2027, $5.60 million in FY2028 and $7.80 million in
FY2029. Each year the added levy is last year's grown by the 2.5% Proposition
2½ allows, plus that year's new step. Three smaller effects ride on top. The
forecast counts new growth as a share of the prior year's levy, because a
higher tax rate means each new building pays more, so new growth rises a
little with the override. The forecast's building permit fees follow new
growth, so they rise a little too. And a larger budget leaves a slightly
larger year-end surplus, which comes back as free cash two years later.

| $ millions | FY2027 | FY2028 | FY2029 | FY2030 | FY2031 |
|---|---|---|---|---|---|
| New override step | 9.85 | 5.60 | 7.80 | | |
| Added levy, growing 2.5% a year | 9.85 | 15.70 | 23.89 | 24.49 | 25.10 |
| New growth on the larger levy | | 0.13 | 0.33 | 0.64 | 0.97 |
| Building permit fees | | 0.15 | 0.25 | 0.38 | 0.39 |
| Free cash, two years later | | | 0.29 | 0.51 | 0.79 |
| **Worth that year** | **9.85** | **15.98** | **24.76** | **26.02** | **27.26** |

The second row can be checked by hand: 9.85 × 1.025 + 5.60 = 15.70, then
15.70 × 1.025 + 7.80 = 23.89, then two more years at 2.5%. Columns may not
add exactly because of rounding.

The Town's plan and the base case answer different questions. The Town's
plan asks what happens if school costs follow the School Department's own
pre-efficiency forecast. The base case asks what happens if costs and revenue
keep behaving as they have.
Which is closer depends mostly on one number: whether school pay keeps rising
about 5% a year or something closer to the record. The teachers' contracts
expired on August 31, 2026 and are being negotiated now. The Town's plan is
kept live below as the **stress case**, because it answers a real question.

The recent record pulls in both directions. Brookline's average teacher
salary rose about 4.7% a year from FY2018 to FY2025, and faster after FY2022
(DESE), which is closer to the School Department's 5% than to the
FY2011–25 record of about 3.4%. The raises the last contract set were smaller: the 2023–2026
teachers' contract raised the salary schedule 2.5% in September 2023, 2.75%
in each of the next two Septembers, and 1% at the end of August 2026.
Teachers who have not reached the top of the schedule also move up one step
for each year of service. A step adds about the same number of dollars at
every level, $3,200 to $3,400, so it is worth about 5% early in a career and
under 3% near the top, 3.6% on average; a teacher moving up a step received
about 6.5% in FY2025 and FY2026 with the raise included, and 4.65% in FY2027.
A teacher at the top step receives the raise alone, plus longevity pay of 1%
to 4% after ten or more years. Over the same years
the number of teachers fell by about a fifth, from 675 in FY2021 to 544 in
FY2025, and a smaller, more senior staff raises the average salary without
anyone's raise being larger. The data here cannot split the rise in the
average among steps, the smaller staff and any one-time payments. So cost per position grows by the raise plus
the steps, less what is saved when a senior teacher retires and is replaced
by a new one lower on the schedule; in a workforce that holds steady, the two
roughly cancel. The School Department's own FY2026 budget build prices the
pieces: the 2.75% raise, steps worth 1.6% of school payroll and degree-column
moves 0.1%, against budgeted turnover savings of 0.4%, about 4.1% a year per
position with staffing held constant. Turnover saved more than budgeted in
FY2025, when professional salaries ended $1.2 million (about 1% of payroll)
under budget from vacancies and rehiring at lower steps, though some of that
is positions left unfilled. At a 2.75% raise, then, cost per position grows
somewhere between about 3.3% and 4.1%. The base case takes the middle of
that range, **3.7%**, rather than the FY2011–25 record of about 3.4%: the
record includes a decade of hiring, when teachers rose from about 524 in
FY2011 to 675 in FY2021 and new hires low on the schedule held the average
down, and the School Department's own arithmetic for the current contract
runs above it. The School Department's
5% sits above the whole range and would need raises of about 3.5% or more in
the next contract. The next contract, and the count of teachers on each
step, which the School Department has and this document does not, will
decide where in the range it lands.

One revenue detail matters enough to name. The Town budgets local receipts
(excise, meals tax, fees, permits) below what it expects to collect; actual
receipts ran $11 to $15 million above budget in FY2022–25. The excess, with
unspent appropriations, becomes the year-end surplus, which the state
certifies as free cash and the Town spends two budgets later. This forecast
budgets receipts the way the Town does, at about 83% of expected
collections once interest income is set at its budgeted level, and returns
each year's excess as free cash two years later, at the 80% share the Town has appropriated recently. The check that this is
counted correctly: FY2026 and FY2027, both adopted balanced budgets, come
out at {{fact:room_fy2026_short}} and {{fact:room_fy2027_short}}. One more step follows the Town's own free
cash policy: what is left after the capital and reserve uses already in the
budget goes to capital and one-time uses, not the operating budget, so the
forecast does not count it as room. The Town has at times used that money for
operating costs; the policy says otherwise, and the base case follows the
policy.

## The base case

| Assumption | Base case | Why |
|---|---|---|
| Starting level | FY2027 adopted budget | Voted by Town Meeting in May 2026, including the override; drivers apply from FY2028 |
| Pay growth, Town staff | 3.0% a year | The Town's bargaining target; national public-sector pay rose 2.8% a year FY2011–25. With the two rows below, all staff average about {{fact:pay_avg}} a year, weighted by FY2027 payroll |
| School pay above target | +0.7 points (3.7%) | The middle of the 3.3–4.1% range the School Department's FY2026 budget build gives at the contract's 2.75% raise; the FY2011–25 record was +0.4 |
| Public Safety pay above target | +0.5 points (3.5%), plus the agreed fire steps and police positions | Police and fire cost per position grew about 3.3% a year in FY2011–25. The faster rise in FY2021–25 came mostly from one-time changes, a police stipend rising from 4% to 7.5% of pay and new steps, already in the FY2027 budget. The fire steps agreed for FY2028 ($909,471) and the four police positions to be refilled in FY2028–29 are added on top |
| School staff | Fall half as fast as enrollment, from about 1,242 in FY2027 to about 1,110 by FY2040 | From FY2019 to FY2025 enrollment fell 10.6% and staff 5.0%, about half as fast. Students from new homes are staffed in full. The School Department's FY2027–29 plan holds staff flat, shown below as a decision |
| Pay's share of spending | Schools 83%; Town departments 76% | Pay grows at each group's rate and the rest with prices. Among Town departments, pay is 87% of Public Safety, about 85% of Human Services, about 80% of General Government, 63% of Public Works and 52% of Culture and Recreation |
| Enrollment | NESDEC projection | 6,833 on October 1, 2026, then NESDEC's path, updated for actual births, to {{fact:enroll_fy2040_about}} by FY2040 |
| Health premiums | 12% a year to FY2029, then 8% | The Town's near-term figure; 8% sits between the 25-year average (6.5%) and recent years (10–12%) |
| Health plan members | Active employees follow staffing; retirees, 36% of the plan's cost, grow 0.92% a year | Retirees are about half of subscribers (1,659 of 3,390 in FY2025) but many are on cheaper Medicare supplement plans. Retiree subscribers grew from 1,459 in FY2011 to 1,659 in FY2025 |
| Prices | 2.5% a year | Boston consumer prices, FY2011–25 |
| Town staff | FY2027 level, plus what growth needs | Town headcount was flat for twenty years |
| Pensions, retiree health, debt | Town schedules to FY2031; then pensions at the yearly cost of new benefits, growing 3.65% a year (the actuary's payroll growth plus an allowance for longer lives), and retiree health at the Town plan's $43.0 million a year until its liability is paid off, after which that money is held for a decision rather than counted as room | Pension full funding in FY2030; the shift to retiree health in FY2031. The retiree health liability is rolled forward from the FY2024 audit |
| State aid | 2.5% a year from the adopted FY2027 figure | The Town plan's rate. State aid grew 3.5% a year over FY2015–25, but that includes a one-year rise of 8.6% in FY2019; since FY2019 it has grown 2.0% a year |
| Free cash, reserves and other non-departmental lines | By Town policy | The reserve fund is 1% of the prior year's net revenue; free cash left after the capital and reserve uses goes to capital and one-time uses |
| New growth | The Town's budgeted $2.5 million in FY2027; then trend, about 1.23% of the levy a year | FY2022–26 average; Chestnut Hill added from FY2032, per the Planning Department's pipeline. Building permits point to about $2.5 million for FY2027 and lower for FY2028 (below) |
| Cost of a new home | $660 a year of Town services, plus students | The [breakeven test](@topic-growth#the-breakeven-test-and-how-to-apply-it-yourself) |

The base case is deliberately not the most favorable one. A version in which
school staff shrink fully with enrollment and pay holds exactly to target would
show larger room still, and neither of those happened in the last fifteen
years. The base case takes the staffing pattern Brookline did show, staff
falling about half as fast as enrollment. Holding staff at the FY2027 level
instead, as the School Department's FY2027–29 plan does, would cost
{{fact:fy40_staff_keep_abs}} a year by FY2040, and the room would run out for good in {{fact:runs_out_staff_keep}}. Both
directions are shown below as decisions.

| | FY2027 | FY2028 | FY2031 | FY2035 | FY2040 |
|---|---|---|---|---|---|
| Revenue | {{fact:revenue_fy2027}} | {{fact:revenue_fy2028}} | {{fact:revenue_fy2031}} | {{fact:revenue_fy2035}} | {{fact:revenue_fy2040}} |
| Spending | {{fact:spending_fy2027}} | {{fact:spending_fy2028}} | {{fact:spending_fy2031}} | {{fact:spending_fy2035}} | {{fact:spending_fy2040}} |
| **Room** | {{fact:room_fy2027_short}} | **{{fact:room_fy2028_short}}** | **{{fact:room_fy2031_short}}** | {{fact:room_fy2035_short}} | **{{fact:room_fy2040_short}}** |

Read left to right: revenue runs about {{fact:room_fy2028}} ahead of spending in
FY2028, {{fact:room_2030s_low}} to {{fact:room_2030s_high}} a year from FY2031 through FY2038, and
{{fact:room_fy2040}} in FY2040, about 2% of revenue. No further override is
needed before 2040 if costs keep behaving as they have.

The near years are the thinnest, and the first risk to them is already
visible. Building permits in 2024 and 2025 were the lowest since at least
2018. The base case holds FY2027's new growth at the Town's budgeted $2.5 million, about what they
point to, but they also point to FY2028 new growth well below the trend. If it comes in there,
FY2028 would have {{fact:fy2028_after_permits}} instead of {{fact:room_fy2028}} of room, and
because each year's levy builds on the last, the shortfall would carry forward: {{fact:pl_effect_fy2040}} a year by FY2040. The state certifies
FY2027's new growth this fall, the first test. [What to watch](@watch) follows it.

The room grows through the mid-2030s, peaks at about {{fact:room_2030s_high}} in FY2036–38, and
then narrows a little, mainly because health insurance keeps compounding at
8% a year, and because enrollment levels off near FY2039, so school staff fall more slowly. From FY2031 to FY2040 revenue and spending both grow about 3.6% a
year; spending's growth speeds up toward the end. Without the override, spending the override funded would have run
about $15 million to $19 million a year ahead of revenue from FY2031 to FY2038;
the override filled that and left room besides.

That room should not be read as a surplus that will accumulate. Brookline
has consistently spent close to what it has, and the override's later steps
were sized to the School Department's own faster forecast. The room is
better read as capacity that the decisions below will use, one way or
another.

## What decides it

{{chart:decide}}

Four decisions each move the FY2040 balance by {{fact:four_decisions_low}} to {{fact:four_decisions_high}} a
year, as much as the whole room or more, and three of them are Brookline's
to make.

**Pay settlements.** One point of pay growth a year for all staff is worth
{{fact:fy40_pay_up1_abs}} a year by FY2040 and {{fact:total_pay_up1_abs}} over the fifteen years. School
wages at the School Department's own forecast rate, about 5% a year
including steps, would cost {{fact:fy40_school_pay_psb_abs}} a year by FY2040. Holding school and
Public Safety pay to the Town's 3% target instead of their recent premiums
would add {{fact:fy40_pay_to_target_abs}}.

**Health insurance.** Premiums settling at 10% a year instead of 8% cost
{{fact:fy40_premiums_high_abs}} a year by FY2040; 6.5% saves {{fact:fy40_premiums_low_abs}}. Health insurance is the
line to watch whatever happens: it nearly triples, from $46 million to
$137 million, and by FY2040 is close to nine-tenths the size of all Town
departments combined. Brookline controls its share of the premium and the plan design,
not the rate.

**School staffing as enrollment changes.** The base case has school staff
falling half as fast as enrollment, as they did from FY2019 to FY2025.
Holding them at the FY2027 level instead costs {{fact:fy40_staff_keep_abs}} a year by FY2040.
If enrollment-linked positions follow enrollment down fully, FY2040 improves by
{{fact:fy40_staff_follow_abs}} more. If enrollment instead rebounds as the School
Department's own demographer projects and staff follow it up, FY2040 is
{{fact:fy40_enroll_cm_staff_abs}} worse. The two forecasts disagree by {{fact:cm_gap_fy2034}} students by
2033–34.

**The pension turn in FY2031.** When the pension system reaches full
funding, about $37 million a year of payments toward past underfunding ends.
The Town's schedule moves that money into prefunding retiree health, whose
unfunded liability was $201.5 million in 2024. The forecast follows the
schedule: $43.0 million a year into the retiree health trust from FY2031, on
top of retirees' premiums, until the liability is paid off, when the payment
stops and the money is free again. Rolled forward from the FY2024 audit on the
actuary's own trend for retiree health costs, the unfunded liability rises to
about {{fact:opeb_net_fy2030}} in FY2030 and is paid off in {{fact:opeb_paid_off}}. If
retirees' costs grew as fast as the base case's 8% premiums, it would not be
paid off before 2040. Not moving the money
would add {{fact:fy40_pension_kept_abs}} a year to the room by FY2040; moving it builds down the Town's
largest remaining long-term liability. What the Town does with the money after the payoff,
{{fact:opeb_freed_fy2040}} a year by FY2040, is a decision for then, so the base case sets it
aside and doesn't count it as room. Counted, the FY2040 room would be
{{fact:room_fy2040_with_freed}}; the Explorer's "Pension savings after full funding" setting
shows both.

When the room runs out for good, turning negative and staying negative through FY2040, depends on
which of these goes the wrong way:

| If | The room runs out for good |
|---|---|
| Costs keep behaving as they have | {{fact:runs_out_base}} |
| Health premiums settle at 10% | {{fact:runs_out_premiums_high}} |
| School staff held at the FY2027 level | {{fact:runs_out_staff_keep}} |
| School wages follow the School Department's forecast | {{fact:runs_out_school_pay_psb}} |
| Pay runs one point higher for all staff | {{fact:runs_out_pay_up1}} |
| Enrollment rebounds and staff follow | {{fact:runs_out_enroll_cm_staff}} |
| Pay one point higher and premiums at 10% | {{fact:runs_out_pay_up1_premiums_high}} |

Growth builds slowly, because each year's addition stacks on the last, and by 2040 it can
move the answer more than any of these, depending on its kind. Reaching the 80th-percentile
peer growth rate through commercial space adds {{fact:fy40_peer_commercial_abs}} a year by FY2040;
through housing alone, {{fact:fy40_peer_housing_abs}} ([the breakeven test](@topic-growth#the-breakeven-test-and-how-to-apply-it-yourself) explains why). Chestnut Hill,
counted on top of trend growth from FY2032, is worth about {{fact:fy40_chca_in_trend_abs}} a year by FY2040.

Less building moves it the other way. If only half the expected new homes are
built, with renovation and commercial growth at their pace, FY2040 has
{{fact:fy40_homes_half_abs}} less room; with none, {{fact:fy40_homes_none_abs}} less. That counts the tax and the Town
costs those homes would bring but leaves the enrollment forecast as it is,
since it already reflects the recent pace of building, so it may overstate
the loss a little. The Explorer's New homes built setting shows both.

## Where the money goes

| Line | FY2027 adopted | FY2031 | FY2040 | Growth a year |
|---|---|---|---|---|
| Schools | {{fact:line_schools_fy2027}} | {{fact:line_schools_fy2031}} | {{fact:line_schools_fy2040}} | {{fact:line_schools_cagr}} |
| Town departments | {{fact:line_town_fy2027}} | {{fact:line_town_fy2031}} | {{fact:line_town_fy2040}} | {{fact:line_town_cagr}} |
| Health insurance | {{fact:line_health_fy2027}} | {{fact:line_health_fy2031}} | {{fact:line_health_fy2040}} | {{fact:line_health_cagr}} |
| Pensions | {{fact:line_pensions_fy2027}} | {{fact:line_pensions_fy2031}} | {{fact:line_pensions_fy2040}} | {{fact:line_pensions_cagr}} |
| Retiree health prefunding (OPEB), then money set aside after the {{fact:opeb_paid_off}} payoff | {{fact:line_opeb_fy2027}} | {{fact:line_opeb_fy2031}} | {{fact:line_opeb_fy2040}} | |
| Other benefits | {{fact:line_otherben_fy2027}} | {{fact:line_otherben_fy2031}} | {{fact:line_otherben_fy2040}} | {{fact:line_otherben_cagr}} |
| Within-levy debt | {{fact:line_debt_fy2027}} | {{fact:line_debt_fy2031}} | {{fact:line_debt_fy2040}} | {{fact:line_debt_cagr}} |
| Capital, reserves and other | {{fact:line_other_fy2027}} | {{fact:line_other_fy2031}} | {{fact:line_other_fy2040}} | {{fact:line_other_cagr}} |
| **Total spending** | **{{fact:line_total_fy2027}}** | **{{fact:line_total_fy2031}}** | **{{fact:line_total_fy2040}}** | **{{fact:line_total_cagr}}** |

The pension and retiree health lines swap places in FY2031, and total
spending barely notices. A two-year delay in reaching full funding barely
moves the room either: the last catch-up payment is spread over the extra
years, and the rest of the money set aside goes to retiree health as
scheduled, so the delay moves money between the two lines and shifts when
the retiree health liability is paid down. The capital,
reserves and other line includes the reserve fund at 1% of the prior year's
net revenue and the free cash set aside for capital by policy. FY2027's
capital, reserves and other line includes a $3.6 million deposit to a new
Override Stabilization Fund, assumed here to be drawn back into the budget
evenly over FY2028–30; the Town documents reviewed do not state the plan.

## How sure these numbers are

- **The method's own error.** Run backward over FY2011–25 with the actual
  staff counts, enrollment and price indices, it predicts Town departments
  3.8% too high and schools 5.7% too low.
- **Enrollment.** The two 2023 forecasts disagree by {{fact:cm_gap_fy2034}} students by
  2033–34. The base uses NESDEC because births to Brookline residents fell
  from about 690 a year (2008–13) to about 490 (2020–22), 422 in 2023, 443 in 2024 and 423 in 2025
  ([Enrollment: three forecasts compared](@topic-enrollment) sets out what that means), and UMass
  Donahue Institute projections have the 5–14 age group falling about 28%
  from 2020 to 2035; the School Department's forecaster has tracked the
  last three years slightly better.
- **The school variable share.** Two-thirds of the school budget is treated
  as moving with enrollment, RKG's judgement with Town staff rather than a
  measured response.
- **One pay rate per group.** Contracts differ by bargaining unit and year,
  and the teachers' contracts are open.
- **Free cash** depends on the Town continuing to budget receipts
  conservatively and appropriating about 80% of each surplus. Following the
  Town's policy, only the part used for capital and reserves counts; the rest
  goes to capital and one-time uses.
- **Capital follows the Town's policy, not a project list.** The Town's policy
  targets 6.6% of the prior year's net revenue for capital (4.5% for debt, 2.1%
  in cash), with free cash topping the total up to at least 8%. The FY2027
  Financial Plan holds it at 6% for FY2026 and FY2027 only, and its six-year
  capital table returns to 6.6% in FY2028. The base case does the same on its
  own revenue, which counts the override passed after the table was written:
  debt follows the table through FY2032 and then grows 3.5% a year, capital paid
  in cash makes up the rest of the 6.6%, and free cash adds about 2.8% more.
  Holding capital at the table's dollars instead, about 6% of this forecast's
  revenue, would leave {{fact:fy40_capital_table_abs}} a year more room by
  FY2040. Large school buildings are not in it:
  Brookline paid for Devotion, the High School, Driscoll and Pierce with debt
  exclusions, which this forecast leaves out of both revenue and spending.
  The next candidate is Baker. A 2019 School Department planning memo put it
  at the end of its lifecycle around 2028, and the FY2027 capital plan lists
  only $6.7 million for Baker's grounds, in its "future years" column, and
  refers to "a Baker reconstruction project" without a date or cost. Paid for
  by a debt exclusion, a Baker project would not change this forecast;
  paid for inside the levy, it would crowd out other spending.
- **A cross-check.** This project's earlier forecast grew each budget line at
  its own historical rate. With the same revenue it comes out about $3 million
  short in both FY2031 and FY2040, because it spends more. Total spending in
  FY2040 is close ($670.2 million against {{fact:spending_fy2040}}); the mix
  differs, with benefits about $9 million higher here and schools about $30
  million lower.

One mechanical note: debt exclusions are left out of both sides throughout,
because voters approved a separate tax that pays that debt service exactly.

## The menu of levers

The forecast above sets the terms these levers are measured against, and they are
not a deficit. On the base case, the override leaves room of about {{fact:room_fy2028}}
to {{fact:room_2030s_high}} a year through 2040, and no further override is
needed within the window. Against that, four decisions are each worth {{fact:four_decisions_low}}
to {{fact:four_decisions_high}} a year by FY2040. So the question is not "how do we
close a gap." It is: **which decisions use the room, which protect it, and
what would keep the next override away once the wedge reopens?**

None of these is presented here as the answer, advice taken from two
sources that don't usually get cited together: the ERSC Final Report's
explicit caution against point estimates (citing the risk to public trust
when a single number turns out wrong), and the Town's own **2030 Roadmap**
(approved by the Select Board May 19, 2026), whose Goal 3, "Increase the
Town's fiscal health and stability", already names several of the levers
below as adopted Town strategy.

**What the Town pays for the services it already provides.** This is the
largest lever, and the one the usual list leaves out. It is not cutting: it
changes what existing services cost, not what the Town provides. Its parts,
each sized above:

- *Pay settlements*, worth about {{fact:fy40_pay_up1_abs}} a year by FY2040 for each point
  of pay growth. Brookline's average teacher salary, $132,000 in FY2025, is
  the highest of the 17 peer districts with data (peer median about
  $112,000), and school cost per staff member ran above the national
  public-sector benchmark over FY2011–25, as Public Safety did in FY2021–25.
  Those are measured facts about pay levels and growth, not a judgement on
  any settlement; pay is also how Brookline recruits and keeps staff.
- *Health insurance*, worth {{fact:fy40_premiums_low_abs}} to {{fact:fy40_premiums_high_abs}} a year by FY2040
  either way, through the Town's premium share and plan design.
- *School staffing as enrollment changes*, worth {{fact:fy40_staff_keep_abs}} a year by FY2040
  between holding staff flat and letting them fall half as fast as
  enrollment, as the base case does, and {{fact:fy40_staff_follow_abs}} more if
  enrollment-linked positions follow enrollment fully. The ERSC's own
  School Model Analysis, a study of consolidating classrooms across school
  buildings, is this lever by another name; it recommended a FY2027 study
  rather than a number. K–8 classes now average 17 to 21 students against
  the district's guidelines of 22 to 25.
- *The pension turn in FY2031*, a choice worth {{fact:fy40_pension_kept_abs}} a year between
  prefunding retiree health, as scheduled, and other uses.

The ERSC's quantified savings belong here too. Its **Solar Initiative** ($3.2
million capital investment, approved 2026-01-22) is projected to avoid about
**$390,000 a year** in electricity costs; an **Electric Demand Management
Strategy** was recommended for further study, not costed. The report also
documents Fire Department overtime running roughly $800,000 a year over
budget, which the Town attributes to leave rules in the FY2018 contract,
injury leave up about 150%, and a 2022 arbitration award. Against the stress case's
{{fact:stress_bal_fy2040}} gap in FY2040 they would be rounding errors. Against the decisions above
they are the right kind of item, and a small one: what moves the answer is
the handful of recurring decisions above, each made in its own cycle.

New growth is the other lever; [Growth: renovation and what faster growth is worth](@topic-growth-value) sizes it.

**Overrides.** The lever every real historical gap has actually been closed
with, four operating overrides since 2005, plus the fifth in May 2026. On
the base case this lever has already been pulled, and far enough: no
further override is needed before FY2040. If pay runs a point high, the
room is gone for good from {{fact:runs_out_pay_up1}}; if school staff are held
flat, from {{fact:runs_out_staff_keep}}; if premiums run high, from
{{fact:runs_out_premiums_high}}. In each case the next override arrives then
rather than after 2040.

The stress case shows what relying on this lever alone looks like. Taking
the Town's own figures extended as-is, and asking what size override, called
every three years (matching the ERSC's own finding that override intervals
have compressed), would restore balance each time: **four new overrides,
FY2029 ({{fact:stress_ov_fy2029}}), FY2032 ({{fact:stress_ov_fy2032}}), FY2035 ({{fact:stress_ov_fy2035}}),
FY2038 ({{fact:stress_ov_fy2038}})**, each larger than the one before, compounding to
**{{fact:stress_ov_total}} a year** of
permanent added levy capacity by FY2040. Roughly three times the entire
FY2005–2025 override total ($38.7 million compounded; see [Revenue, FY2005 to FY2025](@topic-revenue)), raised over
ten years, FY2029 to FY2038, against twenty-one for the earlier total, and even then the budget is not closed:
two years after the last, the gap has reopened to {{fact:stress_gap_fy2040}}. That is
the "compressing intervals, growing amounts" pattern the ERSC flagged, shown
as a quantified consequence rather than an observation.

**Putting them side by side:**

| Lever | Size by FY2040 | Who decides, and when |
|---|---|---|
| **Pay settlements** | {{fact:fy40_pay_up1}} to {{fact:fy40_pay_down_half}} a year | Collective bargaining; the teachers' contracts are open now |
| **Health insurance** | {{fact:fy40_premiums_high}} to {{fact:fy40_premiums_low}} a year | Premium share and plan design, each year |
| **School staffing** | {{fact:fy40_staff_keep}} to {{fact:fy40_staff_follow}} a year | School budget, as enrollment changes |
| **The FY2031 pension turn** | up to {{fact:fy40_pension_kept_abs}} a year | The Town's funding schedule, from the FY2031 budget |
| **New growth** | about {{fact:per_tenth_renovation_m}} a year per tenth of a point through renovation; {{fact:fy40_peer_housing_abs}} to {{fact:fy40_peer_commercial_abs}} at the peer rate | Permitting and zoning, over many years |
| **Overrides** | none needed before FY2040 on the base case | Voters |

Three observations follow. First, **the largest levers are decisions
Brookline already makes every year**, in bargaining, benefit design and the
school budget, and none of them requires closing a program. Second, **they
interact**: the room the override created is one pool, and a decision that
uses it on one line is not available for another. Third, **growth is the
slow lever**: value added early is worth a multiple of the same value added
late, which is the practical case for starting now even though the base
case needs no new revenue before 2040.

### Where these decisions are already on the Town's calendar

Most of these levers already have a place in the Select Board's 2030
Roadmap. The start dates are from the Town's public Goal 3 action tracker,
which is updated quarterly and showed no progress entries as of September
2026.

| Decision | 2030 Roadmap action | Start |
|---|---|---|
| The FY2031 pension turn | 3.D.3: revise the Unfunded Liabilities Policy to set a deadline for fully funding retiree health (OPEB) and a set annual payment above the actuarial contribution | July 2027 |
| How the room is used, all four decisions | 3.D.2 and 3.E.1: a five-year service and funding priority list; a Goal 3 target is to adopt it by FY2027 | July 2027 |
| Pay settlements | 1.B.1: "competitive compensation for certain roles"; 6.B.2: competitive wages to keep vacancies low | Annual and ongoing |
| Town department costs | 3.E.2 to 3.E.5: organisational review and streamlining; 3.E.6: overtime review | 2027 to 2028 |
| New growth | 3.B.1 to 3.B.3: mixed-use development, streamlined permitting, a five-year economic development plan | 2028 to 2030 |
| Business equipment | 3.C.7: identify personal property that should be taxed but is not | July 2028 |
| Health insurance; school staffing | Not in Goal 3 | |

Three things stand out.

**The pension turn is already scheduled for decision.** Action 3.D.3 will
set how much the Town pays toward retiree health above the actuarial
minimum, and by when it reaches full funding. That is the FY2031 choice the forecast
sizes at up to {{fact:fy40_pension_kept_abs}} a year. The Roadmap puts the policy in front of
the Select Board from mid-2027, three budgets before the money arrives,
which is early enough to decide it deliberately.

**On pay, two things are worth holding together.** The Roadmap commits to
competitive compensation, and pay is how the Town recruits and keeps staff;
vacancies have costs of their own, as the Police Department's recent years
of running 14 to 19 officers below authorized strength showed. And each point of pay growth a
year is worth about {{fact:fy40_pay_up1_abs}} a year by FY2040. The Roadmap does not put a
price on its commitment; the forecast does, and the two belong in the same
conversation.

**Two of the four largest decisions are outside Goal 3.** Health insurance
and school staffing do not appear in it. School staffing is the School
Committee's to set, and premium growth is largely set by the market, so
this may be deliberate scope. They are also, with pay, the lines that move
the forecast most. The Town–School Partnership, which action 3.A.1 asks the
Select Board to consider alongside the Expenditures and Revenues Study
Committee, is the natural place for them, and the five-year priority list is
the natural place to weigh all four together.

## What this forecast does not answer

A forecast that lists only its findings is easy to over-trust. This section
lists what is missing, in rough order of how much it could move the
conclusions, so a reader can discount accordingly rather than having to
guess where the soft ground is.

**What the teachers' contracts will settle at.** This is the largest single
number in the forecast, and it is being decided now. The base case assumes
school pay grows 3.7% a year; the School Department's own forecast assumes
about 5%. The difference is about {{fact:fy40_school_pay_psb_abs}} a year by FY2040, more than
the whole room the base case leaves that year. Nothing in this forecast can predict
the outcome; it can only size it.

**Whether Brookline's zoning can actually accommodate faster growth.**
This is open deliberately. The [growth lever](@topic-growth-value) is stated as a *rate*,
valued per tenth of a percentage point, with implied physical equivalents
in homes and square feet. What it does
not establish is whether current zoning permits that, where it would go, or
what would have to change. The scenarios treat the implied unit and
square-foot counts as an output of the arithmetic, not as a claim about
what Brookline would allow.

That gap matters most for the [renovation lever](@topic-growth-value), where it cuts the
optimistic way: an addition or a finished attic is far less constrained by
zoning than a new building is, which is part of why renovation is the
cheapest channel. It matters most against the growth lever generally, where
it cuts the other way: a rate that is arithmetically modest may still be
physically or politically unreachable, and this forecast cannot say which.

**Two physical limits the growth lever would run into.** The Planning
Department's June 2026 look-ahead flags both, and neither is modelled here.
The first is the electric grid: Eversource's summer capacity maps show only
some parts of town as "likely better for 40+ unit buildings," so where large
buildings can go depends partly on where the grid can serve them. The second
is open space: the deck contrasts about 1.5 acres of playground and field
per 1,000 people near the Baker School with about 0.7 near the Ridley School
and Winthrop Square, against a published range of 1.25 to 2.5 for a
community recreation park. Both bear on where added housing could go and
what it would need to come with.

**Roughly $114 million of authorized Pierce School borrowing is not in the
balance sheet.** [The balance sheet projection](@topic-liabilities) shows total liabilities falling from $914
million to about $203 million by FY2040. The Pierce School's full PreK-8
rebuild is approved and its borrowing authorized, but it is not in those
figures. Including it would raise the debt line materially. The $203
million is a defensible floor, not a point estimate, and that page says so, but
it is worth repeating here because the balance sheet is the most
encouraging finding in the forecast and it is the one most exposed to a
single omission.

**Which per-pupil cost basis is right at scale.** [Growth: when a new home pays for itself](@topic-growth) covers this
properly, and it is repeated here only because it propagates: the
difference between {{fact:student_cost}} marginal and $26,683 average per pupil decides
every marginal residential project, and the correct basis shifts from the
first toward the second as growth accumulates. The forecast uses the
marginal figure throughout, which is right for individual projects and
progressively too generous as the volume of growth rises. A scenario that
delivered the full peer-target growth rate would need the average figure
for at least part of it.

**The FY2027 revaluation is not modelled.** Every assessed-value figure
here rests on the FY2025 and FY2026 rolls. Massachusetts requires periodic
full revaluation, and Brookline's next one will move values, including,
potentially, the condominium-versus-rental relationship that carries
much of the [growth analysis](@topic-growth). Nothing suggests it will reverse that relationship, but the
specific breakeven numbers will need re-deriving
afterwards rather than being carried forward.

**Commercial new growth is measured as a floor, not a quantity.** As the
[renovation analysis](@topic-growth-value) notes, the parcel data carries no historical square-footage series for
commercial property, so commercial expansion is structurally much harder to
detect than residential. The 0.01%-a-year figure is what could be
identified, not necessarily what happened. This is the one place in the
forecast where a number could be materially understated for reasons of
measurement rather than substance.

**Timing effects from permitting are named but not sized.** The
[growth analysis](@topic-growth-value) documents real permit-to-assessment lags of 15 to 40 months and declines to
convert them into a scenario, because doing so credibly requires a target
to size against. The forecast now supplies that target, so this is a next step rather
than a permanent gap, but for now, the permitting lever's
value is asserted to be real and not quantified.

**Two mechanical exclusions, stated for completeness.** No future override
or debt exclusion beyond the May 2026 one is modelled anywhere; that is by
design, since those are the levers being sized rather than assumptions to
bake in. And the forecast charges new growth its costs, $660 a year of Town
services per home, less its fire share, plus the schooling of its
students. It models one step cost, a fire company once the town reaches about
{{fact:fire_company_homes}} homes, but not a new classroom or school building,
which also arrive in lumps rather than smoothly.

None of these is a reason to discard the conclusions. The two central
findings, that the override leaves real but modest room through 2040 and
that a few recurring decisions about what existing services cost outweigh
everything else, survive all of them, because they turn on
growth rates and cost trends rather than on any single asset, project, or
valuation. What the list should change is a reader's confidence in the
*precise* numbers, which is lower than the arithmetic's tidiness suggests,
and their confidence in what the answer turns on, which is high: the room is modest
either way, and a few recurring decisions move it more than anything else.
