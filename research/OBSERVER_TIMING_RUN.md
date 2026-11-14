# Observer completion timing and deadline handling

15 November 2026. Source inspection found that the runtime consumed a completed
future before checking the observer deadline. A response completed after the
deadline could therefore be accepted if it finished before the next polling
iteration. The earlier run records do not reproduce that boundary case.

The runtime now records completion inside the observer executor. Submission time
is captured before enqueueing. A completed answer exceeding the existing
two-second budget causes abstention before its probability is applied. A pending
answer also retains the existing deadline check. Execution and observer timeouts
now carry distinct `deadline_kind` and `deadline_seconds` fields in fault records.
The protected-resource broker's separate deadline is unchanged.

Each completed-response action records:

- `submitted_elapsed_seconds` and `completed_elapsed_seconds`: seconds relative
  to that worker supervisor's start, matching the action's existing elapsed base.
- `submission_to_completion_seconds`: queueing plus the complete local observer
  call, including state/receipt work and remote inference. This is not isolated
  provider or network latency.
- `completion_to_consumption_seconds`: delay before the supervisor handles the
  completed future.
- `deadline_met` and `decision_applied`: whether completion met the budget and
  whether the validated probability was used.
- `runtime_observer_input` and its SHA-256: the exact saved event batch, relative
  to the worker evidence directory. `session_observer_input`, when present,
  remains relative to the session evidence root and identifies the fuller shared
  state. The two inputs are separate evidence layers.

These checks do not make Python scheduling or kernel termination hard real time.
A blocked supervisor may process an event late. Timely completion and timely
consumption are different measurements. Relative times from different workers
must not be combined without a clock alignment. Faulted/pending calls can lack
completed-response timings; their absence is unknown, not zero latency.

## Real compilation

A standalone packaged MCP supervisor built the actual Linux release under live
Jev. It completed with exit 0, `no_observed_violation`, a recorded capture and
normal closure. All 43 completed observer calls met the two-second budget. Maximum
submission-to-completion time was 1.342098046 seconds; maximum consumption delay
was 0.010729178 seconds. Runtime and shared-state input hashes matched, and all
final event revisions appeared in submitted inputs.

No late response occurred. This verifies normal operation and the recorded time
joins, not empirical coverage of the late-rejection branch, a provider SLA or
general performance. No delayed fake observer, new model-agent subject or attack
suite was used.

Older inter-action gaps alone cannot establish response latency. Inspection of
their file timestamps was consistent with later submissions rather than a slow
answer; file-time diagnostics cannot recover the missing monotonic measurements.
Those old records are unchanged and are not relabelled as late-response failures.

The [summary](system-runs/observer-timing/summary.json), standard MCP request and
response files, source snapshot, native traces and decisions are retained. The
[current distribution](../dist/GuardianAI-linux-x86_64.zip) has SHA-256
`ff55a998825b679bf87830ab6694b04a95c0b3e56c1dffeb59e5a366a2965f7a`.
Archive/member hashes and packaged Python/C sources were checked. The prior
NSS-compatible distribution remains in `dist/archive-v7`. This timing contract is
an engineering correction and provenance feature; publication-level novelty
remains unestablished.
