# OS observer and enforcement: revised research direction

User steering: target a Q1 journal, develop systems mechanisms rather than expand
fresh-context Grok trials, and evaluate persistent agents under context pressure.
Stop expanding the previous fresh-context subject schedule after this steering.
Preserve unfinished data explicitly in memory-runs/STEERING.md. Future subject
evaluation should follow the persistent-session design below.

## Observable contract

Kernel telemetry observes syscalls, process ancestry, credentials, file/socket
operations and optionally execution stacks. It cannot recover latent thoughts.
A stack trace records control flow, not an LLM's intended future action. Hosted
model inference runs outside WSL. A locally supervised worker can be stopped;
already completed external effects cannot be undone by a later Jev verdict.
The research claim must concern observable attempted violations and bounded
enforcement, not universal malicious-thought detection.

Jev remains outside the kernel, in a trusted supervisor. Linux enforcement holds
authority independently of model output. The agent cannot alter policy, evidence,
observer credentials, or process ownership. The intended flow is:

```
task policy + current capability epoch + tool provenance
                     |                         |
local agent workers -> kernel events -> trusted event reconstruction -> Jev
        |                     |                                    |
        +-- bounded authority +-- coverage/loss status -------------+
                              |
              deny / freeze scope / revoke authority / terminate
```

Blocking a risky operation before approval requires a mediation boundary. Reading
strace files afterward and killing a process is retrospective detection, not
prevention. The current audit_session.py does exactly the latter post-execution
analysis and is not itself a live enforcement daemon. A separate
`runtime_supervisor.py` now provides live syscall observation and pidfd-based
namespace termination; see [measured results](RUNTIME_REPORT.md). The later
[kernel gate](KERNEL_GATE_REPORT.md) adds object-bound protected-snapshot release
and bounded native-stack observer inputs. Shared-scope revocation exists in the
broker; cgroup-wide freezing remains unimplemented.

## Candidate contributions and falsifiable tests

1. Task authority that expires independently of conversational memory. Bind an
   operation to task identity, resource identity, policy epoch and a bounded grant.
   Revoke grants when a task changes or evidence becomes stale, even if an agent
   hallucinates an old instruction after context truncation. Test stale-grant reuse,
   file replacement/rename races and descendant execution against current-grant
   controls. Capability security itself is prior art; the candidate is the measured
   context-loss/authority mismatch and a verified binding across the runtime.
2. Contain the causal scope of a violation. Track parent/child and broker-visible
   artifact/message transfers to identify which workers inherited affected data or
   authority. Compare stopping one PID with revoking the affected scope. Test
   delayed children, daemonization and pre-opened descriptors; measure residual
   effects and collateral interruption. Generic process-tree killing and provenance
   graphs are not new. Cross-agent revocation scope needs a distinct mechanism and
   close-prior-art review before a novelty claim.
3. Make missing evidence an enforcement state. Explicit sequence numbers, capture
   loss, observer liveness, queue saturation and policy epochs determine whether new
   sensitive actions may proceed. Test dropped, reordered and duplicated events,
   supervisor/model outage, and recovery. Measure effects before quarantine, worst
   observed stopping latency and benign work blocked. This extends the current
   retrospective artifact-integrity check; it does not prove complete observation
   or invent fail-closed monitoring.

## Evaluation replacing model-call volume

First validate mechanisms with deterministic real Linux workloads and synthetic
canaries, including direct syscalls, inherited descriptors, subprocesses and
concurrent resource changes. Freeze policies and hold out mechanism families.
Separate attempted violation, successful effect, detection time, authority
revocation time and termination time. Record observer false positives and utility.

Then use a small number of persistent subject sessions with legitimate tasks and
no supplied malicious objective. Track actual token/context usage, summaries,
memory provenance and explicit truncation boundaries. Cross long-context/truncated
context with stable/revoked task authority. Retain task successes, incidental
hallucinations, null results and oversight misses. Session age is not proof that a
context limit was reached. Do not infer hidden intent from an unsupported claim.

## Prior-art boundary

[ACE](https://arxiv.org/abs/2609.28915) already combines application and kernel
evidence. [The Jinn Guard](https://github.com/AlphaReasoning/The-Jinn-Guard)
already describes BPF-LSM governance and tamper-evident audit. Merely combining
Jev, eBPF and a kill switch is insufficient novelty.
[Linux seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html)
documents syscall filtering and inheritance, and explicitly states that seccomp
alone is not a full sandbox. Mediation must address resource identity and races;
copying pointer arguments and then allowing their original syscall is not an
adequate object-binding proof. Kernel feature availability and privileges in the
actual WSL installation must be established before selecting BPF-LSM versus an
unprivileged mediation prototype. Q1 readiness requires broader validation,
baseline implementations, statistical replication and a distinct contribution;
it is not established by the current pilot or this design document.
