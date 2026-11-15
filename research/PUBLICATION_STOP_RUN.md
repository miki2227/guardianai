# Operator revocation at public-only result publication

The [audit](publication-stop-runs/audit.json) records a cancellation failure,
its six-line correction and normal useful work afterward. No new model subjects
or malicious agent instructions were used. Jev and Linux supervision were active.

## Reproduced failure

The [baseline](publication-stop-runs/v2/workflow.py) used the previous packaged
runtime without a flow manifest: the supported public-only mode, recorded as
`information_flow: {mode: untracked}`. Execution remained supervised.
The command generated an index of 17 public source hashes, a README and a ZIP.

After the final tool-response observer input appeared, the trusted controller
issued an operator stop. It observed the matching acknowledgement while the
results directory was absent. The pending result nevertheless published that
directory, returned stdout and reported `no_observed_violation`. The next command
was refused. The worker exited 0 and the content checks were unflagged.

The [observations](publication-stop-runs/v2/run/observations.json), input hash,
acknowledgement, actual response and files retain this cancellation-contract
failure. This was not a kernel escape, malicious model finding or disclosure of
actual private data. The inputs were public.

## Correction and actual reruns

The untracked branch previously renamed output after semantic checks without
rechecking revocation. It now holds the existing broker commit lock, checks the
terminal stop flag and then commits publication. A stopped scope returns
`abstain` with `scope_stopped_before_publication`, omitting stdout/stderr and the
results path. The tracked branch retains its `FlowPolicy.transfer` lock; no
flow-to-broker lock order was introduced.

The [corrected cancellation](publication-stop-runs/v3/run/summary.json) again
observed acknowledgement before publication. The directory stayed private,
stdout/stderr were withheld, MCP returned `isError: true`, and the next command
was refused without another worker.

The [normal run](publication-stop-runs/normal/run/summary.json) sent identical
requests through the corrected runtime without cancellation. Packaging and the
following checksum both exited 0 and returned unflagged results. The index and
README bytes match the baseline publication and corrected private output.
Each ZIP's members match its text files; ZIP wrapper bytes can differ with member
timestamps. All scopes closed.

There were four completed native worker commands: one baseline, one corrected
cancellation and two normal commands. This is one matched cancellation per
revision, not a stress test of every schedule or a detector benchmark. Jev was
not stubbed or artificially delayed. No remote inference cancellation was tested.

## Retained installation failure

The initial [v1 attempt](publication-stop-runs/v1/run/summary.json) extracted the
runtime with Python without restoring the native helper's execute bit. It
abstained with `PermissionError` before creating worker evidence; the intended
cancellation window was not reached. The
[native diagnostic](publication-stop-runs/initial-permissions.json) records
0644/non-executable for v1 and 0755/executable for v2. The corrected controller
restores permission on the trusted installation. This attempt is not counted
as a completed worker or a cancellation result.

## Package, verification and limits

The [corrected core package](publication-stop-runs/v3/run/bootstrap/GuardianAI-linux-x86_64.zip)
has 20 members, 54,069 bytes, policy 3 and launcher guard 1. SHA-256:
`b1712262419b36d62b3e675535c7d299f7752fb677a352b8943a3251c076e601`.
The trusted bootstrap build was outside supervision; its runtime was used by
the corrected cancellation and normal supervised commands.

Run `python research/publication-stop-runs/summarize.py` to recheck request bytes,
stop IDs, local controller ordering, native outcomes, response/publication
differences, source hashes, ZIP members and package hashes without model calls.
The controllers retain machine-specific paths and new-directory requirements.

The commit boundary is the directory rename under the broker lock. Completed
revocation before that commit prevents publication. A stop cannot recall already
committed output. The later stdio write is separate, not transactional transport.
A stop-request file alone is not a revocation acknowledgement.

The host filesystem and runtime remain trusted. Rename can delay lock holders;
this is not hard real-time stopping. Controller clocks establish order within
each case, not across separate runs. Private thoughts, all covert channels and
general malicious-behavior recall remain unobserved. The IEEE front matter and
pinned historical measurements are unchanged.
