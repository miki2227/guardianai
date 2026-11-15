"""Audit actual paired-workflow receipts, delivery hashes and conversation IDs."""
import hashlib
import json
from pathlib import Path
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_content(folder):
    records = sorted(folder.glob('decision-*.json'), key=lambda p: int(p.stem.split('-')[1]))
    previous, chunks, largest = None, 0, 0
    verdicts = {}
    for path in records:
        row = json.loads(path.read_text())
        assert digest(folder / f'content-{row["sequence"]}.json') == row['content_sha256']
        assert row['previous_content_sha256'] == previous
        previous = row['content_sha256']
        verdicts[row['verdict']] = verdicts.get(row['verdict'], 0) + 1
        for chunk in row['chunks']:
            assert digest(folder / chunk['input']) == chunk['input_sha256']
            assert chunk['response']['model'] == 'jev-1.14.0'
            largest = max(largest, (folder / chunk['input']).stat().st_size)
            chunks += 1
    return {'records': len(records), 'jev_calls': chunks, 'verdicts': verdicts,
            'largest_saved_state_bytes': largest, 'hashes_verified': True}


def main():
    root = Path(__file__).resolve().parent
    workflow = json.loads((root / 'workflow.json').read_text())
    rows = []
    for phase in workflow['phases']:
        name = phase['phase']
        client = root / (phase.get('scope', name) + '-client')
        session = root / phase.get('evidence_scope', name) / 'session'
        state = json.loads((session / 'evidence/coding-session.json').read_text())
        model_ids, reported_inputs, identities, emitted = set(), [], set(), 0
        for line in (client / 'stdout.jsonl').read_text().splitlines():
            item = json.loads(line)
            if item.get('session_id'):
                identities.add(item['session_id'])
            if item.get('type') == 'assistant':
                emitted += 1
                model_ids.add(item['message'].get('model'))
                usage = item['message'].get('usage', {})
                reported_inputs.append(sum(usage.get(k, 0) for k in
                    ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')))
        assert identities == {phase['conversation']}
        native = 0
        for path in (session / 'evidence/_observer').glob('decision-*.json'):
            receipt = json.loads(path.read_text())
            assert digest(path.parent / ('input-' + path.stem.split('-')[1] + '.json')) == receipt['input_sha256']
            native += 1
        host = audit_content(client / 'agent-content')
        assert host['records'] == emitted + 1
        rows.append({**phase, 'assistant_messages': emitted, 'reported_model_ids': sorted(model_ids),
                     'largest_reported_input': max(reported_inputs, default=None),
                     'host_content': host, 'tool_content': audit_content(session / 'evidence/_content'),
                     'shared_runtime_receipts': native, 'calls': state['calls'],
                     'closed': state['closed'], 'scope_stopped': state['scope_stopped']})
    delivered = []
    for index, receipt in enumerate(workflow['handoffs']):
        phase = receipt.get('recipient_phase', 'review')
        if not receipt['delivered']:
            delivered.append(receipt)
            continue
        journal = receipt.get('observer_journal', 'handoff-observer')
        source = json.loads((root / journal / f'content-{receipt["observer_sequence"]}.json').read_text())['content']
        assert source['sender'] == receipt['sender'] and source['recipient'] == receipt['recipient']
        approved = {a['name']: a for a in source['artifacts']}
        for name, expected in receipt['files_sha256'].items():
            initial_failed = journal == 'handoff-observer' and (root / 'initial-attempt.json').exists()
            actual = (root / 'initial-recipient-input' / name if initial_failed else
                      root / receipt.get('recipient_scope', phase) / 'session/public/source/incoming' / name)
            assert digest(actual) == expected == approved[name]['sha256']
            assert actual.read_bytes() == approved[name]['text'].encode()
        delivered.append({**receipt, 'recipient_phase': phase, 'exact_bytes_verified': True,
                          'recipient_mcp_input_verified': not initial_failed})
    builds = list((root / 'build/session/public/results').glob('step-*/build-report.json'))
    build = json.loads(builds[0].read_text())
    archive = builds[0].parent / build['archive']
    assert digest(archive) == build['sha256']
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read('manifest.json'))
        for name, expected in manifest['files_sha256'].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
    outputs = {}
    owners = {p['phase']: p.get('evidence_scope', p['phase']) for p in workflow['phases']}
    for phase, names in {'build': ['handoff.md'], 'review': ['review.md', 'message.md'],
                         'resolve': ['response.md', 'operator-guide.md'],
                         'final': ['final-review.md', 'release-decision.json']}.items():
        for name in names:
            found = list((root / owners.get(phase, phase) / 'session/public/results').glob('step-*/' + name))
            if len(found) == 1:
                outputs[phase + '/' + name] = {'path': str(found[0].relative_to(root)), 'sha256': digest(found[0]),
                                              'bytes': found[0].stat().st_size}
    journals = {folder.name: audit_content(folder) for folder in root.glob('handoff-observer*') if folder.is_dir()}
    initial = json.loads((root / 'initial-attempt.json').read_text()) if (root / 'initial-attempt.json').exists() else None
    failed_attempts = []
    for folder_name in ['review-client', *[p.get('scope', p['phase']) + '-client' for p in workflow.get('attempts', [])]]:
        folder = root / folder_name
        results = [json.loads(line) for line in (folder / 'stdout.jsonl').read_text().splitlines()]
        terminal = next((item for item in reversed(results) if item.get('type') == 'result'), None)
        failed_attempts.append({'client': folder_name, 'terminal_result': terminal,
                                'host_content': audit_content(folder / 'agent-content')})
    summary = {'phases': rows, 'handoffs': delivered, 'handoff_observers': journals, 'initial_attempt': initial,
               'failed_attempts': failed_attempts,
               'build': build, 'required_outputs': outputs,
               'completed_all_phases': workflow['completed_all_phases'] and len(outputs) == 7 and all(v['bytes'] > 0 for v in outputs.values()),
               'limits': 'Two conversations, alternating invocations, normal work only. Observations are not calibrated accuracy or proof of absence of covert communication. No context saturation or hidden thought access. Separate local scopes, no concurrent shared broker. Closure snapshots retained as recorded.'}
    (root / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'completed_all_phases': summary['completed_all_phases'], 'phases': len(rows),
                      'handoffs': len(delivered), 'required_outputs': len(outputs), 'build': build,
                      'host_content_calls': sum(r['host_content']['jev_calls'] for r in rows),
                      'tool_content_calls': sum(r['tool_content']['jev_calls'] for r in rows),
                      'runtime_receipts': sum(r['shared_runtime_receipts'] for r in rows)}, indent=2))


if __name__ == '__main__':
    main()
