# Draft ranking refresh — August 29, 2026

## Decision summary

The draft terminal is refreshed through August 29. The data move is large enough
to change the static 1.03 recommendation: assuming Gibbs and Bijan are gone,
Puka Nacua is now the only player in wait band A. On August 20, Puka and Ja'Marr
Chase shared band A and the consensus-first tiebreak put Chase first.

This is a model result, not a final injury ruling. Puka remained out of team work
on August 24 with psoas soreness, and possible league discipline was still an
open question on August 28. Chase hyperextended his left knee on August 25 but
said he was fine; Cincinnati kept him out afterward. The draft-day judgment
layer should verify both players again before treating the static ordering as
the final pick.

## Source refresh

| Input | Prior snapshot | Current snapshot |
| --- | --- | --- |
| ESPN league projections, room ADP/rank, status | Aug 20 | Aug 29 |
| CBS raw-stat projections, rescored locally | Aug 20 | Aug 29 |
| FFToday raw-stat projections, rescored locally | Aug 20 | Aug 29 |
| FantasyPros Latest half-PPR ECR | Aug 20, 101 experts | Aug 29, 107 experts |
| Fantasy Football Calculator 12-team half-PPR ADP | Aug 20 | Aug 29, 3,302 drafts |
| ESPN Week 1–3 K/DST projections and opponents | Aug 20 | Aug 29 |

The 280-player pool retained the same position quotas. Six players entered and
six left because the ESPN player pool, teams, and depth charts changed. The
most relevant new skill players are Najee Harris, Jaydon Blue, George Holani,
Darnell Mooney, and DeMario Douglas. Jayden Higgins moved from doubtful to
injured reserve and is automatically excluded from recommendations.

## What moved

Largest projection moves among players likely to matter in this draft:

| Player | Aug 20 | Aug 29 | Change | Current ECR |
| --- | ---: | ---: | ---: | ---: |
| Bo Nix | 299.4 | 321.0 | +21.6 | 99 |
| George Kittle | 151.4 | 172.0 | +20.6 | 93 |
| Christian McCaffrey | 319.4 | 338.0 | +18.6 | 7 |
| Jaxon Smith-Njigba | 286.8 | 305.3 | +18.5 | 5 |
| Jonathan Taylor | 304.7 | 322.3 | +17.6 | 8 |
| De'Von Achane | 274.9 | 291.9 | +17.0 | 16 |
| Puka Nacua | 317.9 | 334.1 | +16.2 | 4 |
| Derrick Henry | 274.7 | 289.4 | +14.7 | 21 |
| Omarion Hampton | 247.4 | 261.9 | +14.5 | 20 |
| Bucky Irving | 229.9 | 216.6 | -13.3 | 54 |
| Ladd McConkey | 193.3 | 205.3 | +12.0 | 35 |
| Terry McLaurin | 192.2 | 204.2 | +12.0 | 46 |

The notable market/ECR fall is Ashton Jeanty: ECR 12 to 22, market ADP 15.4 to
23.8, projection 261.5 to 254.6, and status active to questionable. Conversely,
Chase Brown moved ECR 14 to 12 and ESPN ADP 23.8 to 20.2.

The ESPN status feed now labels 44 players questionable, up from 35. The most
important new flags include Chase, Kenneth Walker, Zay Flowers, TreVeyon
Henderson, Brian Thomas, and Ashton Jeanty. DeVonta Smith, Xavier Worthy,
Quinshon Judkins, Carnell Tate, and Parker Washington returned to active.

## 1.03 board change

Assumption: Gibbs and Bijan are picks 1–2. Wait cost is the ceiling-adjusted
value lost by waiting to pick 22.

| Current order | Player | Wait band | Wait cost | Model rank | Current ECR |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | Puka Nacua | A | 108.6 | 3 | 4 |
| 2 | Ja'Marr Chase | B | 87.2 | 5 | 3 |
| 3 | Jaxon Smith-Njigba | B | 77.2 | 7 | 5 |
| 4 | Christian McCaffrey | B | 87.4 | 4 | 7 |
| 5 | Amon-Ra St. Brown | C | 68.6 | 8 | 6 |
| 6 | Jonathan Taylor | C | 70.1 | 6 | 8 |
| 7 | De'Von Achane | D | 36.5 | 10 | 16 |
| 8 | Derrick Henry | D | 33.7 | 12 | 21 |

Puka's projection-source median is now 334.1 versus Chase's 314.5. All three
Puka inputs remain high (ESPN 334.1, CBS 350.3, FFToday 317.9); this is not one
outlier source pulling up an average. Chase is tighter but lower (314.5, 317.5,
307.4). The resulting 19.6-point point-estimate gap is large enough to split the
wait band. Current ECR still prefers Chase 3 to 4.

## Where the model differs from ECR

The comparison below uses ECR re-ranked over the same 211 draftable QB/RB/WR/TE
players as the Model. Positive gaps mean the Model is higher. Model rank is a
custom-scoring quality audit; the live Pick Board still applies wait cost,
availability, and roster legality, so it should not be read as an overall-ADP
draft list.

### Top of the board

| Player | Model | Skill-player ECR | Gap |
| --- | ---: | ---: | ---: |
| Puka Nacua | 3 | 4 | +1 |
| Christian McCaffrey | 4 | 7 | +3 |
| Ja'Marr Chase | 5 | 3 | -2 |
| Jonathan Taylor | 6 | 8 | +2 |
| Jaxon Smith-Njigba | 7 | 5 | -2 |
| Amon-Ra St. Brown | 8 | 6 | -2 |
| De'Von Achane | 10 | 16 | +6 |
| Derrick Henry | 12 | 21 | +9 |
| Josh Allen | 14 | 27 | +13 |
| Jeremiyah Love | 24 | 42 | +18 |
| Josh Jacobs | 29 | 43 | +14 |

### ECR-favored actionable players

| Player | Model | Skill-player ECR | Gap |
| --- | ---: | ---: | ---: |
| A.J. Brown | 26 | 13 | -13 |
| Nico Collins | 28 | 17 | -11 |
| George Pickens | 34 | 23 | -11 |
| Justin Jefferson | 20 | 11 | -9 |
| CeeDee Lamb | 16 | 9 | -7 |
| Jaylen Waddle | 58 | 37 | -21 |
| Christian Watson | 81 | 58 | -23 |

Most Model-favored outliers are quarterbacks because the league awards passing
first downs and the three custom-scored projections produce large season totals.
Replacement value and VONA still prevent that from becoming an instruction to
draft quarterbacks at their Model rank. Most ECR-favored outliers are wide
receivers whose three-source custom-scoring point forecasts are lower than the
half-PPR expert panel implies. Those are the best close-call review targets: the
disagreement may reflect role, health, or games-played assumptions not expressed
consistently in the projection feeds.

## Ranking improvements worth testing

No ranking weight changed in this refresh. The existing synthetic optimizer did
not establish a reliable improvement for a more Model-heavy tiebreak, a 50% ECR
blend, or a tighter 15-rank review gate, so changing a live constant one week
before the draft would be overfitting.

The next improvements with the best chance of adding independent signal are:

1. **Availability-adjusted projection audit.** Separate per-game production from
   games-played assumptions, then surface disagreement about missed games. This
   directly targets the current Puka, Chase, McCaffrey, Kittle, Walker, and Jeanty
   decisions without burying volatile news in a permanent player penalty.
2. **Player-specific weekly ceiling in shadow mode.** Replace the generic
   position-rate ceiling proxy with a regressed player-level weekly-volatility
   estimate, while keeping forecast error separate from upside. Backtest it on
   past single-week playoff outcomes before it affects VONA.
3. **Add 2025 as a new out-of-sample policy season.** The historical policy test
   currently seals 2024 as its holdout even though 2025 nflverse weekly data now
   exists. Use 2025 once to validate the ECR weight, same-band tiebreak, review
   threshold, and ceiling weight; do not retune repeatedly on that season.
4. **Role/usage disagreement flags.** Compare projected targets, carries, and
   touchdowns across CBS and FFToday before they are collapsed to points. A
   large role disagreement is more actionable than an unexplained point range.
5. **Final cadence.** Refresh daily this week, then once after final practice
   reports and again roughly 60–90 minutes before the draft. Market timing and
   injury availability are moving much faster than the underlying strategy.

## Current-news checks used for interpretation

- [Rams: Puka remained out of practice with psoas soreness on Aug. 24](https://www.therams.com/news/injury-updates-ol-justin-dedich-hand-and-te-davis-allen-quad-return-to-practice-wr-puka-nacua-psoas-and-de-myles-garrett-knee-still-non-participants)
- [NBC Sports: McVay said the Aug. 27 Atwell trade was unrelated to a possible Puka suspension](https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/sean-mcvay-tutu-atwell-trade-had-nothing-to-do-with-possible-puka-nacua-suspension)
- [Bengals: Chase landed awkwardly on his left knee on Aug. 25](https://www.bengals.com/news/training-camp-report-jamarr-chase-andrei-iosivas-dohnte-meyers-bengals-wrs-depth-on-display)
- [NBC Sports: Chase called the injury a minor hyperextension and said he was fine](https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/jamarr-chase-says-hes-fine-after-hyperextending-his-knee)
- [49ers: McCaffrey returned to team drills Aug. 23 and described the absence as planned workload management](https://www.49ers.com/news/day-16-of-2026-training-camp-george-kittle-s-remarkable-return)
- [NFL: Kittle was activated from PUP Aug. 23 but was not yet guaranteed for Week 1](https://www.nfl.com/news/niners-activate-te-george-kittle-off-physically-unable-to-perform-list)
