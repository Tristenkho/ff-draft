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
rescoring all 212 CBS/FFToday stat lines player-by-player with each player's own
`fd_rec_rate`:

```
WR: mean 0.804  median 0.799  range 0.73-0.87  (n=87)
TE: mean 0.767  median 0.767  range 0.72-0.81  (n=25)
RB: mean 0.664  median 0.664  range 0.63-0.71  (n=44)
```

So the league sits about four-fifths of the way from half-PPR to full-PPR for
wide receivers, three-quarters for tight ends, and two-thirds for running backs.

First downs are not a rounding error. Across the pool they contribute:

| Pos | First-down points | Share of total projection |
|-----|-------------------|---------------------------|
| QB  | +24.2             | 8.0%                      |
| RB  | +15.5             | 8.9%                      |
| WR  | +18.9             | 11.6%                     |
| TE  | +17.2             | 11.1%                     |

RB first-down points come from two streams (0.25/rush FD at 0.224 per carry, plus
0.5/rec FD), which is why the RB share stays respectable even though RB receptions
convert worst. QB first-down points are almost entirely `PFD 0.1` per passing
first down and are large in absolute terms but the smallest share.

## The model already handles this — do not adjust for it twice

All three projection sources are league-scored before they are blended:

- **ESPN** — `scripts/refresh_draft_data.py:170` reads `appliedTotal`, which is
  ESPN's projection under this league's configured scoring settings.
- **CBS and FFToday** — raw stat lines rescored locally by
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
| WR  | **+1.2** spots     |
| TE  | **+0.8** spots     |
| RB  | **-2.1** spots     |

Largest individual movers:

| Player | Pos | half-PPR → league | ADP | Notes |
|--------|-----|-------------------|-----|-------|
| Jaylen Waddle | WR | #58 → #52 (+6) | 60.2 | 73 rec @ 0.83/rec |
| Trey McBride | TE | #34 → #29 (+5) | 20.0 | 110 rec, TE volume king |
| Josh Downs | WR | #101 → #96 (+5) | 122.9 | 68 rec @ 0.78 |
| A.J. Brown | WR | #28 → #24 (+4) | 27.2 | 88 rec @ 0.83 |
| Rashee Rice | WR | #20 → #16 (+4) | 22.3 | 100 rec @ 0.79 |
| Jacory Croskey-Merritt | RB | #93 → #101 (-8) | 136.5 | 10 rec, pure runner |
| Tony Pollard | RB | #53 → #59 (-6) | 101.8 | 33 rec @ 0.64 |
| Jeremiyah Love | RB | #21 → #26 (-5) | 19.2 | 50 rec but low conversion |

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

Numbers here come from rescoring the cached CBS/FFToday stat lines two ways
(with and without first-down bonuses) and re-ranking. Requires
`.cache/projection-ensemble-2026/` to be populated:

```
python3 scripts/analyze_effective_ppr.py
```
