# Verification brief: confirm these claims before any code change

Paste this whole file as your opening prompt.

You are in `/Users/tristenkho/ff-draft`. Read `CLAUDE.md` first. The draft is
**Sun Sep 6 2026, 8:00pm EDT**. Slot 3. Picks: 3, 22, 27, 46, 51, 70, 75, 94,
99, 118, 123, 142, 147, 166.

**Your job is to confirm or break the five claims in §2, then decide which of the
four changes in §3 are justified. You are not being asked to agree.** A prior
review of the companion document `HANDOFF-vona-investigation.md` found six real
errors in it; that review was correct and its corrections are already applied.
Assume more errors remain.

Do not modify `out/draft_terminal.html` in this session unless §3's criteria are
met. The working tree is clean at `84b373f`. The live board has not been
modified in any of this work — only harnesses, reports and these briefs.

**Live engine fingerprint** (sha256 of the engine block, for drift detection):
`f7c73b865910c467bd17d2433754aa2d58cd0b1fe14bc3523bcfeafeeb9715ad`
If this differs, the board changed after this brief was written — re-measure §2.1
before trusting anything here.

---

## 1. How the last round of claims failed, so you can calibrate

Errors already caught and fixed. If you find the same *class* of error again,
that is signal about the apparatus, not just the claim.

| Error | Nature |
|---|---|
| Room-level CI [7.02%, 9.98%] quoted as the effect interval | 2,800 simulated room-seasons treated as independent when 7 NFL seasons supply the variation. True season-level CI: **[1.04%, 15.96%]** |
| "Originally prespecified policy" in every report | Hardcoded template string, false for post-hoc arms. Removed; **older Aug reports still assert it** |
| "+4.5 pts/player × 14 ≈ +63/season" | Sim drafts **12** players (`range(1, 145)`), and per-rostered-player points ≠ team points. Real effect **+18.5** |
| "The defect is in selection, not ranking" | Correlation table rules out one explanation; does not establish another |
| `sd` called "four-source disagreement" | False. `sd = proj * CEILING_RATE[pos]`; disagreement is `proj_unc`, which never enters `value` |
| Dispersion/blend listed as "settled negatives" | Only `sd_proxy` got paired verification; the others merely tied on an underpowered screen |

**The meta-lesson: the training screen in `backtest_draft_policy.py` cannot
resolve anything under ~3 percentage points** (400 rooms, ~4% event rate). Do not
believe it. Only paired all-season verification runs, read at the season level.

---

## 2. Claims to verify

### 2.1 The live engine reaches — HIGHEST PRIORITY, verify this first

**Claim:** the shipped board recommends players well before the room would take
them. Rounds 1–12 average **−5.9 picks** vs ESPN room ADP (median −6.1), with
round 7 at −13.4 and round 9 at −17.0.

**Reproduce:**
```
node scripts/simulate_draft_slot3.js 300 /tmp/reach.json
```
Then aggregate `random.myAdp[]` by `round`; `delta = my pick number − player ADP`,
so negative = reached. This harness executes the live engine **byte-for-byte**
(it fails loudly if it cannot locate the engine block), which is why this claim
does not inherit the historical harness's proxy problem.

**Try to break it:**
- Is `p.adp` (ESPN room ADP) the right reference, or does `market_adp` /
  `room_rank` change the sign? Re-run the aggregation against all three.
- The opponents in this harness pick by market-blended timing. Is "reach vs ADP"
  partly definitional — i.e. would *any* non-ADP selector look like it reaches?
  **Test:** measure reach for a policy that picks by ADP order and confirm it
  comes out near zero. If it does not, the metric is broken.
- Round 6 is **+7.1** and round 2 is **+1.0** while neighbours are strongly
  negative. Unexplained. Find out why before trusting the mean.
- 300 drafts only. Re-run at 2000 and check the round-level means are stable.

**Reaching is not automatically bad** — it is only a loss if the player would have
survived. That audit is now DONE (`myAdp` records `surv`/`gain`/`tier`; 500
drafts, 6,000 skill picks). **The correlation runs backwards:**

| player's surv to my next pick | n | mean reach | % reaching >5 picks |
|---|---|---|---|
| 0.00–0.10 | 2029 | −4.2 | 48% |
| 0.10–0.25 | 789 | −8.4 | 31% |
| 0.25–0.50 | 1849 | −0.9 | 47% |
| 0.50–0.75 | 1229 | **−11.8** | 77% |
| 0.75–0.90 | 89 | **−30.3** | 100% |
| 0.90–1.00 | 15 | **−28.6** | 100% |

A rational selector reaches *most* on players who will not survive and *least* on
those who will. This does the opposite. **17.5% of all skill picks are wasteful
reaches** (>5 picks early on a >50%-survival player) — round 10 is 88% of picks,
round 12 66%, round 9 37%. Repeat offenders: MarShawn Lloyd (280x, −24.1 reach at
0.65 surv), Rachaad White (238x), Denzel Boston (170x), Jordan Mason (138x).

**The `surv` calibration check is now DONE too, and it strengthens the finding.**
`random.calibration[]` records every eligible player I did *not* take, bucketed by
predicted survival, checked at my next pick (500 drafts, 635,104 observations):

| bucket | n | predicted | observed | error |
|---|---|---|---|---|
| 0.1–0.2 | 4,158 | 0.149 | 0.066 | −0.083 |
| 0.2–0.3 | 7,111 | 0.248 | 0.172 | −0.076 |
| 0.4–0.5 | 7,457 | 0.441 | 0.439 | −0.002 |
| 0.5–0.6 | 13,765 | 0.543 | 0.627 | +0.084 |
| 0.6–0.7 | 17,518 | 0.657 | **0.805** | **+0.149** |
| 0.7–0.8 | 15,550 | 0.755 | **0.902** | **+0.148** |
| 0.8–0.9 | 32,163 | 0.854 | 0.952 | +0.098 |

Weighted mean |error| 0.022; overall predicted 0.910 vs observed 0.928.
`surv` is **not inflated — it is UNDERCONFIDENT** in exactly the 0.5–0.9 range
where the wasteful reaches live. Players the board thinks are 65% to last actually
last 80% of the time. So the "reaching is really correct aggression" escape is
refuted, and 17.5% understates the waste.

**External validation against the real 2025 draft is now DONE.**
`python3 scripts/validate_survival_2025.py` scores the same formula against what
these twelve managers actually did on 2025-08-31 (11,721 observations, 12
managers x 13 pick gaps). The underconfidence is **far larger against the real
room than in simulation**:

| bucket | n | predicted | observed | error |
|---|---|---|---|---|
| 0.1–0.2 | 251 | 0.150 | 0.494 | **+0.344** |
| 0.2–0.3 | 246 | 0.250 | 0.602 | **+0.352** |
| 0.3–0.4 | 276 | 0.351 | 0.685 | **+0.333** |
| 0.4–0.5 | 226 | 0.439 | 0.748 | **+0.309** |
| 0.5–0.6 | 406 | 0.539 | 0.788 | **+0.249** |
| 0.6–0.7 | 405 | 0.651 | 0.872 | **+0.221** |
| 0.9–1.0 | 7985 | 0.990 | 0.986 | −0.005 |

Brier 0.0789 vs 0.1013 for the base rate — **skill score +0.221**, so the model
has genuine ranking skill and is simply far too pessimistic in the mid-range.

**Sensitivity, and it survives.** Only 130/168 picks are FFC-priced; the other 38
(K, D/ST, sleepers) still consume slots, which compresses effective ADP and biases
predictions low. Stretching the index by the observed priced-pick density (0.774)
shrinks the overall bias from +0.064 to +0.024 and weighted error from 0.071 to
0.055, but the mid-range gap remains large: predicted 0.35 → observed 0.61,
0.55 → 0.74, 0.65 → 0.80.

**Interpretation:** this room departs from ADP hard (`out/league_tendencies_2025.md`:
K/DST 30–70 picks early, a 38-pick QB desert), and every off-ADP pick a manager
spends is a skill player who lasts longer than a strict-ADP model predicts. So on
Sunday, a player the board calls 30% to survive is closer to **60%** in this room.

**No 2024 draft exists to add a second season, so consistency was tested WITHIN
the draft instead** — using the conservative density-corrected model throughout:

- **Positive bias in 12/12 managers**, range +0.157 (kevin) to +0.311 (rayrice).
  Manager-clustered bootstrap, 5,000 resamples: mean **+0.214, 95% CI
  [+0.191, +0.240]**.
- **It is localised, not uniform.** Rounds 1–5 are calibrated (−0.037 to +0.043).
  The error appears at round 6 and stays: R6 **+0.402**, R7 **+0.387**,
  R8 **+0.448**, R9 +0.224, R11 +0.185, R12 +0.223, R13 +0.326. (R10 is +0.056,
  unexplained.)

That location is the whole story: `out/league_tendencies_2025.md` records rounds
7–9 running **53% special teams**. Every pick a manager spends off-ADP is a skill
player surviving longer than strict-ADP timing predicts — and it is exactly where
the reach audit found the waste (rounds 8–12). The two findings interlock.

**Caveat:** one draft. Managers share a pool and pick against each other, so the
clusters are not independent and the bootstrap interval is optimistic. Read it as
calibration shape and location, not a significance test.

### 2.2 Root cause: VONA gain is positional

**Claim:** `gain = value − expectedNext[pos]` asks "will *someone at this
position* be available later," never "will *this player* be available later," so
per-player `surv` is computed and displayed but never affects that player's own
gain.

**Reproduce:** read `computeBoard()` in `out/draft_terminal.html` (~line 17424)
and `expBestAt`/`survives`. Confirm `surv` appears only in `expectedNext` (over
*other* players) and in display, never in the selected player's `gain`.

**Try to break it:** does `vonaTier` chaining or `decisionRank` reintroduce
survival indirectly? Does `timingMetric` already encode enough of it?

### 2.3 Consensus beat the model in the historical backtest

**Claim:** +8.50% championship, **season-level 95% CI [+1.04%, +15.96%]**, 6/7
seasons. `out/draft_historical_robustness_consensus.md`.

```
python3 scripts/backtest_draft_policy.py --verify-finalist --verify-policy consensus --verification-drafts 400
```
(~20 min; deterministic — it reproduced identically once already.)

**Known weaknesses, all unresolved. Any one may sink it:**
- **Post-selection.** Arm and verification landed together in `5c83c5b`, after all
  outcomes were seen.
- **Not the live engine.** The harness reimplements the board: fixed 7.5pt band vs
  live `clamp(0.12*sqrt(unc^2+unc^2), 4, 12)`; `te2_edge`/`qb2_edge` permit QB2/TE2
  vs the live hard gate; 12 skill rounds vs 14; different model-rank formula.
- **It is ADP, not ECR.** Selection is `min(... p["adp"] ...)`. The live tiebreak
  is ECR-blended. Live-pool Spearman(ECR, market ADP) = 0.927, but ECR reacts to
  news faster (Jacobs: ECR 152, market ADP 42.4).
- **The variance objection, unanswered.** Playoff rates are identical (76.61% vs
  76.57%) and points differ by only +18.5, yet championship swings 8.5 points.
  That ratio suggests three single-elimination weeks dominate the metric.
  **Test:** re-rank the arms by playoff rate and by points. If consensus does not
  lead on those, the championship result is probably variance.
- Baseline championship rate (~4.9%) is *below* the 8.3% chance rate. Explain that
  before trusting either arm.

### 2.4 λ / ceiling weighting is inert

**Claim:** `sd = proj * CEILING_RATE[pos]` exactly (QB .1400, RB .2600, WR .2300,
TE .2499 — constant to 4 decimals), so `value = proj * (1 + λ·k_pos)` and λ
**cannot reorder two players at the same position at any value.** This is algebra,
not statistics; it should be trivially confirmable or refutable.

**Reproduce:** compute `sd/proj` per position over `PLAYERS`; check the spread.
Then ablate λ ∈ {0, 0.40, 1.0} in a patched copy and confirm within-position
ordering is identical.

### 2.5 Board vs ECR agree where it matters

**Claim:** median (ECR order − board rank): QB top-6 +3.5, TE top-6 −1.5, RB
top-30 −1.0, WR top-30 −1.0. Larger gaps exist only in the deep tail. Our sole
real edge over ECR is scoring (~0.80 PPR): WR +1.3, TE +1.3, RB −2.6 spots
(`python3 scripts/analyze_effective_ppr.py`).

**Caveat already found:** calling the tail "undraftable" was wrong — RB 31+ spans
board ranks ~120–206 and picks 118–166 reach into it.

---

## 3. Proposed changes and the evidence each requires

Ordered by value. **None should ship before Sunday Sep 6** unless you conclude
the evidence is stronger than described here.

### 3.1 Fix the screening stage (do this first, it gates everything else)
Finalists are chosen from a 400-room screen that cannot resolve <3 points, then
ranked lexicographically by `(champion, playoff, points)` — the noisiest metric
first. `core_2` has won holdouts and failed robustness twice, the signature of
noise selection.
**Change:** screen on points and playoff rate; confirm on championship. Or raise
screen sample size by ~10×.
**Justified by:** the arithmetic of the event rate. No new experiment needed.

### 3.2 Make the historical backtest execute the live engine
`simulate_draft_slot3.js` already does this and fingerprints the engine;
`backtest_draft_policy.py` reimplements it. Until this is closed, every policy
conclusion in the repo is about a proxy.
**Justified by:** §2.3's second bullet. This is the review's central objection.

### 3.3 Add per-player survival to `gain`
**The gating test in §2.1 has now been run and it passes** — high-survival reaches
are not merely common, they are where reaching is *worst*. Condition this instead
on the `surv` calibration check in §2.1.
**Criterion to ship:** a pre-registered arm, declared *before* running, that beats
baseline at the season level on the corrected gate, using the real engine (3.2).
Predeclare the arm list in a commit, then run. Do not add an arm and its
verification in the same commit again.

### 3.4 Retire or relabel λ
If §2.4 confirms: either remove the slider or document it as a positional
multiplier, and correct `CLAUDE.md`'s "justified by 8-of-12 playoffs + single-week
rounds", which its own backtest contradicts. `CLAUDE.md` marks this "do not
relitigate", so **ask the user before editing it.**

---

## 4. Settled — do not spend time re-deriving

- **No `sd` definition affects championship rate.** Position-rate proxy vs
  prior-season volatility, paired 2,800 rooms × 7 seasons: **+0.11% [−0.69%,
  +0.90%]**, 5/7 positive. (`out/draft_historical_robustness_sd_proxy.md`.)
  Dispersion and blend are *unresolved*, not settled — screen only.
- **ECR dispersion cannot be backtested.** No historical FantasyPros
  ECR-with-dispersion for 2018–24. FFC `adp_sd` is not a stand-in: correlates
  with `ecr_sd` at 0.687 raw but **0.179 after removing ADP level**.
- **The backtest's own `sd` is floored at `proj*0.10` for 47% of players.**
- **`core_2`** has failed the robustness gate twice (4/7 seasons).

---

## 5. Tooling

**Headless board** (run `computeBoard()` with no browser): extract the `<script>`,
truncate at `// ── event listeners`, stub `localStorage` /
`document.querySelector` (Proxy) / `matchMedia`, `new Function(...)` it, return
`{computeBoard, modelMeta, PLAYERS, replacement, skillPool}`. Rows carry
`p, v, gain, surv, modelRank, coreRank, ecrRank, blendScore, eligible,
needsReview, decisionRank, vonaTier`.

**Commands**
| Purpose | Command | Time |
|---|---|---|
| Refresh pool (rewrites the HTML) | `python3 scripts/refresh_draft_data.py --refresh --write` | 25s |
| **Validate after ANY edit** | `node scripts/test_draft_engine.js` (exit 0 = pass) | 10s |
| Live-engine draft sim | `node scripts/simulate_draft_slot3.js 300 <out.json>` | 2m |
| Full policy backtest | `python3 scripts/backtest_draft_policy.py` | 35m |
| Paired gate | `... --verify-finalist --verify-policy <id> --verification-drafts 400` | 20m |
| Effective-PPR | `python3 scripts/analyze_effective_ppr.py` | 30s |

**Gotchas**
- A syntax check proves nothing: a smart-quote bug (U+201C/U+201D) renders the UI
  unstyled while parsing as valid JS. Scan with **python3**, not bash `$'”'`
  (macOS bash 3.2 silently matches nothing and gives a false all-clear).
- `simulate_draft_slot3.js` reports points, not championship rate.
  `backtest_draft_policy.py` scores winning.
- `simulate_draft_slot3.js` prints its JSON to stdout *and* writes the file —
  redirect, don't pipe into a parser.
- Raw `out/*_raw.json` is gitignored by design.

**Commits this work spans:** `27ce986` Sep 2 refresh · `313e7b8` fix
`analyze_effective_ppr` · `21dbe6a` sd_mode arms · `5c83c5b` consensus arm ·
`bfd7bd8` investigation brief · `ae8a6db` corrections + season-level intervals ·
`3c625f9` regenerated report · `76edc0b` live-engine reach.

---

## 6. Draft-day facts (independent of all the above)

- **Josh Allen** — board 16, `surv` to pick 22 = 62%. ECR 28 (expert range 20–47).
  Market ADP 32.2 ±7.8 (n=342). **ESPN room ADP 19.3, room_rank 21.3** — our room
  takes him ~11 picks earlier than the national market.
- **Josh Jacobs** — `COMMISSIONER_EXEMPT`, already gated out of recommendations.
  ECR 152 but expert range **37–332**. Market ADP 42.4 (n=80) predates the news.
- **Settings changed in exactly 4 ways from 2025** — REFD 0.25→0.5, FG40-49 4→3.5,
  FG50-59 5→4, FG60+ 6→5; everything structural identical. Checkable against
  `out/espn_league_2025.json`. The REFD doubling is what makes this ~0.80 PPR and
  it is **new for 2026**, so `out/league_tendencies_2025.md` describes a room
  formed under the old 0.25.
- **On breaking news, trust ECR and ESPN room ADP over market ADP.** Timing and
  survival are 80% market ADP for RB/WR/TE, and FFC ADP lags news badly.

**The only thing recommended for Sunday is behavioural, not code:** the board
prints `survives` on every row. Where it recommends a large reach on a
high-survival player, take the consensus-best available and come back for him.
