# Season companion design interview

Status: product interview consolidated; all recommendations in rounds 11–25 accepted. Revised season-companion-spec.md reflects these answers. Await final shared-understanding confirmation before implementation. Earlier open-question lists below are historical and superseded by accepted decisions.

## Confirmed user requirements

- Cost ceiling: no spending beyond existing Codex and Claude subscriptions and the user's computer. Existing subscription capacity may be used; paid APIs, extra credits, new subscriptions and paid hosting are not authorized.
- Primary outcome: replace time spent researching YouTube videos about risers/fallers, waiver pickups, matchup-based start/sit choices and D/ST streaming with agentic research tailored to the user's team.
- Previously requested: actual draft recap; all current league rosters; weekly matchup and both teams' players/news; decision timing; waiver advice; incoming-trade visibility; mutually beneficial trade suggestions with reasoning; usable human UI and agent navigation.
- User is exploring a unified app reusable across years, with the actual completed draft locked as a historical record. Exact archival behavior remains to be settled.

## Open decisions from round 1

1. Audience: private single league versus more leagues/users.
2. Delivery: proactive versus on-demand, phone/desktop/chat, and required availability.
3. Authority: recommendations versus explicitly approved ESPN actions versus automation.
4. Evidence policy: provisional decisions when sources disagree or inputs are missing.
5. Cost boundary settled: existing subscriptions/computer only. Free unattended execution and computer-off operation remain feasibility investigations, not promised capabilities.
6. Initial delivery deadline and research-first experience; prior dashboard-first recommendation is not accepted by default.

## Research branches opened by the user's response

- Preferred creators/sites, discovery latitude, source diversity and accessible transcript coverage.
- Briefing format: recommended team actions with evidence versus broad league research feed.
- Research cadence: waiver review, pregame review, breaking-news events; delivery constraints depend on free execution resources.
- Distinguish claim extraction from validation: videos supply analyst opinions and leads, not independently verified facts merely because multiple creators repeat them.
- Include start/sit, waiver add/drop pairs, D/ST streamers and role/usage changes; interpret risers/fallers as changes in opportunity/value rather than draft ADP during the season.

## Answers from research round

- Q7: Agent should primarily discover reputable sources across written articles and YouTube. Flock Fantasy was watched mainly for entertainment, not designated as an authoritative required source. No medium or creator receives automatic priority.
- Q9: Existing Codex/Claude subscriptions and local computer are allowed; no incremental spending.
- Q10: Proactive research is desired, ideally with the computer off, but user accepts explicitly prompting for research. Start with an on-demand path; investigate free proactive execution without promising computer-off delivery. This is a requirement preference, not authorization to enable a schedule now.
- Q8 remains unanswered: action briefing versus broad research roundup.

## Remaining product frontier

- Audience/access: private advice versus any sharing with league managers.
- Main research surface: subscription chat produces reports for the app versus an app button that actually dispatches an agent; availability of the latter must be verified.
- Briefing depth and decision style when evidence disagrees.
- ESPN action authority: advice versus user-approved execution; no trades/messages or mutations authorized by this interview.
- Initial release deadline and minimum useful slice.

## Accepted decisions: rounds 11–21

User accepted all recommendations in both rounds. These supersede corresponding open product questions above.

- Private app for the user and this league across seasons; other managers' rosters are research inputs, not access grants.
- Initiate research in Codex/Claude and save briefings/evidence for convenient app reading; an in-app dispatch button is not required initially.
- Give a preferred action, strongest counterargument and flip conditions. Hold is valid; missing evidence is disclosed.
- ESPN execution remains manual initially; research authorization does not authorize claims, lineup changes, trades or manager communications.
- Deliver a real research briefing before polishing the integrated UI.
- Research the full matchup and alternatives, lead with up to five actionable decisions; routine starters receive short status checks.
- Use claim-specific source standards: official/attributed factual reports and at least two independent forecasting perspectives for close decisions when available; disclose missing coverage and syndication.
- Separate immediate waiver improvements from contingent upside. Every proposed add names its drop and opportunity cost. Compare D/ST this week and next two weeks without automatically rostering two defenses.
- Evaluate trade opportunities weekly; surface zero to three supported proposals including both sides' gains, losses and reasons to decline.
- Briefing rhythm: post-games/pre-waivers, pregame lineup review, material injury/offer changes, and on demand. Exact timing follows verified league deadlines. Proactive execution remains a feasibility gate.
- Freeze reconciled actual draft picks and draft-time evidence by season; preserve current rosters separately; version explicit corrections and date retrospective analysis.

## New requirement: matchup prediction

User wants the recommended lineup for their matchup and a prediction of who wins. Home should connect lineup choices with matchup outlook. Presentation of projected score versus win probability, opponent-lineup assumptions, and treatment of uncertainty are the next frontier. No numerical win probability model is accepted or implemented yet.

## Accepted decisions: rounds 22–25

- Show recommended lineup, projected scores, favored team and agreement across sources. Numerical win probabilities wait for a defensible model and remain experimental until calibrated.
- Display opponent's actual lineup, but use an explicitly labeled estimated strongest legal lineup in the main pregame forecast; allow switching assumptions. Preserve locked players.
- Refresh the outlook with actual scores and unstarted-player projections. In-progress remaining production is unknown unless modeled; do not imply a complete final-score forecast from incomplete totals. No continuous live-score promise.
- Favor expected production; matchup-dependent risk changes require material relevance and supported outcome distributions.

## Shared-understanding checkpoint

Product scope settled; awaiting user confirmation of the consolidated summary. No more product questions are needed before the first researched briefing. Hosting, source access, incoming-offer lifecycle and waiver clock semantics are factual feasibility gates; notification channel/quiet-hour preferences can be selected when scheduling is actually deliverable. The first briefing has no dependency on those optional deployment choices. No runtime implementation, schedules or ESPN mutations were performed during the interview.
