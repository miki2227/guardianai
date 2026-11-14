"""Independently validate retained broker outcomes and raw capture hashes."""
import base64
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitor import summarize


ROOT = Path(__file__).resolve().parent / "broker-runs"
results = []
for version in ("comparison-v3", "live-release-v1"):
    base = ROOT / version
    summary = json.loads((base / "summary.json").read_text())
    for case in summary["cases"]:
        root = base / case["case"]
        allowed = case["case"] in {"allow", "path_replacement", "live_allow"}
        commits = [e for e in case["broker_audit"] if e["event"] == "release_committed"]
        assert len(commits) == (2 if allowed else 0)
        expected_hash = hashlib.sha256(b"SYNTHETIC-PROTECTED-SNAPSHOT").hexdigest()
        for worker in case["workers"]:
            path = root / worker["principal"] / "evidence"
            capture = summarize(path)
            assert capture["evidence_status"] == "recorded", (str(path), capture["problems"])
            runtime = json.loads((path / "runtime.json").read_text())
            assert runtime == worker["runtime"], path
            assert runtime["broker_channel"]
            assert worker["later_effect"] == (root / worker["principal"] / "output" / "later").exists() == allowed
            assert runtime["verdict"] == ("no_observed_violation" if allowed else "violation")
            if allowed:
                data = json.loads((root / worker["principal"] / "output" / "result.json").read_text())
                assert worker["output"] == data
                assert all(value == "blocked" for key, value in data.items() if key != "response")
                value = base64.b64decode(data["response"]["content_base64"], validate=True)
                assert hashlib.sha256(value).hexdigest() == expected_hash == data["response"]["sha256"]
                assert any(c["principal"] == worker["principal"] and c["resource_sha256"] == expected_hash for c in commits)
        results.append({"version": version, "case": case["case"], "workers": len(case["workers"]),
                        "release_commits": len(commits), "observer_source": case["observer_source"]})
result = {"verified_workers": sum(r["workers"] for r in results), "cases": results,
          "scope": "Capture hashes, recorded runtime decisions, protected-byte snapshot identity and expected effects verified; not completeness of telemetry or malicious-intent detection."}
(ROOT / "verified-summary.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
