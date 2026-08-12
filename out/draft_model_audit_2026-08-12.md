# Draft model audit — August 12, 2026

## Bottom line

The live Draft tab is a **Decision board**, not a pure VONA sort and not a pure
Model sort. Its order is:

1. legal roster/build options;
2. uncertainty-aware VONA tier;
3. Model decision rank within that tier (including the conservative REVIEW gate
   when Model and ECR differ by 25+ skill-player ranks);
4. exact raw VONA as the final tiebreak.

This is the intended division of labor for this tool. VONA answers the strategic
question — *what value is most likely to disappear before pick 22?* — while the
Model helps choose among differences too small to trust. Points, ECR, ADP, and
Model tabs are read-only audits. The copied-state review remains the current-news
judgment layer.

At pick 1.03, if Gibbs and Bijan are gone, Puka Nacua and Ja'Marr Chase are in
the same VONA uncertainty tier. The live point-estimate board ranks Puka first:
all three custom-scoring projection sources favor him and the current market
selects him earlier. That is the engine answer, not the full on-the-clock answer.
The Model tiebreak is still 65% projection-derived core rank, so it is not an
independent fourth vote after VONA. FantasyPros' current 87-expert panel favors
Chase, Chase has the cleaner current availability signal, and his historical
weekly scoring has the larger upper tail.

**My judgment-layer pick today is Chase by a narrow margin.** The practical
decision rule is:

- **Chase while both Puka's possible league discipline and practice availability
  remain unresolved.**
- **Puka if the league closes the discipline question without a suspension and
  he resumes full, meaningful practice before the draft.**

No player-specific news penalty is hardcoded. It would go stale and double-count
market movement. Instead, the export now exposes source projections, current
market sample/dispersion, status, and latest ESPN-news date and explicitly asks
the judgment layer to override the board for fresh health, discipline, role, or
quarterback information.

## What each number does

| Layer | Formula/input | Used for | Not used for |
| --- | --- | --- | --- |
| Points | median of ESPN, CBS, FFToday rescored to league settings | base player forecast | ADP/ECR do not enter |
| Ceiling value | `projection + lambda × ceiling SD`, default `lambda = 0.40` | replacement, VONA | forecast disagreement |
| VONA | value now − expected best same-position value at the next pick | positional opportunity cost | K/DST |
| VONA tier | 4–12 point band scaled by forecast uncertainty (historical-residual floor plus source disagreement) | prevents false precision | does not change raw VONA |
| Model core | projection − 80% of position replacement projection | cross-position player quality | draft timing |
| Model | 65% Model-core rank + 35% half-PPR ECR re-ranked among QB/RB/WR/TE, then re-ranked | within-tier tiebreak | primary board order |
| REVIEW gate | worse of Model and skill-pool ECR when their gap is 25+ ranks | prevents a major consensus/model conflict from slipping through | VONA calculation |
| Timing | 60% ESPN-only room rank/ADP + 40% current 12-team half-PPR market | opponent order and survival | player projection or ECR |
| Survival | `1 − Phi((next pick − remaining-player timing rank) / ADP SD)` | chance of lasting to next turn | player value |
| Eligibility | roster caps and configured build guardrails/deadlines | which choices can be recommended | opponent bookkeeping |

Two consequences matter:

1. For two players at the same position, the expected-next-player term is the
   same. Their VONA difference is therefore exactly their ceiling-value
   difference. VONA does not add a separate Puka-versus-Chase argument.
2. Model decision rank is deliberately subordinate to VONA tier. It can resolve
   a close comparison, but it cannot promote a materially lower-opportunity-cost
   player simply because consensus likes him. For same-position players, its
   core component repeats the projection ordering already present in VONA; ECR,
   expert disagreement, historical shape, and current news are the genuinely
   independent checks.

## Puka versus Chase at 1.03

Assumption: Gibbs and Bijan were picks 1–2. Values use the fixed `lambda = 0.40`,
the best retained baseline from the earlier historical policy tests. Those tests
did not exercise every component of this revised engine exactly.

| Input/output | Puka Nacua | Ja'Marr Chase | Edge |
| --- | ---: | ---: | --- |
| ESPN custom projection | 314.5 | 294.9 | Puka +19.6 |
| CBS rescored projection | 350.5 | 318.7 | Puka +31.8 |
| FFToday rescored projection | 317.9 | 307.4 | Puka +10.5 |
| Ensemble projection | **317.9** | **307.4** | Puka +10.5 |
| Generic WR ceiling SD (23%) | 73.1 | 70.7 | Puka +2.4 |
| Ceiling-adjusted value | **347.14** | **335.68** | Puka +11.46 |
| Raw VONA | **+97.79** | **+86.33** | Puka +11.46 |
| VONA tier | **1** | **1** | tie |
| Model rank | **3** | **4** | Puka |
| FantasyPros half-PPR ECR | 4 | **3** | Chase |
| Expert rank average ± SD | 4.00 ± 1.35 | **2.73 ± 1.09** | Chase |
| Expert rank range | 1–9 | **1–5** | Chase tighter |
| Current 12-team half-PPR ADP | **2.8** | 4.1 | Puka |
| Observed ADP SD / sample | 0.6 / 43 | 0.9 / 294 | Chase sample stronger |

Every independent projection source in the ensemble favors Puka. FantasyPros
consensus narrowly favors Chase, while current Fantasy Football Calculator
draft rooms favor Puka. That is disagreement about ordering, not evidence that
the projection should be averaged with ADP or ECR.

The corrected ceiling proxy is important. The prior file carried SDs tied to
older projections and placed Chase barely outside Puka's tier. Recomputing every
SD from the current ensemble puts them in the same tier, where the documented
Model tiebreak belongs. The 73.1 versus 70.7 ceiling row is not an independent
Puka signal: both numbers are the same generic WR rate multiplied by projection.
It preserves cross-position policy behavior but cannot identify which WR has
the better player-specific weekly ceiling.

## Ceiling and current-news interpretation

Exact 2023–2025 weekly scoring under this league's rules shows different shapes:

| Historical weekly result | Puka | Chase |
| --- | ---: | ---: |
| Games | 44 | 49 |
| Mean | 18.73 | 18.56 |
| Population SD | 9.48 | 11.82 |
| 90th percentile | 32.75 | 34.60 |
| Maximum | 44.0 | 55.4 |

This historical sample says Chase has produced the larger single-week spike,
which matters in one-week playoff rounds. It does **not** by itself justify
replacing the generic ceiling proxy today: player history confounds changing
role, health, quarterback, and team context, and the configured position-rate
constants have not been isolated in a player-level volatility backtest. The UI
now labels that limitation instead of presenting the proxy as measured player
upside.

As of this audit, the Rams confirmed that Puka left the August 11 practice early.
Ian Rapoport reported minor groin soreness and caution; that characterization is
not yet a team diagnosis. Adam Schefter reported that possible discipline for
Puka remains under league review and raised Week 1 as a possible absence; there
is no official suspension or duration. Cincinnati's official August 12 preview
says Burrow, Chase, Higgins, and Chase Brown are set to play limited preseason
snaps, with no comparable current Chase/Burrow flag.

A one-game scenario is close but not automatically disqualifying. If the season
projections are spread across 17 games, 16 Puka games contribute about 299.2
points, so the replacement needs only 8.2 in the missed game to match Chase's
307.4. An exploratory 80-room forced-pick check found the next WR on Puka builds
averaged 9.5 points, putting Puka plus replacement about 1.3 points ahead in
that simplified scenario. That conditional average is not precise enough to
convert into an injury-probability threshold: it ignores which replacement is
actually startable that week, partial-game loss, and the different later picks
created by each Round 1 choice. Treat it only as evidence that one fully missed
game is approximately neutral in a season-total calculation. It does not price
the extra risk of an in-game aggravation, an uncertain return, or a suspension
longer than one week. Those asymmetric live risks are why the judgment-layer
recommendation can be Chase even while the static board correctly remains Puka.

## Should more expert rankings enter the model?

**Not as another weighted consensus today.** The refreshed FantasyPros Latest
ECR is already a broad half-PPR panel of 87 experts: 27 updated within one day,
53 within three days, and every included expert within seven days. The payload
also provides each player's average rank, standard deviation, and range. The
tool previously discarded those confidence fields; it now preserves and exports
them without turning them into an unvalidated weight.

Across the current top-150 skill-player pool, Spearman rank correlation with ECR
is 0.953 for ESPN rank, 0.955 for ESPN ADP, and 0.943 for current FFC ADP. Adding
another mainstream rank list to the same score is therefore likely to count the
same consensus twice. Projection rank is less redundant with ECR (0.674), which
supports the current separation between custom-scoring points and an expert
sanity check.

Current public cross-checks do not reveal a missing consensus signal. PFF's June
half-PPR list names Puka its top WR; RotoBaller's July list ranks Puka third and
Chase fourth; DraftSharks' team-coded public table appears to place the LAR WR
ahead of the CIN WR.
RotoBaller already contributes multiple experts to the FantasyPros panel, while
premium products such as Establish The Run and DraftSharks mix rankings with
their own projections, ADP, injury assumptions, and dynamic value methods. They
are useful independent reading, but poor candidates for an automatic extra vote
without licensed, stable data and an incremental historical test.

The minimal source architecture should remain:

1. stat projections → league-scored points;
2. one current expert panel → within-tier sanity check plus disagreement;
3. actual draft markets → availability only;
4. current news and genuinely independent analysts → judgment-layer override.

Before any new ranker receives live weight, freeze preseason snapshots across
multiple past seasons and compare out-of-season custom-score regret for the
existing Model versus a shadow candidate. Require improvement across seasons,
not merely across simulated rooms, and measure whether it adds signal after ECR,
projection, and market rank are already known. Until then: shadow-test, do not
blend.

## What changed in the tool

- Restored fixed `lambda = 0.40` as the default; removed the unvalidated
  round-varying auto-lambda schedule.
- Restored raw VONA by removing a roster-need multiplier from the VONA number.
  Build needs remain an eligibility layer, where they are visible and testable.
- Changed the default label to Decision and documented the precise hierarchy.
- Limited the live board to eight players and added 1–8 draft keys.
- Made Model, Points, ECR, ADP, and Snake planning views read-only.
- Removed Auto-to-my-pick because randomized guesses were being persisted in
  the authoritative real-pick ledger. The non-mutating Snake simulator remains.
- Warns users to reset if an older browser session still contains legacy auto
  picks.
- Excludes OUT/suspended/zero-projection/low-confidence players from opponent,
  survival, and expected-next-player forecasts while retaining them for manual
  bookkeeping.
- Replaced stale consensus-ADP reuse with current Fantasy Football Calculator
  12-team half-PPR ADP and observed per-player draft dispersion.
- Removed FantasyPros ECR from the ESPN-room timing proxy. Consensus now affects
  Model/review only and cannot also change survival or VONA.
- Re-ranked ECR among the same QB/RB/WR/TE pool as Model so late K/DST slots do
  not distort the scales.
- Preserved FantasyPros panel size, recency, and player-level mean/SD/range in
  the live file and copied state; additional rankings remain shadow evidence.
- Removed the artificial 1.5-pick floor from positive observed ADP SD; fallbacks
  still use a defensive floor.
- Added market sample size and dispersion source to copied state.
- Corrected first-down inputs to nflverse weekly data for 2023–2025.
- Regenerates generic ceiling SD from the current projection on every refresh.
- Requires a network refresh before the scripts can write the live HTML and
  rejects stale or undersampled market data.
- Added golden engine checks for pick 1.03, source data, same-position VONA,
  observed-SD survival, unavailable-player exclusion, every team's legal final
  roster, late K/DST, and read-only/keyboard safety.
- Aligned simulator and optimizer with the live engine. Optimizer confirmation
  now uses an independent Stage 2 and computes uncertainty across draft rooms,
  not correlated seasons from the same roster.

## Validation and confidence

The strongest retained conclusions are:

- K and D/ST in Rounds 13–14, supported primarily by the observed 2025 room
  (including Fairbairn still available at 14.05), not by the synthetic harness
  that assumes the same late-special-teams policy.
- Fixed `lambda = 0.40` as the best surviving tested baseline; no challenger has
  earned a live change. The retained historical harness is not an exact replay
  of every revised decision-layer component.
- Build through RB/WR, with one QB and one TE in this shallow format.
- Current projection ensemble and opponent selector have broad source coverage.

Moderate-confidence guardrails are three RB/WR by Round 4, starter core by Round
8, and ten total RB/WR. Exact QB/TE deadlines are less certain because the one
observed league draft shows an early QB run and a later desert that the generic
room simulator cannot fully reproduce. Those room findings remain visible in
the exported judgment context but are not silently hardcoded.

The simulation is a stress test, not proof of player truth. It checks that the
policy produces legal, varied rosters across room assumptions and that code
paths agree. Its free replacement-level fill-ins make it weak evidence for
QB2/TE2 and bench-depth choices. Historical weekly backtests remain the strategy
gate, and the live news check remains the player gate. The stale August 8
optimizer report has been retired rather than presented as current evidence.

## Sources

- [Fantasy Football Calculator 2026 half-PPR ADP](https://fantasyfootballcalculator.com/adp/half-ppr)
- [FantasyPros 2026 half-PPR consensus](https://www.fantasypros.com/nfl/cheatsheets/top-half-ppr-players.php)
- [FantasyPros ECR methodology](https://support.fantasypros.com/hc/en-us/articles/115001219327-What-is-ECR-Expert-Consensus-Rankings-and-how-do-you-calculate-it)
- [Mike Clay 2026 projections](https://g.espncdn.com/s/ffldraftkit/26/NFLDK2026_CS_ClayProjections2026.pdf)
- [NFL 2026 wide-receiver tiers](https://www.nfl.com/news/fantasy-football-wr-rankings-for-2026-nfl-season-draft-tiers-and-analysis)
- [PFF 2026 half-PPR rankings](https://www.pff.com/news/fantasy-football-half-ppr-rankings)
- [RotoBaller 2026 half-PPR top 300](https://www.rotoballer.com/fantasy-football-half-ppr-rankings-top-300-july-2026/1889522)
- [DraftSharks 2026 half-PPR rankings](https://www.draftsharks.com/rankings/half-ppr)
- [Establish The Run 2026 draft-kit architecture](https://establishtherun.com/establish-the-run-fantasy-football-draft-kit-pro-whats-inside/)
- [Rams: Puka's 2026 offseason return](https://www.therams.com/news/puka-nacua-nice-to-be-back-in-football-grateful-rams-support-otas-2026-offseason)
- [Rams: August 11 joint-practice observations](https://www.therams.com/news/10-observations-from-rams-joint-practice-with-cowboys-august-11-2026)
- [Bengals: August 13 preseason-game preview](https://www.bengals.com/news/game-preview-2026-preseason-week-bengals-lions)
- [NFL: Puka rehab and offseason context](https://www.nfl.com/news/rams-wr-puka-nacua-says-rehab-meetings-have-provided-great-improvement-in-his-life)
- [Ian Rapoport: minor groin soreness reported August 12](https://x.com/RapSheet/status/2087319528267272452)
- [Adam Schefter Podcast: possible Week 1 discipline scenario](https://open.spotify.com/episode/0IfETXOijszDz4lFtqG7Qu)
