# Handoff: is the VONA selection logic costing us championships?

Paste this whole file as your opening prompt. It is self-contained.

You are picking up an investigation in `/Users/tristenkho/ff-draft`. Read
`CLAUDE.md` first — it holds league rules, scoring, and locked design decisions.
The draft is **Sun Sep 6 2026, 8:00pm EDT**; this handoff was written Sep 2.
Slot 3. Picks: 3, 22, 27, 46, 51, 70, 75, 94, 99, 118, 123, 142, 147, 166.

**Your job is to falsify or confirm the headline finding below, then decide
whether the live board should change before Sunday.** Do not change
`out/draft_terminal.html` without clearing the robustness gate described here.

A prior review of this document found real errors in it. They are corrected
inline and each correction is labelled. If you find more, fix them here rather
than working around them.

---

## 1. The headline finding (directionally positive, NOT grounds for a live change)

Drafting **best-available by contemporaneous market rank** beats the live VONA
wait-band selection logic, with roster eligibility held identical so only the
ranker differs.

`python3 scripts/backtest_draft_policy.py --verify-finalist --verify-policy consensus --verification-drafts 400`

- Championship delta **+8.50%**, positive in **6/7** seasons
- **Season-level 95% CI [+1.04%, +15.96%]** (7 seasons, t with 6 df). Quote this one.
- The room-level CI [7.02%, 9.98%] is Monte Carlo precision only — it treats
  2,800 simulated room-seasons as independent when only 7 NFL seasons supply
  independent outcome variation. An earlier version of this handoff quoted it
  as the effect interval. That was wrong.
- 2,800 fresh-seed paired rooms per policy, all seasons 2018–2024
- Report: `out/draft_historical_robustness_consensus.md`

**This is a post-selection result.** The arm and its verification were introduced
in the same commit (`5c83c5b`), after all 2018–2024 outcomes had been examined.
Fresh seeds reduce Monte Carlo noise; they do not create fresh historical
evidence. The report template used to print "originally prespecified" for every
arm regardless — that boilerplate has since been removed.

Per-season championship: 2018 7.25→2.75 (−4.50), 2019 14.00→23.75 (+9.75),
2020 0.00→6.50 (+6.50), 2021 0.50→15.25 (+14.75), 2022 3.75→17.75 (+14.00),
2023 7.25→8.25 (+1.00), 2024 1.50→19.50 (+18.00).

**The baseline loses to chance.** Its mean championship rate is ~4.9% in a
12-team league where chance is 8.3%. Consensus runs ~13.4%.

**The strongest objection, unresolved.** Playoff rates are effectively identical
(76.61% baseline vs 76.57% consensus, delta −0.04%) and regular-season points
differ by only **+18.5** [13.7, 23.3]. An 8.5-point championship swing off ~1.3
points per week, with no movement in playoff qualification, suggests the
championship metric here is dominated by three single-elimination weeks rather
than by roster quality. Settle this before trusting the effect size.

### Scope limit: this is not the live engine

The historical harness reimplements the board rather than executing it. Known
divergences: fixed 7.5-point tier band vs the live uncertainty-scaled
`clamp(0.12*sqrt(unc^2+unc^2), 4, 12)`; `te2_edge`/`qb2_edge` permit QB2/TE2 vs
the live hard gate of exactly one each; 12 skill rounds vs 14; a different
model-rank formula. And the arm selects on **FFC ADP**, not FantasyPros ECR —
the live board's tiebreak is ECR-blended. So the result establishes *"ADP beats
this historical VONA proxy in this simulator"*, not *"ADP beats the live board."*
Closing that gap is the single highest-value next step.

### It is not a weak-projection artifact — I checked

The obvious objection is that the backtest reconstructs `proj` from prior-season
results plus market baseline, so maybe ADP just wins by default. **False.**
`proj` predicts actual season points *better* than ADP in every season:

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | mean |
|---|---|---|---|---|---|---|---|---|
| Spearman(proj, actual) | .565 | .620 | .605 | .603 | .681 | .556 | .553 | **.597** |
| Spearman(−ADP, actual) | .384 | .404 | .338 | .463 | .510 | .490 | .411 | **.429** |

Consensus wins **with the worse signal**, which rules out "ADP just predicts
better." It does **not** positively establish that the defect is in selection —
better global rank correlation does not imply better marginal value at each
price, or better playoff-week scoring. An earlier version asserted "the defect is
in selection, not ranking." That overstated what the table shows.

### Mechanism: VONA reaches

| | mean reach | median | actual pts/rostered player |
|---|---|---|---|
| VONA (live logic) | **−3.4 picks** | −2.3 | 170.6 |
| Consensus | **+2.7 picks** | +2.0 | 175.1 |

Negative = took the player before the market would. VONA reaches in nearly every
round, worst in rounds 5, 7, 8, 12 (−5 to −7 picks).

Do **not** convert that per-player gap into a season total. An earlier version of
this handoff wrote "+4.5 × 14 ≈ +63/season, matching the winning seasons" — wrong
twice: the simulator drafts **12** players, not 14 (`range(1, 145)` = 144 picks),
and per-rostered-player points do not map to team points because only started
players score. The measured team effect is **+18.5** points/season, and comparing
it selectively against the winning seasons was cherry-picking.

---

## 2. What is NOT established — this is your work

1. **Which component causes the reach.** Never decomposed. Candidates in
   `choose_user()` (`scripts/backtest_draft_policy.py:383`): the `gain`
   formulation itself (`value − expectedNext[pos]`), `need_factor()`, the 7.5pt
   tier compression, or `expected_best()`'s survival model. VONA gain is
   *positional* — it asks "will someone at this position be there later," never
   "will **this player** be there later." That is the most likely culprit and it
   is untested.
2. **Transfer to the real room.** The simulated opponents are ADP-driven *by
   construction* (`Opponent(model_weight=0.0, need_weight=.20, noise_scale=.65)`).
   Our actual room is not: `out/league_tendencies_2025.md` documents K/DST going
   30–70 picks early and a 38-pick QB desert. Following ADP against a room that
   departs from ADP could be better (you harvest their reaches) or could behave
   differently. **Untested, and it is the main reason the finding was not applied.**
3. **Whether it survives the real projection.** The backtest uses a
   reconstruction; the live board uses a 4-source ESPN+CBS+FFToday+Sleeper median.
4. **Why the baseline underperforms chance.** Suspicious on its own terms.
5. **Position mix.** Differs sharply (round 1: VONA takes WR 44% of drafts,
   consensus takes RB 89%; round 3: VONA 65% RB / 7% WR vs consensus 50% / 42%),
   but round-level points deltas are noisy and VONA wins some rounds. Do not
   assume the mix difference is the cause.

### Suggested attack order

1. Ablate `need_factor` and the tier compression separately against baseline.
2. Add a player-level survival term to `gain` (not just positional) and re-run.
3. Build an opponent config that reproduces the documented league tendencies
   (K/DST early, QB desert) and re-run consensus vs VONA against *that* room.
4. Only then decide on a live change.

---

## 3. Settled negatives — do not redo these

**λ / ceiling weighting is inert.** `sd = proj * CEILING_RATE[pos]` exactly
(`sd_source: "position-rate proxy"`; ratio constant to 4 decimals: QB .1400,
RB .2600, WR .2300, TE .2499). So `value = proj * (1 + λ·k_pos)` and **λ can
never reorder two players at the same position, at any value.** Ablating λ,
`ecrWeight`, and `MODEL_REPLACEMENT_WEIGHT` moves board-vs-ECR medians by ≤1 rank.

**No `sd` definition affects championship rate** — but only the position-rate
proxy got the full paired verification. Dispersion and blend merely tied on the
underpowered training screen, which by this document's own §6 gotcha cannot
resolve anything under ~3 points. Treat those two as *unresolved*, not settled.
Tested via the `sd_mode` knob
now on `Policy` (`volatility` / `proxy` / `dispersion` / `blend`):
- ADP-dispersion and volatility+dispersion blend: **exactly** baseline (4.75%),
  while drafting measurably different rosters. Neither reached the holdout.
- Live position-rate proxy, paired 2,800 rooms × 7 seasons: **+0.11%
  [−0.69%, +0.90%]**, positive 5/7. `out/draft_historical_robustness_sd_proxy.md`.

**ECR dispersion cannot be backtested.** FantasyPros historical ECR-with-dispersion
does not exist for 2018–24. FFC `adp_sd` is not a usable stand-in: it correlates
with `ecr_sd` at 0.687 raw but **0.179 after removing ADP level**. Also note the
backtest's own `sd` is floored at `proj*0.10` for **47%** of players, so it was
never the rich variance signal it appears to be.

**`core_2` ("Two RB/WR through R4")** wins holdouts repeatedly but has failed the
robustness gate twice (4/7 seasons). `out/draft_historical_robustness_core_2.md`.

---

## 4. Board vs ECR — the real picture

Split by whether the player is ever actually drafted (gated build = 1 QB, 1 TE,
10 RB/WR), median (ECR order − board rank):

| Pos | Segment | n | median Δ |
|---|---|---|---|
| QB | top 6 | 6 | +3.5 |
| QB | rest (never drafted) | 24 | +13.0 |
| TE | top 6 | 6 | −1.5 |
| TE | rest | 20 | +14.0 |
| RB | top 30 | 30 | −1.0 |
| RB | 31+ | 39 | −23.0 |
| WR | top 30 | 30 | −1.0 |
| WR | 31+ | 57 | +10.0 |

**Where we actually draft, board and ECR agree within 1–3 ranks.** Any larger
number computed across the whole eligible pool is dominated by the deep tail.
"Undraftable" overstates it: RB 31+ spans board ranks ~120–206 and picks 118–166
reach into that, so part of that segment is genuinely in play for the last four
or five picks.

Our only genuine informational edge over ECR is scoring: ECR is half-PPR, this
league is ~0.80 PPR for WR because REFD is 0.5. Worth **WR +1.3, TE +1.3,
RB −2.6 spots** (`out/effective_ppr.md`, `python3 scripts/analyze_effective_ppr.py`).

RB 31+ at −23 is the one live blind spot. Note the mechanism carefully: `sd` is
the position-rate proxy (`proj * CEILING_RATE[pos]`), a pure function of `proj`,
so it cannot encode bimodality at all. The four-source disagreement figure lives
in a *different* field, `proj_unc`, which does not enter `value`. Either way the
model cannot see handcuff upside. ECR can — `ecr_min`/`ecr_max`/`ecr_sd` are already stored
and displayed. Keep that as a judgment signal; putting it into `value` tested null.

---

## 5. Draft-day facts (current as of Sep 2 refresh)

**League settings changed in exactly 4 ways from 2025** — REFD 0.25→0.5,
FG40-49 4→3.5, FG50-59 5→4, FG60+ 6→5. Everything structural is byte-identical.
Draft slot moved 6 → 3. The REFD doubling is what makes this ~0.80 PPR; it is
**new for 2026**, so `league_tendencies_2025.md` describes room behavior formed
under the old 0.25.

**Josh Allen** — board 16, gain +18.9, survival to pick 22 **62%**. ECR 28
(expert range 20–47, sd 6.22 — experts agree). Market ADP 32.2 ±7.8 (n=342).
**But ESPN room ADP 19.3, room_rank 21.3** — our room takes him ~11 picks earlier
than the national market. Expert mock took him round 3 (~pick 32) as QB1 overall.

**Josh Jacobs** — `COMMISSIONER_EXEMPT`, Sleeper `NA`, already gated out of
recommendations. ECR 152 but expert range **37–332**, sd 58.67 — the widest
disagreement in the pool. Market ADP 42.4 (n=80) is stale and predates the news;
ESPN ADP 66.2 and rising. Expert mock took him round 9.

**Provenance note.** The expert-mock timings below come from a YouTube transcript
pulled into a session scratchpad, not from any repo artifact, so they are not
independently checkable here — treat them as anecdote. The 2025-vs-2026 settings
comparison came from a live ESPN API fetch of the 2025 season; the raw response is
now committed at `out/espn_league_2025.json` so that claim *is* checkable.

**Sep 2 refresh deltas** — Pacheco → IR (proj 96.8→81.3). Newly questionable:
Tee Higgins, Carnell Tate, Bhayshul Tuten, Sean Tucker, Jonathon Brooks. Cleared
to active: Kenneth Walker III, Brian Thomas Jr. Kaytron Allen in, Ty Johnson out.

**ECR is fresher than market ADP on news.** Spearman(ECR order, market ADP order)
= 0.927, median gap 9 ranks — but the biggest disagreements are all news cases
(Jacobs, Ollie Gordon II at ECR 258 / market ADP 52 on n=6). Timing and survival
are 80% market ADP for RB/WR/TE, so **on a player with breaking news, trust ECR
and ESPN room ADP over the market number.**

Low-n market ADP is a checked non-issue: `n=0` rows fall back to `room_rank`, and
only two eligible players ride on small nonzero n (Ollie Gordon II n=6, Travis
Hunter n=16), both far outside the draftable range.

---

## 6. Tooling

**Headless board harness** (run `computeBoard()` without a browser) — extract the
`<script>`, truncate at `// ── event listeners`, stub `localStorage` /
`document.querySelector` (Proxy) / `matchMedia`, `new Function(...)` it. A working
copy with a constant-patching hook is described in
`.claude/projects/-Users-tristenkho-ff-draft/memory/` notes; rebuild it if absent.
`computeBoard()` returns rows with `p, v, gain, surv, modelRank, coreRank,
ecrRank, blendScore, eligible, needsReview, decisionRank, vonaTier`.

**Commands**
- Refresh pool (15–25s, rewrites the HTML): `python3 scripts/refresh_draft_data.py --refresh --write`
- Validate after ANY edit: `node scripts/test_draft_engine.js` (exit 0 = pass)
- Full policy backtest (~35 min): `python3 scripts/backtest_draft_policy.py`
- Paired gate (~20 min): `... --verify-finalist --verify-policy <id> --verification-drafts 400`
- Effective-PPR analysis: `python3 scripts/analyze_effective_ppr.py`

**Gotchas**
- A syntax check proves nothing — a smart-quote bug (U+201C/U+201D) renders the
  UI unstyled while parsing as valid JS. After editing `render()`, scan for those
  with **python3**, not bash `$'”'` (macOS bash 3.2 silently matches nothing).
- The training screen in `backtest_draft_policy.py` is unpaired with ~4% event
  rates and 400 rooms — **it cannot resolve anything under ~3 points.** Only
  believe paired all-season verification runs. I misread the screen once this
  session and had to retract.
- `simulate_draft_slot3.js` reports `meanProj`/`meanVor` (points), not
  championship rate. `backtest_draft_policy.py` is the one that scores winning.

**Relevant commits (all pushed to `main`)**
`27ce986` Sep 2 data refresh · `313e7b8` fix `analyze_effective_ppr` (was dead
since the Sleeper commit) · `21dbe6a` sd_mode knob, three sd definitions
equivalent · `5c83c5b` consensus arm, the headline finding.

---

## 7. The decision you are being asked to reach

Options, in the order I'd weigh them:

- **(a)** Behavioral rule only — don't reach; prefer consensus-best available and
  let VONA break ties. Zero code risk, captures most of the measured effect.
- **(b)** Add a consensus-first selection toggle to the live board so both orders
  are visible on draft day. Reversible, doesn't require trusting the backtest.
- **(c)** Decompose the VONA reach first (§2), then decide.

I lean **(b)**, but the transfer caveat in §2.2 is unresolved and it is the single
most important thing to settle before touching the ranking engine.
