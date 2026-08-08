# Draft policy championship optimizer

## Outcome

**Synthetic candidate: Four early RB/WR.** Its paired interval excludes zero in this model, so it advances to historical robustness testing; it is not automatically a live change.

## Method

- Stage 1: 12 policies × 300 paired draft rooms × 5 season outcomes per room.
- Final: baseline plus the top three policies, each extended by 600 paired draft rooms × 5 outcomes.
- Opponents use the historically calibrated ADP + roster-need selector and ADP-dispersion-scaled randomness from the live assistant.
- Evaluation is separate from draft selection: projection/ADP/ECR ensemble, season uncertainty, weekly volatility, team correlation, injuries, replacement pickups, lineup setting, 14-week standings, and 8-team Weeks 15–17 playoffs.
- This synthetic optimizer is subordinate to the historical weekly backtest in `out/draft_historical_backtest.md`.

## Finalists

| Rank | Policy | Champion | Playoffs | Avg regular-season PF | Championship Δ vs baseline (95% CI) | Legal drafts | QB2/TE2 exception |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Four early RB/WR | 17.38% | 83.49% | 1736.7 | 2.73% [1.35%, 4.12%] | 900/900 | 38.56% |
| 2 | Only two early RB/WR | 15.36% | 84.13% | 1735.9 | 0.71% [-0.17%, 1.59%] | 900/900 | 35.00% |
| 3 | Finish starters by R7 | 15.00% | 83.71% | 1737.2 | 0.36% [-0.23%, 0.94%] | 900/900 | 34.56% |
| 4 | Current tuned build | 14.64% | 83.69% | 1735.4 | 0.00% [0.00%, 0.00%] | 900/900 | 35.44% |

## Stage-one screen

| Policy | Champion | Playoffs | Avg PF |
| --- | ---: | ---: | ---: |
| Current tuned build | 14.27% | 83.73% | 1739.6 |
| Lower ceiling weight | 14.33% | 83.87% | 1739.3 |
| Higher ceiling weight | 14.53% | 84.07% | 1739.6 |
| Only two early RB/WR | 15.07% | 84.60% | 1739.4 |
| Four early RB/WR | 18.27% | 82.67% | 1739.0 |
| Finish starters by R7 | 15.13% | 84.40% | 1741.3 |
| Finish starters by R9 | 14.47% | 83.53% | 1739.1 |
| Take any superior TE2 | 14.27% | 83.73% | 1739.6 |
| Require +10 for TE2 | 14.47% | 83.53% | 1739.4 |
| Delay QB2/TE2 to R10 | 14.27% | 83.73% | 1739.6 |
| No QB2/TE2 | 15.07% | 83.73% | 1737.9 |
| Allow 7/3 RB-WR split | 14.53% | 83.47% | 1740.3 |

## Decision

Test Four early RB/WR against actual historical weeks with fresh seeds before changing the live policy: `{"id":"core_4","label":"Four early RB/WR","lambda":0.4,"coreEarly":4,"coreDeadline":4,"starterDeadline":8,"coreTotal":10,"minCoreEach":4,"luxuryStart":9,"te2Edge":5,"qb2Edge":5}`. It subsequently failed the seven-season consistency gate in `out/draft_historical_robustness_core_4.md`, so the live policy remains unchanged.
