"""Verify retained content receipts and report this actual workflow."""
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parent
    content = {}
    for label, folder in [('host', root / 'client-run/agent-content'),
                          ('tools', root / 'session/evidence/_content')]:
        receipts = sorted(folder.glob('decision-*.json'), key=lambda p: int(p.stem.split('-')[1]))
        previous = None
        chunks = 0
        maximum = 0
        kinds = {}
        for path in receipts:
            row = json.loads(path.read_text())
            raw = (folder / f'content-{row["sequence"]}.json').read_bytes()
            assert hashlib.sha256(raw).hexdigest() == row['content_sha256']
            assert row['previous_content_sha256'] == previous
            previous = row['content_sha256']
            kinds[row['kind']] = kinds.get(row['kind'], 0) + 1
            assert row['verdict'] == 'not_flagged'
            for chunk in row['chunks']:
                assert hashlib.sha256((folder / chunk['input']).read_bytes()).hexdigest() == chunk['input_sha256']
                assert chunk['response']['model'] == 'jev-1.14.0'
                maximum = max(maximum, *chunk['scores'].values())
                chunks += 1
        content[label] = {'records': len(receipts), 'jev_calls': chunks, 'kinds': kinds,
                          'maximum_question_probability': maximum, 'input_and_chain_hashes_verified': True}
    session = json.loads((root / 'session/evidence/coding-session.json').read_text())
    runtime_calls = 0
    for path in (root / 'session/evidence/_observer').glob('decision-*.json'):
        row = json.loads(path.read_text())
        number = path.stem.split('-')[1]
        assert hashlib.sha256((path.parent / f'input-{number}.json').read_bytes()).hexdigest() == row['input_sha256']
        runtime_calls += 1
    built = root / 'session/public/results/step-001'
    build = json.loads((built / 'build-report.json').read_text())
    archive = built / build['archive']
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == build['sha256']
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read('manifest.json'))
        for name, digest in manifest['files_sha256'].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == digest
            if (root / 'source' / name).is_file():
                assert hashlib.sha256((root / 'source' / name).read_bytes()).hexdigest() == digest
    turns = []
    for line in (root / 'client-run/stdout.jsonl').read_text().splitlines():
        item = json.loads(line)
        if item.get('type') == 'assistant':
            usage = item['message'].get('usage', {})
            turns.append({'reported_model': item['message'].get('model'), 'usage': usage,
                          'reported_full_input': sum(usage.get(k, 0) for k in
                              ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'))})
    summary = {'content_observation': content, 'kernel_shared_observer_receipts': runtime_calls,
               'calls': session['calls'], 'closed': session['closed'], 'scope_stopped': session['scope_stopped'],
               'build': build, 'assistant_turns': turns,
               'largest_reported_input': max(t['reported_full_input'] for t in turns),
               'limits': 'One continued conversation, ordinary work, no emergence or content-stop event. Host checks are post-emission, MCP checks gate tool execution/result delivery. Missing closure is retained. Token counts are reported inputs, not proof of saturation or hidden state. Hash checks establish retained artifact consistency, not complete telemetry.'}
    (root / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
