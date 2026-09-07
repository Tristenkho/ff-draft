# Fantasy Season Companion — product and implementation specification

Status: consolidated from the accepted interview recommendations; awaiting final shared-understanding confirmation before implementation. Updated September 7, 2026.
Owner: Tristen. League: ESPN 1238596447; season 2026; team 5.
This document specifies the product; no monitoring jobs, trades, claims or lineup changes are enabled by it.

## 1. Product outcome

Open the app and immediately understand: who I face, who each team owns, what changed, which decisions matter, what the evidence says, and when I must act. Agents must be able to retrieve and evaluate the exact same information without reverse-engineering the screen.

Primary job: replace the user's time researching videos and articles about risers/fallers, waivers, start/sit matchups and D/ST streaming with a researched, actionable briefing tailored to this league. Research all relevant alternatives but lead with at most five decisions; routine starters get short status checks. Give a preferred action, strongest counterargument and flip conditions. “Hold” is valid.

Accepted delivery constraints:
- One private app for this league across seasons, with Draft and Season modules sharing player identities, rules and evidence. Other managers do not get access to private analysis.
- No incremental spending: existing Codex/Claude subscriptions and the user's computer only. No paid API, credits, hosting or data subscription. Honor existing usage limits; do not silently incur overages.
- Research starts in Codex/Claude; save structured evidence and a readable briefing into the app. An in-app agent invocation is not required. Subscription access is not assumed to include programmatic API access.
- Agent primarily discovers reputable written and video sources; Flock Fantasy is not a mandatory or authoritative source. Prefer official/attributed reporting for facts and independent forecasts for close decisions; accessible transcripts must actually be read before claiming a video was reviewed.
- Proactive pre-waiver, pregame and material-change research is desired, including computer-off operation if genuinely feasible for free. On-demand research is an accepted fallback. No existing off-device execution capability is assumed.
- First deliverable is a real weekly research briefing before UI polish. ESPN actions remain manual.

Success criteria:
- Within one screen, identify the next relevant decision and its deadline.
- Within two interactions, compare any two players or inspect either matchup roster and associated news.
- Every recommendation exposes sources, timestamps, scoring assumptions, alternatives and unresolved facts.
- No claim of a completed ESPN action until a subsequent authoritative read confirms it.
- Unsupported access or stale data is visible, never rendered as no news/no offers/no moves needed.

## 2. Verified integration baseline and unresolved capabilities

Read-only probes against the existing authenticated ESPN connection on September 7:
- Team, roster, league settings and matchup reads work. Week 1 is Tristen versus Kevin.
- mPendingTransactions returns an explicitly present empty pendingTransactions array. No pending transaction is returned by that read. This establishes access to the view, not proof that all incoming-offer lifecycles are supported.
- mTransactions2 returns historical executed draft transactions. Transaction history is not an incoming trade inbox.
- Trade settings expose revisionHours=24, vetoVotesRequired=5 and deadlineDate. Display the date after timezone conversion; do not infer veto authority solely from the vote count.
- Acquisition settings show traditional waivers, no active acquisition budget, 24-hour waiver period and weekly order reset. Raw processing days and waiverProcessHour=11 are available. The hour's timezone/semantics and player-specific clearance must be verified before publishing an exact processing time. A budget field exists even though FAAB is disabled: do not display bids.
- League settings previously verified individual-game lineup locking, five bench slots and two IR slots. Re-read rather than hardcode.

Integration acceptance gates:
1. Reconcile matchup and all 12 current rosters against ESPN's visible league UI.
2. Confirm actual claim submission/clearance times and trade deadline against ESPN UI. Store supporting observation and time interpretation.
3. Validate a real incoming offer when one exists: correct recipient, all player legs, status, expiration, modification, cancellation and acceptance. Do not send a dummy offer to another manager for testing. Use synthetic fixtures until real evidence exists.
4. Verify direct-to-IR acquisition and OUT eligibility separately; eligibleSlots alone does not prove an action is currently permitted.
5. Audit weekly projection, ranking and market coverage before enabling a multi-source label.

## 3. Information architecture

Primary navigation: This Week / League / Moves / Draft. On mobile, use four bottom navigation items; desktop uses a narrow left navigation rail. Player search, source health, refresh and settings are global. Week and team selections have persistent URLs.

### This Week — default home

Ordered by urgency, not a wall of statistics:
1. Attention strip: next action time, number of actionable decisions, incoming offers, last successful sync. If nothing needs action, say so.
2. Matchup: my team and opponent, actual points when available, projected remaining points, players remaining. Distinguish ESPN's submitted lineups from suggested lineups. Do not publish a win probability until a calibrated distribution model exists.
3. Side-by-side starters aligned by fantasy slot, followed by expandable benches and IR for BOTH teams. Each player row: name, position/NFL team, NFL opponent, kickoff in local time, lock state, injury status, projection and news indicator.
4. Up to three priority decision cards: start/sit, claim deadline, injured starter, incoming offer. Additional decisions remain accessible.
5. Relevant news feed for both matchup rosters. Distinguish direct news from teammate news that changes a player's opportunity.
6. Upcoming decision timeline, grouped by day and actual game windows.

Show the opponent's actual submitted lineup, but use an estimated strongest legal opponent lineup for the main pregame outlook, explicitly labeled; provide a submitted-lineup scenario toggle. Neither scenario predicts the manager's actual choice. Respect locked slots in both cases.

Home presents my recommended lineup beside the opponent scenario, projected scores, favored team and source agreement. A small edge is a slight lean; source disagreement is visible. Numerical win probabilities require a defensible model of variability and correlation and must be labeled experimental until calibrated; do not derive them from point differences alone.

On refresh during the week, separate actual points, projections for players yet to start, and in-progress players. Do not add full-game projections to points already scored. Without an in-game remaining-production model, show in-progress players' actual points and mark the overall forecast incomplete; do not call actual points plus only unstarted projections an unbiased final score. This is a refresh-based outlook, not a promised live scoreboard. Show legal decisions still available.

Default to strongest expected production. Consider matchup-dependent variance only when the situation materially warrants it and supported player outcome ranges justify it.

Illustrative layout, with live values supplied at runtime:

    THIS WEEK · Week 1                     Updated [time]  Refresh
    Next: [decision] by [local date/time]       [Review]
    Tristen                         Kevin
    Actual / projected remaining    Actual / projected remaining
    QB  Allen                       Maye
    RB  ...                         ...
    FLEX Burden [Compare Warren]    ...
    [Bench + IR]                    [Bench + IR]
    Needs attention                 Relevant news
    [Warren vs Burden]               [Event → affected players]
    [Waiver review]                  [Event → affected players]
    Decision timeline →

The layout above is a wireframe, not a current start/sit recommendation.

### League

All 12 teams in a sortable roster directory. Default ordering follows league standings when available. Show starters, bench, IR, bye concentration, positional depth and pending completed-roster changes. Search by player to locate the current owner. Select any two teams for comparison and trade exploration.

Show “drafted by,” “currently owned by” and acquisition history separately. Rankings distinguish subjective assessments from projected lineup totals; avoid an unexplained overall grade.

### Moves

Tabs: Waivers / Trade inbox / Find a trade / Decision history.

Waivers: actionable add/drop pairs, current ownership status, claim priority, verified processing window, reason to act now, alternative claims and cost of dropping the player. Separate immediate starters, injury replacements, contingent stashes and K/DST streams. Include “hold current roster.”

Trade inbox: actual incoming and outgoing ESPN offers, sender/recipient, players in/out, expiration if known, status and last checked time. Show Accept / Counter / Decline advice as recommendations; “Review in ESPN” performs navigation only. User-authored proposed trades remain separate from real offers.

Find a trade: up to three supported candidates with before/after lineups for both sides, depth changes, required drops, waiver replacements, disagreement among sources and reasons each manager might accept or decline. Display “No clearly beneficial trade found” when appropriate.

Decision history: recommendation, source snapshot, time, user choice, observed ESPN execution and later outcome. User marking “done” cannot substitute for execution verification.

### Draft

The Draft tab is a locked actual recap after ESPN confirms completion and picks are reconciled. The existing standalone terminal is retained only as a migration fallback; its editable local ledger is not the frozen archive. Recap shows all 168 picks, round/team filters, each drafted roster and the original pre-draft evaluation inputs when captured. Reconstruct drafted rosters from picks and durable player IDs/names, not current roster membership. Missing historical evidence is marked unavailable rather than reconstructed with present-day data. Separate “quality at the time” from “season outcome so far.” Never rewrite a draft grade using later injuries or results without labeling the retrospective perspective. Draft ownership must never overwrite live ownership. Corrections create explicit versions rather than silent overwrites. Preserve original draft assessments; later retrospective assessments carry dates and a different horizon.

A season selector retains prior years. New seasons re-fetch league membership, rules, draft order and player data. Carry forward user preferences, not stale player judgments or unvalidated policy constants. Before the draft show preparation/practice; during the draft show live assistance; after completion lock the actual recap; after the season show review. Do not redesign the live draft algorithm during the initial weekly-research delivery.

### Shared player drawer and comparison view

Open from every player row, news event or trade leg. Show weekly/remaining-season views separately; projections by source; market evidence; usage; injury timeline; next games; league ownership; source links; and compare controls. Drawer content must also have a direct URL. On mobile it becomes a full-screen page with a back action.

## 4. Decision card contract

Every recommendation includes:
- Action and scope: week, lineup slot, player IDs, team IDs, proposed moves.
- Current-state snapshot and evaluated-at timestamp.
- Recommendation: start A, claim A/drop B, hold, trade proposal, or investigate.
- Ranked alternatives including no action and their opportunity cost.
- Expected benefit with units and horizon, range/sensitivity when supported; avoid false precision.
- Facts: source-linked, dated observations.
- Forecasts: named models and scoring basis; inferred first downs labeled.
- Judgment: explicit explanation connecting evidence to the action.
- Agreement: each source's direction, missing coverage and shared-provider provenance.
- Preconditions: health, roster eligibility, availability, claim outcome, trade review.
- Act-by time, verification state and remaining alternatives after that time.
- Flip conditions and next recheck time.
- Lifecycle: proposed / needs evidence / ready for review / superseded / dismissed / execution observed / expired.

Use “facts checked” and “forecast agreement” as separate indicators. No universal “verified winner” badge. Confidence is qualitative until calibrated; source vote percentages are not the probability a player outscores another.

## 5. Start/sit method

1. Retrieve authoritative current roster, settings, schedule and locked slots.
2. Compare complete legal lineups including all bench alternatives; preserve already locked assignments.
3. Score statistical forecasts under league rules. Do not add first-down bonuses to totals already containing them.
4. For close decisions seek at least two independent forecasting perspectives where available; disclose missing coverage and still offer a provisional choice unless critical facts are missing. Compare ESPN with independently sourced weekly projections and weekly flex consensus. RB25 versus WR25 is not a cross-position ordering. ADP and season ECR are not weekly start/sit rankings.
5. Inspect disagreement in carries, routes/targets, yards, receptions, touchdowns and health assumptions. Prefer expected points as the baseline; do not import draft lambda or VONA.
6. Identify new verified information not already included in the forecast. Avoid double injury discounts and adding another matchup bonus to matchup-adjusted projections.
7. Preserve flexibility: place later-starting eligible players in FLEX where this does not change the selected lineup. Show the earliest lock among competing options as the decision deadline.
8. Only use opponent-dependent variance adjustments with supported distributions/correlation and a meaningful scenario. Do not claim every WR has more upside than every RB.

Warren/Burden acceptance example: display the underlying projected opportunities, first-down contribution, source disagreement, Burden's actual practice evidence and Warren's committee uncertainty. A 1.4-point projection edge is a lean, not certainty. Earlier ESPN values in conversation are fixtures, never production defaults.

## 6. Sportsbook and prediction-market evidence

Keep three visible lanes initially: ESPN; independent fantasy forecasts; market-derived estimate. No arbitrary 60/40 weighting and no claim that markets outperform until tested.

For each market observation retain provider/book, original upstream source, timestamp, player/game ID, statistic, threshold, over/under prices, settlement terms and liquidity/limits when available. Use ordinary two-sided markets, excluding boosts/promotions. Group shared feeds; several books are not necessarily independent models.

- Remove margin using a documented method with sensitivity where material.
- A balanced over/under threshold approximates a median, not mean production. Unequal prices change the implied quantile. A single threshold cannot identify the entire distribution.
- Estimate means from suitable alternate thresholds/distribution assumptions; expose fit coverage and uncertainty. If unsupported, show a market check rather than fabricated fantasy points.
- Anytime TD probability is P(TD >= 1), not E[TD]. Use multiple-TD information or label the count-model assumption. Missing markets are unknown, not zero.
- Check participation and injury-void settlement conditions; fantasy still counts early-exit production.
- Apply this league's first-down and other scoring separately when not covered. Do not sum component medians and call it a calibrated expected total.
- Prediction contracts require matching resolution rules, timestamps, bid/ask spread and meaningful liquidity. Use as supplemental evidence when relevant; never require a market for every player.
- Team totals/spreads contextualize forecasts; do not count them twice if already used by the projection provider.

Backtest forecasts available at the actual decision time, not closing prices unavailable then. Compare ESPN, independent model, market method and blends on common coverage and report excluded players. Evaluate point error and paired start/sit outcomes with uncertainty; avoid tuning weights to a handful of wins.

## 7. Waiver decisions and deadlines

Rank feasible acquisition PLANS, not isolated player names. For D/ST compare the current week and the following two weeks; do not automatically reserve a second bench slot for a defense. Evaluate add/drop, immediate and next-few-week lineup benefit, contingencies, bye needs, IR eligibility, waiver priority cost and alternatives if a claim fails. Do not value unused bench season totals as starting points.

Claims are ordered and may conflict. Store which drop each claim uses, which claims are mutually exclusive, and what to do after partial success. Evaluate final roster legality including pending trades, IR activation and positional limits. A claim becoming unavailable supersedes its advice.

Deadline model separates:
- Claim submission cutoff, when known.
- Expected processing window, which may not be an exact instant.
- Individual player's waiver-clear time.
- Free-agent acquisition lock and affected player kickoff.
- User's recommended action time, deliberately before the hard deadline.

Never assume every claim runs Tuesday night. Determine actual league settings and player state; if ambiguous, label “Time unverified — check ESPN” and withhold exact countdowns. Store instants in UTC, display America/Chicago with timezone abbreviation and full date; handle daylight saving and international/Wednesday/Saturday games.

Accepted briefing rhythm: post-games/pre-waivers, pregame lineup review, material changes and on demand. The following intervals and quiet hours are implementation proposals to validate during scheduling setup, not commitments to an always-on service or accepted notification settings.

Proposed monitoring policy after implementation (configurable):
- Build waiver review 24 hours before a VERIFIED processing window; if a claim has a shorter lifetime, review on discovery.
- Refresh availability and news 2 hours before the verified cutoff; send a final reminder 30 minutes before only for an unresolved recommended action.
- Reconcile after processing; report actual wins/losses and available fallback moves.
- Background news/rosters every 60 minutes; pending offers every 15 minutes while service runs. Back off on rate limits.
- For each relevant kickoff: review 24 hours before, recheck around 90 minutes before, final unresolved-action reminder 30 minutes before. Ninety minutes is a recheck target, not a guarantee injury information has been published.
- Offer created/modified/expired: reevaluate; remind before verified expiration when still unresolved.

Notifications only for meaningful actionable changes. Deduplicate by event + decision version, support snooze and resolved state, and avoid repeated unchanged reports. Planned default quiet hours 10 p.m.–8 a.m. Central; surface overnight deadlines before quiet hours. Explicitly configured urgent deadline exceptions may bypass quiet hours. The app shows next scheduled check, last successful job and missed-run state. No monitoring claim while the host is asleep or worker is offline.

## 8. Trade evaluation and discovery

Evaluate both sides independently across near-term and rest-of-season horizons. Re-optimize lineups for each week under bye/injury scenarios, with remaining projection coverage clearly stated. Separate baseline starter gains, bench resilience and contingent upside; account for forced drops and the other team's best waiver option. Do not sum trade-value-chart numbers as proof of mutual benefit.

Search a bounded set of one-for-one, two-for-one and two-for-two exchanges among complementary roster needs. Screen by legal ownership and plausible value, then review a small shortlist. Include trade deadline, review delay, game locks and execution timing; accepting now does not imply eligibility this week.

Display for each team: players sent/received; starter changes; bench/IR changes; forecast range; role/health exposure; why it helps; strongest reason to decline. Label “potential fit” versus “both sides improve across tested scenarios.” Do not attach invented acceptance probabilities or assume managers follow last year's habits.

Initial league-specific examples to evaluate, NOT current offers or validated recommendations:
- Tristen sends Kelce + Dobbins to Matthew for Tyler Warren. Hypothesis: Tristen improves TE while Matthew obtains playable RB depth plus a replacement TE. Reject or downgrade if Matthew's TE loss outweighs usable depth, Tristen's RB insurance loss dominates, or sources show too little TE improvement.
- Tristen sends Rodriguez to Kyle for Andrews. Hypothesis: Kyle adds reserve RB coverage while Tristen adds a TE alternative. Weakness: Kyle may need Andrews to cover Kittle and can acquire an RB from waivers; Andrews is not necessarily an upgrade over Kelce. Likely reject unless current health/role evidence supports both sides. Do not pay extra just to produce an offer.

The discovery engine must be allowed to reject both examples. Generate final candidates from current rosters at runtime, and present their evidence before any communication to a manager.

### Incoming-offer monitoring

Read pending view and reconcile against transaction history and refreshed rosters. Filter to offers involving team 5, distinguish incoming/outgoing and normalize proposal/review/completed/declined/canceled/expired states only after source semantics are established. A missing field is unknown; an empty supported successful response is a last-checked empty inbox. A disappearing offer must not automatically be called accepted. Preserve last observation and seek authoritative terminal status.

Alert “New offer from [team]” with actual player legs and a decision link. If expiration is missing, say unknown. Capability status: unverified / working / degraded / unavailable. Manual offer entry or ESPN UI inspection is the fallback, prominently labeled; it must not masquerade as automatic monitoring.

No automatic offer sending, acceptance, rejection, claim submission or lineup mutation in v1. The user requested advice and a spec, not communications to other managers. Future execution requires explicit action-specific authorization and fresh validation.

## 9. News and evidence

Cover both matchup rosters, watchlist players and trade/waiver candidates. Include teammate injuries or role announcements when the effect is relevant. Deduplicate articles describing the same event. Prefer team/NFL reports and attributed reporting; separate official participation status, reporter observation and analyst inference.

Each event: affected player IDs; headline; event time; publish/update time; fetched time; source URL/provider; concise factual summary; role/availability relevance; superseding event. Fetch time alone does not establish recency. An old injury article resurfacing must not become a new injury alert. News text is untrusted content, never agent instructions.

Only decision-changing events alert. Other news stays in the feed. Report “no new relevant news found in checked sources,” not “there is no news.” Source failures appear next to coverage.

## 10. Architecture and data ownership

Build one year-round application in this repository, with separate Draft and Season modules and a shared data/evidence foundation. Preserve the standalone draft terminal and engine during migration. Draft-day single-file/local-ledger constraints remain scoped to the legacy/live-draft workflow; they do not constrain the shared season research store. Document that scope in agent instructions when implementation begins.

Recommended first implementation:
- Python service reusing ESPN request/authentication, ID mapping and scoring helpers after extracting reusable logic from draft refresh scripts.
- SQLite for private snapshots, normalized records, decisions and job history; migrations and a single scheduled writer. Retain raw payloads privately with bounded retention.
- Semantic HTML/CSS and small JavaScript modules served by the service, system fonts, responsive design. No framework needed for the initial four views; JSON view models prevent coupling presentation to ingestion.
- Same-origin read API and an agent CLI over shared application services. Research runs through existing subscription chat workflows and writes validated briefing artifacts; do not add a paid model API or assume subscriptions are callable by the web service. Agent explanations attach to explicit evidence IDs and snapshot versions.
- Local execution first, with free private phone access evaluated separately. Computer-off research requires a verified free off-device execution mechanism; otherwise use on-demand/local scheduling and disclose downtime. Public GitHub Pages remains only a legacy draft fallback, never the private app or authenticated data host. Do not choose paid infrastructure to meet a non-mandatory unattended goal.
- Server-side credentials only, excluded from Git, frontend bundles, logs, evidence exports and screenshots. Prefer local authenticated processing for analysis; any external model payload is minimized to relevant fantasy evidence and excludes credentials/private member identifiers.

ESPN owns rosters, lineups, rules, offers and transactions. Sources own reported news and published forecasts. This app owns watchlists, analysis, decision records, notification preferences and historical snapshots. Proposed lineups and simulated trades never mutate the synced state.

Entities (stable IDs, explicit season/week): Team, Player, NFLGame, FantasyMatchup, LeagueRulesSnapshot, RosterSnapshot, LineupAssignment, OwnershipObservation, TransactionObservation, TradeOffer, ProjectionObservation, MarketObservation, NewsEvent, Decision, Deadline, Notification, RefreshRun.

Every input observation stores source, observed_at, effective_at/as_of where supplied, snapshot ID and validity state. Every decision stores input snapshot IDs, scoring/model version and dependencies. Changed ownership/injury/offer/lock information invalidates dependent recommendations. Snapshot refreshes are atomic; never mix half-updated rosters with old ownership in a recommendation.

## 11. Agent and accessibility contract

Agents should use structured interfaces; UI automation is a fallback. Humans and agents receive the same decision payload and provenance.

Proposed read endpoints:
- GET /api/v1/overview?week=1
- GET /api/v1/matchups/{id}
- GET /api/v1/teams/{id}/roster?week=1
- GET /api/v1/players/{id}?week=1
- GET /api/v1/decisions?status=ready&week=1
- GET /api/v1/decisions/{id}/evidence
- GET /api/v1/waivers?week=1
- GET /api/v1/trade-offers?direction=incoming
- GET /api/v1/deadlines
- GET /api/v1/source-health

Local analysis operations (not ESPN mutations): request refresh; compare players; evaluate specified trade; generate waiver plans; dismiss/snooze local recommendation. Publish typed schemas/OpenAPI with legal parameters and returned status values. CLI mirrors these actions, supports --json and nonzero failure exits. Protect private reads and local writes; no arbitrary remote execution endpoint.

Every response: schema_version, snapshot_id, generated_at, data_as_of, stale flag, coverage, warnings, and stable entity IDs. Evidence exports use bounded structured JSON plus a concise readable summary; paginate full-roster/news history rather than truncate silently. Include relevant league scoring, current assignments, lock states, alternatives and source URLs. No credentials or unrelated member data.

UI requirements:
- Real links for navigation, buttons for actions, labeled inputs, semantic headings/tables and visible keyboard focus.
- Stable data-testid identifiers based on entity IDs, plus accessible names such as “Compare Jaylen Warren with Luther Burden.”
- No canvas-only roster, hover-only information, drag-only claim ordering or color-only injury/lock cues.
- Explicit loading, empty, stale, unsupported and failed states. Use readable error messages and retry controls.
- Direct URLs retain selected week/team/player/comparison; back navigation restores filters and scroll.
- “Copy decision context” on each card and “Copy week context” on home; export both facts and uncertainty.
- Proposed-versus-current lineup visually distinct. UI changes never imply an ESPN action occurred.
- Mobile touch targets at least 44px, comfortable readable text, reduced-motion support; long rosters scroll naturally. Reserve dense tables for comparison views rather than shrinking them to illegibility.

## 12. Freshness and failure policy

Initial targets, to tune against provider behavior: league rosters/offers 15 minutes at decision time; projections 24 hours away from games and 6 hours within the final day; market quotes 30 minutes near a decision; news checked within 30 minutes in the pregame window. Publication time must also be current for the relevant week. These are product policies, not claims about available provider SLAs.

Before presenting an actionable claim/offer/lineup recommendation, refresh mutable ownership and lock state. If it fails, retain the old view with a stale banner and mark affected decisions needs evidence. If an independent source is unavailable, show single-source coverage instead of blocking all roster browsing. After reconnect or host wake, reconcile first, then coalesce notifications; do not replay expired reminders.

## 13. Delivery slices and acceptance criteria

### Slice 0 — real researched briefing (first delivery)

Use the existing subscriptions to research a real week: recommended legal lineup, matchup score/favorite under explicit opponent assumptions, close start/sit comparisons, relevant news on both rosters, waiver add/drop plans, this-week/next-two-week D/ST choices, watchlist changes, verified deadlines and any supported trade opportunities/offers. Discover sources and record original timestamps, coverage and disagreements. Deliver a readable briefing plus structured evidence locally, without waiting for a polished UI, paid odds feed or scheduled worker. User feedback on usefulness shapes presentation. Acceptance: the user can act without having to repeat the research in videos/articles, and every decisive factual claim is traceable.

### Slice 1 — league truth, matchup and agent-readable shell

Deliver This Week, League and Draft navigation; current opponent, all rosters, current lineups, kickoff times, source health, stable routes, private storage and JSON/CLI exports. Validate exact 12-team roster reconciliation, draft/current separation, league scoring and special-team tiers, local time conversion and unavailable integration states. No AI needed to make these views useful.

### Slice 2 — evidence-backed start/sit and news

Audit and integrate independent weekly coverage. Add player comparison, affected-player news, decision timelines and explicit evidence exports. Acceptance: Warren/Burden comparison reproducible from stored snapshots; stale/contradictory news visible; no double scoring; locked lineups remain legal; no missing component represented as zero.

### Slice 3 — waivers and operational reminders

Implement available-player feed, ranked feasible plans, processing-time verification, IR capability checks, scheduler and notifications. Acceptance: order-dependent claim failures, player-specific clearance, overnight deadlines, DST transition, rate-limit backoff and sleeping-host recovery tested. A real read-only rehearsal before enabling notifications.

### Slice 4 — trade inbox and trade discovery

Implement proposal lifecycle and targeted scenario search. Acceptance: incoming real offer parity when available; synthetic tests for changes, cancellation, expired offer and missing fields; both-team lineup effects and forced drops; accepted-but-not-yet-executed distinction; no unsupported mutual-benefit claims.

### Slice 5 — market comparison and calibration

Integrate usable odds provider coverage, rules and conversion model. Display it separately first. Acceptance: margin adjustment, median/mean distinction, multi-TD counts, settlement differences, missing props, independent-source grouping and timestamp integrity. Enable learned weighting only after out-of-sample evidence supports it.

Market integration can proceed earlier as a bounded investigation; reliable weekly decisions must not wait on paid or unavailable data.

## 14. Validation scenarios and measurement

Required cases: player traded after recommendation; duplicate names/changed NFL team; bench player whose game locked; Wednesday opener; overseas morning kickoff; postponed game; OUT becomes questionable on IR; unavailable waiver target; mutually exclusive claims; trade requiring extra drop; offer disappears during refresh; ESPN auth expiration; provider wrong season/week; news republishes old surgery; first-down double counting; incomplete odds; source duplicates; job offline over deadline; corrected stats.

Measure source availability/freshness, unsupported decisive claims, missed deadlines, time to find next action, mobile/keyboard task completion, and recommendation reproducibility. Track fantasy forecast error and decision outcomes by position and source coverage, with sample sizes. Distinguish bad reasoning from a reasonable decision losing to variance. Do not promise championship probabilities from a small season sample.

## 15. Explicit non-goals and implementation gates

V1 does not place bets, execute ESPN actions, send manager messages, scrape credentials from browsers, invent missing reports, or require public exposure of league data. It does not promise instant trade notifications from periodic polling. It does not retrofit VONA/ADP survival into weekly decisions.

Before enabling the corresponding features: verify free source access and terms; private device access and any free off-device execution; notification destination and cadence preferences; waiver clock semantics and pending-offer lifecycle. Never substitute a paid service without a new user decision. These are implementation gates, not reasons to delay the read-only matchup/roster slice.

## References

- Existing code: scripts/espn_fetch.py, scripts/espn_draft_recap.py, scripts/refresh_draft_data.py, scripts/update_projection_ensemble.py.
- [ESPN waiver overview](https://support.espn.com/hc/en-us/articles/360000041152-Waivers-Overview)
- [ESPN waiver period](https://support.espn.com/hc/en-us/articles/360012531592-Waiver-Period)
- [ESPN lineup and roster lock times](https://support.espn.com/hc/en-us/articles/360055424451-Lineup-and-Roster-Lock-Times)
- [ESPN API client source, unofficial](https://github.com/cwendt94/espn-api/blob/master/espn_api/football/league.py)
- [DraftKings football settlement rules](https://sportsbook.draftkings.com/help/sport-rules/football?sf260608803=1)
- [Market mean/median methodology example](https://evanalytics.com/ncaaf/faq/propsheet)

Live league reads take precedence over generic ESPN support defaults. API behavior is unofficial and must remain covered by integration tests.
