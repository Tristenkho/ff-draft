# Historical draft-policy backtest

## Decision

Holdout candidate: **Two RB/WR through R4**. It improved the sealed holdout, but must pass the separate fresh-seed, all-season robustness gate before any live change.

## Sealed 2024 holdout

| Policy | Champion | Playoffs | Regular-season points | Championship delta vs baseline (95% CI) |
| --- | ---: | ---: | ---: | ---: |
| Two RB/WR through R4 | 3.08% | 62.33% | 1476.5 | 1.92% [0.75%, 3.08%] |
| No QB2/TE2 | 1.75% | 74.58% | 1506.1 | 0.58% [-0.23%, 1.40%] |
| Current tuned build | 1.17% | 77.00% | 1510.3 | 0.00% [0.00%, 0.00%] |

## Training screen (2018–2022)

| Policy | Champion | Playoffs | Regular-season points |
| --- | ---: | ---: | ---: |
| No QB2/TE2 | 6.50% | 69.50% | 1528.5 |
| Four RB/WR through R4 | 6.50% | 62.50% | 1488.9 |
| Ceiling weight 0.60 | 5.50% | 77.50% | 1556.7 |
| Two RB/WR through R4 | 5.50% | 77.00% | 1554.0 |
| No ceiling premium | 5.00% | 78.75% | 1547.8 |
| Finish starters by R7 | 5.00% | 77.50% | 1547.1 |
| Ceiling weight 0.20 | 4.75% | 78.00% | 1549.3 |
| Volatility+dispersion sd | 4.75% | 78.00% | 1550.9 |
| ADP-dispersion sd | 4.75% | 77.25% | 1545.7 |
| Allow 7/3 RB-WR | 4.75% | 76.25% | 1548.1 |
| Current tuned build | 4.75% | 76.00% | 1547.8 |
| Nine total RB/WR | 4.75% | 76.00% | 1547.8 |
| Any superior late TE2 | 4.75% | 74.00% | 1541.8 |
| Finish starters by R9 | 4.50% | 76.25% | 1551.3 |
| Live position-rate sd (ships today) | 3.25% | 79.00% | 1551.0 |
| Live proxy sd, ceiling 0.60 | 3.00% | 77.75% | 1550.2 |

## Opponent selection validation (2023–2024)

| Selector | Pick-error RMSE (ADP SD) | Mean pick bias | Simulated/observed dispersion |
| --- | ---: | ---: | ---: |
| Calibrated market blend | 0.748 | +2.78 | 0.53× |
| Current fixed-noise logic | 3.094 | +3.89 | 0.53× |

## Method

- Preseason market: Fantasy Football Calculator half-PPR ADP snapshots from real 12-team drafts.
- Outcomes: nflverse regular-season weekly player statistics scored with this league's passing, rushing, receiving, first-down, two-point, fumble, and return-TD rules.
- Split: 2018–2022 training, 2023 policy validation, and one sealed 2024 holdout read after finalists were chosen.
- Opponent calibration: model-deviation weight `0.00`, need weight `0.20`, ADP-SD randomness multiplier `0.65` selected only on training years. Lower pick-error RMSE is better.
- ADP-to-outcome player match: 2018: 97.35% · 2019: 97.14% · 2020: 96.84% · 2021: 96.84% · 2022: 100.00% · 2023: 100.00% · 2024: 99.44%.
- Weekly lineups use only preseason value and results from earlier weeks; actual current-week points never choose the lineup.
- The same draft rooms, weekly results, special-team noise, and schedules are paired across policies.

## Limits

- Public nflverse player stats currently end at 2024, so 2025 was not invented or silently imputed.
- Only one untouched holdout season is available. Thousands of rooms reduce draft-room Monte Carlo error but do not turn one NFL season into thousands of independent seasons.
- Historical source projections were not available consistently across all years. The backtest constructs preseason values only from prior-season results plus contemporaneous ADP, without using that season's outcomes.
- K/DST contribute paired generic weekly scoring because nflverse player stats do not contain defense-level fantasy scoring. Policy comparisons still reserve the same final two picks for them.
- Waiver execution and historical injury designations are not reconstructed; missing weeks are reflected in actual player availability and roster depth.
