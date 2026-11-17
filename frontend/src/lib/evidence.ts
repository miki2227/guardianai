export type Obj = Record<string, any>;
export type FileRec = { path: string; text: string; json?: any; error?: string };
export type Call = { id: string; label: string; argv?: string[]; verdict: string|null; rc: number|null; elapsed?: number; evidence: string|null; events: Obj[]; actions: Obj[]; files: string[]; base: string; task?: string; closed: boolean|null; stopped: boolean|null; detail: Obj };
export type Dataset = { title: string; description: string; source: string; files: Map<string, FileRec>; calls: Call[]; task?: string; closed?: boolean|null; stopped?: boolean|null; handoffs?: FileRec[]; acceptance?: FileRec; cancellation?: Obj };
export const obj = (x: any): Obj => x && typeof x === 'object' && !Array.isArray(x) ? x : {};
const records = (x: any): Obj[] => Array.isArray(x) ? x.filter(v => v && typeof v === 'object' && !Array.isArray(v)) : [];
const str = (x: any): string|undefined => typeof x === 'string' ? x : undefined;
const num = (x: any): number|undefined => typeof x === 'number' && Number.isFinite(x) ? x : undefined;
const bool = (x: any): boolean|null => typeof x === 'boolean' ? x : null;
const dir = (path: string) => path.slice(0, path.lastIndexOf('/') + 1);

export function makeDataset(title: string, source: string, raw: Record<string, any>, description: string): Dataset {
  const files = new Map<string, FileRec>();
  for (const [path, json] of Object.entries(raw)) files.set(path, { path, text: JSON.stringify(json, null, 2), json });
  return normalize({ title, source, description, files, calls: [] });
}

export function normalize(ds: Dataset): Dataset {
  const all = [...ds.files.values()];
  const calls = new Map<string, Call>();
  const sessions = all.filter(f => /(^|\/)coding-session\.json$/.test(f.path));
  function join(c: Obj, base: string, scope: string, session: Obj) {
    const execution = str(c.execution);
    if (!execution || !/^step-\d+$/.test(execution)) return;
    const worker = `${base}${execution}/`;
    const rt = obj(ds.files.get(`${worker}runtime.json`)?.json);
    const mf = obj(ds.files.get(`${worker}manifest.json`)?.json);
    const id = `${scope ? `${scope}/` : ''}${execution}`;
    const argv = c.argv ?? mf.argv;
    calls.set(id, {
      id, label: id.replaceAll('/', ' · '), base: worker,
      argv: Array.isArray(argv) && argv.every(v => typeof v === 'string') ? argv : undefined,
      verdict: str(c.verdict) ?? str(rt.verdict) ?? null,
      rc: num(c.returncode) ?? num(mf.returncode) ?? num(rt.returncode) ?? null,
      elapsed: num(c.elapsed_seconds) ?? num(mf.elapsed_seconds) ?? num(rt.elapsed_seconds),
      evidence: str(c.evidence_status) ?? str(rt.evidence_status) ?? str(mf.evidence_status) ?? null,
      events: records(rt.events), actions: records(rt.actions ?? rt.decisions),
      files: all.filter(f => f.path.startsWith(worker)).map(f => f.path),
      task: str(session.task), closed: bool(session.closed), stopped: bool(session.scope_stopped),
      detail: { ...c, manifest: mf, runtime: rt },
    });
  }
  for (const f of sessions) {
    const session = obj(f.json), base = dir(f.path);
    const scope = base.replace(/(?:^|\/)evidence\/$/, '').replace(/\/$/, '');
    for (const c of records(session.calls)) join(c, base, scope, session);
  }
  // Historical summaries include scopes whose detailed evidence was not retained.
  for (const f of all.filter(f => /(^|\/)summary\.json$/.test(f.path))) {
    for (const scope of records(obj(f.json).scopes)) {
      const name = str(scope.scope);
      if (!name) continue;
      const scopedName = dir(f.path) + name;
      for (const c of records(scope.calls)) {
        if (!calls.has(`${scopedName}/${c.execution}`)) join(c, `${dir(f.path)}${name}/evidence/`, scopedName, {});
      }
    }
  }
  const cancel = obj(all.find(f => /(^|\/)cancellation\.json$/.test(f.path))?.json);
  if (Object.keys(cancel).length && ![...calls.values()].some(c => c.id.startsWith('cancelled/'))) {
    calls.set('cancelled-owner', { id: 'cancelled-owner', label: 'Cancelled owner · GCC build', base: '', verdict: null,
      rc: num(cancel.owner_returncode) ?? null, evidence: 'incomplete', events: [], actions: [], files: [],
      closed: null, stopped: null, detail: cancel });
  }
  const states = sessions.map(f => obj(f.json));
  const closed = states.length && states.every(s => s.closed === true) ? true : states.some(s => s.closed === false) ? false : null;
  const stopped = states.some(s => s.scope_stopped === true) ? true : states.length && states.every(s => s.scope_stopped === false) ? false : null;
  return { ...ds, calls: [...calls.values()], task: str(states[0]?.task), closed, stopped,
    handoffs: all.filter(f => /(^|\/)handoff-receipt\.json$/.test(f.path)),
    acceptance: all.find(f => f.path === 'audit.json' || f.path === 'acceptance-failure.json'), cancellation: cancel };
}

export function stateLabel(verdict: unknown, rc: unknown, evidence: unknown) {
  const s = String(verdict ?? '').toLowerCase();
  if (s === 'violation') return { text: 'Violation observed', tone: 'danger' };
  if (s === 'blocked' || s === 'denied') return { text: 'Blocked', tone: 'danger' };
  if (s === 'abstain') return { text: 'Observer abstained', tone: 'warn' };
  if (evidence === 'incomplete') return { text: 'Incomplete evidence', tone: 'warn' };
  if (s === 'interrupted' || typeof rc === 'number' && rc < 0) return { text: 'Interrupted', tone: 'warn' };
  if (typeof rc === 'number' && rc !== 0) return { text: `Nonzero exit · ${rc}`, tone: 'warn' };
  if (s === 'review_cleared') return { text: 'Alert cleared by review', tone: 'muted' };
  if (s === 'no_observed_violation' && rc === 0) return { text: 'No violation observed · exit 0', tone: 'good' };
  return { text: 'Unknown outcome', tone: 'muted' };
}

// Bound local imports before reading; skip binary databases, archives and raw traces.
export function importable(path: string, size: number, total: number): string|undefined {
  if (!/\.(?:json|jsonl|md|txt|log|toml)$/i.test(path)) return 'unsupported/binary file';
  if (size > 2 * 1024 * 1024) return 'over 2 MiB file limit';
  if (total + size > 64 * 1024 * 1024) return 'over 64 MiB import limit';
  return undefined;
}
