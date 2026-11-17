"""Record actual delivered text through a WSL2-contained controller relay.

This traces the relay, not the hosted model's inference or T3 tool runtime.
"""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

from monitor import capture, sha256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--sensor", required=True)
    parser.add_argument("--direction", choices=["message", "a", "b"], default="message")
    args = parser.parse_args()
    run = Path(args.run)
    name = "delivered-message.txt" if args.direction == "message" else "delivered-" + args.direction + ".txt"
    capture_name = "relay-capture" if args.direction == "message" else "relay-" + args.direction + "-capture"
    metadata_name = "relay.json" if args.direction == "message" else "relay-" + args.direction + ".json"
    message = (run / name).read_bytes()
    with tempfile.TemporaryDirectory(prefix="guardian-pair-relay-") as temporary:
        root = Path(temporary)
        workspace, output = root / "input", root / "output"
        workspace.mkdir(); output.mkdir()
        (workspace / "message.txt").write_bytes(message)
        code = "from pathlib import Path; Path('/output/delivered.txt').write_bytes(Path('/workspace/message.txt').read_bytes())"
        summary = capture(workspace, ["python3", "-c", code], output=output,
                          evidence=root / "capture", sensor=args.sensor)
        delivered = (output / "delivered.txt").read_bytes()
        if delivered != message or summary["evidence_status"] != "recorded":
            raise RuntimeError("Message relay evidence failed validation")
        shutil.copytree(root / "capture", run / capture_name)
        result = {"scope": "contained controller relay, not model runtime", "byte_identity_verified": True,
                  "message_sha256": sha256(workspace / "message.txt"),
                  "delivered_sha256": sha256(output / "delivered.txt"),
                  "evidence_status": summary["evidence_status"]}
        (run / metadata_name).write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))


if __name__ == "__main__":
    main()
