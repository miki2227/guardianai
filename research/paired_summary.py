"""Summarize completed real-agent episodes without inventing missing outcomes."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitor import sha256
from paired_experiment import parse_subject


root = Path(__file__).resolve().parent / "paired-runs"
rows = []
for path in sorted(root.glob("*/outcome.json")):
    directory = path.parent
    episode = json.loads((directory / "episode.json").read_text())
    outcome = json.loads(path.read_text())
    sender = parse_subject((directory / "sender-reply.txt").read_text(), "sender")
    delivered = (directory / "delivered-message.txt").read_text()
    relay = json.loads((directory / "relay.json").read_text())
    identity = sender["message"] == delivered and relay["message_sha256"] == sha256(directory / "delivered-message.txt")
    if not identity:
        raise ValueError("Delivered-message identity check failed: " + directory.name)
    row = {"run": directory.name, "seed": episode["seed"], "condition": episode["condition"],
           "sender_disclosure": outcome["sender_disclosure"],
           "receiver_disclosure": outcome["receiver_disclosure"],
           "structured_facts_correct": outcome["structured_facts_correct"],
           "message_identity_verified": identity,
           "observer_status": outcome["observer"]["status"],
           "outcome_sha256": sha256(path)}
    rows.append(row)
summary = {"evidence": "actual Grok subjects and live Jev observations; no model training",
           "completed_episodes": len(rows), "episodes": rows,
           "scope": "Small handoff pilot; no covert convention, longitudinal effect, or universal safety is established."}
(root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
