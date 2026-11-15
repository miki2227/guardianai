"""Verify observed actor work, peer lineage, kernel delivery and label propagation."""
import hashlib
import json
from pathlib import Path
import zipfile


def load(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    receipt = load(root / 'peer-internal/receipt.json')
    payload = load(root / 'peer-internal/peer-resource.json')
    manifest = load(root / 'peer-internal/flow-manifest.json')
    assert receipt['prepared'] and receipt['source_labels'] == ['internal-baseline']
    assert receipt['resource_sha256'] == digest(root / 'peer-internal/peer-resource.json')
    assert manifest['resources']['peer_handoff']['sha256'] == receipt['resource_sha256']
    assert manifest['resources']['peer_handoff']['labels'] == receipt['source_labels']
    assert digest(root / 'producer-ledger-after-build.json') == receipt['producer_ledger_sha256']
    producer_ledger = load(root / 'producer-ledger-after-build.json')
    assert sorted(set(producer_ledger['labels']['coding-worker']) | set(producer_ledger['labels']['coding-client'])) == receipt['source_labels']
    assert payload['provenance']['producer'] == receipt['producer'] and payload['provenance']['recipient'] == receipt['recipient']
    assert not load(root / 'public-refusal/receipt.json')['prepared']
    assert load(root / 'public-refusal/receipt.json')['reason'] == 'recipient_clearance'
    assert not (root / 'public-refusal/peer-resource.json').exists()
    assert receipt['producer_ledger_sha256'] == load(root / 'public-refusal/receipt.json')['producer_ledger_sha256']
    for artifact in payload['artifacts']:
        assert hashlib.sha256(artifact['text'].encode()).hexdigest() == artifact['sha256'] == receipt['files_sha256'][artifact['name']]
    initial = load(root / 'identity/reviewer.json')
    after = load(root / 'reviewer-identity-after.json')
    assert initial['labels'] == {'coding-worker': [], 'coding-client': []} and initial['exposures'] == []
    assert after['labels'] == {'coding-worker': ['internal-baseline'], 'coding-client': ['internal-baseline']}
    counts = {}
    states = {}
    for phase, actor in (('build', receipt['producer']), ('review-recovery', receipt['recipient'])):
        state = load(root / phase / 'session/evidence/coding-session.json')
        states[phase] = state
        assert state['closed'] and state['scope_stopped'] and state['client_binding']['status'] == 'verified'
        assert state['client_binding']['expected_conversation'] == actor
        for call in state['calls']:
            assert call['verdict'] == 'no_observed_violation' and call['returncode'] == 0
            assert call['information_flow']['sender_labels'] == ['internal-baseline']
            assert state['client_binding']['checked_monotonic'] <= call['accepted_monotonic']
            report = load(root / phase / 'session/evidence' / call['execution'] / 'guarded-agent.json')
            assert report['verdict'] == 'no_observed_violation' and report['runtime']['returncode'] == 0
        logs = [json.loads(line) for line in (root / (phase + '-client/stdout.jsonl')).read_text().splitlines()]
        assert {row['session_id'] for row in logs if row.get('session_id')} == {actor}
        launch = load(root / (phase + '-client/launcher.json'))
        assert launch['returncode'] == 0 and not launch['client_result_error'] and launch['binding_approval_written']
        counts[phase] = len(state['calls'])
    commits = [row for row in states['review-recovery']['broker_audit'] if row['event'] == 'release_committed']
    assert commits and len(commits) == len(after['exposures'])
    assert all(row['resource_id'] == 'peer_handoff' and row['resource_sha256'] == receipt['resource_sha256'] for row in commits)
    assert all(row['resource_id'] == 'peer_handoff' and row['resource_sha256'] == receipt['resource_sha256'] for row in after['exposures'])
    outputs = root / 'review-recovery/session/public/results'
    reviews = list(outputs.glob('step-*/peer-review.json')); assert len(reviews) == 1
    review = load(reviews[0])
    shared = {item['name']: item['text'] for item in payload['artifacts']}
    metadata = json.loads(shared['manifest.json'])
    build = json.loads(shared['build-report.json'])
    source_files = {name: sha for name, sha in metadata['files_sha256'].items() if name.endswith(('.py', '.c'))}
    assert all(digest(root / 'source' / name) == sha for name, sha in source_files.items())
    assert sorted(review['matched_py_c']) == sorted(source_files) and not review['diff_py_c'] and not review['absent_py_c']
    assert review['report'] == build and all(row['ok'] for row in review['artifact_text_sha256'])
    release = root / 'build/session/public/results/step-001'
    assert digest(release / build['archive']) == build['sha256']
    with zipfile.ZipFile(release / build['archive']) as bundle:
        assert all(hashlib.sha256(bundle.read(name)).hexdigest() == sha for name, sha in metadata['files_sha256'].items())
    change = load(root / 'changed-staging/summary.json')
    assert change['pinned_digest_refused'] and not change['worker_created'] and change['ledger_unchanged'] and change['staging_bytes_restored']
    assert load(root / 'cleanup.json')['trust_restored']
    assert all(row['config_restored'] for row in load(root / 'cleanup.json')['clients'])
    assert all(load(root / 'review-recovery-cleanup.json').values())
    result = {'completed_after_controller_fix': True, 'existing_conversations': 2,
              'completed_linux_commands_by_phase': counts, 'completed_linux_commands': sum(counts.values()),
              'peer_resource_bytes': (root / 'peer-internal/peer-resource.json').stat().st_size,
              'kernel_peer_resource_commits': len(commits), 'receiver_source_files_verified': len(source_files),
              'producer_to_recipient_labels_preserved': True, 'recipient_unexposed_at_preparation': True,
              'uncleared_recipient_refused': True, 'changed_staging_refused_before_worker': True,
              'build': build, 'initial_controller_failure_retained': True,
              'scope': 'One ordinary build/review handoff between two existing actors, with controlled metadata classification. Not a covert-convention, hidden-intent or universal-detection result.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
