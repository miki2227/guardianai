import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { normalize, makeDataset, stateLabel, importable } from '../.test-build/evidence.js';

const root = fileURLToPath(new URL('../src/demo/paired/', import.meta.url));
function load(folder, prefix = '', files = new Map()) {
  for (const entry of readdirSync(folder, { withFileTypes: true })) {
    const name = prefix + entry.name, full = path.join(folder, entry.name);
    if (entry.isDirectory()) load(full, name + '/', files);
    else { const text = readFileSync(full, 'utf8'); files.set(name, { path: name, text, json: name.endsWith('.json') ? JSON.parse(text) : undefined }); }
  }
  return files;
}
const files = load(root);
const dataset = () => normalize({ title: 'fixture', description: '', source: '', files, calls: [] });

test('real paired run joins nine commands to their exact runtime and manifests', () => {
  const ds = dataset();
  assert.equal(ds.calls.length, 9);
  assert.equal(new Set(ds.calls.map(c => c.id)).size, 9);
  assert.equal(ds.calls.reduce((n, c) => n + c.events.length, 0), 133);
  for (const c of ds.calls) {
    assert.deepEqual(c.events, files.get(c.base + 'runtime.json').json.events);
    assert.deepEqual(c.actions, files.get(c.base + 'runtime.json').json.actions);
    assert.ok(c.files.every(f => f.startsWith(c.base)));
    assert.equal(c.rc, 0);
    assert.equal(c.closed, true);
  }
});
test('both handoffs and the independent audit remain separate from worker decisions', () => {
  const ds = dataset();
  assert.equal(ds.handoffs.length, 2);
  assert.ok(ds.handoffs.every(f => f.json.delivered === true));
  assert.equal(ds.acceptance.json.verified_public_text_handoffs, 2);
});
test('bundled real artifacts match source and declared SHA-256 bytes', () => {
  const manifest = files.get('source-sha256.json').json;
  for (const [name, hash] of Object.entries(manifest.files)) {
    const bytes = readFileSync(path.join(root, name));
    assert.equal(createHash('sha256').update(bytes).digest('hex'), hash, name);
    assert.deepEqual(bytes, readFileSync(new URL('../../research/checkstyle-paired/v5/' + name, import.meta.url)));
  }
});
test('missing runtime never borrows another worker decisions', () => {
  const reduced = new Map(files);
  reduced.delete('review/evidence/step-001/runtime.json');
  const ds = normalize({ title: '', description: '', source: '', files: reduced, calls: [] });
  const c = ds.calls.find(c => c.id === 'review/step-001');
  assert.deepEqual(c.events, []); assert.deepEqual(c.actions, []);
});
test('nonzero, interrupted, incomplete and absent outcomes cannot appear green', () => {
  for (const [rc, evidence] of [[1, 'recorded'], [-9, 'recorded'], [0, 'incomplete'], [null, null]]) {
    assert.notEqual(stateLabel('no_observed_violation', rc, evidence).tone, 'good');
  }
  assert.notEqual(stateLabel('review_cleared', 0, 'recorded').tone, 'good');
});
test('malformed imported shapes remain unknown instead of crashing or inventing calls', () => {
  const ds = makeDataset('', '', { 'coding-session.json': { calls: {}, closed: 'yes' }, 'summary.json': { scopes: 'bad' } }, '');
  assert.equal(ds.calls.length, 0); assert.equal(ds.closed, null);
});
test('local import excludes binaries and bounds individual and aggregate allocation', () => {
  assert.ok(importable('history.sqlite3', 200, 0));
  assert.ok(importable('trace.1', 200, 0));
  assert.ok(importable('runtime.json', 3 * 1024 * 1024, 0));
  assert.ok(importable('runtime.json', 1024, 64 * 1024 * 1024));
  assert.equal(importable('runtime.json', 1024, 0), undefined);
});
