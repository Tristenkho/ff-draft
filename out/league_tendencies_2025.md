# Lava Hound room tendencies — 2025 draft study

Source draft: ESPN recap, league 1238596447, 12 teams, 14 rounds, drafted
2025-08-31. Transcribed to `out/league_draft_2025.json`.

Market baseline: FantasyFootballCalculator half-PPR ADP, 12-team, 718 drafts,
window 2025-08-31 to 2025-09-01 — the same weekend as the draft. Cached at
`.cache/ff-backtest/ffc_half_ppr_adp_2025.json`.

**No season outcomes are used anywhere in this document.** Every number is
knowable before the draft starts. This is a study of process, not results.

## Outcome

Three exploitable abnormalities, in order of size:

1. K and D/ST go 30–70 picks ahead of market. Rounds 7–9 were 53% special teams.
2. QB1–12 go 9–33 picks early, then a 38-pick desert with no QB at all.
3. WR is priced at market. There is no WR edge here.

The room is not sharp. Eleven of twelve managers spent a round 7–9 pick on a
kicker or defense. Only Ray Rice Boxing Co waited on both.

## Positional timing vs market

Overall pick at which the Nth player of a position left the board. Premium is
`market − room`; positive means the room reached.

| N | QB room | QB mkt | prem | | K room | K mkt | prem |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 1 | 9 | 22 | +13 | | 90 | 120 | +30 |
| 3 | 25 | 52 | +27 | | 93 | 144 | +51 |
| 5 | 42 | 60 | +18 | | 97 | 156 | +59 |
| 7 | 44 | 75 | +31 | | 102 | 171 | +69 |
| 9 | 60 | 81 | +21 | | 106 | 173 | +67 |
| 10 | 74 | 83 | +9 | | 157 | 175 | +18 |
| 12 | 83 | 98 | +15 | | 161 | 180 | +19 |
| 13 | 121 | 99 | **−22** | | — | — | — |
| 15 | 124 | 103 | **−21** | | — | — | — |

RB ran 1–14 picks *later* than market and WR ran within ±5. Treat the RB
discount as unproven: this compares a 2025 draft against 2026 pool structure,
and the RB/WR talent distribution shifted between years. The QB and K/DST
signals are far too large to be that kind of artifact.

D/ST has no useful market comparison — only 8 defenses appear in the top 156
nationally, and this room took its first at pick 75.

## Rounds 7–9 collapse

| Round | K | D/ST | RB | WR |
| ---: | ---: | ---: | ---: | ---: |
| 7 | 0 | 5 | **0** | 2 |
| 8 | 4 | 3 | **0** | 4 |
| 9 | 5 | 2 | **0** | 4 |

Nineteen of 36 picks on special teams. **Zero running backs across 36
consecutive picks** (7.01–9.12), then five went in round 10.

By the end of round 9, ten of twelve teams had a defense and nine had a kicker.
It bought them nothing: the last three kickers off the board, in round 14, were
Butker, Cairo Santos, and **Ka'imi Fairbairn** — a perennial top-3 kicker who
sat until 14.05 while nine teams spent rounds 8–9 on the position.

D/ST is the softer half. Leftovers were Chiefs and Colts, so waiting there has a
real but small cost. Kicker is free.

## The QB desert

```
QB10 -> pick  74
QB11 -> pick  80
QB12 -> pick  83
                    <- 38 picks, zero QBs
QB13 -> pick 121
QB14 -> pick 122
QB15 -> pick 124
```

The draft-capital cliff is enormous. The value cliff is not:

| | QB10 | QB13 | QB15 |
| --- | ---: | ---: | ---: |
| 2026 projection | 319 | 312 | 304 |

Fifteen points from QB10 to QB15 is 0.9/week. The room has built a 38-pick
discontinuity around a nearly flat value curve. That is the arbitrage.

## Why QB is cheap here

League scoring compresses it deliberately: passing TD 4 (not 6), passing yards
0.04/yd, and passing first downs pay **0.1** against 0.5 receiving and 0.25
rushing. Receivers are paid five times more per first down than passers.

Starter-range spread on the 2026 pool:

| | points |
| --- | ---: |
| QB1 → QB12 | 80 |
| TE1 → TE12 | 80 |
| WR1 → WR24 | 125 |
| RB1 → RB24 | **167** |

Cost of moving down a position, in season points:

```
QB6  -> QB12    10.5   (0.6/wk)
RB18 -> RB30    53.9   (3.2/wk)
WR18 -> WR30    27.1   (1.6/wk)
```

## Waiver reality

Twenty-one QBs were drafted in 2025. Eight of twelve managers rostered a backup.
The free-agent pool opened at roughly QB22 — 279 projected, about **2.0/week**
below QB12.

Managers who carried only one QB: **Tristen**, Ray Rice, Capullo, Worthy.

This matters because `recommendationEligibility()` in the terminal currently
hard-blocks a second QB with the reason *"QB2 belongs on waivers."* That rule is
calibrated for a generic room. **In this league the waiver safety net it assumes
does not exist.**

## Draft grade — 2025, consensus only

Total surplus is `Σ (pick − ADP)`; positive means the manager consistently got
players later than consensus. Players outside the national top 156 are floored
at ADP 170. Skill-only surplus covers matched QB/RB/WR/TE picks and isolates
player evaluation from pick allocation.

| rk | manager | total | skill only (n) | reaches >15 | early K/DST | RB+WR R1–10 | QBs |
| ---: | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 1 | **Tristen's Talented** | **+75** | **+222 (12)** | 0 | 2 (R8, R9) | 6 | 1 |
| 2 | Kevin's Killers | +42 | +131 (11) | 1 | 2 (R7, R8) | 6 | 2 |
| 3 | Ray Rice Boxing Co | +38 | +102 (11) | 1 | **0** | 8 | 1 |
| 4 | Houston Hotdogs | −4 | +140 (11) | 0 | 2 (R7, R9) | 7 | 2 |
| 5 | Capullo | −7 | +49 (11) | 2 | 1 (R8) | 7 | 1 |
| 6 | Deshaun Watson Stans | −20 | +123 (11) | 1 | 2 (R7, R9) | 6 | 2 |
| 7 | You are not Worthy | −36 | +78 (11) | 0 | 1 (R9) | 8 | 1 |
| 8 | Matthew's Magnificent | −64 | +38 (11) | 1 | 1 (R8) | 7 | 2 |
| 9 | Kyle's Little Diddlers | −72 | +35 (11) | 1 | 2 (R7, R9) | 6 | 2 |
| 10 | BERDS FLY FOREVER | −94 | +80 (10) | 0 | 2 (R8, R9) | 6 | 2 |
| 11 | $weet $acks | −178 | +80 (10) | 1 | 2 (R7, R8) | 5 | 3 |
| 12 | Castelani's Cool | −196 | +61 (9) | 2 | 2 (R8, R9) | 5 | 2 |

Ranking is stable under a softer ADP-170 floor; re-running at 150 moves nobody
more than one place and leaves the top and bottom intact.

**Ray Rice Boxing Co is the only structurally sound drafter in the room** — the
sole manager to wait on both K and D/ST, and eight RB/WR through round 10. In
2026 he picks at slot 11. He is the main competitor for the rounds 7–9 window.

**$weet $acks and Castelani** are the softest. $weet drafted three QBs and
reached 118 picks on a tight end; Castelani reached on a TE, a kicker at market
minus 44, and a defense.

### Correction to an earlier read

Joe Burrow at 4.07 was **not** a reach. His national ADP was 28 and he went at
pick 43 — a 15-pick bargain. The positional-allocation argument against
spending pick 43 on a QB still holds, but the individually largest identifiable
errors in that draft were Seahawks D/ST at 8.07 (−79) and Jake Elliott at 9.06
(−68): **−147 surplus from two picks**, more than the total spread between 1st
and 8th place in the table above.

The 2025 QB injury was bad luck, not a bad pick. The lack of a backup was the
process error.

## Implications for 2026 (slot 3)

Picks: `3 · 22 · 27 · 46 · 51 · 70 · 75 · 94 · 99 · 118 · 123 · 142 · 147 · 166`

- **Never take K or D/ST before pick 147.** Largest single edge available.
- **Do not take a QB before pick 75.** The room's worst overpay band is QB4–9,
  picks 39–60 — rounds 4 and 5.
- **Pick 75 is the last top-12 QB.** Picks 70 and 75 are only five apart, so the
  round 6/7 turn can take a skill player and then a QB with little exposure.
- **Rounds 7–9 have a deeper effective pool than a sharp league**, because five
  to seven opponents are spending those picks on special teams. Picks 75, 94 and
  99 behave like round 5–6 picks elsewhere.
- **Survival numbers will be wrong in both directions in this window.** The
  terminal's timing model uses national ADP: it under-predicts K/D/ST and QB
  demand and over-predicts RB/WR demand between picks 70 and 100.

### Model changes this argues for

| constant | current | suggested | why |
| --- | --- | --- | --- |
| `STRATEGY.qbDeadline` | 10 | 7 | all 12 QBs gone by pick 83 |
| `STRATEGY.teDeadline` | 9 | 8 | 12 TEs gone by pick 100 |
| QB2 block | hard block | allow from R11 | waivers open at ~QB22 here |
| `mockNeedAdjustment` K/DST | `+90` before R13 | room-calibrated | opponents take them R7–9 |

These contradict values that came out of the historical backtest, which was fit
to a generic room. They should be validated against
`scripts/backtest_draft_policy.py` before going live, not hand-applied.

## Limits

- **One draft, 168 picks.** The K/DST and QB effects are large enough to act on.
  The RB effect is not.
- The 2026 draft order differs from 2025, so these are room-level tendencies,
  not seat-level ones. Do not map a manager's 2025 pick numbers onto 2026.
- Only 156 players carry national ADP, so 30 of 168 picks — mostly K, D/ST and
  late fliers — are floored rather than matched.
- Managers can change. One of them may have read the same articles this year.
