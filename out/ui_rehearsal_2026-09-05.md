# UI rehearsal — September 5, 2026

Synthetic rehearsal used only http://127.0.0.1:18769/draft_terminal.html.
No ESPN draft selections were made. Existing draft-day/practice URL states
were not reset. The built-in opponent simulation is not ESPN's autopick engine.

## Verified through browser controls

- Pristine slot 3 / empty ledger / storage ready before starting.
- Recorded Gibbs, then Bijan: clock correctly reached 1.03.
- Thesis top 3 showed Chase first; numeric board remained Puka, McCaffrey,
  Chase. Chase is an explicit advisory preference, not an automatic pick or
  a rewritten model rank. The terminal queue is separate from ESPN's queue.
- Added Chase to queue. Ambiguous search `Chase` refused to record one of its
  three matches. Drafted Chase from queue, undid him, verified queue restoration,
  then drafted him again.
- At 22, Copy state was actually pasted through the browser into the search
  field and inspected, then cleared without recording. It included roster,
  league/scoring, candidates, twelve alternatives, and full ledger.
- In ECR audit mode, entering Nico Collins did not record a pick.
- Position filter and exact-name recording worked. Auto advancement stopped
  at all fourteen slot-3 turns. Simulated picks were flagged in UI and export.
- All 168 picks completed; roster had nine starters and five bench players,
  within caps, with K and DST selected at 147 and 166.
- Backup UI exposed parseable JSON with 168 picks. Invalid JSON was rejected.
- Opening a fresh tab at the same rehearsal origin restored the full ledger.
- Found and fixed misleading completed-draft labels: `15.01`, special-teams
  prompt after roster completion, and export still requesting a pick. Fresh-tab
  DOM and screenshot verified Complete / 14 of 14 / Roster complete labels.
- No console errors in fresh-tab verification.

## Example roster, not a recommendation or forecast

| Pick | Player |
|---:|---|
| 3 | Ja'Marr Chase |
| 22 | Kenneth Walker III |
| 27 | Brock Bowers |
| 46 | Jaylen Waddle |
| 51 | David Montgomery |
| 70 | Jaylen Warren |
| 75 | Caleb Williams |
| 94 | Jonathon Brooks |
| 99 | Jordan Mason |
| 118 | Kyle Monangai |
| 123 | De'Zhaun Stribling |
| 142 | Denzel Boston |
| 147 | Ka'imi Fairbairn |
| 166 | Ravens D/ST |

## Testing boundary

The in-app browser stalled on the native Reset confirmation. Reset and a valid
restore round trip were therefore not verified through UI. The isolated rehearsal
origin retains its synthetic ledger and must not be used for the live draft.
Copy/paste worked at pick 22; a later attempt after reconnecting hit a virtual
clipboard limitation. Export content is additionally checked by the automated
state-export test. This rehearsal verifies mechanics, not championship odds or
future player availability.

## Small improvements delivered

Export now carries ESPN default rank separately from ADP for the eight board
candidates and twelve consensus alternatives, plus queue/custom-ranking caveats.
Ranking weights and survival probabilities were not retuned. Completion labels
now reflect the finished draft. Engine and state-export regression checks passed.
