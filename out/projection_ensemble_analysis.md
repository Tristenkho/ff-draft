# 2026 projection ensemble analysis

## Outcome

- ESPN, CBS, and FFToday are combined with a robust median when available.
- CBS and FFToday raw stat lines are rescored under the league's passing, rushing, receiving, first-down, and fumble rules.
- ADP and ECR are not projection inputs.
- Player-specific 2023-24 first-down rates are regressed toward position averages before CBS/FFToday are rescored; matched players: 160/216.
- Mean absolute projection change among matched players: 10.8 points.
- Three-source coverage: 194/216 skill players (89.8%).
- Two-or-more-source coverage: 212/216 skill players (98.1%).

## Coverage

| Position | Three sources | At least two sources |
| --- | ---: | ---: |
| QB | 30/30 | 30/30 |
| RB | 64/70 | 70/70 |
| WR | 75/90 | 87/90 |
| TE | 25/26 | 25/26 |

## Largest overall projection-rank changes

Positive means the ensemble moves the player up.

| Player | Pos | ESPN/custom | Ensemble | Old rank | New rank | Change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Stefon Diggs | WR | 0.0 | 155.3 | 215 | 120 | +95 |
| Tyrone Tracy Jr. | RB | 83.2 | 123.8 | 181 | 151 | +30 |
| Chris Godwin Jr. | WR | 135.9 | 163.1 | 137 | 108 | +29 |
| Tank Dell | WR | 92.3 | 130.0 | 174 | 146 | +28 |
| Blake Corum | RB | 157.3 | 136.9 | 111 | 138 | -27 |
| Mike Evans | WR | 164.1 | 194.9 | 104 | 77 | +27 |
| Matthew Golden | WR | 162.5 | 143.3 | 106 | 133 | -27 |
| James Conner | RB | 0.0 | 75.9 | 214 | 191 | +23 |
| Terrance Ferguson | TE | 119.8 | 97.7 | 154 | 177 | -23 |
| Jacoby Brissett | QB | 201.0 | 246.1 | 71 | 49 | +22 |
| Wan'Dale Robinson | WR | 145.1 | 160.7 | 131 | 109 | +22 |
| Malik Willis | QB | 240.7 | 294.4 | 46 | 26 | +20 |
| Jayden Reed | WR | 148.3 | 163.4 | 127 | 107 | +20 |
| Chris Rodriguez Jr. | RB | 71.9 | 101.9 | 189 | 171 | +18 |
| Dalton Schultz | TE | 110.8 | 133.9 | 160 | 142 | +18 |
| Kyler Murray | QB | 253.4 | 299.3 | 41 | 24 | +17 |
| Bucky Irving | RB | 198.6 | 231.7 | 72 | 55 | +17 |
| Dylan Sampson | RB | 76.2 | 104.0 | 186 | 169 | +17 |
| Makai Lemon | WR | 153.3 | 141.6 | 117 | 134 | -17 |
| Kenyon Sadiq | TE | 137.6 | 122.3 | 136 | 153 | -17 |

## Largest source disagreements

| Player | Pos | ESPN | CBS | FFToday | Median | Uncertainty |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Troy Franklin | WR | 44.8 | 137.1 | 63.6 | 63.6 | 42.0 |
| Emanuel Wilson | RB | 9.6 | 95.4 | 11.5 | 11.5 | 40.1 |
| Jordan James | RB | 59.6 | 121.5 | 44.5 | 59.6 | 36.7 |
| Drake London | WR | 233.5 | 309.8 | 254.5 | 254.5 | 62.8 |
| Jacoby Brissett | QB | 201.0 | 275.8 | 246.1 | 246.1 | 49.2 |
| Malik Willis | QB | 240.7 | 308.1 | 294.4 | 294.4 | 54.4 |
| George Pickens | WR | 211.9 | 275.0 | 212.2 | 212.2 | 53.9 |
| Bijan Robinson | RB | 331.6 | 394.5 | 357.1 | 357.1 | 96.4 |
| Kayshon Boutte | WR | 68.1 | 125.9 | 65.1 | 68.1 | 31.5 |
| Tyrone Tracy Jr. | RB | 83.2 | 142.3 | 123.8 | 123.8 | 40.6 |
| George Kittle | TE | 151.7 | 183.8 | 127.8 | 151.7 | 41.6 |
| Kyler Murray | QB | 253.4 | 299.3 | 307.3 | 299.3 | 52.4 |
| Chris Olave | WR | 213.2 | 265.0 | 229.9 | 229.9 | 53.3 |
| Jonathan Taylor | RB | 304.9 | 343.7 | 292.0 | 304.9 | 82.3 |
| Tyler Shough | QB | 267.4 | 302.4 | 319.0 | 302.4 | 51.8 |
| Rashee Rice | WR | 236.4 | 281.2 | 229.7 | 236.4 | 55.1 |
| Kenyon Sadiq | TE | 137.6 | 122.3 | 87.0 | 122.3 | 35.1 |
| Chris Rodriguez Jr. | RB | 71.9 | 121.4 | 101.8 | 101.9 | 33.4 |
| Jauan Jennings | WR | 97.4 | 143.8 | 94.3 | 97.4 | 30.6 |
| Baker Mayfield | QB | 267.3 | 315.7 | 288.3 | 288.3 | 49.2 |

## Uncertainty

The separate player `proj_unc` field combines a position-specific historical residual floor with current source disagreement in quadrature. The residual floors are half of the robust 2018–2023 preseason error scale: QB 15.6%, RB 26.0%, WR 21.2%, and TE 22.9%. This prevents three similar projections from implying false certainty while increasing uncertainty when sources materially disagree. It deliberately does not replace `sd`, which remains the app's ceiling/upside input; treating forecast error as upside created a position bias in validation.

## Limitations

- ESPN is the current authenticated league-scored projection embedded by `refresh_draft_data.py`.
- CBS and FFToday do not project first downs, so player-specific 2023–24 reception/carry/completion rates are regressed toward the position baseline; rookies and unmatched players use that baseline.
- FFToday does not expose projected fumbles in its public table; its source score therefore omits that small component. CBS and ESPN retain their fumble assumptions.
- K and D/ST use ESPN's league-scored season and Weeks 1–3 projections because equivalent raw multi-source scoring was not available under this league's distance and defense-tier rules. D/ST is ranked primarily for early streaming; kicker retains more season-long and consensus signal.
