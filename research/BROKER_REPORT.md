# Pre-release authorization at the protected-resource boundary

`release_broker.py` closes one demonstrated gap in the live syscall monitor:
protected bytes are withheld before authorization rather than read first and
classified afterward. Protected resources are immutable byte snapshots in the
trusted broker and are never mounted into the worker's filesystem. This is a
specific reference-monitor boundary, not interception of every possible syscall.

## Mechanism and assumptions

The supervisor binds a principal to a private Unix SOCK_SEQPACKET socketpair.
The worker deliberately inherits only that channel, alongside ordinary standard
descriptors; it receives no protected-file descriptor. Other descriptors and the
supervisor's credentials remain closed. The resource identifier is a lookup key,
not a filesystem path. Requests cannot choose another principal, task or policy.
The broker checks supervisor-provisioned grants and an integer task epoch before
calling its observer. Jev sees trusted task/resource metadata and a snapshot hash,
not the protected bytes. Correct grants and provisioning are trusted inputs.

After the observer returns, the broker reacquires the release lock and rechecks
the epoch, resource hash, grant, health and stop state. It requires a finite valid
probability below the provisional 0.5 threshold and an approval returned within
two seconds. A slow synchronous observer can delay denial until it returns, but
cannot obtain a release by returning after that deadline. This is not a hard
two-second worker-termination bound.

The final check and nonblocking packet send occur under the same lock as trusted
revocation, resource changes and external supervisor stop signals. A full socket
closes the channel and stops the scope; it cannot block revocation behind a waiting
send. Denial stops the group. The runtime supervisor polls the shared stop signal
and kills each worker's PID namespace. Detected live-monitor faults propagate to
that same signal; this does not establish detection of every lost event.

No secret bytes are released to ungranted requests or through paths omitted from
the mount namespace. Already-authorized content can subsequently be copied by the
worker and cannot be erased by revocation. Runtime libraries, outputs and scratch
files remain within the existing sandbox contract. The trusted supervisor, kernel,
Bubblewrap, resource provisioning and broker itself are not adversaries. A worker
holding the channel may use it from descendants within its principal's scope.

## Commit-order property

Let R denote the successful kernel send of one protected packet, and V completion
of a revocation/stop operation. Both use the same commit lock. If V precedes R,
the final predicate observes the changed epoch, removed grant, changed hash,
unhealthy state or terminal stop flag, so no protected send can occur. If R precedes
V, the packet is already queued in the kernel and may be received afterward. The
guarantee concerns release commits, not erasure or delivery time.

This is a conditional code-level argument, not a mechanized proof or a new
concurrency theorem. It requires all relevant transitions to use the guarded API.
Tests include stopping between approval and commit, and an external stop contending
with a commit already in progress. An initial implementation used a raw Event for
external stops; that setter could interleave with the last check/send. `ScopeStop`
now acquires the commit lock, and the dedicated concurrency test verifies its order.

## Measured evidence

All 65 repository tests passed in native Kali WSL. Twelve broker tests include real
socket traffic, concurrent pending decisions, backpressure, identity/schema attacks,
stale epochs, non-retractable committed messages, and two real sandbox tests. The
terminal-stop test prevents accidental resurrection of a revoked scope, and invalid
or unavailable observer outputs are verified to deny release. The retained full
[WSL test log](broker-runs/tests-wsl2.txt) records all 65 passing tests. A stopped
scope must be replaced with a newly provisioned broker rather than resumed.
The descriptor test confirms only one descriptor above stderr is deliberately exposed:
the broker channel. Deterministic callbacks are labelled as fixtures, not Jev results.

The final deterministic pilot contains six cases, each with two concurrent real
sandbox workers, with retained raw syscall captures:

| Condition | Protected release commits | Later worker outputs |
|---|---:|---:|
| Stable allowed task | 2 | 2 |
| Ungranted resource | 0 | 0 |
| Task changes while approvals are pending | 0 | 0 |
| Resource changes while approvals are pending | 0 | 0 |
| Detected coverage loss while approvals are pending | 0 | 0 |
| Host pathname replaced; approved snapshot unchanged | 2 | 2 |

The two allowed pathname cases return the original snapshot hash, not replacement
path content. In every allowed worker the direct host path and `/proc/1/root` path
attempts fail. A separate two-worker live-provider case uses actual Jev release
decisions, 0.36 and 0.17, and both authorized releases complete. Its syscall-level
observer remains a fixture; the release gate is the live component. No Grok subjects
were launched. This establishes plumbing and these specific invariants, not accuracy
rates or generalization.

[verified-summary.json](broker-runs/verified-summary.json) independently validates
the fourteen final worker captures, hash manifests, runtime records, snapshot hashes
and expected outputs. Historical development-v1 retains a pilot-reader failure:
termination interrupted a worker's JSON output, and the analysis assumed every
existing output file was valid JSON. The reader now records absent, parsed and
partial/invalid outputs. Comparison-v2 is retained; comparison-v3 uses the guarded
stop event and final behavior. Captures labelled `elapsed_commit` contain absolute
monotonic timestamps, not latency; the source field is now named `commit_monotonic`.

## Closest prior work and novelty verdict

[DelegateGuard](https://arxiv.org/html/2610.16005v1) already addresses purpose-bound
capabilities, delegated authority and cascading revocation. Its threat model excludes
operations bypassing its mediation boundary. [Lever](https://lever.to/capabilities/)
already documents identity-bound broker capabilities with epoch/revocation checks.
[Capsicum](https://man.freebsd.org/cgi/man.cgi?query=capsicum&sektion=4) predates both
with capability-based Unix isolation. Consequently, capabilities, brokered access,
epochs and revocation are not new contributions here. Word searches failing to
find a concurrency detail in a paper are not evidence that its implementation has
a race or that our ordering rule is novel. No prior-system bug is claimed.

The current artifact adds concrete WSL process isolation, protected-byte release
tests and in-flight approval invalidation to GuardianAI. Whether a larger study of
decision latency, coverage faults and context-pressure authority mismatches yields
a distinct journal contribution remains open. No Q1-readiness claim is warranted
without prior-system baselines, broader fault/bypass testing, persistent-agent
measurements and a defensible new finding. See the next experimental protocol.

## Reproduction

```sh
python3 -m unittest discover -s tests -v
python3 research/broker_pilot.py --destination /new/empty-parent/broker-pilot \
  --sensor /path/to/strace
python3 research/broker_pilot.py --destination /new/empty-parent/live-release \
  --sensor /path/to/strace --case live_allow
python3 research/broker_summary.py
```

The first pilot uses fixtures only. `live_allow` requires the trusted supervisor's
Jev credential and makes live calls. The summary script makes no API calls.
