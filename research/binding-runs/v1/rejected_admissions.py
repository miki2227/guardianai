"""Exercise the real MCP admission boundary using isolated ledger copies."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


BASE = Path('/home/pratz/guardianai-binding-v1')
RUNTIME = BASE / 'bootstrap/guardianai-linux-x86_64'
ORIGINAL = Path('/home/pratz/guardianai-continued-agent-v1/identity/flow.json')


def main():
    results = {}
    actual_id = json.loads(ORIGINAL.read_text())['provider_conversation']
    stale = json.loads((BASE / 'session/evidence/client-binding.json').read_text())
    init = {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}}
    run = {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'run',
           'arguments': {'argv': ['/usr/bin/sha256sum', '/workspace/source/guardian_mcp.py'], 'finish': True}}}
    original_hash = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    for name in ('wrong-conversation', 'missing-approval', 'stale-approval'):
        folder = BASE / name
        folder.mkdir()
        ledger = folder / 'identity.json'
        shutil.copyfile(ORIGINAL, ledger)
        command = ['python3', str(RUNTIME / 'guardian_mcp.py'), '--task', 'Verify the public MCP source checksum.',
                   '--workspace', str(BASE / 'source'), '--session', str(folder / 'session'),
                   '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace',
                   '--flow-manifest', '/home/pratz/guardianai-continued-agent-v1/flow-manifest.json',
                   '--identity-ledger', str(ledger)]
        if name != 'missing-approval':
            command += ['--expected-conversation', '01a1de3e-92fe-7b21-99dc-077973f0d60a' if name == 'wrong-conversation' else actual_id]
        (folder / 'command.json').write_text(json.dumps(command, indent=2)+'\n')
        (folder / 'requests.jsonl').write_text(json.dumps(init)+'\n'+json.dumps(run)+'\n')
        with (folder / 'stderr.txt').open('w') as stderr:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, text=True)
            first, rest = '', ''
            try:
                process.stdin.write(json.dumps(init)+'\n'); process.stdin.flush()
                first = process.stdout.readline()
                if name == 'wrong-conversation':
                    process.wait(timeout=15)
                    assert process.returncode != 0
                    assert 'belongs to another conversation' in (folder / 'stderr.txt').read_text()
                    assert ledger.read_bytes() == ORIGINAL.read_bytes()
                    result = {'startup_refused': True, 'ledger_unchanged': True, 'returncode': process.returncode}
                else:
                    assert json.loads(first)['id'] == 1
                    state = json.loads((folder / 'session/evidence/coding-session.json').read_text())
                    assert state['client_binding']['expected_conversation'] == actual_id
                    assert state['client_binding']['request_id'] != stale['request_id']
                    if name == 'stale-approval':
                        (folder / 'session/evidence/client-binding.json').write_text(json.dumps(stale)+'\n')
                    rest, _ = process.communicate(json.dumps(run)+'\n', timeout=15)
                    response = json.loads(next(line for line in rest.splitlines() if json.loads(line)['id'] == 2))
                    verdict = json.loads(response['result']['content'][0]['text'])
                    state = json.loads((folder / 'session/evidence/coding-session.json').read_text())
                    assert verdict['reason'] == 'client_binding_unverified'
                    assert state['calls'] == [] and state['scope_stopped'] and state['closed']
                    assert not (folder / 'session/evidence/step-001').exists()
                    result = {'result': verdict, 'commands_executed': 0, 'closed': state['closed'],
                              'binding_status': state['client_binding']['status']}
                (folder / 'responses.jsonl').write_text(first+rest)
                results[name] = result
            finally:
                if process.poll() is None: process.kill(); process.wait()
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == original_hash
    (BASE / 'admission-summary.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(results))


if __name__ == '__main__': main()
