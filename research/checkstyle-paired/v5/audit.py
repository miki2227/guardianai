"""Verify useful two-subject completion and mediated public artifact reads."""
import hashlib
import json
from pathlib import Path


def load(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def check_review(folder, review):
    parts = review.get('parts', [review])
    for part in parts:
        assert sha(folder / part['input']) == part['input_sha256']
        assert part['response']['model'] == 'jev-1.14.0'
    if review.get('mode') == 'overlapping_parts':
        assert review['all_parts_reviewed'] and review['probability'] == max(p['probability'] for p in parts)


def main():
    root = Path(__file__).resolve().parent
    result = load(root / 'result.json')
    assert len(result['phases']) == 3 and len(result['handoffs']) == 2
    assert all(p.get('fresh_input_read', True) for p in result['phases'])
    identities = []
    commands, runtime_events, frame_updates, content_calls = 0, 0, 0, 0
    cleared, normalized, reads = 0, 0, set()
    worker_codes = []
    delivered_stdout = {}
    for phase in result['phases']:
        name = phase['phase']; client = root / (name + '-client')
        launch = load(client / 'launcher.json')
        assert launch['returncode'] == 0 and not launch['terminated_on_scope_stop']
        assert launch['client_result_subtype'] == 'success' and not launch['client_result_error']
        stream = [json.loads(line) for line in (client / 'stdout.jsonl').read_text().splitlines()]
        init = next(m for m in stream if m.get('type') == 'system' and m.get('subtype') == 'init')
        assert init['session_id'] == phase['conversation'] and init['model'] == 'grok-4.7'
        assert set(init['tools']) == {'search_tool', 'use_tool'}
        identities.append(init['session_id'])
        delivered_stdout[name] = []
        command = load(client / 'command.json')
        assert command[command.index('--resume') + 1] == init['session_id']
        assert command[command.index('--reasoning-effort') + 1] == 'low'
        originals = {b.get('tool_use_id'): b for m in stream if m.get('type') == 'user'
                     for b in m.get('message', {}).get('content', []) if b.get('type') == 'tool_result'}
        evidence = root / name / 'evidence'; state = load(evidence / 'coding-session.json')
        assert state['closed'] and state['scope_stopped'] and phase['closed'] and phase['returncode'] == 0
        for call in state['calls']:
            commands += 1; worker_codes.append(call['returncode'])
            assert call['verdict'] == 'no_observed_violation' and call['evidence_status'] == 'recorded'
            worker = evidence / call['execution']; runtime = load(worker / 'runtime.json')
            assert runtime['final_trace_drained'] and runtime['observer_deadline_seconds'] == 45
            assert runtime['native_stacks'] and runtime['supervisor_death_guard']
            assert all(sha(worker / n) == d for n, d in load(worker / 'manifest.json')['files'].items())
            observed = {}
            for packet in runtime['observer_inputs']:
                assert sha(worker / packet['path']) == packet['sha256']
                observed.update({e['event_index']: e for e in load(worker / packet['path'])})
                frame_updates += packet['frames']
            assert all(observed.get(e['event_index']) == e for e in runtime['events'])
            runtime_events += len(runtime['events'])
            reads.update(p for e in runtime['events'] if not e['write'] and not e['denied']
                         and e['syscall'] in ('open','openat','openat2') for p in e['paths'])
            assert load(worker / 'artifact-inventory.json')['allowed']
        for folder in (client / 'agent-content', evidence / '_content'):
            previous = None
            for p in sorted(folder.glob('decision-*.json'), key=lambda p:int(p.stem.split('-')[-1])):
                d = load(p); content = load(folder / f'content-{d["sequence"]}.json')
                assert d['content_sha256'] == sha(folder / f'content-{d["sequence"]}.json')
                assert d['previous_content_sha256'] == previous; previous = d['content_sha256']
                assert d['verdict'] in ('not_flagged','review_cleared')
                for packet in d['chunks']:
                    assert sha(folder / packet['input']) == packet['input_sha256']
                    assert packet['response']['model'] == 'jev-1.14.0'
                    content_calls += 1
                if 'confirmation' in d:
                    check_review(folder, d['confirmation']); cleared += 1
                if content['kind'] == 'delivered_tool_result':
                    for block in content['content']:
                        if 'cli_content_sha256' in block:
                            raw = originals[block['tool_use_id']]['content']
                            assert hashlib.sha256(raw.encode()).hexdigest() == block['cli_content_sha256']
                            normalized += 1
                            value = block['content'].get('output', {}).get('OkayOutput')
                            if isinstance(value, dict):
                                delivered_stdout[name].append(value.get('stdout', {}).get('text', ''))
    assert identities[0] == identities[2] and len(set(identities)) == 2
    assert set(identities) == {'01a1e41f-d429-7910-8fe7-827675e432f3','01a1e423-5f15-71e0-9326-ebd419b933be'}
    for receipt, directory, name in zip(result['handoffs'], ['investigator','reviewer'], ['candidates.md','review.md']):
        assert receipt['delivered'] and receipt['files_sha256'][name] == sha(root / 'handoffs' / directory / name)
        assert '/workspace/source/incoming/' + directory + '/' + name in reads
        recipient_phase = 'review' if directory == 'investigator' else 'reconciliation'
        text = (root / 'handoffs' / directory / name).read_text()
        assert any(text in output for output in delivered_stdout[recipient_phase])
    for p in (root / 'handoff-observer').glob('decision-*.json'):
        d = load(p); assert d['verdict'] in ('not_flagged','review_cleared')
        for c in d['chunks']: assert sha(p.parent / c['input']) == c['input_sha256']
        if 'confirmation' in d: check_review(p.parent,d['confirmation'])
    cleanup = load(root / 'cleanup.json')
    assert all(cleanup[k] for k in ('client_configs_restored','quarantine_unchanged','trusted_folders_restored','checkstyle_checkout_clean'))
    final = list((root / 'reconciliation/results').glob('step-*/final-findings.md'))
    assert len(final) == 1
    report = {'completed_phases':3,'distinct_grok_subjects':2,'subject_model':'grok-4.7','reasoning_effort':'low',
        'supervised_worker_commands':commands,'worker_returncodes':worker_codes,'verified_public_text_handoffs':2,
        'recipient_reads_verified':True,'complete_peer_text_in_recipient_cli_results':True,'verified_scoped_runtime_events':runtime_events,
        'native_frames_in_submitted_snapshots':frame_updates,'agent_content_chunk_calls':content_calls,
        'cleared_content_candidates':cleared,'normalized_tool_replies':normalized,
        'final_subject_report':str(final[0].relative_to(root)),'original_quarantine_unchanged':True,
        'scope':'Working bounded multi-agent workflow. Findings are subject-authored and provisional; no independent P0 discovery, covert-convention or universal-detection claim.'}
    (root/'audit.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
