# Supervisor lifetime and actual build cancellation

15 November 2026. The real Grok integration exposed missing final closure records
when the client killed its MCP subprocess. Python `finally` blocks cannot handle
SIGKILL. Source inspection also showed that the old tracer launch had no kernel
binding to the supervising Python thread. A missing final record and a surviving
worker are separate problems; this change addresses the execution-lifetime link.

The trusted native helper now supports `--watch-parent EXPECTED_PID COMMAND`.
It checks the expected parent, sets `PR_SET_PDEATHSIG(SIGKILL)`, checks the parent
again, and execs the trusted tracer. The tracer runs with `--kill-on-exit`, which
sets `PTRACE_O_EXITKILL`. Namespace-init death then terminates namespace members.
These are existing Linux mechanisms, not a new detection algorithm.
[Parent-death semantics](https://man7.org/linux/man-pages/man2/PR_SET_PDEATHSIG.2const.html),
[strace exit-kill semantics](https://man7.org/linux/man-pages/man1/strace.1.html).

```mermaid
flowchart LR
  S[Supervising Linux thread] -->|parent-death SIGKILL| T[Trusted strace]
  T -->|PTRACE_O_EXITKILL| N[Traced namespace leader and processes]
  N -->|namespace-init termination| D[Remaining namespace members]
```

Supported guarded launchers require helper `launch_guard_version: 1`; their
syscall filter remains `policy_version: 3`. Old helpers lacking the guard feature
are refused before launching workers. Runtime manifests retain the tracer argv
and configured guard status. Raw `supervise` calls without the trusted helper
receive exit-kill tracing but do not get the supervisor parent-death binding.

## Actual operation

A standalone packaged MCP server completed a real GCC release build under live
Jev. The worker exited 0 with a recorded capture, final trace drain and 236 scoped
events. All final event revisions matched 44 saved observer inputs and their
hashes. This normal MCP client then closed stdin; its terminal scope record was
written with `closed: true`.

A second actual release build was cancelled while GCC was running. The external
controller held stable pidfds for the owner and captured live descendants, then
sent SIGKILL only to the Python owner. The four captured descendants—strace,
Bubblewrap, namespace PID 1 and GCC—all became exited without manual cleanup.
Their first observed exit times were approximately 10.4 ms after the signal,
within one polling interval. This is a single observation bound, not an isolated
component benchmark or hard-real-time guarantee.

No new model-agent session or attack suite was used. The controller executes the
actual MCP build operation; it does not substitute a fabricated workload. Its
[source](system-runs/owner-lifetime/controller.py), [summary](system-runs/owner-lifetime/summary.json),
[pidfd observations](system-runs/owner-lifetime/cancellation.json) and raw artifacts
are retained. The cancelled execution has no runtime verdict; its killed tracer
cannot flush a complete final capture. It remains interrupted evidence.

The [toolchain observation](system-runs/owner-lifetime/toolchain-observation.json)
records a non-setid tracer without file capabilities. Parent-death settings can
be cleared by privileged exec or credential changes and refer to the creating
thread, so the argument depends on this trusted, nonprivileged launch path.
The normal run and cancellation do not cover kernel compromise, every startup
interleaving, other platforms or a modified tracer. No data is recalled and no
remote inference is cancelled. Abrupt-death closure records remain unavailable;
the execution guard does not fabricate them.

The [updated distribution](../dist/GuardianAI-linux-x86_64.zip) has SHA-256
`8498881e8ab3399387b973df453055ed4332815baf706408f6b422372326def2`.
Its archive/member hashes and packaged Python/C sources were checked. The earlier
coding-agent package remains in `dist/archive-v5`.
