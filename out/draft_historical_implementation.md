# Historical calibration implementation

## Final decision

- **Keep the live strategy and VONA parameters unchanged.** Finishing starters by Round 7 won the first sealed 2024 holdout, but failed the predeclared fresh-seed robustness gate: +0.63 percentage points in championship rate, 95% room-level CI -0.33 to +1.59, with a positive delta in only 4 of 7 seasons.
- Four RB/WR through Round 4 also won the recalibrated synthetic optimizer (+2.73 points, 95% CI +1.35 to +4.12), but failed historical season consistency: positive in only 4/7 seasons, lower playoff rates in five, and a -162-point 2018 result. It was rejected.
- **Replace model-heavy opponent Auto Draft with the historically calibrated selector.** Opponents now follow ADP plus 20% of the roster-need adjustment, with Gaussian randomness scaled to 65% of each player's observed ADP standard deviation. The fitted model weight is zero.
- Preserve the current Round-8 starter deadline, 0.40 ceiling weight, VONA formula, roster caps, RB/WR depth rules, and late QB2/TE2 exception.

## Samples

- Historical source seasons: 2018–2024.
- Policy screen: 12 policies × 30 rooms in each of five training seasons (1,800 rooms total).
- Validation: 300 paired rooms in 2023 for each finalist.
- Sealed holdout: 800 paired rooms in 2024 for each finalist.
- Fresh-seed robustness: 250 paired rooms per season across all seven seasons, or 1,750 rooms per policy.
- Post-change live-engine verification: 5,000 complete 12-team, 14-round drafts from slot 3.

## Opponent calibration

On unseen 2023–2024 market snapshots, the calibrated selector reduced pick-error RMSE from 3.100 ADP standard deviations for the former fixed-noise, model-heavy logic to 0.756. Mean pick bias improved from +3.80 picks to +2.78 picks.

The selected 0.65 randomness multiplier reproduced about 54% of observed player-level draft dispersion. A 0.90 multiplier improved dispersion to 72% but worsened unseen RMSE from 0.739 to 0.807 and mean bias from +2.79 to +2.99, so it was rejected. Operational diversity remains meaningful at the selected value: 2,510 unique rosters in 5,000 live-engine drafts.

## Live-engine verification

- Legal rosters: 5,000/5,000 (100%).
- Complete skill lineups through Round 8: 5,000/5,000 (100%).
- Three RB/WR through Round 4: 5,000/5,000 (100%).
- K and D/ST in Rounds 13–14: 5,000/5,000 (100%).
- Unique complete rosters: 2,510/5,000 (50.2%).
- Most common Round-8 builds: QB1 RB3 WR3 TE1 (47.6%), QB1 RB2 WR4 TE1 (31.4%), and QB1 RB4 WR2 TE1 (20.9%).
- Late value exceptions remained active: final builds included QB2 in 23.6% and TE2 in 32.2% of drafts; no roster took both.

The 2026 player pool still drives highly stable early behavior—Josh Allen was selected in Round 2 in 98.6% of rooms. That is a current projection/ADP result, not opponent-selector determinism.

## Data and limits

- Preseason market source: [Fantasy Football Calculator ADP API](https://fantasyfootballcalculator.com/adp), using half-PPR snapshots and only using PPR/standard snapshots to fill missing late-player tails.
- Weekly outcome source: [nflverse player stats](https://github.com/nflverse/nflverse-data/releases/tag/player_stats), scored with this league's custom rules including first downs.
- Player match rates were 96.8%–100% by season.
- nflverse's public player-stat release currently ends at 2024. No 2025 outcomes were fabricated.
- One untouched holdout NFL season is not seven independent holdouts. Room-level intervals measure draft-room uncertainty and are not presented as proof across future NFL seasons.
- Historical source projections were unavailable consistently across all years, so preseason values use only prior-season results plus contemporaneous ADP.
- K/DST use paired generic scoring, and historical waiver transactions and injury designations were not reconstructed.

Detailed results are in `out/draft_historical_backtest.md`, `out/draft_historical_robustness.md`, and `out/draft_historical_robustness_core_4.md`. Generated raw JSON remains uncommitted.
