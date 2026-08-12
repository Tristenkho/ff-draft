/* Golden checks for the exact engine embedded in the single-file draft app. */
const assert=require('assert');
const crypto=require('crypto');
const fs=require('fs');
const vm=require('vm');

const html=fs.readFileSync(process.env.DRAFT_HTML||'out/draft_terminal.html','utf8');
const start=html.indexOf('const TEAMS=12, ROUNDS=14;');
const end=html.indexOf('// ── render ───────────────────────────────────────');
assert(start>=0&&end>start,'embedded draft engine not found');
const engine=html.slice(start,end);

const harness=`
function near(actual,expected,tolerance,label){
  if(Math.abs(actual-expected)>tolerance)throw new Error(label+': expected '+expected+', got '+actual);
}
function playerNamed(name){
  const player=PLAYERS.find(p=>p.name===name);
  if(!player)throw new Error('missing player: '+name);
  return player;
}
function autoOppUntilMineForTest(){
  const meta=modelMeta(),rosters=rostersFromDraft();
  while(picks.length<TEAMS*ROUNDS&&!myPicks().includes(curPick())){
    const n=curPick(),round=Math.ceil(n/TEAMS),roster=rosters[teamAtPick(n)-1];
    let candidates=remaining().filter(p=>modelDraftable(p)&&mockEligible(p,roster,true,round));
    if(!candidates.length)candidates=remaining().filter(p=>modelDraftable(p)&&mockEligible(p,roster,false,round));
    const selected=chooseNeedAware(candidates,roster,round,meta,false);
    if(!selected)throw new Error('opponent has no legal selection at '+n);
    picks.push(selected.id);roster.push(selected);
  }
}

slot=3;lambda=.40;ecrWeight=.35;autoPickNos=[];
const gibbs=playerNamed('Jahmyr Gibbs'),bijan=playerNamed('Bijan Robinson');
const puka=playerNamed('Puka Nacua'),chase=playerNamed("Ja'Marr Chase");
picks=[gibbs.id,bijan.id];
const opening=computeBoard(),pukaRow=opening.find(r=>r.p.id===puka.id),chaseRow=opening.find(r=>r.p.id===chase.id);
if(opening[0].p.id!==puka.id)throw new Error('golden 1.03 recommendation is not Puka');
const expectedTopEight=['Puka Nacua',"Ja'Marr Chase",'Christian McCaffrey','Amon-Ra St. Brown',
  'Jaxon Smith-Njigba','Jonathan Taylor',"De'Von Achane",'Derrick Henry'];
if(JSON.stringify(opening.slice(0,8).map(r=>r.p.name))!==JSON.stringify(expectedTopEight))
  throw new Error('golden 1.03 top eight changed unexpectedly');
near(puka.proj,317.9,.05,'Puka projection');near(chase.proj,307.4,.05,'Chase projection');
near(puka.sd,73.1,.05,'Puka ceiling proxy');near(chase.sd,70.7,.05,'Chase ceiling proxy');
near(pukaRow.v,347.14,.02,'Puka value');near(chaseRow.v,335.68,.02,'Chase value');
near(pukaRow.gain,97.79,.02,'Puka VONA');near(chaseRow.gain,86.33,.02,'Chase VONA');
if(Math.abs((pukaRow.gain-chaseRow.gain)-(pukaRow.v-chaseRow.v))>1e-8)
  throw new Error('same-position VONA baseline did not cancel');
if(pukaRow.vonaTier!==1||chaseRow.vonaTier!==1)
  throw new Error('Puka/Chase should remain an uncertainty-tier tie');
if(puka.adp_sd_source!=='FFC observed'||chase.adp_sd_source!=='FFC observed')
  throw new Error('top-player survival is not using observed market dispersion');
if(ECR_META.updated7d!==ECR_META.experts||ECR_META.updated1d>ECR_META.updated3d||ECR_META.updated3d>ECR_META.updated7d||ECR_META.experts<20)
  throw new Error('FantasyPros panel recency metadata is invalid');
near(puka.ecr_mean,4,.01,'Puka expert mean');near(puka.ecr_sd,1.35,.01,'Puka expert SD');
near(chase.ecr_mean,2.73,.01,'Chase expert mean');near(chase.ecr_sd,1.09,.01,'Chase expert SD');
if(puka.ecr_min!==1||puka.ecr_max!==9||chase.ecr_min!==1||chase.ecr_max!==5)
  throw new Error('expert rank ranges are missing');
near(puka.room_rank,.70*puka.adp+.30*puka.espn_rank,.11,'Puka ESPN-only room rank');
near(chase.room_rank,.70*chase.adp+.30*chase.espn_rank,.11,'Chase ESPN-only room rank');
const timingBefore=timingMetric(puka),ecrBefore=puka.ecr;
puka.ecr=250;
near(timingMetric(puka),timingBefore,1e-12,'ECR leaked into timing');
puka.ecr=ecrBefore;
if(puka.sd_source!=='position-rate proxy'||chase.sd_source!=='position-rate proxy')
  throw new Error('ceiling proxy provenance is missing');
near(timingSd(puka),.6,1e-9,'Puka observed timing SD');
near(timingSd(chase),.9,1e-9,'Chase observed timing SD');
near(survives(puka,3.6,new Map([[puka.id,3]])),.158655,1e-5,'observed-SD survival formula');
if(!puka.proj_sources?.ESPN||!puka.proj_sources?.CBS||!puka.proj_sources?.FFToday)
  throw new Error('projection source audit trail is incomplete');
const ecrMeta=modelMeta(),skillEcrRanks=skillPool().map(p=>ecrMeta.ecrRank(p));
if(Math.max(...skillEcrRanks)>skillPool().length)
  throw new Error('ECR was not normalized to the skill-player rank scale');

const oldStatus=puka.status;
puka.status='OUT';picks=[gibbs.id,bijan.id];
const outRow=computeBoard().find(r=>r.p.id===puka.id);
puka.status=oldStatus;
if(outRow.eligible||outRow.surv!==0||outRow.vonaTier!==999)
  throw new Error('unavailable player leaked into recommendation/forecast modeling');

picks=[];autoPickNos=[];autoOppUntilMineForTest();
const selected=[];
for(let round=1;round<=ROUNDS;round++){
  const rec=computeBoard()[0];
  if(!rec?.eligible)throw new Error('no eligible recommendation in round '+round);
  picks.push(rec.p.id);selected.push(rec.p);
  autoOppUntilMineForTest();
}
const counts=rosterCounts(selected);
if(selected.length!==14||counts.QB!==1||counts.TE!==1||counts.K!==1||counts.DST!==1||counts.RB+counts.WR!==10)
  throw new Error('deterministic draft produced an invalid final roster');
if(Math.min(counts.RB,counts.WR)<4)throw new Error('deterministic draft violated RB/WR balance');
if(!['K','DST'].includes(selected[12].pos)||!['K','DST'].includes(selected[13].pos)||selected[12].pos===selected[13].pos)
  throw new Error('K/DST were not reserved for rounds 13-14');
const finalLeague=rostersFromDraft();
if(!finalLeague.every(roster=>{
  const c=rosterCounts(roster);
  return roster.length===ROUNDS&&c.QB>=1&&c.RB>=2&&c.WR>=2&&c.TE>=1&&c.K===1&&c.DST===1
    &&Object.keys(CAPS).every(pos=>c[pos]<=CAPS[pos]);
}))throw new Error('need-aware opponents did not produce legal final rosters');

globalThis.TEST_RESULT={
  lambda:currentLambda(),
  replacement:replacement(skillPool()).rep,
  pick3:opening.slice(0,8).map(r=>({name:r.p.name,pos:r.p.pos,vona:+r.gain.toFixed(2),tier:r.vonaTier,model:r.modelRank})),
  puka:{projection:puka.proj,value:+pukaRow.v.toFixed(2),vona:+pukaRow.gain.toFixed(2),tier:pukaRow.vonaTier,market:puka.market_adp,marketSd:puka.adp_sd},
  chase:{projection:chase.proj,value:+chaseRow.v.toFixed(2),vona:+chaseRow.gain.toFixed(2),tier:chaseRow.vonaTier,market:chase.market_adp,marketSd:chase.adp_sd},
  expertPanel:ECR_META,
  deterministicBuild:counts,
  deterministicPicks:selected.map(p=>p.name)
};
`;

const context={
  console,Math,Map,Set,Array,Object,JSON,Date,
  localStorage:{getItem:()=>null,setItem:()=>{}},
  document:{querySelector:()=>({classList:{toggle:()=>{}},textContent:'',innerHTML:'',value:'',style:{}})},
};
vm.createContext(context);
vm.runInContext(engine+'\n'+harness,context,{timeout:30000});
const result=context.TEST_RESULT;
result.engineSha256=crypto.createHash('sha256').update(engine).digest('hex');
assert(!html.includes('id="auto"'),'live Auto control must not mutate the real ledger');
assert(!html.includes('function autoToMyPick'),'legacy Auto mutation path returned');
assert(engine.includes('Math.abs(modelRank-ecrRank)')&&!engine.includes('Math.abs(modelRank-p.ecr)'),
  'review gate must compare Model with skill-pool ECR on the same rank scale');
assert(html.includes('row&&decisionInputActive()'),'non-Pick-Board rows are not guarded as read-only');
assert(html.includes("if($('#help').classList.contains('on'))"),'keyboard actions are not guarded behind Help');
assert(html.includes('role="dialog" aria-modal="true" aria-labelledby="helptitle"'),
  'Help is not exposed as a modal dialog');
assert(html.includes("$('#app').setAttribute('inert','')")&&html.includes('function draftLocked()'),
  'Help does not hard-lock the draft surface');
assert(html.includes('id="helpbody" tabindex="0"')&&html.includes("const stops=[$('#helpclose'),$('#helpbody')]"),
  'Help does not provide a scrollable, trapped keyboard surface');
assert(html.includes('function waitBandLabel(tier)')&&html.includes('>Wait Cost</div>'),
  'Pick Board wait-band presentation is missing');
assert(html.includes('data-board-view')&&html.includes('ECR &minus; Model'),
  'mobile audit metric or ECR/Model comparison presentation is missing');
assert(html.includes('const show=rows2;')&&html.includes('visibleRows=show.slice(0,8);')&&
  html.includes('.board{flex:1;min-height:0;overflow:auto'),
  'full ranking is not scrollable while hotkeys remain limited to the top eight');
assert(!html.includes('NEWS today')&&!/NEWS \d+d/.test(html)&&html.includes('ESPN update ${NEWS_MONTHS'),
  'news recency is not shown as a neutral exact-date stamp');
assert(/grid-template-columns:repeat\(4,minmax\(0,1fr\)\)/.test(html),'mobile footer button grid is stale');
console.log(JSON.stringify(result,null,2));
