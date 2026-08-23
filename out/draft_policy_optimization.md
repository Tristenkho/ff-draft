# Draft policy championship optimizer

## Outcome

**No challenger proved a statistically reliable championship-rate improvement over the current tuned build.** Keep the baseline configuration; the apparent leader's adjusted room-clustered interval still includes zero.

## Method

- Exact live-engine fingerprint: `ae8561a3b3fdea03b8689f0a876bda26b49cb084199722163f2281968f1d918a`.
- Stage 1: 16 policies × 100 seeded draft rooms × 3 season outcomes per room.
- Confirmation: baseline plus the top three challengers, each tested in 200 new seeded rooms × 3 outcomes. Confirmation rankings and intervals use this sample only; Stage 1 is screening data only. This is sample independence inside one synthetic model, not independent real-world evidence.
- Opponents use the live market + roster-need selector and observed-ADP-dispersion-scaled randomness. Policy paths can consume randomness differently, so "same seed" does not guarantee identical opponent picks after paths diverge.
- Evaluation is separate from draft selection: projection/consensus ensemble, season uncertainty, weekly volatility, team correlation, injuries, free replacement-level starter fill-ins, lineup setting, 14-week standings, and 8-team Weeks 15–17 playoffs. The free fill-in assumption makes this evaluator weak evidence for bench-depth, QB2, TE2, K, or D/ST strategy.
- Ranking challengers alter only the recommendation selected from the live engine's uncertainty-aware top wait band. ECR-first uses expert rank before Model rank inside that band; it does not put ECR into projections, timing, survival, or VONA.
- The synthetic talent evaluator includes an ADP/ECR-derived consensus component, so it is structurally favorable to consensus challengers. Any apparent win still needs historical robustness and is not independent evidence.
- Confidence intervals cluster policy differences by seeded draft room after averaging the 3 correlated season outcomes within each drafted roster. The 98.33% two-sided intervals (z = 2.394) are Bonferroni-adjusted for three finalist-versus-baseline comparisons.
- Every tested policy must match the live strategy schema and every simulated roster must pass the legal-roster assertion.
- This synthetic optimizer is subordinate to the historical weekly backtest in `out/draft_historical_backtest.md`.

## Finalists (new confirmation sample)

| Rank | Policy | Champion | Playoffs | Avg regular-season PF | Championship Δ vs baseline (adjusted CI) | Legal drafts |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Model-first band + 50% blend | 16.17% | 83.00% | 1652.4 | 3.33% [-0.86%, 7.53%] | 200/200 |
| 2 | Model first inside wait band | 14.00% | 82.00% | 1650.9 | 1.17% [-3.19%, 5.53%] | 200/200 |
| 3 | 15-rank conservative review | 13.50% | 81.67% | 1653.5 | 0.67% [-3.64%, 4.97%] | 200/200 |
| 4 | Current tuned build | 12.83% | 80.33% | 1643.3 | 0.00% [0.00%, 0.00%] | 200/200 |

## Stage-one screen

| Policy | Champion | Playoffs | Avg PF |
| --- | ---: | ---: | ---: |
| Current tuned build | 12.67% | 78.00% | 1631.0 |
| Model first inside wait band | 17.33% | 78.33% | 1655.0 |
| 50% ECR Model blend | 12.67% | 78.00% | 1631.0 |
| Model-first band + 50% blend | 14.00% | 79.33% | 1645.8 |
| 15-rank conservative review | 17.33% | 76.33% | 1651.8 |
| Lower ceiling weight | 13.00% | 80.33% | 1633.7 |
| Higher ceiling weight | 13.67% | 75.33% | 1635.0 |
| Only two early RB/WR | 11.67% | 77.33% | 1633.5 |
| Four early RB/WR | 12.00% | 77.67% | 1638.0 |
| Finish RB2/WR2/FLEX by R7 | 12.33% | 78.00% | 1632.0 |
| Finish RB2/WR2/FLEX by R9 | 12.67% | 78.67% | 1630.9 |
| Secure WR1 by R4 | 12.67% | 78.00% | 1631.0 |
| Delay WR1 deadline to R6 | 12.67% | 78.00% | 1631.0 |
| Secure QB by R9 | 12.67% | 78.00% | 1631.0 |
| Delay QB deadline to R11 | 12.67% | 78.00% | 1631.0 |
| Allow 7/3 RB-WR split | 12.67% | 78.33% | 1631.4 |

## Decision

Retain the current strategy configuration: `{"id":"baseline","label":"Current tuned build","lambda":0.4,"ecrWeight":0.35,"decisionMode":"consensus_tier","coreEarly":3,"coreDeadline":4,"wrDeadline":5,"coreStarterDeadline":8,"teDeadline":9,"qbDeadline":10,"coreTotal":10,"minCoreEach":4}`. Historical holdout and robustness testing remain the final gate for live policy changes.
