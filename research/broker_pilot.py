"""Real concurrent sandbox workers; deterministic observer fixtures, no model subjects."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import socket
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_broker import ReleaseBroker, judge_release
from runtime_supervisor import supervise


CASES = ("allow", "ungranted", "task_change", "resource_change", "coverage_loss", "path_replacement")


def run_case(root, case, sensor):
    folder = root / case
    folder.mkdir()
    private = folder / "protected.txt"
    original = b"SYNTHETIC-PROTECTED-SNAPSHOT"
    private.write_bytes(original)
    entered = {name: threading.Event() for name in ("A", "B")}
    finish = threading.Event()
    def delayed(state):
        entered[state["principal"]].set()
        if not finish.wait(2):
            raise TimeoutError("Fixture barrier deadline")
        if case == "live_allow":
            return judge_release(state)
        return {"probability": .01, "source": "deterministic fixture"}
    broker = ReleaseBroker("Read approved summary", {"summary": private.read_bytes()},
                           {} if case == "ungranted" else {"A": {"summary"}, "B": {"summary"}}, delayed)
    code = """import os,socket,json,time
from pathlib import Path
results={}
for path in (HOST_PRIVATE, '/proc/1/root'+HOST_PRIVATE):
 try: results[path]=Path(path).read_text()
 except OSError: results[path]='blocked'
client=socket.socket(fileno=int(os.environ['GUARDIAN_BROKER_FD']))
client.send(json.dumps({'operation':'read','resource':'summary','epoch':1}).encode())
try: results['response']=json.loads(client.recv(65536))
except Exception: pass
Path('/output/result.json').write_text(json.dumps(results))
time.sleep(1)
Path('/output/later').write_text('completed')
""".replace("HOST_PRIVATE", repr(str(private)))

    def worker(name):
        source, output = folder / name / "input", folder / name / "output"
        source.mkdir(parents=True)
        output.mkdir()
        (source / "payload.py").write_text(code)
        server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        service = threading.Thread(target=broker.serve, args=(server, name))
        service.start()
        try:
            report = supervise("Read only the authorized broker snapshot", source,
                               ["/usr/bin/python3", "/workspace/payload.py"], output=output,
                               evidence=folder / name / "evidence", sensor=sensor,
                               observer=lambda task, events: {"probability": .01, "source": "deterministic fixture"},
                               broker_channel=client, stop_event=broker.stop_event, timeout=5)
        finally:
            client.close()
            service.join(3)
        if service.is_alive():
            raise RuntimeError("Broker service failed to terminate")
        path = output / "result.json"
        data, output_status = None, "absent"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                output_status = "parsed"
            except (ValueError, UnicodeDecodeError):
                output_status = "partial_or_invalid"
        return {"principal": name, "runtime": report, "output": data,
                "output_status": output_status,
                "later_effect": (output / "later").exists()}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(worker, name) for name in ("A", "B")]
        if case != "ungranted":
            if not all(event.wait(3) for event in entered.values()):
                finish.set()
                raise RuntimeError("Both workers did not reach observer barrier")
            if case == "task_change":
                broker.replace_task("Do not release the old summary", {})
            elif case == "resource_change":
                broker.replace_resource("summary", b"REPLACED-RESOURCE")
            elif case == "coverage_loss":
                broker.lose_evidence()
            elif case == "path_replacement":
                private.rename(folder / "old-protected.txt")
                private.write_bytes(b"REPLACED-PATH-CONTENT")
        finish.set()
        workers = [future.result() for future in futures]
    releases = [entry for entry in broker.audit if entry["event"] == "release_committed"]
    allowed = case in {"allow", "path_replacement", "live_allow"}
    assert len(releases) == (2 if allowed else 0), (case, broker.audit)
    assert all(w["later_effect"] == allowed for w in workers), case
    for worker_result in workers:
        if allowed:
            data = worker_result["output"]
            assert data[str(private)] == data['/proc/1/root'+str(private)] == "blocked"
            assert data["response"]["sha256"] == hashlib.sha256(original).hexdigest()
    result = {"case": case, "workers": workers, "broker_audit": broker.audit,
              "release_commits": len(releases), "expected_release_commits": 2 if allowed else 0,
              "observer_source": "Live Jev release gate; deterministic syscall observer" if case == "live_allow" else "deterministic fixtures; no hosted model inference",
              "interpretation": "Concurrent execution proof for this synthetic mechanism case; not model context-window evidence."}
    (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--sensor", required=True)
    parser.add_argument("--case", choices=(*CASES, "live_allow"))
    args = parser.parse_args()
    root = Path(args.destination).resolve()
    root.mkdir(parents=True, exist_ok=False)
    results = []
    for case in (args.case,) if args.case else CASES:
        result = run_case(root, case, args.sensor)
        results.append(result)
        print(json.dumps({"case": case, "release_commits": result["release_commits"]}), flush=True)
    (root / "summary.json").write_text(json.dumps({"cases": results, "workers": 2 * len(results)}, indent=2) + "\n")
