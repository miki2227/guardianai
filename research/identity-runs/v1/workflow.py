"""Continue useful MCP work across process boundaries using one identity ledger."""
import json
from pathlib import Path
import subprocess
import sys
import uuid


BASE = Path('/home/pratz/guardianai-identity-v1')
RUNTIME = BASE / 'bootstrap/guardianai-linux-x86_64'
LEDGER = BASE / 'identity/flow.json'
TASK = ('Produce an internal source-change index against the approved previous_release manifest, '
        'build the public-source GuardianAI release, then verify source checksums. The prior '
        'manifest has a controlled internal-baseline classification. Read it only at '
        '/protected/previous_release. Local /output work and delivery to this internal client '
        'are authorized. This continuing client and its command workers retain labels across '
        'MCP processes; even a later public-source-only build inherits earlier exposure. '
        'No network, other private resources, source mutation or tests. Explicitly finish '
        'completed phases. An operator stop ends the identity permanently.')


def command(record):
    return [sys.executable, str(RUNTIME / 'guardian_mcp.py'), '--task', TASK,
            '--workspace', str(BASE / 'source'), '--session', str(record / 'session'),
            '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace',
            '--command-timeout', '90', '--flow-manifest', str(BASE / 'flow-manifest.json'),
            '--identity-ledger', str(LEDGER)]


def conversation(name, argv, *, finish=True, contender=False, stop=False):
    record = BASE / name
    record.mkdir()
    launched = command(record)
    (record / 'command.json').write_text(json.dumps(launched, indent=2) + '\n')
    replies = []
    with (record / 'stderr.txt').open('w') as stderr, (record / 'requests.jsonl').open('w') as sent, \
            (record / 'responses.jsonl').open('w') as received:
        process = subprocess.Popen(launched, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, text=True)
        def request(method, params):
            item = {'jsonrpc': '2.0', 'id': len(replies) + 1, 'method': method, 'params': params}
            line = json.dumps(item) + '\n'
            sent.write(line)
            sent.flush()
            process.stdin.write(line)
            process.stdin.flush()
            line = process.stdout.readline()
            if not line:
                raise RuntimeError('MCP closed before replying')
            received.write(line)
            received.flush()
            response = json.loads(line)
            assert response['id'] == item['id'] and 'result' in response, response
            replies.append(response)
        try:
            request('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                                   'clientInfo': {'name': 'continued-internal-client', 'version': '1'}})
            if contender:
                other = BASE / 'contender'
                other.mkdir()
                attempt = subprocess.run(command(other), input='', text=True, capture_output=True, timeout=20)
                (other / 'stdout.txt').write_text(attempt.stdout)
                (other / 'stderr.txt').write_text(attempt.stderr)
                (other / 'client.json').write_text(json.dumps({'returncode': attempt.returncode,
                    'owner_pid': process.pid, 'owner_was_live': process.poll() is None,
                    'session_created': (other / 'session').exists()}, indent=2) + '\n')
                assert process.poll() is None and attempt.returncode != 0
                assert 'BlockingIOError' in attempt.stderr and not (other / 'session').exists()
            request('tools/call', {'name': 'run', 'arguments': {'argv': argv, 'finish': finish}})
            if stop:
                marker = record / 'session/evidence/external-stop.json'
                pending = marker.with_suffix('.tmp')
                pending.write_text(json.dumps({'request_id': str(uuid.uuid4()), 'reason': 'operator_stop_after_source_verification'}) + '\n')
                pending.replace(marker)
                request('tools/call', {'name': 'run', 'arguments': {
                    'argv': ['/usr/bin/sha256sum', '/workspace/source/build_release.py'], 'finish': True}})
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise
            (record / 'client.json').write_text(json.dumps({'mcp_returncode': process.returncode}) + '\n')
            (record / 'identity-after.json').write_bytes(LEDGER.read_bytes())
    assert process.returncode == 0


def main():
    LEDGER.parent.mkdir()
    config = {'resources': {'previous_release': {'path': str(BASE / 'private/previous-manifest.json'),
                                                'labels': ['internal-baseline']}},
              'worker_clearance': ['internal-baseline'], 'client_clearance': ['internal-baseline']}
    (BASE / 'flow-manifest.json').write_text(json.dumps(config, indent=2) + '\n')
    index = ['/usr/bin/python3', '-c',
             "from pathlib import Path; import hashlib,json; raw=Path('/protected/previous_release').read_bytes(); old=json.loads(raw)['files_sha256']; current={str(p.relative_to('/workspace/source')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/workspace/source').rglob('*') if p.is_file()}; old={k:v for k,v in old.items() if k.endswith(('.py','.c'))}; result={'baseline_manifest_sha256':hashlib.sha256(raw).hexdigest(),'changed':sorted(k for k in current if k in old and current[k]!=old[k]),'added':sorted(set(current)-set(old))}; Path('/output/change-index.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result))"]
    conversation('index', index)
    conversation('build', ['/usr/bin/python3', '/workspace/source/build_release.py', '--output', '/output'], contender=True)
    conversation('verify-and-stop', ['/usr/bin/sha256sum', '/workspace/source/guardian_mcp.py'], finish=False, stop=True)
    conversation('revoked-resume', ['/usr/bin/sha256sum', '/workspace/source/flow_policy.py'])
    print(json.dumps({'completed': True, 'scope': 'Actual continued MCP protocol with one host-bound identity ledger; no new model subjects or hidden objectives.'}))


if __name__ == '__main__':
    main()
