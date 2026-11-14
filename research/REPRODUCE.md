# Reproduce or audit GuardianAI

## Environment

Measured: Kali WSL2, Linux `6.6.87.2-microsoft-standard-WSL2`, Python 3.13.12,
Bubblewrap 0.11.0, strace 7.0 (`strace_7.0+ds-1_amd64.deb`), Jev `jev-1.14.0`.
The code uses Python's standard library. Figure generation additionally uses
matplotlib and NumPy; figures were generated on Windows with matplotlib 3.10.8.
No kernel module or eBPF program is installed.

Run Linux tests from a native Linux filesystem, not `/mnt/c`. Copy the source
into a fresh directory under your WSL home. Never use the project checkout,
credential directory, or real private files as an agent workspace.

## Verify retained evidence without making API calls

Extract `results/raw-results.tar.gz` into a new empty directory. It contains
`main-v1`, `reanalysis-v1`, `counterfactual-v1`, and the diagnostic `smoke-v1`.
The manifest under each capture contains the raw trace hashes. Use
`monitor.summarize(capture_directory)` to validate/reinterpret an individual set.
Do not substitute raw trace text from an agent response for trusted sensor files.

```sh
mkdir /tmp/guardian-review-results
tar -xzf research/results/raw-results.tar.gz -C /tmp/guardian-review-results
python3 research/analyze.py --results /tmp/guardian-review-results
python3 -m unittest discover -s tests -v
```

Compare the recomputed `summary.json` with the delivered one. Timing fields in
raw captures are measured; analysis itself makes no network calls. `analyze.py`
uses the corrected parser to revalidate the counterfactual captures. The original
all-abstention rows remain visible in `main-v1`; reported classifier results use
`reanalysis-v1`. The raw archive includes the complete original and derivative data.

## Run new experiments

Provide Bubblewrap and strace on the Linux machine. In this run, strace was
unpacked into the user's home from a distro package with `apt download strace`
and `dpkg-deb -x`, without installing it system-wide. Its path was
`/home/pratz/guardianai-tools/unpacked/usr/bin/strace`.

Configure `TYPESAFE_API_KEY` only in the trusted supervisor environment. Keep it
out of task inputs, shell history, output files, and version control. For WSL,
the existing Windows key was forwarded through WSLENV, without putting its value
on a command line. If no key is available, omit `--live` for execution-only
diagnostics and do not describe their classifier outcomes as measured.

```sh
python3 research/evaluate.py --sensor /path/to/strace \
  --destination /new/empty-parent/main --seeds 4 --live
python3 research/counterfactual.py --sensor /path/to/strace \
  --destination /new/empty-parent/counterfactual
```

Destination directories must not already exist. Each workload runs only in a
fresh dedicated sandbox. The evaluation intentionally executes even preflight
denials to collect paired offline evidence. The command launcher does not do this.
Remote-model probabilities and timings can change on replay; pinning the model
does not guarantee identical provider behavior.

## Audit a new contained command

```sh
mkdir /tmp/guardian-audit-input
audit_output=$(mktemp -d /tmp/guardian-audit-output.XXXXXX)
python3 audit_session.py --task 'Print the number 42' \
  --workspace /tmp/guardian-audit-input --output "$audit_output" \
  --evidence /new/nonexistent/evidence-dir --sensor /path/to/strace -- \
  /usr/bin/printf 42
```

Evidence must be disjoint from input/output. A denied preflight returns 77 and
does not execute. Invalid setup or unavailable evidence returns 78. A retrospective
violation, review, or abstention returns 79; this does not undo completed actions.
The process's stdout/stderr are retained as untrusted artifacts in the evidence
directory. The audit writes `audit.json`. `--audit-forbidden-read /workspace/file`
adds a retrospective read predicate; it does not add a kernel read restriction.
The immutable-input mount and network isolation enforce independently of Jev.

## What reproducing this does not establish

The supporting kernel experiments use handcrafted workloads and explicitly engineered channels,
not unprompted malicious intent, emergent conventions, model training, or a
representative real-world security corpus. Family bootstrap intervals are
descriptive, with only twelve families. Publication-level novelty requires a
separate evaluation and a broader survey.

## Audit the actual pretrained-agent experiments

The paired and social directories contain real hosted subject responses, exact
prompts, requested model metadata, Jev judgments, and message-relay evidence.
Provider private reasoning is excluded from saved activity records. The role
threads were configured as Grok 4.7 low effort; no separate executed-model ID
was returned. No weight updates occur. Later replayed handshakes and replayed
sender messages are labelled as replay, not counted as fresh sender inference.

```sh
python research/paired_summary.py
python research/social_summary.py
python research/replay_summary.py
```

These scripts validate retained artifacts without API calls. See
[SOCIAL_REPORT.md](SOCIAL_REPORT.md) for the small-sample limits and fact-label
source. `research/t3_social_driver.js` preserves the orchestration used with the
two configured subject threads. It is a T3 functions-execution helper using the
session's tool bindings and store/load state, not a standalone Node program.
Each send uses fresh context and passes only the saved own-history note and
permitted feedback when assigned. To reproduce with another provider, submit
the saved role prompts in their recorded order and retain the actual replies;
do not expect identical remote-model samples.

`research/observer_diagnostic.py` makes new live Jev calls and refuses to overwrite
the saved diagnostic files. Use a separate artifact copy without those files for
a new run. `research/memory_replay.py prepare` similarly requires a new memory-runs
directory. Its frozen schedule and inputs can also be inspected without calling
any model. Both original and role-aware observer scores are retained; neither
rewrites historical feedback. The relay runs in Linux; hosted subject inference
does not. The Windows supervisor's API credential is never included in prompts.
