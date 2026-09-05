# Fantasy Draft Terminal

## Goal
Single-file HTML draft assistant for one ESPN league.
Draft is Sun Sep 6 2026, 8:00pm EDT (7:00pm CDT). No backend, no CDN, no build step.

## Workflow (draft day)
Network is assumed available. The HTML tool is the source of truth for draft
state: click each player as they come off the board. When it is my pick, read
the board, then paste the exported state to Claude Code to confirm a top 3
with reasoning before committing.
- HTML holds state. Do NOT record picks anywhere else — two state stores diverge.
- Claude Code is the judgement layer, not the bookkeeping layer.

Two corrections to apply when reading the board (both measured 2026-09-02,
see the memory notes and `scripts/validate_survival_2025.py`):
- **`survives` is calibrated in rounds 1-5 and roughly half the truth from
  round 6 on.** Validated against the real 2025 draft by these same twelve
  managers: bias +0.39 to +0.45 in rounds 6-8, 12/12 managers positive. A
  player shown at 40% in round 7 has historically lasted ~85%.
- **The board reaches.** Byte-for-byte simulation of the live engine puts its
  own recommendations ~5.9 picks ahead of ESPN room ADP over rounds 1-12,
  worst in rounds 7-12 — the same window where survival is most underestimated.
  Before taking a large reach, check `survives`, apply the correction above,
  and prefer the consensus-best player if he would keep.

## Latest pre-draft audit (September 5)
Read `DRAFT-DAY-BRIEF.md` and `out/draft_eve_audit_2026-09-05.md` before live
judgment. They supersede the September 2 snapshot numbers above: the refreshed
300-draft simulation averages 6.6 picks ahead of ESPN ADP. Historical survival
underprediction is strongest in rounds 6–8; round 2 also had +13 percentage
points of bias. Do not mechanically double all probabilities. Model rank has
material QB premiums and WR/contingent-RB discounts versus ECR; the scoring
adjustment alone does not justify large gaps. Copy state now includes consensus
alternatives outside the top eight so those players receive explicit review.

## Delivery automation
- After completing and validating requested code or site changes, automatically
  stage only the files owned by that task, create a focused commit, and push it.
- Treat a successful push to the publishing branch as authorization to trigger
  the configured GitHub Pages deployment; do not ask for a separate routine
  commit, push, or publish confirmation.
- Preserve unrelated working-tree changes and never include them in the commit.
  Generated scratch files and bulky raw simulation output stay uncommitted unless
  the user explicitly asks to publish them.
- If the current branch cannot publish directly, push a focused feature branch,
  open a pull request, mark it ready, and merge it automatically after validation
  and required checks pass. Do not wait for manual review or merge confirmation.
- Stop before publishing only when validation fails, authentication or the remote
  is unavailable, the intended file scope is genuinely ambiguous, or the action
  would expose secrets or perform a destructive migration.

## League
12 teams, snake, redraft, 14 rounds, 90s/pick. Draft slot: 3
2026 order: berds, kevin, tristen, castelani, kyle, houston hotdogs, deshaun,
worthy, matthew, capullo, ray rice, sweet
My picks: 3 22 27 46 51 70 75 94 99 118 123 142 147 166
Starters: QB1 RB2 WR2 TE1 FLEX1 K1 DST1 · Bench 5 · IR 2
Caps: QB4 RB8 WR8 TE3 K3 DST3
Playoffs: 8 of 12 teams, weeks 15-17, one week per round
Waivers: reset weekly to inverse standings, no FAAB, 1-day period

## Scoring
Pass: 0.04/yd, TD 4, INT -2, PFD 0.1, 2PC 2 (no yardage bonuses)
Rush: 0.1/yd, TD 6, RFD 0.25, 2PR 2
Rec:  0.1/yd, REC 0.5, TD 6, REFD 0.5, 2PRE 2
Misc: FUML -2, all return/recovery TDs 6
K: PAT 1, FG 3/3.5/4/5 by distance, miss -1
DST: see league settings (points-allowed and yards-allowed tiers)

## Design decisions (do not relitigate)
- Rank by VONA: gain = value - E[best at position at my next pick]
- Ceiling weighting: value = proj + lambda*sd, lambda live-adjustable, default 0.40
  (justified by 8-of-12 playoffs + single-week rounds)
- Survival: P = 1 - Phi((k - effective_adp)/adp_sd), where effective_adp is
  ADP re-ranked among REMAINING players, not absolute ADP
- K and DST excluded from VONA entirely, hardcoded to rounds 13-14
- Replacement: 12QB/24RB/24WR/12TE + 12 FLEX allocated to best next man
- Show the top 8 candidates in the first viewport, then allow scrolling through
  the full ranking. Keys 1–8 select only the top eight.

## Room intelligence (read before changing draft strategy)
`out/league_tendencies_2025.md` — study of the 2025 draft by the same twelve
managers, graded against same-weekend FantasyFootballCalculator ADP. No season
outcomes used. Raw draft in `out/league_draft_2025.json`.
The three exploitable findings: K/DST go 30-70 picks early (rounds 7-9 were 53%
special teams), QB1-12 go early then a 38-pick desert with no QB at all, and WR
is priced at market. Its "Model changes this argues for" table is NOT applied —
those constants contradict the generic-room backtest and must be validated
through scripts/backtest_draft_policy.py before going live.

## Empirical first-down rates (nflverse 2023-25, already computed)
See out/first_down_rates.json. WR 0.597/rec, TE 0.511, RB 0.325.
RB 0.224/carry, QB 0.344.
Deep targets convert at 0.92-0.99 — deep threats are NOT devalued here.

## Constraints
- Single file output. Inline all data as a JS array. System fonts only.
- No localStorage caveat: running as local file, browser storage works fine.
- Needs a one-click "Copy state" export (roster, picks, board) to hand to Claude.
