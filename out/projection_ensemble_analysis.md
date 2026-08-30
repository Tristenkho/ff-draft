# 2026 projection ensemble analysis

## Outcome

- ESPN, CBS, and FFToday are combined with a robust median when available.
- CBS and FFToday raw stat lines are rescored under the league's passing, rushing, receiving, first-down, and fumble rules.
- ADP and ECR are not projection inputs.
- Player-specific 2023-25 first-down rates are regressed toward position averages before CBS/FFToday are rescored; matched players: 195/218.
- Mean absolute projection change among matched players: 6.6 points.
- Three-source coverage: 199/218 skill players (91.3%).
- Two-or-more-source coverage: 212/218 skill players (97.2%).

## Coverage

| Position | Three sources | At least two sources |
| --- | ---: | ---: |
| QB | 30/30 | 30/30 |
| RB | 66/72 | 70/72 |
| WR | 78/90 | 87/90 |
| TE | 25/26 | 25/26 |

## Largest overall projection-rank changes

Positive means the ensemble moves the player up.

| Player | Pos | ESPN/custom | Ensemble | Old rank | New rank | Change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| MarShawn Lloyd | RB | 86.9 | 141.5 | 184 | 137 | +47 |
| Tyrone Tracy Jr. | RB | 39.4 | 101.2 | 209 | 175 | +34 |
| Matthew Golden | WR | 172.4 | 143.0 | 103 | 133 | -30 |
| Blake Corum | RB | 165.8 | 138.4 | 115 | 141 | -26 |
| Chris Rodriguez Jr. | RB | 76.0 | 102.3 | 195 | 172 | +23 |
| Mike Evans | WR | 171.9 | 195.3 | 106 | 83 | +23 |
| Chris Godwin Jr. | WR | 144.1 | 163.3 | 134 | 112 | +22 |
| Jacoby Brissett | QB | 218.8 | 246.6 | 68 | 48 | +20 |
| Aaron Jones Sr. | RB | 172.4 | 157.4 | 102 | 121 | -19 |
| Adonai Mitchell | WR | 120.7 | 100.6 | 158 | 177 | -19 |
| Tank Dell | WR | 89.3 | 112.4 | 183 | 164 | +19 |
| Malik Willis | QB | 263.4 | 295.0 | 45 | 27 | +18 |
| Dylan Sampson | RB | 82.9 | 103.3 | 188 | 171 | +17 |
| Josh Jacobs | RB | 265.5 | 231.5 | 43 | 59 | -16 |
| Kyle Monangai | RB | 180.5 | 161.5 | 97 | 113 | -16 |
| Breece Hall | RB | 275.7 | 243.0 | 35 | 50 | -15 |
| Jacory Croskey-Merritt | RB | 166.6 | 153.3 | 113 | 128 | -15 |
| Keaton Mitchell | RB | 93.4 | 79.0 | 179 | 194 | -15 |
| Carnell Tate | WR | 188.1 | 168.6 | 92 | 107 | -15 |
| Gunnar Helm | TE | 111.7 | 96.5 | 164 | 179 | -15 |

## Largest source disagreements

| Player | Pos | ESPN | CBS | FFToday | Median | Uncertainty |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Josh Jacobs | RB | 265.5 | 231.5 | 122.4 | 231.5 | 85.7 |
| Tyrone Tracy Jr. | RB | 39.4 | 136.8 | 101.2 | 101.2 | 48.1 |
| Jordan James | RB | 30.0 | 121.6 | 43.4 | 43.4 | 41.9 |
| MarShawn Lloyd | RB | 86.9 | 141.5 | 177.9 | 141.5 | 52.5 |
| Kaelon Black | RB | 62.4 | 121.2 | 38.4 | 62.4 | 38.4 |
| Mike Washington Jr. | RB | 67.6 | 137.0 | 64.6 | 67.6 | 37.8 |
| Denzel Boston | WR | 130.5 | 160.8 | 96.5 | 130.5 | 38.1 |
| George Pickens | WR | 224.3 | 277.7 | 214.2 | 224.3 | 55.1 |
| Ja'Kobi Lane | WR | 95.1 | 142.4 | 79.4 | 95.1 | 33.5 |
| Rashee Rice | WR | 242.0 | 281.7 | 222.8 | 242.0 | 56.9 |
| George Kittle | TE | 172.0 | 199.8 | 141.4 | 172.0 | 46.0 |
| Breece Hall | RB | 275.7 | 220.5 | 243.0 | 243.0 | 67.1 |
| Chris Rodriguez Jr. | RB | 76.0 | 130.6 | 102.3 | 102.3 | 34.7 |
| Jacoby Brissett | QB | 218.8 | 272.6 | 246.7 | 246.6 | 44.3 |
| Oronde Gadsden | TE | 70.0 | 122.5 | 85.5 | 85.5 | 29.5 |
| Jauan Jennings | WR | 103.5 | 144.2 | 94.5 | 103.5 | 30.8 |
| Javonte Williams | RB | 265.9 | 216.6 | 235.1 | 235.1 | 64.4 |
| Isaiah Likely | TE | 140.8 | 180.9 | 132.1 | 140.8 | 38.6 |
| Jonah Coleman | RB | 73.3 | 25.5 | 57.5 | 57.5 | 24.9 |
| Jonathan Taylor | RB | 322.3 | 339.9 | 292.6 | 322.3 | 86.0 |

## Uncertainty

The separate player `proj_unc` field combines a position-specific historical residual floor with current source disagreement in quadrature. The residual floors are half of the robust 2018–2023 preseason error scale: QB 15.6%, RB 26.0%, WR 21.2%, and TE 22.9%. This prevents three similar projections from implying false certainty while increasing uncertainty when sources materially disagree. It deliberately does not replace `sd`, which remains the app's ceiling/upside input; treating forecast error as upside created a position bias in validation.

The ceiling `sd` input is regenerated from the current ensemble projection on every refresh using the configured generic position-rate proxy: QB 14%, RB 26%, WR 23%, TE 25%, K 10%, and D/ST 18%. It is not a player-specific volatility estimate.

## Limitations

- ESPN is the current authenticated league-scored projection embedded by `refresh_draft_data.py`.
- CBS and FFToday do not project first downs, so player-specific 2023–25 reception/carry/completion rates are regressed toward the position baseline; rookies and unmatched players use that baseline.
- FFToday does not expose projected fumbles in its public table; its source score therefore omits that small component. CBS and ESPN retain their fumble assumptions.
- K and D/ST use ESPN's league-scored season and Weeks 1–3 projections because equivalent raw multi-source scoring was not available under this league's distance and defense-tier rules. D/ST is ranked primarily for early streaming; kicker retains more season-long and consensus signal.
