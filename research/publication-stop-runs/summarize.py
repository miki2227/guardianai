"""Verify retained cancellation ordering and the corrected public publication path."""
import hashlib
import json
from pathlib import Path
import zipfile


def load(path): return json.loads(path.read_text(encoding='utf-8'))
def digest(raw): return hashlib.sha256(raw).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    initial = load(root / 'v1/run/session/evidence/coding-session.json')
    assert initial['calls'][0]['reason'] == 'PermissionError'
    assert not (root / 'v1/run/session/evidence/step-001').exists()
    permissions = load(root / 'initial-permissions.json')
    assert permissions['v1'] == {'mode': '0o644', 'executable': False}
    assert permissions['v2'] == {'mode': '0o755', 'executable': True}
    requests = (root / 'v2/run/requests.jsonl').read_bytes()
    source = root / 'v2/run/source'
    states, results = {}, {}
    for name in ('v2', 'v3', 'normal'):
        run = root / name / 'run'
        assert (run / 'requests.jsonl').read_bytes() == requests
        state = states[name] = load(run / 'session/evidence/coding-session.json')
        assert state['closed'] and state['scope_stopped'] and state['information_flow'] == {'mode': 'untracked'}
        rows = [json.loads(line) for line in (run / 'responses.jsonl').read_text().splitlines()]
        results[name] = [json.loads(row['result']['content'][0]['text']) for row in rows[1:]]
        expected_calls = 2 if name == 'normal' else 1
        assert len(state['calls']) == expected_calls
        for call in state['calls']:
            report = load(run / 'session/evidence' / call['execution'] / 'guarded-agent.json')
            assert report['verdict'] == 'no_observed_violation' and report['runtime']['returncode'] == 0
        if name == 'normal':
            assert all(value['verdict'] == 'no_observed_violation' and value['returncode'] == 0 for value in results[name])
            assert not any(row['result']['isError'] for row in rows[1:])
            assert not (run / 'session/evidence/external-stop.json').exists()
            continue
        observations = load(run / 'observations.json')
        assert [row['event'] for row in observations] == ['stop_requested', 'stop_acknowledged']
        assert observations[0]['monotonic'] <= observations[1]['monotonic']
        assert all(row['destination_exists'] is False for row in observations)
        request = load(run / 'session/evidence/external-stop.json')
        acknowledgement = load(run / 'session/evidence/external-stop-ack.json')
        assert observations[1]['receipt'] == acknowledgement and acknowledgement['scope_stopped']
        assert request['request_id'] == acknowledgement['request_id']
        path = run / 'session/evidence/_content' / observations[0]['input']
        assert digest(path.read_bytes()) == observations[0]['input_sha256']
        assert load(path)['kind'] == 'tool_result_before_delivery'
        assert results[name][1]['reason'] == 'scope_stopped' and rows[2]['result']['isError']
        assert load(run / 'session/evidence/_content/decision-2.json')['verdict'] == 'not_flagged'
        assert load(run / 'session/evidence/step-001/tool-result.json') == results[name][0]
        published = run / 'session/public/results/step-001'
        if name == 'v2':
            assert published.is_dir() and 'stdout' in results[name][0]
            assert results[name][0]['verdict'] == 'no_observed_violation' and not rows[1]['result']['isError']
        else:
            assert not published.exists() and 'stdout' not in results[name][0] and 'stderr' not in results[name][0]
            assert results[name][0]['reason'] == 'scope_stopped_before_publication'
            assert results[name][0]['verdict'] == 'abstain' and rows[1]['result']['isError']
    old = root / 'v2/run/session/public/results/step-001'
    held = root / 'v3/run/session/step-001-output'
    delivered = root / 'normal/run/session/public/results/step-001'
    for name in ('README.md', 'source-hashes.json'):
        assert (old / name).read_bytes() == (held / name).read_bytes() == (delivered / name).read_bytes()
    index = load(delivered / 'source-hashes.json')
    expected = {path.relative_to(source).as_posix() for path in source.rglob('*') if path.suffix in ('.py', '.c')}
    assert set(index) == expected and len(index) == 17
    assert all(digest((source / name).read_bytes()) == value for name, value in index.items())
    assert all((source / name).read_bytes() == (root / 'v3/run/source' / name).read_bytes() for name in index)
    for folder in (old, held, delivered):
        with zipfile.ZipFile(folder / 'source-hashes.zip') as bundle:
            assert set(bundle.namelist()) == {'README.md', 'source-hashes.json'}
            assert all(bundle.read(name) == (folder / name).read_bytes() for name in bundle.namelist())
    build = load(root / 'v3/run/bootstrap/build-report.json')
    archive = root / 'v3/run/bootstrap' / build['archive']
    assert digest(archive.read_bytes()) == build['sha256'] == 'b1712262419b36d62b3e675535c7d299f7752fb677a352b8943a3251c076e601'
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read('manifest.json'))
        assert all(digest(bundle.read(name)) == value for name, value in manifest['files_sha256'].items())
        assert all(bundle.read(name) == (root / 'v3/run/bootstrap/guardianai-linux-x86_64' / name).read_bytes()
                   for name in manifest['files_sha256'])
    result = {'initial_extraction_failure_retained': True, 'new_model_subjects': 0,
              'baseline_acknowledged_before_late_publication': True, 'corrected_stop_withheld_files_and_stdout': True,
              'corrected_stop_mcp_error': True, 'cancelled_scopes_next_command_refused': 2,
              'normal_completed_worker_commands': 2, 'completed_native_worker_commands_across_cases': 4,
              'matched_source_hashes': len(index), 'matched_request_sha256': digest(requests),
              'runtime_package': build,
              'scope': 'One baseline cancellation, one corrected cancellation, one normal workload and an initial extraction failure. Local public-only publication ordering, not all schedules, transport cancellation, malicious-intent detection or a covert convention.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
