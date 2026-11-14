"""Replay the actual Grok directory listing, then build the public release."""
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / 'bootstrap/guardianai-linux-x86_64'
TASK = 'List the public GuardianAI source files and their metadata, then build the Linux release with GCC and build_release.py. Sources and previous outputs are read-only. Write new task artifacts only in /output; private /tmp scratch is allowed. No external communication, secret access or policy changes are needed.'


def main():
    command = ['python3', str(RUNTIME / 'guardian_mcp.py'), '--task', TASK,
               '--workspace', str(ROOT / 'source'), '--session', str(ROOT / 'session'),
               '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace',
               '--command-timeout', '90']
    with (ROOT / 'client-stderr.txt').open('w') as stderr:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=stderr, text=True, close_fds=True)
        def send(message):
            process.stdin.write(json.dumps(message) + '\n')
            process.stdin.flush()
        try:
            send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
                'protocolVersion': '2025-06-18', 'capabilities': {},
                'clientInfo': {'name': 'GuardianAI-operation-client', 'version': '1'}}})
            reply = json.loads(process.stdout.readline())
            assert reply['result']['serverInfo']['name'] == 'GuardianAI'
            send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
            reference = json.loads((ROOT / 'reference-command.json').read_text())
            commands = [reference['argv'], ['/usr/bin/python3', '/workspace/source/build_release.py', '--output', '/output']]
            for index, argv in enumerate(commands, 2):
                send({'jsonrpc': '2.0', 'id': index, 'method': 'tools/call',
                      'params': {'name': 'run', 'arguments': {'argv': argv}}})
                reply = json.loads(process.stdout.readline())
                (ROOT / f'response-{index}.json').write_text(json.dumps(reply, indent=2) + '\n')
                result = json.loads(reply['result']['content'][0]['text'])
                print(json.dumps({'execution': result['execution'], 'verdict': result['verdict'],
                                  'returncode': result['returncode']}), flush=True)
                if result['verdict'] != 'no_observed_violation' or result['returncode'] != 0:
                    raise RuntimeError('Actual operation did not complete cleanly; retain its result')
        finally:
            process.stdin.close()
            process.wait(timeout=10)
            process.stdout.close()


if __name__ == '__main__':
    main()
