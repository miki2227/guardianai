"""Apply the frozen grounding diagnostic to raw messages, retaining baseline scores."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from social_experiment import observe_role_aware, parse
from social_summary import ROOT, RUNS


for name in RUNS:
    folder = ROOT / name
    state = json.loads((folder / "episode.json").read_text())
    for side, role in (("a", "sender"), ("b", "receiver")):
        destination = folder / ("observed-" + side + "-role-aware.json")
        if destination.exists():
            raise FileExistsError(destination)
        reply = parse((folder / (role + "-reply.txt")).read_text(), role)
        raw = reply["message" if side == "a" else "reply"]
        history = [] if side == "a" else [(folder / "delivered-a.txt").read_text()]
        result = observe_role_aware(state, raw, side, history)
        destination.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"run": name, "side": side, **result}), flush=True)
