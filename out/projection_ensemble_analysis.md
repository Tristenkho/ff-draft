# 2026 projection ensemble analysis

## Outcome

- ESPN, CBS, and FFToday are combined with a robust median when available.
- CBS and FFToday raw stat lines are rescored under the league's passing, rushing, receiving, first-down, and fumble rules.
- ADP and ECR are not projection inputs.
- Mean absolute projection change among matched players: 7.1 points.
- Three-source coverage: 171/181 skill players (94.5%).
- Two-or-more-source coverage: 180/181 skill players (99.4%).

## Coverage

| Position | Three sources | At least two sources |
| --- | ---: | ---: |
| QB | 24/24 | 24/24 |
| RB | 57/59 | 59/59 |
| WR | 69/77 | 76/77 |
| TE | 21/21 | 21/21 |

## Largest overall projection-rank changes

Positive means the ensemble moves the player up.

| Player | Pos | ESPN/custom | Ensemble | Old rank | New rank | Change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Stefon Diggs | WR | 0.0 | 160.6 | 179 | 110 | +69 |
| Matthew Golden | WR | 172.4 | 143.3 | 99 | 128 | -29 |
| Blake Corum | RB | 164.0 | 136.9 | 108 | 134 | -26 |
| Jordyn Tyson | WR | 174.9 | 156.9 | 97 | 120 | -23 |
| Chris Godwin Jr. | WR | 145.5 | 162.2 | 131 | 108 | +23 |
| Tank Dell | WR | 98.5 | 132.2 | 163 | 140 | +23 |
| Kenyon Sadiq | TE | 146.0 | 122.3 | 130 | 151 | -21 |
| Mike Evans | WR | 171.3 | 192.6 | 100 | 80 | +20 |
| Carnell Tate | WR | 195.5 | 168.6 | 78 | 97 | -19 |
| T.J. Hockenson | TE | 139.2 | 119.4 | 134 | 153 | -19 |
| Kyle Monangai | RB | 178.5 | 159.9 | 94 | 112 | -18 |
| Tyrone Tracy Jr. | RB | 88.0 | 124.1 | 167 | 149 | +18 |
| Terrance Ferguson | TE | 124.7 | 97.7 | 149 | 167 | -18 |
| Makai Lemon | WR | 161.5 | 141.5 | 113 | 130 | -17 |
| Malik Willis | QB | 266.5 | 294.9 | 43 | 26 | +17 |
| Jonathon Brooks | RB | 161.6 | 148.4 | 112 | 127 | -15 |
| Bucky Irving | RB | 208.8 | 230.5 | 67 | 53 | +14 |
| Wan'Dale Robinson | WR | 158.5 | 165.1 | 119 | 105 | +14 |
| Quinshon Judkins | RB | 232.2 | 213.6 | 52 | 65 | -13 |
| Aaron Jones Sr. | RB | 182.4 | 167.6 | 89 | 100 | -11 |

## Largest source disagreements

| Player | Pos | ESPN | CBS | FFToday | Median | Uncertainty |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Jordan James | RB | 62.6 | 121.5 | 44.5 | 62.6 | 36.7 |
| George Pickens | WR | 223.0 | 273.6 | 211.3 | 223.0 | 54.5 |
| Kenyon Sadiq | TE | 146.0 | 122.3 | 87.0 | 122.3 | 37.1 |
| Drake London | WR | 249.1 | 307.4 | 252.2 | 252.3 | 59.8 |
| Tyrone Tracy Jr. | RB | 88.0 | 143.3 | 124.1 | 124.1 | 39.6 |
| George Kittle | TE | 160.0 | 180.8 | 125.5 | 160.0 | 43.1 |
| Carnell Tate | WR | 195.5 | 143.2 | 168.6 | 168.6 | 41.6 |
| Rashee Rice | WR | 251.4 | 281.8 | 230.4 | 251.4 | 57.3 |
| Jonathan Taylor | RB | 318.0 | 342.5 | 291.1 | 318.0 | 85.3 |
| Chris Rodriguez Jr. | RB | 75.5 | 126.4 | 101.0 | 101.0 | 33.5 |
| Matthew Golden | WR | 172.4 | 121.7 | 143.3 | 143.3 | 36.8 |
| Jauan Jennings | WR | 105.2 | 143.5 | 94.1 | 105.2 | 30.7 |
| Antonio Williams | WR | 107.3 | 126.8 | 78.4 | 107.3 | 30.2 |
| Kenneth Walker III | RB | 271.8 | 223.5 | 258.4 | 258.4 | 70.2 |
| Isaiah Likely | TE | 140.9 | 180.0 | 131.9 | 140.9 | 38.4 |
| Bijan Robinson | RB | 343.5 | 391.4 | 354.2 | 354.2 | 94.4 |
| Darnell Mooney | WR | 85.8 | 110.9 | 63.9 | 85.8 | 26.5 |
| Dallas Goedert | TE | 159.5 | 189.1 | 142.3 | 159.5 | 41.3 |
| Rico Dowdle | RB | 188.1 | 213.2 | 166.7 | 188.1 | 52.5 |
| Kenny Gainwell | RB | 167.2 | 177.9 | 131.5 | 167.2 | 47.8 |

## Uncertainty

The separate player `proj_unc` field combines a position-specific historical residual floor with current source disagreement in quadrature. The residual floors are half of the robust 2018–2023 preseason error scale: QB 15.6%, RB 26.0%, WR 21.2%, and TE 22.9%. This prevents three similar projections from implying false certainty while increasing uncertainty when sources materially disagree. It deliberately does not replace `sd`, which remains the app's ceiling/upside input; treating forecast error as upside created a position bias in validation.

## Limitations

- ESPN is retained from the existing embedded custom projection because the original raw ESPN stat snapshot is not stored in the repository.
- CBS and FFToday do not project first downs, so the existing empirical reception/carry rates are applied. Passing first downs use 0.518 per completion from nflverse 2023–2024 player stats.
- FFToday does not expose projected fumbles in its public table; its source score therefore omits that small component. CBS and ESPN retain their fumble assumptions.
- K and D/ST remain on the existing projection because equivalent raw multi-source scoring was not available under this league's distance and defense-tier rules.
