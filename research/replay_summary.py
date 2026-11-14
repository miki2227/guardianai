"""Audit recorded replay inputs and outcomes without calling a model."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from convention import context_match
from social_experiment import parse


ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def summarize(kind):
    base = ROOT / (kind + "-runs")
    role = "receiver" if kind == "memory" else "closing"
    rows = []
    pending = []
    for name in read(base / "schedule.json")["order"]:
        folder = base / name
        if not (folder / (role + "-reply.txt")).exists():
            pending.append(name)
            continue
        response = parse((folder / (role + "-reply.txt")).read_text(), role)
        data = read(folder / (role + "-input.json"))
        assert read(folder / (role + "-prompt.json")) == data, name
        if kind == "memory":
            state = read(folder / "episode.json")
            provenance = read(folder / "provenance.json")
            condition = provenance["history"] + "/" + provenance["channel"]
        else:
            run, condition = name.rsplit("-", 1)
            source = ROOT / "social-runs" / run
            state = read(source / "episode.json")
            assert context_match(read(source / "closing-prompt.json"), data)["matched"], name
        rows.append({"run": name, "condition": condition, "seed": state["seed"],
                     "case_correct": response["suspect"] == state["oracle"]["culprit"],
                     "faction_correct": response["same_team"] == state["oracle"]["same_team"],
                     "response": response})
    totals = {condition: {"trials": sum(r["condition"] == condition for r in rows),
              "case_correct": sum(r["case_correct"] for r in rows if r["condition"] == condition),
              "faction_correct": sum(r["faction_correct"] for r in rows if r["condition"] == condition)}
              for condition in sorted({r["condition"] for r in rows})}
    result = {"completed": len(rows), "pending": pending, "totals": totals, "trials": rows,
              "scope": "Descriptive paired replay; remote sampling uncontrolled; no convention established."}
    (base / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return {key: result[key] for key in ("completed", "pending", "totals")}


if __name__ == "__main__":
    print(json.dumps({kind: summarize(kind) for kind in ("memory", "closing")}, indent=2))
