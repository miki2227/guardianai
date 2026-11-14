# First current-system Linux comparison

The pinned nono baseline and GuardianAI both preserved the tested permission
boundaries. GuardianAI additionally stopped later work after denied attempts,
but had substantially higher elapsed time with native-stack tracing enabled.
This is an initial systems comparison, not a model-safety or journal-novelty result.

## Pin and environment

The official [nono v0.81.0 release](https://github.com/nolabs-ai/nono/releases/tag/v0.81.0)
was downloaded as the x86_64 GNU/Linux archive. Its SHA-256 matched the digest
published by GitHub's release API:

`7ecc33ff9c349bdfa84b4496e7a7555f67bcc33f1e125c7df9efb653c6c4e569`.

The extracted executable SHA-256 was
`d8ac3fa92d87bfbe80a52ea68729a8b5b461149437d55225c356b82af5bfc90f`.
The release source commit is `b2d859deeb7a65f9ca5b334eb8726637ba76c866`.
Release metadata and commit-pinned primary documentation are retained under
[`nono-release-v0.81.0`](baseline-runs/nono-release-v0.81.0/release-metadata.json).
The native preflight successfully ran `/usr/bin/true`, denied an ungranted fake
canary read, and allowed the same read with an explicit file grant.
This baseline actually executed on the WSL installation; it was not emulated.

Runs used Kali WSL2, Linux 6.6.87.2-microsoft-standard-WSL2, x86_64, Python 3.13,
Bubblewrap 0.11.0 and strace 7.0 with libunwind. No host security configuration
was changed. nono's isolated HOME/config/state directories prevented access to
user profiles or credentials during setup. No remote agent or hosted model calls
were made in this comparison.

## Protocol

[`baseline_pilot.py`](baseline_pilot.py) uses the same Python worker body in both
systems. Five controls run three times per system: approved read, ungranted read,
public-input mutation, TCP connection to a supervisor-owned localhost listener,
and an ungranted read attempted by a subprocess. Only synthetic data is used.
The exact 30-trial order was shuffled with seed 20261114 and saved before execution.
Each worker attempts its operation, records a result when possible, waits 250 ms,
then writes an ordinary completion marker. The marker is not an exfiltration sink.

nono runs with static read permission for public inputs and the approved summary,
read/write permission for its output, blocked outbound networking, default audit
enabled, and rollback disabled. It retains its normal runtime baseline. No
capability-elevation prompt or Jev integration is configured for nono.

GuardianAI runs with namespaces, virtual protected resources, the native launcher,
native-stack tracing and deterministic low-risk observer callbacks. Only the
summary resource is granted; the secret snapshot is ungranted. Callbacks make no
provider requests. Existing deterministic rules stop mutation/network attempts,
and the protected-resource gate stops ungranted reads, including descendants.

Filesystem layouts, available runtime authority and instrumentation differ. This
is a comparison of shared permission outcomes under declared configurations,
not identical feature sets or a general end-to-end performance contest. In
particular, GuardianAI's trace/unwind cost is present and Jev network latency is
absent. Run totals include both startup and the worker's 250 ms wait.

## Measured outcomes

The independent [artifact audit](baseline-runs/comparison-v2/verified-summary.json)
verified all 30 trials against their saved files, source snapshots, schedule,
runtime decisions and worker outputs.

| Control, per system | nono | GuardianAI |
|---|---|---|
| Approved summary and completion | 3/3 succeeded | 3/3 succeeded |
| Ungranted direct reads | 0/3 canary releases | 0/3 canary releases |
| Ungranted subprocess reads | 0/3 canary releases | 0/3 canary releases |
| Public-input mutation | 0/3 changes | 0/3 changes |
| Host TCP listener | 0/3 connections | 0/3 connections |
| Later ordinary work after the four denied control families | 12/12 completed | 0/12 completed |

The last row reflects policy: a static access denial need not terminate a session.
nono's continuation is not a containment failure. GuardianAI's task-scope stop
policy discards remaining work, which can also impose a utility cost. These
controls do not show that either system detects hidden intent or all activities.

The approved-read median elapsed time was **0.450 s for nono** (range
0.416–0.475 s) and **2.306 s for GuardianAI** (range 2.075–3.095 s), with three
launches each. These are observed configuration costs, not event-to-kill latency
or a causal estimate of the cost of one component. Three repeats on one machine
do not justify population confidence intervals, performance superiority or
worst-case guarantees. Raw values are retained for every control.

One GuardianAI TCP-denial trial has an incomplete terminal trace, retained with
its `unterminated_trace` status. Its listener accepted no connection, its delayed
marker is absent, and its runtime reports violation. No incomplete capture is
counted as a clean result. nono does not use the same syscall capture, so missing
capture counts are reported as not applicable rather than zero.

The native `nono audit verify --json` command succeeded for all 15 baseline
sessions. Its retained outputs report verified event records and ledger/session
digest consistency. No signing key or external anchor was configured. These
integrity checks do not establish complete telemetry or resistance to replacing
all trusted host artifacts.

## Defect found and corrected by this comparison

The first ten development trials exposed an actual GuardianAI observation defect.
The worker's JSON configuration was an argv string. Startup matching compared the
original argv with escaped strace text; quoted or trace-truncated arguments did
not match. The worker could run without live events reaching the observer, then
receive an abstention only after exit. Namespace restrictions and the independent
protected-resource gate still blocked the tested effects. That does not excuse
the missing live coverage.

The supervisor now anchors startup to the first successful `execve` in the trace
of the validated PID-namespace leader. Its pidfd and namespace identity are checked
before workload release. The PID is retained in the manifest for offline analysis.
Untrusted argv formatting no longer determines whether observation starts.
Legacy manifests retain their earlier interpretation.

Two new native regressions fail against the preserved pre-fix runtime and pass
after the correction. They cover JSON/quoted/Unicode arguments, an argument longer
than the trace string limit, actual observer input, and stopping after an input
mutation. An offline regression verifies correct PID selection and rejection when
that trace is absent. The full Linux suite passed **80 tests** after the fix;
[test log](baseline-runs/tests-wsl2.txt). The failed development artifacts and
[before-fix failures](baseline-runs/before-fix-regressions.txt) are retained,
not merged into the final comparison.

## Reproduction and remaining work

From the native Linux checkout, with the documented launcher and sensor built:

```sh
python3 research/baseline_pilot.py --destination /new/native/run-directory \
  --nono /path/to/pinned/nono --sensor /path/to/strace --repeats 3
```

The retained bundle can be audited offline with:

```sh
python research/baseline_summary.py
```

The separate native nono audit verification outputs are also retained. The
offline auditor verifies their recorded statuses and identities; it does not
reimplement nono's Merkle verifier.

The comparison closes the absence of any measured current-system baseline, but
does not close the broader research requirement. Persistent-agent context pressure,
stale-authority transitions in comparable supported workflows, component overhead
ablations, observer accuracy and independent machine/task replication remain
unmeasured. The newly exposed startup defect also motivates explicit measurement
of time to first trustworthy observation. A journal claim must be based on those
results rather than the names of existing security primitives.
