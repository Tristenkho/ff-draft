# 2026 projection ensemble analysis

## Outcome

- ESPN, CBS, and FFToday are combined with a robust median when available.
- CBS and FFToday raw stat lines are rescored under the league's passing, rushing, receiving, first-down, and fumble rules.
- ADP and ECR are not projection inputs.
- Player-specific 2023-25 first-down rates are regressed toward position averages before CBS/FFToday are rescored; matched players: 190/216.
- Mean absolute projection change among matched players: 10.1 points.
- Three-source coverage: 197/216 skill players (91.2%).
- Two-or-more-source coverage: 213/216 skill players (98.6%).

## Coverage

| Position | Three sources | At least two sources |
| --- | ---: | ---: |
| QB | 30/30 | 30/30 |
| RB | 65/70 | 70/70 |
| WR | 77/90 | 88/90 |
| TE | 25/26 | 25/26 |

## Largest overall projection-rank changes

Positive means the ensemble moves the player up.

| Player | Pos | ESPN/custom | Ensemble | Old rank | New rank | Change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Chris Godwin Jr. | WR | 135.9 | 163.3 | 138 | 106 | +32 |
| Tyrone Tracy Jr. | RB | 83.2 | 124.1 | 182 | 151 | +31 |
| Tank Dell | WR | 92.3 | 129.9 | 174 | 146 | +28 |
| Matthew Golden | WR | 162.5 | 143.0 | 106 | 133 | -27 |
| Blake Corum | RB | 157.3 | 138.4 | 111 | 137 | -26 |
| Mike Evans | WR | 164.0 | 195.3 | 104 | 78 | +26 |
| James Conner | RB | 0.0 | 75.9 | 216 | 193 | +23 |
| Jacoby Brissett | QB | 201.0 | 246.6 | 71 | 50 | +21 |
| Aaron Jones Sr. | RB | 174.2 | 157.4 | 95 | 116 | -21 |
| Makai Lemon | WR | 153.3 | 138.3 | 117 | 138 | -21 |
| Wan'Dale Robinson | WR | 145.0 | 160.1 | 131 | 110 | +21 |
| Malik Willis | QB | 240.7 | 295.0 | 46 | 26 | +20 |
| Jayden Reed | WR | 148.3 | 163.0 | 127 | 107 | +20 |
| Dalton Schultz | TE | 110.8 | 133.3 | 161 | 141 | +20 |
| Kyler Murray | QB | 253.4 | 299.1 | 41 | 24 | +17 |
| Josh Jacobs | RB | 266.8 | 247.6 | 31 | 48 | -17 |
| Bucky Irving | RB | 198.6 | 229.9 | 72 | 55 | +17 |
| Kyle Monangai | RB | 171.0 | 157.8 | 97 | 114 | -17 |
| Chris Rodriguez Jr. | RB | 71.9 | 102.3 | 190 | 173 | +17 |
| Dylan Sampson | RB | 76.2 | 103.3 | 188 | 171 | +17 |

## Largest source disagreements

| Player | Pos | ESPN | CBS | FFToday | Median | Uncertainty |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Kaelon Black | RB | 28.1 | 121.2 | 21.9 | 28.1 | 46.0 |
| Troy Franklin | WR | 44.8 | 137.6 | 63.4 | 63.4 | 42.3 |
| Emanuel Wilson | RB | 9.6 | 95.6 | 11.6 | 11.6 | 40.2 |
| Jordan James | RB | 59.6 | 121.5 | 44.5 | 59.6 | 36.7 |
| Drake London | WR | 233.5 | 310.1 | 254.8 | 254.8 | 62.9 |
| Jacoby Brissett | QB | 201.0 | 276.5 | 246.7 | 246.6 | 49.4 |
| Malik Willis | QB | 240.7 | 308.8 | 295.0 | 295.0 | 54.6 |
| George Pickens | WR | 211.9 | 277.6 | 214.2 | 214.3 | 54.7 |
| Bijan Robinson | RB | 331.6 | 394.7 | 357.4 | 357.4 | 96.5 |
| Kayshon Boutte | WR | 68.1 | 126.9 | 65.7 | 68.1 | 31.8 |
| Tyrone Tracy Jr. | RB | 83.2 | 142.6 | 124.1 | 124.1 | 40.7 |
| Chris Rodriguez Jr. | RB | 71.9 | 130.2 | 102.3 | 102.3 | 35.7 |
| George Kittle | TE | 151.6 | 184.4 | 128.2 | 151.6 | 41.7 |
| Caleb Williams | QB | 284.2 | 337.9 | 325.1 | 325.1 | 55.6 |
| Kyler Murray | QB | 253.4 | 299.1 | 307.1 | 299.1 | 52.3 |
| Antonio Williams | WR | 69.0 | 122.5 | 78.4 | 78.4 | 28.7 |
| Jonathan Taylor | RB | 304.9 | 344.6 | 292.6 | 304.9 | 82.3 |
| Rashee Rice | WR | 236.4 | 280.6 | 229.1 | 236.4 | 55.0 |
| Kenyon Sadiq | TE | 137.6 | 122.3 | 87.0 | 122.3 | 35.1 |
| Tyler Shough | QB | 267.4 | 301.3 | 317.9 | 301.3 | 51.5 |

## Uncertainty

The separate player `proj_unc` field combines a position-specific historical residual floor with current source disagreement in quadrature. The residual floors are half of the robust 2018–2023 preseason error scale: QB 15.6%, RB 26.0%, WR 21.2%, and TE 22.9%. This prevents three similar projections from implying false certainty while increasing uncertainty when sources materially disagree. It deliberately does not replace `sd`, which remains the app's ceiling/upside input; treating forecast error as upside created a position bias in validation.

The ceiling `sd` input is regenerated from the current ensemble projection on every refresh using the configured generic position-rate proxy: QB 14%, RB 26%, WR 23%, TE 25%, K 10%, and D/ST 18%. It is not a player-specific volatility estimate.

## Limitations

- ESPN is the current authenticated league-scored projection embedded by `refresh_draft_data.py`.
- CBS and FFToday do not project first downs, so player-specific 2023–25 reception/carry/completion rates are regressed toward the position baseline; rookies and unmatched players use that baseline.
- FFToday does not expose projected fumbles in its public table; its source score therefore omits that small component. CBS and ESPN retain their fumble assumptions.
- K and D/ST use ESPN's league-scored season and Weeks 1–3 projections because equivalent raw multi-source scoring was not available under this league's distance and defense-tier rules. D/ST is ranked primarily for early streaming; kicker retains more season-long and consensus signal.
