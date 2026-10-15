---
slug: budget-to-2040
path: forecast/budget-to-2040
title: Will Brookline need another override?
layer: topic
question: When would Brookline need another override, and what would prevent it?
answer: Not in the base case. It would if pay or health costs run higher than the base case assumes, if school staff are held steady as enrollment falls, or if enrollment rebounds and staff follow it; faster growth from commercial space would cover pay running a point high.
summary:
- In the base case, no: revenue covers spending every year to 2040, with school staff falling about half as fast as enrollment, as they have since FY2019.
- Held at the FY2027 level instead, school staff would leave FY2028 a little short and use up the room for good from {{fact:runs_out_staff_keep}}.
- If pay runs one point higher for all staff, the budget falls short in FY2028 and for good from {{fact:runs_out_pay_up1}}. Closing the gap would take an override of about {{fact:bill_override_amount}}, about {{fact:bill_override_sf_extra_fy2040}} a year on the median single-family bill by FY2040.
- Other risks run out sooner or later: health premiums at 10% in {{fact:runs_out_premiums_high}}, enrollment rebounding with staff following in {{fact:runs_out_enroll_cm_staff}}, school pay at the School Department's forecast in {{fact:runs_out_school_pay_psb}}, and pay and premiums both high in {{fact:runs_out_pay_up1_premiums_high}}.
- Counting the money freed once the pension liability is paid off as room, instead of moving it to retiree health, would add {{fact:fy40_pension_kept_abs}} a year to the room by FY2040. Moved to retiree health as the Town plans, it pays that liability off in {{fact:opeb_paid_off}} and is then free again; the base case sets it aside for that decision rather than counting it as room.
- Growth at the pace of the fastest-growing fifth of Massachusetts towns through commercial space would cover pay running a point high; the same pace through new homes alone would not, and the room would run out in {{fact:runs_out_pay_up1_housing}}.
related: topic-growth, topic-forecast, explorer
updated: 2026-10-15
---

The [base case](@base-case) leaves room every year to 2040. This page changes one assumption
at a time and asks when that room would run out, and what would keep it from running out.

The nearest years are the thinnest. FY2028 has {{fact:room_fy2028}} of room. The base case holds
FY2027's new growth at the Town's budgeted $2.5 million, about what building permits in 2024 and
2025 point to, but the permits also point to FY2028 new growth well below the trend. If FY2028's
comes in that low, FY2028 would have {{fact:fy2028_after_permits}}, and each later year less, growing to
{{fact:pl_effect_fy2040}} by FY2040. That alone would not bring an override, but it leaves little margin
for anything else in those years.

## What could use up the room

Each bar moves one assumption away from the base case and shows the effect on revenue minus
spending in a single year, FY2040 and FY2035. Navy bars are decisions Brookline makes; gray bars
are set mostly outside Brookline; purple bars are about growth. The two years show timing.
Keeping the freed pension money matters as much by FY2035 as by FY2040, while the retiree health
payoff frees money only after {{fact:opeb_paid_off}}. Pay, health premiums and growth compound,
so each grows much larger between the two years.

{{chart:decide}}

**The largest lever Brookline sets directly is what the Town pays for the services it already
provides.** None of these
requires closing a program. Each is a decision Brookline makes every year, in bargaining, benefit
design and the school budget:

- **How fast staff pay grows.** One point of pay growth a year for all staff is worth
  {{fact:fy40_pay_up1_abs}} a year by FY2040. School pay at the School Department's own forecast,
  about 5% a year including steps, would cost {{fact:fy40_school_pay_psb_abs}} a year. The
  teachers' contracts expired in August 2026 and are being negotiated now.
- **What the Town does with the money freed once the pension liability is paid off.** When the
  pension system reaches full funding in FY2030, its catch-up payments end. The Town's schedule
  moves that money to paying down the retiree health ([[OPEB]]) liability from FY2031.
  Not moving it, and counting it as room, would add {{fact:fy40_pension_kept_abs}} a year to the room by FY2040.
  Moved, it pays the retiree health liability off in {{fact:opeb_paid_off}} on the actuary's own
  trend for retiree health costs, and the money is free again, {{fact:opeb_freed_fy2040}} a year by
  FY2040. The base case sets that money aside for a decision then and doesn't count it as room; counted, the room in FY2040 would be {{fact:room_fy2040_with_freed}}.
- **School staffing levels.** The base case assumes enrollment falls as [[NESDEC]] projects and
  school staff fall about half as fast, as they did from FY2019 to FY2025. Holding staff at the
  FY2027 level instead would cost {{fact:fy40_staff_keep_abs}} a year by FY2040, and letting
  enrollment-linked positions follow enrollment fully would add {{fact:fy40_staff_follow_abs}}. If
  enrollment instead rebounds as the School Department's forecast projects and staff follow it up,
  FY2040 worsens by {{fact:fy40_enroll_cm_staff_abs}}.
- **What the health plan costs**, which Brookline controls only through its share of the premium
  and its plan design: 6.5% a year instead of 8% from FY2030 improves FY2040 by
  {{fact:fy40_premiums_low_abs}}; 10% worsens it by {{fact:fy40_premiums_high_abs}}.

## When the room runs out

| If | The room runs out for good |
|---|---|
| Costs keep behaving as they have | {{fact:runs_out_base}} |
| School staff held at the FY2027 level | {{fact:runs_out_staff_keep}} |
| Health premiums settle at 10% a year | {{fact:runs_out_premiums_high}} |
| Enrollment rebounds and staff follow | {{fact:runs_out_enroll_cm_staff}} |
| School pay follows the School Department's forecast | {{fact:runs_out_school_pay_psb}} |
| Pay runs one point higher for all staff | {{fact:runs_out_pay_up1}} |
| Pay one point higher and premiums at 10% | {{fact:runs_out_pay_up1_premiums_high}} |
| Pay one point higher, with growth at the peer rate from new homes | {{fact:runs_out_pay_up1_housing}} |
| Pay one point higher, with growth at the peer rate from commercial space | {{fact:runs_out_pay_up1_commercial}} |

Each year shown is when the room goes below zero and stays there through FY2040. With only
{{fact:room_fy2028}} of room in FY2028, most of these settings also leave that year a little short.

The last two rows are where commercial building matters to a household. New commercial property
pays its own tax, so under [[Proposition 2½]] it raises the town's total without raising anyone
else's bill. Its direct effect on a typical bill is a small cut, from spreading the fixed payments
on school building debt over more property. Its real effect is on whether another override is
needed. If pay runs a point high, the budget falls short in FY2028 and for good from
{{fact:runs_out_pay_up1}}, and the override
that closes the gap would add about {{fact:bill_override_sf_extra_fy2040}} a year to the median
single-family bill by FY2040. Growth at the peer rate through commercial space would leave
{{fact:room_fy2040_pay_up1_commercial}} of room in FY2040 instead, with no override; the same
growth through new homes would still run out in {{fact:runs_out_pay_up1_housing}}. Brookline
already taxes commercial property at nearly the highest rate state law allows relative to homes,
so as commercial value grows, a little more of the total also shifts off homes; the forecast does
not count that.

Several of these decisions already have a place in the Select Board's 2030 Roadmap. Action 3.D.3
revises the Town's policy on funding retiree health from July 2027, which is the FY2031 pension
decision. Actions 3.D.2 and 3.E.1 call for a five-year list of service and funding priorities,
the natural place to weigh all four. Health insurance and school staffing are not in the
Roadmap's fiscal goal.

## Growth helps, and its kind matters

Brookline's tax base has grown from new growth at about {{fact:trend_growth_rate}} of the levy a
year over FY2022 to FY2026, slower than most comparable towns. Growth builds slowly, because each
year's addition stacks on the last: at the pace of the fastest-growing fifth of Massachusetts
towns, {{fact:peer_growth_rate}} of the levy a year, it adds about
{{fact:growth_peer_even_gain_fy2030}} a year of room by FY2030 and {{fact:fy40_peer_even_abs}} by
FY2040. What is built matters as much as how much: reaching that pace through commercial space
would add {{fact:fy40_peer_commercial_abs}} a year by FY2040, and through new homes alone,
{{fact:fy40_peer_housing_abs}}. [Growth: when a new home pays for itself](@topic-growth) explains the
difference. Building fewer homes than the recent pace would not help: with half as many, FY2040
would have {{fact:fy40_homes_half_abs}} less room, and with none, {{fact:fy40_homes_none_abs}} less.

The difference is cost. Renovation adds tax without adding homes, and it is most of Brookline's
growth: about 78% of the real-estate part of new growth at the recent pace of building is
investment in existing property, and over the eight years to 2025 renovation, including houses
rebuilt as houses, added more assessed value than all the buildings that added homes. A larger, renovated house can still draw a family with more children, which the forecast
does not count, but the margin is wide: each $1 million spent on residential renovation raises
assessed value by about $1.3 million and adds about $13,400 a year in tax, about four-fifths of what one added student costs. About a quarter more renovation
than Brookline already does would add more by 2040 than all the room the override leaves that
year.

Homes with children cost more, because schooling is the largest cost. Whether any home pays its
way depends on its value, who lives in it, and how many school-age children it has:

{{chart:unit-breakeven}}

With enrollment falling faster than school staff, children from new homes can fill seats the
schools already have, and the answer changes a good deal. [New homes and Brookline's
budget](@new-homes) works through that case.

## How sure this is

The forecast is a continuation of Brookline's own record, not a prediction, and it reproduces
FY2011 to FY2025 closely when run over those years ([how it was checked](@base-case#how-sure-this-is)).
The largest uncertainties are school pay, while the teachers' contracts are open, and enrollment,
where the School Department's own forecast expects a rebound this one does not
([the three enrollment forecasts compared](@topic-enrollment)). The
[Forecast Explorer](@explorer) lets anyone change any of these assumptions and see the result.
