# Initial season API contract

Local private app, four views: This Week / League / Moves / Draft. GET /api/v1/overview?season=2026&week=1 returns the complete normalized snapshot below (same JSON export used by agents). GET /api/v1/seasons returns {seasons:[2026]}. POST /api/v1/refresh with JSON {season:2026,week:1} refreshes ESPN read-only and returns new overview; protect same-origin server-side. GET /api/v1/briefing returns current briefing JSON. No ESPN writes. Route selections use query parameters (view,team,player,week,season). Backend has no other static assets beyond season/static allowlist.

Overview object:
```
{
 schema_version:1, snapshot_id:string, generated_at:ISO, data_as_of:ISO,
 stale:boolean, warnings:[string], season:2026, week:1,
 league:{id:number,name:string,my_team_id:5,timezone:'America/Chicago'},
 rules:{lineup_slots:[{id:0,label:'QB',count:1}],waiver_priority:10,waiver_hours:24,waiver_timing_verified:false,trade_review_hours:24,trade_deadline:ISO|null,scoring:[{stat_id:string,points:number}]},
 teams:[{id:number,name:string,abbrev:string,waiver_priority:number|null,roster:[PLAYER],submitted:LINEUP,recommended:LINEUP}],
 matchup:{id:number,my_team_id:5,opponent_team_id:number}|null,
 deadlines:[{id:string,label:string,at:ISO|null,verified:boolean,detail:string}],
 free_agents:[PLAYER],
 trade_inbox:{status:'empty'|'observed'|'unavailable',last_checked:ISO,capability_note:string,offers:[{id:string,type:string,status:string,team_id:number|null,items:[{player_id:number,name:string,from_team_id:number,to_team_id:number}],expires_at:ISO|null}]},
 source_health:[{name:string,status:'ok'|'limited'|'unavailable',detail:string,checked_at:ISO|null}],
 draft:{status:'frozen'|'unreconciled'|'in_progress',version:1,frozen_at:ISO|null,picks:[{overall:number,round:number,team_id:number,player_id:number,name:string,pos:string,ecr:number|null}],note:string},
 briefing:BRIEFING|null
}
PLAYER={id:number,name:string,pos:string,nfl_team:string,status:string,slot_id:number,slot:string,owner_id:number,eligible_slots:[number],projection:number|null,actual:number|null,kickoff:ISO|null,opponent:string|null,game_state:'pre'|'in'|'post'|'unknown',locked:boolean,availability:string,week_outlook:[{week:number,projection:number|null,opponent:string|null,kickoff:ISO|null}],outlook:string}
LINEUP={assignments:[{slot_id:number,slot:string,player_id:number}],projection:number|null,actual:number,remaining_projection:number|null,in_progress:boolean,complete:boolean,note:string}
BRIEFING={title:string,season:number,week:number,generated_at:ISO,snapshot_id:string,summary:string,coverage_note:string,decisions:[{id:string,title:string,recommendation:string,rationale:string,counterargument:string,flip_condition:string,player_ids:[number],source_ids:[string],status:string}],news:[{title:string,summary:string,player_ids:[number],source_ids:[string]}],sources:[{id:string,title:string,url:string,checked_at:ISO,published_at:string|null}],trade_ideas:[{title:string,benefit_us:string,benefit_partner:string,reason_to_decline:string,status:string}],watchlist:[{name:string,reason:string}]}
```
Briefing may be stale vs snapshot; UI must show its own generated time and use snapshot comparison to label 'Research predates this sync; recheck decisions'. Projections are ESPN league scoring only, not consensus. Recommended lineups are projection baselines, not independently researched picks. Opponent default recommended; allow submitted toggle. No win probability. When either forecast incomplete/in progress, do not name projected winner from incomplete totals. Player drawer via player query; escape all external data. All kickoff times America/Chicago. No fake data production fallback. Empty states explicit. Focused first release, source evidence via links and JSON export. No automatic research promise: user invokes subscription agent and imports briefing locally via CLI.
