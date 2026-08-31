# Draft-eve refresh

Run this on Saturday, September 5, 2026 from the repository root. The HTML
remains the only draft-state store; the reports below are read-only audits.

## 1. Refresh and inspect the numeric feeds

```bash
python3 scripts/refresh_draft_data.py --refresh
```

Review:

- `out/draft_data_refresh_analysis.md`
- `out/projection_ensemble_analysis.md`
- `out/special_teams_streaming_analysis.md`
- `out/draft_data_refresh_raw.json`

Check non-active statuses, large ESPN/market gaps, large Model/ECR conflicts,
low projection-source coverage, and the largest changes from the prior refresh.
In particular, re-check the early-round decision set and every player in the
late target thesis.

After the report is credible, write one newly downloaded snapshot into the
single-file terminal:

```bash
python3 scripts/refresh_draft_data.py --refresh --write
```

Do not run `update_projection_ensemble.py --write` afterward. The full refresh
already updates ESPN, CBS, FFToday, FantasyPros ECR, Fantasy Football Calculator
market ADP, weekly special-teams projections, and the embedded player pool.

## 2. Review the judgment layer

Numeric refreshes do not certify breaking news or editorial upside claims.
Review these source families separately:

- NFL and team transactions, injury reports, and practice reports for hard
  availability overrides.
- RotoWire for current depth charts and role/news synthesis.
- Footballguys for cross-platform ADP disagreement.
- PFF, Fantasy Life, CBS, NFL Fantasy, and DraftSharks for qualitative upside.

Require at least two independent source families before keeping a player in
`TARGET_THESIS`. Update its source labels, pick windows, and risk note in
`out/draft_terminal.html`; remove stale names. Then set `TARGET_THESIS.updated`
to the review date. Review the Chase/Puka, QB-window, and roster-build calls and
set `DRAFT_THESIS.updated` only after that review is complete.

Do not turn editorial mentions into a score bonus. The target thesis is an
advisory queue/watch layer; VONA, survival, Model rank, and eligibility remain
independent.

## 3. Validate before publishing

```bash
python3 -m py_compile scripts/refresh_draft_data.py scripts/update_projection_ensemble.py
node scripts/test_draft_engine.js
node scripts/simulate_draft_slot3.js 300 /tmp/draft-eve-sim.json
git diff --check
```

Open the terminal and confirm that Draft-day preflight shows projections,
market, ECR, and target research no more than one day old. Confirm the ledger is
empty, slot 3 is selected, browser storage is available, Jacobs remains
searchable but not model-draftable unless an authoritative status change occurs,
and every target-thesis player appears in the player pool.

## 4. Draft-day delta check

On Sunday, re-check only facts capable of changing a decision: official status,
practice participation, discipline, depth-chart transactions, and sharp ADP
movement. Run the full numeric refresh again only if a feed or material fact
changed. Never reset model weights from one news cycle.

During the draft, record every pick only in the HTML. At each of our picks, use
Copy state for the external top-three judgment step.
