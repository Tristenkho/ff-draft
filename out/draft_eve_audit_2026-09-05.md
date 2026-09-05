# Draft-eve audit — September 5, 2026

The feeds are refreshed and the league settings match ESPN. The model is useful for scoring, roster construction and timing questions, but its departures from consensus are not uniformly justified. No evidence here establishes a championship-probability improvement from changing model weights the day before the draft.

## Verified league configuration

Authenticated ESPN `mSettings`, `mTeam`, and `mRoster` retrieved September 5: the entire settings object equals the saved `out/espn_league.json` snapshot. Draft is September 6 at 7 p.m. CDT / 8 p.m. EDT. ESPN timestamp is September 7 00:00 UTC. Twelve-team snake, slot 3, 90 seconds, 14 selections; QB1/RB2/WR2/TE1/FLEX1/K1/DST1, five bench, two IR. Position caps match. Eight teams make Weeks 15–17 playoffs, one week per round. Traditional waivers, weekly reset, no FAAB, 24-hour waiver period.

All 49 scoring entries match the stored settings, including receiving first downs 0.5, rushing first downs 0.25, passing first downs 0.1, receptions 0.5, passing TDs 4, and the league's field-goal and DST tiers. The ensemble applies the major skill scoring rules; ESPN supplies league-scored K/DST projections. Non-ESPN feeds do not project every rare return/recovery/two-point event, so an exact projection of every scoring category is not claimed.

## Refreshed evidence

282 players; 218 skill players. All four projection feeds and independent Sleeper availability retrieved September 5. Four-source coverage is 203/218; at least two sources for 217/218. FFC timing contains 2,879 drafts through September 5. FantasyPros Latest half-PPR ECR contains 134 experts updated within seven days, 42 within one day and 94 within three. Retrieval today does not mean every expert or underlying projection was revised today.

The app retains 282 players, including unavailable players for bookkeeping. Jacobs, Charbonnet, Dell, Pacheco, Tyson and Higgins are excluded from model recommendations under current status/coverage gates. OUT/IR is an availability gate, not proof of a season-long absence; a late IR stash needs explicit status and roster review.

## Model versus ECR

Ranks below are overall Model evaluation ranks, **not live Pick Board order**. The board adds wait bands and roster eligibility. Gap = ECR re-ranked within the same draftable QB/RB/WR/TE pool minus Model rank; positive means the model likes the player more. Published ECR is shown separately. Default settings: lambda 0.40, ECR blend 35%.

| Player | Model | Published ECR | Same-pool gap | Judgment |
| --- | ---: | ---: | ---: | --- |
| Puka Nacua | 3 | 4 | +1 | Small scoring/projection difference; Chase remains the health-risk preference at 3 pending Sunday news. |
| Josh Allen | 14 | 26 | +12 | Elite QB case is credible; Model 14 is not a reason to pay pick 14. Compare the 22/27 pair and the remaining RB/WR. |
| Derrick Henry | 13 | 21 | +8 | Production bet, not a first-down scoring edge (zero flex-rank change in scoring ablation). Fair faller at 22; avoid manufacturing a reach. |
| A.J. Brown | 24 | 13 | -11 | Not justified by first downs (only -1 flex rank). Projection uncertainty/new situation may explain caution; give ECR more weight if he falls to 22. |
| Jeremiyah Love | 29 | 41 | +12 | Insufficient justification while ankle recovery remains unresolved. Four sources span 207–273 points; prefer healthier comparable talent. |
| Jaxson Dart | 61 | 99 | +38 | Large QB positional premium. Draft-window evidence matters more than Model 61; ESPN 83 is much earlier than market 123. |
| Tyler Shough | 94 | 131 | +37 | Useful late-QB candidate, but the 37-rank premium is not a validated edge. Revisit at 118/123 if deliberately waiting on QB. |
| Parker Washington | 83 | 64 | -19 | Model is conservative about breakout/volume. Reasonable consensus challenge at 70/75; national market 63 means 94 is only a faller scenario. |
| Chris Godwin Jr. | 100 | 80 | -20 | Health history and source spread explain some caution; a 20-rank fade is not explained by scoring. Consider 75/94/99 based on the board. |
| Josh Downs | 122 | 97 | -25 | Calf and target competition justify caution, not an automatic 25-rank rejection. Consider 99/118/123 with a current news check. |
| Blake Corum | 125 | 88 | -37 | A known projection limitation: season totals understate contingent starter value. Scoring costs only 4 flex ranks, not the full 37-place gap. |
| RJ Harvey | 129 | 98 | -31 | Similar contingent-RB issue; first downs cost 6 flex ranks, not the full 31-place gap. Prefer ECR/upside scrutiny for a bench selection. |
| MarShawn Lloyd | 103 | 89 | -14 | Current role supports a bump. Now ECR 89; the old 118–142-only watch window is stale. Consider 94/99 and 118 only if he lasts. |
| Jonah Coleman | 181 | 138 | -43 | Model 181 misses much of the contingent-upside thesis. ECR 138 warrants late bench review, not a guaranteed breakout. |

Among players in the top 100 of the same-pool ECR, mean gaps are QB +17.2 (13 players), RB -2.4 (36), WR -9.2 (42), TE +3.9 (9). This is a snapshot comparison, not evidence that ECR is always right. The older brief's claim of near-agreement everywhere important was too broad.

A 25-rank conflict flag is a review prompt, not a guarantee that the higher-consensus player wins: wait bands still come first, and the current same-band comparator uses ECR directly. The conservative decision-rank field does not override this ordering.

The actual ranking formula helps explain the QB premium: core score subtracts only 80% of positional replacement points. Relative to full value-over-replacement, it leaves an extra 20% of the baseline: QB +62.4 points, RB +36.0, WR +36.0, TE +29.0. This is a mechanical positional premium, not a player-specific insight. Diagnostic full-VOR core ranks move Dart from 44 to 69 and Shough from 79 to 109. This ablation explains the mechanism; it does not validate a replacement-weight change, and none was made.

The scoring ablation rescored 217 players, with 162 in the projection-over-80 RB/WR/TE comparison pool. Average first-down effects were WR +1.3 rank, TE +1.3 and RB -2.8 versus the same projections scored as ordinary half-PPR. This is **not** an ECR backtest. Effective receiving points per catch average WR 0.803, TE 0.766, RB 0.663. Rushing first downs still help RBs. These bonuses are already included; adding another manual WR premium double-counts them.

Ceiling SD remains a rounded position-rate proxy. Lambda cannot meaningfully distinguish upside between two players at the same position, although it can change cross-position ordering and draft behavior. Expert rank range measures analyst disagreement, not a calibrated player outcome distribution. For bench RBs, explicitly consider the value of becoming a starter; low median volume alone is insufficient to reject them.

## The room: observations, not personality predictions

Recounted all 168 picks in `out/league_draft_2025.json`. Rounds 7–9 contained 19 K/DST picks out of 36, and zero RBs. QB10–12 went at 74/80/83; the next QB was 121. Eight managers drafted a backup QB; 21 QBs total. This supports patient skill-player selection during a special-teams run and cautions against assuming strong QB waivers. It does not guarantee the same behavior in 2026.

| 2026 slot / manager | 2025 first QB round | First TE round | K / DST rounds | Actionable observation |
| --- | ---: | ---: | --- | --- |
| 1 / berds | 3 | 2 | 9 / 8 | TE then QB in rounds 2/3 last year. |
| 2 / kevin | 4 | 6 | 8 / 7 | RB/RB in 2/3; one of only two managers between our 22 and 27. |
| 3 / tristen | 4 | 3 | 9 / 8 | Our own past K/DST picks in 8/9 are the behavior to improve. |
| 4 / castelani | 4 | 3 | 8 / 9 | Three TEs; early K/DST. Do not copy those runs. |
| 5 / kyle | 1 | 5 | 9 / 7 | Only first-round QB in this draft. |
| 6 / hotdogs | 4 | 14 | 9 / 7 | Three WRs in rounds 4–6, TE waited until 14. |
| 7 / deshaun | 4 | 8 | 9 / 7 | Three WRs in first five rounds; K/DST 7/9. |
| 8 / worthy | 7 | 12 | 14 / 9 | Three RBs by round 5; no backup QB. |
| 9 / matthew | 7 | 6 | 8 / 13 | Three RBs by round 5, QB in round 7. |
| 10 / capullo | 7 | 6 | 14 / 8 | RB/RB opener and third RB in round 5. |
| 11 / rayrice | 5 | 7 | 14 / 13 | Waited until 13/14 for special teams; likely skill-player competition if repeated. |
| 12 / sweet | 2 | 5 | 8 / 7 | QB in round 2 plus two backups; do not count on late QB depth remaining. |

There are four intervening picks between 22 and 27, all by Kevin and Berds. This is more useful than treating every opponent as equally likely to select a particular position. Watch their actual first two selections. On the long 3→22 and 27→46 gaps, all eleven opponents matter.

Re-running the historical survival check reproduced the largest underprediction in rounds 6–8: mid-range predicted averages 40.9%, 45.1%, 45.2% versus observed 81.2%, 83.8%, 90.0%. The earlier "rounds 1–5 all within four points" claim is inaccurate: round 2 bias is +12.6 points. Do not literally double every survival probability. One draft and interdependent managers cannot support a precise universal correction.

Fresh live-engine simulation: 300 randomized drafts, 3,600 skill picks, mean pick-minus-ESPN-ADP -6.58, median -6.20. 16.36% of selections were over five picks early while the model itself assigned over 50% survival. Round means 1–12: -2.1, 0.0, -6.1, -3.2, -1.2, +1.6, -11.4, -5.0, -12.4, -8.9, -9.6, -20.8. This is a diagnostic against simulated opponents, not an estimate of championship odds or proof that every reach loses value. The refreshed tendency supports checking who can wait, especially late.

## Current news and reviewed target watch

- Chase remains the conditional pick-3 preference when Gibbs/Bijan are gone while Puka ramps up. Puka was working separately August 31 and was reported progressing September 4; no suspension or return date is assumed. [RotoWire](https://www.rotowire.com/football/player/puka-nacua-16790), [September 4 report](https://ca.sports.yahoo.com/news/puka-nacua-making-progress-204759353.html).
- Love was still recovering from his ankle injury in the September 3 report. That weakens the case for following Model 29 over ECR 41. [RotoWire update](https://www.rotowire.com/football/headlines/jeremiyah-love-injury-continues-to-progress-636168).
- Jacobs remains on the Exempt List. The hearing moved to September 10; that is not a clearance date. [NFL/AP September 4](https://amp.nfl.com/news/packers-rb-josh-jacobs-initial-court-appearance-moved-up-to-sept-10).
- Lloyd is a credible early-role bet, with durability, competition and Jacobs-return uncertainty. Move the watch window to 94/99/118. [Packers September 2](https://www.packers.com/news/rb-marshawn-lloyd-as-ready-as-he-s-ever-been-to-help-packers-sep-2-2026), [4for4-derived September 4 review](https://www.bleachernation.com/fantasy-football-sleepers/).
- Likely's old foot-warning was stale: he said September 2 that he finished camp healthy; Dart is in his second year. [Giants transcript](https://www.giants.com/news/quotes-9-2-gm-joe-schoen-coach-john-harbaugh-te-isaiah-likely-cb-greg-newsome-ii), [FantasyPros TE targets](https://www.fantasypros.com/2026/08/fantasy-football-draft-cheat-sheet-rankings-targets-2026/). A 118/123 TE plan remains a deliberate override of the app's round-9 deadline, not its default.
- Watson and Godwin retain independent support; Watson's market price already reflects breakout enthusiasm. Godwin's review window is now 75/94/99. [CBS WR tiers](https://secure-www.cbssports.com/fantasy/football/news/jamey-eisenberg-wide-receiver-rankings-2026-wr-tiers/), [FantasyPros target list](https://www.fantasypros.com/2026/08/fantasy-football-draft-cheat-sheet-rankings-targets-2026/).
- Washington remains a 70/75 target, with 94 only if he falls. [Fantasy Life](https://www.fantasylife.com/articles/fantasy/fantasy-football-rankings-my-guys-from-our-2026-fantasy-rankings), [CBS sleepers](https://new.cbssports.com/fantasy/football/news/jamey-eisenberg-sleepers-fantasy-football-2026/).
- Brooks/Mason retain upside support, not a score bonus. [PFF RB sleepers](https://www.pff.com/news/fantasy-football-sleeper-running-backs-2026), [September 4 value review](https://www.bleachernation.com/fantasy-football-sleepers/). Brooks' injury history and Mason's receiving limitations remain relevant.
- Downs remains conditional at 99/118/123; calf and target competition warrant a final check. [RotoWire](https://www.rotowire.com/football/player/josh-downs-16689), [CBS sleepers](https://new.cbssports.com/fantasy/football/news/jamey-eisenberg-sleepers-fantasy-football-2026/).
- Shough remains a deliberate late-QB option. [PFF](https://www.pff.com/news/fantasy-football-breakout-quarterbacks-2026), [CBS](https://secure-www.cbssports.com/fantasy/football/news/2026-fantasy-football-deep-sleepers-projections/).
- Rodriguez and Boston remain late upside watches. [NFL target list](https://www.nfl.com/news/2026-nfl-fantasy-football-six-late-round-sleepers-to-target), [CBS](https://new.cbssports.com/fantasy/football/news/jamey-eisenberg-sleepers-fantasy-football-2026/), [FanDuel](https://www.fanduel.com/research/4-deep-sleepers-for-2026-fantasy-football-drafts). These are contingent bets, not guaranteed starters.

Source families can share information or contribute to ECR; two mentions are corroboration, not two independent statistical votes. Review dates certify today's review, not a new article publication date.

## Shipped changes and validation

Refreshed all numeric data and reviewed watch dates/windows/risks. Copy state now includes twelve additional consensus candidates outside the top eight, explicit policy-block labels, unavailable consensus names, the measured calibration limitations, and corrected news context. Fixed the export's stale description of the same-band ordering. Updated the priming brief so tomorrow's judgment layer sees these findings.

No changes to VONA, survival formula, ranking weights, roster guardrails, or K/DST rounds. The historical championship backtest uses a proxy engine and post-selected policies, so old championship improvement claims do not justify a last-minute formula change.

Validated with engine checks, executable state-export checks (distinct alternatives, no drafted/unavailable candidates in the alternatives, policy labels, no state writes), the 300-draft live-engine simulation, scoring ablation, historical survival rerun, Python compilation, diff checks, and browser rendering/copy-button feedback. Browser origins inspected contained existing practice ledgers; these were preserved. Before tomorrow's first pick, reset practice picks in the exact browser/URL you will use and confirm an empty ledger and slot 3.

Reproduce the full player comparison with `node scripts/audit_model_ecr.js`; it emits every draftable skill player's Model/core/ECR ranks, source projections, timing prices and a diagnostic full-VOR rank. Raw simulation output stays uncommitted.
