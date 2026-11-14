"""Re-analyze retained raw captures without rerunning the workloads or preflight."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import monitor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    source, destination = Path(args.source), Path(args.destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "config.json").write_text(json.dumps({
        "evidence": "new live post-execution judgments on retained real syscall traces; preflight retained",
        "parent": source.name, "parent_ledger_sha256": monitor.sha256(source / "sessions.jsonl"),
        "parser_sha256": monitor.sha256(Path(monitor.__file__)),
    }, indent=2) + "\n")
    with (destination / "sessions.jsonl").open("w") as ledger:
        for line in (source / "sessions.jsonl").read_text().splitlines():
            row = json.loads(line)
            capture = source / row["session"] / "capture"
            summary = monitor.summarize(capture)
            case = destination / row["session"]
            case.mkdir()
            (case / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
            for view in ("kernel", "joined"):
                row["views"][view] = monitor.judge(row["task"], row["argv"], summary, view=view)
            # This path is an explicit prohibition present only in the relevant task.
            forbidden = []
            if row["family"] != "auxiliary_authorized":
                forbidden = ["/workspace/" + row["task"].split("Do not read ", 1)[1].split(";", 1)[0]]
            row.update(evidence_status=summary["evidence_status"],
                       rule=monitor.rule_verdict(summary, forbidden_reads=forbidden),
                       effects_only_rule=monitor.rule_verdict(summary, successful_only=True, forbidden_reads=forbidden),
                       capture_reference="../" + source.name + "/" + row["session"] + "/capture")
            ledger.write(json.dumps(row) + "\n"); ledger.flush()
            print(row["session"], summary["evidence_status"], row["views"], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
