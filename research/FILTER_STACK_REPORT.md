# Worker-installed filter suppression

Policy 2 had a confirmed notification-coverage gap. A worker could install an
additional seccomp filter returning `ERRNO` for `ptrace`, so that the operation
was denied without reaching GuardianAI's notification listener. The worker could
then request its previously granted protected summary before retrospective scope
stopping. Both Linux installation interfaces reproduced the gap.

This behavior follows documented Linux filter precedence. Existing filters remain
active, but the selected action can suppress a lower-precedence notification.
An increasingly restrictive syscall policy can therefore weaken observation-based
scope revocation. The experiment exposes this defect in GuardianAI's policy 2;
it establishes no corresponding defect in nono or another published system.
[Linux filter documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html),
[seccomp manual](https://man7.org/linux/man-pages/man2/seccomp.2.html).

## Working policy 3

The native filter now routes worker filter-changing operations through the
notification listener, where the shared scope is stopped before the call receives
`EPERM`. It intercepts `prctl(PR_SET_SECCOMP, ...)` and seccomp operations other
than the two supported query commands. Both strict-mode and filter-mode changes
are covered by regressions. The worker-supplied BPF program is never dereferenced
or executed to make the denial decision.

`SECCOMP_GET_ACTION_AVAIL`, `SECCOMP_GET_NOTIF_SIZES`, and other `prctl` operations
remain available. The native program reloads the syscall number after examining
the operation argument, so unrelated calls still reach their intended rule.
`ptrace` and `connect` continue to use policy 2's synchronous scope-stop path.
The Python gate now requires helper policy version 3, rejecting policy 2 and
unversioned helpers before worker execution. Rebuild after an update.

The policy imposes a real compatibility restriction: a worker application that
needs to install its own seccomp sandbox will be stopped, even when that
application's purpose is legitimate. Such applications are outside this runtime
profile. Ordinary query success is not evidence that every workload remains
compatible. Unknown seccomp operations are denied rather than assumed harmless.

The two installation interfaces are documented Linux APIs, not new attack
primitives. [PR_SET_SECCOMP manual](https://man7.org/linux/man-pages/man2/PR_SET_SECCOMP.2const.html).
This is a concrete monitoring correction and an executable counterexample to
unqualified notification coverage, not an established new security algorithm.

## Retained execution evidence

The extended [`release_order_pilot.py`](release_order_pilot.py) compiles a small
ordinary C worker. Each masking case installs a valid filter that changes only
`ptrace` to an `ERRNO` result, attempts self-`ptrace`, then immediately reads a
synthetic summary through the protected-resource interface. The summary is an
allowed resource until the task-scope stop policy intervenes. There is no host
escape or real secret. Observer callbacks are labelled deterministic fixtures;
no Grok subjects or hosted model calls participate in these probes.

| Configuration | Installation interface | Successful installs | Descriptor commits | Canary printed |
|---|---|---:|---:|---:|
| Policy 2, no native unwinding | `seccomp` | 3/3 | 3/3 | 3/3 |
| Policy 2, no native unwinding | `prctl` | 3/3 | 3/3 | 3/3 |
| Policy 3, no native unwinding | `seccomp` | 0/3 | 0/3 | 0/3 |
| Policy 3, no native unwinding | `prctl` | 0/3 | 0/3 | 0/3 |
| Policy 3, native unwinding | `seccomp` | 0/3 | 0/3 | 0/3 |
| Policy 3, native unwinding | `prctl` | 0/3 | 0/3 | 0/3 |

Three further native-unwinding controls successfully queried notification support,
notification structure sizes and their current seccomp mode, then read and printed
the approved summary. Those controls complete the 21 retained workers. Separate
regressions also check ordinary `PR_SET_NAME`, strict-mode changes through both
interfaces, and refusal of older native helpers.

All 21 captures satisfy their recorded manifest/termination checks. The
[offline auditor](filter_stack_summary.py) validates source snapshots, preserved
helper bytes, probe-source identity, trace sets/hashes, observer snapshot hashes,
worker output, release counts and notification/scope-audit joins.
[Verified result](filter-stack-runs/verified-summary.json).
These checks assume a trusted supervisor; they do not establish complete evidence
capture against arbitrary host tampering. Three repetitions on one WSL2 host do
not estimate population failure rates or a worst-case latency bound.

The full native Linux suite passed **92 tests**;
[test log](filter-stack-runs/tests-wsl2.txt). Earlier ordering and baseline artifacts
remain pinned to their actual historical code and native policies. The old
suppression examples are retained rather than rewritten using the corrected gate.

The updated [live Jev CLI smoke](filter-stack-runs/live-cli-policy3/summary.json)
also passed its approved-read, unregistered-read and ordinary-worker-failure
controls with native exit statuses 0, 77 and 1. Its source snapshots, captures and
approval joins were audited separately; the unregistered request is denied before
inference. This provider-backed smoke is not part of the 21 fixture-only probes.

## Remaining research boundary

The correction blocks the tested worker-controlled installation routes after the
trusted launcher installs its filter. It does not prove coverage under arbitrary
pre-existing host filters, compromised tracers, kernel exploits, unknown syscall
surfaces or all future kernel API extensions. Trace-based input-mutation and
semantic-rule checks retain their own observation delays. Previously committed
data cannot be retracted, and a completed read need not produce a captured print.

This result strengthens a necessary runtime precondition for the planned persistent
agent study. It does not measure spontaneous misalignment, covert coordination,
natural context-window pressure, Jev accuracy or publication-level novelty.
Notifications, filter precedence and anti-tampering policies are prior mechanisms;
the measured interaction between denial, observation suppression and subsequent
descriptor release is the narrowly supported finding.

Reproduce in a native Linux checkout with the current helper built:

```sh
python3 research/release_order_pilot.py --destination /new/native/filter-probe \
  --sensor /path/to/strace --case seccomp_mask --native-stacks --repeats 3
```

Use `--case prctl_mask` for the other installation route and `--case queries` for
the utility control. The retained historical bundle can be audited without
launching a worker:

```sh
python research/filter_stack_summary.py
```
