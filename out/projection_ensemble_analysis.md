# 2026 projection ensemble analysis

## Outcome

- ESPN, CBS, and FFToday are combined with a robust median when available.
- CBS and FFToday raw stat lines are rescored under the league's passing, rushing, receiving, first-down, and fumble rules.
- ADP and ECR are not projection inputs.
- Player-specific 2023-25 first-down rates are regressed toward position averages before CBS/FFToday are rescored; matched players: 195/218.
- Mean absolute projection change among matched players: 6.2 points.
- Three-source coverage: 202/218 skill players (92.7%).
- Two-or-more-source coverage: 212/218 skill players (97.2%).

## Coverage

| Position | Three sources | At least two sources |
| --- | ---: | ---: |
| QB | 30/30 | 30/30 |
| RB | 69/72 | 71/72 |
| WR | 78/90 | 86/90 |
| TE | 25/26 | 25/26 |

## Largest overall projection-rank changes

Positive means the ensemble moves the player up.

| Player | Pos | ESPN/custom | Ensemble | Old rank | New rank | Change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| MarShawn Lloyd | RB | 137.4 | 168.3 | 145 | 108 | +37 |
| Tyrone Tracy Jr. | RB | 39.4 | 101.2 | 210 | 177 | +33 |
| Matthew Golden | WR | 176.1 | 148.1 | 99 | 132 | -33 |
| Chris Godwin Jr. | WR | 144.0 | 163.3 | 135 | 111 | +24 |
| Blake Corum | RB | 165.7 | 141.5 | 115 | 138 | -23 |
| Chris Rodriguez Jr. | RB | 76.1 | 102.3 | 198 | 175 | +23 |
| Jacoby Brissett | QB | 218.4 | 246.6 | 67 | 46 | +21 |
| Josh Jacobs | RB | 168.1 | 153.1 | 110 | 130 | -20 |
| Adonai Mitchell | WR | 121.1 | 100.6 | 159 | 179 | -20 |
| Zach Charbonnet | RB | 136.2 | 111.3 | 146 | 164 | -18 |
| Keaton Mitchell | RB | 93.4 | 79.0 | 181 | 198 | -17 |
| Jordyn Tyson | WR | 93.0 | 109.8 | 183 | 166 | +17 |
| Dalton Schultz | TE | 117.5 | 133.3 | 161 | 144 | +17 |
| Malik Willis | QB | 264.1 | 295.0 | 43 | 27 | +16 |
| Jacory Croskey-Merritt | RB | 166.1 | 153.3 | 113 | 129 | -16 |
| Aaron Jones Sr. | RB | 173.3 | 157.4 | 105 | 121 | -16 |
| Dylan Sampson | RB | 82.8 | 103.3 | 188 | 172 | +16 |
| Mike Evans | WR | 171.1 | 189.7 | 106 | 90 | +16 |
| Gunnar Helm | TE | 111.6 | 96.5 | 166 | 182 | -16 |
| Kyle Monangai | RB | 179.3 | 161.6 | 98 | 113 | -15 |

## Largest source disagreements

| Player | Pos | ESPN | CBS | FFToday | Median | Uncertainty |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Kaelon Black | RB | 62.3 | 121.2 | 38.4 | 62.3 | 38.4 |
| Mike Washington Jr. | RB | 69.4 | 136.9 | 64.6 | 69.4 | 37.6 |
| Ja'Kobi Lane | WR | 103.9 | 142.3 | 79.4 | 103.9 | 34.0 |
| Tyrone Tracy Jr. | RB | 39.4 | 101.8 | 101.2 | 101.2 | 39.3 |
| George Pickens | WR | 224.9 | 276.4 | 214.2 | 224.9 | 54.9 |
| George Kittle | TE | 175.9 | 200.4 | 141.4 | 175.9 | 47.0 |
| Rashee Rice | WR | 240.8 | 280.8 | 222.8 | 240.8 | 56.5 |
| Breece Hall | RB | 276.1 | 220.5 | 243.0 | 243.0 | 67.2 |
| Chris Rodriguez Jr. | RB | 76.1 | 130.7 | 102.3 | 102.3 | 34.7 |
| Denzel Boston | WR | 130.5 | 149.7 | 96.5 | 130.5 | 35.3 |
| Jacoby Brissett | QB | 218.4 | 271.0 | 246.7 | 246.6 | 44.1 |
| Jeremiyah Love | RB | 273.1 | 221.1 | 254.8 | 254.8 | 69.7 |
| Isaiah Likely | TE | 140.4 | 182.2 | 132.1 | 140.4 | 38.9 |
| Jauan Jennings | WR | 103.8 | 144.3 | 94.5 | 103.8 | 30.8 |
| Malik Willis | QB | 264.1 | 313.6 | 295.0 | 295.0 | 50.3 |
| Jonah Coleman | RB | 73.2 | 25.5 | 57.5 | 57.5 | 24.9 |
| Jonathan Taylor | RB | 322.2 | 339.9 | 292.6 | 322.2 | 86.0 |
| Dallas Goedert | TE | 160.3 | 190.0 | 142.9 | 160.3 | 41.6 |
| Kayshon Boutte | WR | 128.6 | 126.9 | 82.0 | 126.9 | 34.5 |
| De'Von Achane | RB | 292.2 | 308.5 | 262.0 | 292.2 | 78.4 |

## Uncertainty

The separate player `proj_unc` field combines a position-specific historical residual floor with current source disagreement in quadrature. The residual floors are half of the robust 2018–2023 preseason error scale: QB 15.6%, RB 26.0%, WR 21.2%, and TE 22.9%. This prevents three similar projections from implying false certainty while increasing uncertainty when sources materially disagree. It deliberately does not replace `sd`, which remains the app's ceiling/upside input; treating forecast error as upside created a position bias in validation.

The ceiling `sd` input is regenerated from the current ensemble projection on every refresh using the configured generic position-rate proxy: QB 14%, RB 26%, WR 23%, TE 25%, K 10%, and D/ST 18%. It is not a player-specific volatility estimate.

## Limitations

- ESPN is the current authenticated league-scored projection embedded by `refresh_draft_data.py`.
- CBS and FFToday do not project first downs, so player-specific 2023–25 reception/carry/completion rates are regressed toward the position baseline; rookies and unmatched players use that baseline.
- FFToday does not expose projected fumbles in its public table; its source score therefore omits that small component. CBS and ESPN retain their fumble assumptions.
- K and D/ST use ESPN's league-scored season and Weeks 1–3 projections because equivalent raw multi-source scoring was not available under this league's distance and defense-tier rules. D/ST is ranked primarily for early streaming; kicker retains more season-long and consensus signal.
