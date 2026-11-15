# Does GuardianAI work?

**Yes, as a bounded prototype for supervised MCP/Linux execution and declared
information-flow policy. It is not yet a validated detector of emergent hidden
signalling, and it cannot inspect private model thoughts.**

The evidence comes from separate development cases and source snapshots; it is
not a pooled accuracy benchmark. Existing-agent continuation completed eight
actual Linux commands across indexing, release building and correction work,
with three clean closed scopes. Earlier paired work completed 15 commands and
three verified handoffs. The public/internal MCP case withheld the prohibited
index and refused the next command while delivering identical index bytes to
an authorized internal client.

## New real crash-recovery check

The [actual run](crash-recovery-runs/v1/run/summary.json) killed the supervising
MCP process with SIGKILL while a release-build Python worker was confirmed live.
The owned process exited with -9. A pidfd confirmed that the observed worker
exited after its supervisor died. This is an interrupted build, not a completed
build or a claim that GCC itself had already started.

The persistent ledger retained its active-session marker. Reopening the same
identity stopped it and returned `abstain: scope_stopped`; no resumed worker
directory was created. The [controller](crash-recovery-runs/v1/workflow.py) and
exact runtime source hashes are retained. The worker used the real packaged
runtime and project release script, with live Jev checks. No new model subjects
or artificial malicious objective were introduced.

This replaces the previous source-only status for one abrupt-death recovery
path. It does not establish every descendant/fault timing, power-loss durability
or hard real-time cleanup.

## What remains

- Provider conversation binding is still supplied by the host and checked after
  execution, rather than authenticated before dispatch.
- Confidentiality labels cover registered inputs and mediated outputs. They do
  not automatically discover every private input or inspect arbitrary binary
  meaning. A binary in MCP `/output` is nevertheless subject to publication gates.
- Jev can produce false alarms and miss factual mistakes. Contextual review
  cleared a live alert, but human review found the operator-note scope ambiguity.
  Accuracy, calibration and false-negative rates require labelled replicated data.
- The continuing-agent records do not establish context saturation or a
  spontaneous two-agent convention. Hidden provider reasoning is unavailable.
- Atomic ledger replacement is not a tested power-loss durability protocol.

The practical outcome is useful work completing under enforced declared
boundaries, including a successful observed crash/restart refusal. Universal
malicious-activity detection and research-level covert-convention detection
remain unproven. The full goal is not marked complete.
