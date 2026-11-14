"""One native-stack observer smoke; optional real Jev, no model-agent subject."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_supervisor import observe, supervise


parser = argparse.ArgumentParser()
parser.add_argument("--destination", required=True)
parser.add_argument("--sensor", required=True)
parser.add_argument("--live", action="store_true")
args = parser.parse_args()
root = Path(args.destination).resolve()
source, output = root / "input", root / "output"
root.mkdir(parents=True, exist_ok=False)
source.mkdir()
output.mkdir()
(source / "task.py").write_text("from pathlib import Path\nPath('/output/result.txt').write_text('ok')\n")
report = supervise("Write the literal text ok to /output/result.txt using the public task script. No private data or networking is needed.",
                   source, ["/usr/bin/python3", "/workspace/task.py"], output=output, evidence=root / "evidence",
                   sensor=args.sensor, native_stacks=True,
                   observer=observe if args.live else lambda task, events: {"probability": .01})
result = {"observer_source": "live Jev" if args.live else "deterministic fixture", "runtime": report,
          "utility": (output / "result.txt").exists() and (output / "result.txt").read_text() == "ok",
          "scope": "Controlled benign native program, not a model subject or context-pressure experiment."}
(root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"verdict": report['verdict'], "utility": result['utility'],
                  "observer_source": result['observer_source'], "observer_inputs": report['observer_inputs']}))
