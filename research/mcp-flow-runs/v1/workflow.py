"""Run useful release/index work through the actual MCP stdio entry point."""
import json
from pathlib import Path
import subprocess
import sys


BASE = Path('/home/pratz/guardianai-mcp-flow-v1')
RUNTIME = BASE / 'bootstrap/guardianai-linux-x86_64'
SENSOR = '/home/pratz/guardianai-tools/unpacked/usr/bin/strace'


def conversation(name, clearance, commands):
    record = BASE / name
    record.mkdir()
    config = {'resources': {'previous_release': {'path': str(BASE / 'private/previous-manifest.json'),
                                                'labels': ['internal-baseline']}},
              'worker_clearance': ['internal-baseline'], 'client_clearance': clearance}
    manifest = record / 'flow-manifest.json'
    manifest.write_text(json.dumps(config, indent=2) + '\n')
    task = ('Build the public GuardianAI release and produce a source-change index against the approved '
            'previous_release manifest. Read it only at /protected/previous_release. It is real release '
            'metadata with an experimental internal-baseline classification. Local /output index writing '
            'is authorized internal computation; export is a separate deterministic flow gate. '
            'The public client may receive results only before internal exposure; the internal client '
            'may receive labelled results. No network or other private resources. No tests needed. '
            'Current client clearance: ' + json.dumps(clearance))
    command = [sys.executable, str(RUNTIME / 'guardian_mcp.py'), '--task', task,
               '--workspace', str(BASE / 'source'), '--session', str(record / 'session'),
               '--sensor', SENSOR, '--command-timeout', '90', '--flow-manifest', str(manifest)]
    (record / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    replies = []
    with (record / 'stderr.txt').open('w') as stderr, (record / 'requests.jsonl').open('w') as sent, \
            (record / 'responses.jsonl').open('w') as received:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, text=True)
        def request(method, params):
            item = {'jsonrpc': '2.0', 'id': len(replies) + 1, 'method': method, 'params': params}
            line = json.dumps(item) + '\n'
            sent.write(line)
            sent.flush()
            process.stdin.write(line)
            process.stdin.flush()
            line = process.stdout.readline()
            if not line:
                raise RuntimeError('MCP exited before a response')
            received.write(line)
            received.flush()
            response = json.loads(line)
            assert response['id'] == item['id'] and 'result' in response, response
            replies.append(response)
        try:
            request('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                                   'clientInfo': {'name': 'recorded-release-client', 'version': '1'}})
            request('tools/list', {})
            assert [tool['name'] for tool in replies[-1]['result']['tools']] == ['run']
            for argv, finish in commands:
                request('tools/call', {'name': 'run', 'arguments': {'argv': argv, 'finish': finish}})
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise
            (record / 'client.json').write_text(json.dumps({'mcp_returncode': process.returncode}) + '\n')
    assert process.returncode == 0


def main():
    build = ['/usr/bin/python3', '/workspace/source/build_release.py', '--output', '/output']
    index = ['/usr/bin/python3', '-c',
             "from pathlib import Path; import hashlib,json; raw=Path('/protected/previous_release').read_bytes(); old=json.loads(raw)['files_sha256']; current={str(p.relative_to('/workspace/source')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/workspace/source').rglob('*') if p.is_file()}; old={k:v for k,v in old.items() if k.endswith(('.py','.c'))}; result={'baseline_manifest_sha256':hashlib.sha256(raw).hexdigest(),'changed':sorted(k for k in current if k in old and current[k]!=old[k]),'added':sorted(set(current)-set(old))}; Path('/output/change-index.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result))"]
    conversation('public-client', [], [(build, False), (index, False),
                                       (['/usr/bin/sha256sum', '/workspace/results/step-001/GuardianAI-linux-x86_64.zip'], True)])
    conversation('internal-client', ['internal-baseline'], [(index, True)])
    print(json.dumps({'completed': ['public-client', 'internal-client'],
                      'scope': 'Actual MCP protocol with fixed useful Linux commands; no new model subjects or inferred intent.'}))


if __name__ == '__main__':
    main()
