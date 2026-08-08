# Draft policy championship optimizer

## Outcome

**No challenger proved a statistically reliable championship-rate improvement over the current tuned build.** Keep the baseline configuration; the apparent leader's paired interval still includes zero.

## Method

- Stage 1: 12 policies × 300 paired draft rooms × 5 season outcomes per room.
- Final: baseline plus the top three policies, each extended by 600 paired draft rooms × 5 outcomes.
- Opponent rooms mix need-aware (60%), ADP-oriented (25%), and Model-oriented (15%) team behavior with controlled randomness.
- Evaluation is separate from draft selection: projection/ADP/ECR ensemble, season uncertainty, weekly volatility, team correlation, injuries, replacement pickups, lineup setting, 14-week standings, and 8-team Weeks 15–17 playoffs.
- The workspace has no historical weekly outcomes or bye-week data. Team byes are assigned consistently for paired comparisons, and this remains a synthetic optimizer rather than historical proof.

## Finalists

| Rank | Policy | Champion | Playoffs | Avg regular-season PF | Championship Δ vs baseline (95% CI) | Legal drafts | QB2/TE2 exception |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Current tuned build | 13.24% | 80.04% | 1710.2 | 0.00% [0.00%, 0.00%] | 900/900 | 28.00% |
| 2 | Delay QB2/TE2 to R10 | 13.24% | 80.04% | 1710.2 | 0.00% [0.00%, 0.00%] | 900/900 | 28.00% |
| 3 | Allow 7/3 RB-WR split | 13.20% | 79.98% | 1710.6 | -0.04% [-0.43%, 0.35%] | 900/900 | 34.89% |

## Stage-one screen

| Policy | Champion | Playoffs | Avg PF |
| --- | ---: | ---: | ---: |
| Current tuned build | 14.67% | 81.27% | 1714.9 |
| Lower ceiling weight | 12.60% | 79.73% | 1715.7 |
| Higher ceiling weight | 13.67% | 79.27% | 1714.3 |
| Only two early RB/WR | 12.93% | 79.67% | 1708.2 |
| Four early RB/WR | 13.47% | 83.00% | 1722.3 |
| Finish starters by R7 | 14.67% | 80.40% | 1713.2 |
| Finish starters by R9 | 13.60% | 80.00% | 1713.2 |
| Take any superior TE2 | 14.20% | 81.40% | 1716.0 |
| Require +10 for TE2 | 14.13% | 81.40% | 1714.4 |
| Delay QB2/TE2 to R10 | 14.67% | 81.27% | 1714.9 |
| No QB2/TE2 | 13.73% | 81.60% | 1714.4 |
| Allow 7/3 RB-WR split | 14.87% | 81.47% | 1715.2 |

## Decision

Retain the current strategy configuration: `{"id":"baseline","label":"Current tuned build","lambda":0.4,"coreEarly":3,"coreDeadline":4,"starterDeadline":8,"coreTotal":10,"minCoreEach":4,"luxuryStart":9,"te2Edge":5,"qb2Edge":5}`. More synthetic trials would narrow Monte Carlo error, but historical weekly backtesting is the more valuable next source of evidence.
