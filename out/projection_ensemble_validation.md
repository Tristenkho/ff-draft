# Projection ensemble draft validation

## Test design

- Draft engine: the exact recommendation and opponent Auto Draft functions embedded in `out/draft_terminal.html`.
- League: 12 teams, slot 3, 14 rounds, current position caps and roster requirements.
- Randomized sample: 5,000 drafts before the projection update and 5,000 drafts after it.
- Control: deterministic opponent mode was also exercised by the harness.
- Sampling error: for a 50% event in 5,000 drafts, the approximate 95% margin is ±1.4 percentage points. Rare events below roughly 1% should not be treated as stable strategy signals.

## Data validation

- 171/181 skill players (94.5%) match ESPN, CBS, and FFToday.
- 180/181 (99.4%) have at least two current-season sources.
- Mean absolute change from the embedded ESPN projection is 7.1 fantasy points.
- ADP and ECR remain market/timing inputs only; neither is averaged into projected points.
- K and D/ST remain on their existing projections because equivalent raw custom-scoring inputs were unavailable.

## Draft behavior after the update

### Frequent early selections

| Round | Most common choices |
| --- | --- |
| 1 | Jahmyr Gibbs 43.9%, Bijan Robinson 38.2%, Puka Nacua 17.9% |
| 2 | Trey McBride 72.5%, Josh Allen 14.3%, Derrick Henry 13.1% |
| 3 | Josh Jacobs 50.5%, Rashee Rice 26.4%, Josh Allen 6.3%, Trey McBride 6.0% |
| 4 | D'Andre Swift 61.2%, Bucky Irving 21.3%, Garrett Wilson 9.5% |
| 5 | Jayden Daniels 48.0%, D'Andre Swift 26.2%, Tyler Warren 11.3%, Colston Loveland 8.3% |
| 6 | Alec Pierce 70.7%, Jaxson Dart 10.8%, Jalen Hurts 9.5% |
| 7 | Courtland Sutton 47.2%, Tony Pollard 28.8%, Alec Pierce 22.0% |
| 8 | Michael Pittman Jr. 85.7%, Courtland Sutton 7.2%, Jakobi Meyers 4.2% |

### Roster construction

- Through round 8, QB1/RB3/WR3/TE1 is the dominant build at 77.8%; QB1/RB2/WR4/TE1 is 11.7%, and QB1/RB4/WR2/TE1 is 10.6%.
- At round 14, QB1/RB4/WR6/TE1/K1/DST1 occurs 77.8% and QB1/RB5/WR5/TE1/K1/DST1 occurs 19.0%.
- Every simulated roster was legal and complete. K and D/ST were selected in rounds 13 and 14 in 100% of drafts.
- Second QB fell from 17.6% in the prior model to 1.4%; second TE fell from 32.3% to 0.2%. Those remain legal but are now used only when the board produces a sufficiently unusual value.

### Diversity and randomness

- The randomized run produced 2,756 distinct rosters in 5,000 drafts (55.1%).
- The deterministic control produces one repeated roster, so opponent randomness is materially changing availability and final teams.
- No single first-three combination exceeds 17.8%. The top four combinations account for 52.0%, which is concentrated enough to be actionable but not a locked script.

## Guardrail discovered during validation

An initial test incorrectly placed cross-source forecast uncertainty into the existing `sd` field used for ceiling-adjusted value. That conflated “we are less sure about the forecast” with “this player has more winning upside,” creating a strong positional bias. The implementation now keeps:

- `sd` as the existing ceiling/upside input used by `value = projection + lambda × sd`;
- `proj_unc` as a separate forecast-confidence field; and
- `proj_low`/`proj_high` as the visible source range.

The corrected model restores a balanced round-8 roster in 89.5% of drafts (three or four WR and two or three RB) while retaining legal late-value QB/TE paths.

## Interpretation

The updated projected-point totals cannot be compared directly with the previous totals because the underlying scoring estimates changed. The simulation validates internal behavior, legality, sensitivity to availability, and absence of obvious strategy pathologies; it does not prove that a 2026 forecast will beat the market before games are played. The ensemble should reduce reliance on any one provider and make missing/outlier projections less damaging, while ADP, news, roles, and injuries still need refreshes near draft day.
