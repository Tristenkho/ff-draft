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
if(opening.length<8||new Set(opening.slice(0,8).map(r=>r.p.id)).size!==8||
  !opening.slice(0,8).every(r=>r.eligible))
  throw new Error('opening board does not provide eight distinct eligible candidates');
if(!Number.isFinite(puka.proj)||!Number.isFinite(chase.proj)||puka.proj<=0||chase.proj<=0)
  throw new Error('opening-player projections are missing');
near(puka.sd,puka.proj*.23,.05,'Puka ceiling proxy');
near(chase.sd,chase.proj*.23,.05,'Chase ceiling proxy');
if(!Number.isFinite(pukaRow.v)||!Number.isFinite(chaseRow.v)||
  !Number.isFinite(pukaRow.gain)||!Number.isFinite(chaseRow.gain))
  throw new Error('opening-player value or VONA is missing');
if(Math.abs((pukaRow.gain-chaseRow.gain)-(pukaRow.v-chaseRow.v))>1e-8)
  throw new Error('same-position VONA baseline did not cancel');
if(puka.adp_sd_source!=='FFC observed'||chase.adp_sd_source!=='FFC observed')
  throw new Error('top-player survival is not using observed market dispersion');
if(ECR_META.updated7d!==ECR_META.experts||ECR_META.updated1d>ECR_META.updated3d||ECR_META.updated3d>ECR_META.updated7d||ECR_META.experts<20)
  throw new Error('FantasyPros panel recency metadata is invalid');
for(const p of [puka,chase])if(!Number.isFinite(p.ecr_mean)||!Number.isFinite(p.ecr_sd)||
  !Number.isInteger(p.ecr_min)||!Number.isInteger(p.ecr_max)||p.ecr_min>p.ecr_max)
  throw new Error('expert distribution fields are missing');
near(puka.room_rank,.70*puka.adp+.30*puka.espn_rank,.11,'Puka ESPN-only room rank');
near(chase.room_rank,.70*chase.adp+.30*chase.espn_rank,.11,'Chase ESPN-only room rank');
const timingBefore=timingMetric(puka),ecrBefore=puka.ecr;
puka.ecr=250;
near(timingMetric(puka),timingBefore,1e-12,'ECR leaked into timing');
puka.ecr=ecrBefore;
if(puka.sd_source!=='position-rate proxy'||chase.sd_source!=='position-rate proxy')
  throw new Error('ceiling proxy provenance is missing');
if(!(timingSd(puka)>0&&timingSd(chase)>0))throw new Error('observed timing SD is missing');
const survivalCheck=survives(puka,3.6,new Map([[puka.id,3]]));
if(!(survivalCheck>0&&survivalCheck<1))throw new Error('survival formula returned an invalid probability');
if(!puka.proj_sources?.ESPN||!puka.proj_sources?.CBS||!puka.proj_sources?.FFToday)
  throw new Error('projection source audit trail is incomplete');
const ecrMeta=modelMeta(),skillEcrRanks=skillPool().map(p=>ecrMeta.ecrRank(p));
if(Math.max(...skillEcrRanks)>skillPool().length)
  throw new Error('ECR was not normalized to the skill-player rank scale');

// Projection audit fields are labels for judgment, not a second hidden pick
// score. Keep the point estimate, source range, source identities, and the
// generic ceiling proxy visibly and semantically distinct.
const bowers=playerNamed('Brock Bowers'),mcbride=playerNamed('Trey McBride');
for(const p of [puka,chase,bowers,mcbride]){
  const sources=Object.keys(p.proj_sources||{});
  if(!Number.isInteger(p.proj_n)||p.proj_n<2||sources.length!==p.proj_n||
    !Number.isFinite(p.proj_low)||!Number.isFinite(p.proj_high)||
    p.proj_low>p.proj||p.proj>p.proj_high)
    throw new Error('projection audit range is incomplete for '+p.name);
  const audit=projectionText(p);
  if(!audit.includes(p.proj_n+'-source '+PROJECTION_META.method)||
    audit.includes('HIGH confidence')||audit.includes('LOW confidence')||
    !audit.includes(p.proj_low.toFixed(0)+'–'+p.proj_high.toFixed(0)))
    throw new Error('projection audit naming/range is not honest for '+p.name);
  const sourceText=projectionSourcesText(p);
  if(!['ESPN','CBS','FFToday'].every(name=>sourceText.includes(name)))
    throw new Error('projection source names are missing for '+p.name);
  if(!Number.isFinite(p.proj_unc)||p.proj_unc<=0||p.sd_source!=='position-rate proxy')
    throw new Error('projection confidence and ceiling provenance are conflated for '+p.name);
}
// A large model/ECR disagreement must be visible and conservative. This is
// deliberately a rank-scale contract; it does not assert any particular
// player or change the underlying ECR weight.
picks=[chase.id];
const conflictRows=computeBoard().filter(r=>r.needsReview);
const conflict=conflictRows.find(r=>r.ecrRank<=500&&Math.abs(r.modelRank-r.ecrRank)>=25);
if(!conflict||conflict.decisionRank!==Math.max(conflict.modelRank,conflict.ecrRank)||
  !why(conflict).includes('REVIEW gate uses conservative rank')||
  !['projection-led','consensus-led'].some(label=>conflictSignal(conflict).includes(label))||
  !conflictSignal(conflict).includes('rank gap'))
  throw new Error('Model/ECR conflict flag or conservative decision gate is missing');

if(!ecrEvidenceText(bowers).includes('expert avg')||!ecrEvidenceText(bowers).includes('range'))
  throw new Error('ECR evidence wording does not expose expert average and range');
const qbEarly=computeBoard().find(r=>r.p.pos==='QB'&&r.eligible);
if(!qbEarly||why(qbEarly).includes('starter need'))
  throw new Error('early QB/TE onesie was treated as a required starter need');

// The turn-pair planner should distinguish players who are conditional fallers
// from realistic 22/27 targets using the timing/survival signal. It must not
// turn an early conditional faller into a recommendation merely because the
// player has a large projection.
// This is the Chase turn snapshot used by the planner: the two opponents
// before 1.03, Chase at my first pick, then one opponent selection before the
// read-only 22/27 forecast is rendered.
const love=playerNamed('Jeremiyah Love');
picks=[gibbs.id,bijan.id,chase.id,love.id];
const pairRows=computeBoard();
const conditionalFaller=pairRows.filter(r=>r.eligible&&!r.isSpecial&&r.p.market_adp<15)
  .sort((a,b)=>a.p.market_adp-b.p.market_adp)[0];
const realisticFaller=pairRows.filter(r=>r.eligible&&!r.isSpecial&&r.p.market_adp>=20&&r.p.market_adp<=35&&r.surv>.20)
  .sort((a,b)=>a.p.market_adp-b.p.market_adp)[0];
if(!conditionalFaller||!realisticFaller||
  !(timingMetric(conditionalFaller.p)<timingMetric(realisticFaller.p))||
  !(conditionalFaller.surv<.05&&realisticFaller.surv>conditionalFaller.surv))
  throw new Error('realistic and conditional fallers are not separated by timing/survival');

if(SAME_BAND_TIEBREAK!=='consensus')
  throw new Error('same-band planner tiebreak is not explicitly consensus-first');
const turnPairBefore=JSON.stringify(picks),turnPairText=turnPairPlanner(pairRows);
if(JSON.stringify(picks)!==turnPairBefore||!turnPairText.includes('1.03 turn planner')||
  !turnPairText.includes('picks 22/27')||!turnPairText.includes('read-only advisory')||
  !turnPairText.includes('Pick 22 targets')||!turnPairText.includes('Likely pick 27 survivors')||
  !turnPairText.includes('Use the 22 list for first-pick planning'))
  throw new Error('read-only separate-pool turn-pair planner is missing or mutating state');

const plannerForecast=remaining().filter(modelDraftable);
const plannerRanked=new Map([...plannerForecast]
  .sort((a,b)=>timingMetric(a)-timingMetric(b)||a.id-b.id)
  .map((p,i)=>[p.id,curPick()+i]));
const plannerRows=pairRows.filter(r=>r.eligible&&!r.isSpecial).map(r=>({...r,
  s22:survives(r.p,22,plannerRanked),s27:survives(r.p,27,plannerRanked)}));
const planner22Core=plannerRows.filter(r=>r.s22>=.30&&(r.p.pos==='RB'||r.p.pos==='WR'))
  .sort(boardDecisionCompare);
const planner27Core=plannerRows.filter(r=>r.s27>=.30&&(r.p.pos==='RB'||r.p.pos==='WR'))
  .sort(boardDecisionCompare);
const pairStart=turnPairText.indexOf('<b>Pair ideas</b>');
const pairEnd=turnPairText.indexOf('<br><b>Conditional fallers</b>');
const pairSection=pairStart>=0?turnPairText.slice(pairStart,pairEnd>=0?pairEnd:turnPairText.length):'';
if(pairStart<0||!planner22Core.some(r=>pairSection.includes(r.p.name))||
  !planner27Core.some(r=>pairSection.includes(r.p.name)))
  throw new Error('turn-pair ideas do not combine separate pick-22 and pick-27 target pools');
if(PLAYERS.filter(p=>p.pos==='QB').some(p=>pairSection.includes(p.name)))
  throw new Error('turn-pair ideas incorrectly include a QB pair');
const tePairStart=pairSection.indexOf('TE pivot:');
const tePairText=tePairStart>=0?pairSection.slice(tePairStart):'';
const bowersRow=plannerRows.find(r=>r.p.name==='Brock Bowers');
const mcbrideRow=plannerRows.find(r=>r.p.name==='Trey McBride');
const teOverlap=bowersRow&&mcbrideRow&&Number.isFinite(bowersRow.p.proj_low)&&
  Number.isFinite(bowersRow.p.proj_high)&&Number.isFinite(mcbrideRow.p.proj_low)&&
  Number.isFinite(mcbrideRow.p.proj_high)&&
  Math.max(bowersRow.p.proj_low,mcbrideRow.p.proj_low)<=Math.min(bowersRow.p.proj_high,mcbrideRow.p.proj_high);
if(teOverlap&&bowersRow.s22>=.30&&mcbrideRow.s22>=.30&&
  (!tePairText.includes('TE pivot: Brock Bowers')||tePairText.includes('TE pivot: Trey McBride')))
  throw new Error('overlapping elite-TE projections did not prefer Bowers in the pair advisory');
if(!turnPairText.includes('Balanced core: Chris Olave + Kyren Williams')||
  !turnPairText.includes('TE pivot: Brock Bowers + Kyren Williams'))
  throw new Error('Chase turn scenario did not produce the Olave/Kyren and Bowers/Kyren pair plan');
const expectedMiracles=plannerRows.filter(r=>r.modelRank<90&&r.s22<.15)
  .sort((a,b)=>a.modelRank-b.modelRank).slice(0,5);
if(expectedMiracles.length&&(!turnPairText.includes('Conditional fallers')||
    !turnPairText.includes(expectedMiracles[0].p.name)))
  throw new Error('conditional fallers are not based on survival to pick 22');

// Auto-to-my-pick in the planning bar is a read-only turn-pair preview. Use a
// valid opening ledger, stub only rendering, and prove that neither real picks
// nor the simulated-pick ledger are mixed into one another.
const plannerOpening=[gibbs.id,bijan.id,chase.id];
picks=plannerOpening.slice();autoPickNos=[];mockPicks=[];render=()=>{};
const realBefore=JSON.stringify(picks),autoBefore=JSON.stringify(autoPickNos);
runMock('needs',true,true);
if(JSON.stringify(picks)!==realBefore||JSON.stringify(autoPickNos)!==autoBefore||
  !mockUntilMine||!mockRandom||mockMode!=='needs'||mockPicks.length!==nextMyPick()-1||
  mockPicks[2]!==chase.id||new Set(mockPicks.filter(Boolean)).size!==mockPicks.filter(Boolean).length)
  throw new Error('turn-pair planner changed or mixed the real draft ledger');

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

// ── Smart Queue: genuine conditional 22/27 evaluation ───────────────────
// Build a fresh, real pick-3 -> pick-22 ledger (opponent picks via the same
// calibrated model, my pick-3 chosen from the live board) so curPick()===22
// and slot 3's myPicks() line up on 22/27 exactly as the feature requires.
confirm=()=>true;
render=()=>{};
picks=[];autoPickNos=[];
autoOppUntilMineForTest();
const pick3Row=computeBoard().find(r=>r.eligible&&!r.isSpecial&&(r.p.pos==='RB'||r.p.pos==='WR'));
if(!pick3Row)throw new Error('no eligible RB/WR available for the Smart Queue fixture pick 3');
picks.push(pick3Row.p.id);
autoOppUntilMineForTest();
if(curPick()!==22||!myPicks().includes(22)||!myPicks().includes(27))
  throw new Error('Smart Queue fixture did not reach pick 22 on slot 3 22/27 turn');

// Guard rails: only meaningful for slot 3 at the exact moment pick 22 is on
// the clock (before it, "candidates at 22" are not yet grounded in the live
// board; after it, the decision is already made).
const sqBoard=computeBoard();
if(smartQueue(sqBoard)===null)throw new Error('Smart Queue should be active at slot 3, pick 22');
const savedSlot=slot; slot=5;
if(smartQueue(sqBoard)!==null)throw new Error('Smart Queue must return null off slot 3');
slot=savedSlot;
picks.push(remaining()[0].id);
if(smartQueue(computeBoard())!==null)throw new Error('Smart Queue must return null once pick 22 has been made');
picks.pop();

// Purity: neither smartQueue() nor jointPickEvaluation() may mutate real
// picks/queue/queueArchive/autoPickNos, or touch localStorage.
let storageWrites=0;
const originalSetItem=localStorage.setItem;
localStorage.setItem=()=>{storageWrites++;};
const picksBefore=JSON.stringify(picks), queueBefore=JSON.stringify(queue),
  archiveBefore=JSON.stringify(queueArchive), autoBefore2=JSON.stringify(autoPickNos);
const meta=modelMeta();
const probeCandRow=sqBoard.filter(r=>r.eligible&&!r.isSpecial)[0];
jointPickEvaluation(probeCandRow.p.id,meta,50,1);
const evalsA=smartQueue(sqBoard);
if(JSON.stringify(picks)!==picksBefore||JSON.stringify(queue)!==queueBefore||
  JSON.stringify(queueArchive)!==archiveBefore||JSON.stringify(autoPickNos)!==autoBefore2||storageWrites!==0)
  throw new Error('Smart Queue mutated real draft state or touched storage');
localStorage.setItem=originalSetItem;

// Determinism: identical inputs and a fixed seed must give byte-identical
// jointValue/meanBestVor27/best-27-partner output across repeated calls.
const evalsB=smartQueue(sqBoard);
if(evalsA.length!==evalsB.length||!evalsA.every((e,i)=>
  e.c22.id===evalsB[i].c22.id&&Math.abs(e.jointValue-evalsB[i].jointValue)<1e-9&&
  Math.abs(e.meanBestVor27-evalsB[i].meanBestVor27)<1e-9&&
  (e.best27?.id??null)===(evalsB[i].best27?.id??null)))
  throw new Error('Smart Queue is not deterministic for a fixed seed and board state');

// Dimensional consistency: jointValue must be VOR@22 (the candidate's r.vor
// from the current board) plus E[VOR@27], not raw projected value(c22) plus
// a value-over-replacement figure -- those are different units and would
// misrank across positions with different replacement baselines.
if(!evalsA.every(e=>Math.abs(e.jointValue-(e.vor22+e.meanBestVor27))<1e-9))
  throw new Error('Smart Queue jointValue is not vor22+meanBestVor27');
if(!evalsA.every(e=>{const row=sqBoard.find(r=>r.p.id===e.c22.id);return row&&Math.abs(e.vor22-row.vor)<1e-9;}))
  throw new Error('Smart Queue vor22 must equal the candidate current-board value-over-replacement (r.vor)');

// K/DST exclusion: never a pick-22 candidate or a pick-27 fallback.
if(evalsA.some(e=>['K','DST'].includes(e.c22.pos))||evalsA.some(e=>e.best27&&['K','DST'].includes(e.best27.pos)))
  throw new Error('Smart Queue proposed a K/DST pick-22 candidate or pick-27 fallback');

// Manual-queue independence: queue/queueArchive state must never change the
// computed jointValue, and smartQueue()/jointPickEvaluation() must never
// call toggleQueue (verified by the picksBefore/queueBefore purity check
// above finding zero drift even though nothing here special-cased queue).
const anyOtherCand=sqBoard.filter(r=>r.eligible&&!r.isSpecial&&r.p.id!==probeCandRow.p.id)[0];
queue.push(anyOtherCand.p.id);
const evalsWithQueue=smartQueue(sqBoard);
queue.pop();
if(!evalsWithQueue.every((e,i)=>Math.abs(e.jointValue-evalsA[i].jointValue)<1e-9))
  throw new Error('populating the manual queue changed a Smart Queue jointValue');

// Non-naive-sum / eligibility re-check: taking a core (RB/WR) player at pick
// 22 relaxes the "preserve three-RB/WR start" deadline (STRATEGY.coreDeadline)
// enough to make an onesie (QB) pick eligible again at pick 27; taking a
// onesie (TE) at 22 does not. This is the exact mechanism that makes
// jointValue a genuine conditional evaluation rather than value(c22) plus a
// fixed, c22-independent pick-27 number.
const round27=Math.ceil(27/TEAMS);
const coreCand=sqBoard.find(r=>r.eligible&&!r.isSpecial&&(r.p.pos==='RB'||r.p.pos==='WR')&&r.p.id!==pick3Row.p.id);
const teCand=sqBoard.find(r=>r.eligible&&!r.isSpecial&&r.p.pos==='TE');
if(!coreCand||!teCand)throw new Error('Smart Queue fixture needs both an RB/WR and a TE candidate at pick 22');
const probeQb=remaining().find(p=>p.pos==='QB'&&p.id!==coreCand.p.id&&p.id!==teCand.p.id&&modelDraftable(p));
if(!probeQb)throw new Error('no probe QB available for the eligibility re-check test');
const eligBeforeC22=recommendationEligibility(probeQb,[pick3Row.p],round27);
const eligAfterCoreC22=recommendationEligibility(probeQb,[pick3Row.p,coreCand.p],round27);
const eligAfterTeC22=recommendationEligibility(probeQb,[pick3Row.p,teCand.p],round27);
if(eligBeforeC22.ok||eligAfterTeC22.ok||!eligAfterCoreC22.ok)
  throw new Error('pick-22 candidate eligibility narrowing/widening at pick 27 is not being recomputed per-candidate');
// The onesie (TE) candidate's simulated pick-27 pool must NEVER include a
// QB, in every one of its trials -- this is a structural guarantee (the
// blocked eligibility does not depend on the randomized opponent draws),
// not a statistical tendency, so it holds with a small trial count too.
const teJoint=jointPickEvaluation(teCand.p.id,meta,60,7);
if([...teJoint.topOptions.keys()].some(id=>byId.get(id).pos==='QB'))
  throw new Error('a blocked-eligibility QB leaked into the Smart Queue pick-27 fallback pool');
// A naive "value(c22) + fixed independent pick-27 gain" combination cannot
// see this at all: by construction the SAME fixed pick-27 figure is added to
// both candidates, so its contribution to the core-vs-TE gap is always
// exactly value(core)-value(TE) -- it structurally cannot express that only
// the core candidate unlocks QB eligibility at 27. The real per-candidate
// mechanism (asserted above) is not bound by that limitation.
const naiveGain27=(()=>{
  const forecastPool=PLAYERS.filter(p=>!picks.includes(p.id)&&modelDraftable(p));
  const skill=forecastPool.filter(p=>POS.includes(p.pos));
  const {rep}=replacement(skill);
  const rows=skill.filter(p=>recommendationEligibility(p,[pick3Row.p],round27).ok);
  return rows.reduce((best,p)=>Math.max(best,value(p)-(rep[p.pos]||0)),-Infinity);
})();
const naiveJointCore=value(coreCand.p)+naiveGain27, naiveJointTe=value(teCand.p)+naiveGain27;
if(Math.abs((naiveJointCore-naiveJointTe)-(value(coreCand.p)-value(teCand.p)))>1e-9)
  throw new Error('naive fixed-baseline gap must reduce to a pure value(c22) difference, blind to eligibility');

// noEligibleTrials: zero-fallback trials (no player clears recommendation
// eligibility for the simulated pick-27 pool/roster) must be counted and
// exposed, not silently folded into a mean that looks like a normal number.
if(!evalsA.every(e=>typeof e.noEligibleTrials==='number'&&e.noEligibleTrials>=0&&e.noEligibleTrials<=e.trials))
  throw new Error('smartQueue evals must expose a valid noEligibleTrials per candidate');
const originalRecEligibility=recommendationEligibility;
recommendationEligibility=()=>({ok:false,reason:'test-forced-ineligible'});
const forcedZeroJoint=jointPickEvaluation(probeCandRow.p.id,meta,12,3);
recommendationEligibility=originalRecEligibility;
if(forcedZeroJoint.noEligibleTrials!==12||forcedZeroJoint.meanBestVor27!==0)
  throw new Error('jointPickEvaluation did not track noEligibleTrials when every trial has no eligible pick-27 candidate');
const normalJoint=jointPickEvaluation(probeCandRow.p.id,meta,40,3);
if(normalJoint.noEligibleTrials!==0)
  throw new Error('a normal, well-stocked board should not report any zero-fallback trials');

// ── Smart Queue cache key: ordered pick IDs, not just count/curPick ─────
// Two ledgers of equal length (same curPick(), same picks.length) but
// different actual picks (e.g. a snipe swapped a different player into the
// same slot) must never collide on the same cache key.
const ledgerA=picks.slice(), otherOptA=sqBoard.filter(r=>r.eligible&&!r.isSpecial&&r.p.id!==picks[picks.length-1])[0];
const swappedLast=picks.slice(0,-1).concat([otherOptA.p.id]);
if(swappedLast.length!==ledgerA.length)throw new Error('cache-key fixture must keep pick count identical');
picks=ledgerA;
const keyForLedgerA=smartQueueCacheKey();
picks=swappedLast;
const keyForSwappedLedger=smartQueueCacheKey();
picks=ledgerA;
if(curPick()!==ledgerA.length+1)throw new Error('cache-key fixture setup is wrong');
if(keyForLedgerA===keyForSwappedLedger)
  throw new Error('smartQueueCacheKey collided for two same-length ledgers with different actual picks');
if(!keyForLedgerA.includes(String(ledgerA[ledgerA.length-1])))
  throw new Error('smartQueueCacheKey does not encode the actual ordered pick IDs');

// ── Smart Queue compute guard: single-flight + before/after staleness ───
// scheduleSmartQueueCompute() is the pure orchestration the UI's Compute
// button drives; it is exercised directly here (deferring the DOM-facing
// requestAnimationFrame/setTimeout wrapper, which is covered by the
// html.includes() checks below) so its guard logic is regression-tested
// without stubbing a browser scheduler.
let paintCalls=0;
const capturedRuns=[];
const captureScheduler=fn=>capturedRuns.push(fn);
const startedFirst=scheduleSmartQueueCompute(captureScheduler,()=>{paintCalls++;});
if(!startedFirst||!smartQueueComputing||paintCalls!==1||capturedRuns.length!==1)
  throw new Error('scheduleSmartQueueCompute must flip smartQueueComputing and paint the Computing state immediately, before the heavy work runs');
const startedSecond=scheduleSmartQueueCompute(captureScheduler,()=>{paintCalls++;});
if(startedSecond||paintCalls!==1||capturedRuns.length!==1)
  throw new Error('scheduleSmartQueueCompute must refuse a second computation while one is already in flight');
// "Before" guard: the ledger changes while the computation is still queued
// (captured but not yet run) -- when it finally runs, it must not overwrite
// the cache with a result computed against the stale request key.
smartQueueCache=null;
picks.push(remaining().find(p=>!picks.includes(p.id)).id);
capturedRuns[0]();
if(smartQueueCache!==null)
  throw new Error('a ledger change before the deferred Smart Queue computation ran must prevent it from writing the cache');
if(smartQueueComputing)throw new Error('scheduleSmartQueueCompute must release the single-flight guard once its deferred work finishes');
if(paintCalls!==2)throw new Error('scheduleSmartQueueCompute must paint again once the deferred work finishes');
picks.pop();
// "After" guard: the ledger changes DURING the (normally atomic) heavy
// computation itself. Simulate reentrancy by monkeypatching smartQueue() to
// mutate picks as a side effect before returning, and confirm the
// post-computation key re-check still refuses to cache the result.
const originalSmartQueueFn=smartQueue;
let reentrantMutationApplied=false;
smartQueue=function(...args){
  const out=originalSmartQueueFn.apply(null,args);
  if(!reentrantMutationApplied){reentrantMutationApplied=true;picks.push(remaining()[0].id);}
  return out;
};
smartQueueCache=null;
const capturedRuns2=[];
scheduleSmartQueueCompute(fn=>capturedRuns2.push(fn),()=>{});
capturedRuns2[0]();
smartQueue=originalSmartQueueFn;
if(smartQueueCache!==null)
  throw new Error('a ledger mutation occurring during the Smart Queue computation must be caught by the post-computation guard');
if(reentrantMutationApplied)picks.pop();
smartQueueComputing=false;
smartQueueCache=null;

// ── Smart Queue compute guard: exception safety ──────────────────────────
// scheduleSmartQueueCompute()'s deferred work must run inside try/finally:
// if computeBoard()/smartQueue() throws mid-simulation, smartQueueComputing
// must still release (otherwise the Compute button stays disabled forever),
// no stale/partial result may reach smartQueueCache, the surfaced error
// must be readable via smartQueueError, and onPaint() must still fire so the
// UI repaints out of "Computing…" into the failed state. A subsequent
// compute must then be able to start clean.
smartQueueError=null; smartQueueCache={key:'stale-should-be-cleared',evals:[{fake:true}]};
let paintCallsErr=0;
const capturedRunsErr=[];
const throwingSmartQueue=()=>{throw new Error('boom: simulated smartQueue failure');};
smartQueue=throwingSmartQueue;
const startedThrow=scheduleSmartQueueCompute(fn=>capturedRunsErr.push(fn),()=>{paintCallsErr++;});
if(!startedThrow||!smartQueueComputing)throw new Error('exception-safety fixture: compute did not start');
capturedRunsErr[0]();
smartQueue=originalSmartQueueFn;
if(smartQueueComputing)
  throw new Error('an exception inside the deferred Smart Queue work must still release smartQueueComputing');
if(!smartQueueError||!smartQueueError.includes('boom'))
  throw new Error('a thrown Smart Queue computation must surface its error via smartQueueError');
if(!smartQueueCache||smartQueueCache.key!=='stale-should-be-cleared')
  throw new Error('an exception inside the deferred Smart Queue work must not overwrite/clear an unrelated stale cache with a partial result');
if(paintCallsErr!==2)
  throw new Error('scheduleSmartQueueCompute must still call onPaint (Computing… then failed) even when the work throws');
// Another computation must be able to start cleanly right after a failure.
smartQueueCache=null;
const capturedRunsAfterErr=[];
const startedAfterErr=scheduleSmartQueueCompute(fn=>capturedRunsAfterErr.push(fn),()=>{});
if(!startedAfterErr)throw new Error('a released Smart Queue guard must allow a fresh computation to start after a prior failure');
capturedRunsAfterErr[0]();
if(smartQueueComputing)throw new Error('the post-failure retry computation must also release smartQueueComputing when it completes');
if(!smartQueueCache||smartQueueCache.key!==smartQueueCacheKey())
  throw new Error('a successful retry after a prior failure must write a fresh cache entry');
if(smartQueueError!==null)
  throw new Error('a successful retry must clear the previous smartQueueError');
smartQueueComputing=false; smartQueueCache=null; smartQueueError=null;

// ── Manual Queue tags: Target / Conditional / Fade ──────────────────────
// Pure presentation metadata: never read by computeBoard()/value()/
// replacement()/survives()/recommendationEligibility().
const tagA=remaining()[0].id, tagB=remaining()[1].id;
queue=[]; queueArchive=[]; queueTags={};
toggleQueue(tagA); toggleQueue(tagB);
setQueueTag(tagA,'target');
if(queueTags[tagA]!=='target')throw new Error('setQueueTag did not apply a valid tag to a queued player');
setQueueTag(tagA,'fade');
if(queueTags[tagA]!=='fade'||Object.keys(queueTags).length!==1)
  throw new Error('re-tagging a queued player must replace, not add to, its tag (mutual exclusivity)');
setQueueTag(tagA,'fade');
if(queueTags[tagA]!==undefined)throw new Error('clicking the active tag again should clear it');
setQueueTag(tagA,'target'); setQueueTag(tagB,'conditional');
setQueueTag(tagB,'not-a-real-tag');
if(queueTags[tagB]!=='conditional')throw new Error('an invalid tag value must be rejected, not applied');

// Board byte-equivalence: tagging/queueing must never change computeBoard()'s
// ranking output. This is the direct test of "advisory never touches
// ranking" for the tag feature.
const boardNoTags=JSON.stringify(computeBoard().map(r=>({id:r.p.id,gain:r.gain,vonaTier:r.vonaTier,eligible:r.eligible,decisionRank:r.decisionRank})));
queueTags[tagA]='fade'; queue.push(remaining()[2].id);
const boardWithTags=JSON.stringify(computeBoard().map(r=>({id:r.p.id,gain:r.gain,vonaTier:r.vonaTier,eligible:r.eligible,decisionRank:r.decisionRank})));
if(boardNoTags!==boardWithTags)throw new Error('populating queueTags/queue changed computeBoard() ranking output');
queue.pop(); queueTags[tagA]='target';

// Sanitize contract: mirrors sanitizeQueueArchive's defensive filtering.
// (a) valid id/value, (b) id not currently in queue, (c) id not in PLAYERS,
// (d) invalid enum value -- only (a) should survive.
const rawTags={[String(tagA)]:'target',[String(remaining()[5].id)]:'fade','999999':'target',[String(tagB)]:'not-real'};
const sanitized=sanitizeQueueTags(rawTags,queue);
if(!(Object.keys(sanitized).length===1&&sanitized[tagA]==='target'))
  throw new Error('sanitizeQueueTags did not drop orphaned/unknown-id/invalid-enum tags');

// Mutator cleanup contract: removeQueueEntry / toggleQueue-off / clearQueue
// must delete the corresponding tag; stash+restore (snipe, then undo) must
// carry the tag through unchanged. tagB is already tagged 'conditional' from
// the mutual-exclusivity test above; re-applying it here would toggle it OFF
// (same-tag click clears), so set a genuinely different value to guarantee
// an active tag going into removeQueueEntry.
setQueueTag(tagB,'target');
if(queueTags[tagB]!=='target')throw new Error('test setup failed: tagB should carry an active tag before removeQueueEntry');
removeQueueEntry(tagB);
if(queueTags[tagB]!==undefined)throw new Error('removeQueueEntry did not delete its queueTags entry');
toggleQueue(tagB); setQueueTag(tagB,'fade'); toggleQueue(tagB);
if(queueTags[tagB]!==undefined)throw new Error('toggling a queued player off did not delete its queueTags entry');
toggleQueue(tagB); setQueueTag(tagB,'target');
const snipeStashPick=picks.length+1;
stashQueuedPlayer(tagB,snipeStashPick,'sniped');
if(queueTags[tagB]!==undefined)throw new Error('a sniped player must leave the active queueTags map');
const stashedEntry=queueArchive.find(e=>e.id===tagB);
if(!stashedEntry||stashedEntry.tag!=='target')throw new Error('the sniped archive entry must carry the tag through');
restoreQueuedPlayer(tagB,snipeStashPick);
if(queueTags[tagB]!=='target')throw new Error('undo (restoreQueuedPlayer) did not restore the tag');
clearQueue();
if(Object.keys(queueTags).length!==0)throw new Error('clearQueue did not clear all queueTags');

// Reset preserves tags: restoreAllQueueEntries (used by resetDraft) must
// carry archived tags back onto the restored queue entries.
queue=[]; queueArchive=[]; queueTags={};
toggleQueue(tagA); setQueueTag(tagA,'fade');
stashQueuedPlayer(tagA,1,'drafted');
restoreAllQueueEntries();
if(!queue.includes(tagA)||queueTags[tagA]!=='fade')
  throw new Error('restoreAllQueueEntries (reset draft) did not preserve the queue tag');
queue=[]; queueArchive=[]; queueTags={};

// Backup/import round-trip: queueTags must export and validate.
toggleQueue(tagA); setQueueTag(tagA,'conditional');
const backup=buildBackupState();
if(!backup.queueTags||backup.queueTags[tagA]!=='conditional')
  throw new Error('buildBackupState did not include the current queueTags');
const badBackup={...backup,queueTags:{...backup.queueTags,[String(remaining()[9].id)]:'target'}};
let rejectedOrphanTag=false;
try{validateBackupState(badBackup);}catch(e){rejectedOrphanTag=true;}
if(!rejectedOrphanTag)throw new Error('validateBackupState accepted a queueTags entry for a non-queued id');
const restored=validateBackupState(backup);
if(restored.queueTags[tagA]!=='conditional')throw new Error('validateBackupState did not round-trip a valid queueTags entry');
queue=[]; queueArchive=[]; queueTags={};

// ── Performance: computational bound for a live 90s pick clock ─────────
// Observed ~3.8s locally for SMART_QUEUE.candidates x SMART_QUEUE.trials.
// The cap here is deliberately loose (not a tight perf budget) -- it exists
// to catch an accidental O(n^2)/runaway-loop regression, not to police
// exact timing, so it tolerates a slower/shared CI box without being flaky
// while still leaving a large margin under the real 90s pick clock.
const perfStart=Date.now();
smartQueue(sqBoard);
const perfMs=Date.now()-perfStart;
if(perfMs>20000)throw new Error('Smart Queue took '+perfMs+'ms for '+SMART_QUEUE.candidates+' candidates x '+SMART_QUEUE.trials+' trials -- too slow for a 90s pick clock');
globalThis.SMART_QUEUE_PERF_MS=perfMs;

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
  setTimeout:()=>0,clearTimeout:()=>{},
};
vm.createContext(context);
vm.runInContext(engine+'\n'+harness,context,{timeout:30000});
const result=context.TEST_RESULT;
result.engineSha256=crypto.createHash('sha256').update(engine).digest('hex');
result.smartQueuePerfMs=context.SMART_QUEUE_PERF_MS;
assert(html.includes('Projection audit view (read only)')&&
  html.includes('title="Projected fantasy points for this league\'s scoring"')&&
  html.includes('<b>Projection</b> is the median of ESPN, CBS, and FFToday')&&
  html.includes('not a calibrated confidence grade'),
  'projection audit naming is missing or misleading');
assert(engine.includes('const miracles=rows.filter(r=>r.modelRank<90&&r.s22<.15)'),
  'conditional fallers must use survival to pick 22');
assert(html.includes('id="auto"')&&html.includes('autoPickNos.push(n)')&&html.includes('function autoToMyPick'),
  'Draft-page Auto rehearsal is not connected to the marked draft ledger');
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
assert(html.includes('ADP avg')&&html.includes('r.p.adp.toFixed(1)'),
  'ADP audit view is hiding decimal average-pick values');
assert(html.includes('const show=rows2;')&&html.includes('visibleRows=show.slice(0,8);')&&
  html.includes('.board{flex:1;min-height:0;overflow:auto'),
  'full ranking is not scrollable while hotkeys remain limited to the top eight');
assert(html.includes('id="autountil"')&&html.includes('runMock(\'needs\',true,true)')&&
  html.includes('mockUntilMine'),
  'planning-only Auto to my pick preview is missing');
assert(html.includes('id="auto"')&&html.includes('function autoToMyPick()')&&
  html.includes("(e.ctrlKey||e.metaKey)&&e.key==='Enter'"),
  'Draft-page Auto to my pick control or shortcut is missing');
assert(!html.includes('NEWS today')&&!/NEWS \d+d/.test(html)&&html.includes('ESPN update ${NEWS_MONTHS'),
  'news recency is not shown as a neutral exact-date stamp');
assert(/grid-template-columns:repeat\(5,minmax\(0,1fr\)\)/.test(html),'mobile footer button grid is stale');
assert(html.includes('function computeSmartQueueNow(){')&&html.includes('scheduleSmartQueueCompute(fn=>{')&&
  html.includes('requestAnimationFrame')&&html.includes('smartQueueComputing'),
  'Smart Queue Compute must defer the heavy work via requestAnimationFrame/setTimeout through scheduleSmartQueueCompute');
assert(html.includes('<b>Computing…</b>')&&html.includes('<button class="mini-btn" type="button" disabled>Computing…</button>'),
  'Smart Queue must render a Computing state and disable the Compute button while a computation is in flight');
assert(html.includes('VOR@22')&&html.includes('E[VOR@27]')&&html.includes('e.vor22.toFixed(1)')&&html.includes('e.meanBestVor27.toFixed(1)'),
  'Smart Queue UI must present VOR@22 + E[VOR@27], not raw projected value plus a value-over-replacement figure');
assert(html.includes('noEligibleTrials')&&html.includes('had no eligible candidate'),
  'Smart Queue must surface a noEligibleTrials warning in the UI, not silently hide zero-fallback trials');
console.log(JSON.stringify(result,null,2));
