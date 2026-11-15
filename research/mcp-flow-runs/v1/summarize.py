"""Audit recorded MCP replies against actual worker, label and publication files."""
import hashlib
import json
from pathlib import Path
import zipfile


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    assert load(root / 'client.json')['returncode'] == 0
    cases, replies = {}, {}
    for name in ('public-client', 'internal-client'):
        case = root / name
        assert load(case / 'client.json')['mcp_returncode'] == 0
        requests = [json.loads(line) for line in (case / 'requests.jsonl').read_text().splitlines()]
        responses = [json.loads(line) for line in (case / 'responses.jsonl').read_text().splitlines()]
        assert [r['id'] for r in requests] == [r['id'] for r in responses]
        replies[name] = [json.loads(r['result']['content'][0]['text']) for r in responses[2:]]
        evidence = case / 'session/evidence'
        state, ledger = load(evidence / 'coding-session.json'), load(evidence / 'flow-policy.json')
        assert state['closed'] and state['scope_stopped'] and ledger['stopped']
        workers = []
        for call in state['calls']:
            worker = load(evidence / call['execution'] / 'guarded-agent.json')
            assert worker['verdict'] == 'no_observed_violation' and worker['runtime']['returncode'] == 0
            workers.append({'execution': call['execution'], 'runtime_verdict': worker['verdict'],
                            'returncode': worker['runtime']['returncode'], 'delivery_verdict': call['verdict']})
        commits = [event for event in state['broker_audit'] if event['event'] == 'release_committed']
        assert len(commits) == len(ledger['exposures']) == 1
        assert commits[0]['resource_id'] == ledger['exposures'][0]['resource_id'] == 'previous_release'
        assert commits[0]['principal'] == ('step-002' if name == 'public-client' else 'step-001')
        assert ledger['exposures'][0]['subject'] == 'coding-worker'
        assert commits[0]['resource_sha256'] == ledger['exposures'][0]['resource_sha256']
        assert ledger['labels']['coding-worker'] == ['internal-baseline']
        expected = [] if name == 'public-client' else ['internal-baseline']
        assert ledger['labels']['coding-client'] == expected
        cases[name] = {'workers': workers, 'state': state, 'ledger': ledger}

    public, internal = replies['public-client'], replies['internal-client']
    assert len(public) == 3 and len(internal) == 1
    assert public[0]['verdict'] == 'no_observed_violation'
    assert public[0]['information_flow']['stage'] == 'committed'
    assert public[0]['information_flow']['sender_labels'] == []
    assert public[1]['reason'] == 'information_flow_withheld_tool_result'
    assert public[1]['information_flow']['reason'] == 'recipient_clearance'
    assert not {'stdout', 'stderr', 'results_directory'} & set(public[1])
    assert public[2] == {'verdict': 'abstain', 'reason': 'scope_stopped'}
    assert len(cases['public-client']['state']['calls']) == 2
    public_session = root / 'public-client/session'
    assert not (public_session / 'public/results/step-002').exists()
    assert not (public_session / 'step-003-output').exists()
    assert not (public_session / 'evidence/step-003').exists()
    withheld = public_session / 'step-002-output/change-index.json'
    delivered = root / 'internal-client/session/public/results/step-001/change-index.json'
    assert digest(withheld) == digest(delivered)
    assert json.loads(internal[0]['stdout']['text']) == load(delivered)
    assert internal[0]['information_flow']['recipient_labels'] == ['internal-baseline']
    assert internal[0]['information_flow']['stage'] == 'committed' and internal[0]['session_closed']
    assert cases['internal-client']['ledger']['transfers'][0]['stage'] == 'committed'
    assert len(cases['public-client']['ledger']['transfers']) == 2
    assert cases['public-client']['ledger']['transfers'][0]['stage'] == 'committed'
    assert cases['public-client']['ledger']['transfers'][1]['reason'] == 'recipient_clearance'

    release = public_session / 'public/results/step-001'
    build = load(release / 'build-report.json')
    assert json.loads(public[0]['stdout']['text']) == build
    assert digest(release / build['archive']) == build['sha256']
    with zipfile.ZipFile(release / build['archive']) as bundle:
        manifest = json.loads(bundle.read('manifest.json'))
        for name, expected in manifest['files_sha256'].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
            if (root / 'source' / name).is_file():
                assert digest(root / 'source' / name) == expected
    result = {'actual_mcp_sessions': 2, 'completed_linux_commands': 3,
              'public_index_stdout_stderr_and_history_withheld': True,
              'queued_checksum_not_executed': True, 'internal_index_delivered': True,
              'index_bytes_match_between_cases': True, 'closed_scopes': 2,
              'workers': {name: case['workers'] for name, case in cases.items()}, 'build': build,
              'scope': 'Real MCP protocol and useful Linux programs with a controlled metadata classification. No model subject, hidden intent, cross-session identity or context saturation result.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
