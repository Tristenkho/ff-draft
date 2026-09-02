# This league is not half-PPR. It is ~0.80 PPR for WR.

The scoring block in `CLAUDE.md` reads `REC 0.5`, which looks like a standard
half-PPR league. It is not. The same block also carries `REFD 0.5` — half a point
per *receiving first down* — and receptions convert to first downs at high,
position-dependent rates. The two settings compound into an effective per-reception
value well above 0.5, and the gap between positions is large enough to matter when
reading any external ranking.

## The arithmetic

Effective points per reception = `REC + REFD x P(first down | reception)`.

Using the empirical rates already computed in `out/first_down_rates.json`
(nflverse play-by-play, 2023-25 regular season):

| Pos | fd/reception | Effective pts/reception | vs. nominal 0.5 |
|-----|--------------|-------------------------|-----------------|
| WR  | 0.597        | **0.799**               | +60%            |
| TE  | 0.511        | **0.756**               | +51%            |
| RB  | 0.325        | **0.663**               | +33%            |

Verified against the actual 2026 player pool rather than the position averages —
rescoring all 217 CBS/FFToday/Sleeper stat lines player-by-player with each
player's own `fd_rec_rate`:

```
WR: mean 0.803  median 0.798  range 0.73-0.87  (n=89)
TE: mean 0.766  median 0.766  range 0.72-0.81  (n=26)
RB: mean 0.663  median 0.663  range 0.63-0.71  (n=44)
```

So the league sits about four-fifths of the way from half-PPR to full-PPR for
wide receivers, three-quarters for tight ends, and two-thirds for running backs.

First downs are not a rounding error. Across the pool they contribute:

| Pos | First-down points | Share of total projection |
|-----|-------------------|---------------------------|
| QB  | +23.8             | 8.0%                      |
| RB  | +14.9             | 9.0%                      |
| WR  | +18.6             | 11.8%                     |
| TE  | +17.3             | 11.5%                     |

RB first-down points come from two streams (0.25/rush FD at 0.224 per carry, plus
0.5/rec FD), which is why the RB share stays respectable even though RB receptions
convert worst. QB first-down points are almost entirely `PFD 0.1` per passing
first down and are large in absolute terms but the smallest share.

## The model already handles this — do not adjust for it twice

All four projection sources are league-scored before they are blended:

- **ESPN** — `scripts/refresh_draft_data.py:170` reads `appliedTotal`, which is
  ESPN's projection under this league's configured scoring settings.
- **CBS, FFToday and Sleeper** — raw stat lines rescored locally by
  `custom_score()` in `scripts/update_projection_ensemble.py:195`, which applies
  `REFD`, `RFD`, and `PFD` using each player's own first-down rates where
  nflverse has a match and position defaults otherwise.

`proj` is the median of those three. The first-down bonuses are already inside
every number the terminal shows. **Do not mentally mark receiving backs down or
volume receivers up at the draft — the board has already done it.** Doing it again
by hand is double-counting.

## Where the real edge is: the market prices half-PPR

The projections are league-scored. The *market comparisons* are not:

- `scripts/refresh_draft_data.py:32` — FantasyFootballCalculator ADP, `half-ppr`
- `scripts/refresh_draft_data.py:31` — FantasyPros ECR, `half-point-ppr-cheatsheets`

So `adp`, `market_adp`, `ecr`, and `room_rank` all describe a half-PPR world,
while `proj` describes this league. Any player whose value is concentrated in
high-conversion receptions is systematically underpriced by the yardstick, and
low-catch early-down backs are overpriced.

Re-ranking the flex pool (RB/WR/TE, proj > 80) under league scoring versus plain
half-PPR gives the average drift:

| Pos | Mean rank movement |
|-----|--------------------|
| WR  | **+1.3** spots     |
| TE  | **+1.3** spots     |
| RB  | **-2.6** spots     |

Largest individual movers:

| Player | Pos | half-PPR → league | ADP | Notes |
|--------|-----|-------------------|-----|-------|
| KC Concepcion | WR | #108 → #102 (+6) | 146.8 | 58 rec @ 0.80/rec |
| Romeo Doubs | WR | #95 → #89 (+6) | 147.7 | 58 rec @ 0.84 |
| Stefon Diggs | WR | #97 → #92 (+5) | 102.9 | 64 rec @ 0.79 |
| Michael Wilson | WR | #85 → #80 (+5) | 102.5 | 66 rec @ 0.82 |
| Rashee Rice | WR | #34 → #30 (+4) | 29.1 | 93 rec @ 0.79 |
| Trey McBride | TE | #32 → #28 (+4) | 22.6 | 104 rec, TE volume king |
| Brock Bowers | TE | #31 → #27 (+4) | 24.0 | 102 rec @ 0.77 |
| Rachaad White | RB | #84 → #94 (-10) | 125.6 | 34 rec @ 0.66 |
| Jonathon Brooks | RB | #87 → #95 (-8) | 105.3 | 32 rec @ 0.67 |
| Kyle Monangai | RB | #79 → #87 (-8) | 124.0 | 23 rec @ 0.67 |
| Bhayshul Tuten | RB | #35 → #42 (-7) | 61.9 | 32 rec @ 0.66 |

## Honest magnitude

This is a real, verified property of the league, but it is a **tilt, not a
reshuffle**. The typical player moves one to three spots; the extremes move five
to eight. It will not on its own justify taking a receiver over a back, and it is
smaller than the uncertainty in the projections it adjusts (`proj_unc` runs 60-95
points for early-round players — several times the entire first-down effect).

Treat it as a tiebreaker and a framing correction, not a strategy:

1. **Say "0.8 PPR", not "half PPR"**, when reasoning out loud or handing context to
   an outside tool. The wrong label invites the wrong intuitions.
2. **Discount external half-PPR rankings** slightly toward receptions — but only
   when reading raw ADP/ECR, never when reading the terminal's own `proj`/`gain`.
3. **Break WR-vs-RB flex ties toward the pass-catcher**, and RB-vs-RB ties toward
   the receiving back, when everything else is level.
4. Where per-player nflverse data is thin (`fd_rate_n` small — rookies especially),
   the model falls back to position defaults, so a rookie back's first-down rate is
   an assumption, not a measurement. Croskey-Merritt's -8 is the least trustworthy
   number in the table above.

## Reproducing

Numbers here come from rescoring the cached CBS/FFToday/Sleeper stat lines two ways
(with and without first-down bonuses) and re-ranking. Requires
`.cache/projection-ensemble-2026/` to be populated:

```
python3 scripts/analyze_effective_ppr.py
```
