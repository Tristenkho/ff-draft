/* Read-only rank audit of the actual embedded engine; never loads browser state. */
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('out/draft_terminal.html', 'utf8');
const start = html.indexOf('const TEAMS=12, ROUNDS=14;');
const end = html.indexOf('// ── render ───────────────────────────────────────');
if (start < 0 || end <= start) throw new Error('Embedded engine not found');
const context = {
  localStorage: {getItem: () => null, setItem: () => {throw new Error('Audit attempted a storage write');}},
  document: {querySelector: () => ({classList: {toggle: () => {}}, style: {}})},
  setTimeout: () => 0, clearTimeout: () => {},
};
vm.createContext(context);
vm.runInContext(html.slice(start, end) + `
  slot=3; lambda=.40; ecrWeight=.35; picks=[];
  const auditMeta=modelMeta();
  const auditReplacement=replacement(skillPool(),p=>p.proj).rep;
  const fullVorRank=new Map([...skillPool()].sort((a,b)=>(b.proj-auditReplacement[b.pos])-(a.proj-auditReplacement[a.pos])).map((p,i)=>[p.id,i+1]));
  globalThis.audit={
    projection:PROJECTION_META, market:MARKET_META, consensus:ECR_META,
    replacement:auditReplacement,
    rows:skillPool().map(p=>({
      name:p.name,pos:p.pos,model:auditMeta.modelRank.get(p.id),
      core:auditMeta.coreRank.get(p.id),ecr:p.ecr,skillEcr:auditMeta.ecrRank(p),
      fullVorRank:fullVorRank.get(p.id),
      gap:auditMeta.ecrRank(p)-auditMeta.modelRank.get(p.id),
      proj:p.proj,sources:p.proj_sources,espn:p.adp,market:p.market_adp,
      status:p.status,expertRange:[p.ecr_min,p.ecr_max],
      fdRec:p.fd_rec_rate,sdRatio:p.sd/p.proj,
    })).sort((a,b)=>a.model-b.model),
    excluded:PLAYERS.filter(p=>POS.includes(p.pos)&&!modelDraftable(p))
      .map(p=>({name:p.name,status:p.status,ecr:p.ecr,proj:p.proj})),
  };
`, context, {timeout: 30000});
console.log(JSON.stringify(context.audit, null, 2));
