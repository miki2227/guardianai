# Contribution and integration update

Checked 15 November 2026 against primary preprints. This extends the targeted review; it is not a systematic search or evidence that an unmentioned mechanism is novel. No new workers, agent subjects or model requests were run for this update.

## Close work that changes the contribution boundary

| Primary source and inspected scope | Consequence for GuardianAI |
|---|---|
| Toyoda, Leung and U, [guardscope, v1](https://arxiv.org/html/2611.15223v1), sections 3–6. Measures control coverage by reconciling decision records with kernel events. Its exercised workload covers four of fifteen analyzed paths; coverage and security effectiveness are distinct. | Kernel-based coverage auditing is prior art. Our scoped traces do not justify a claim to cover every action path. A denied operation, later descriptor commitment and completed output remain separate local outcomes. |
| Sehgal, Panahandeh and Ezzati-Jivan, [Context Is a Pipeline, Not a Window, v1](https://arxiv.org/html/2610.36114v1), sections III–VI. Measures destructive tool-result delivery, including losses with spare context capacity; controlled results distinguish additional work from answer accuracy. | Evidence truncation and context delivery are prior research topics. Our observer overflow is a different recorded event from worker context exhaustion. State receipts establish supplied state, not everything the provider retained or used. |
| Wang et al., [ClawSentry, v1](https://arxiv.org/html/2608.21101v1), sections 3, 5–6 and 9. Combines package review, invocation mediation, session memory of denied effects and non-retroactive consequence feedback through a harness protocol. | External observers, session-aware decisions and follow-up detection are prior art. GuardianAI must distinguish its local execution/release boundary and measured failure mechanisms; adding another reviewer tier alone would not establish novelty. |
| Tran-Truong et al., [DelegateGuard, v1](https://arxiv.org/html/2610.16005v1), sections 3–6. Purpose-bound capabilities include cascading revocation. The paper explicitly retains trusted-adapter and observable-legitimate-sink limitations. | Task grants, revocation lineage and the need for content-aware sink controls are prior art. Our epoch/lock implementation is not a new capability theory, and stopping later releases cannot recall data already released. |

These are reported contributions and stated boundaries of the cited versions, not reproduced results. They do not establish that the other systems exhibit GuardianAI's earlier defects.

## Candidates worth developing, with rejection criteria

The following are research questions, not newly established contributions. The implementation and retained executions make them concrete enough to evaluate without building unrelated features.

1. **The interval between denial and terminal revocation.** Connect syscall return, shared-stop transition, descriptor commitment and actual output for a useful workflow. Existing evidence shows this distinction in GuardianAI's earlier revisions. A publishable extension would need to establish where the distinction changes a real workflow's authority outcome. Reject a generality claim if the result depends only on our deliberately weak earlier implementation or changes configured policy between systems.
2. **Observer state as part of the security boundary.** Inspect the exact events, permission facts and namespace facts available when a live decision or protected release occurs. The retained false alarm and provider error motivate this question. Reject an accuracy-improvement claim if representation changes, task timing and available evidence change together, as in the current development sequence.
3. **Authority surviving agent memory loss.** Keep host grants and revocation state independent of conversational notes while an agent performs useful work. This is an evaluation hypothesis about an existing boundary, not a new memory or capability mechanism. Reject a natural-context-pressure claim when retained context, resets or compaction are unknown. A manually shortened history must be labelled as an intervention.

None currently passes the publication-level novelty gate. The strongest available evidence supports a bounded systems case study of observed failures and corrections. Rebranding these questions as named algorithms would not resolve the gap.

## Next real-workflow integration

The current package supervises local Linux commands and their descendants. A compiler building the package is useful product operation; it is not a persistent model agent. The next integration requires the actual agent command and legitimate repository task, rather than another population of short subject calls.

The existing profile has no worker network access and clears the child environment. A hosted coding agent generally needs model transport. Giving that worker unrestricted network access or the observer credential would change the current boundary. The concrete choice therefore depends on its interface: keep model transport in the trusted host and supervise its local tool execution, or explicitly implement and document narrowly mediated transport. A command that assumes unrestricted connectivity cannot simply be dropped into the present manifest and called integrated.

Before interpreting a run, retain the task authorization, source revision, worker manifest, requested and resolved model identity where exposed, and the actual reset/compaction declarations. Provider usage and capacity should be recorded when available. Missing fields remain unknown; a running token total across calls is not retained-window occupancy.

Run that agent on its useful task under the existing supervisor. Inspect task output together with native traces, observer input receipts, stop state and release history. Preserve ordinary failures and null findings. Do not insert a hidden malicious objective, force a covert protocol or manufacture context pressure and then report it as spontaneous behavior.

**Subsequent integration:** after the user selected an existing coding agent, the installed Grok CLI was discovered and integrated with a Linux MCP command adapter. Its [real build/review run](../CODING_AGENT_RUN.md) includes per-message usage, retained failures and an incomplete closure record. The workflow-selection blocker is resolved; context saturation and publication-level novelty remain unestablished. This later run is separate from the original manuscript evaluation blocks.
