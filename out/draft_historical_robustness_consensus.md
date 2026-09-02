# Historical policy robustness check: Consensus rank, model roster rules

## Decision

**Verified: Consensus rank, model roster rules.**

- 400 fresh-seed paired draft rooms per season; 2,800 rooms per policy.
- Championship delta: 8.50%.
- **Season-level 95% CI 1.04% to 15.96%** (7 seasons). This is the interval to quote.
- Room-level 95% CI 7.02% to 9.98% — Monte Carlo precision only. It treats every simulated room-season as independent and is far too narrow to describe the effect.
- Playoff delta: -0.04%. Regular-season points delta: +18.5.
- Positive championship delta in 6/7 seasons.

| Season | Baseline champion | Challenger champion | Champion delta | Playoff delta | Points delta |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | 7.25% | 2.75% | -4.50% | -15.50% | -61.7 |
| 2019 | 14.00% | 23.75% | 9.75% | -2.00% | +42.2 |
| 2020 | 0.00% | 6.50% | 6.50% | 9.00% | +38.6 |
| 2021 | 0.50% | 15.25% | 14.75% | 7.50% | +44.7 |
| 2022 | 3.75% | 17.75% | 14.00% | 7.50% | +62.9 |
| 2023 | 7.25% | 8.25% | 1.00% | -14.25% | -36.2 |
| 2024 | 1.50% | 19.50% | 18.00% | 7.50% | +38.8 |

**Provenance:** this template cannot tell whether the challenger was prespecified or added after the outcomes were seen. If the arm was introduced in the same change as its verification, this is a post-selection result and the interval above is optimistic — record that in the commit message. Fresh seeds reduce Monte Carlo noise; they do not create fresh historical evidence.

Only 7 NFL seasons supply independent outcome variation, and the same 12-team simulator, opponent model, and free replacement-level fill-ins are shared by both arms. A championship-rate gap much larger than the regular-season points gap should be treated as a warning that the metric is dominated by single-week playoff variance, not as evidence of a better roster.
