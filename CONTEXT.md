# Fantasy Draft Terminal Context

This context covers the single-page draft assistant and the pre-draft learning workflow used on a phone or desktop.

## Draft navigation

**Snake grid**:
The full 12-team-by-14-round draft board, with team slots as columns and rounds as rows. The user's draft slot is highlighted as one vertical column.
_Avoid_: snake cards when referring to the full grid

**Mobile prep view**:
The phone experience used before draft day to study approximate rankings and rehearse room behavior. It is not the primary live-draft interface.
_Avoid_: mobile draft mode

**User slot column**:
The single team column corresponding to the user's draft position, currently slot 3, highlighted throughout the snake grid.
_Avoid_: user's picks row

## Draft evaluation

**ECR rank gap**:
The difference between FantasyPros Expert Consensus Rank and the terminal's Model rank for the same skill-player pool. It measures disagreement about player quality or expected value; it does not measure when the room will draft the player.
_Avoid_: draft-timing deviation

**Draft-timing deviation**:
The difference between an actual or modeled draft pick and a reference timing source such as market ADP or ECR. Negative means the player was drafted earlier than the reference; positive means later.
_Avoid_: ECR rank gap

**Market ADP**:
Aggregated draft behavior from the external 12-team half-PPR market. It is evidence about when players are selected, not a projection of player quality.

**ECR audit signal**:
Expert consensus used to challenge or contextualize the Model's player evaluation. It is kept separate from draft-behavior timing unless historical testing proves that combining them improves decisions.

**Availability estimate**:
The estimated probability that a player remains available at the user's next pick. It is a forecast of room behavior and timing uncertainty, not a statement about the player's quality.

**Model objective**:
Maximize expected roster value while accurately forecasting this league's draft behavior. Resembling ECR is a diagnostic outcome, not the objective by itself.

**Architecture Decision Record (ADR)**:
A short decision note that records an important modeling choice, the reasoning behind it, alternatives considered, and consequences for future changes.

**Timing calibration**:
The validated process for choosing how much weight each timing source receives. Refreshing current ADP does not by itself justify changing calibration weights.

**Source conflict**:
A disagreement among Model evaluation, ECR consensus, and draft-timing signals. It is surfaced for judgment using tier scarcity, availability uncertainty, and roster needs rather than resolved by an automatic source override.

## App identity

**Home-screen icon**:
The static icon shown when the GitHub Pages URL is saved to the phone home screen. It should use a terminal-prompt and football-seam visual rather than a single letter.
_Avoid_: favicon when discussing the home-screen icon
