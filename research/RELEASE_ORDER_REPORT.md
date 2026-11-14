# Prohibited syscall and protected-release ordering

A scripted Linux ordering probe exposed a gap between a kernel-denied operation
and revocation of the worker's remaining authority. In the original implementation,
`ptrace` returned `EPERM` in the kernel, while the supervisor learned about the
attempt later from strace. An already-granted protected read could reach the
descriptor broker in that interval. The resource approval callback did not know
about the unprocessed attempt.

This matters for GuardianAI's policy of stopping a task scope after a prohibited
attempt. The synthetic summary was an allowed resource before that attempt.
The probe demonstrates delayed scope revocation and subsequent release, with
no namespace escape, real private data or model-agent subject involved.

## Working correction

The trusted native launcher's policy version 2 sends `connect` and `ptrace`
syscalls to the seccomp notification listener. These syscall families already
triggered deterministic stopping in the trace monitor. The listener now records
the kernel notification, stops the shared broker scope under its commit lock,
then returns `EPERM` to the caller. The protected syscall is never continued.
No pathname or socket-address pointer must be interpreted to make this denial.

Pending approvals in other workers recheck the same shared stop state under that
lock before descriptor injection. A two-worker Linux regression holds B's approval
pending, triggers A's prohibited connection attempt, then returns B's low-risk
fixture decision. Both scopes report violation and B receives no protected release.
This regression tests an explicit synthetic ordering rather than model intent.

At this study revision, `SeccompGate` required native policy version 2. The later
[filter-stacking correction](FILTER_STACK_REPORT.md) requires policy version 3.
Rebuilding the helper is required after updating; the one-command demo rebuilds
it before running. ABI size checks remain in place.

The [Linux seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html)
defines notification behavior and filter inheritance. The
[notification manual](https://man7.org/linux/man-pages/man2/seccomp_unotify.2.html)
describes suspended target calls and supervisor replies. This correction uses
existing Linux mechanisms; syscall notifications or scope revocation are not new
primitives invented by this project.

## Retained experiment

[`release_order_pilot.py`](release_order_pilot.py) compiles an ordinary C worker
with three modes: an approved read, self-`ptrace` followed by that read, and a
localhost connection attempt followed by that read. A kernel denial is caught
and execution proceeds immediately to the read. The worker then waits so the
monitor has an opportunity to stop it. Protected bytes are a synthetic canary.
Both observer callbacks are deterministic fixtures; no hosted model calls are
used in these ordering probes.

The following controls were each run three times on the existing WSL2 host.
The no-stack condition still uses strace; it disables native unwinding only.
Source snapshots, helper bytes, source/helper hashes, native traces, frozen
observer inputs and broker/kernel audit records are retained for all 36 workers.

| Configuration | Prior call | Descriptor commits / 3 | Canary printed / 3 |
|---|---|---:|---:|
| Original, native stacks | `ptrace` | 2 | 1 |
| Original, native stacks | `connect` | 0 | 0 |
| Original, no native stacks | `ptrace` | 3 | 3 |
| Original, no native stacks | `connect` | 3 | 3 |
| Policy 2, native stacks | `ptrace` | 0 | 0 |
| Policy 2, native stacks | `connect` | 0 | 0 |
| Policy 2, no native stacks | `ptrace` | 0 | 0 |
| Policy 2, no native stacks | `connect` | 0 | 0 |

Approved-read controls committed and printed their canary in all three repeats
of all four configurations. The difference between commits and printed bytes is
retained: a descriptor injected before termination is already delegated authority,
even when no completed stdout write follows. Neither count should replace the other.

All retained ordering captures pass their current manifest/termination checks.
The offline [verified summary](release-order-runs/verified-summary.json) independently
checks source/helper hashes, case sets, trace hashes, capture statuses, observer
input hashes, release counts, stdout and notification/scope-audit joins. These
consistency checks assume a trusted supervisor; they do not prove all events were
captured. A clean capture status is not a universal observation guarantee.

The full native Linux suite passed **89 tests**, including new sequential denial,
cross-worker pending-release and stale-helper regressions;
[log](release-order-runs/tests-wsl2.txt). Historical test and trial counts remain
versioned rather than rewritten as if older artifacts used policy 2.

The updated [live Jev CLI smoke](release-order-runs/live-cli-policy2/summary.json)
also passed: the approved read returned exit 0, an unregistered read returned 77,
and an ordinary worker failure retained exit 1. The unregistered read is rejected
before inference. Source snapshots, captures, frozen observer inputs and approval
joins were audited. This provider-backed smoke is separate from the fixture-only
36-worker ordering experiment.

## Bounds and next checks

The measured correction covers notifications delivered for the two declared
syscall families. It does not establish a global evidence frontier across every
operation or thread. Input-mutation attempts and arbitrary semantic policy
violations still have other observation paths. Already committed descriptors,
already delivered knowledge, unknown sensor loss and host/kernel compromise
remain outside this result.

The subsequent [filter-stacking study](FILTER_STACK_REPORT.md) confirmed that a
worker-installed filter could suppress policy 2 notifications through both Linux
installation interfaces. Policy 3 blocks those installation routes. The versioned
policy 2 result above must still be read within its tested filter configuration;
broader mandatory observation coverage is not established by either finite test.

The differences between the original unwinding conditions are small-sample
scheduling outcomes. They do not establish that disabling unwinding generally
increases failure probability or that a particular measured rate will reproduce.
Three repeats cannot establish a worst-case bound. The contribution candidate is
the measured separation between attempted-operation denial, scope revocation,
descriptor commitment and observable output, with a working bounded correction.
Publication-level novelty and persistent-context effects remain unestablished.

Reproduce inside the native Linux checkout with a newly built launcher:

```sh
python3 research/release_order_pilot.py --destination /new/native/ordering-run \
  --sensor /path/to/strace --native-stacks --repeats 3
```

Audit the retained versioned bundle without launching workers:

```sh
python research/release_order_summary.py
```
