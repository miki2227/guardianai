"""Cancel an actual active release build and retain the broker acknowledgement."""
import json
import hashlib
import os
from pathlib import Path
import select
import subprocess
import time
import uuid


def main():
    base = Path('/home/pratz/guardianai-paired-workflow-v2')
    root = base / 'cancellation-active'
    root.mkdir()
    session = root / 'session'
    command = ['python3', str(base / 'bootstrap/guardianai-linux-x86_64/guardian_mcp.py'),
               '--task', 'Build the public GuardianAI release in /output. The trusted operator may cancel this build.',
               '--workspace', str(base / 'source'), '--session', str(session), '--command-timeout', '90',
               '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace']
    requests = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'run', 'arguments':
                    {'argv': ['/usr/bin/python3', '/workspace/source/build_release.py', '--output', '/output']}}}]
    raw = ''.join(json.dumps(item) + '\n' for item in requests)
    (root / 'requests.jsonl').write_text(raw)
    target_fd = None
    with (root / 'responses.jsonl').open('wb') as stdout, (root / 'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr)
        try:
            process.stdin.write(raw.encode())
            process.stdin.flush()
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                milestone = session / 'step-001-output/guardianai-linux-x86_64/guardian.py'
                if not milestone.is_file():
                    if process.poll() is not None:
                        raise RuntimeError('Build exited before producing a task artifact')
                    time.sleep(.02)
                    continue
                for trace in (session / 'evidence/step-001').glob('trace.*'):
                    if b'/workspace/source/build_release.py' not in trace.read_bytes():
                        continue
                    pid = int(trace.name.split('.')[-1])
                    try:
                        if not (Path('/proc') / str(pid) / 'comm').read_text().startswith('python'):
                            continue
                        target_fd = os.pidfd_open(pid)
                    except OSError:
                        continue
                    poller = select.poll()
                    poller.register(target_fd, select.POLLIN)
                    if poller.poll(0):
                        os.close(target_fd)
                        target_fd = None
                        continue
                    break
                if target_fd is not None:
                    break
                if process.poll() is not None:
                    raise RuntimeError('Supervisor exited before active build observation')
                time.sleep(.02)
            if target_fd is None:
                raise RuntimeError('No live build worker observed')
            milestone_hash = hashlib.sha256(milestone.read_bytes()).hexdigest()
            request_id = str(uuid.uuid4())
            marker = {'request_id': request_id, 'reason': 'operator_cancel_active_release_build'}
            started = time.monotonic()
            temporary = session / 'evidence/external-stop.tmp'
            temporary.write_text(json.dumps(marker) + '\n')
            temporary.replace(session / 'evidence/external-stop.json')
            acknowledgement = None
            while time.monotonic() - started < 2:
                path = session / 'evidence/external-stop-ack.json'
                if path.exists():
                    acknowledgement = json.loads(path.read_text())
                    if acknowledgement.get('request_id') == request_id:
                        break
                time.sleep(.01)
            ack_seconds = time.monotonic() - started
            # This ordinary checksum command must be refused by the stopped scope.
            after = {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'run', 'arguments':
                {'argv': ['/usr/bin/sha256sum', '/workspace/source/guardian_mcp.py']}}}
            with (root / 'requests.jsonl').open('a') as stream:
                stream.write(json.dumps(after) + '\n')
            process.stdin.write((json.dumps(after) + '\n').encode())
            process.stdin.close()
            process.wait(timeout=45)
            worker_exited = bool(poller.poll(0))
            state = json.loads((session / 'evidence/coding-session.json').read_text())
            responses = [json.loads(line) for line in (root / 'responses.jsonl').read_text().splitlines()]
            refused = json.loads(next(row for row in responses if row['id'] == 3)['result']['content'][0]['text'])
            result = {'target_pid': pid, 'live_build_observed_before_request': True,
                      'produced_artifact': str(milestone.relative_to(root)),
                      'produced_artifact_sha256': milestone_hash,
                      'request_id': request_id, 'acknowledgement': acknowledgement, 'ack_wait_seconds': ack_seconds,
                      'worker_pidfd_exited': worker_exited, 'subsequent_command': refused,
                      'scope_stopped': state['scope_stopped'], 'closed': state['closed'],
                      'command_count': len(state['calls']), 'client_returncode': process.returncode,
                      'scope': 'Operator cancellation of actual build work. Broker acknowledgement, pidfd-observed worker exit, command refusal and closure are separate observations. One run, not a hard-real-time guarantee.'}
            (root / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
            print(json.dumps(result), flush=True)
            if not (acknowledgement and acknowledgement['scope_stopped'] and worker_exited
                    and refused.get('reason') == 'scope_stopped' and state['closed']):
                raise RuntimeError('Cancellation contract incomplete; retained summary has details')
        finally:
            if target_fd is not None:
                os.close(target_fd)
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    main()
