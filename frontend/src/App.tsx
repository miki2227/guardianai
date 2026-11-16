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

type Obj = Record<string, any>;
type FileRec = { path: string; text: string; json?: any; error?: string };
type Call = { id:string; label:string; argv?:string[]; verdict?:string|null; rc?:number|null; elapsed?:number; evidence?:string|null; events:Obj[]; actions:Obj[]; files:string[]; detail:Obj };
type Dataset = { title:string; description:string; files:Map<string,FileRec>; calls:Call[]; task?:string; closed?:boolean|null; stopped?:boolean|null; cancellation?:Obj; source:string };
const demoSets: Record<string,Dataset> = {
  grok: makeDataset('Grok build and review · real recorded run', 'research/coding-agent-runs/grok-v1/summary.json', {
    'summary.json':grokSummary,'session-completion/evidence/coding-session.json':codingSession,'session-completion/evidence/step-001/manifest.json':manifest,'session-completion/evidence/step-001/runtime.json':runtime,'session-completion/evidence/step-001/observer-input-0.json':observerInput,
  }, 'A real retained coding-agent run. Use the call list to switch between successful, policy-stopped and timed-out scopes in the summary.'),
  cancelled: makeDataset('Owner lifetime · normal build and cancellation', 'research/system-runs/owner-lifetime/summary.json', {
    'summary.json':ownerSummary,'normal/evidence/coding-session.json':normalSession,'cancelled/evidence/coding-session.json':cancelledSession,'cancellation.json':cancellation,
  }, 'A real GCC build completed normally; a separate actual build was cancelled by SIGKILL. The cancelled execution has no runtime verdict.'),
};
function makeDataset(title:string,source:string,raw:Record<string,any>,description:string):Dataset { const files=new Map<string,FileRec>(); for(const [path,json] of Object.entries(raw)) files.set(path,{path,text:JSON.stringify(json,null,2),json}); const ds={title,description,files,calls:[] as Call[],source}; return normalize(ds); }
function obj(x:any):Obj{return x&&typeof x==='object'&&!Array.isArray(x)?x:{}}
function normalize(ds:Dataset):Dataset {
  const calls:Call[]=[]; let task:string|undefined,closed:boolean|null=null,stopped:boolean|null=null;
  const all=[...ds.files.values()];
  const sess=all.find(f=>f.path.endsWith('coding-session.json'))?.json;
  const summary=all.find(f=>f.path==='summary.json')?.json;
  if(sess){ task=sess.task; closed=typeof sess.closed==='boolean'?sess.closed:null; stopped=typeof sess.scope_stopped==='boolean'?sess.scope_stopped:null;
    if(!summary?.scopes)
    for(const c of sess.calls??[]) calls.push({id:c.execution??`call-${calls.length+1}`,label:c.execution??'Command',argv:Array.isArray(c.argv)?c.argv:undefined,verdict:c.verdict??null,rc:c.returncode??null,evidence:c.evidence_status??null,events:[],actions:[],files:[],detail:c});
  }
  const runtimeFile=all.find(f=>f.path.endsWith('/runtime.json')||f.path==='runtime.json'); const rt=obj(runtimeFile?.json);
  const events=Array.isArray(rt.events)?rt.events:[];
  const actions=Array.isArray(rt.actions)?rt.actions:Array.isArray(rt.decisions)?rt.decisions:[];
  const manifestFile=all.find(f=>f.path.endsWith('/manifest.json')&&f.path.includes('step-001'));
  if(calls.length && !summary?.scopes){ const c=calls[0]!; c.events=events; c.actions=actions; c.files=all.filter(f=>f.path.includes('step-001')||f.path.includes('_observer')).map(f=>f.path); const mf=obj(manifestFile?.json); c.argv=c.argv??mf.argv; c.rc=c.rc??mf.returncode??rt.returncode??null; c.elapsed=mf.elapsed_seconds??rt.elapsed_seconds; c.verdict=c.verdict??rt.verdict??null; c.evidence=c.evidence??mf.evidence_status??null; c.detail={...c.detail, manifest:mf, runtime:rt}; }
  if(summary?.scopes){ for(const scope of summary.scopes) for(const c of scope.calls??[]) calls.push({id:`${scope.scope}/${c.execution}`,label:`${scope.scope} · ${c.execution}`,argv:undefined,verdict:c.verdict??null,rc:c.returncode??null,elapsed:c.elapsed_seconds,evidence:c.evidence_status??null,events:[],actions:[],files:[],detail:{...c,scope:scope.scope,client:scope.client}}); }
  if(summary?.scopes && (events.length||actions.length)) { const c=calls.find(x=>x.id==='session-completion/step-001'); if(c){const mf=obj(manifestFile?.json); c.events=events;c.actions=actions;c.files=all.filter(f=>f.path.includes('step-001')||f.path.includes('_observer')).map(f=>f.path);c.argv=mf.argv;c.elapsed=mf.elapsed_seconds;c.detail={...c.detail,manifest:mf,runtime:rt};} }
  const cancel=all.find(f=>f.path.endsWith('cancellation.json'))?.json;
  if(cancel && !calls.some(c=>c.label.toLowerCase().includes('cancel'))){ calls.push({id:'cancelled-owner',label:'Cancelled owner · GCC build',verdict:null,rc:cancel.owner_returncode??null,evidence:'incomplete',events:[],actions:[],files:['cancellation.json'],detail:cancel}); }
  return {...ds,task:task??(summary?.task),closed,stopped,cancellation:cancel,calls};
}
const stateLabel=(v:any,rc:any,evidence:any)=>{
 const s=String(v??'').toLowerCase();
 if(s==='no_observed_violation'||s==='review_cleared') return {text:'Successful observation',tone:'good'};
 if(s==='violation') return {text:'Violation observed',tone:'danger'};
 if(s==='abstain') return {text:'Observer abstained',tone:'warn'};
 if(s.includes('unavailable')) return {text:'Verdict unavailable',tone:'muted'};
 if(s==='blocked'||s==='denied') return {text:'Blocked',tone:'danger'};
 if(s==='interrupted') return {text:'Interrupted',tone:'warn'};
 if(typeof rc==='number'&&rc<0) return {text:'Interrupted',tone:'warn'};
 if(rc===null||rc===undefined) return {text:'Unknown outcome',tone:'muted'};
 if(rc!==0) return {text:`Nonzero exit · ${rc}`,tone:'warn'};
 if(evidence==='incomplete') return {text:'Incomplete evidence',tone:'warn'};
 return {text:'Recorded outcome',tone:'muted'};
};
const pretty=(x:any)=>x===null||x===undefined?'Not recorded':typeof x==='string'?x:JSON.stringify(x,null,2);
function App(){
 const [ds,setDs]=useState<Dataset>(demoSets.grok!); const [selected,setSelected]=useState(demoSets.grok!.calls.findIndex(c=>c.id==='session-completion/step-001')); const [query,setQuery]=useState(''); const [filter,setFilter]=useState('all'); const [tab,setTab]=useState<'events'|'decisions'|'files'>('events'); const [errors,setErrors]=useState<string[]>([]);
 const call=ds.calls[selected]??ds.calls[0];
 const visible=useMemo(()=>ds.calls.map((c,i)=>({c,i})).filter(({c})=>{const label=stateLabel(c.verdict,c.rc,c.evidence); return (!query||`${c.label} ${(c.argv??[]).join(' ')} ${c.verdict??''}`.toLowerCase().includes(query.toLowerCase()))&&(filter==='all'||label.tone===filter)}),[ds,query,filter]);
 async function importFolder(e:ChangeEvent<HTMLInputElement>){ const picked=Array.from(e.target.files??[]); if(!picked.length)return; const files=new Map<string,FileRec>(), errs:string[]=[]; for(const f of picked){const path=f.webkitRelativePath||f.name; try{const text=await f.text();let json:any; if(f.name.endsWith('.json'))try{json=JSON.parse(text)}catch{errs.push(`${path}: invalid JSON`)} files.set(path,{path,text,json});}catch{errs.push(`${path}: could not read file`)}} const next=normalize({title:picked[0]?.webkitRelativePath.split('/')[0]||'Imported run',description:'Imported locally in this browser. Files are not uploaded.',files,calls:[],source:'Local folder import'});setDs(next);setSelected(0);setErrors(errs);e.target.value=''; }
 function download(path:string){const f=ds.files.get(path);if(!f)return;const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([f.text],{type:'application/json'}));a.download=path.split('/').pop()||'evidence.json';a.click();URL.revokeObjectURL(a.href)}
 const loadDemo=(key:string)=>{const next=demoSets[key]!;setDs(next);setSelected(key==='grok'?next.calls.findIndex(c=>c.id==='session-completion/step-001'):0);setErrors([])};
 return <main className="app-shell">
  <header className="topbar"><div className="brand"><span className="brand-mark">G</span><span>GUARDIAN<span className="brand-light">AI</span></span></div><div className="top-meta"><span className="read-only"><i/>READ-ONLY EVIDENCE</span><button className="import-btn" onClick={()=>document.getElementById('folder-input')?.click()}>＋ Import run folder</button><input id="folder-input" type="file" hidden multiple onChange={importFolder} {...{webkitdirectory:'',directory:''} as any}/></div></header>
  <div className="demo-strip"><span className="demo-label">REAL RUN EXAMPLES</span><button className={ds===demoSets.grok?'active':''} onClick={()=>loadDemo('grok')}>Grok build &amp; review</button><button className={ds===demoSets.cancelled?'active':''} onClick={()=>loadDemo('cancelled')}>Owner cancellation</button><span className="strip-note">Bundled from retained repository JSON</span></div>
  <section className="run-heading"><div><div className="eyebrow">RECORDED EXECUTION / LOCAL INSPECTION</div><h1>{ds.title}</h1><p>{ds.description}</p></div><div className="run-source"><span>Source</span><code>{ds.source}</code></div></section>
  {errors.length>0&&<div className="error-box"><b>Some files could not be parsed</b>{errors.map(x=><div key={x}>{x}</div>)}</div>}
  <section className="summary-grid">
   <div className="metric"><span>WORKER COMMANDS</span><strong>{ds.calls.length||'—'}</strong><small>{ds.calls.length?'from available session and summary files':'No command records found'}</small></div>
   <div className="metric"><span>SYSCALL EVENTS</span><strong>{call?.events.length||'—'}</strong><small>{call?.events.length?'loaded from runtime.json':'Not available for selected scope'}</small></div>
   <div className="metric"><span>CAPTURE STATUS</span><strong className="small-strong">{call?.evidence??'Unknown'}</strong><small>“Recorded” does not imply complete telemetry</small></div>
   <div className="metric"><span>LIFECYCLE</span><strong className="small-strong">{ds.closed===null?'Not recorded':ds.closed?'Closed':'Open / incomplete'}</strong><small>Scope stopped: {ds.stopped===null?'unknown':ds.stopped?'yes':'no'}</small></div>
  </section>
  <div className="layout">
   <aside className="call-panel"><div className="panel-title"><div><span className="eyebrow">RUN WORK</span><h2>Worker commands</h2></div><span className="count-pill">{ds.calls.length}</span></div>
    <div className="filters"><input aria-label="Search commands" placeholder="Search commands…" value={query} onChange={e=>setQuery(e.target.value)}/><select aria-label="Filter outcomes" value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All outcomes</option><option value="good">Successful observation</option><option value="danger">Blocked / violation</option><option value="warn">Abstain / incomplete</option><option value="muted">Unknown / other</option></select></div>
    <div className="call-list">{visible.map(({c,i})=>{const badge=stateLabel(c.verdict,c.rc,c.evidence);return <button key={c.id} className={`call-row ${selected===i?'selected':''}`} onClick={()=>setSelected(i)}><div className="call-row-head"><b>{c.label}</b><span className={`dot ${badge.tone}`}/></div><code>{c.argv?.join(' ')??(c.detail.scope?`scope ${c.detail.scope} · ${c.id.split('/').pop()}`:'Command unavailable')}</code><div className="call-row-foot"><span className={`mini-badge ${badge.tone}`}>{badge.text}</span><span>{c.elapsed!==undefined?`${c.elapsed.toFixed(2)}s`:c.rc===null?'—':`exit ${c.rc}`}</span></div></button>})}{!visible.length&&<div className="empty">No commands match this filter.</div>}{!ds.calls.length&&<div className="empty">No supported command records found. Select a run folder containing coding-session.json or a recognized summary.json.</div>}</div>
    <div className="task-card"><span className="eyebrow">DECLARED TASK</span><p>{ds.task??'Task text not present in imported files.'}</p></div>
   </aside>
   <section className="detail-panel"><div className="detail-head"><div><span className="eyebrow">SELECTED WORKER · {call?.id??'NO SELECTION'}</span><h2>{call?.label??'No command selected'}</h2></div>{call&&<span className={`status-pill ${stateLabel(call.verdict,call.rc,call.evidence).tone}`}>{stateLabel(call.verdict,call.rc,call.evidence).text}</span>}</div>
    {call&&<><div className="facts"><div><span>RETURN CODE</span><b>{call.rc===undefined?'Unknown':call.rc===null?'Not recorded':call.rc}</b></div><div><span>ELAPSED</span><b>{call.elapsed===undefined?'Not recorded':`${call.elapsed.toFixed(3)} s`}</b></div><div><span>RUNTIME VERDICT</span><b>{call.verdict??'Unavailable'}</b></div><div><span>CAPTURE</span><b>{call.evidence??'Unknown'}</b></div></div><div className="argv-block"><span className="eyebrow">ARGV</span><pre>{call.argv?JSON.stringify(call.argv,null,2):'Command arguments are not present in this summary.'}</pre></div>
    <div className="tabbar"><button className={tab==='events'?'on':''} onClick={()=>setTab('events')}>Syscall timeline <span>{call.events.length}</span></button><button className={tab==='decisions'?'on':''} onClick={()=>setTab('decisions')}>Jev decisions <span>{call.actions.length}</span></button><button className={tab==='files'?'on':''} onClick={()=>setTab('files')}>Evidence files <span>{call.files.length||ds.files.size}</span></button></div>
    <div className="tab-content">{tab==='events'&&<EventView events={call.events}/>}{tab==='decisions'&&<DecisionView actions={call.actions} files={ds.files}/>}{tab==='files'&&<FileView files={ds.files} call={call} download={download}/>}</div>
    </>}
   </section>
  </div>
  <footer><span>GuardianAI · local evidence viewer</span><span>Imported files stay in this browser session · no execution controls</span></footer>
 </main>
}
function EventView({events}:{events:Obj[]}){const [active,setActive]=useState<number|null>(null);if(!events.length)return <div className="empty large-empty"><strong>No syscall timeline available</strong><span>This selected record has no loaded runtime events. Missing evidence is shown as unavailable.</span></div>;return <div className="event-layout"><div className="timeline">{events.slice(0,2000).map((e,i)=><button key={i} className={`event-row ${active===i?'chosen':''} ${e.rule_violation||e.permission_denied?'event-alert':''}`} onClick={()=>setActive(i)}><span className="event-time">{typeof e.timestamp==='number'?new Date(e.timestamp*1000).toISOString().slice(11,23):e.elapsed_seconds!==undefined?`${e.elapsed_seconds.toFixed(3)}s`:'—'}</span><span className="event-name">{e.syscall??e.name??'Event'}</span><span className="event-path">{(e.paths??(e.path?[e.path]:[])).join(', ')||'Path not recorded'}</span><span className={`event-state ${e.permission_denied||e.rule_violation?'red':''}`}>{e.permission_denied?'permission denied':e.rule_violation?'rule violation':e.errno?`errno ${e.errno}`:'observed'}</span></button>)}</div><div className="event-detail">{active===null?<div className="empty">Select an event to inspect its fields and native stack.</div>:<><div className="event-detail-title"><span className="eyebrow">EVENT {events[active]?.event_index??active}</span><h3>{events[active]?.syscall??events[active]?.name??'Event detail'}</h3></div><div className="detail-pairs">{[['Source',events[active]?.source],['Timestamp',events[active]?.timestamp],['Elapsed',events[active]?.elapsed_seconds],['Paths',events[active]?.paths],['Errno',events[active]?.errno],['Permission denied',events[active]?.permission_denied],['Rule violation',events[active]?.rule_violation],['Legacy denied flag',events[active]?.denied]].map(([k,v])=><div key={String(k)}><span>{k}</span><b>{pretty(v)}</b></div>)}</div>{Array.isArray(events[active]?.native_stack)&&<><span className="eyebrow stack-label">NATIVE EXECUTION STACK</span><pre className="stack">{events[active].native_stack.join('\n')}</pre></>}</>}</div></div>}
function DecisionView({actions,files}:{actions:Obj[];files:Map<string,FileRec>}){const actionFile=[...files.values()].find(f=>f.path.endsWith('runtime.json'));const data=actions.length?actions:actionFile?.json?.actions??[];if(!data.length)return <div className="empty large-empty"><strong>No Jev decision records available</strong><span>Observer receipts may be saved in the imported folder, but this format has no joined decision for the selected worker.</span></div>;return <div className="decision-list">{data.map((a:any,i:number)=><article className="decision" key={i}><div className="decision-top"><b>{a.action??a.verdict??`Decision ${i+1}`}</b><span>{a.elapsed_seconds??a.elapsed??'time unavailable'}</span></div><div className="decision-grid"><div><span>Probability</span><b>{a.probability??a.score??'Not recorded'}</b></div><div><span>Model</span><b>{a.model??'Not recorded'}</b></div><div><span>Decision</span><b>{a.verdict??a.decision??'Not recorded'}</b></div><div><span>Observer input</span><b>{a.session_observer_input??a.input_path??'Not linked'}</b></div></div><details><summary>Raw saved decision</summary><pre>{JSON.stringify(a,null,2)}</pre></details></article>)}</div>}
function FileView({files,call,download}:{files:Map<string,FileRec>;call:Call;download:(x:string)=>void}){const rows=[...files.values()];const manifestFile=rows.find(f=>f.path.endsWith('manifest.json'));const receipt=obj(manifestFile?.json?.files);return <div className="file-list">{call.evidence==='incomplete'&&<div className="error-box"><b>Capture incomplete.</b> Final runtime evidence is missing or could not be flushed. This viewer does not fill in a verdict or missing events.</div>}{rows.map(f=><div className="file-row" key={f.path}><div><b>{f.path}</b><small>{f.error??`${new Blob([f.text]).size.toLocaleString()} bytes · ${f.json?'JSON parsed':'text file'}`}</small>{f.path.endsWith('manifest.json')&&Object.keys(receipt).length>0&&<small>Recorded file hash receipts: {Object.keys(receipt).length} entries · values retained in the original manifest</small>}</div><button onClick={()=>download(f.path)} disabled={!f.json}>Download JSON</button></div>)}{call.detail?.processes&&<details className="raw-record" open><summary>Cancellation observation · {call.detail.processes.length} captured processes</summary><pre>{JSON.stringify(call.detail,null,2)}</pre></details>}{call.detail?.cancellation&&<details className="raw-record"><summary>Cancellation observation record</summary><pre>{JSON.stringify(call.detail.cancellation,null,2)}</pre></details>}</div>}

export default App;
