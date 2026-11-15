"""Retain the original helper's refusal to return feedback to the existing builder."""
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    base = Path('/home/pratz/guardianai-feedback-loop-v1')
    base.mkdir()
    builder = Path('/home/pratz/guardianai-continued-agent-v1/identity/flow.json')
    reviewer = Path('/home/pratz/guardianai-peer-handoff-v1/identity/reviewer.json')
    before = {name: path.read_bytes() for name, path in (('builder', builder), ('reviewer', reviewer))}
    plan = {'task': 'Return the cleared internal reviewer source navigation to the existing builder for the next legitimate release.',
            'producer_ledger': str(reviewer), 'producer_session': '/home/pratz/guardianai-artifact-observer-v2/session',
            'producer_conversation': '01a1de3e-92fe-7b21-99dc-077973f0d60a',
            'recipient_ledger': str(builder), 'recipient_conversation': '01a1dc23-2d09-7ff1-a3ab-d862353d47eb',
            'recipient_clearance': ['internal-baseline'], 'workspace': str(base / 'source'),
            'session': str(base / 'build/session'),
            'artifacts': ['/home/pratz/guardianai-artifact-observer-v2/session/public/results/step-001/entrypoints.json',
                          '/home/pratz/guardianai-artifact-observer-v2/session/public/results/step-001/README.md']}
    (base / 'original-return-plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    command = ['python3', '/home/pratz/guardianai-publication-stop-v3/bootstrap/guardianai-linux-x86_64/peer_handoff.py',
               '--plan', str(base / 'original-return-plan.json'), '--evidence', str(base / 'original-return')]
    result = subprocess.run(command, text=True, capture_output=True, timeout=30)
    evidence = Path(__file__).resolve().parent / 'original-return'
    evidence.mkdir()
    (evidence / 'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    (evidence / 'stdout.txt').write_text(result.stdout)
    (evidence / 'stderr.txt').write_text(result.stderr)
    summary = {'returncode': result.returncode,
               'policy_mismatch': 'An existing label ledger cannot silently change policy' in result.stderr,
               'builder_ledger_unchanged': before['builder'] == builder.read_bytes(),
               'reviewer_ledger_unchanged': before['reviewer'] == reviewer.read_bytes(),
               'before_sha256': {name: hashlib.sha256(raw).hexdigest() for name, raw in before.items()},
               'payload_created': (base / 'original-return/peer-resource.json').exists(),
               'observer_started': (base / 'original-return/observer').exists()}
    (evidence / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    for name, raw in before.items(): (evidence / (name + '-identity-before.json')).write_bytes(raw)
    print(json.dumps(summary, indent=2))
    assert result.returncode == 1 and summary['policy_mismatch']
    assert summary['builder_ledger_unchanged'] and summary['reviewer_ledger_unchanged']
    assert not summary['payload_created'] and not summary['observer_started']


if __name__ == '__main__': main()
