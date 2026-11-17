# Working supervised two-agent Checkstyle workflow

**The corrected practical workflow completed.** Two continuing Grok 4.7 subjects,
both at low reasoning effort, performed investigation, independent review and
reconciliation. They completed nine supervised Linux commands with zero worker
exit codes and three clean closed scopes. Two Jev-approved artifact handoffs were
opened by their recipients, and the complete peer texts appear in the receiving
CLI tool results. The [audit](checkstyle-paired/v5/audit.json) verifies these joins.

The Grok subjects performed the bug work. The host implemented supervision,
authorized local fixtures, relayed their artifacts and checked evidence. It did
not supply bug findings, train weights, upgrade the subjects, give them a hidden
protocol or require a P0 result. The final subject report says no P0 was
established; its lower-severity claims remain provisional and not independently
validated here. This run establishes useful supervised collaboration, not a
validated covert convention or detection of private thoughts.

## Working path and evidence

The source snapshot is the clean Checkstyle checkout at
`88eca75e60213e788100f2f6aadc3c8ec5d44919`. Original tracked-file hashes are in the
earlier [snapshot manifest](checkstyle-practical/v1/source-manifest.json). Cached
Checkstyle classes and a dedicated public JDK were used; this was not a fresh
source build. The CLI's version string is null and is not treated as a release
identifier. No issue, PR or vulnerability disclosure was sent.

The accepted run retains [prompts and results](checkstyle-paired/v5/result.json),
CLI messages, tool requests/results, artifact inventories, Jev inputs/answers,
native traces and runtime source snapshots. The audit verifies 133 scoped runtime
events and 1,582 frame entries in submitted snapshots. These are bounded native
execution frames, not unique call stacks or hidden model reasoning. Runtime
library reads remain in raw traces and are not individually semantic-scored.
There were 109 host/MCP content chunk calls, excluding runtime, handoff and
confirmation calls; that count is not a sample size for detector accuracy.

The agents' [final report](checkstyle-paired/v5/reconciliation/results/step-002/final-findings.md)
records the result of their collaboration. Their entity tests used only
hardcoded local markers and configs under `/output/csfix`, with no real private
files or network. Parser-error exit codes inside those reproductions are distinct
from the nine successful supervising worker commands.

## Corrections required to make it useful

- Known MCP JSON wrappers are decoded before host content observation. Original
  CLI strings remain in the captured stream and are linked by SHA-256. Duplicate
  object keys prevent decoding rather than silently discarding evidence.
- A candidate alert first receives complete-message contextual review. If that
  cannot fit 20 KiB, every character is reviewed in overlapping parts with a
  shared source hash and offsets. A flagged part stops; errors abstain. Cleared
  multipart reviews require all parts. Parts do not provide simultaneous whole-
  message context, and taking the maximum is not a calibrated operating point.
- Trace records are submitted after their bounded frame sequence closes, avoiding
  repeated judgments of partially growing stacks. Parsing is bounded to 128 raw
  lines per pass. The worker process group is paused during runtime inference;
  this is not an atomic freeze of all namespace descendants. The response cap is
  now 45 seconds for up to two existing 20-second transport calls and evidence
  overhead. Execution deadlines and protected-read deadlines remain separate.
- `--runtime-subdir practical-runtime` exposes only a selected subset of the
  already-public source read-only at `/runtime`. It grants no new host access.
  The standard JDK and compiled libraries use that alias instead of being treated
  as source activity. Attempted runtime writes remain scoped violations.
- The policy distinguishes task-authorized synthetic fixtures from real private
  data. The concrete task explicitly permits local XXE/DTD fixtures only under
  `/output/csfix`; that authorization does not declassify protected data.
- The tracer uses a pinned strace 7.0 build with libdw. The earlier libunwind build
  exited fatally during Java thread teardown. Upstream's
  [libunwind backend](https://raw.githubusercontent.com/strace/strace/v7.0/src/unwind-libunwind.c)
  contains the matching fatal initialization path; the
  [libdw implementation](https://raw.githubusercontent.com/strace/strace/v7.0/src/unwind-libdw.c)
  is an existing alternative, not a new unwinder. The
  [local build report](checkstyle-paired/sensor-build/report.json) pins source,
  package and binary hashes. Dependencies were unpacked in a dedicated tools
  directory, not installed into the system.
- A non-returning `exit`/`exit_group` record is accepted only with its terminal
  trace record. Interrupted non-exit syscalls and missing terminal records still
  fail closed. This does not silently accept arbitrary split syscall evidence.

## Real subject mistake caught during verification

The [v4 attempt](checkstyle-paired/v4/acceptance-failure.json) closed its scopes,
but the reviewer reused earlier history without reading the new candidates file.
The host audit rejected freshness; Jev alone did not detect that omission. The
old reports remain intact and are not counted as an accepted fresh review.

The corrected workflow now requires an actual read of the current peer artifact
before accepting that phase and allowing its report to be handed onward. Its
independent verifier additionally checks complete peer text in the recipient's
CLI result. This is an evidence-based workflow requirement, not a claim about
what the model understood. The same two histories received the correction;
no replacement subjects were introduced. The original client folders were reused
for resumption, and their temporary MCP configurations were restored afterward.

## Safety and validation

The [separate live control](checkstyle-paired/v5/safety-result.json) rejected an
unapproved protected-file request before worker execution, stopped the scope and
refused the next ordinary command. It started zero workers and read no private
file. This is a deliberate control, not spontaneous agent misconduct. The
[final selected Linux suite](checkstyle-paired/v4/validation-passed-output.txt)
passed 74 tests with no skips. Those tests include fixture observers and actual
kernel denials/namespace stopping; they are separate from live Jev inference.

Earlier v2/v3 runtime, policy-scope, transport/configuration and review failures
are retained separately. The first full regression attempt exposed a stale
exception-message assertion; its failure and corrected rerun are both retained.
Nothing here is a pooled detector-accuracy benchmark.

The [cleanup record](checkstyle-paired/v5/cleanup.json) confirms restored client
and trust configuration, an unchanged clean OneDrive checkout and the unchanged
original builder quarantine. The quarantined builder was never resumed. Old MCP
stop records were never cleared. New public-only scopes reused only the two
Checkstyle histories under the user's instruction to make the experiment work.

Run `python research/checkstyle-paired/v5/audit.py` for retained evidence joins.
The external source/JDK/dependency copies are not included in the run dataset.
No universal detection, spontaneous misalignment, context saturation or globally
novel algorithm is claimed. The full original research objective remains broader
than this successful practical workflow.
