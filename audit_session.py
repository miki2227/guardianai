"""Run the Jev preflight and a retrospective syscall audit in WSL2/Linux."""
import argparse
import json
from pathlib import Path
import sys

from guardian import assess
from monitor import capture, judge, rule_verdict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--sensor", default="strace")
    parser.add_argument("--audit-forbidden-read", action="append", default=[],
                        help="sandbox path: detect access retrospectively; not a kernel read restriction")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("command required after --")
    try:
        preflight = assess(args.task, command)
        if preflight["decision"] != "allow":
            print(json.dumps({"phase": "preflight", **preflight}))
            return 77
        summary = capture(args.workspace, command, output=args.output,
                          evidence=args.evidence, sensor=args.sensor)
        rule = rule_verdict(summary, forbidden_reads=args.audit_forbidden_read)
        learned = judge(args.task, command, summary)
        # Evidence-based violations cannot be downgraded by the probabilistic judge.
        verdict = rule
        if rule != "violation":
            if rule == "abstain" or learned["decision"] == "abstain":
                verdict = "abstain"
            elif learned["decision"] == "deny":
                verdict = "review"
        result = {"preflight": preflight, "rule": rule, "model_audit": learned,
                  "verdict": verdict, "evidence_status": summary["evidence_status"],
                  "scope": "post-execution audit; no_observed_violation is not a safety guarantee"}
        (Path(args.evidence) / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        return 0 if verdict == "no_observed_violation" else 79
    except Exception as error:
        print(json.dumps({"verdict": "abstain", "reason": type(error).__name__}))
        return 78


if __name__ == "__main__":
    sys.exit(main())
