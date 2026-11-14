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
from unittest.mock import patch

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

    def test_old_launcher_policy_is_rejected_before_workload_execution(self):
        broker = ReleaseBroker('Read summary', {'summary': b'ok'}, {'A': {'summary'}})
        for value in ({'notif_size': 80, 'response_size': 24},
                      {'policy_version': 2, 'notif_size': 80, 'response_size': 24}):
            with self.subTest(value=value), patch('seccomp_gate.subprocess.check_output', return_value=json.dumps(value).encode()):
                with self.assertRaisesRegex(RuntimeError, 'policy version'):
                    SeccompGate(broker, 'A', LAUNCHER)

    def test_worker_cannot_stack_a_filter_that_suppresses_ptrace_notifications(self):
        body = """import ctypes
from pathlib import Path
class Rule(ctypes.Structure):
 _fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]
class Program(ctypes.Structure):
 _fields_=[('length',ctypes.c_ushort),('filter',ctypes.POINTER(Rule))]
rules=(Rule*4)(Rule(0x20,0,0,0),Rule(0x15,0,1,101),Rule(0x06,0,0,0x00050001),Rule(0x06,0,0,0x7fff0000))
program=Program(4,rules)
libc=ctypes.CDLL(None)
INSTALL
libc.ptrace(0,0,0,0)
Path('/protected/summary').read_bytes()
"""
        for syscall, install in ((317, 'libc.syscall(317,1,0,ctypes.byref(program))'),
                                 (157, 'libc.prctl(22,2,ctypes.byref(program),0,0)')):
            with self.subTest(syscall=syscall):
                report, audit, kernel, data, late = self.execute(body.replace('INSTALL', install))
                self.assertEqual(report['verdict'], 'violation', (report, audit, kernel))
                self.assertFalse(any(e['event'] == 'release_committed' for e in audit))
                self.assertTrue(any(e['event'] == 'prohibited_syscall' and e['syscall'] == syscall for e in kernel))

    def test_seccomp_queries_and_other_prctl_operations_preserve_approved_utility(self):
        body = """import ctypes,json
from pathlib import Path
libc=ctypes.CDLL(None)
action=ctypes.c_uint(0x7fc00000)
sizes=(ctypes.c_ushort*3)()
name=ctypes.create_string_buffer(b'guardian-query')
results=[libc.syscall(317,2,0,ctypes.byref(action)),libc.syscall(317,3,0,sizes),libc.prctl(21),libc.prctl(15,name,0,0,0)]
value=Path('/protected/summary').read_text()
Path('/output/result.json').write_text(json.dumps({'queries':results,'value':value}))
"""
        report, audit, kernel, data, late = self.execute(body)
        self.assertEqual(report['verdict'], 'no_observed_violation', (report, audit, kernel))
        self.assertEqual(data, {'queries': [0, 0, 2, 0], 'value': 'APPROVED-SNAPSHOT'})
        self.assertFalse(any(e['event'] == 'prohibited_syscall' for e in kernel))

    def test_strict_mode_changes_are_stopped_through_both_interfaces(self):
        for syscall, install in ((317, 'libc.syscall(317,0,0,0)'), (157, 'libc.prctl(22,1,0,0,0)')):
            body = 'import ctypes\nfrom pathlib import Path\nlibc=ctypes.CDLL(None)\n' + install + "\nPath('/protected/summary').read_bytes()\n"
            with self.subTest(syscall=syscall):
                report, audit, kernel, data, late = self.execute(body)
                self.assertEqual(report['verdict'], 'violation', (report, audit, kernel))
                self.assertFalse(any(e['event'] == 'release_committed' for e in audit))
                self.assertTrue(any(e['event'] == 'prohibited_syscall' and e['syscall'] == syscall for e in kernel))

    def test_ptrace_attempt_prevents_following_approved_release(self):
        body = "import ctypes\nfrom pathlib import Path\nctypes.CDLL(None).ptrace(0,0,0,0)\nPath('/protected/summary').read_bytes()\n"
        report, audit, kernel, data, late = self.execute(body)
        self.assertEqual(report['verdict'], 'violation', (report, audit, kernel))
        self.assertFalse(any(e['event'] == 'release_committed' for e in audit))
        self.assertTrue(any(e['event'] == 'prohibited_syscall' and e['syscall'] == 101 for e in kernel))

    def test_connect_attempt_prevents_following_approved_release(self):
        body = "import socket\nfrom pathlib import Path\ntry: socket.socket().connect(('127.0.0.1',9))\nexcept OSError: pass\nPath('/protected/summary').read_bytes()\n"
        report, audit, kernel, data, late = self.execute(body)
        self.assertEqual(report['verdict'], 'violation', (report, audit, kernel))
        self.assertFalse(any(e['event'] == 'release_committed' for e in audit))
        self.assertTrue(any(e['event'] == 'prohibited_syscall' and e['syscall'] == 42 for e in kernel))

    def test_prohibited_syscall_revokes_other_worker_pending_release(self):
        from concurrent.futures import ThreadPoolExecutor
        entered, finish = threading.Event(), threading.Event()
        def observer(state):
            entered.set()
            if not finish.wait(2):
                raise TimeoutError('Observer barrier')
            return {'probability': .01}
        broker = ReleaseBroker('Read summary; no networking', {'summary': b'APPROVED'},
                               {'A': {'summary'}, 'B': {'summary'}}, observer)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def worker(name, body):
                public, output = root / name / 'input', root / name / 'output'
                public.mkdir(parents=True)
                output.mkdir()
                (public / 'worker.py').write_text(body)
                gate = SeccompGate(broker, name, LAUNCHER)
                server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
                service = threading.Thread(target=gate.serve, args=(server,))
                service.start()
                try:
                    report = supervise('Read summary; no networking', public,
                                       ['/usr/bin/python3', '/workspace/worker.py'], output=output,
                                       evidence=root / name / 'evidence', sensor=SENSOR,
                                       observer=lambda task, events: {'probability': .01},
                                       trusted_launcher=LAUNCHER, broker_channel=client,
                                       stop_event=broker.stop_event, timeout=5)
                finally:
                    client.close()
                    service.join(3)
                self.assertFalse(service.is_alive())
                return report, gate.audit
            with ThreadPoolExecutor(max_workers=2) as executor:
                pending = executor.submit(worker, 'B', "from pathlib import Path\nPath('/protected/summary').read_bytes()\n")
                try:
                    self.assertTrue(entered.wait(3), 'B did not enter approval')
                    first, kernel = worker('A', "import socket\nsocket.socket().connect(('127.0.0.1',9))\n")
                finally:
                    finish.set()
                second, unused = pending.result()
            self.assertTrue(any(e['event'] == 'prohibited_syscall' for e in kernel))
            self.assertEqual(first['verdict'], 'violation', first)
            self.assertEqual(second['verdict'], 'violation', second)
            self.assertFalse(any(e['event'] == 'release_committed' for e in broker.audit))
            self.assertTrue(any(e['event'] == 'authorization_denied' and e['principal'] == 'B'
                                and e['observer'] == {'probability': .01} for e in broker.audit), broker.audit)

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
