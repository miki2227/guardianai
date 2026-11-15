"""Audit admission ordering, inherited exposure and rejected real MCP requests."""
import hashlib
import json
from pathlib import Path
import zipfile


def load(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    result = load(root / 'result.json')
    state = load(root / 'session/evidence/coding-session.json')
    before, after = load(root / 'identity-before.json'), load(root / 'identity-after.json')
    binding = state['client_binding']
    assert result['returncode'] == 0 and state['closed'] and state['scope_stopped']
    assert binding['status'] == 'verified' and binding['expected_conversation'] == result['conversation']
    assert after['provider_conversation'] == result['conversation']
    assert before['labels'] == after['labels'] and before['exposures'] == after['exposures']
    assert not after['stopped'] and after['active_session'] is None
    assert load(root / 'cleanup.json')['config_restored']
    approval = load(root / 'client/client-binding.json')
    assert approval == load(root / 'session/evidence/client-binding.json')
    assert approval['request_id'] == binding['request_id'] and approval['session_id'] == result['conversation']
    launch = load(root / 'client/launcher.json')
    assert launch['binding_required'] and launch['binding_approval_written'] and not launch['client_result_error']
    rows = [json.loads(line) for line in (root / 'client/stdout.jsonl').read_text().splitlines()]
    assert {r['session_id'] for r in rows if r.get('session_id')} == {result['conversation']}
    assert next(r for r in rows if r.get('type') == 'system' and r.get('subtype') == 'init')['session_id'] == result['conversation']
    for call in state['calls']:
        assert call['verdict'] == 'no_observed_violation' and call['returncode'] == 0
        assert binding['checked_monotonic'] <= call['accepted_monotonic']
        assert call['client_binding']['status'] == 'verified'
        assert call['information_flow']['sender_labels'] == ['internal-baseline']
        worker = load(root / 'session/evidence' / call['execution'] / 'guarded-agent.json')
        assert worker['runtime']['returncode'] == 0 and worker['verdict'] == 'no_observed_violation'
    controls = load(root / 'admission-summary.json')
    assert controls['wrong-conversation']['startup_refused'] and controls['wrong-conversation']['ledger_unchanged']
    for name in ('wrong-conversation', 'missing-approval', 'stale-approval'):
        assert not list((root / name / 'session/evidence').glob('step-*'))
    for name in ('missing-approval', 'stale-approval'):
        assert controls[name]['commands_executed'] == 0
        assert controls[name]['result']['reason'] == 'client_binding_unverified'
        assert load(root / name / 'session/evidence/coding-session.json')['calls'] == []
    output = root / 'session/public/results/step-001'
    build = load(output / 'build-report.json')
    assert digest(output / build['archive']) == build['sha256']
    with zipfile.ZipFile(output / build['archive']) as bundle:
        manifest = json.loads(bundle.read('manifest.json'))
        for name, expected in manifest['files_sha256'].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
            if (root / 'source' / name).is_file(): assert digest(root / 'source' / name) == expected
    summary = {'completed_linux_commands': len(state['calls']), 'pre_execution_binding_verified': True,
               'binding_preceded_all_command_admissions': True, 'existing_exposure_labels_retained': True,
               'new_protected_exposures': len(after['exposures']) - len(before['exposures']),
               'rejected_admission_cases': 3, 'rejected_cases_executed_commands': 0, 'build': build,
               'scope': 'Trusted CLI startup metadata and private host approval, not cryptographic provider authentication. Controlled rejection cases use isolated ledger copies, not the real conversation ledger.'}
    (root / 'audit.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
