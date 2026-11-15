"""Refuse changed peer bytes before starting a real checksum command."""
import hashlib
import json
from pathlib import Path
import subprocess


BASE = Path('/home/pratz/guardianai-peer-handoff-v1')


def main():
    manifest = BASE / 'peer-internal/flow-manifest.json'
    config = json.loads(manifest.read_text())
    resource = Path(config['resources']['peer_handoff']['path'])
    original = resource.read_bytes()
    ledger = BASE / 'identity/reviewer.json'
    ledger_before = ledger.read_bytes()
    state = json.loads(ledger_before)
    assert not state['stopped'] and state['active_session'] is None
    assert hashlib.sha256(original).hexdigest() == config['resources']['peer_handoff']['sha256']
    folder = BASE / 'changed-staging'
    folder.mkdir()
    command = ['python3', str(BASE / 'bootstrap/guardianai-linux-x86_64/guardian_mcp.py'),
               '--task', 'Verify the public peer-handoff source checksum.', '--workspace', str(BASE / 'source'),
               '--session', str(folder / 'session'), '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace',
               '--flow-manifest', str(manifest), '--identity-ledger', str(ledger),
               '--expected-conversation', state['provider_conversation']]
    request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'run', 'arguments': {
        'argv': ['/usr/bin/sha256sum', '/workspace/source/peer_handoff.py'], 'finish': True}}}
    (folder / 'command.json').write_text(json.dumps(command, indent=2)+'\n')
    (folder / 'request.json').write_text(json.dumps(request)+'\n')
    try:
        resource.write_bytes(original + b'\n')  # Still valid JSON; byte identity changed.
        result = subprocess.run(command, input=json.dumps(request)+'\n', text=True, capture_output=True, timeout=30)
        (folder / 'stdout.txt').write_text(result.stdout)
        (folder / 'stderr.txt').write_text(result.stderr)
    finally:
        resource.write_bytes(original)
    summary = {'returncode': result.returncode, 'pinned_digest_refused': 'differs from its pinned SHA-256' in result.stderr,
               'worker_created': (folder / 'session/evidence/step-001').exists(),
               'ledger_unchanged': ledger.read_bytes() == ledger_before,
               'staging_bytes_restored': resource.read_bytes() == original,
               'scope': 'Deliberate private staging change during a real MCP startup; no model subject or worker execution.'}
    (folder / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary))
    assert result.returncode != 0 and summary['pinned_digest_refused']
    assert not summary['worker_created'] and summary['ledger_unchanged'] and summary['staging_bytes_restored']


if __name__ == '__main__': main()
