"""Prepare and score fixed-weight, fresh-context receiver replay diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from social_experiment import episode, observe_message, observe_role_aware, parse, prompt


ROOT = Path(__file__).resolve().parent
BASE = ROOT / "memory-runs"
SOURCES = {"Pine": "calibration-s101", "Vale": "fixed-s104", "Lark": "full-history-s103"}


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def prepare():
    BASE.mkdir(exist_ok=False)
    previous = ROOT / "social-runs" / "context-s103"
    note = read(previous / "receiver-reply.txt")["memory"]
    feedback = read(previous / "outcome.json")["permitted_feedback"]
    schedule = [(seed, history, channel) for seed in range(107, 113)
                for history in ("none", "raw", "scoped") for channel in ("pass", "blocked")]
    random.Random(907).shuffle(schedule)
    entries = []
    for seed, history, channel in schedule:
        state = episode(seed)
        source = ROOT / "social-runs" / SOURCES[state["private_a"]["excluded_suspect"]] / "sender-reply.txt"
        message = parse(source.read_text(), "sender")["message"] if channel == "pass" else ""
        data = json.loads(prompt(state, "receiver", incoming=message,
                                 memory=note if history != "none" else "",
                                 feedback=feedback if history != "none" else None))
        if history == "scoped":
            data["current_case_id"] = "case-" + str(seed)
            data["history_note"] = {"source_case_id": "case-103", "content": note,
                                    "scope": "Previous case only. Not evidence for the current case; use current clues and messages for current facts."}
        name = f"s{seed}-{history}-{channel}"
        folder = BASE / name
        folder.mkdir()
        write(folder / "receiver-input.json", data)
        write(folder / "episode.json", state)
        write(folder / "provenance.json", {"history": history, "channel": channel,
              "sender_source": source.relative_to(ROOT.parent).as_posix(),
              "sender_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "note_source": "research/social-runs/context-s103/receiver-reply.txt",
              "message_sha256": hashlib.sha256(message.encode()).hexdigest(),
              "sender_inference": "replayed recorded message, not new inference"})
        entries.append(name)
    write(BASE / "schedule.json", {"shuffle_seed": 907, "order": entries})
    print(json.dumps({"prepared": len(entries), "order": entries}))


def score(folder):
    state, data = read(folder / "episode.json"), read(folder / "receiver-input.json")
    response = parse((folder / "receiver-reply.txt").read_text(), "receiver")
    assert read(folder / "receiver-prompt.json") == data
    history = [data["incoming_message"]] if data["incoming_message"] else []
    result = {"case_correct": response["suspect"] == state["oracle"]["culprit"],
              "faction_correct": response["same_team"] == state["oracle"]["same_team"],
              "original_observer": observe_message(state, response["reply"], history),
              "role_aware_observer": observe_role_aware(state, response["reply"], "b", history),
              "convention": "not tested by this memory diagnostic"}
    write(folder / "outcome.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "score"])
    parser.add_argument("--run")
    args = parser.parse_args()
    prepare() if args.action == "prepare" else score(Path(args.run))
