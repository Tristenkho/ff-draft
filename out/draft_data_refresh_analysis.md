# Draft data hardening analysis

## Outcome

- Player pool expanded from 205 to 280 players.
- Position coverage: QB 30, RB 70, WR 90, TE 26, K 32, DST 32.
- ESPN custom projections, ESPN room ADP/rank, current teams, and status were retrieved 2026-08-20.
- FantasyPros half-PPR ECR was updated 2026-08-20 from 101 experts: 38 updated within one day, 84 within three days, and all 101 within seven days.
- All 32 NFL bye weeks are populated from the official schedule.
- D/ST is a streaming board: 55% Week 1, 25% Week 2, 10% Week 3, 7.5% season projection, and 2.5% positional ECR.
- K balances immediate and season-long value: 40% Week 1, 20% Week 2, 10% Week 3, 22.5% season projection, and 7.5% positional ECR.
- 75 net players were added. Skill players without a current projection: 1; each remains searchable and status-flagged.

## Status coverage

- ACTIVE: 240
- DOUBTFUL: 2
- OUT: 3
- QUESTIONABLE: 35

## Zero-projection skill players

- Jayden Higgins (HOU, DOUBTFUL, ESPN ADP 161.1)

## Model boundaries

- Opponent timing and survival blend 60% ESPN-only room rank/ADP with 40% current Fantasy Football Calculator 12-team half-PPR ADP. Its observed draft standard deviation drives availability uncertainty when matched; FantasyPros ECR remains separate as the Model sanity check.
- FantasyPros supplies not only ECR but each player's expert mean, standard deviation, and range. Those disagreement fields are exported for judgment and are not silently converted into another ranking weight.
- Status is visible and zero-projection/long-term unavailable players are not automatically recommended, but every player remains clickable for accurate bookkeeping.
- Bye week is informational; elite players are not downgraded for sharing a bye.
