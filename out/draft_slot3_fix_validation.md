# Slot 3 strategy-fix validation

Validated against the embedded engine in `out/draft_terminal.html` after adding recommendation eligibility and hard cap enforcement.

## Sample

- 5,000 complete randomized 12-team, 14-round drafts from slot 3.
- Opponents used the existing need-aware Auto Draft selector and Gaussian noise.
- My pick used the first eligible VONA recommendation every round.
- 167 additional no-noise controls verified deterministic behavior.

## Results

- **Legal final rosters: 5,000/5,000 (100%).**
- **Complete skill lineups by Round 8: 5,000/5,000 (100%).**
- **Three RB/WR through Round 4: 5,000/5,000 (100%).**
- **K/DST limited to Rounds 13–14: 5,000/5,000 (100%).**
- **Unique full rosters: 4,997/5,000 (99.9%).** Opponent randomness still creates materially different player paths.
- **Late TE2 value exception: 1,190/5,000 (23.8%).** No QB2 was selected because Josh Allen was already rostered in 99.0% of drafts and no backup cleared the higher QB hurdle.

Final construction:

| Construction | Drafts | Share |
| --- | ---: | ---: |
| QB1 RB4 WR6 TE1 K1 DST1 | 1,848 | 37.0% |
| QB1 RB5 WR5 TE1 K1 DST1 | 1,345 | 26.9% |
| QB1 RB6 WR4 TE1 K1 DST1 | 617 | 12.3% |
| QB1 RB5 WR4 TE2 K1 DST1 | 607 | 12.1% |
| QB1 RB4 WR5 TE2 K1 DST1 | 583 | 11.7% |

Round 8 construction:

| Construction | Drafts | Share |
| --- | ---: | ---: |
| QB1 RB4 WR2 TE1 | 2,065 | 41.3% |
| QB1 RB3 WR3 TE1 | 1,956 | 39.1% |
| QB1 RB2 WR4 TE1 | 979 | 19.6% |

The most stable slot-3 sequence was an RB/WR in Round 1, Josh Allen in Round 2 (99.0%), two RB/WR in Rounds 3–4, and a TE in Round 5. Later rounds responded to opponent removals while maintaining lineup and depth requirements.

Mean totals were 2,819.6 projected points, 3,070.7 ceiling-adjusted value, and 268.2 skill-player VOR. These are legal-roster totals; they should not be compared directly with the higher pre-fix totals, which came from illegal QB/TE-heavy rosters.

The TE2 exceptions were Brenton Strange 535 times, Juwan Johnson 376, and Kenyon Sadiq 279. Each occurred in Round 11 or 12 only when the TE's ceiling-adjusted points beat the best legal RB/WR by at least five. Opponents were allowed one late QB/TE luxury slot as well: 66.7% finished with TE2 and 33.1% with QB2, so those falls were contested rather than artificially reserved for slot 3.

## Enforced behavior

- League position caps are rejected when recording a pick for the team on the clock.
- Capped or strategically blocked players remain searchable, but rank below eligible recommendations.
- One QB and one TE are recommended by default. One late QB2 or TE2 may replace a depth pick, but never both.
- Three RB/WR are secured by Round 4.
- QB1, RB2, WR2, TE1, and an RB/WR FLEX are secured by Round 8.
- The first 12 rounds finish with ten RB/WR normally, or nine when a qualified QB2/TE2 exception is taken, always with at least four RB and four WR.
- K and D/ST are recommended in Rounds 13 and 14.
