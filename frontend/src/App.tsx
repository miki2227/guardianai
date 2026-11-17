import { useMemo, useState } from 'react';
import type { ChangeEvent } from 'react';
import grokSummary from './demo/grok-summary.json';
import codingSession from './demo/coding-session.json';
import manifest from './demo/step-001-manifest.json';
import runtime from './demo/step-001-runtime.json';
import observerInput from './demo/step-001-observer-input.json';
import ownerSummary from './demo/owner-summary.json';
import cancellation from './demo/cancellation.json';
import cancelledSession from './demo/cancelled-session.json';
import normalSession from './demo/normal-session.json';

import { makeDataset, normalize, obj, stateLabel, importable } from './lib/evidence';
import type { Obj, FileRec, Call, Dataset } from './lib/evidence';

const pairedRaw = import.meta.glob('./demo/paired/**/*', { query: '?raw', import: 'default', eager: true }) as Record<string, string>;
const pairedFiles = new Map<string, FileRec>();
for (const [name, text] of Object.entries(pairedRaw)) {
 const path = name.slice('./demo/paired/'.length);
 pairedFiles.set(path, { path, text, json: path.endsWith('.json') ? JSON.parse(text) : undefined });
}
const demoSets: Record<string,Dataset> = {
 paired: normalize({ title: 'Two agents · Checkstyle investigation', source: 'research/checkstyle-paired/v5', description: 'Two continuing Grok agents completed investigation, review and reconciliation under GuardianAI. Nine commands and two public artifact handoffs. No P0 or covert convention was validated.', files: pairedFiles, calls: [] }),
  grok: makeDataset('Build and review', 'research/coding-agent-runs/grok-v1/summary.json', {
    'summary.json':grokSummary,'session-completion/evidence/coding-session.json':codingSession,'session-completion/evidence/step-001/manifest.json':manifest,'session-completion/evidence/step-001/runtime.json':runtime,'session-completion/evidence/step-001/observer-input-0.json':observerInput,
  }, 'A real retained coding-agent run. Use the call list to switch between successful, policy-stopped and timed-out scopes in the summary.'),
  cancelled: makeDataset('Owner lifetime · normal build and cancellation', 'research/system-runs/owner-lifetime/summary.json', {
    'summary.json':ownerSummary,'normal/evidence/coding-session.json':normalSession,'cancelled/evidence/coding-session.json':cancelledSession,'cancellation.json':cancellation,
  }, 'A real GCC build completed normally; a separate actual build was cancelled by SIGKILL. The cancelled execution has no runtime verdict.'),
};
const pretty=(x:any)=>x===null||x===undefined?'Not recorded':typeof x==='string'?x:JSON.stringify(x,null,2);
function App(){
 const [ds,setDs]=useState<Dataset>(demoSets.paired!); const [selected,setSelected]=useState(0); const [query,setQuery]=useState(''); const [filter,setFilter]=useState('all'); const [tab,setTab]=useState<'events'|'decisions'|'files'|'output'|'content'>('events'); const [errors,setErrors]=useState<string[]>([]);
 const call=ds.calls[selected]??ds.calls[0];
 const visible=useMemo(()=>ds.calls.map((c,i)=>({c,i})).filter(({c})=>{const label=stateLabel(c.verdict,c.rc,c.evidence); return (!query||`${c.label} ${(c.argv??[]).join(' ')} ${c.verdict??''}`.toLowerCase().includes(query.toLowerCase()))&&(filter==='all'||label.tone===filter)}),[ds,query,filter]);
 async function importFolder(e:ChangeEvent<HTMLInputElement>){
  const picked=Array.from(e.target.files??[]); if(!picked.length)return;
  const files=new Map<string,FileRec>(), errs:string[]=[]; let total=0, skipped=0;
  for(const f of picked){
   const full=f.webkitRelativePath||f.name, path=f.webkitRelativePath?full.slice(full.indexOf('/')+1):full;
   const reason=importable(path,f.size,total); if(reason){skipped++;if(errs.length<20)errs.push(`${path}: skipped (${reason})`);continue;}
   total+=f.size;
   try{const text=await f.text();let json:any;let error:string|undefined;
    if(f.name.endsWith('.json'))try{json=JSON.parse(text)}catch{error='Invalid JSON';errs.push(`${path}: invalid JSON`)}
    files.set(path,{path,text,json,error});
   }catch{errs.push(`${path}: could not read file`)}
  }
  if(skipped)errs.push(`${skipped} files skipped in total; supported text remains available.`);
  setDs(normalize({title:picked[0]?.webkitRelativePath.split('/')[0]||'Imported run',description:'Imported locally in this browser. Files are not uploaded.',files,calls:[],source:'Local folder import'}));
  setSelected(0);setQuery('');setFilter('all');setErrors(errs);e.target.value='';
 }
 function download(path:string){const f=ds.files.get(path);if(!f)return;const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([f.text],{type:'text/plain;charset=utf-8'}));a.download=path.split('/').pop()||'evidence.json';a.click();URL.revokeObjectURL(a.href)}
 const loadDemo=(key:string)=>{const next=demoSets[key]!;setDs(next);setSelected(key==='grok'?next.calls.findIndex(c=>c.id==='session-completion/step-001'):0);setErrors([]);setQuery('');setFilter('all')};
 return <main className="app-shell">
  <header className="topbar"><div className="brand"><span className="brand-mark">G</span><span>GUARDIAN<span className="brand-light">AI</span></span></div><div className="top-meta"><span className="read-only"><i/>READ-ONLY EVIDENCE</span><button className="import-btn" onClick={()=>document.getElementById('folder-input')?.click()}>＋ Import run folder</button><input id="folder-input" type="file" hidden multiple onChange={importFolder} {...{webkitdirectory:'',directory:''} as any}/></div></header>
  <div className="demo-strip"><span className="demo-label">REAL RUN EXAMPLES</span><button className={ds===demoSets.paired?'active':''} onClick={()=>loadDemo('paired')}>Two-agent Checkstyle</button><button className={ds===demoSets.grok?'active':''} onClick={()=>loadDemo('grok')}>Grok build &amp; review</button><button className={ds===demoSets.cancelled?'active':''} onClick={()=>loadDemo('cancelled')}>Owner cancellation</button><span className="strip-note">Bundled from retained repository JSON</span></div>
  <section className="run-heading"><div><div className="eyebrow">RECORDED EXECUTION / LOCAL INSPECTION</div><h1>{ds.title}</h1><p>{ds.description}</p></div><div className="run-source"><span>Source</span><code>{ds.source}</code></div></section>
  {errors.length>0&&<div className="error-box"><b>Import notes</b>{errors.map(x=><div key={x}>{x}</div>)}</div>}
  <section className="summary-grid">
   <div className="metric"><span>WORKER COMMANDS</span><strong>{ds.calls.length||'—'}</strong><small>{ds.calls.length?'from available session and summary files':'No command records found'}</small></div>
   <div className="metric"><span>SYSCALL EVENTS</span><strong>{call?.events.length||'—'}</strong><small>{call?.events.length?'loaded from runtime.json':'Not available for selected scope'}</small></div>
   <div className="metric"><span>CAPTURE STATUS</span><strong className="small-strong">{call?.evidence??'Unknown'}</strong><small>“Recorded” does not imply complete telemetry</small></div>
   <div className="metric"><span>LIFECYCLE</span><strong className="small-strong">{call?.closed==null?'Not recorded':call?.closed?'Closed':'Open / incomplete'}</strong><small>Scope stopped: {call?.stopped==null?'unknown':call?.stopped?'yes':'no'}</small></div>
  </section>
  <RunEvidence ds={ds}/><div className="layout">
   <aside className="call-panel"><div className="panel-title"><div><span className="eyebrow">RUN WORK</span><h2>Worker commands</h2></div><span className="count-pill">{ds.calls.length}</span></div>
    <div className="filters"><input aria-label="Search commands" placeholder="Search commands…" value={query} onChange={e=>setQuery(e.target.value)}/><select aria-label="Filter outcomes" value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All outcomes</option><option value="good">No violation observed · exit 0</option><option value="danger">Blocked / violation</option><option value="warn">Abstain / incomplete</option><option value="muted">Unknown / other</option></select></div>
    <div className="call-list">{visible.map(({c,i})=>{const badge=stateLabel(c.verdict,c.rc,c.evidence);return <button key={c.id} className={`call-row ${selected===i?'selected':''}`} onClick={()=>setSelected(i)}><div className="call-row-head"><b>{c.label}</b><span className={`dot ${badge.tone}`}/></div><code>{c.argv?.join(' ')??(c.detail.scope?`scope ${c.detail.scope} · ${c.id.split('/').pop()}`:'Command unavailable')}</code><div className="call-row-foot"><span className={`mini-badge ${badge.tone}`}>{badge.text}</span><span>{c.elapsed!==undefined?`${c.elapsed.toFixed(2)}s`:c.rc===null?'—':`exit ${c.rc}`}</span></div></button>})}{!visible.length&&<div className="empty">No commands match this filter.</div>}{!ds.calls.length&&<div className="empty">No supported command records found. Select a run folder containing coding-session.json or a recognized summary.json.</div>}</div>
    <div className="task-card"><span className="eyebrow">DECLARED TASK</span><p>{call?.task??ds.task??'Task text not present in imported files.'}</p></div>
   </aside>
   <section className="detail-panel"><div className="detail-head"><div><span className="eyebrow">SELECTED WORKER · {call?.id??'NO SELECTION'}</span><h2>{call?.label??'No command selected'}</h2></div>{call&&<span className={`status-pill ${stateLabel(call.verdict,call.rc,call.evidence).tone}`}>{stateLabel(call.verdict,call.rc,call.evidence).text}</span>}</div>
    {call&&<><div className="facts"><div><span>RETURN CODE</span><b>{call.rc===undefined?'Unknown':call.rc===null?'Not recorded':call.rc}</b></div><div><span>ELAPSED</span><b>{call.elapsed===undefined?'Not recorded':`${call.elapsed.toFixed(3)} s`}</b></div><div><span>RUNTIME VERDICT</span><b>{call.verdict??'Unavailable'}</b></div><div><span>CAPTURE</span><b>{call.evidence??'Unknown'}</b></div></div><div className="argv-block"><span className="eyebrow">ARGV</span><pre>{call.argv?JSON.stringify(call.argv,null,2):'Command arguments are not present in this summary.'}</pre></div>
    <div className="tabbar"><button className={tab==='content'?'on':''} onClick={()=>setTab('content')}>Message observation (phase)</button><button className={tab==='output'?'on':''} onClick={()=>setTab('output')}>Command output</button><button className={tab==='events'?'on':''} onClick={()=>setTab('events')}>Syscall timeline <span>{call.events.length}</span></button><button className={tab==='decisions'?'on':''} onClick={()=>setTab('decisions')}>Jev decisions <span>{call.actions.length}</span></button><button className={tab==='files'?'on':''} onClick={()=>setTab('files')}>Evidence files <span>{call.files.length}</span></button></div>
    <div className="tab-content">{tab==='events'&&<EventView key={call.id} events={call.events}/>}{tab==='decisions'&&<DecisionView actions={call.actions} files={ds.files} call={call}/>}{tab==='content'&&<ContentView files={ds.files} call={call}/>} {tab==='output'&&<OutputView files={ds.files} call={call}/>} {tab==='files'&&<FileView key={call.id} files={ds.files} call={call} download={download}/>}</div>
    </>}
   </section>
  </div>
  <footer><span>GuardianAI · local evidence viewer</span><span>Imported files stay in this browser session · no execution controls</span></footer>
 </main>
}
function EventView({events}:{events:Obj[]}){const [active,setActive]=useState<number|null>(null);if(!events.length)return <div className="empty large-empty"><strong>No syscall timeline available</strong><span>This selected record has no loaded runtime events. Missing evidence is shown as unavailable.</span></div>;return <div className="event-layout"><div className="timeline">{events.slice(0,2000).map((e,i)=><button key={i} className={`event-row ${active===i?'chosen':''} ${e.rule_violation||e.permission_denied?'event-alert':''}`} onClick={()=>setActive(i)}><span className="event-time">{typeof e.timestamp==='number'&&Number.isFinite(e.timestamp)&&Math.abs(e.timestamp)<8.64e12?new Date(e.timestamp*1000).toISOString().slice(11,23):typeof e.elapsed_seconds==='number'?`${e.elapsed_seconds.toFixed(3)}s`:'—'}</span><span className="event-name">{String(e.syscall??e.name??'Event')}</span><span className="event-path">{(Array.isArray(e.paths)?e.paths.map(String):typeof e.path==='string'?[e.path]:[]).join(', ')||'Path not recorded'}</span><span className={`event-state ${e.permission_denied||e.rule_violation?'red':''}`}>{e.permission_denied?'permission denied':e.rule_violation?'rule violation':e.errno?`errno ${e.errno}`:'observed'}</span></button>)}</div><div className="event-detail">{active===null?<div className="empty">Select an event to inspect its fields and native stack.</div>:<><div className="event-detail-title"><span className="eyebrow">EVENT {String(events[active]?.event_index??active)}</span><h3>{String(events[active]?.syscall??events[active]?.name??'Event detail')}</h3></div><div className="detail-pairs">{[['Source',events[active]?.source],['Timestamp',events[active]?.timestamp],['Elapsed',events[active]?.elapsed_seconds],['Paths',events[active]?.paths],['Errno',events[active]?.errno],['Permission denied',events[active]?.permission_denied],['Rule violation',events[active]?.rule_violation],['Legacy denied flag',events[active]?.denied]].map(([k,v])=><div key={String(k)}><span>{k}</span><b>{pretty(v)}</b></div>)}</div>{Array.isArray(events[active]?.native_stack)&&<><span className="eyebrow stack-label">NATIVE EXECUTION STACK</span><pre className="stack">{events[active].native_stack.join('\n')}</pre></>}</>}</div></div>}
function DecisionView({actions,files,call}:{actions:Obj[];files:Map<string,FileRec>;call:Call}){
 if(!actions.length)return <div className="empty large-empty"><strong>No Jev decision records available</strong><span>No exact runtime decision join exists for this worker.</span></div>;
 return <div className="decision-list">{actions.map((a,i)=>{
  const runtimePath=typeof a.runtime_observer_input==='string'?call.base+a.runtime_observer_input:undefined;
  const sessionPath=typeof a.session_observer_input==='string'?call.base.replace(/step-\d+\/$/,'')+a.session_observer_input:undefined;
  return <article className="decision" key={i}><div className="decision-top"><b>{String(a.action??`Decision ${i+1}`)}</b><span>{String(a.elapsed_seconds??a.elapsed??'time unavailable')}</span></div>
   <div className="decision-grid"><div><span>Probability</span><b>{pretty(a.probability??a.score)}</b></div><div><span>Model</span><b>{pretty(a.model)}</b></div><div><span>Applied / deadline met</span><b>{pretty(a.decision_applied)} / {pretty(a.deadline_met)}</b></div><div><span>Observer input</span><b>{runtimePath??sessionPath??'Not linked'}</b></div></div>
   {[runtimePath,sessionPath].filter((p):p is string=>!!p).map(path=><details key={path}><summary>{files.has(path)?'Saved input available':'Saved input missing'} · {path}</summary><pre>{files.get(path)?.text??'Receipt reference only; input was not imported. Hash has not been recomputed by this viewer.'}</pre></details>)}
   <details><summary>Raw saved decision and hash references</summary><pre>{pretty(a)}</pre></details>
  </article>})}</div>
}
function ContentView({files,call}:{files:Map<string,FileRec>;call:Call}){
 const phase=call.base.split('/evidence/')[0];
 const rows=[...files.values()].filter(f=>f.path.startsWith(`${phase}-client/agent-content/decision-`)||f.path.startsWith(`${phase}/evidence/_content/decision-`));
 return <div className="decision-list"><p>These records cover the selected phase, including messages and tool requests or results. They are not all attributable to this worker. Saved scores describe observed content; they do not reveal private thoughts.</p>
  {rows.map(f=><details className="decision" key={f.path}><summary>{f.path} · {String(obj(f.json).verdict??'receipt')}</summary><pre>{f.text}</pre></details>)}
  {!rows.length&&<div className="empty">No matching phase content receipts were imported.</div>}
 </div>;
}
function OutputView({files,call}:{files:Map<string,FileRec>;call:Call}){
 const rows=[...files.values()].filter(f=>f.path===`${call.base}stdout.txt`||f.path===`${call.base}stderr.txt`);
 return rows.length?<div>{rows.map(f=><article className="decision" key={f.path}><b>{f.path}</b><pre>{f.text||'(empty)'}</pre></article>)}</div>:<div className="empty">No stdout/stderr files were retained or imported for this worker.</div>;
}
function RunEvidence({ds}:{ds:Dataset}){
 if(!ds.acceptance&&!ds.handoffs?.length)return null;
 return <section className="run-evidence"><h2>Workflow evidence</h2>
  {ds.acceptance&&<details><summary>{ds.acceptance.path==='audit.json'?'Saved host audit':'Workflow not accepted'} · {ds.acceptance.path}</summary><pre>{ds.acceptance.text}</pre></details>}
  {(ds.handoffs??[]).map(f=>{const j=obj(f.json);return <details key={f.path}><summary>{String(j.sender??'Unknown sender')} → {String(j.recipient??'unknown recipient')} · {j.delivered===true?'delivery recorded':j.delivered===false?'not delivered':'delivery unknown'}</summary><p>Flow policy: {String(obj(j.information_flow).mode??'not recorded')}. File hashes below are saved receipts; this viewer does not independently verify delivery.</p><pre>{f.text}</pre>{Object.keys(obj(j.files_sha256)).map(name=>{const p=f.path.slice(0,f.path.lastIndexOf('/')+1)+name;return <pre key={p}>{ds.files.get(p)?.text??`Artifact not imported: ${p}`}</pre>})}</details>})}
 </section>
}
function FileView({files,call,download}:{files:Map<string,FileRec>;call:Call;download:(x:string)=>void}){
 const [all,setAll]=useState(false);const rows=[...files.values()].filter(f=>all||call.files.includes(f.path));
 return <div className="file-list"><label><input type="checkbox" checked={all} onChange={e=>setAll(e.target.checked)}/> Show all run files (outside this worker)</label>
  {call.evidence==='incomplete'&&<div className="error-box">Capture incomplete. Missing events and verdicts remain unavailable.</div>}
  {rows.map(f=><div className="file-row" key={f.path}><div><b>{f.path}</b><small>{f.error??`${new Blob([f.text]).size.toLocaleString()} bytes · ${f.json!==undefined?'JSON parsed':'text file'}`}</small>{f.path.endsWith('/manifest.json')&&<small>Saved file hash receipts: {Object.keys(obj(obj(f.json).files)).length}. Hashes are not recomputed in the viewer.</small>}</div><button onClick={()=>download(f.path)}>Download file</button></div>)}
  {!rows.length&&<div className="empty">No files joined to this worker. Select “Show all run files” to inspect unjoined evidence.</div>}
 </div>
}

export default App;
