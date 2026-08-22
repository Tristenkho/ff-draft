# ADR 0001: Separate ECR quality evaluation from draft timing

## Status

Accepted

## Context

The draft assistant uses several external signals that answer different questions. FantasyPros ECR is an expert consensus about player quality. Market ADP is evidence about when players are selected in comparable drafts. ESPN room data is evidence about this league's behavior, but the 2025 sample is small and position-specific.

Treating those signals as one ranking caused a category error: a player could appear available later because ESPN's platform ADP was late, even when market ADP and ECR indicated that the player would be drafted sooner.

## Decision

Keep two measurements separate:

- ECR rank gap measures disagreement between the Model's player evaluation and expert consensus.
- Draft-timing deviation measures when a player is selected relative to market ADP, ECR, or the modeled room.

The Model's objective is expected roster value plus accurate room-behavior forecasting, not minimizing its distance from ECR. ECR remains an independent audit and review signal. Market ADP is the baseline for availability timing, with room behavior used as a position-aware adjustment. Large source disagreements widen availability uncertainty.

## Alternatives rejected

- Optimizing directly for smaller Model–ECR gaps.
- Using ECR as a substitute for draft timing.
- Applying an RB-only correction while leaving WR and TE timing biases untreated.

## Consequences

Recommendations can intentionally differ from ECR when projections, roster value, or room timing justify it. Model–ECR rank gaps, draft-timing calibration, and simulated roster value must be evaluated separately. Updating ADP timing does not claim that the underlying player rankings became more accurate relative to ECR.

Timing data may be refreshed frequently, but timing weights change only after historical backtesting. When Model, ECR, and timing sources conflict during the draft, the conflict is shown for human judgment rather than triggering an automatic override.
