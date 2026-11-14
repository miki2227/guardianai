<img src="assets/icon.svg" width="64" height="64" alt="">

# GuardianAI

Research testbed for pretrained sender/receiver agents communicating under Jev
oversight, supported by Linux kernel namespace isolation and execution evidence.
See [research scope and limitations](RESEARCH.md) before running untrusted code.

The [live OS-supervisor report](research/RUNTIME_REPORT.md) records runtime
observation, Jev-triggered namespace termination, and WSL validation. This reacts
to completed syscalls; pre-effect mediation remains unfinished.

The [protected-resource broker](research/BROKER_REPORT.md) adds a pre-release
boundary for resources kept outside agent mounts, with task/epoch revalidation
and shared-scope stopping. This does not mediate every syscall or erase prior data.

The corrected [paired-agent protocol](research/PAIRED_PROTOCOL.md) and
[current paired results](research/PAIRED_REPORT.md) are the main experiment.
The [social-deduction report](research/SOCIAL_REPORT.md) adds the matched
fixed/history block, actual paraphrasing, and observer-state diagnostics.
Agents receive ordinary tasks, without a supplied covert objective or protocol.
There is no model training or weight-update arm. Jev is the independent observer.

The supporting [kernel research report](research/REPORT.md) includes a primary-source
[literature audit](research/LITERATURE.md), replicated real WSL2 executions, live
Jev judgments, evidence-damage ablations, and engineered two-agent channel controls.
Use [reproduction instructions](research/REPRODUCE.md) to inspect the raw traces
or run the study. The report preserves negative results and limits novelty claims.

Requires Python 3.10+, Linux (native or WSL2), Bubblewrap, and user namespaces.
Set `TYPESAFE_API_KEY` in the trusted supervisor environment. Never put credentials
in the task directory. Jev evaluates task text and command arguments remotely.

```sh
mkdir -p /tmp/guardian-input
output_dir=$(mktemp -d /tmp/guardian-output.XXXXXX)
python3 guardian.py --task 'Write /output/result.txt containing ok' \
  --workspace /tmp/guardian-input --output "$output_dir" -- \
  python3 -c "from pathlib import Path; Path('/output/result.txt').write_text('ok')"
python3 -m unittest discover -s tests -v
```

The CLI denies on Jev probability >= 0.2 or missing/invalid provider results.
This threshold has not been calibrated for deployment. The model is pinned to
`jev-1.14.0`. Inputs are mounted read-only at `/workspace`. Results go into a
separate, initially empty directory at `/output`; the command starts in `/output`.
Input and output directories must be disjoint, including resolved symlinks.
The isolated command can write `/output` and private `/tmp`,
read runtime libraries, and cannot use the host network or see host home directories.
Child processes inherit isolation. No kernel module is installed.

`python tests/live_pilot.py` runs six synthetic command descriptions against the
real Jev API and writes `evidence/live-pilot-output-boundary.json`; it executes no described commands.
Kernel tests execute bounded Python payloads with actual namespace isolation.
Windows skips those tests; run them inside Linux for containment evidence.

Earlier evidence records the initial fully writable workspace prototype. Those
reports remain historical; their runners use its earlier API. Current launch calls
require `output=` and the CLI requires `--output`.

`audit_session.py` adds strace-based kernel-origin evidence and a retrospective
task-rule/Jev audit. It requires a trusted evidence directory outside the agent's
mounts. This is user-space tracing of kernel syscalls; Jev inference remains remote.
