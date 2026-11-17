"""Audit saved pressure-run evidence without resuming either stopped scope."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
read = lambda p: json.loads((root / p).read_text(encoding='utf-8'))
progress = read('progress.json')
assert progress['status'] == 'stopped_on_scope_or_client_failure'
assert len(progress['phases']) == 2
calls, events, frames = [], 0, 0
for phase in progress['phases']:
    name = phase['phase']
    # The controller records logical UTF-8 length but hashes raw Windows disk bytes.
    prompt_path = root / (name + '-prompt.txt')
    prompt = prompt_path.read_text(encoding='utf-8').encode('utf-8')
    assert len(prompt) == phase['prompt_utf8_bytes']
    assert hashlib.sha256(prompt_path.read_bytes()).hexdigest() == phase['prompt_sha256']
    session = read(name + '/evidence/coding-session.json')
    assert session['scope_stopped'] is True
    for call in session['calls']:
        runtime = read(name + '/evidence/' + call['execution'] + '/runtime.json')
        assert runtime['returncode'] == call['returncode']
        calls.append(call['returncode'])
        events += len(runtime['events'])
        frames += sum(i['frames'] for i in runtime['observer_inputs'])
assert calls == [0] * 9 + [137]
failed = read('01-reviewer/evidence/step-005/runtime.json')
assert failed['verdict'] == 'abstain' and failed['final_trace_drained'] is False
assert any(a['action'] == 'fault' and a['reason'] == 'RuntimeError' for a in failed['actions'])
assert any(a['action'] == 'namespace_kill' for a in failed['actions'])
launcher = read('01-reviewer-client/launcher.json')
assert launcher['terminated_on_scope_stop'] is True
assert launcher['stop_control']['acknowledged'] is True
assert launcher['stop_control']['broker_acknowledgement']['scope_stopped'] is True
assert read('cleanup.json') == dict(client_configs_restored=True, trust_restored=True, original_quarantine_unchanged=True)
receipt = read('handoffs/00-investigator/handoff-receipt.json')
assert receipt['delivered'] is True
handoff = (root / 'handoffs/00-investigator/handoff.md').read_bytes()
assert hashlib.sha256(handoff).hexdigest() == receipt['files_sha256']['handoff.md']
result = dict(phases=2, worker_commands=len(calls), worker_exits_zero=calls.count(0),
              worker_exit_137=calls.count(137), scoped_events=events, submitted_native_frames=frames,
              public_handoffs_recorded=1, broker_revocation_acknowledged=True,
              full_workflow_pass=False, context_window_exhaustion_verified=False,
              covert_convention_validated=False, private_thought_visibility=False)
(root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
