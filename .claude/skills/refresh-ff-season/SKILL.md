---
name: refresh-ff-season
description: Refresh, publish and verify the Lava Hound League season companion from its authenticated read-only ESPN connection, then confirm the public GitHub Pages board is actually serving the new snapshot. Use when asked to refresh fantasy football, update the season companion or the phone board, sync ESPN roster/matchup data, publish the week, or check whether the live board is stale. Never use it to set a lineup, make a claim, or send anything to another manager.
---

# Refresh the fantasy season companion

Repo: `/Users/tristenkho/ff-draft`. Read `CLAUDE.md` first. The draft is over;
the live artifact is the **season companion** (`season/`, published at
`https://tristenkho.github.io/ff-draft/season/`). The draft terminal
(`out/draft_terminal.html`, published at the site root) is frozen history and a
refresh does not touch it.

Treat "refresh fantasy", "update the board", "publish the week" as the
**end-to-end request**:

```bash
./agent-tools/refresh
```

That is the whole lever. It detects the league's real week, runs the validation
suite, refreshes ESPN, exports the frozen HTML, scans it for secrets, commits,
pushes, and then polls the public URL until it serves the new snapshot id. Do
not hand-run the individual steps unless one of them fails.

Treat "check the board", "is it stale", "verify" as a **read-only status run**:
report without refreshing or publishing anything.

```bash
./agent-tools/current-week                                   # league's real week
python3 -m season briefing-status --season 2026 --week "$W"  # research vs snapshot
curl -s https://tristenkho.github.io/ff-draft/season/ | grep -o '"data_as_of":"[^"]*"' | head -1
```

Compare that live `data_as_of` against the newest row in
`.season/season.sqlite3`. A stale live page with a fresh local snapshot means a
publish was skipped, not that a refresh is needed.

## Safety boundary

- ESPN is **read-only**. Never set a lineup, submit a waiver claim, propose or
  accept a trade, or message a manager. Those are the user's to execute in ESPN.
- `./agent-tools/refresh` **publishes publicly**. The exported page carries the
  league name, every manager's roster and the draft recap. It carries no
  credentials and no league id and is `noindex`, but anyone with the URL can
  read it. That trade was already accepted; do not re-litigate it, and do not
  widen it by publishing anything new to `out/`.
- Never commit `.espn.json`, `.season/`, `.odds.json` or the access token.
  `publish-season` refuses to publish an export containing any of them — treat
  that refusal as a stop, never as something to work around.
- Do not hand-edit `.season/season.sqlite3` or a stored snapshot. Snapshots are
  append-only evidence; correcting one means refreshing again.

## What "done" means

A clean exit is not the result. Report all four, from evidence:

1. **Week** — the detected `scoringPeriodId`, not an assumed one.
2. **Snapshot** — the new snapshot id and its `data_as_of`.
3. **Live** — the public URL confirmed serving that same snapshot id. If the
   verification loop timed out, say the push landed and the deploy did not, and
   check `gh run list --limit 3`. Never report a push as a live update.
4. **Briefing** — whether research still matches the snapshot.

## The briefing is a separate import

Refreshing mints a new snapshot, which orphans a briefing reconciled against the
old one; the page then reads "Research predates this sync". This is expected and
is not a bug to fix in code. Research is written by a subscription agent and
imported by hand:

```bash
python3 -m season import-briefing --file .season/briefings/2026-weekNN.json
```

If you refreshed only to move the data forward and the user did not ask for new
research, say the briefing is now behind and offer to re-import; do not
manufacture briefing content to close the gap. To publish an already-reconciled
briefing without disturbing it, use `SKIP_REFRESH=1 ./agent-tools/publish-season`.

## When something fails

- **`check` fails** — stop. Do not publish. The suite's smart-quote scan exists
  because a smart quote used as an HTML attribute delimiter inside a template
  literal is valid JavaScript that renders the entire UI unstyled; a syntax
  check passes and the page is broken.
- **ESPN refresh fails** — usually expired cookies in `.espn.json`. Ask the user
  to re-copy `espn_s2`/`SWID` from a signed-in browser. Never request, store or
  type their ESPN password, and never substitute invented or scraped data for a
  failed fetch.
- **The week looks wrong** — `current-week` reads ESPN's own
  `scoringPeriodId` and fails loudly rather than guessing. Override with
  `WEEK=N ./agent-tools/refresh` only when you can say why ESPN is wrong.

## Related levers

`./agent-tools/phone` serves the live app to the user's phone over the LAN
(token required, `caffeinate` mandatory — this Mac sleeps in one minute).
`./agent-tools/export-week` freezes a week locally without publishing.
`python3 -m season refresh-props` fetches sportsbook lines and needs
`ODDS_API_KEY`; it is not part of a refresh and never runs implicitly.
