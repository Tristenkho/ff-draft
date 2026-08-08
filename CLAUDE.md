# Fantasy Draft Terminal

## Goal
Single-file HTML draft assistant for one ESPN league.
Draft is [DATE]. No backend, no CDN, no build step.

## Workflow (draft day)
Network is assumed available. The HTML tool is the source of truth for draft
state: click each player as they come off the board. When it is my pick, read
the board, then paste the exported state to Claude Code to confirm a top 3
with reasoning before committing.
- HTML holds state. Do NOT record picks anywhere else — two state stores diverge.
- Claude Code is the judgement layer, not the bookkeeping layer.

## Delivery automation
- After completing and validating requested code or site changes, automatically
  stage only the files owned by that task, create a focused commit, and push it.
- Treat a successful push to the publishing branch as authorization to trigger
  the configured GitHub Pages deployment; do not ask for a separate routine
  commit, push, or publish confirmation.
- Preserve unrelated working-tree changes and never include them in the commit.
  Generated scratch files and bulky raw simulation output stay uncommitted unless
  the user explicitly asks to publish them.
- If the current branch cannot publish directly, push a focused feature branch
  and open a draft pull request automatically.
- Stop before publishing only when validation fails, authentication or the remote
  is unavailable, the intended file scope is genuinely ambiguous, or the action
  would expose secrets or perform a destructive migration.

## League
12 teams, snake, redraft, 14 rounds, 90s/pick. Draft slot: [TBD]
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
- Show 8 candidates max. One screen, no scrolling, keyboard-driven.

## Empirical first-down rates (nflverse 2023-25, already computed)
See out/first_down_rates.json. WR 0.597/rec, TE 0.511, RB 0.325.
RB 0.224/carry, QB 0.344.
Deep targets convert at 0.92-0.99 — deep threats are NOT devalued here.

## Constraints
- Single file output. Inline all data as a JS array. System fonts only.
- No localStorage caveat: running as local file, browser storage works fine.
- Needs a one-click "Copy state" export (roster, picks, board) to hand to Claude.
