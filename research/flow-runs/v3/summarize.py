"""Audit actual kernel exposures, inherited labels and handoff publications."""
import hashlib
import json
from pathlib import Path
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    summary = json.loads((root / 'summary.json').read_text())
    ledger = json.loads((root / 'flow-policy.json').read_text())
    before = json.loads((root / 'before-denial.json').read_text())
    workers = json.loads((root / 'worker-summary.json').read_text())
    assert all(row['verdict'] == 'no_observed_violation' and row['returncode'] == 0 for row in workers.values())
    assert [row['delivered'] for row in summary['transfers']] == [True, True, False, False]
    assert ledger['labels']['builder'] == []
    assert ledger['labels']['indexer'] == ledger['labels']['internal-reviewer'] == ['internal-baseline']
    assert ledger['labels']['public-reviewer'] == []
    assert before['labels'] == ledger['labels'] and not before['stopped'] and ledger['stopped']
    assert summary['broker_stopped'] and not summary['blocked_directory_exists'] and not summary['after_stop_directory_exists']
    commits = [row for row in summary['broker_audit'] if row['event'] == 'release_committed']
    assert len(commits) == len(ledger['exposures']) == 1
    assert commits[0]['principal'] == ledger['exposures'][0]['subject'] == 'indexer'
    assert commits[0]['resource_id'] == ledger['exposures'][0]['resource_id'] == 'previous_release'
    assert commits[0]['resource_sha256'] == ledger['exposures'][0]['resource_sha256'] == summary['private_manifest_sha256']
    assert any(row['event'] == 'task_changed' for row in summary['broker_audit'])
    for index, (source, destination) in enumerate([('builder-output/build-report.json', 'public-handoff'),
                                                  ('indexer-output/change-index.json', 'internal-handoff')]):
        path = root / source
        json.loads(path.read_text())
        received = root / destination / path.name
        assert digest(path) == digest(received) == summary['transfers'][index]['files_sha256'][path.name]
        assert ledger['transfers'][index]['stage'] == 'committed'
        row = ledger['transfers'][index]
        assert set(row['sender_labels']) <= set(row['recipient_clearance'])
    assert summary['transfers'][2]['information_flow']['reason'] == 'recipient_clearance'
    assert summary['transfers'][3]['information_flow']['reason'] == 'scope_stopped'
    assert summary['transfers'][2]['observer_sequence'] is None and summary['transfers'][3]['observer_sequence'] is None
    decisions = list((root / 'handoff-observer').glob('decision-*.json'))
    assert len(decisions) == 2
    for path in decisions:
        receipt = json.loads(path.read_text())
        assert receipt['verdict'] in ('not_flagged', 'review_cleared')
        source = path.parent / f'content-{receipt["sequence"]}.json'
        assert digest(source) == receipt['content_sha256']
        for chunk in receipt['chunks']:
            assert digest(path.parent / chunk['input']) == chunk['input_sha256']
    build = json.loads((root / 'builder-output/build-report.json').read_text())
    assert digest(root / 'builder-output' / build['archive']) == build['sha256']
    with zipfile.ZipFile(root / 'builder-output' / build['archive']) as bundle:
        manifest = json.loads(bundle.read('manifest.json'))
        for name, expected in manifest['files_sha256'].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
            if (root / 'source' / name).is_file():
                assert digest(root / 'source' / name) == expected
    result = {'workers': workers, 'kernel_resource_commits': len(commits),
              'exposure_subject': 'indexer', 'grant_without_exposure_subject': 'builder',
              'label_propagation_verified': True, 'task_epoch_did_not_clear_labels': True,
              'handoff_publications': [True, True, False, False], 'permitted_file_hashes_verified': True,
              'broker_stopped_after_denial': True, 'build': build,
              'scope': 'Controlled confidentiality classification on real release metadata, with unmodified Linux build/index programs. Handoff publication means bytes placed in the recipient directory, not confirmed model consumption. No model-agent misalignment, covert-convention or general noninterference result.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
