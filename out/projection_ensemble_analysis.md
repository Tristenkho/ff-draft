# 2026 projection ensemble analysis

## Outcome

- ESPN, CBS, and FFToday are combined with a robust median when available.
- CBS and FFToday raw stat lines are rescored under the league's passing, rushing, receiving, first-down, and fumble rules.
- ADP and ECR are not projection inputs.
- Mean absolute projection change among matched players: 10.5 points.
- Three-source coverage: 194/216 skill players (89.8%).
- Two-or-more-source coverage: 213/216 skill players (98.6%).

## Coverage

| Position | Three sources | At least two sources |
| --- | ---: | ---: |
| QB | 30/30 | 30/30 |
| RB | 64/70 | 70/70 |
| WR | 75/90 | 88/90 |
| TE | 25/26 | 25/26 |

## Largest overall projection-rank changes

Positive means the ensemble moves the player up.

| Player | Pos | ESPN/custom | Ensemble | Old rank | New rank | Change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Stefon Diggs | WR | 0.0 | 160.6 | 215 | 110 | +105 |
| Tyrone Tracy Jr. | RB | 83.2 | 124.1 | 181 | 151 | +30 |
| Chris Godwin Jr. | WR | 135.9 | 162.2 | 137 | 109 | +28 |
| Tank Dell | WR | 92.3 | 129.1 | 174 | 146 | +28 |
| Blake Corum | RB | 157.3 | 136.9 | 111 | 138 | -27 |
| Matthew Golden | WR | 162.5 | 143.3 | 106 | 133 | -27 |
| Wan'Dale Robinson | WR | 145.1 | 165.1 | 131 | 105 | +26 |
| Mike Evans | WR | 164.1 | 192.6 | 104 | 80 | +24 |
| Jacoby Brissett | QB | 201.0 | 246.8 | 71 | 48 | +23 |
| Terrance Ferguson | TE | 119.8 | 97.7 | 154 | 177 | -23 |
| James Conner | RB | 0.0 | 75.0 | 214 | 192 | +22 |
| Malik Willis | QB | 240.7 | 294.9 | 46 | 25 | +21 |
| Jayden Reed | WR | 148.3 | 164.8 | 127 | 107 | +20 |
| Makai Lemon | WR | 153.3 | 141.5 | 117 | 135 | -18 |
| Dalton Schultz | TE | 110.8 | 133.2 | 160 | 142 | +18 |
| Kyler Murray | QB | 253.4 | 299.3 | 41 | 24 | +17 |
| Bucky Irving | RB | 198.6 | 230.5 | 72 | 55 | +17 |
| Dylan Sampson | RB | 76.2 | 104.0 | 186 | 169 | +17 |
| Kenyon Sadiq | TE | 137.6 | 122.3 | 136 | 153 | -17 |
| Sam Darnold | QB | 243.5 | 282.6 | 45 | 29 | +16 |

## Largest source disagreements

| Player | Pos | ESPN | CBS | FFToday | Median | Uncertainty |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Troy Franklin | WR | 44.8 | 138.6 | 64.4 | 64.4 | 42.6 |
| Emanuel Wilson | RB | 9.6 | 95.0 | 11.5 | 11.5 | 40.0 |
| Jordan James | RB | 59.6 | 121.5 | 44.5 | 59.6 | 36.7 |
| Jacoby Brissett | QB | 201.0 | 276.8 | 246.8 | 246.8 | 49.5 |
| Drake London | WR | 233.5 | 307.4 | 252.2 | 252.3 | 62.0 |
| Malik Willis | QB | 240.7 | 308.8 | 294.9 | 294.9 | 54.6 |
| George Pickens | WR | 211.9 | 273.6 | 211.3 | 211.9 | 53.6 |
| Kayshon Boutte | WR | 68.1 | 126.1 | 65.3 | 68.1 | 31.6 |
| Tyrone Tracy Jr. | RB | 83.2 | 143.3 | 124.1 | 124.1 | 40.9 |
| Bijan Robinson | RB | 331.6 | 391.4 | 354.2 | 354.2 | 95.3 |
| George Kittle | TE | 151.7 | 180.8 | 125.5 | 151.7 | 41.4 |
| Chris Rodriguez Jr. | RB | 71.9 | 126.4 | 101.0 | 101.0 | 34.4 |
| Kyler Murray | QB | 253.4 | 299.3 | 307.5 | 299.3 | 52.4 |
| Tyler Shough | QB | 267.4 | 302.4 | 319.0 | 302.4 | 51.8 |
| Rashee Rice | WR | 236.4 | 281.8 | 230.4 | 236.4 | 55.1 |
| Jonathan Taylor | RB | 304.9 | 342.5 | 291.1 | 304.9 | 82.2 |
| Kenyon Sadiq | TE | 137.6 | 122.3 | 87.0 | 122.3 | 35.1 |
| Chris Olave | WR | 213.2 | 263.0 | 228.1 | 228.1 | 52.7 |
| Cooper Kupp | WR | 88.0 | 137.5 | 91.2 | 91.2 | 29.7 |
| Jauan Jennings | WR | 97.4 | 143.5 | 94.1 | 97.4 | 30.6 |

## Uncertainty

The separate player `proj_unc` field combines a position-specific historical residual floor with current source disagreement in quadrature. The residual floors are half of the robust 2018–2023 preseason error scale: QB 15.6%, RB 26.0%, WR 21.2%, and TE 22.9%. This prevents three similar projections from implying false certainty while increasing uncertainty when sources materially disagree. It deliberately does not replace `sd`, which remains the app's ceiling/upside input; treating forecast error as upside created a position bias in validation.

## Limitations

- ESPN is the current authenticated league-scored projection embedded by `refresh_draft_data.py`.
- CBS and FFToday do not project first downs, so the existing empirical reception/carry rates are applied. Passing first downs use 0.518 per completion from nflverse 2023–2024 player stats.
- FFToday does not expose projected fumbles in its public table; its source score therefore omits that small component. CBS and ESPN retain their fumble assumptions.
- K and D/ST use ESPN's league-scored projection because equivalent raw multi-source scoring was not available under this league's distance and defense-tier rules; their late-round order adds a 25% positional-consensus sanity check.
