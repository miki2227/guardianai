"""Interrupt a real packaged release build and check fail-closed resumption."""
import json
import os
from pathlib import Path
import select
import subprocess
import time

BASE = Path('/home/pratz/guardianai-crash-recovery-v1')
RUNTIME = Path('/home/pratz/guardianai-identity-v1/bootstrap/guardianai-linux-x86_64')


def main():
    BASE.mkdir()
    (BASE / 'identity').mkdir()
    manifest = BASE / 'flow.json'
    manifest.write_text(json.dumps({'resources': {}, 'worker_clearance': [], 'client_clearance': []}))
    ledger = BASE / 'identity/ledger.json'
    def command(name):
        return ['python3', str(RUNTIME / 'guardian_mcp.py'), '--task',
                'Build the GuardianAI release from public source into /output. The operator may interrupt this actual build.',
                '--workspace', '/home/pratz/guardianai-identity-v1/source', '--session', str(BASE / name),
                '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace',
                '--command-timeout', '90', '--flow-manifest', str(manifest), '--identity-ledger', str(ledger)]
    initialize = {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}}
    run = {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'run', 'arguments':
           {'argv': ['/usr/bin/python3', '/workspace/source/build_release.py', '--output', '/output']}}}
    request = '\n'.join(json.dumps(item) for item in (initialize, run)) + '\n'
    (BASE / 'requests.jsonl').write_text(request)
    worker_fd = None
    with (BASE / 'responses.jsonl').open('wb') as stdout, (BASE / 'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(command('interrupted'), stdin=subprocess.PIPE, stdout=stdout, stderr=stderr)
        try:
            process.stdin.write(request.encode()); process.stdin.flush()
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                for trace in (BASE / 'interrupted/evidence/step-001').glob('trace.*'):
                    if b'/workspace/source/build_release.py' not in trace.read_bytes(): continue
                    pid = int(trace.name.split('.')[-1])
                    try:
                        if not (Path('/proc') / str(pid) / 'comm').read_text().startswith('python'): continue
                        candidate = os.pidfd_open(pid)
                    except OSError: continue
                    poller = select.poll(); poller.register(candidate, select.POLLIN)
                    if poller.poll(0): os.close(candidate); continue
                    worker_fd = candidate
                    break
                if worker_fd is not None: break
                if process.poll() is not None: raise RuntimeError('Supervisor exited before active build')
                time.sleep(.02)
            if worker_fd is None: raise RuntimeError('No live build observed')
            (BASE / 'identity-before-kill.json').write_bytes(ledger.read_bytes())
            process.kill(); process.wait(timeout=15)
            exited = bool(poller.poll(10000))
            (BASE / 'identity-after-kill.json').write_bytes(ledger.read_bytes())
            result = {'supervisor_returncode': process.returncode, 'worker_pid': pid,
                      'live_build_observed': True, 'worker_pidfd_exited_after_supervisor_kill': exited}
        finally:
            if worker_fd is not None: os.close(worker_fd)
            if process.poll() is None: process.kill(); process.wait()
    run['params']['arguments'] = {'argv': ['/usr/bin/sha256sum', '/workspace/source/guardian_mcp.py'], 'finish': True}
    resume = subprocess.run(command('resumed'), input='\n'.join(json.dumps(r) for r in (initialize, run))+'\n',
                            text=True, capture_output=True, timeout=30)
    (BASE / 'resume-responses.jsonl').write_text(resume.stdout)
    (BASE / 'resume-stderr.txt').write_text(resume.stderr)
    replies = [json.loads(line) for line in resume.stdout.splitlines()]
    refused = json.loads(next(r for r in replies if r['id'] == 2)['result']['content'][0]['text'])
    result.update(resume_returncode=resume.returncode, resume_result=refused,
                  identity_stopped_after_resume=json.loads(ledger.read_text())['stopped'],
                  resumed_worker_created=(BASE / 'resumed/evidence/step-001').exists(),
                  scope='One real release worker interrupted by SIGKILL; process restart recovery, not power-loss or universal cleanup proof.')
    (BASE / 'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    assert exited and refused.get('reason') == 'scope_stopped' and result['identity_stopped_after_resume']
    assert not result['resumed_worker_created']


if __name__ == '__main__': main()
