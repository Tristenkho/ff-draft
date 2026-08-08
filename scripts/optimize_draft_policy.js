/* Draft-policy tournament with independent weekly season/playoff evaluation. */
const fs=require('fs'),vm=require('vm');
const html=fs.readFileSync('out/draft_terminal.html','utf8');
const start=html.indexOf('const TEAMS=12, ROUNDS=14;');
const end=html.indexOf('// ── render ───────────────────────────────────────');
if(start<0||end<0)throw new Error('Could not locate embedded draft engine');

const policies=[
  {id:'baseline',label:'Current tuned build',lambda:.40,coreEarly:3,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:4,luxuryStart:9,te2Edge:5,qb2Edge:5},
  {id:'lambda_020',label:'Lower ceiling weight',lambda:.20,coreEarly:3,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:4,luxuryStart:9,te2Edge:5,qb2Edge:5},
  {id:'lambda_060',label:'Higher ceiling weight',lambda:.60,coreEarly:3,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:4,luxuryStart:9,te2Edge:5,qb2Edge:5},
  {id:'core_2',label:'Only two early RB/WR',lambda:.40,coreEarly:2,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:4,luxuryStart:9,te2Edge:5,qb2Edge:5},
  {id:'core_4',label:'Four early RB/WR',lambda:.40,coreEarly:4,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:4,luxuryStart:9,te2Edge:5,qb2Edge:5},
  {id:'starters_7',label:'Finish starters by R7',lambda:.40,coreEarly:3,coreDeadline:4,starterDeadline:7,coreTotal:10,minCoreEach:4,luxuryStart:9,te2Edge:5,qb2Edge:5},
  {id:'starters_9',label:'Finish starters by R9',lambda:.40,coreEarly:3,coreDeadline:4,starterDeadline:9,coreTotal:10,minCoreEach:4,luxuryStart:10,te2Edge:5,qb2Edge:5},
  {id:'te_edge_0',label:'Take any superior TE2',lambda:.40,coreEarly:3,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:4,luxuryStart:9,te2Edge:0,qb2Edge:5},
  {id:'te_edge_10',label:'Require +10 for TE2',lambda:.40,coreEarly:3,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:4,luxuryStart:9,te2Edge:10,qb2Edge:5},
  {id:'luxury_10',label:'Delay QB2/TE2 to R10',lambda:.40,coreEarly:3,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:4,luxuryStart:10,te2Edge:5,qb2Edge:5},
  {id:'no_luxury',label:'No QB2/TE2',lambda:.40,coreEarly:3,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:4,luxuryStart:13,te2Edge:99,qb2Edge:99},
  {id:'loose_balance',label:'Allow 7/3 RB-WR split',lambda:.40,coreEarly:3,coreDeadline:4,starterDeadline:8,coreTotal:10,minCoreEach:3,luxuryStart:9,te2Edge:5,qb2Edge:5}
];
const stage1Drafts=Number(process.argv[2]||300);
const stage2Drafts=Number(process.argv[3]||600);
const seasonsPerDraft=Number(process.argv[4]||5);

const engine=html.slice(start,end);
const harness=`
const POLICY_LIST=${JSON.stringify(policies)};
const BASE_STRATEGY={...STRATEGY};
let RNG_STATE=1;
function seedDraft(n){RNG_STATE=(n>>>0)||1;}
Math.random=()=>{RNG_STATE=(RNG_STATE+0x6D2B79F5)|0;let t=RNG_STATE;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};
function h32(a,b=0,c=0,d=0){let x=(a^Math.imul(b,0x9e3779b1)^Math.imul(c,0x85ebca6b)^Math.imul(d,0xc2b2ae35))|0;x=Math.imul(x^x>>>16,0x7feb352d);x=Math.imul(x^x>>>15,0x846ca68b);return(x^x>>>16)>>>0;}
function u01(a,b,c,d=0){return (h32(a,b,c,d)+.5)/4294967296;}
function norm(a,b,c,d=0){const u=Math.max(u01(a,b,c,d),1e-9),v=u01(a,b,c,d+7919);return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);}
function strHash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;}
function setPolicy(p){Object.assign(STRATEGY,BASE_STRATEGY,p);lambda=p.lambda;}
function ensembleOpponent(candidates,roster,round,meta,seed,team){
  const style=h32(seed,team,71)%100;
  const scores=new Map(candidates.map(p=>{
    const need=mockNeedAdjustment(p,roster,round), noise=mockNoise();
    let score;
    if(style<60)score=(meta.modelRank.get(p.id)||999)+need+noise;
    else if(style<85)score=(p.adp||999)+need*.30+noise*1.5;
    else score=(meta.modelRank.get(p.id)||999)+need*.50+noise*1.25;
    return [p.id,score];
  }));
  return [...candidates].sort((a,b)=>scores.get(a.id)-scores.get(b.id)||a.name.localeCompare(b.name))[0];
}
function autoEnsemble(seed,meta,rosters){
  const total=TEAMS*ROUNDS;
  while(picks.length<total&&!myPicks().includes(curPick())){
    const n=curPick(),round=Math.ceil(n/TEAMS),team=teamAtPick(n),roster=rosters[team-1];
    let candidates=remaining().filter(p=>mockEligible(p,roster,true,round));
    if(!candidates.length)candidates=remaining().filter(p=>mockEligible(p,roster,false,round));
    const pick=ensembleOpponent(candidates,roster,round,meta,seed,team);
    if(!pick)throw new Error('Opponent has no eligible pick');
    picks.push(pick.id);roster.push(pick);
  }
}
function draftLeague(policy,seed){
  setPolicy(policy);seedDraft(seed);picks=[];autoPickNos=[];slot=3;
  const meta=modelMeta(),rosters=Array.from({length:TEAMS},()=>[]);
  autoEnsemble(seed,meta,rosters);
  for(let round=1;round<=ROUNDS;round++){
    const rec=computeBoard()[0];
    if(!rec||!rec.eligible)throw new Error(policy.id+' has no eligible recommendation R'+round);
    picks.push(rec.p.id);rosters[slot-1].push(rec.p);
    autoEnsemble(seed,meta,rosters);
  }
  return rosters.map(r=>r.map(p=>p.id));
}

const consensus=new Map();
for(const pos of ['QB','RB','WR','TE']){
  const group=PLAYERS.filter(p=>p.pos===pos);
  const values=group.map(p=>p.proj).sort((a,b)=>b-a);
  const order=[...group].sort((a,b)=>((a.adp||999)+(a.ecr||999))-((b.adp||999)+(b.ecr||999)));
  order.forEach((p,i)=>consensus.set(p.id,values[Math.min(i,values.length-1)]));
}
for(const p of PLAYERS)if(!consensus.has(p.id))consensus.set(p.id,p.proj);
const injury={QB:.018,RB:.050,WR:.038,TE:.040,K:.010,DST:0};
const volatility={QB:.25,RB:.55,WR:.60,TE:.52,K:.38,DST:.48};
const replacementWeek={QB:14,RB:7.5,WR:7.5,TE:6.5,K:7,DST:7};
function talentFor(p,seasonSeed){
  const regime=h32(seasonSeed,991)%3;
  const w=regime===0?.70:regime===1?.45:.25;
  const base=w*p.proj+(1-w)*(consensus.get(p.id)||p.proj);
  return clamp(base+norm(seasonSeed,p.id,17)*p.sd*.60,base*.45,base*1.65);
}
function byeFor(p){return 5+(strHash(p.team||p.name)%10);}
function playerWeek(p,seasonSeed,week,talent){
  if(week===byeFor(p))return null;
  const inj=injury[p.pos]||0;
  if(u01(seasonSeed,p.id,week,13)<inj)return null;
  const activeMean=talent/17/Math.max(1-inj,.8);
  const teamShock=1+norm(seasonSeed,strHash(p.team||''),week,29)*.08;
  const score=Math.max(0,activeMean*teamShock+norm(seasonSeed,p.id,week,47)*activeMean*(volatility[p.pos]||.5));
  const forecast=activeMean*(1+norm(seasonSeed,p.id,week,61)*.10);
  return {p,score,forecast};
}
function lineupScore(ids,seasonSeed,week,talents){
  const avail=ids.map(id=>{const p=byId.get(id);return playerWeek(p,seasonSeed,week,talents.get(id));}).filter(Boolean);
  const used=new Set();let total=0;
  function take(pos,n){const a=avail.filter(x=>x.p.pos===pos&&!used.has(x.p.id)).sort((x,y)=>y.forecast-x.forecast);for(let i=0;i<n;i++){if(a[i]){used.add(a[i].p.id);total+=a[i].score;}else total+=replacementWeek[pos]*(.75+.5*u01(seasonSeed,week,strHash(pos),i));}}
  take('QB',1);take('RB',2);take('WR',2);take('TE',1);
  const flex=avail.filter(x=>['RB','WR','TE'].includes(x.p.pos)&&!used.has(x.p.id)).sort((x,y)=>y.forecast-x.forecast)[0];
  if(flex){used.add(flex.p.id);total+=flex.score;}else total+=6.5*(.75+.5*u01(seasonSeed,week,777,1));
  take('K',1);take('DST',1);return total;
}
function simulateSeason(rosters,seasonSeed){
  const talents=new Map();for(const ids of rosters)for(const id of ids)if(!talents.has(id))talents.set(id,talentFor(byId.get(id),seasonSeed));
  const scores=Array.from({length:TEAMS},()=>Array(18).fill(0));
  for(let w=1;w<=17;w++)for(let t=0;t<TEAMS;t++)scores[t][w]=lineupScore(rosters[t],seasonSeed,w,talents);
  const wins=Array(TEAMS).fill(0),pf=Array(TEAMS).fill(0);
  for(let w=1;w<=14;w++){
    const order=[...Array(TEAMS).keys()].sort((a,b)=>h32(seasonSeed,w,a)-h32(seasonSeed,w,b));
    for(let i=0;i<TEAMS;i+=2){const a=order[i],b=order[i+1];pf[a]+=scores[a][w];pf[b]+=scores[b][w];if(scores[a][w]>=scores[b][w])wins[a]++;else wins[b]++;}
  }
  const seeds=[...Array(TEAMS).keys()].sort((a,b)=>wins[b]-wins[a]||pf[b]-pf[a]).slice(0,8);
  const made=seeds.includes(slot-1);const seedRank=seeds.indexOf(slot-1)+1;
  const win=(a,b,w)=>scores[a][w]>=scores[b][w]?a:b;
  const q=[win(seeds[0],seeds[7],15),win(seeds[3],seeds[4],15),win(seeds[1],seeds[6],15),win(seeds[2],seeds[5],15)];
  const s=[win(q[0],q[1],16),win(q[2],q[3],16)],champ=win(s[0],s[1],17);
  return {playoff:made?1:0,champ:champ===slot-1?1:0,pf:pf[slot-1],seed:made?seedRank:9};
}
function summarize(out){
  const n=out.length,mean=k=>out.reduce((s,x)=>s+x[k],0)/n;
  return {trials:n,playoff:mean('playoff'),champ:mean('champ'),pf:mean('pf'),seed:mean('seed'),rawChamp:out.map(x=>x.champ),rawPlayoff:out.map(x=>x.playoff)};
}
function evaluate(policy,startDraft,drafts,seasonsPerDraft){
  const out=[];let legal=0,te2=0,qb2=0;
  for(let d=0;d<drafts;d++){
    const draftSeed=100003+Math.imul(startDraft+d,7919),rosters=draftLeague(policy,draftSeed);
    const mine=rosters[slot-1].map(id=>byId.get(id)),counts=rosterCounts(mine);legal+=counts.QB>=1&&counts.RB>=2&&counts.WR>=2&&counts.TE>=1&&counts.K===1&&counts.DST===1;te2+=counts.TE===2;qb2+=counts.QB===2;
    for(let s=0;s<seasonsPerDraft;s++)out.push(simulateSeason(rosters,700001+Math.imul(startDraft+d,3571)+Math.imul(s,104729)));
  }
  return {...summarize(out),drafts,legal,te2,qb2};
}
function paired(a,b){const n=Math.min(a.length,b.length);let sum=0,sq=0;for(let i=0;i<n;i++){const d=a[i]-b[i];sum+=d;sq+=d*d;}const mean=sum/n,sd=Math.sqrt(Math.max(0,(sq-n*mean*mean)/Math.max(1,n-1))),se=sd/Math.sqrt(n);return {delta:mean,lo:mean-1.96*se,hi:mean+1.96*se};}
const stage1={};for(const p of POLICY_LIST)stage1[p.id]=evaluate(p,0,${stage1Drafts},${seasonsPerDraft});
const ranked=[...POLICY_LIST].sort((a,b)=>stage1[b.id].champ-stage1[a.id].champ||stage1[b.id].playoff-stage1[a.id].playoff);
const finalistIds=new Set(['baseline',...ranked.slice(0,3).map(p=>p.id)]),stage2={};
for(const p of POLICY_LIST)if(finalistIds.has(p.id))stage2[p.id]=evaluate(p,10000,${stage2Drafts},${seasonsPerDraft});
const final=[...finalistIds].map(id=>{const p=POLICY_LIST.find(x=>x.id===id),a=stage1[id],b=stage2[id];const combined={...summarize([...a.rawChamp.map((champ,i)=>({champ,playoff:a.rawPlayoff[i],pf:0,seed:0})),...b.rawChamp.map((champ,i)=>({champ,playoff:b.rawPlayoff[i],pf:0,seed:0}))])};return {policy:p,stage1:a,stage2:b,champ:(a.champ*a.trials+b.champ*b.trials)/(a.trials+b.trials),playoff:(a.playoff*a.trials+b.playoff*b.trials)/(a.trials+b.trials),pf:(a.pf*a.trials+b.pf*b.trials)/(a.trials+b.trials),drafts:a.drafts+b.drafts,legal:a.legal+b.legal,te2:a.te2+b.te2,qb2:a.qb2+b.qb2,rawChamp:[...a.rawChamp,...b.rawChamp],rawPlayoff:[...a.rawPlayoff,...b.rawPlayoff]};}).sort((a,b)=>b.champ-a.champ||b.playoff-a.playoff);
const base=final.find(x=>x.policy.id==='baseline');for(const row of final){row.champVsBaseline=paired(row.rawChamp,base.rawChamp);row.playoffVsBaseline=paired(row.rawPlayoff,base.rawPlayoff);}for(const row of final){delete row.rawChamp;delete row.rawPlayoff;}
for(const v of Object.values(stage1)){delete v.rawChamp;delete v.rawPlayoff;}for(const v of Object.values(stage2)){delete v.rawChamp;delete v.rawPlayoff;}
globalThis.OPT_RESULT={method:{stage1Drafts:${stage1Drafts},stage2Drafts:${stage2Drafts},seasonsPerDraft:${seasonsPerDraft},evaluator:'projection/consensus ensemble + uncertainty + weekly lineups/injuries/replacement + 8-team playoffs'},policies:POLICY_LIST,stage1,final};
`;

const seededMath=Object.create(Math);
const context={console,Math:seededMath,Map,Set,Array,Object,JSON};
vm.createContext(context);
vm.runInContext(engine+'\n'+harness,context,{timeout:900000});
const result=context.OPT_RESULT;
fs.writeFileSync('out/draft_policy_optimization_raw.json',JSON.stringify(result,null,2));

const pct=x=>(100*x).toFixed(2)+'%';
const rows=result.final.map((r,i)=>`| ${i+1} | ${r.policy.label} | ${pct(r.champ)} | ${pct(r.playoff)} | ${r.pf.toFixed(1)} | ${pct(r.champVsBaseline.delta)} [${pct(r.champVsBaseline.lo)}, ${pct(r.champVsBaseline.hi)}] | ${r.legal}/${r.drafts} | ${pct(r.te2/r.drafts)} |`).join('\n');
const stage=result.policies.map(p=>{const r=result.stage1[p.id];return `| ${p.label} | ${pct(r.champ)} | ${pct(r.playoff)} | ${r.pf.toFixed(1)} |`;}).join('\n');
const winner=result.final[0],stable=winner.policy.id!=='baseline'&&winner.champVsBaseline.lo>0;
const report=`# Draft policy championship optimizer\n\n## Outcome\n\n${stable?`**Stable winner: ${winner.policy.label}.** Its paired 95% interval versus baseline excludes zero.`:`**No challenger proved a statistically reliable championship-rate improvement over the current tuned build.** Keep the baseline configuration; the apparent leader's paired interval still includes zero.`}\n\n## Method\n\n- Stage 1: 12 policies × ${stage1Drafts} paired draft rooms × ${seasonsPerDraft} season outcomes per room.\n- Final: baseline plus the top three policies, each extended by ${stage2Drafts} paired draft rooms × ${seasonsPerDraft} outcomes.\n- Opponent rooms mix need-aware (60%), ADP-oriented (25%), and Model-oriented (15%) team behavior with controlled randomness.\n- Evaluation is separate from draft selection: projection/ADP/ECR ensemble, season uncertainty, weekly volatility, team correlation, injuries, replacement pickups, lineup setting, 14-week standings, and 8-team Weeks 15–17 playoffs.\n- The workspace has no historical weekly outcomes or bye-week data. Team byes are assigned consistently for paired comparisons, and this remains a synthetic optimizer rather than historical proof.\n\n## Finalists\n\n| Rank | Policy | Champion | Playoffs | Avg regular-season PF | Championship Δ vs baseline (95% CI) | Legal drafts | QB2/TE2 exception |\n| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |\n${rows}\n\n## Stage-one screen\n\n| Policy | Champion | Playoffs | Avg PF |\n| --- | ---: | ---: | ---: |\n${stage}\n\n## Decision\n\n${stable?`Apply ${winner.policy.label}: \`${JSON.stringify(winner.policy)}\`.`:`Retain the current strategy configuration: \`${JSON.stringify(result.policies.find(p=>p.id==='baseline'))}\`. More synthetic trials would narrow Monte Carlo error, but historical weekly backtesting is the more valuable next source of evidence.`}\n`;
fs.writeFileSync('out/draft_policy_optimization.md',report);
console.log(report);
