# Handoff: draft terminal UI work (for Codex)

Read `AGENTS.md` first — it carries the league rules, scoring, delivery
automation policy, and a "do not relitigate" list of locked design decisions.
This document is the task spec that sits on top of it.

**Draft day is Sun Sep 6 2026, 8:00pm EDT.** Everything here must be finished and
merged before then. Nothing in this document changes draft *strategy* or model
math — it is presentation only. If a task appears to require changing a ranking
formula, you have misread it; stop and ask.

## The one file

Everything lives in `out/draft_terminal.html` (~16,100 lines). Single file, no
build step, no CDN, no external fonts, data inlined as a JS array. A GitHub Pages
workflow copies it to `_site/index.html` on push to `main`.

Layout of the `<script>` block:

| Line (approx) | Section |
|---|---|
| 412 | `// ── league constants` — `POS`, `TEAMS`, `ROUNDS`, `STARTERS` |
| 416 | `const PLAYERS=[...]` — 280 entries, ~40 fields each |
| 15126 | `// ── extended constants` — `CAPS`, `KDST_ROUND`, `STRATEGY`, `OPPONENT` |
| 15164 | `// ── state` — `picks`, `slot`, `lambda`, localStorage restore, `save()` |
| 15366 | `renderSnake()` — the 12×14 draft grid |
| 15415 | `// ── replacement level` |
| 15599 | `nextTurnTargets()` |
| 15608 | `computeBoard()` — returns board rows |
| 15665 | `// ── render` → `render()` at 15675 |
| 15849 | `// ── actions` |
| 15878 | `// ── state export` (Copy state) |
| 15995 | `// ── event listeners` |

**Line numbers shift as you edit.** Re-grep for the section banner comments
(`// ── render`) rather than trusting these after your first change.

## Ground truth: what already exists

This was verified by reading the code, not by grepping for feature names. Do not
rebuild any of it.

- **Positional run detection exists** — `render()`, search `$('#runs')`. Counts
  the last 8 picks and flags any position with ≥4.
- **The 12×14 draft grid exists** — `renderSnake()`. Desktop grid + a separate
  mobile round-by-round layout, click/keyboard to open `#snake-detail`.
- **Tier information exists** — `computeBoard()` assigns `r.vonaTier` and
  `r.tierBand`; each board row prints `waitBandLabel(r.vonaTier)` as "wait band A/B/C".
- **An auto-computed at-risk list exists** — `nextTurnTargets()` shows the top 3
  eligible players with `surv < .45` before your next pick.
- Position filter, sort, search, roster rail, needs panel, pick log, undo
  (`#backpick`, Ctrl/Cmd+Z), auto-draft, mock/plan view, help dialog, mobile nav.

## Conventions to follow

- **Vanilla JS only.** No frameworks, no bundler, no imports.
- `const $=s=>document.querySelector(s)` is the DOM helper. `clamp(x,a,b)` exists.
- Rendering is **full re-render**: `render()` rebuilds `innerHTML` for each panel.
  Do not introduce incremental DOM patching.
- CSS custom properties are the only palette:
  `--ink --panel --text --dim --dimmer --rule --green --amber --red --cyan`
  plus `--mono` / `--sans` for fonts. **Do not add new colors** — reuse these so
  the light/dark and mobile layouts keep working.
- Persisted state goes through `save()` (localStorage key `ff26-v3`). If you add
  a persisted field, add it to both the restore IIFE (~15169) and `save()`, and
  validate it on restore the way `slot` and `lambda` are validated.
- Existing markup classes to match: `.brow`, `.runbox`, `.slotrow`, `.logrow`,
  `.snakecell`, `.eyebrow`, `.empty-state`.

## Tasks

Ordered by value. Ship each as its own commit; they are independent.

### 1. User-managed queue (genuinely missing — biggest win)

Today the only forward-looking list is `nextTurnTargets()`, which is *computed*
(top 3 by survival). There is no list **you** curate. Sleeper's queue is the
feature reviewers single out, and it is what removes the need to re-read the
whole board every pick.

Build:
- A `queue` array of player ids in state, persisted via `save()`.
- Add/remove from a board row without drafting — a small control in `.brow` that
  does not collide with the existing click-to-draft. Use a dedicated button
  element and `e.stopPropagation()`; do not make the whole row toggle.
- Render the queue in the left rail near `#runs`, in queue order, each entry
  showing name, pos, and live survival % from `computeBoard()`.
- **Sniped detection:** when a queued player is drafted by anyone, mark that
  entry struck-through and dim until the user clears it. This is the actual value
  of a queue — knowing your target is gone without hunting for it.
- Drafting from the queue must go through the existing `draft(id)` path so all
  eligibility/cap logic still applies.
- Removing a drafted player from the queue on undo must work — hook the same
  place `undo()` restores state.

Keyboard: keys 1-8 are already bound to the top-8 board rows. **Do not rebind
them.** If you want a queue shortcut, use a modifier, and check the existing
handlers at `// ── event listeners` first.

### 2. Special-teams run detection (small change, room-specific value)

The existing `#runs` block filters K and DST *out* of the count:

```js
const last8=picks.slice(-8).map(id=>byId.get(id)).filter(p=>p&&!['K','DST'].includes(p.pos));
```

This hides the single most exploitable tendency in this league. From
`out/league_tendencies_2025.md` and `out/league_draft_2025.json`, this exact room
spent **42% / 58% / 58%** of rounds 7, 8 and 9 on kickers and defenses — 19 of 36
picks — while only 5 of 24 special-teams picks came in rounds 13-14.

Add a **separate** counter (do not change the skill-position one, which is
correctly scoped): count K+DST in the last 8 picks and, at ≥3, show a `.runbox hot`
reading something like *"Special-teams run — 4 of last 8. Skill players are
surviving longer than the board predicts."*

That message is the point: when opponents spend picks on kickers, survival
estimates for RB/WR become **pessimistic**, and you can wait longer than the
board suggests. Keep the wording factual; do not claim a specific pick advantage.

### 3. Bye-week conflicts (genuinely missing)

`bye` is currently rendered as text on each board row and never aggregated.

- In the needs/roster panel, show the bye distribution of your current roster.
- Flag when **3+ starters** share a bye week, and flag it harder when that week
  falls in weeks 15-17 (this league's playoffs, one week per round — a bye stack
  there is worse than in the regular season).
- On a board row, mark a player whose bye matches an already-stacked week.
- **Advisory only.** Do not let bye weeks change ranking, ordering, or
  eligibility. It is a note for the human, nothing else.

### 4. Tier cliff visuals (partially exists)

`vonaTier` and `tierBand` are already computed and printed as a text label. What
is missing is the *visual* break and the count.

- Draw a separator between the last row of one wait band and the first row of the
  next, in the default board view (`sortBy==='gain'`).
- Show how many eligible players remain in the current band — "3 left in band A".
  This is the most actionable single number in a draft UI: it tells you whether
  waiting costs you the tier.
- Only in the pick-board view. The audit view (`.brow.audit`) is a flat ranking
  by design; leave it alone.

Use the existing `r.vonaTier` values. **Do not recompute or retune tiers** —
`VONA_UNCERTAINTY_SCALE`, `VONA_TIER_MIN`, `VONA_TIER_MAX` are backtested
constants and are on the do-not-relitigate list.

### 5. Position colour-coding in the snake grid (small)

`renderSnake()` renders `.snakecell` with classes for `mine` / `real` / `mock`
only; position appears as text. ESPN's grid colour-codes by position so roster
shape reads at a glance.

Add a position class (`pos-qb`, `pos-rb`, …) to each populated cell and tint it
using the **existing** CSS variables. Keep it subtle — the `mine`, `real` and
`mock` states must stay clearly distinguishable, and the mobile layout
(`.snake-mobile-pick`) needs the same treatment. Verify both layouts.

## Verifying your work — required

A syntax check is **not** sufficient. This file has a known failure mode where
the JS parses cleanly and the entire UI renders unstyled. Do all three:

**1. Smart-quote check.** An earlier edit introduced U+201D as HTML attribute
delimiters inside a template literal (`class=”brow”`). That is valid JavaScript,
so `new Function(js)` passes while every style silently breaks.

`grep $'”'` does **not** work — macOS bash 3.2 does not support `\uXXXX` in
`$'...'` and matches nothing, giving a false all-clear. Use Python:

```bash
python3 -c "
s=open('out/draft_terminal.html',encoding='utf-8').read()
bad=[(i,hex(ord(c))) for i,c in enumerate(s) if c in '“”‘’']
print('smart quotes:', len(bad)); print(bad[:10])"
```

**2. Execute the logic headlessly.** Extract the script, truncate at
`// ── event listeners`, stub `localStorage`, `document.querySelector` (a Proxy
works), and `matchMedia`, then `new Function(...)` it and call `computeBoard()`.
`scripts/simulate_draft_slot3.js` already does exactly this — read it for the
working recipe, and run it as a regression check:

```bash
node scripts/simulate_draft_slot3.js 300 /tmp/sim.json
```

It runs the live engine byte-for-byte. Expect ~0.1 s/draft. Confirm 100% legal
rosters, K in R13, DST in R14, QB1 and TE1 in every roster. **If your change
alters these, you have touched model logic and must revert.**

**3. Open it in a browser.** Load `out/draft_terminal.html` as a local file,
record a few picks, and check the panel you changed plus the mobile layout at a
narrow viewport. `renderSnake()` has a separate mobile DOM path that desktop
testing will not exercise.

## Do not touch

- `computeBoard()` ranking math, `value()`, `survives()`, `replacement()`,
  `recommendationEligibility()`, or the `STRATEGY` / `OPPONENT` / `CAPS` constants.
- The λ schedule and ECR weighting.
- The `PLAYERS` array — it is regenerated by `scripts/refresh_draft_data.py`.
  Hand edits get overwritten and will be lost.
- Keys 1-8 board selection, Ctrl/Cmd+Z undo, Ctrl/Cmd+Enter auto-to-my-pick.
- Anything under `## Design decisions (do not relitigate)` in `AGENTS.md`.

There is a separate, unrelated open question about whether the opponent model's
K/DST timing should be recalibrated. **That is not in scope here** and is being
handled elsewhere — task 2 above only surfaces what opponents actually did, it
does not change how the model predicts them.

## Delivery

`AGENTS.md` authorizes automatic commit, push, PR and merge for completed and
validated work. Follow it:

- Stage **only** the files your task owns. The working tree has unrelated
  modifications (`scripts/espn_fetch.py`, `scripts/simulate_draft_slot3.js`) and
  untracked scratch/raw JSON — never include them.
- One focused commit per task above.
- Raw simulation output (`out/*_raw.json`) stays uncommitted.
- Stop before publishing only if validation fails, the remote is unavailable, or
  file scope is genuinely ambiguous.

## Reference

- `AGENTS.md` — league rules, scoring, locked decisions, delivery policy
- `out/league_tendencies_2025.md` — room study behind task 2
- `out/effective_ppr.md` — why this league is ~0.80 PPR for WR, not half-PPR
- `out/draft_slot3_fix_validation.md` — the roster-legality guarantees to preserve
- `out/draft_slot3_simulation_analysis.md` — **stale, pre-fix, ignore.** Describes
  QB4/TE5 rosters that the current eligibility gate makes impossible.
