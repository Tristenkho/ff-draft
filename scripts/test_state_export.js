/* Exercise the real export with synthetic states, without reading/writing a live ledger. */
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync('out/draft_terminal.html', 'utf8');
const start = html.indexOf('const TEAMS=12, ROUNDS=14;');
const end = html.indexOf('// ── event listeners');
assert(start >= 0 && end > start);
const context = {
  localStorage: {getItem: () => null, setItem: () => {throw new Error('Export wrote state');}},
  document: {querySelector: () => ({classList: {toggle: () => {}}, style: {}})},
  setTimeout: () => 0, clearTimeout: () => {}, assert,
};
vm.createContext(context);
vm.runInContext(html.slice(start, end) + String.raw`
  slot=3; picks=PLAYERS.filter(p=>['Jahmyr Gibbs','Bijan Robinson'].includes(p.name)).map(p=>p.id);
  const before=JSON.stringify({picks,queue,queueArchive,autoPickNos});
  const text=buildState();
  assert(text.includes('ECR → Model → gain'));
  assert(text.includes('MEASURED MODEL LIMITS'));
  const section=text.split('CONSENSUS ALTERNATIVES OUTSIDE TOP EIGHT')[1].split('UNAVAILABLE / LOW-COVERAGE')[0];
  const names=[...section.matchAll(/  · (.*?) \(/g)].map(m=>m[1]);
  assert.equal(names.length,12);
  assert.equal(new Set(names).size,12);
  assert(!computeBoard().slice(0,8).some(r=>names.includes(r.p.name)));
  assert(!names.includes('Jahmyr Gibbs')&&!names.includes('Bijan Robinson'));
  assert(!names.includes('Josh Jacobs'));
  assert(text.includes('Josh Jacobs (RB, ECR'));
  assert.equal(JSON.stringify({picks,queue,queueArchive,autoPickNos}),before);
  // A second QB can be reviewed without being falsely presented as policy-eligible.
  picks.push(PLAYERS.find(p=>p.name==='Josh Allen').id);
  picks.push(...remaining().filter(p=>p.pos!=='QB').sort((a,b)=>a.ecr-b.ecr).slice(0,18).map(p=>p.id));
  assert(buildState().includes('POLICY BLOCK: QB2 belongs on waivers'));
`, context, {timeout: 30000});
console.log('State export checks passed');
