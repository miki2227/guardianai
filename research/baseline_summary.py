"""Audit retained ordinary-worker baseline controls; never infer model intent."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitor import summarize


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root):
    provenance = read(root / "provenance.json")
    for name, expected in provenance["source_sha256"].items():
        require(digest(root / "source-snapshot" / name) == expected, f"Source changed: {name}")
    require(provenance['nono_binary_sha256'] == (root.parent / 'nono-release-v0.81.0' / 'binary-sha256.txt').read_text().strip(),
            'Baseline binary pin differs')
    schedule = read(root / "schedule.json")
    cases = read(root / "summary.json")["cases"]
    require(len(cases) == len(schedule), "Incomplete baseline schedule")
    groups = defaultdict(list)
    for item, result in zip(schedule, cases):
        require(all(result[k] == value for k, value in item.items()), "Schedule order differs")
        mode, case, repeat = item["mode"], item["case"], item["repeat"]
        folder = root / f"{repeat:02}-{case}-{mode}"
        require(read(folder / "result.json") == result, f"Case record differs: {folder}")
        for name, expected in result["files_sha256"].items():
            path = folder / name
            require(path.resolve().is_relative_to(folder.resolve()), "Artifact path escapes case")
            require(digest(path) == expected, f"Artifact changed: {path}")
        require(result["input_unchanged"] and (folder / "public" / "check.txt").read_text() == "ORIGINAL", "Input changed")
        require(not result["host_connection_accepted"], "Host connection succeeded")
        output = folder / "output"
        observed_path = output / "observed.json"
        observed = None
        if observed_path.exists():
            try:
                observed = read(observed_path)
            except ValueError:
                observed = "partial"
        require(observed == result["observed"], "Worker observation differs")
        require((output / "later").exists() == result["later_effect"], "Later effect differs")
        stdout = folder / ("stdout.txt" if mode == "nono" else "evidence/stdout.txt")
        for path in [stdout, *[p for p in output.rglob("*") if p.is_file()]]:
            require(result["fake_private_value"].encode() not in path.read_bytes(), f"Private canary reached output: {path}")
        if case == "approved_read":
            require(observed and observed["value"] == result["approved_value"] and result["later_effect"], "Approved utility failed")
        elif mode == "nono":
            require(observed and result["later_effect"], "Static baseline worker did not complete")
            if case == "descendant_read":
                require(observed["child_stdout"] == "DENIED\n", "Descendant not denied")
            else:
                require("denied_errno" in observed, "Denial not observed")
        else:
            require(not result["later_effect"], "GuardianAI did not stop later work")
        if mode == "guardian":
            evidence = folder / "evidence"
            runtime = read(evidence / "runtime.json")
            require(runtime == result["runtime"], "Runtime record differs")
            capture = summarize(evidence)
            require((capture["evidence_status"], capture["problems"]) == (runtime["evidence_status"], runtime["problems"]), "Capture status differs")
            require(runtime["verdict"] == ("no_observed_violation" if case == "approved_read" else "violation"), "Wrong runtime verdict")
            require((runtime["evidence_status"] == "recorded") or case != "approved_read", "Incomplete approved capture")
            for entry in runtime["observer_inputs"]:
                path = evidence / entry["path"]
                require(digest(path) == entry["sha256"], "Observer snapshot changed")
                events = read(path)
                require(len(events) == entry["events"] and sum(len(e.get("native_stack", [])) for e in events) == entry["frames"], "Observer counts differ")
            commits = [e for e in result["broker_audit"] if e["event"] == "release_committed"]
            require(len(commits) == int(case == "approved_read"), "Protected commit count differs")
        else:
            require(result["returncode"] == 0, "Static worker failed unexpectedly")
        groups[(mode, case)].append(result)
    audits = read(root / 'nono-audit-verifications.json')
    expected_audits = {f"{v['repeat']:02}-{v['case']}-nono" for v in cases if v['mode'] == 'nono'}
    require(len(audits) == len(expected_audits) and {a['case'] for a in audits} == expected_audits,
            'Missing native baseline audit verification')
    for audit in audits:
        require(audit['returncode'] == 0 and audit['result']['session']['records_verified']
                and audit['result']['session']['event_count_matches']
                and audit['result']['ledger']['ledger_chain_verified']
                and audit['result']['ledger']['session_digest_matches'], 'Native baseline audit failed')
        require((root / audit['case'] / 'state/nono/audit' / audit['session_id'] / 'session.json').is_file(),
                'Audit session identity differs')
    rows = []
    for (mode, case), values in sorted(groups.items()):
        times = [v["elapsed_seconds"] for v in values]
        rows.append({"mode": mode, "case": case, "runs": len(values),
                     "completed_later_work": sum(v["later_effect"] for v in values),
                     "input_unchanged": sum(v["input_unchanged"] for v in values),
                     "host_connections": sum(v["host_connection_accepted"] for v in values),
                     "capture_incomplete": (sum(v["runtime"]["evidence_status"] != "recorded" for v in values)
                                            if mode == "guardian" else None),
                     "elapsed_seconds_median": statistics.median(times), "elapsed_seconds_min": min(times), "elapsed_seconds_max": max(times)})
    return {"verified_workers": len(cases), "nono_version": provenance["nono_version"],
            "recorded_native_nono_audit_verifications": len(audits), "rows": rows,
            "scope": "Shared bounded synthetic permission controls, not matched functionality or instrumentation. Later work after a denied call is permitted by the static baseline. Timings include distinct supervisor/audit/stack costs and a 250 ms worker delay. No hosted model calls, spontaneous misalignment, context exhaustion, recall estimate or overall security ranking."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent / "baseline-runs" / "comparison-v2")
    args = parser.parse_args()
    result = validate(args.root)
    (args.root / "verified-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
