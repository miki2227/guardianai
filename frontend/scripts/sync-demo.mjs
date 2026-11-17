import { readdir, readFile, mkdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const source = fileURLToPath(new URL('../../research/checkstyle-paired/v5/', import.meta.url));
const target = fileURLToPath(new URL('../src/demo/paired/', import.meta.url));
const receipts = {};
async function copy(relative) {
  const bytes = await readFile(path.join(source, relative));
  await mkdir(path.dirname(path.join(target, relative)), { recursive: true });
  await writeFile(path.join(target, relative), bytes);
  receipts[relative.replaceAll('\\', '/')] = createHash('sha256').update(bytes).digest('hex');
}
for (const file of ['result.json', 'audit.json', 'safety-result.json']) await copy(file);
for (const phase of ['investigation', 'review', 'reconciliation']) {
  const base = `${phase}/evidence`;
  await copy(`${base}/coding-session.json`);
  for (const step of await readdir(path.join(source, base))) {
    if (!/^step-\d+$/.test(step)) continue;
    for (const name of await readdir(path.join(source, base, step))) {
      if (/^(runtime\.json|manifest\.json|observer-input-\d+\.json|stdout\.txt|stderr\.txt)$/.test(name)) await copy(`${base}/${step}/${name}`);
    }
  }
  for (const name of await readdir(path.join(source, base, '_observer'))) {
    if (/^input-\d+\.json$/.test(name)) await copy(`${base}/_observer/${name}`);
  }
  for (const name of await readdir(path.join(source, base, '_content'))) {
    if (/^decision-\d+\.json$/.test(name)) await copy(`${base}/_content/${name}`);
  }
  for (const name of await readdir(path.join(source, `${phase}-client`, 'agent-content'))) {
    if (/^decision-\d+\.json$/.test(name)) await copy(`${phase}-client/agent-content/${name}`);
  }
}
for (const role of ['investigator', 'reviewer']) {
  for (const name of await readdir(path.join(source, 'handoffs', role))) await copy(`handoffs/${role}/${name}`);
}
await writeFile(path.join(target, 'source-sha256.json'), JSON.stringify({ source: 'research/checkstyle-paired/v5', files: receipts }, null, 2) + '\n');
console.log(`Copied ${Object.keys(receipts).length} exact evidence files.`);
