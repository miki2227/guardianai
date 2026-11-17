import base64
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest

from release_broker import ReleaseBroker
from runtime_supervisor import supervise


@unittest.skipUnless(sys.platform == "linux", "requires Linux seqpacket transport")
class ReleaseTests(unittest.TestCase):
    def broker(self, observer=lambda state: {"probability": .01}):
        return ReleaseBroker("Read the approved summary", {"summary": b"approved bytes"},
                             {"A": {"summary"}}, observer)

    def request(self, broker, request=None, agent="A"):
        server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        try:
            broker.handle(server, agent, request or {"operation": "read", "resource": "summary", "epoch": 1})
            return json.loads(client.recv(65536))
        finally:
            server.close()
            client.close()

    def test_approved_release_matches_snapshot(self):
        response = self.request(self.broker())
        self.assertEqual(base64.b64decode(response["content_base64"]), b"approved bytes")

    def test_spoofed_principal_and_path_requests_are_denied(self):
        for request in ({"operation": "read", "resource": "/etc/passwd", "epoch": 1},
                        {"operation": "read", "resource": "summary", "epoch": 1, "agent": "A"},
                        {"operation": "read", "resource": "summary", "epoch": True}):
            self.assertEqual(self.request(self.broker(), request)["decision"], "deny")
        self.assertEqual(self.request(self.broker(), agent="B")["decision"], "deny")

    def test_stale_epoch_is_denied_without_inference(self):
        def should_not_run(state):
            self.fail("Stale authority reached observer")
        broker = self.broker(should_not_run)
        broker.replace_task("New task", {"A": {"summary"}})
        self.assertEqual(self.request(broker)["decision"], "deny")

    def test_stop_is_terminal_for_this_scope(self):
        broker = self.broker()
        broker.stop_event.set()
        with self.assertRaises(RuntimeError):
            broker.stop_event.clear()
        self.assertEqual(self.request(broker)["decision"], "deny")

    def test_invalid_or_unavailable_observer_cannot_release_bytes(self):
        for value in (float('nan'), float('inf'), True, "allow", -.01, 1.01):
            broker = self.broker(lambda state: {"probability": value})
            self.assertEqual(self.request(broker)["decision"], "deny")
            self.assertFalse(any(e["event"] == "release_committed" for e in broker.audit))
        def unavailable(state):
            raise ConnectionError("Injected outage")
        self.assertEqual(self.request(self.broker(unavailable))["decision"], "deny")

    def test_pending_allow_invalidated_by_task_resource_or_evidence_change(self):
        for change in (lambda b: b.revoke(), lambda b: b.lose_evidence(),
                       lambda b: b.replace_task("Different task", {"A": {"summary"}}),
                       lambda b: b.replace_resource("summary", b"replacement")):
            with self.subTest(change=change):
                entered, finish = threading.Event(), threading.Event()
                def delayed(state):
                    entered.set()
                    if not finish.wait(1):
                        raise TimeoutError()
                    return {"probability": .01}
                broker = self.broker(delayed)
                server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
                worker = threading.Thread(target=broker.handle, args=(server, "A", {"operation": "read", "resource": "summary", "epoch": 1}))
                worker.start()
                try:
                    self.assertTrue(entered.wait(1))
                    change(broker)
                    finish.set()
                    worker.join(2)
                    self.assertFalse(worker.is_alive())
                    self.assertEqual(json.loads(client.recv(65536))["decision"], "deny")
                    self.assertFalse(any(e["event"] == "release_committed" for e in broker.audit))
                finally:
                    finish.set()
                    worker.join(2)
                    server.close()
                    client.close()

    def test_committed_bytes_cannot_be_retracted(self):
        broker = self.broker()
        server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        try:
            broker.handle(server, "A", {"operation": "read", "resource": "summary", "epoch": 1})
            broker.revoke()
            self.assertEqual(json.loads(client.recv(65536))["decision"], "allow")
        finally:
            server.close()
            client.close()

    def test_truncated_request_stops_scope_without_release(self):
        broker = self.broker()
        stop = broker.stop_event
        server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        worker = threading.Thread(target=broker.serve, args=(server, "A"))
        worker.start()
        try:
            client.send(b" " * 5000)
            self.assertEqual(json.loads(client.recv(65536))["decision"], "deny")
            worker.join(2)
            self.assertTrue(stop.is_set())
            self.assertFalse(worker.is_alive())
        finally:
            client.close()
            worker.join(2)

    def test_full_socket_cannot_block_revocation_or_commit_protected_bytes(self):
        broker = self.broker()
        server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        try:
            while True:
                try:
                    server.send(b"x" * 8192, socket.MSG_DONTWAIT)
                except BlockingIOError:
                    break
            self.assertFalse(broker.handle(server, "A", {"operation": "read", "resource": "summary", "epoch": 1}))
            self.assertTrue(broker.stop_event.is_set())
            self.assertFalse(any(e["event"] == "release_committed" for e in broker.audit))
        finally:
            server.close()
            client.close()

    def test_external_stop_linearizes_after_a_commit_already_in_progress(self):
        broker = self.broker()
        entered, proceed = threading.Event(), threading.Event()
        setter_started, setter_done = threading.Event(), threading.Event()
        original_send = broker._send_locked
        def paused_send(*args):
            entered.set()
            if not proceed.wait(1):
                raise TimeoutError()
            return original_send(*args)
        broker._send_locked = paused_send
        server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        worker = threading.Thread(target=broker.handle, args=(server, "A", {"operation": "read", "resource": "summary", "epoch": 1}))
        def external_stop():
            setter_started.set()
            broker.stop_event.set()
            setter_done.set()
        stopper = threading.Thread(target=external_stop)
        worker.start()
        try:
            self.assertTrue(entered.wait(1))
            stopper.start()
            self.assertTrue(setter_started.wait(1))
            self.assertFalse(setter_done.wait(.02))
            proceed.set()
            worker.join(2)
            stopper.join(2)
            self.assertTrue(setter_done.is_set())
            self.assertEqual(json.loads(client.recv(65536))["decision"], "allow")
            self.assertTrue(broker.stop_event.is_set())
        finally:
            proceed.set()
            worker.join(2)
            if stopper.ident is not None:
                stopper.join(2)
            server.close()
            client.close()


SENSOR = "/home/pratz/guardianai-tools/unpacked/usr/bin/strace"


@unittest.skipUnless(sys.platform == "linux" and Path(SENSOR).exists(), "requires native Linux sensor")
class BrokerKernelTests(unittest.TestCase):
    def execute(self, permitted):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private = root / "private.txt"
            private.write_bytes(b"FAKE-BROKER-CANARY")
            source, output = root / "input", root / "output"
            source.mkdir()
            output.mkdir()
            code = """import os,socket,json,base64,time
from pathlib import Path
hidden=HOST_PRIVATE
out={}
for path in (hidden, '/proc/1/root'+hidden):
 try: out[path]=Path(path).read_text()
 except OSError: out[path]='blocked'
s=socket.socket(fileno=int(os.environ['GUARDIAN_BROKER_FD']))
out['fds']={}
for n in os.listdir('/proc/self/fd'):
 try: out['fds'][n]=os.readlink('/proc/self/fd/'+n)
 except OSError: pass
s.send(json.dumps({'operation':'read','resource':'summary','epoch':1}).encode())
try: out['broker']=json.loads(s.recv(65536))
except Exception: pass
Path('/output/result.json').write_text(json.dumps(out))
time.sleep(1)
Path('/output/late').write_text('late')
""".replace("HOST_PRIVATE", repr(str(private)))
            (source / "payload.py").write_text(code)
            broker = ReleaseBroker("Read summary", {"summary": private.read_bytes()},
                                   {"A": {"summary"}} if permitted else {}, lambda state: {"probability": .01})
            server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            stop = broker.stop_event
            worker = threading.Thread(target=broker.serve, args=(server, "A"))
            worker.start()
            try:
                result = supervise("Read authorized summary", source, ["/usr/bin/python3", "/workspace/payload.py"],
                                   output=output, evidence=root / "evidence", sensor=SENSOR,
                                   observer=lambda task, events: {"probability": .01},
                                   broker_channel=client, stop_event=stop, timeout=4)
            finally:
                client.close()
                worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(result["verdict"], "no_observed_violation" if permitted else "violation", result)
            self.assertEqual((output / "late").exists(), permitted)
            if permitted:
                data = json.loads((output / "result.json").read_text())
                self.assertEqual(data[str(private)], "blocked")
                self.assertEqual(data['/proc/1/root'+str(private)], "blocked")
                self.assertEqual(base64.b64decode(data["broker"]["content_base64"]), b"FAKE-BROKER-CANARY")
                self.assertEqual(sum(int(n) > 2 for n in data['fds']), 1)
            else:
                self.assertFalse(any(e["event"] == "release_committed" for e in broker.audit))

    def test_arbitrary_direct_read_is_blocked_but_authorized_release_succeeds(self):
        self.execute(True)

    def test_denied_release_stops_namespace_before_later_effect(self):
        self.execute(False)
