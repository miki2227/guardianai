"""Audit inherited labels, explicit closure, exclusive ownership and revocation."""
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
    records = {}
    expected_labels = {'coding-worker': ['internal-baseline'], 'coding-client': ['internal-baseline']}
    for name in ('index', 'build', 'verify-and-stop', 'revoked-resume'):
        folder = root / name
        assert load(folder / 'client.json')['mcp_returncode'] == 0
        requests = [json.loads(line) for line in (folder / 'requests.jsonl').read_text().splitlines()]
        responses = [json.loads(line) for line in (folder / 'responses.jsonl').read_text().splitlines()]
        assert [r['id'] for r in requests] == [r['id'] for r in responses]
        state = load(folder / 'session/evidence/coding-session.json')
        after = load(folder / 'identity-after.json')
        assert state['closed'] and state['scope_stopped']
        assert after['labels'] == expected_labels
        records[name] = {'state': state, 'after': after,
                         'replies': [json.loads(r['result']['content'][0]['text']) for r in responses[1:]]}
    index, build, verify, revoked = [records[name] for name in ('index', 'build', 'verify-and-stop', 'revoked-resume')]
    assert index['state']['identity_at_start']['labels'] == {'coding-worker': [], 'coding-client': []}
    assert len(index['after']['exposures']) == 1
    for record in (index, build):
        assert not record['after']['stopped'] and record['after']['active_session'] is None
    assert build['state']['identity_at_start']['labels'] == expected_labels
    assert not build['state']['identity_at_start']['stopped']
    assert build['state']['identity_at_start']['active_session'] is None
    assert build['after']['exposures'] == index['after']['exposures']
    assert not any(row['event'] == 'release_committed' for row in build['state']['broker_audit'])
    commits = [row for row in index['state']['broker_audit'] if row['event'] == 'release_committed']
    assert len(commits) == 1
    exposure = index['after']['exposures'][0]
    assert commits[0]['resource_sha256'] == exposure['resource_sha256']
    assert commits[0]['resource_id'] == exposure['resource_id'] == 'previous_release'
    assert exposure['subject'] == 'coding-worker'
    inherited_inputs = list((root / 'build/session/evidence/_observer').glob('input-*.json'))
    assert inherited_inputs
    for path in inherited_inputs:
        assert load(path)['information_flow']['possible_exposure_labels'] == ['internal-baseline']
        receipt = load(path.with_name(path.name.replace('input-', 'decision-')))
        assert receipt['input_sha256'] == receipt['answer']['session_observer_input_sha256'] == digest(path)
        assert receipt['initial_response']['model'] == 'jev-1.14.0'
    for name in ('index', 'build', 'verify-and-stop'):
        case = records[name]
        assert len(case['state']['calls']) == 1
        worker = load(root / name / 'session/evidence/step-001/guarded-agent.json')
        assert worker['verdict'] == 'no_observed_violation' and worker['runtime']['returncode'] == 0
        result = case['replies'][0]
        assert result['verdict'] == 'no_observed_violation' and result['returncode'] == 0
        assert result['information_flow']['sender_labels'] == ['internal-baseline']
        assert result['information_flow']['stage'] == 'committed'
    assert [len(records[name]['after']['transfers']) for name in ('index', 'build', 'verify-and-stop', 'revoked-resume')] == [1, 2, 3, 3]
    assert verify['replies'][1] == {'verdict': 'abstain', 'reason': 'scope_stopped'}
    evidence = root / 'verify-and-stop/session/evidence'
    request, ack = load(evidence / 'external-stop.json'), load(evidence / 'external-stop-ack.json')
    assert request['request_id'] == ack['request_id'] and ack['scope_stopped']
    assert verify['after']['stopped'] and revoked['state']['identity_at_start']['stopped']
    assert verify['after']['active_session'].endswith('/verify-and-stop/session')
    assert revoked['after'] == verify['after']
    assert not revoked['state']['calls']
    assert revoked['replies'] == [{'verdict': 'abstain', 'reason': 'scope_stopped'}]
    assert not (root / 'revoked-resume/session/evidence/step-001').exists()
    assert not (root / 'verify-and-stop/session/evidence/step-002').exists()
    contender = load(root / 'contender/client.json')
    assert contender['owner_was_live'] and contender['returncode'] != 0 and not contender['session_created']
    assert 'BlockingIOError' in (root / 'contender/stderr.txt').read_text()
    assert not (root / 'contender/session').exists()
    assert verify['replies'][0]['stdout']['text'].split()[0] == digest(root / 'source/guardian_mcp.py')
    release = root / 'build/session/public/results/step-001'
    build_report = load(release / 'build-report.json')
    assert json.loads(build['replies'][0]['stdout']['text']) == build_report
    assert digest(release / build_report['archive']) == build_report['sha256']
    with zipfile.ZipFile(release / build_report['archive']) as bundle:
        manifest = json.loads(bundle.read('manifest.json'))
        for name, expected in manifest['files_sha256'].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
            if (root / 'source' / name).is_file():
                assert digest(root / 'source' / name) == expected
    result = {'completed_linux_commands': 3, 'mcp_sessions': 4, 'clean_resumable_closures': 2,
              'resource_commits': 1, 'inherited_label_in_build_observer_inputs': len(inherited_inputs),
              'build_added_no_resource_exposure': True, 'contending_owner_refused': True,
              'operator_stop_acknowledged': True, 'revoked_identity_refused_after_restart': True,
              'build': build_report,
              'scope': 'Host-bound identity continuity in actual MCP processes. Controlled classification of real release metadata; no model-agent behavior, abrupt-death recovery measurement, power-loss durability or universal detection result.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
