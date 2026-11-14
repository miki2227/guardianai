# GuardianAI: initial scope and research gates

The core study uses two actual pretrained language-model subjects communicating
over a mediated message channel while Jev independently observes. Ordinary tasks
and partial information may produce unintended errors, disclosure, or candidate
coordination patterns; none is assumed or explicitly assigned. There is no model
training, following the user's clarification. See the
[paired protocol](research/PAIRED_PROTOCOL.md) and [results](research/PAIRED_REPORT.md).
The [social report](research/SOCIAL_REPORT.md) records the corrected fixed/history
comparison and Jev observer diagnostics; the [reference audit](research/REFERENCE_AUDIT.md)
checks the supplied bibliography against primary records.
The Linux command launcher and previous scripted tests are supporting containment
and measurement infrastructure, not substitutes for the paired interaction.

## Architecture

Trusted supervisor -> Jev preflight probability -> local threshold -> Bubblewrap
-> isolated command and descendants. Jev is called over HTTPS from user space;
no inference runs in the kernel. Linux namespaces, mounts, and capability removal
enforce containment even if the classifier misses malicious command text. RLCD
is TypeSafe's training method, not a kernel interface or an algorithm reproduced
by this project. The 0.2 decision threshold is a provisional experimental choice.

The current gate sees only task text and argv. It cannot inspect a script loaded
later, prove intent, or observe every syscall. Failure to load the sandbox or
obtain a valid pinned-model answer refuses execution. There is no unrestricted
fallback. The supported `execute` path removes the supervisor environment, isolates
stdin, and closes descriptors above stderr. Standard output/error remain output
channels. The low-level `sandbox_argv` helper only builds arguments; a caller that
explicitly inherits host descriptors can expose their contents inside the sandbox.
Use `execute` for containment launches. Output is untrusted and must never be
treated as commands.

## Threat model and limits

Use an unprivileged Linux account and a dedicated disposable task directory with
synthetic data. The supervisor, workspace provisioning, runtime installation,
Bubblewrap, and host kernel are trusted. Give different agents different task
directories; sharing a directory permits storage-based communication. Read-only
/usr, /bin, /lib, and /lib64 are exposed as runtime dependencies; they must not
contain secrets. Inputs at /workspace are read-only. The trusted supervisor must
provision a separate, empty output directory mounted at /output, with no overlapping
input/output paths after symlink resolution. The agent can create and destroy any
file in /output and use private /tmp. Namespace isolation removes external networking
and host filesystem visibility; it does not classify the meaning of output.

Not covered: kernel exploits, resource exhaustion, timing/resource covert channels,
semantic collusion through allowed outputs, malicious files later published by a
human, workspace mount replacement by another host process, or privileged agents.
No seccomp filter, cgroup resource budget, authenticated remote event log, or
per-action capability broker exists yet. The research extension adds process-tree
strace capture, trusted-manifest validation, conservative abstention, and matched
two-program artifact provenance controls; see [the report](research/REPORT.md).
The Python execute function directly exercises containment for tests; the CLI is
the entry point which requires the Jev gate. Agents must not control the supervisor.

## Prior art checked 2026-11-14

- TypeSafe's [launch announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
  names RLCD; [official docs](https://docs.typesafe.ai/introduction) describe typed
  decisions. The client request/response shape was checked against the live
  [OpenAPI specification](https://api.typesafe.ai/openapi.json).
- [Decision Models as Policy Gates for Coding Agents](https://arxiv.org/abs/2611.02155)
  already evaluates Jev for policy classification. Jev guardrails alone are not new.
- [On the Effectiveness of Kernel-Level Evidence for Agent Security](https://arxiv.org/abs/2609.28915)
  already combines application telemetry and kernel traces. Cross-layer detection
  alone is not new.
- [The Jinn Guard](https://github.com/AlphaReasoning/The-Jinn-Guard) describes BPF-LSM
  enforcement and policy checks. Kernel enforcement alone is not new.
- [Bubblewrap](https://github.com/containers/bubblewrap) supplies the isolation here;
  [Linux Landlock documentation](https://docs.kernel.org/userspace-api/landlock.html)
  describes another kernel mechanism. Neither is an original GuardianAI invention.

These are preliminary primary-source checks, not an exhaustive novelty review.
The attachment's individual references have not all been independently verified.

## Candidate research contributions: unproven

1. Bind approved task capabilities to causal kernel events across two agents.
   Test whether joint event histories reveal forbidden coordination missed by
   isolated per-agent monitors. Compare kernel-only, task-only, and joined evidence.
2. Explicitly represent missing evidence, dropped events, model outage, and
   ambiguous probabilities as abstention. Measure missed violations and legitimate
   task completion rather than treating unavailable telemetry as benign.
3. Adapt the attachment's counterfactual convention validation to execution traces:
   disrupt a suspected shared-storage or timing feature while holding legitimate
   task information fixed. Test causal coordination effects with matched controls.

To claim novelty, find the closest prior implementation for each idea, demonstrate
a distinct mechanism, and evaluate held-out attack families and benign workloads.
Two prompted adversarial agents are a pilot, not proof of emergent collusion,
RL training, calibration, novelty, or universal coverage. Retain bypasses and failed
defenses as findings. Detection, containment, and task success are separate outcomes.

See [initial adversarial assessment](evidence/ASSESSMENT.md) for a real controlled
failure in the initial writable-workspace version: an allowed opaque script deleted
an unrelated fake input canary. The current version mounts inputs read-only and
requires a separate empty output directory. This prevents that input deletion
independently of Jev's decision, without detecting the script's intent. The raw
pilot reports and their runners describe the earlier API and policy.

Linux through WSL2 is the confirmed initial target. TypeSafe's launch post names
RLCD as Reinforcement Learning for Calibrated Decisions and Jev after William
Stanley Jevons. Type-safe responses do not establish correctness or immunity to
adversarial states. Our opaque-script failure demonstrated missing evidence;
it did not demonstrate a successful prompt injection against Jev.
