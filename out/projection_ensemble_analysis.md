# 2026 projection ensemble analysis

## Outcome

- ESPN, CBS, and FFToday are combined with a robust median when available.
- CBS and FFToday raw stat lines are rescored under the league's passing, rushing, receiving, first-down, and fumble rules.
- ADP and ECR are not projection inputs.
- Player-specific 2023-25 first-down rates are regressed toward position averages before CBS/FFToday are rescored; matched players: 193/216.
- Mean absolute projection change among matched players: 9.8 points.
- Three-source coverage: 201/216 skill players (93.1%).
- Two-or-more-source coverage: 212/216 skill players (98.1%).

## Coverage

| Position | Three sources | At least two sources |
| --- | ---: | ---: |
| QB | 30/30 | 30/30 |
| RB | 65/70 | 70/70 |
| WR | 81/90 | 87/90 |
| TE | 25/26 | 25/26 |

## Largest overall projection-rank changes

Positive means the ensemble moves the player up.

| Player | Pos | ESPN/custom | Ensemble | Old rank | New rank | Change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Tyrone Tracy Jr. | RB | 61.8 | 101.2 | 201 | 171 | +30 |
| Chris Godwin Jr. | WR | 135.7 | 163.3 | 134 | 106 | +28 |
| Matthew Golden | WR | 162.0 | 143.0 | 105 | 132 | -27 |
| Blake Corum | RB | 157.3 | 138.4 | 111 | 136 | -25 |
| Mike Evans | WR | 163.8 | 195.3 | 102 | 77 | +25 |
| Chris Rodriguez Jr. | RB | 72.1 | 102.3 | 193 | 169 | +24 |
| Dylan Sampson | RB | 76.5 | 103.3 | 190 | 167 | +23 |
| Jacoby Brissett | QB | 200.2 | 246.6 | 71 | 49 | +22 |
| Malik Willis | QB | 242.0 | 295.0 | 46 | 26 | +20 |
| James Conner | RB | 0.0 | 75.9 | 215 | 195 | +20 |
| Jayden Reed | WR | 147.8 | 163.2 | 126 | 107 | +19 |
| De'Zhaun Stribling | WR | 116.0 | 136.4 | 158 | 139 | +19 |
| Dalton Schultz | TE | 110.7 | 133.3 | 160 | 143 | +17 |
| Sam Darnold | QB | 243.5 | 283.4 | 45 | 29 | +16 |
| Breece Hall | RB | 260.5 | 243.0 | 34 | 50 | -16 |
| Jordyn Tyson | WR | 87.5 | 106.1 | 181 | 165 | +16 |
| Kyler Murray | QB | 253.0 | 299.1 | 39 | 24 | +15 |
| Bucky Irving | RB | 198.1 | 229.9 | 72 | 57 | +15 |
| Jaylen Warren | RB | 177.6 | 199.0 | 91 | 76 | +15 |
| Caleb Williams | QB | 283.8 | 325.1 | 22 | 8 | +14 |

## Largest source disagreements

| Player | Pos | ESPN | CBS | FFToday | Median | Uncertainty |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Kaelon Black | RB | 59.0 | 121.1 | 21.9 | 59.0 | 43.7 |
| Jordan James | RB | 28.4 | 121.6 | 44.5 | 44.5 | 42.3 |
| Emanuel Wilson | RB | 9.6 | 95.8 | 11.6 | 11.6 | 40.3 |
| Troy Franklin | WR | 44.9 | 131.0 | 63.4 | 63.4 | 39.4 |
| Jacoby Brissett | QB | 200.2 | 276.8 | 246.7 | 246.6 | 49.7 |
| Tyrone Tracy Jr. | RB | 61.8 | 136.3 | 101.2 | 101.2 | 40.2 |
| Drake London | WR | 233.6 | 303.9 | 254.8 | 254.8 | 61.5 |
| Tank Dell | WR | 133.6 | 138.8 | 69.7 | 133.6 | 42.3 |
| Malik Willis | QB | 242.0 | 309.3 | 295.0 | 295.0 | 54.4 |
| George Pickens | WR | 211.5 | 277.7 | 214.2 | 214.3 | 54.8 |
| Ja'Kobi Lane | WR | 89.9 | 142.4 | 79.4 | 89.9 | 33.5 |
| Kayshon Boutte | WR | 76.9 | 124.4 | 65.7 | 76.9 | 30.2 |
| Chris Rodriguez Jr. | RB | 72.1 | 130.6 | 102.3 | 102.3 | 35.7 |
| Oronde Gadsden | TE | 66.0 | 122.5 | 85.5 | 85.5 | 30.5 |
| Bijan Robinson | RB | 331.4 | 387.4 | 357.4 | 357.4 | 95.7 |
| Kyler Murray | QB | 253.0 | 299.1 | 307.1 | 299.1 | 52.4 |
| Denzel Boston | WR | 121.1 | 149.1 | 96.5 | 121.1 | 33.5 |
| Rashee Rice | WR | 237.2 | 281.6 | 229.1 | 237.2 | 55.3 |
| Omar Cooper Jr. | WR | 58.4 | 110.6 | 75.9 | 75.9 | 27.0 |
| RJ Harvey | RB | 132.4 | 182.2 | 140.5 | 140.5 | 42.5 |

## Uncertainty

The separate player `proj_unc` field combines a position-specific historical residual floor with current source disagreement in quadrature. The residual floors are half of the robust 2018–2023 preseason error scale: QB 15.6%, RB 26.0%, WR 21.2%, and TE 22.9%. This prevents three similar projections from implying false certainty while increasing uncertainty when sources materially disagree. It deliberately does not replace `sd`, which remains the app's ceiling/upside input; treating forecast error as upside created a position bias in validation.

The ceiling `sd` input is regenerated from the current ensemble projection on every refresh using the configured generic position-rate proxy: QB 14%, RB 26%, WR 23%, TE 25%, K 10%, and D/ST 18%. It is not a player-specific volatility estimate.

## Limitations

- ESPN is the current authenticated league-scored projection embedded by `refresh_draft_data.py`.
- CBS and FFToday do not project first downs, so player-specific 2023–25 reception/carry/completion rates are regressed toward the position baseline; rookies and unmatched players use that baseline.
- FFToday does not expose projected fumbles in its public table; its source score therefore omits that small component. CBS and ESPN retain their fumble assumptions.
- K and D/ST use ESPN's league-scored season and Weeks 1–3 projections because equivalent raw multi-source scoring was not available under this league's distance and defense-tier rules. D/ST is ranked primarily for early streaming; kicker retains more season-long and consensus signal.
