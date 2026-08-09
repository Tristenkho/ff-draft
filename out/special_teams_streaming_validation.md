# Special-teams streaming validation

## Decision

Keep kicker in Round 13 and D/ST in Round 14, but rank both from the current weekly custom-scoring forecasts. Treat D/ST as a Week 1 stream and reassess it every week. Hold a top kicker while role and offense remain strong; otherwise stream the position too.

## Inputs and model boundary

- ESPN authenticated custom-league projections for Weeks 1–3, refreshed 2026-08-08.
- Official 2026 opponents from ESPN's schedule feed; schedule cross-checked against the NFL Week 1 schedule.
- D/ST rank weights: Week 1 55%, Week 2 25%, Week 3 10%, season 7.5%, positional ECR 2.5%.
- K rank weights: Week 1 40%, Week 2 20%, Week 3 10%, season 22.5%, positional ECR 7.5%.
- Opponents retain the app's ESPN-room timing and controlled randomness. They do not use the user's streaming rank.

The weekly point forecasts and schedule are player-pool/current-data inputs. The rate at which options survive to slot 3 and which fallback is selected are outcomes of the opponent and recommendation logic.

## 5,000-draft live-policy validation

- Sample: 5,000 randomized 12-team, 14-round drafts from slot 3; 70,000 user recommendations.
- Legal recommendations: 70,000/70,000 (100%).
- Unique complete rosters: 4,853/5,000 (97.06%).
- K selected in Round 13: 5,000/5,000 (100%).
- D/ST selected in Round 14: 5,000/5,000 (100%).
- Most common full build: QB1/RB6/WR4/TE1/K1/DST1, 4,470/5,000 (89.40%).
- Next build: QB1/RB5/WR5/TE1/K1/DST1, 500/5,000 (10.00%).

### Round 13 kicker outcomes

| Player | Drafts | Rate |
| --- | ---: | ---: |
| Ka'imi Fairbairn | 3,821 | 76.42% |
| Jason Myers | 534 | 10.68% |
| Cameron Dicker | 385 | 7.70% |
| Harrison Mevis | 255 | 5.10% |
| Eddy Pineiro | 4 | 0.08% |
| Brandon Aubrey | 1 | 0.02% |

### Round 14 D/ST outcomes

| Defense | Drafts | Rate |
| --- | ---: | ---: |
| Chargers | 3,288 | 65.76% |
| Jaguars | 852 | 17.04% |
| Lions | 799 | 15.98% |
| Ravens | 46 | 0.92% |
| Eagles | 15 | 0.30% |

The board is not blindly choosing the preseason D/ST consensus. The most common available options project well immediately: Chargers 7.4 in Week 1 versus Arizona, Jaguars 8.2 versus Cleveland, and Lions 7.3 versus New Orleans.

## Round-order challenge

A separate 2,000-draft test reversed the order to D/ST in Round 13 and K in Round 14.

| Metric | K first (n=5,000) | D/ST first (n=2,000) | D/ST-first difference |
| --- | ---: | ---: | ---: |
| Combined Week 1 K + D/ST projection | 16.591 | 15.474 | -1.117 (95% simulation interval -1.134 to -1.100) |
| Combined Weeks 1–3 K + D/ST projection | 44.304 | 44.403 | +0.099 (95% simulation interval +0.053 to +0.144) |

The three-week gain from D/ST-first is statistically detectable inside this simulation but not practically meaningful. It is less than one tenth of a point across three weeks, while the Week 1 loss is more than one point. Because D/ST will be streamed again before Weeks 2–3, the Week 1 result is the more relevant decision metric. Retain K-first.

## Randomness and stability

The deterministic control took Fairbairn and Jacksonville in every control draft. Controlled opponent randomness produced six kicker outcomes, five D/ST outcomes, and 4,853 unique overall rosters in 5,000 drafts. The randomness therefore changes the available board meaningfully without breaking roster legality or the late-round policy.

The main conclusions are stable at these sample sizes: position legality, the K-first Week 1 advantage, and the dominant fallback groups. Very rare outcomes below 1% (Aubrey, Pineiro, Ravens, Eagles) should not be interpreted precisely; their existence matters more than their exact rate.

## Draft-day rules

1. Do not spend a pick before Round 13 on K or D/ST.
2. In Round 13, take the highest remaining kicker on the weekly board. Aubrey and Dicker are ideal holds; Fairbairn, Myers, and Mevis are the most realistic strong outcomes at slot 3.
3. In Round 14, take the highest remaining early-stream D/ST. The current realistic targets are the Chargers, Jaguars, and Lions, not necessarily the best season-long defense.
4. Before Week 1, refresh projections and confirm injuries, weather, and starting kickers.
5. Reassess D/ST every week. Reassess K if role, accuracy, or offensive environment deteriorates; never keep either merely because it was drafted.

Sources: [NFL 2026 Week 1 schedule](https://www.nfl.com/schedules/2026/REG1/) and ESPN authenticated league/schedule APIs used by the refresh script.
