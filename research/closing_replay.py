"""Prepare matched closing prompts and verify their exposed knowledge context."""
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from convention import context_match


root = Path(__file__).resolve().parent
base = root / "closing-runs"
base.mkdir(exist_ok=False)
schedule = [(run, mode) for run in ("fixed-s105", "context-s105", "fixed-s106", "context-s106")
            for mode in ("raw", "edited")]
random.Random(1307).shuffle(schedule)
order = []
for run, mode in schedule:
    source = root / "social-runs" / run
    original = json.loads((source / "closing-prompt.json").read_text())
    value = dict(original)
    if mode == "raw":
        value["incoming_message"] = json.loads((source / "receiver-reply.txt").read_text())["reply"]
    match = context_match(original, value)
    assert match["matched"], (run, mode)
    name = run + "-" + mode
    folder = base / name
    folder.mkdir()
    for filename, content in (("closing-input.json", value), ("context-check.json", match)):
        (folder / filename).write_text(json.dumps(content, indent=2) + "\n")
    order.append(name)
(base / "schedule.json").write_text(json.dumps({"shuffle_seed": 1307, "order": order}, indent=2) + "\n")
print(json.dumps({"prepared": len(order), "order": order}))
