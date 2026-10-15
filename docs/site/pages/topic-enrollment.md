---
slug: topic-enrollment
path: forecast/topics/enrollment
title: Enrollment: three forecasts compared
layer: topic
question: Why do the enrollment forecasts disagree, and which one does the base case use?
answer: The base case uses the forecast by the district's own consultant, NESDEC, updated for the births that have since been counted. The School Department plans with a second forecast, by Cropper-McKibben, which expects enrollment to rise again; the difference is almost entirely how many young children each expects Brookline to have, not how classes move through the grades.
summary:
- All three start from about 6,900 students this fall. By FY2034 NESDEC has 6,127, the base case {{fact:enroll_fy2034}} and Cropper-McKibben 7,444.
- NESDEC estimated about 500 births a year from 2023, before those births were counted; the counts came in at 422 in 2023 and 443 in 2024, and the base case updates NESDEC's forecast with them.
- Cropper-McKibben forecasts the whole population first and projects far more births and young families, so its kindergarten classes rise from about 500 to 607 a year.
- On how classes grow or shrink as they move up a grade, the two published forecasts are close to each other and to Brookline's recent record.
- Births have fallen about twice as fast in Brookline and its neighbors as in Massachusetts as a whole; Brookline differs from the family suburbs in how many families move in with young children, not in births.
- Four numbers, updated each fall, show which forecast enrollment is following: births, kindergartners per birth, the October count, and the room that leaves for children from new homes.
- For births not yet counted, the base case assumes {{fact:births_ahead}} a year, the 2022 to 2024 average: it continues the level Brookline has actually had rather than assuming a rebound or a further fall. Births are the main reason the forecasts differ; measured against their own births, all three assume similar rates of families moving in.
related: topic-schools, topic-families, base-case, new-homes, assumptions
updated: 2026-10-14
---

Every enrollment forecast answers two questions: how many children start kindergarten each year,
and what happens to each class as it moves up a grade. This page sets out how the three forecasts
used on this site answer them, where they agree and where they do not. The
[enrollment workbook](/forecast/Brookline_Enrollment_Explained.xlsx) has every number below and a
version you can change.

## The three forecasts

| | NESDEC | Cropper-McKibben | The base case |
|---|---|---|---|
| Who | The New England School Development Council, the district's consultant | Cropper-McKibben, for the School Department | This site |
| When | October 2023 | 2023, revised April 2024 | October 2026 |
| Used by | | The School Department's budget plans | The forecast on this site |
| Method | Cohort survival: births become kindergarten, then each class moves up a grade by Brookline's historical ratios | A population model: forecasts every resident by age, area by area, then converts school-age children into enrollment | NESDEC's forecast, with the births it estimated replaced by the births that were counted |
| Births assumed | About 500 a year from 2023 | About 616 a year for 2025 to 2030 | Actual through 2024 (482, 422, 443), then {{fact:births_ahead}} a year |
| FY2027 (this fall) | 6,774 | 6,917 | 6,889, the actual count |
| FY2030 | 6,464 | 7,050 | {{fact:enroll_fy2030}} |
| FY2034 | 6,127 | 7,444 | {{fact:enroll_fy2034}} |
| FY2040 | | | {{fact:enroll_fy2040}} |

{{chart:enroll-seats}}

## The two assumptions that matter

Every forecast rests on two assumptions: how many children are born to Brookline residents, and how
many families move in or out as those children grow up. The chart shows both. On the left, births:
Brookline's actual count fell from about 690 a year in 2008–13 to 422 in 2023 and 443 in 2024;
NESDEC's 2023 forecast estimated about 500 a year, Cropper-McKibben's population model about 590 to
630, and the base case holds {{fact:births_ahead}}. On the right, students per birth: total enrollment
divided by the births of the 13 years whose children are in K-12, a single measure of families
moving in. Measured against each forecast's own births, all three expect it to rise from about {{fact:birthtab_today_ratio}}
today to around the 0.90 of the 2016–19 peak; the base case reaches {{fact:birthtab_base_ratio}} by FY2040.

{{chart:enroll-assume}}

Because the births behind enrollment are smaller, even a return to the families-moving-in rate of
the 2010s boom would leave enrollment lower than today. Counting 2024's 443 births and assuming
births from 2025 on match the 2022–24 average, about {{fact:births_ahead}} a year, the pool of
Brookline-born children falls about {{fact:birthpool_fall_pct}} by FY2040:

| FY2040 enrollment if enrollment per birth… | Students | Per birth |
|---|---|---|
| stays where it is today | {{fact:birthtab_today_students}} | {{fact:birthtab_today_ratio}} |
| returns to the peak of the 2010s boom | {{fact:birthtab_peak_students}} | 0.90 |
| follows the base case (NESDEC, updated for actual births) | {{fact:birthtab_base_students}} | {{fact:birthtab_base_ratio}} |
| keeps enrollment level with today | 6,889 | {{fact:birthtab_level_ratio}} |

The base case's {{fact:birthtab_base_ratio}} is already a little above the 2010s peak. Keeping
enrollment level would take more families moving in than during the 2010s boom, by a wide margin.

So the forecasts agree more than their totals suggest. They differ mainly in how many children they
expect to be born, and the births of 2022 to 2024 are now counted.

## Is the drop in births unique to Brookline?

No. Between the 2005–09 period and the 2019–23 period, comparing five-year averages, births fell
{{fact:births_drop_state}} across Massachusetts and faster in the towns around Brookline: {{fact:births_drop_inner}} in the
neighboring cities and inner suburbs and {{fact:births_drop_suburbs}} in the family suburbs as a
group. Brookline's {{fact:births_drop_brookline}} was the {{fact:births_drop_rank}} largest fall of
the {{fact:births_drop_towns}} towns with at least 200 births a year, close to Newton
({{fact:births_change_newton}}), Lexington ({{fact:births_change_lexington}}) and Belmont
({{fact:births_change_belmont}}).

{{chart:births-towns}}

Where Brookline differs from the family suburbs is not how many children are born there but how
many families arrive with young children. In Lexington, the fall 2025 kindergarten was
{{fact:kpb_lexington}} times the town's births five years earlier; in Brookline it was
{{fact:kpb_brookline}}. [Why families settle elsewhere](@topic-families) looks at what goes with
that difference. For the forecast, it means a rebound in Brookline's births would most likely be
part of a regional one, and the counts so far, 422 in 2023 and 443 in 2024, show a level rather
than a rise.

## How a kindergarten class is set

Kindergarten is births five years earlier times a kindergarten-per-birth ratio: some children born
here move away or go to private school, and some born elsewhere move in. Brookline's ratio has run
from {{fact:ind_kpb_min}} to {{fact:ind_kpb_max}} since FY2014, leaving out the COVID year, averaging about 0.90 before COVID and 0.85 since. This fall it was
about 0.84: about 411 kindergartners from 491 births in 2021.

NESDEC uses about 0.85, close to the recent record. What has changed since its forecast is births:
it estimated 518 for 2023 and 507 for 2024, before those births were counted, and the counts came in
at 422 and 443. Updating for them makes the FY2029 and FY2030 kindergarten classes 12% to 19% smaller
than NESDEC's, and later ones about 9% smaller, which is what the base case does.

Cropper-McKibben does not use a fixed ratio. Its population model forecasts births and families
moving in together, area by area, and its kindergarten rises from 507 this fall to 607 by FY2034.
Most of that rise comes from births: the model projected about 588 a year for 2020 to 2025 (the
counts averaged 465) and about 616 a year for 2025 to 2030. Measured against its own births, its
kindergarten per birth rises from about 0.86 to about 0.99, within Brookline's historical range. If
births stay near the level counted so far, about {{fact:births_ahead}} a year, reaching 607
kindergartners would take about {{fact:cm_kpb_fy2034}} per birth.

## How a class moves up the grades

Each year a class is multiplied by a grade-to-grade ratio. Above 1, more families arrive than leave
at that age; below 1, more leave. Brookline's actual record, against what each forecast assumes:

| Move | Before COVID | Since FY2022 | NESDEC | Cropper-McKibben |
|---|---|---|---|---|
| K to 1 | 1.00 | 1.03 | 1.03 | 0.99 |
| 1 to 2 | 0.99 | 1.02 | 1.02 | 1.01 |
| 2 to 3 | 1.02 | 1.00 | 1.00 | 1.00 |
| 3 to 4 | 0.98 | 1.01 | 1.01 | 1.02 |
| 4 to 5 | 0.99 | 0.99 | 1.00 | 1.02 |
| 5 to 6 | 0.99 | 0.97 | 0.95 | 0.98 |
| 6 to 7 | 0.98 | 1.00 | 1.00 | 1.02 |
| 7 to 8 | 0.98 | 1.00 | 1.00 | 1.00 |
| 8 to 9 | 0.99 | 1.01 | 1.00 | 0.99 |
| 9 to 10 | 1.02 | 1.02 | 1.01 | 1.03 |
| 10 to 11 | 0.98 | 1.00 | 1.00 | 0.99 |
| 11 to 12 | 1.01 | 1.00 | 1.01 | 1.01 |
| **Kindergarten to grade 12, multiplied** | **0.93** | **1.06** | **1.02** | **1.05** |

Before COVID a class finished grade 12 about 7% smaller than it started; since FY2022 classes have
grown about 6%, partly families returning after COVID. Both published forecasts sit between the two
eras, and close to each other. Running the forecast on Brookline's post-COVID ratios instead of
NESDEC's adds about 80 students by FY2040, against more than 2,000 between the forecasts.

## One class, followed through the grades

The children who started kindergarten this fall were mostly born in 2021, when Brookline residents
had 491 babies:

| School year | Grade | NESDEC | Cropper-McKibben | Actual |
|---|---|---|---|---|
| 2026–27 | K | 415 | 507 | about 411 |
| 2027–28 | 1 | 427 | 505 | |
| 2028–29 | 2 | 437 | 511 | |
| 2029–30 | 3 | 437 | 513 | |
| 2030–31 | 4 | 441 | 523 | |
| 2031–32 | 5 | 441 | 535 | |
| 2032–33 | 6 | 419 | 530 | |
| 2033–34 | 7 | 417 | 544 | |

NESDEC sets the class at 491 × 0.845 = 415 and moves it up by its ratios; the base case follows the
same path, about 1.7% higher to match this fall's total count. Cropper-McKibben starts the same
children 92 higher and keeps the class growing. The actual kindergarten came in at about 411.

## How each has done so far

Both forecasts were made in 2023, so two school years can be checked:

| | Actual | NESDEC | Cropper-McKibben |
|---|---|---|---|
| Total, FY2026 (2025–26) | 6,948 | 6,880 (−1.0%) | 6,929 (−0.3%) |
| Total, FY2027 (2026–27) | 6,889 | 6,774 (−1.7%) | 6,917 (+0.4%) |
| Kindergarten, FY2026 | 453 | 412 | 497 |
| Kindergarten, FY2027 | about 411 | 415 | 507 |

Cropper-McKibben has been closer on total enrollment, because classes already in school have grown a
little faster than NESDEC assumed. NESDEC has been closer on kindergarten, the part that depends on
births. The two forecasts only pull far apart from FY2029, as the smaller birth years reach
kindergarten, so the next few kindergarten counts are the real test.

## Indicators to watch

Births are a leading indicator: they say five years ahead how many children will start
kindergarten, and the October count shows how many families moved in since. Read together each
fall, four numbers show whether enrollment is following the base case or the School Department's
forecast, and how much room the schools have for children from new homes.

{{include:indicators}}

## Why the base case uses NESDEC, updated for actual births

Births are the one input known five years ahead: every child who will start kindergarten through
fall 2030 has already been born. NESDEC's method turns those births into enrollment in a way anyone
can check, and once its estimated births are replaced with the counted ones, its kindergarten
classes match this fall's. UMass Donahue Institute population projections point the same way,
with Brookline's 5–14 age group falling about 28% from 2020 to 2035. Cropper-McKibben's higher enrollment rests on more births than have been
counted so far. If births stay near the counted level, reaching its FY2034 enrollment would take
about {{fact:cm_per_birth_fy2034}} students for every birth, against a twenty-year high of 0.90:
drawing families the way Newton or Belmont do, a change in what kind of town Brookline is rather
than a continuation of its record. [Why families settle elsewhere](@topic-families) compares Brookline with its neighbors.

## What it means for the budget

In the base case, school staff fall half as fast as enrollment, as they did from FY2019 to FY2025
(enrollment fell 10.6% and staff 5.0%). The School Department's own plan holds staff at this year's
level. Because staff move with enrollment, at half speed as it falls and in full as it rises, the
choice between NESDEC and
Cropper-McKibben moves FY2040 by {{fact:fy40_enroll_cm_abs}}. The difference shows up in two
choices:

- **Staffing.** If school staff follow enrollment down fully, FY2040 has
  {{fact:fy40_staff_follow_abs}} more room than the base case; if they are held at this year's
  level, as the School Department plans, it has {{fact:fy40_staff_keep_abs}} less, and the room
  runs out for good in {{fact:runs_out_staff_keep}}. If enrollment instead rebounds as Cropper-McKibben
  forecasts and staff follow it up, FY2040 has {{fact:fy40_enroll_cm_staff_abs}} less. [Will Brookline need another
  override?](@budget-to-2040) sets both against the other decisions.
- **Empty seats.** Enrollment falling faster than staff opens seats that children from new homes
  can fill at little cost. [New homes and Brookline's budget](@new-homes) works through that case, and it disappears if
  Cropper-McKibben is right.

The [Forecast Explorer](@explorer)'s *School enrollment forecast* setting switches the whole forecast
between the base case, flat enrollment and Cropper-McKibben.
