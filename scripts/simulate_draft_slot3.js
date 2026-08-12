/* Offline Monte Carlo harness for out/draft_terminal.html. Does not alter the app.
   Set DRAFT_MARKET=espn|blend|conservative to stress-test ESPN versus the
   current 12-team half-PPR market used by the live board.
   Seed picks before slot 3 with DRAFT_SEED='Puka Nacua|Jahmyr Gibbs'. */
const fs=require('fs'), vm=require('vm');
const html=fs.readFileSync(process.env.DRAFT_HTML||'out/draft_terminal.html','utf8');
const start=html.indexOf('const TEAMS=12, ROUNDS=14;');
const end=html.indexOf('// ── render ───────────────────────────────────────');
if(start<0||end<0) throw new Error('Could not locate the draft engine');

const market=process.env.DRAFT_MARKET||'blend';
if(!['espn','blend','conservative'].includes(market))throw new Error('DRAFT_MARKET must be espn, blend, or conservative');
const seed=(process.env.DRAFT_SEED||'').split('|').map(name=>name.trim()).filter(Boolean);
if(seed.length>2)throw new Error('DRAFT_SEED can contain at most the two picks before slot 3');
const timingSource=`function timingMetric(p){
  const espn=roomMetric(p)+ADP_TREND_WEIGHT*clamp(adpTrend(p),-20,20);
  const market=(p?.market_adp??999)<500?p.market_adp:espn;
  return (1-MARKET_ADP_WEIGHT)*espn+MARKET_ADP_WEIGHT*market;
}`;
const timingScenario=`const timingMetric=p=>{
  const espn=roomMetric(p)+ADP_TREND_WEIGHT*clamp(adpTrend(p),-20,20);
  const market=(p?.market_adp??999)<500?p.market_adp:espn;
  if(SIM_MARKET==='blend')return .60*espn+.40*market;
  if(SIM_MARKET==='conservative')return Math.min(espn,market);
  return espn;
};`;
const originalEngine=html.slice(start,end);
if(!originalEngine.includes(timingSource))throw new Error('Could not locate timing metric');
const engine=originalEngine.replace(timingSource,timingScenario);
const harness=`
function initialPicks(){
  const ids=[];
  for(const name of SIM_SEED_NAMES){
    const p=PLAYERS.find(player=>player.name===name);
    if(!p)throw new Error('Seed player not found: '+name);
    if(ids.includes(p.id))throw new Error('Duplicate seed player: '+name);
    ids.push(p.id);
  }
  return ids;
}
function autoOppUntilMine(){
  const total=TEAMS*ROUNDS, meta=modelMeta(), rosters=rostersFromDraft();
  while(picks.length<total&&!myPicks().includes(curPick())){
    const n=curPick(), round=Math.ceil(n/TEAMS), team=teamAtPick(n), roster=rosters[team-1];
    let candidates=remaining().filter(p=>modelDraftable(p)&&mockEligible(p,roster,true,round));
    if(!candidates.length)candidates=remaining().filter(p=>modelDraftable(p)&&mockEligible(p,roster,false,round));
    const pick=chooseNeedAware(candidates,roster,round,meta,SIM_RANDOM);
    if(!pick) break;
    picks.push(pick.id); roster.push(pick);
  }
}
function keyRoster(list){
  const counts={QB:0,RB:0,WR:0,TE:0,K:0,DST:0};
  list.forEach(p=>counts[p.pos]++);
  return 'QB'+counts.QB+' RB'+counts.RB+' WR'+counts.WR+' TE'+counts.TE+' K'+counts.K+' DST'+counts.DST;
}
function add(map,key,n=1){map.set(key,(map.get(key)||0)+n)}
function top(map,n=12){return [...map.entries()].sort((a,b)=>b[1]-a[1]||String(a[0]).localeCompare(String(b[0]))).slice(0,n)}
function simulate(n,randomized){
  SIM_RANDOM=randomized; const rounds=Array.from({length:14},()=>new Map());
  const posByRound=Array.from({length:14},()=>new Map()); const builds={4:new Map(),8:new Map(),14:new Map()};
  const combos=new Map(), oppBuilds=new Map(), unavailable=Array.from({length:14},()=>new Map()), firstAt=new Map(), pickedAt=new Map();
  const totals=[], myAdp=[], oppReach=[], signatures=new Set(); let exactRecommended=0;
  const baseRep=replacement(skillPool()).rep;
  for(let d=0;d<n;d++){
    picks=initialPicks(); autoPickNos=[]; slot=3; lambda=.40; autoOppUntilMine();
    const mine=[];
    for(let r=1;r<=14;r++){
      const pre=new Set(remaining().map(p=>p.id));
      const rows=computeBoard(); const rec=rows[0];
      if(!rec) throw new Error('No recommendation at round '+r);
      if(!rec.eligible)throw new Error('No eligible recommendation at round '+r+': '+rec.blockedReason);
      if(SIM_TRACE&&d===0)console.error('TRACE',r,rec.p.name,rec.p.pos,rec.eligible,rec.blockedReason,
        rows.slice(0,6).map(x=>[x.p.name,x.p.pos,x.eligible,x.blockedReason]),
        r>=9?rows.filter(x=>x.luxury).sort((a,b)=>b.gain-a.gain).slice(0,4).map(x=>[x.p.name,x.p.pos,x.gain,x.vor,x.eligible,x.blockedReason]):[]);
      const selected=rec.p; if(rows[0].p.id===selected.id) exactRecommended++;
      for(const p of PLAYERS) if(!pre.has(p.id)) { add(unavailable[r-1],p.name); if(!firstAt.has(p.id)) firstAt.set(p.id,r); }
      picks.push(selected.id); mine.push(selected);
      add(rounds[r-1],selected.name); add(posByRound[r-1],selected.pos);
      myAdp.push({round:r,name:selected.name,delta:(myPicks()[r-1]-selected.adp)});
      if([4,8,14].includes(r)) add(builds[r],keyRoster(mine));
      autoOppUntilMine();
    }
    signatures.add(mine.map(p=>p.id).join(','));
    const leagueRosters=rostersFromDraft();
    leagueRosters.forEach((roster,i)=>{
      const c=rosterCounts(roster);
      const legal=roster.length===ROUNDS&&c.QB>=1&&c.RB>=2&&c.WR>=2&&c.TE>=1&&c.K===1&&c.DST===1
        &&Object.keys(CAPS).every(pos=>c[pos]<=CAPS[pos]);
      if(!legal)throw new Error('Illegal roster in simulation '+d+', team '+(i+1)+': '+keyRoster(roster));
      if(i!==slot-1)add(oppBuilds,keyRoster(roster));
    });
    add(combos,mine.slice(0,3).map(p=>p.name).join(' + '));
    const skill=mine.filter(p=>POS.includes(p.pos));
    totals.push({proj:mine.reduce((s,p)=>s+p.proj,0),value:mine.reduce((s,p)=>s+value(p),0),vor:skill.reduce((s,p)=>s+value(p)-(baseRep[p.pos]||0),0), roster:keyRoster(mine)});
    picks.forEach((id,i)=>{ if(!myPicks().includes(i+1)) { const p=byId.get(id); oppReach.push({name:p.name,delta:i+1-p.adp}); if(!pickedAt.has(p.id)) pickedAt.set(p.id,i+1); }});
  }
  const mean=k=>totals.reduce((s,x)=>s+x[k],0)/n;
  const sd=k=>{const m=mean(k);return Math.sqrt(totals.reduce((s,x)=>s+(x[k]-m)**2,0)/Math.max(1,n-1));};
  const names=PLAYERS.filter(p=>POS.includes(p.pos)).map(p=>({name:p.name,pos:p.pos,adp:p.adp,
    unavailable:unavailable.map((m,r)=>({r:r+1,p:(m.get(p.name)||0)/n})),
    first:firstAt.get(p.id), actual:pickedAt.get(p.id)}));
  const disappearing=names.map(x=>{const useful=x.unavailable.filter(z=>z.r<=10&&z.p>=.05&&z.p<=.95);return {...x,best:useful.sort((a,b)=>b.p-a.p)[0]};}).filter(x=>x.best).sort((a,b)=>b.best.p-a.best.p).slice(0,30);
  const reachAgg=new Map(); oppReach.forEach(x=>{const v=reachAgg.get(x.name)||{sum:0,n:0};v.sum+=x.delta;v.n++;reachAgg.set(x.name,v)});
  const systematicReaches=[...reachAgg].map(([name,v])=>({name,mean:v.sum/v.n,n:v.n,pos:PLAYERS.find(p=>p.name===name)?.pos,adp:PLAYERS.find(p=>p.name===name)?.adp})).filter(x=>x.pos&&POS.includes(x.pos)&&x.adp<900&&x.n>=n*.35&&x.mean<=-4).sort((a,b)=>a.mean-b.mean).slice(0,15);
  return {n, rounds:rounds.map(m=>top(m,10)), posByRound:posByRound.map(m=>top(m,8)), builds:Object.fromEntries(Object.entries(builds).map(([r,m])=>[r,top(m,10)])), combos:top(combos,15), oppBuilds:top(oppBuilds,15), totals:{meanProj:mean('proj'),sdProj:sd('proj'),meanValue:mean('value'),sdValue:sd('value'),meanVor:mean('vor'),sdVor:sd('vor')}, unavailable:disappearing, systematicReaches, myAdp, uniqueSignatures:signatures.size, exactRecommended};
}
const samples=SIM_SAMPLES;
globalThis.RESULT_RANDOM=simulate(samples,true);
globalThis.RESULT_CONTROL=simulate(Math.max(1,Math.round(samples/30)),false);
`;
const context={console, Math, Map, Set, Array, Object, JSON, SIM_RANDOM:true, SIM_MARKET:market, SIM_SEED_NAMES:seed,
  SIM_SAMPLES:Number(process.argv[2]||6000), SIM_TRACE:process.argv[4]==='trace', localStorage:{getItem:()=>null,setItem:()=>{}}, document:{querySelector:()=>({classList:{toggle:()=>{}},textContent:'',innerHTML:'',value:'',style:{}})}};
vm.createContext(context); vm.runInContext(engine+'\n'+harness,context,{timeout:300000});
fs.writeFileSync(process.argv[3]||'out/draft_slot3_simulation_raw.json',JSON.stringify({market,seed,random:context.RESULT_RANDOM,control:context.RESULT_CONTROL},null,2));
console.log(JSON.stringify({market,seed,random:context.RESULT_RANDOM,control:context.RESULT_CONTROL}));
