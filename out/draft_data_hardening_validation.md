# Draft-day data hardening validation

## Final exact-engine sample

- 5,000 randomized 12-team, 14-round drafts from slot 3.
- 70,000/70,000 user selections matched the assistant's top legal recommendation.
- 4,930 distinct final rosters (98.6% of simulations).
- Deterministic control produced one roster, confirming that opponent randomness materially changes the draft.
- K was selected in round 13 and D/ST in round 14 in 100% of drafts.
- No incomplete rosters, position-cap violations, or unavailable-player recommendations occurred.

For a 50% event in 5,000 drafts, the approximate 95% sampling margin is ±1.4 percentage points. Events below roughly 1% are not treated as stable strategy signals.

## Early-round decisions

| Round | Most common choices |
| --- | --- |
| 1 | Jahmyr Gibbs 41.7%, Bijan Robinson 36.9%, Puka Nacua 21.4% |
| 2 | Brock Bowers 49.0%, Josh Allen 38.4%, Trey McBride 5.9%, Derrick Henry 3.3% |
| 3 | Josh Jacobs 48.0%, Breece Hall 27.1%, Kenneth Walker III 11.5%, Chase Brown 10.1% |
| 4 | Bucky Irving 56.8%, Travis Etienne Jr. 22.0%, D'Andre Swift 17.9% |
| 5 | D'Andre Swift 63.9%, Drake Maye 13.3%, Jameson Williams 10.5% |
| 6 | Mike Evans 34.6%, Harold Fannin Jr. 21.1%, Tony Pollard 17.8%, Jaylen Warren 14.6% |

No first-three combination exceeded 9.4%. The four most common combinations total 33.5%, so the assistant has recognizable decision rules without a locked script.

## Position construction

- Through round 8: QB1/RB4/WR2/TE1 in 98.2%; QB1/RB3/WR3/TE1 in 1.8%.
- Final: QB1/RB6/WR4/TE1/K1/DST1 in 89.9%; QB1/RB5/WR5/TE1/K1/DST1 in 9.6%.
- The RB6/WR4 lean is caused by the current player pool and room prices: rounds 3–5 repeatedly expose RB values, while usable WR depth reaches rounds 6–12. It still preserves two WR starters and two WR bench options.
- QB2 and TE2 remain legal value exceptions but occur in less than 1%, which is not statistically stable.

## Opponent-model correction

The first hardening simulation incorrectly let Brock Bowers reach pick 2.10 in 95.0% of drafts. The cause was double-counting roster construction: ESPN room ADP/rank already reflects the one-QB/one-TE format, while the old opponent logic added another early QB/TE and RB/WR positional adjustment.

Early-round positional adjustments are now neutral through round 4. Later need adjustments remain active for filling starters and avoiding redundant QB/TE selections. In the final run, Bowers reaches the round-2 pick 49.0%, Josh Allen becomes the recommendation 38.4%, and the most common first-three combination falls to 9.4%.

## Data completeness

- 280 total players: QB 30, RB 70, WR 90, TE 26, K 32, D/ST 32.
- All 280 players have official 2026 bye weeks.
- ESPN status is present for every player: 262 active, 12 questionable, 5 out, and 1 injured reserve at refresh time.
- Ricky Pearsall is the only zero-projection skill player. He remains searchable for bookkeeping, displays his IR status and ESPN ADP, and is excluded from automatic recommendations.
- K and D/ST ordering blends 75% league-scored projection rank with 25% current positional consensus rank.

## Interpretation

This validates legality, data completeness, market sensitivity, and the absence of obvious deterministic opponent-selection defects. It cannot prove real 2026 outcomes before games are played. A final refresh should still be run within 24 hours of the real draft because injuries, depth charts, signings, projections, and ESPN room prices can move quickly.
