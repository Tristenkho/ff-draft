# Draft data hardening analysis

## Outcome

- Player pool expanded from 205 to 282 players.
- Position coverage: QB 30, RB 72, WR 90, TE 26, K 32, DST 32.
- ESPN custom projections, ESPN room ADP/rank, current teams, and status were retrieved 2026-09-02.
- FantasyPros half-PPR ECR was updated 2026-09-02 from 113 experts: 50 updated within one day, 91 within three days, and all 113 within seven days.
- All 32 NFL bye weeks are populated from the official schedule.
- D/ST is a streaming board: 55% Week 1, 25% Week 2, 10% Week 3, 7.5% season projection, and 2.5% positional ECR.
- K balances immediate and season-long value: 40% Week 1, 20% Week 2, 10% Week 3, 22.5% season projection, and 7.5% positional ECR.
- 77 net players were added. Skill players without a current projection: 1; each remains searchable and status-flagged.
- Sleeper corroborated availability for 250/250 non-D/ST players; 0 disagree with ESPN.

## Status coverage

- ACTIVE: 231
- COMMISSIONER_EXEMPT: 1
- INJURY_RESERVE: 4
- OUT: 1
- QUESTIONABLE: 45

## Availability cross-check

ESPN remains the status of record. Sleeper is a second independent read: where
the two disagree, neither is applied automatically — the conflict is listed here
so it can be resolved against the actual league transaction before the draft.

- No disagreements: ESPN and Sleeper agree on every matched player.

## Zero-projection skill players

- Jayden Higgins (HOU, INJURY_RESERVE, ESPN ADP 170.0)

## Model boundaries

- Opponent timing and survival are market-first: RB/WR/TE blend 80% current Fantasy Football Calculator 12-team half-PPR ADP with 20% ESPN-only room rank/ADP, QB blends 50/50, K/DST are unchanged. Its observed draft standard deviation drives availability uncertainty when matched, widened when ESPN and market disagree; FantasyPros ECR remains separate as the Model sanity check.
- FantasyPros supplies not only ECR but each player's expert mean, standard deviation, and range. Those disagreement fields are exported for judgment and are not silently converted into another ranking weight.
- Status is visible and zero-projection/long-term unavailable players are not automatically recommended, but every player remains clickable for accurate bookkeeping.
- Bye week is informational; elite players are not downgraded for sharing a bye.
