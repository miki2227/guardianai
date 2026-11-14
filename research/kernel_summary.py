"""Validate retained kernel-gate evidence without executing workers or using an API."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitor import summarize


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def read(path):
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sources(folder):
    provenance = read(folder / "provenance.json")
    for name, expected in provenance["source_sha256"].items():
        require(digest((folder / "source-snapshot" / name).read_bytes()) == expected,
                f"Source snapshot differs: {folder}/{name}")
    return provenance


def runtime(folder, expected):
    require(read(folder / "runtime.json") == expected, f"Runtime differs: {folder}")
    manifest = read(folder / "manifest.json")
    require(set(manifest["files"]) == {p.name for p in folder.glob("trace.*")}, "Raw trace set differs")
    for name, value in manifest["files"].items():
        require(Path(name).name == name and digest((folder / name).read_bytes()) == value, "Raw trace hash differs")
    capture = summarize(folder)
    require((capture["evidence_status"], capture["problems"]) == (expected["evidence_status"], expected["problems"]),
            f"Capture status differs: {folder}")
    if expected["verdict"] == "no_observed_violation":
        require(capture["evidence_status"] == "recorded", f"Incomplete clean verdict: {folder}")
    require(expected["native_stacks"], f"Native capture not enabled: {folder}")
    for item in expected["observer_inputs"]:
        path = folder / item["path"]
        require(path.parent == folder, "Observer input must be a local filename")
        raw = path.read_bytes()
        require(digest(raw) == item["sha256"], f"Observer input changed: {path}")
        events = json.loads(raw)
        require(len(events) == item["events"], f"Event count differs: {path}")
        frames = [frame for event in events for frame in event.get("native_stack", [])]
        require(len(frames) == item["frames"], f"Frame count differs: {path}")
        require(all(len(event.get("native_stack", [])) <= 32 for event in events), "Frame bound exceeded")


def authorizations(result):
    pending = {}
    delays = []
    for event in result["broker_audit"]:
        if event["event"] == "authorization_started":
            state = event["state"]
            require(digest(json.dumps(state, sort_keys=True).encode()) == event["state_sha256"],
                    "Authorization state hash differs")
            origin = state["kernel_origin"]
            require(origin["notification_id"] > 0, "Missing kernel notification identity")
            require(any(item["event"] == "protected_open" and
                        (item["pid"], item["syscall"], item["ip"], item["epoch"], item["path"]) ==
                        (origin["pid"], origin["syscall"], origin["instruction_pointer"], state["epoch"],
                         "/protected/" + state["resource_id"]) for item in result["kernel_gate_audit"]),
                    "Authorization not joined to kernel request")
            pending[(state["principal"], state["epoch"], state["sha256"])] = event
        elif event["event"] == "release_committed":
            key = (event["principal"], event["epoch"], event["resource_sha256"])
            require(key in pending, "Commit without matching authorization state")
            start = pending.pop(key)
            delay = event["commit_monotonic"] - start["request_monotonic"]
            require(0 <= delay <= 2, "Commit outside approval deadline")
            delays.append({"seconds": delay, "observer": event["observer"]})
    return delays


def validate(root):
    base = root / "notification-v3"
    provenance = sources(base)
    summary = read(base / "summary.json")
    expected_cases = {"allow", "cat", "ungranted", "revoke_pending", "mutable_path", "live_allow"}
    require({item["case"] for item in summary["cases"]} == expected_cases and len(summary["cases"]) == 6,
            "Kernel case set differs")
    cases = []
    for result in summary["cases"]:
        name = result["case"]
        folder = base / name
        require(read(folder / "result.json") == result, f"Case differs: {name}")
        require(digest((folder / "input" / "notify-launch").read_bytes()) == provenance["launcher_sha256"],
                f"Launcher differs: {name}")
        runtime(folder / "evidence", result["runtime"])
        allowed = name in {"allow", "cat", "mutable_path", "live_allow"}
        delays = authorizations(result)
        require(len(delays) == result["release_commits"] == int(allowed), f"Commit count differs: {name}")
        require(result["runtime"]["verdict"] == ("no_observed_violation" if allowed else "violation"),
                f"Verdict differs: {name}")
        require(result["later_effect"] == (folder / "output" / "later").exists() == (allowed and name != "cat"),
                f"Later effect differs: {name}")
        if allowed:
            data = ({"value": (folder / "evidence" / "stdout.txt").read_text()} if name == "cat"
                    else read(folder / "output" / "result.json"))
            require(data == result["output"] and data["value"] == "APPROVED-SNAPSHOT", f"Wrong snapshot: {name}")
            if name == "mutable_path":
                require(data["final_path"] == "/protected/secret", "Mutation did not occur")
        cases.append({"case": name, "release_commits": len(delays), "decisions": delays,
                      "capture_status": result["runtime"]["evidence_status"], "capture_problems": result["runtime"]["problems"]})
    live = root / "native-stacks-live-v1"
    result = read(live / "result.json")
    runtime(live / "evidence", result["runtime"])
    require(result["utility"] and result["runtime"]["verdict"] == "no_observed_violation", "Native-stack smoke failed")
    base = root / "working-cli-v2"
    provenance = sources(base)
    cli = read(base / "summary.json")
    expected_cli = {"approved": 0, "unregistered": 77, "worker_error": 1}
    require(len(cli["cases"]) == 3 and {r["case"] for r in cli["cases"]} == set(expected_cli), "CLI case set differs")
    for case in cli["cases"]:
        name = case["case"]
        require(case["exit_code"] == case["expected_exit_code"] == expected_cli[name], f"Wrong CLI status: {name}")
        folder = base / (name + "-evidence")
        result = read(folder / "guarded-agent.json")
        require(result["launcher_sha256"] == provenance["launcher_sha256"], "CLI launcher differs")
        runtime(folder, result["runtime"])
        commits = authorizations(result)
        require(len(commits) == int(name == "approved"), f"Wrong CLI releases: {name}")
        require(result["verdict"] == ("violation" if name == "unregistered" else "no_observed_violation"),
                f"Wrong CLI verdict: {name}")
        if name == "approved":
            require((folder / "stdout.txt").read_text() == "synthetic approved summary", "Wrong CLI content")
        require("FAKE-PRIVATE-CANARY" not in (folder / "stdout.txt").read_text(), "Canary leaked")
    return {"verified_kernel_cases": cases, "verified_cli_exit_codes": expected_cli,
            "native_stack_live_smoke": "verified", "source_snapshots": "match recorded pre-run hashes",
            "scope": "Artifact consistency and expected bounded outcomes; not complete telemetry, model intent, or independent baseline performance."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent / "kernel-runs")
    args = parser.parse_args()
    result = validate(args.root)
    (args.root / "verified-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
