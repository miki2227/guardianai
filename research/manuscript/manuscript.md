# When Kernel Denial Is Not Task Revocation: Evidence-Grounded Supervision of Agent Workloads

Research draft, 15 November 2026. Submission readiness and unresolved contribution claims are listed in [SUBMISSION_STATUS.md](SUBMISSION_STATUS.md).

## Abstract

An agent supervisor must distinguish a prohibited operation being denied from the worker's remaining authority being revoked. We present GuardianAI, a working Linux/WSL2 runtime that combines namespace containment, kernel notifications, a pretrained structured-decision observer and a protected-resource release broker. The broker checks task, principal, resource identity, epoch and shared stop state at an atomic descriptor-release boundary. Retained controlled executions expose two failures in earlier revisions: a protected descriptor can be committed after a denied operation while retrospective observation is pending, and a worker-installed filter can suppress the notification needed for immediate revocation. Subsequent revisions prevent the tested sequences. Ordinary compiler and packaging workloads expose different operational failures: cumulative observer inputs exceed the provider's context limit, and ambiguous shared-state representations produce a false alarm. Bounded event streaming and explicit errno, grant and namespace facts support completed real build sessions, while their limitations remain visible in state receipts. These results establish an executable artifact and bounded implementation evidence. They do not establish universal malicious-intent detection, spontaneous agent collusion, natural agent context-window effects or publication-level algorithmic novelty.

## 1. Introduction

The security consequence of an agent action depends on more than a classifier's label. A sandbox may reject one syscall while leaving the worker authorized to retrieve other data. A monitor may eventually flag the attempt after that data has already been delivered. A structured decision model can return a well-formed answer while evaluating incomplete or misleading state. These are different boundaries, and treating them as one safety outcome obscures both failure and successful containment.

GuardianAI was developed to support agent workloads under an independent observer without training the working models. Its enforcement target is local Linux execution through WSL2. Hosted model inference remains outside that process tree. The runtime can observe native execution evidence, withhold provisioned resources and terminate supervised local namespaces. It cannot read unexpressed model thoughts. Different latent intentions that produce the same available evidence are observationally indistinguishable to this monitor.

The resulting research questions are narrower and testable. First, when can operation denial precede a later protected-resource release? Second, what assumptions are required for a notification-driven scope stop? Third, can the implemented observer remain operational during useful compiler and packaging work? Fourth, what evidence actually supports claims about persistent agent context?

The present artifact contributes an integrated runtime and evidence collection, rather than a claim to have invented its underlying security primitives. Its findings separate attempted operations, scope stopping, descriptor commitment and completed output; preserve notification-suppression counterexamples and their corrections; and expose practical observer-state failures during real application work. The study retains negative outcomes and distinguishes scripted mechanism controls, actual model replies and ordinary software workloads. A broader novelty claim remains a research requirement rather than a conclusion.

## 2. Related work and scope of contribution

King et al.'s Agent Cross-Layer Evidence work studies how application telemetry and syscall evidence complement one another for agent security. That establishes close prior work for cross-layer observation. GuardianAI's current evidence concerns the execution boundary between observation, scope revocation and resource release; it does not reproduce ACE's corpus or establish superior detection. [ACE](https://arxiv.org/abs/2609.28915).

nono already provides a trusted supervisor with capability restrictions and Linux notification-based delegation. Its documented file-descriptor injection and audit model prevent claiming those mechanisms as new. We execute a pinned nono release as a limited baseline under declared configuration differences. Findings about GuardianAI's earlier revisions are not findings about nono. [nono v0.81.0 security model](https://github.com/nolabs-ai/nono/blob/v0.81.0/docs/cli/internals/security-model.mdx).

Lilienthal and Hong study time-of-check to time-of-use vulnerabilities in LLM-enabled agents and countermeasures including state integrity and tool fusion. Agent TOCTOU is therefore established prior work. Our narrower implementation argument concerns revalidation of immutable resource identity and current authority immediately before an atomic descriptor commitment. [Mind the Gap](https://arxiv.org/abs/2508.17155).

Motwani et al. study secret collusion through steganographic capabilities, while Mathew et al. investigate emergence and mitigation through optimization-based and in-context approaches. These works motivate examining information exchange, but neither an engineered channel nor an unsupported agent statement proves an emergent covert convention. The historical GuardianAI subjects receive no supplied covert protocol, and the retained pilot establishes no such convention. [Secret Collusion](https://arxiv.org/abs/2402.07510), [Hidden in Plain Text](https://aclanthology.org/2025.ijcnlp-long.34/).

Jev is the independent pretrained decision observer. The provider defines RLCD as Reinforcement Learning for Calibrated Decisions and exposes typed probabilistic decisions. RLCD is the provider's training method, not a separately implemented kernel mechanism in this artifact. Well-formed output does not establish correct judgments or adversarial immunity; our operational false alarm is direct evidence of that distinction. [TypeSafe introduction](https://typesafe.ai/blog/introducing-system-one-models-and-jev).

Recent work further narrows the contribution. guardscope reconciles runtime-control records with kernel events to measure coverage, while distinguishing coverage from security effectiveness. Context Is a Pipeline, Not a Window measures evidence lost before model delivery, including loss with spare window capacity. Consequently, neither kernel coverage auditing nor context-delivery measurement is a new general claim here. [guardscope](https://arxiv.org/html/2611.15223v1), [Context Is a Pipeline](https://arxiv.org/html/2610.36114v1).

ClawSentry already combines external supervision, session memory of denied effects and post-action feedback. DelegateGuard supplies purpose-bound capabilities and cascading revocation, with explicit limitations for trusted adapters and legitimate observable sinks. These systems preclude broad novelty claims for session-aware observers or task-scoped revocation. [ClawSentry](https://arxiv.org/html/2608.21101v1), [DelegateGuard](https://arxiv.org/html/2610.16005v1).

The survey is targeted rather than systematic. Existing mechanisms and close systems materially limit the novelty claim. The currently supported contribution is an executable integration with measured boundary failures and operational evidence. Establishing that its combined findings merit a journal contribution requires further comparison and independent review. The [contribution update](PRIOR_ART_UPDATE.md) states candidate questions, rejection criteria and the unresolved real-agent integration boundary.

## 3. Threat model and observable contract

The untrusted workload is a declared local worker and its descendants. A trusted host manifest fixes the task, worker identities, public input mounts, output directories and protected-resource grants before launch. Multiple workers may share read-only public inputs; their outputs are disjoint. Worker conversational memory cannot change these host grants.

The trusted computing base includes the host kernel, namespace launcher, tracing and parsing components, supervisor, release broker and provisioned policy. The remote observer is a decision service whose availability and correctness are not assumed perfect. Provider failures cause abstention; they are not converted into approvals. A host adversary able to replace both evidence and its hash manifest is outside the integrity claim.

Protected resources are bounded immutable byte snapshots retained outside worker mounts. Ordinary public files are already readable inside the sandbox and do not receive per-read semantic authorization. A copy of private data mistakenly placed in a public mount is therefore outside the protected-resource guarantee. Path validation also cannot prove the absence of exposed duplicates or hard links.

The model observes scoped execution evidence. Native stack frames describe user-space control flow, not model activations, Python logical tracebacks or unexpressed intentions. The supervisor stops its declared local workers; it cannot terminate an external provider's inference session. Unknown lost events, kernel exploitation, resource-exhaustion attacks and general covert-channel suppression are not covered by demonstrated guarantees.

## 4. System design

### 4.1 Containment, observation and local termination

Each worker starts under Bubblewrap with separate namespaces, read-only public inputs, separate writable output and private scratch storage. The workload is held before release while the supervisor validates the PID-namespace leader and opens a stable pidfd. Terminating that leader terminates namespace members under Linux semantics. This avoids relying on a later lookup of a potentially reused PID. [PID namespace semantics](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html).

Strace follows relevant syscall families and collects bounded native unwinds. The supervisor parses scoped file, network and process-inspection activity. Local event indices remain stable across later frame updates. Frozen event inputs and their hashes identify what was submitted to the observer. A recorded capture status means that the retained artifact set and terminal-record checks pass; it does not prove complete telemetry.

An early real comparison exposed a startup-recognition error: escaped JSON argv and trace-truncated strings could prevent a textual argv match. Containment remained active while live observation was skipped. Startup is now anchored to the first successful execution in the validated leader's trace. The failed development runs remain separate from the corrected comparison.

### 4.2 Protected-resource release

A trusted native helper installs the notification filter and transfers its listener through a private channel before executing the ordinary worker. The channel and observer credential are not delegated to the workload. Absolute opens of `/protected/NAME` are virtual resource requests; no backing private file exists in that namespace.

The gate binds a request to its launch-assigned principal, task epoch, resource identifier, immutable content digest and kernel notification identity. Jev evaluates the task and metadata, not the resource's contents. After the answer returns, the broker revalidates authority under its commit lock. An approved request receives a read-only sealed snapshot descriptor through atomic `ADDFD_SEND`; the original mutable pathname syscall is not continued for the protected release. Linux documents both this atomic facility and the hazards of pointer-based continuation. [Notification manual](https://man7.org/linux/man-pages/man2/seccomp_unotify.2.html).

This is a narrow virtual interface for bounded opens, not a complete virtual filesystem. Directory enumeration, `stat` and relative virtual opens are not emulated. Already committed descriptors and previously disclosed knowledge cannot be retracted.

### 4.3 Scope stopping and filter integrity

Earlier revisions depended on retrospective traces to turn a prohibited attempt into scope stopping. Policy 2 moved `ptrace` and `connect` into the notification path. The supervisor stops shared authority before returning the denial. Other workers' pending approvals recheck that same stop state before commitment.

The next correction addresses filter stacking. A worker-installed `ERRNO` action can suppress a lower-precedence notification while preserving operation denial. Policy 3 therefore intercepts filter-changing calls through both Linux installation interfaces. Supported seccomp queries and unrelated `prctl` operations remain available. This uses established Linux filter semantics. [Seccomp filter documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html).

Policy 3 has a compatibility cost: applications requiring their own seccomp sandbox are outside this runtime profile. It also does not establish notification coverage under arbitrary pre-existing host filters or every unsupported syscall/ABI surface. The gate rejects incompatible helper versions before launch.

### 4.4 Bounded shared observer state

Cumulative native-event history eventually exceeded the remote observer's context limit during ordinary build work. The runtime now submits event batches capped at 8 KiB while retaining full local evidence. Later frame revisions remain pending until submitted. This is not a token-capacity guarantee for arbitrary task text.

The shared session observer adds protected grants, namespace facts, activity counts, up to 32 recent event summaries and eight recent broker records. Shared context is capped at 6 KiB and serialized state at 20 KiB. Older detail can roll out, with explicit omission counts; unique-event bookkeeping is bounded at 8,192 identities. Budget exhaustion causes abstention. Hashed state/decision receipts join runtime and release judgments to their supplied context.

The representation distinguishes ordinary failed lookups from permission errors using errno. It also distinguishes protected grants from normal public/runtime access and identifies worker-local output views. These are host-grounded facts, not learned hidden protocols. Recent receipt order is not a claim of causal ordering or complete long-term memory.

## 5. Conditional implementation arguments

These arguments describe the implemented control structure under its trusted-component assumptions. They are not a mechanized verification of Python, Linux or the whole deployed system.

Let `S` be the terminal scope-stop state, `E` the current epoch, `G[p]` the grants for principal `p`, and `B[r]` the immutable resource snapshot. A request records epoch `e`, resource `r` and digest `d`. The observer returns probability `q`. Commitment requires valid finite `q < 0.5`, elapsed authorization time no greater than two seconds, `e = E`, `r` in `G[p]`, healthy evidence, `S = false`, and the unchanged snapshot digest. These conditions are rechecked under the same lock used by scope stopping.

**Terminal-stop ordering.** Once `ScopeStop.set()` returns, an authorization that subsequently acquires the commit lock cannot pass the current-state predicate. If commitment already owns the lock, stopping waits and the commitment precedes completed revocation. That is a linearization boundary, not a promise to retract prior data or instantly stop every process. Clearing the terminal stop state is rejected; a new task scope requires a new broker.

**Snapshot binding.** Replacing a task or resource increments the epoch. A pending old-epoch decision cannot authorize the new state. An approved resource is committed from the immutable snapshot whose digest was checked, so a later host pathname replacement cannot substitute different bytes through that commitment. Mutable worker pointers do not select a different backing host path after approval. Already injected descriptors remain an explicit residual.

**Observation does not reveal intention.** If two executions expose identical available evidence and differ only in latent intention, the observer receives the same state for both. No classifier operating solely on that state can universally distinguish the two latent labels. The operational claim must therefore concern observable policy violations and enforceable authority, not all malicious thoughts.

The two-second authorization validity rule is also not a hard real-time supervisor-exit bound. A remote HTTP call can remain outstanding after a local worker is stopped. Provider failures, parser limitations and unknown event loss remain separate from the lock-order argument.

## 6. Evidence and results

### 6.1 Environment and evidence classes

The retained native studies use Kali WSL2, Linux 6.6.87.2-microsoft-standard-WSL2 on x86-64, Python 3.13, Bubblewrap 0.11.0 and strace 7.0 with libunwind. Observer calls pin `jev-1.14.0`. Controlled native probes, ordinary compiler workloads and hosted subject replies are reported separately. Observer callbacks in scripted mechanism probes are fixtures unless explicitly identified as provider-backed.

The datasets below come from existing retained runs. No additional probe suites or model-agent subjects were launched to prepare this manuscript. Counts from versioned revisions are not presented as validation of later revisions.

### 6.2 Denial can precede protected release

The 36-worker ordering block runs approved reads and prohibited-call/read sequences with and without native unwinding. Each listed cell has three repetitions.

| Revision and tracing | Prior call | Descriptor commits | Canary prints |
|---|---|---:|---:|
| Original, native unwinding | `ptrace` | 2/3 | 1/3 |
| Original, native unwinding | `connect` | 0/3 | 0/3 |
| Original, no native unwinding | `ptrace` | 3/3 | 3/3 |
| Original, no native unwinding | `connect` | 3/3 | 3/3 |
| Policy 2, native unwinding | `ptrace` | 0/3 | 0/3 |
| Policy 2, native unwinding | `connect` | 0/3 | 0/3 |
| Policy 2, no native unwinding | `ptrace` | 0/3 | 0/3 |
| Policy 2, no native unwinding | `connect` | 0/3 | 0/3 |

All approved-read controls commit and print in each configuration. Commitment and printing are different outcomes: a delegated descriptor remains a release even if termination prevents later output. These small scheduling samples do not estimate general failure probabilities or the effect of unwinding in a population. [Ordering evidence](../release-order-runs/verified-summary.json).

### 6.3 Operation denial can suppress the revocation signal

The filter-stacking block contains 21 workers: six policy-2 masking cases, twelve policy-3 masking cases across two tracing modes, and three query controls. Policy 2 permits all six filters to install; all six then receive and print the synthetic protected summary. Policy 3 permits none of the twelve tested installations or subsequent protected releases. The three query controls retain their approved utility. The result concerns GuardianAI's revisions and known installation interfaces, not a flaw in another system or universal syscall coverage. [Filter-stacking evidence](../filter-stack-runs/verified-summary.json).

### 6.4 Current-system baseline

A pinned nono 0.81.0 release runs on the same WSL2 installation. The retained comparison contains 30 workers: five permission controls, three repetitions and two configurations. Both configurations allow their approved reads and block the tested ungranted direct/subprocess reads, public-input changes and connection attempts. nono allows ordinary later work after access denial; GuardianAI stops its task scope. Continuation under the configured static baseline is not a containment failure.

For the approved-read control, median launch-to-completion time is 0.450 s for nono and 2.306 s for GuardianAI, with three launches each. Instrumentation and authority models differ: GuardianAI includes native unwinding and fixture observers; nono uses static grants and its default audit. A 250 ms worker wait is included. These are configuration costs, not isolated component overhead, Jev latency or an overall security ranking. Fifteen native nono audit verifications succeed. One GuardianAI TCP-denial capture is incomplete and remains labelled as such. [Baseline evidence](../baseline-runs/comparison-v2/verified-summary.json).

### 6.5 Actual application work

The initial real build terminates with an abstention on an HTTP error. Replaying its final observer input returns `max_tokens_exceeded`. That event snapshot is 64,749 serialized bytes; no token count or full HTTP-body size is inferred from it. TypeSafe documents separate request/question context limits and this rejection. [Model limits](https://docs.typesafe.ai/models), [request errors](https://docs.typesafe.ai/api/errors).

After bounded streaming, ordinary GCC compilation and packaging complete under live Jev. The packaged runtime then rebuilds itself outside the development checkout. Both workers exit 0 with recorded captures. Shared-session integration subsequently completes concurrent build and source-index work, including an authorized previous-release manifest read by the indexer.

The first shared-context integration nevertheless produces a false alarm at 0.54 after the compiler has completed. That run remains a reported violation, not a prevention success. A combined representation update adds errno distinctions and explicit namespace/grant facts. A subsequent real session completes both jobs. Its 36 shared-state receipts include 35 runtime batches joined to retained native inputs; 32 contain observed activity from both workers and 34 contain broker history. The largest state is 15,323 bytes. The representation changes and execution timing are not isolated, so this sequence does not establish improved classifier accuracy. [Real build evidence](../system-runs/build-summary.json), [shared-session work](../system-runs/shared-session-summary.json), [shared-context evidence](../system-runs/shared-context-build/observer-summary.json).

### 6.6 Agent context remains unmeasured

The corrected historical social block contains 16 sender/receiver exchanges from two logical subjects. All dispatch records declare fresh contexts and none exposes token usage. Requested configuration is Grok 4.7 with low effort; the retained metadata does not expose a separate resolved executed-model pin. Own-note prompting is not evidence of a naturally retained, growing provider window. No covert convention is established in that pilot.

The context recorder verifies message/run/subject joins and preserves unknown measurements. Logical thread age, turn count and checkpoint records do not establish token occupancy or compaction. The observed Jev request overflow is an observer-capacity event, not evidence that a working Grok subject exceeded its context window. [Context import](../context-records/import-v2/summary.json), [context measurement report](../CONTEXT_MEASUREMENT_REPORT.md).

## 7. Limitations and publication implications

The strongest evidence is for specific implementation boundaries and real operation, not detection quality. Scripted probes deliberately exercise known mechanisms; ordinary builds contain no supplied malicious objective. Neither provides representative malicious-agent ground truth. There is no independently replicated long-horizon study, unseen model-family transfer, blinded labeling, general recall estimate or population-level uncertainty analysis.

The tested machine, policies and source revisions differ across development stages. Earlier baseline timings cannot be reused as performance measurements for the later shared observer. Historical test counts likewise belong to their revisions: the 92-test result precedes streaming/shared-context changes. The latter changes have real-workload execution evidence, not a claimed rerun of that complete suite.

Observed false alarms, incomplete captures and provider failures remain material. File hashes depend on the trusted host and are not external attestation. Recent shared context can omit older details, public mounts remain readable, and general within-authority data misuse is not prevented. Filter restrictions exclude legitimate applications needing additional sandboxes. Namespace termination does not recall data or stop hosted inference.

These limitations also define the remaining contribution gate. A defensible journal submission needs a sharper distinction from existing supervisor architectures and a stronger empirical basis for the intended persistent-agent claim. Q1 suitability cannot be established by assembling known primitives, passing implementation checks or producing an archive. The working artifact provides a concrete basis for that assessment without presenting the missing evidence as completed.

## 8. Conclusion

GuardianAI demonstrates that operation denial, observable violation, task revocation and data release require separate evidence. Its retained revisions expose delayed revocation and notification suppression, then implement bounded corrections. Real compilation and packaging expose observer context and representation failures that scripted controls alone did not reveal. The current runtime supports shared supervision, protected releases and bounded shared-state receipts. Universal intent detection, natural agent context-pressure effects and publication-level novelty remain unestablished.

## Artifact access

The current [core runtime archive](../../dist/GuardianAI-linux-x86_64.zip), [session instructions](../../SESSION.md), [claim ledger](claim-evidence.json) and [submission status](SUBMISSION_STATUS.md) accompany this draft. The artifact includes source and per-file hashes. Subsequent [final-drain work](../FINAL_DRAIN_REPORT.md), an [existing Grok coding-agent integration](../CODING_AGENT_RUN.md) and [supervisor-lifetime work](../OWNER_LIFETIME_RUN.md) are recorded separately from this manuscript's evaluation blocks; their results are not attributed to those later revisions. The coding-agent integration provides usage records and a completed build/review, with retained failures, but no context-saturation finding. External sources are linked at their associated claims; related-work verification details are in [references.md](references.md).
