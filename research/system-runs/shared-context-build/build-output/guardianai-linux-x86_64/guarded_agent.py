"""Run an ordinary Linux worker with Jev oversight and kernel-gated protected reads."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys
import threading

from guardian import sandbox_argv
from release_broker import MAX_RESOURCE_BYTES, ReleaseBroker
from runtime_supervisor import supervise


def run(task, workspace, command, *, output, evidence, resources, sensor="strace"):
    if sys.platform != "linux":
        raise RuntimeError("Run inside Linux or WSL2")
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise RuntimeError("Trusted supervisor requires TYPESAFE_API_KEY")
    # Validate containment before loading resources or calling the provider.
    sandbox_argv(workspace, command, output=output)
    launcher = Path(__file__).resolve().parent / "native" / "notify-launch"
    if not launcher.is_file():
        raise RuntimeError("Build native/notify-launch using the documented gcc command")
    public_roots = [Path(workspace).resolve(), Path(output).resolve()]
    public_roots += [Path(name).resolve() for name in ("/usr", "/bin", "/lib", "/lib64") if Path(name).exists()]
    snapshots = load_resources(resources, public_roots, launcher)
    broker = ReleaseBroker(task, snapshots, {"worker": set(snapshots)})
    return run_worker(task, workspace, command, output=output, evidence=evidence,
                      sensor=sensor, broker=broker, principal="worker", launcher=launcher)


def load_resources(resources, public_roots, launcher):
    snapshots = {}
    for name, filename in resources.items():
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", name):
            raise ValueError("Use a single-component protected resource identifier")
        path = Path(filename).resolve(strict=True)
        if path == launcher.resolve() or any(path.is_relative_to(root) for root in public_roots):
            raise ValueError("Protected resources must be outside public/runtime mounts")
        if not path.is_file():
            raise ValueError("Protected resource must be a regular file")
        with path.open("rb") as stream:
            content = stream.read(MAX_RESOURCE_BYTES + 1)
        if len(content) > MAX_RESOURCE_BYTES:
            raise ValueError("Protected snapshot exceeds 32768 bytes")
        snapshots[name] = content
    return snapshots


def run_worker(task, workspace, command, *, output, evidence, sensor, broker, principal, launcher, observer=None):
    from seccomp_gate import SeccompGate
    gate = SeccompGate(broker, principal, launcher)
    server, client = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    service = threading.Thread(target=gate.serve, args=(server,))
    service.start()
    try:
        observe_options = {} if observer is None else {"observer": observer}
        report = supervise(task, workspace, command, output=output, evidence=evidence,
                           sensor=sensor, broker_channel=client, stop_event=broker.stop_event,
                           native_stacks=True, trusted_launcher=launcher, **observe_options)
    except BaseException:
        broker.lose_evidence()
        raise
    finally:
        client.close()
        # The pinned provider has a 20-second HTTP deadline. Pending inference can
        # delay supervisor exit even after the namespace has already been killed.
        service.join(21)
    final_verdict = report["verdict"]
    if service.is_alive():
        broker.lose_evidence()
        final_verdict = "abstain"
    if any(event["event"] == "gate_fault" for event in gate.audit):
        final_verdict = "abstain"
    with broker.lock:
        audit = copy.deepcopy(broker.audit)
        resource_hashes = {name: hashlib.sha256(broker.resources[name]).hexdigest()
                           for name in broker.grants.get(principal, ())}
    result = {"verdict": final_verdict, "task": task, "principal": principal, "runtime": report, "broker_audit": audit, "kernel_gate_audit": gate.audit,
              "launcher_sha256": hashlib.sha256(launcher.read_bytes()).hexdigest(),
              "resources": resource_hashes,
              "scope": "Protected snapshots only; no guarantee for private copies already exposed in public mounts or previously released data."}
    (Path(evidence) / "guarded-agent.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("task", "workspace", "output", "evidence"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--sensor", default="strace")
    parser.add_argument("--resource", action="append", default=[], metavar="NAME=HOST_FILE")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("A worker command is required after --")
    resources = {}
    for item in args.resource:
        name, separator, filename = item.partition("=")
        if not separator or not filename or name in resources:
            parser.error("Each resource must be a unique NAME=HOST_FILE")
        resources[name] = filename
    try:
        result = run(args.task, args.workspace, command, output=args.output, evidence=args.evidence,
                     resources=resources, sensor=args.sensor)
        verdict = result["verdict"]
        print(json.dumps({"verdict": verdict, "evidence": str(Path(args.evidence).resolve())}))
        if verdict == "no_observed_violation":
            status = result["runtime"]["returncode"]
            return status if status >= 0 else 128 - status
        return 77 if verdict == "violation" else 78
    except Exception as error:
        print(json.dumps({"verdict": "abstain", "reason": type(error).__name__}))
        return 78


if __name__ == "__main__":
    sys.exit(main())
