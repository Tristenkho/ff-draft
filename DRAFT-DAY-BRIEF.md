# Draft-day priming brief — reviewed September 5, 2026

Read this once before the first pick. Then paste only Copy state each turn.
Copy state now carries the room order, who picks between our turns, the 90-second
clock, and the effective per-catch scoring on its own, so a session started fresh
mid-draft is still usable from the export alone. This brief adds the reasoning
behind those facts and the September 5 decision notes.
Codex and Claude Code both read the repo instructions through AGENTS.md/CLAUDE.md.
The detailed evidence is in `out/draft_eve_audit_2026-09-05.md`.

You are the judgment layer for a live fantasy draft. The HTML is the only ledger.
Never invent or persist picks elsewhere. Give a **clear first choice and two
alternatives, one line of reasoning each**, with a short wait-on note when useful.
The clock is 90 seconds. Lead with the pick; do not re-run model research on clock.
Check current decision-changing player news and distinguish unverified facts.

## League and priorities

Sunday September 6, 7 p.m. CDT / 8 p.m. EDT. ESPN settings verified September 5.
12 teams, 14 rounds, snake, slot 3. Picks: 3, 22, 27, 46, 51, 70, 75, 94, 99,
118, 123, 142, 147, 166. QB1 RB2 WR2 TE1 FLEX1 K1 DST1; five bench, two IR.
Eight teams make playoffs, Weeks 15–17, one week per round.

Receiving first downs pay 0.5 on top of 0.5 PPR. Effective receiving points per
catch average WR 0.803, TE 0.766, RB 0.663. Rushing first downs pay 0.25 and
passing first downs 0.1. These are already included in projections. Do not add
another scoring bonus. Keep K/DST until rounds 13–14.

## Read the board critically

- **Model rank is not Pick Board order.** The board orders by eligibility, wait
  band, then ECR/Model/gain within a band. Same-band candidates are near-ties.
- **Consensus alternatives matter.** Copy state now includes twelve names
  outside the top eight, with policy-block reasons. Review those too.
- **The model favors QB and discounts many WR/contingent RBs.** Among same-pool
  ECR top 100, mean ECR-minus-Model gaps are QB +17.2, WR -9.2, RB -2.4, TE +3.9.
  First-down scoring only shifts the rescored flex pool by about WR/TE +1.3 and
  RB -2.8 on average. It does not explain every 20–40-rank disagreement.
- **Ceiling SD is a position-rate proxy.** Lambda does not meaningfully identify
  upside within a position. Expert rank dispersion is analyst disagreement,
  not measured player volatility. Late bench RBs need contingent-role judgment.
- **Survival is often too pessimistic in rounds 6–8.** In the single 2025 draft,
  mid-range predictions averaged 41–45% and observed survival 81–90%. Use this
  as directional room evidence, not a rule to double every probability. Early
  rounds were closer, but round 2 also had +13 percentage points of bias.
- **Reaches persist after refresh.** September 5 live-engine simulation, 300
  drafts: recommended skill picks averaged 6.6 picks ahead of ESPN ADP;
  16.4% were over five picks early with model survival above 50%. This does not
  prove all reaches are bad. Ask whether THIS player keeps and whether the
  better consensus player will disappear. Especially scrutinize rounds 7–12.

## The actual room

The 2025 draft had 19 K/DST picks out of 36 in rounds 7–9 and zero RBs. Exploit
that only if it repeats. QB10–12 went at 74/80/83, then none until 121. Eight
managers drafted QB2; waivers are not automatically a safe QB plan.

Kevin and Berds make **all four picks between 22 and 27**. Last year Kevin
started WR/RB/RB and Berds WR/TE/QB. Their actual rosters tomorrow matter more
than blindly repeating that history. Ray Rice waited on special teams and is
plausible competition for discounted skill players. One season is not a fixed
personality model.

Default QB review window remains 70/75. If punting past it, explicitly compare
remaining QBs and the 118/123 plan; the app's QB-by-round-10 and TE-by-round-9
rules are policy choices, not league rules. QB2 is blocked by the board but may
be discussed late if an insecure QB1 and weak waivers justify the bench cost.

## September 5 decision notes — re-check Sunday

- At 3, take an unexpected Gibbs/Bijan fall seriously. If both are gone, Chase
  remains the conditional preference while Puka ramps up from the groin issue.
  Do not assume a suspension or that practice clearance has occurred.
- Josh Allen: Model 14, ECR 26, ESPN ADP 19.1, market 30.6. Credible 22/27
  option after comparing the pair; not permission to sacrifice a major
  RB/WR faller. Model QB rank alone does not settle it.
- A.J. Brown: Model 24 vs ECR 13. Consider him seriously if he falls to 22;
  the scoring ablation does not justify that whole discount.
- Jeremiyah Love: Model 29 vs ECR 41, ankle recovery not resolved in the Sep 3
  report. Prefer healthier comparable options until current evidence changes.
- Parker Washington 83 vs 64, Godwin 100 vs 80, Downs 122 vs 97: do not let
  conservative projections make you miss consensus value. Check role/health.
- Corum 125 vs 88, Harvey 129 vs 98, Coleman 181 vs 138: late RB upside deserves
  more consideration than median season points alone.
- Lloyd is now ECR 89. Watch 94/99/118; the old 118–142-only plan is stale.
  Durability, competition and Jacobs' uncertain return remain material.
- Jacobs remains on the Exempt List. A September 10 hearing is not a return date.
- Likely said September 2 that he finished camp healthy. The foot-surgery note
  was from 2025, and Dart is a second-year QB. Do not repeat the stale warning.

## Before the first pick

Open the exact browser/URL you will use live. Verify September 5 or newer feed
and research dates, slot 3, storage ready, and an empty ledger. Reset any practice
picks first. Record every real pick, including ours, in the HTML. Paste an export
a couple of picks early when possible, then the current export on our turn.

## ESPN autopick — reviewed September 5

The terminal's queue does not sync to ESPN. For timeout protection, put Chase
first in the actual ESPN live queue once Gibbs/Bijan are gone. Saved ESPN
rankings apply when a live manager times out with no pending queued player.
Other managers' custom rankings/queues are unknown; never treat default rank
as a guaranteed selection order. Copy state includes default rank separately
from ADP for its eight candidates and twelve consensus alternatives.

Conditional default-autopick discounts: Watson ECR 57 / ESPN rank 81, Parker
Washington 64/87, Godwin 80/127, Downs 97/131. These support waiting only when
actual opponents, their roster needs, and the number of intervening picks
support it. An active manager can take any of them earlier. Allen illustrates
why rank and ADP must be distinct: ECR 26 / ESPN rank 26 / ESPN ADP 19.1.

ESPN sources:
- https://support.espn.com/hc/en-us/articles/360046492471-Updating-Your-Draft-Rankings-and-Strategy
- https://support.espn.com/hc/en-us/articles/360000140911-Online-Draft-Player-Queue


## First-principles review — September 5

The objective is usable lineup strength and a chance to win, not maximum VONA,
season-long bench points, or getting players below ADP. Consensus is the starting
comparison; departures need a concrete scoring, role, health, roster, or
opportunity-cost reason. Do not count first-down scoring or correlated sleeper
mentions as extra bonuses after they have already informed the inputs.

For starters compare usable lineup production. For bench players compare a
plausible path to starting value with the cost of a scarce bench slot. Position
SD does not identify individual upside, and the playoff format does not prove
that lambda 0.40 is optimal. Its value is unchanged pending meaningful evidence.

Removed the requirement that Smart Queue approve an early QB. It runs only at
22, screens six candidates, and uses the same uncertain inputs. It remains an
optional pair scenario tool and no longer replaces the main top-three display.
Compare QB-now plus later skill player against skill-player-now plus later QB.

Removed the three slot-specific RB eligibility deadlines at 27/51/75. Keep
those windows as reminders, but consider superior fallers when the roster can
still be completed. Existing broader core/lineup safeguards, legal caps, and
K/DST timing remain. One-QB/one-TE rules remain overrideable defaults; the claim
that a useful backup necessarily belongs on waivers has been removed.

These changes remove unsupported decision authority. They are not a measured
increase in championship probability; historical proxy results do not validate
that claim. The exported judgment instructions now state this decision order.

Validation: exact-engine checks passed, including faller visibility at 27/51/75,
preserved core/starter feasibility, and a legal full draft. State-export checks
passed. The aggregate suite needed a longer timeout; its separate 20-second
single-Smart-Queue limit remains and measured about eight seconds. The earlier
6.6-pick reach diagnostic predates removal of the slot-specific RB exclusions;
it is historical baseline evidence, not a new measurement of this revision.
