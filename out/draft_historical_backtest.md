# Historical draft-policy backtest

## Decision

Holdout candidate: **Finish starters by R7**. It improved the sealed holdout, but must pass the separate fresh-seed, all-season robustness gate before any live change.

## Sealed 2024 holdout

| Policy | Champion | Playoffs | Regular-season points | Championship delta vs baseline (95% CI) |
| --- | ---: | ---: | ---: | ---: |
| Finish starters by R7 | 4.25% | 86.75% | 1578.6 | 2.75% [1.14%, 4.36%] |
| Four RB/WR through R4 | 3.88% | 65.25% | 1491.2 | 2.38% [0.78%, 3.97%] |
| Current tuned build | 1.50% | 76.50% | 1509.5 | 0.00% [0.00%, 0.00%] |
| No QB2/TE2 | 1.38% | 74.38% | 1506.6 | -0.12% [-1.07%, 0.82%] |

## Training screen (2018–2022)

| Policy | Champion | Playoffs | Regular-season points |
| --- | ---: | ---: | ---: |
| Four RB/WR through R4 | 9.33% | 62.67% | 1486.9 |
| No QB2/TE2 | 5.33% | 66.00% | 1527.2 |
| Finish starters by R7 | 3.33% | 78.00% | 1545.0 |
| Ceiling weight 0.60 | 3.33% | 76.00% | 1556.1 |
| Two RB/WR through R4 | 2.67% | 79.33% | 1554.5 |
| Finish starters by R9 | 2.67% | 77.33% | 1550.2 |
| Allow 7/3 RB-WR | 2.67% | 77.33% | 1546.0 |
| Ceiling weight 0.20 | 2.00% | 78.67% | 1543.7 |
| Current tuned build | 2.00% | 76.00% | 1544.9 |
| Nine total RB/WR | 2.00% | 76.00% | 1544.9 |
| Any superior late TE2 | 2.00% | 74.67% | 1540.8 |
| No ceiling premium | 1.33% | 80.00% | 1543.9 |

## Opponent selection validation (2023–2024)

| Selector | Pick-error RMSE (ADP SD) | Mean pick bias | Simulated/observed dispersion |
| --- | ---: | ---: | ---: |
| Calibrated market blend | 0.756 | +2.78 | 0.52× |
| Current fixed-noise logic | 3.100 | +3.80 | 0.52× |

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
