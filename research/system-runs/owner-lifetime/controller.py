"""Run a real release build, then cancel a second build by killing its supervisor."""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / 'bootstrap/guardianai-linux-x86_64'
SENSOR = '/home/pratz/guardianai-tools/unpacked/usr/bin/strace'
TASK = 'Build the public GuardianAI release with GCC and build_release.py. Write artifacts only in /output. Public sources are read-only; private /tmp scratch is allowed. No external communication or policy changes are needed.'


def send(process, message):
    process.stdin.write(json.dumps(message) + '\n')
    process.stdin.flush()


def start(name):
    stderr = (ROOT / (name + '-stderr.txt')).open('w')
    process = subprocess.Popen(['python3', str(RUNTIME / 'guardian_mcp.py'), '--task', TASK,
                                '--workspace', str(ROOT / 'source'), '--session', str(ROOT / name),
                                '--sensor', SENSOR, '--command-timeout', '90'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                               text=True, close_fds=True)
    send(process, {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                   'params': {'protocolVersion': '2025-06-18', 'capabilities': {},
                              'clientInfo': {'name': 'GuardianAI-build-controller', 'version': '1'}}})
    response = json.loads(process.stdout.readline())
    assert response['result']['serverInfo']['name'] == 'GuardianAI'
    send(process, {'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    send(process, {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {
        'name': 'run', 'arguments': {'argv': ['/usr/bin/python3', '/workspace/source/build_release.py', '--output', '/output']}}})
    return process, stderr


def descendants(owner):
    pending, rows = [owner], []
    for parent in pending:
        for task in Path(f'/proc/{parent}/task').glob('*'):
            try:
                children = (task / 'children').read_text().split()
            except FileNotFoundError:
                continue
            for child in children:
                pid = int(child)
                if pid in pending:
                    continue
                pending.append(pid)
                try:
                    fields = dict(line.split(':', 1) for line in Path(f'/proc/{pid}/status').read_text().splitlines())
                    argv = Path(f'/proc/{pid}/cmdline').read_bytes().decode(errors='replace').split('\0')[:-1]
                    rows.append({'pid': pid, 'comm': fields['Name'].strip(), 'ppid': int(fields['PPid']),
                                 'nspid': [int(x) for x in fields['NSpid'].split()],
                                 'tracer_pid': int(fields['TracerPid']), 'argv': argv})
                except (FileNotFoundError, ProcessLookupError):
                    continue
    return rows


def exited(descriptor):
    poller = select.poll()
    poller.register(descriptor, select.POLLIN)
    return bool(poller.poll(0))


def main():
    normal, stderr = start('normal')
    response = json.loads(normal.stdout.readline())
    result = json.loads(response['result']['content'][0]['text'])
    (ROOT / 'normal-response.json').write_text(json.dumps(response, indent=2) + '\n')
    normal.stdin.close()
    normal.wait(timeout=10)
    normal.stdout.close()
    stderr.close()
    assert result['verdict'] == 'no_observed_violation' and result['returncode'] == 0
    print(json.dumps({'normal_build': 'completed', 'supervisor_returncode': normal.returncode}), flush=True)

    owner, stderr = start('cancelled')
    owner_fd = os.pidfd_open(owner.pid)
    handles = []
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            rows = descendants(owner.pid)
            if any(row['comm'] in ('gcc', 'cc1', 'as', 'ld') for row in rows):
                break
            if owner.poll() is not None:
                raise RuntimeError('Build supervisor exited before compiler observation')
            time.sleep(.01)
        else:
            raise RuntimeError('Compiler was not observed')
        for row in rows:
            try:
                descriptor = os.pidfd_open(row['pid'])
            except ProcessLookupError:
                continue
            if exited(descriptor):
                os.close(descriptor)
            else:
                handles.append((row, descriptor))
        assert any('--kill-on-exit' in row['argv'] for row, fd in handles)
        assert any(row['nspid'][-1] == 1 and len(row['nspid']) > 1 for row, fd in handles)
        assert any(row['comm'] in ('gcc', 'cc1', 'as', 'ld') for row, fd in handles)
        killed = time.monotonic()
        signal.pidfd_send_signal(owner_fd, signal.SIGKILL)
        observed = {}
        while time.monotonic() - killed < 5:
            for row, descriptor in handles:
                if row['pid'] not in observed and exited(descriptor):
                    observed[row['pid']] = time.monotonic() - killed
            if len(observed) == len(handles):
                break
            time.sleep(.01)
        owner.wait(timeout=5)
        report = {'operation': 'Cancel an actual running GCC release build by SIGKILL of its Python supervisor',
                  'owner_returncode': owner.returncode, 'all_captured_live_descendants_exited': len(observed) == len(handles),
                  'processes': [{**row, 'exit_observed_seconds': observed.get(row['pid'])} for row, fd in handles],
                  'scope': 'One operational cancellation, using stable pidfds for captured live descendants. Poll timings are observation bounds, not hard-real-time guarantees. Interrupted traces are not clean execution evidence.'}
        (ROOT / 'cancellation.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'cancelled_build': report['all_captured_live_descendants_exited'],
                          'captured_live_descendants': len(handles)}), flush=True)
    finally:
        if owner.poll() is None:
            signal.pidfd_send_signal(owner_fd, signal.SIGKILL)
            owner.wait(timeout=5)
        for row, descriptor in handles:
            if not exited(descriptor):
                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            os.close(descriptor)
        os.close(owner_fd)
        owner.stdin.close()
        owner.stdout.close()
        stderr.close()


if __name__ == '__main__':
    main()
