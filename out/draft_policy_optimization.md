# Draft policy optimizer status — August 12, 2026

## Outcome

**No synthetic-optimizer result is current enough to justify a live policy
change. Retain the baseline configuration and use the historical weekly tests as
the strategy gate.**

The prior report in this path was generated August 8 by an older harness and has
been retired. It contained policies and keys that no longer exist in the live
engine, pooled correlated season outcomes too aggressively, and did not adjust
for screening multiple challengers. Its apparent winner, four RB/WR through
Round 4, subsequently failed the seven-season historical robustness check.

## Current harness

`scripts/optimize_draft_policy.js` now:

- fingerprints the exact embedded HTML engine;
- requires every policy to match the live strategy schema exactly;
- screens all policies in Stage 1, then tests the baseline and top three in new
  seeded rooms;
- computes finalist intervals from the confirmation sample only;
- clusters outcomes by draft room after averaging correlated seasons;
- uses 98.33% Bonferroni-adjusted intervals for three baseline comparisons;
- throws if any tested roster is illegal.

The full current run was intentionally not published after the ranking engine
changed again on August 12 to remove ECR from timing/VONA and normalize ECR to
the skill-player pool. A completed result from the preceding engine would have
been stale on arrival.

A 3-room/3-room execution smoke test of the final engine fingerprint
`19c1bec74028077f1e85b0dee278ebbc9fccafea1af4926d84bdebc219d8328d`
completed successfully and all 12 rosters in every room passed the legal
assertion. Its rates are deliberately omitted because that sample is far too
small for inference.

## Important limits

- The two stages use disjoint samples from one synthetic data-generating model;
  they are not independent real-world evidence.
- Policies with different draft paths can consume randomized opponent choices in
  different order, so common seeds do not guarantee identical opponent boards
  after the paths diverge.
- The evaluator supplies free replacement-level points when a starter is absent.
  This makes it weak evidence for QB2, TE2, bench depth, kicker, and D/ST policy.
- K/DST in Rounds 13–14 is supported primarily by the observed 2025 league room,
  not by a simulator that assumes the same rule.
- The historical weekly harness is not an exact replay of every revised live
  decision component, but it uses actual out-of-season weekly outcomes and is
  the more important gate for strategy changes.

## Decision

Keep the live strategy unchanged:

```json
{"lambda":0.4,"coreEarly":3,"coreDeadline":4,"wrDeadline":5,"coreStarterDeadline":8,"teDeadline":9,"qbDeadline":10,"coreTotal":10,"minCoreEach":4}
```

Do not use the retired August 8 synthetic rates as evidence. Before a future
policy change, complete a fresh full run from the final engine, then require the
candidate to pass multi-season historical robustness with a predeclared metric.
