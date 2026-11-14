import hashlib
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import threading
import time
import unittest

from release_broker import ReleaseBroker
from runtime_supervisor import supervise
if sys.platform == "linux":
    from seccomp_gate import SeccompGate


SENSOR = "/home/pratz/guardianai-tools/unpacked/usr/bin/strace"
LAUNCHER = Path(__file__).resolve().parents[1] / "native" / "notify-launch"


@unittest.skipUnless(sys.platform == "linux" and Path(SENSOR).exists() and LAUNCHER.exists(), "requires built Linux notification launcher")
class SeccompKernelTests(unittest.TestCase):
    def execute(self, body, *, granted=True, observer=None, broker_ready=None, command=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "input", root / "output"
            source.mkdir()
            output.mkdir()
            shutil.copyfile(LAUNCHER, source / "notify-launch")
            (source / "notify-launch").chmod(0o500)
            (source / "payload.py").write_text(body)
            broker = ReleaseBroker("Read approved summary", {"summary": b"APPROVED-SNAPSHOT", "secret": b"UNGRANTED-CANARY"},
                                   {"A": {"summary"}} if granted else {}, observer or (lambda state: {"probability": .01}))
            gate = SeccompGate(broker, "A", LAUNCHER)
            server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            worker = threading.Thread(target=gate.serve, args=(server,))
            worker.start()
            if broker_ready:
                broker_ready(broker)
            try:
                report = supervise("Read authorized virtual summary", source,
                                   ["/workspace/notify-launch", *(command or ["/usr/bin/python3", "/workspace/payload.py"])],
                                   output=output, evidence=root / "evidence", sensor=SENSOR,
                                   observer=lambda task, events: {"probability": .01},
                                   broker_channel=client, stop_event=broker.stop_event, timeout=6)
            finally:
                client.close()
                worker.join(3)
            data = json.loads((output / "result.json").read_text()) if (output / "result.json").exists() else None
            if command:
                data = {'stdout': (root / 'evidence' / 'stdout.txt').read_text()}
            self.assertFalse(worker.is_alive(), gate.audit)
            return report, broker.audit, gate.audit, data, (output / "late").exists()

    def test_normal_file_read_uses_kernel_gate_and_no_client_fd_survives(self):
        body = """import os,json
from pathlib import Path
value=Path('/protected/summary').read_bytes()
fds={}
for n in os.listdir('/proc/self/fd'):
 try: fds[n]=os.readlink('/proc/self/fd/'+n)
 except OSError: pass
Path('/output/result.json').write_text(json.dumps({'value':value.decode(),'fds':fds,'channel_env':os.environ.get('GUARDIAN_BROKER_FD')}))
"""
        report, audit, kernel, data, late = self.execute(body)
        self.assertEqual(report["verdict"], "no_observed_violation", (report, audit, kernel))
        self.assertEqual(data['value'], 'APPROVED-SNAPSHOT')
        self.assertIsNone(data['channel_env'])
        self.assertTrue(all(int(n) <= 2 for n in data['fds']))
        self.assertEqual(sum(e['event'] == 'release_committed' for e in audit), 1)
        self.assertEqual(sum(e['event'] == 'protected_open' for e in kernel), 1)

    def test_ungranted_file_open_stops_scope_without_protected_fd(self):
        body = "from pathlib import Path\nimport time\ntry: Path('/protected/summary').read_bytes()\nexcept OSError: pass\ntime.sleep(1)\nPath('/output/late').write_text('bad')\n"
        report, audit, kernel, data, late = self.execute(body, granted=False)
        self.assertEqual(report['verdict'], 'violation', (report, audit, kernel))
        self.assertFalse(late)
        self.assertFalse(any(e['event'] == 'release_committed' for e in audit))

    def test_non_utf8_public_path_does_not_reach_resource_policy(self):
        body = "import os\nfd=os.open(b'/output/nonutf8-\\xff',os.O_WRONLY|os.O_CREAT,0o600)\nos.write(fd,b'ok')\nos.close(fd)\n"
        report, audit, kernel, data, late = self.execute(body)
        self.assertEqual(report['verdict'], 'no_observed_violation', (report, audit, kernel))
        self.assertFalse(any(e['event'] == 'release_committed' for e in audit))

    def test_unmodified_cat_reads_authorized_virtual_file(self):
        report, audit, kernel, data, late = self.execute('', command=['/usr/bin/cat', '/protected/summary'])
        self.assertEqual(report['verdict'], 'no_observed_violation', (report, audit, kernel))
        self.assertEqual(data['stdout'], 'APPROVED-SNAPSHOT')

    def test_open_openat_openat2_return_readonly_sealed_snapshots(self):
        body = """import os,ctypes,json
from pathlib import Path
libc=ctypes.CDLL(None,use_errno=True)
path=ctypes.create_string_buffer(b'/protected/summary')
class How(ctypes.Structure):
 _fields_=[('flags',ctypes.c_uint64),('mode',ctypes.c_uint64),('resolve',ctypes.c_uint64)]
how=How(os.O_CLOEXEC,0,0)
fds=[libc.syscall(2,path,os.O_RDONLY|os.O_CLOEXEC),libc.syscall(257,-100,path,os.O_RDONLY|os.O_CLOEXEC),libc.syscall(437,-100,path,ctypes.byref(how),ctypes.sizeof(how))]
values=[]
for fd in fds:
 if fd<0: raise OSError(ctypes.get_errno(),'open failed')
 try: os.write(fd,b'bad'); raise AssertionError('writable snapshot')
 except OSError: pass
 values.append(os.read(fd,100).decode())
 os.close(fd)
Path('/output/result.json').write_text(json.dumps(values))
"""
        report, audit, kernel, data, late = self.execute(body)
        self.assertEqual(report['verdict'], 'no_observed_violation', (report, audit, kernel))
        self.assertEqual(data, ['APPROVED-SNAPSHOT']*3)

    def test_mutating_path_during_approval_cannot_select_ungranted_resource(self):
        body = """import ctypes,threading,time,os,json
from pathlib import Path
libc=ctypes.CDLL(None,use_errno=True)
path=ctypes.create_string_buffer(b'/protected/summary',64)
def change():
 time.sleep(.1)
 path.value=b'/protected/secret'
thread=threading.Thread(target=change)
thread.start()
fd=libc.syscall(257,-100,path,os.O_RDONLY|os.O_CLOEXEC)
if fd<0: raise OSError(ctypes.get_errno(),'open failed')
value=os.read(fd,100).decode()
os.close(fd)
thread.join()
Path('/output/result.json').write_text(json.dumps({'value':value,'final_path':path.value.decode()}))
"""
        def delayed(state):
            time.sleep(.3)
            return {'probability': .01}
        report, audit, kernel, data, late = self.execute(body, observer=delayed)
        self.assertEqual(report['verdict'], 'no_observed_violation', (report, audit, kernel))
        self.assertEqual(data['final_path'], '/protected/secret')
        self.assertEqual(data['value'], 'APPROVED-SNAPSHOT')
        commits = [e for e in audit if e['event'] == 'release_committed']
        self.assertEqual([e['resource_sha256'] for e in commits], [hashlib.sha256(b'APPROVED-SNAPSHOT').hexdigest()])

    def test_revocation_during_pending_syscall_prevents_fd_injection(self):
        entered, finish = threading.Event(), threading.Event()
        def delayed(state):
            entered.set()
            if not finish.wait(2): raise TimeoutError()
            return {'probability': .01}
        revoker = None
        def ready(broker):
            nonlocal revoker
            def revoke():
                if entered.wait(3): broker.revoke()
                finish.set()
            revoker = threading.Thread(target=revoke)
            revoker.start()
        body = "from pathlib import Path\nimport time\ntry: Path('/protected/summary').read_bytes()\nexcept OSError: pass\ntime.sleep(1)\nPath('/output/late').write_text('bad')\n"
        try:
            report, audit, kernel, data, late = self.execute(body, observer=delayed, broker_ready=ready)
        finally:
            finish.set()
            if revoker: revoker.join(3)
        self.assertTrue(entered.is_set())
        self.assertEqual(report['verdict'], 'violation', (report, audit, kernel))
        self.assertFalse(late)
        self.assertFalse(any(e['event'] == 'release_committed' for e in audit))
