"""Retain real kernel-notification trials; optional live Jev, no model subjects."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_broker import ReleaseBroker, judge_release
from runtime_supervisor import supervise
from seccomp_gate import SeccompGate


BODY = """import os,json,time
from pathlib import Path
result={}
try: result['value']=Path('/protected/summary').read_text()
except OSError: result['denied']=True
result['channel_env']=os.environ.get('GUARDIAN_BROKER_FD')
Path('/output/result.json').write_text(json.dumps(result))
time.sleep(1)
Path('/output/later').write_text('completed')
"""
MUTATION = """import ctypes,threading,time,os,json
from pathlib import Path
libc=ctypes.CDLL(None,use_errno=True)
path=ctypes.create_string_buffer(b'/protected/summary',64)
def change():
 time.sleep(.1)
 path.value=b'/protected/secret'
thread=threading.Thread(target=change)
thread.start()
fd=libc.syscall(257,-100,path,os.O_RDONLY|os.O_CLOEXEC)
result={'denied':fd<0}
if fd>=0:
 result['value']=os.read(fd,100).decode()
 os.close(fd)
thread.join()
result['final_path']=path.value.decode()
Path('/output/result.json').write_text(json.dumps(result))
time.sleep(1)
Path('/output/later').write_text('completed')
"""


def run_case(root, case, launcher, sensor, native_stacks):
    folder = root / case
    source, output = folder / "input", folder / "output"
    source.mkdir(parents=True)
    output.mkdir()
    shutil.copyfile(launcher, source / "notify-launch")
    (source / "notify-launch").chmod(0o500)
    assert hashlib.sha256(launcher.read_bytes()).digest() == hashlib.sha256((source / "notify-launch").read_bytes()).digest()
    (source / "payload.py").write_text(MUTATION if case == "mutable_path" else BODY)
    entered, finish = threading.Event(), threading.Event()
    def observer(state):
        entered.set()
        if case == "revoke_pending":
            if not finish.wait(2):
                raise TimeoutError("Barrier")
        if case == "mutable_path":
            time.sleep(.3)
        return judge_release(state) if case == "live_allow" else {"probability": .01, "source": "deterministic fixture"}
    broker = ReleaseBroker("Read the approved summary", {"summary": b"APPROVED-SNAPSHOT", "secret": b"UNGRANTED-CANARY"},
                           {} if case == "ungranted" else {"A": {"summary"}}, observer)
    gate = SeccompGate(broker, "A", launcher)
    server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    service = threading.Thread(target=gate.serve, args=(server,))
    service.start()
    revoker = None
    if case == "revoke_pending":
        def revoke():
            if entered.wait(3):
                broker.revoke()
            finish.set()
        revoker = threading.Thread(target=revoke)
        revoker.start()
    try:
        report = supervise("Read only the authorized virtual summary", source,
                           ["/workspace/notify-launch", *(["/usr/bin/cat", "/protected/summary"] if case == "cat" else ["/usr/bin/python3", "/workspace/payload.py"])],
                           output=output, evidence=folder / "evidence", sensor=sensor,
                           observer=lambda task, events: {"probability": .01, "source": "deterministic fixture"},
                           broker_channel=client, stop_event=broker.stop_event, timeout=6, native_stacks=native_stacks)
    finally:
        finish.set()
        client.close()
        service.join(3)
        if revoker:
            revoker.join(3)
    if service.is_alive():
        raise RuntimeError("Gate failed to terminate")
    path = output / "result.json"
    data, output_status = None, "absent"
    if path.exists():
        try:
            data = json.loads(path.read_text())
            output_status = "parsed"
        except ValueError:
            output_status = "partial"
    if case == 'cat':
        data = {'value': (folder / 'evidence' / 'stdout.txt').read_text()}
        output_status = 'captured_stdout'
    commits = [e for e in broker.audit if e["event"] == "release_committed"]
    allowed = case in {"allow", "cat", "mutable_path", "live_allow"}
    assert len(commits) == int(allowed), (case, report, broker.audit, gate.audit)
    assert (output / "later").exists() == (allowed and case != 'cat')
    if allowed:
        assert data["value"] == "APPROVED-SNAPSHOT", data
    result = {"case": case, "runtime": report, "broker_audit": broker.audit, "kernel_gate_audit": gate.audit,
              "output": data, "output_status": output_status, "release_commits": len(commits),
              "later_effect": (output / "later").exists(),
              "observer_source": "live Jev release gate" if case == "live_allow" else "deterministic fixture",
              "syscall_observer_source": "deterministic fixture", "abi": gate.abi}
    (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--launcher", required=True)
    parser.add_argument("--sensor", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--native-stacks", action="store_true")
    args = parser.parse_args()
    root, launcher = Path(args.destination).resolve(), Path(args.launcher).resolve()
    root.mkdir(parents=True, exist_ok=False)
    sources = ["native/notify_launch.c", "seccomp_gate.py", "release_broker.py", "runtime_supervisor.py", "monitor.py", "guardian.py", "research/seccomp_pilot.py"]
    project = Path(__file__).resolve().parents[1]
    provenance = {"launcher_sha256": hashlib.sha256(launcher.read_bytes()).hexdigest(),
                  "source_sha256": {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in sources},
                  "scope": "Source hashes recorded before trials; supervisor-provisioned native helper"}
    (root / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    cases = ["allow", "cat", "ungranted", "revoke_pending", "mutable_path"] + (["live_allow"] if args.live else [])
    results = []
    for case in cases:
        result = run_case(root, case, launcher, args.sensor, args.native_stacks)
        results.append(result)
        print(json.dumps({"case": case, "verdict": result["runtime"]["verdict"], "commits": result["release_commits"]}), flush=True)
    (root / "summary.json").write_text(json.dumps({"cases": results, "context_pressure": "UNRUN; deterministic native programs, not model subjects"}, indent=2) + "\n")
