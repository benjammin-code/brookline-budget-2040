# Reserve Trajectory and Rating Thresholds, FY2025-2040 — Methodology

Companion to `reserve_trajectory_fy25_40.csv`. Rolls the last audited reserve balance forward under each forecast and flags where stated thresholds would be crossed.

Start from the last audited available fund balance and roll it forward,
letting reserves absorb each year's operating balance:

    reserves(t) = reserves(t-1) + operating_balance(t)
    ratio(t)    = reserves(t) / operating_revenue(t)

Then flag two thresholds, both of which Brookline has effectively adopted:

- **20% of revenue.** The Town's own formal Reserve Policy (FY2027 Financial
  Plan, Appendix) sets "no less than 20% of revenue," and Moody's February
  2024 credit opinion names a decline below 20% as its downgrade trigger. The
  two numbers coincide.
- **Zero.** The point at which reserves can no longer absorb anything and the
  gap must be met by an override or by cuts in the year it appears.

## What "downgrade" means here, stated carefully

This does NOT predict a downgrade. Rating agencies weigh a scorecard, they
disagree with each other on the same town in the same year (Moody's cut
Braintree in October 2025 while S&P affirmed it in February 2026), and a
single ratio breach is not a mechanical trigger. What the model does is
identify the year a stated threshold would be crossed on each path, which is
the most that can be said honestly.

Brookline's own position also carries more room than the headline suggests:
Moody's most recent published report (May 2025, on FY2023 data) puts its
available fund balance ratio at 27.1%, against the 23.1% in the February 2024
report on FY2022 data. Note that Moody's measure sweeps in operating funds
beyond the General Fund and so runs about six points above this project's
audit-derived figure; the two are tracked separately and never mixed.

## Result

| Path | FY2040 reserves | % of revenue | Falls below 20% | Exhausted |
|---|---|---|---|---|
| as_legislated | $300.2M | 43.1% | never | never |
| structural | $-101.2M | -15.4% | FY2028 | FY2035 |
| downside | $-669.4M | -108.6% | FY2028 | FY2033 |

Read the three together rather than separately. Under the base case as legislated, reserves are never drawn on at all, because the May 2026 override holds the operating budget in surplus for the whole window. That is the realistic path and it is the reason this section is not an alarm. The other two show what reserves are insuring against.

One honest qualification on the first path: a town that ran a surplus of roughly 4% of revenue for fifteen consecutive years would not accumulate it. The twenty-year record is that Brookline spends close to what it has. Treat the as-legislated reserve line as headroom that gets used, not as a balance that builds.

## What one notch would cost

| FY | Projected long-term debt | Annual cost at 20 bp |
|---|---|---|
| 2030 | $411.8M | $823,657 |
| 2035 | $280.6M | $561,150 |
| 2040 | $146.4M | $292,770 |

At the September 2026 spread of roughly **10 basis points at ten years and 20 at twenty to thirty**, one notch costs Brookline in the low hundreds of thousands a year against a declining debt portfolio. For scale, that is a fraction of the structural wedge itself.

The cost of a downgrade is therefore not mainly the interest. It is that the conditions producing a downgrade, sustained deficits and falling reserves, are expensive in their own right, and the rating is a signal of them rather than the harm itself.

## What this deliberately does not claim

- **It does not predict a downgrade.** Agencies weigh a full scorecard and disagree with each other on the same town in the same year. A single ratio crossing a stated threshold is a flag, not a mechanism.
- **It does not model reserve policy behaviour.** Real towns replenish reserves deliberately, and Brookline has: available fund balance went from 12.29% of revenue in FY2019 to 22.91% in FY2024. The roll-forward here is mechanical and makes no allowance for that.
- **It does not use Moody's own measure.** Moody's available fund balance ratio sweeps in operating funds beyond the General Fund and runs about six points higher than the audit-derived figure used here, so this model is the conservative one. Peer comparisons should use Moody's series, not this one.
