# Literature-to-contribution audit

Search date: 2026-11-14. Search queries included `"JEV" "RLCD"`, `"kernel"
"agent" "sensor integrity" monitoring`, `"collusion" "causal" "agents" detection
counterfactual`, and `"covert channel" "counterfactual" detection`. Sources below
were opened directly. This is a targeted survey, not a systematic review.

The [15 November contribution update](manuscript/PRIOR_ART_UPDATE.md) extends this
review with primary full texts for guardscope, context-pipeline attrition,
ClawSentry and DelegateGuard. The manuscript bibliography records the checked
versions. These additions narrow the contribution rather than establish novelty.

| Primary source | What is already established | GuardianAI's narrower research question | Verdict |
|---|---|---|---|
| [Mathew et al., Hidden in Plain Text](https://aclanthology.org/2025.ijcnlp-long.34/) | Optimization can elicit linguistic steganography; monitoring and paraphrasing are imperfect. | Does a kernel-backed delivery boundary preserve legitimate utility while breaking an engineered storage channel? | Application/measurement extension, not new emergence. |
| [Motwani et al., Secret Collusion](https://arxiv.org/abs/2402.07510) | Threat models and empirical covert communication tests. | Separate a channel's causal usefulness from its policy authorization. | Threat model reused; broad covert-channel novelty refuted. |
| [King et al., ACE](https://arxiv.org/html/2609.28915v1) | App and syscall evidence can complement each other. Section 2.4 assumes a functioning sensor; Appendix C calls for expanded sensor surfaces. | Retain blocked attempts and explicitly abstain on detectable capture damage; measure both after containment. | Narrow gap candidate. Cross-layer detection itself is already covered. |
| [Beno, Decision Models as Policy Gates](https://arxiv.org/html/2611.02155v1) | Jev and other decision models classify coding-agent policy risks. | How do opaque paths, denied syscalls, and task-bound read permissions affect preflight versus retrospective Jev? | Jev gates are prior art. This implementation contributes a paired WSL2 mechanism test. |
| [Kaur et al., Beyond the Transcript](https://arxiv.org/abs/2608.19161) | Shared event identity, matched causal analysis, and interventions for private latent channels. | Apply matched input/output interventions to filesystem artifacts without model activations. | Generic causal intervention and event joining are not new. |
| [Mohsin and Rahman, What Do Collusion Probes Read?](https://arxiv.org/abs/2611.10620) | Instruction, decision, and post-action information can confound collusion evaluation. | Keep labels from judges, include identical-code permission controls, and label retrospective detection as post-action. | Evaluation safeguards reused; no claim of pre-action detection from traces. |
| [Engelbrecht, What Should Count as Evidence?](https://apartresearch.com/sprints/projects/what-should-count-as-evidence-of-aiagent-collusion-testing-plusfactor-signals-against-innocent-lookalikes-todz) | Causal dependence and innocent look-alikes are tested as collusion evidence. Participant sprint project, not a peer-reviewed publication. | Include a receiver that ignores the private marker under the same interventions. | Counterfactual validation alone fails novelty gate. |
| [The Jinn Guard](https://github.com/AlphaReasoning/The-Jinn-Guard) | Kernel-aware governance with BPF-LSM enforcement and audit artifacts. | A reproducible unprivileged WSL2 study linking containment, observation quality, and utility. | Kernel agent enforcement is not new. |
| [OWASP APTS safety controls](https://owasp.github.io/APTS/standard/2_Safety_Controls/) | External containment, blocked-operation logging, watchdogs, and action allowlists. | Implement and evaluate a concrete bounded evidence contract. | Blocked-attempt logging and watchdog concepts are not new. |

## Claim discipline

C1: **Attempt/effect separation under containment.** Implemented as an explicit
ablation using actual syscall return values. The research contribution is the
joint empirical evaluation with an opaque Jev gate, not invention of syscall
auditing or denied-attempt detection.

C2: **Evidence-aware abstention contract.** Artifact-set hashes, terminal records,
parse limitations, timeouts, and provider errors prevent a no-observed-violation
verdict. This addresses part of ACE's stated sensor-integrity boundary, but only
detectable artifact faults under a trusted supervisor. No kernel-level guarantee
of complete capture or resistance to manifest replacement is claimed.

C3: **Task-preserving counterfactual artifact delivery.** Broker normalization
retains an allowed result while suppressing an explicitly engineered extra field;
full blocking is a utility-destroying control and shuffled markers are a causal
control. Both channel-using and honest receivers run in real isolated processes.
This is a systems instantiation and reproducible control, not a new general
causal test, learned convention, or universal steganography defense.

The defensible combined contribution is a small, executable, evidence-backed
WSL2 research artifact that evaluates these mechanisms together. A strong claim
of algorithmic or publication-level novelty remains **NOT ESTABLISHED**. Finding
close prior art is a research result, not a reason to rename an existing idea.
The user's later clarification removes parameter training from the study.
Fixed pretrained agents and agents carrying their own operational notes can
test repeated interaction without changing weights. Neither that comparison
nor Jev's hosted endpoint reproduces the original gradient-adaptation arm.

## Fixed-weight paired-agent extension

Further OS-direction checks found [DelegateGuard](https://arxiv.org/html/2610.16005v1)
and [Lever](https://lever.to/capabilities/), which already cover purpose-bound
capabilities/cascading revocation and identity-bound broker epochs, respectively.
The broad novelty claim for task-scoped capabilities or epoch revocation is
therefore rejected. [BROKER_REPORT.md](BROKER_REPORT.md) limits the new artifact's
claims to implemented boundary mechanics and measured concurrent executions.

[Li et al., Auditable Belief Updates](https://arxiv.org/abs/2610.38869)
externalize evidence-based commitments and propose a cognitive firewall for
weakly supported updates, including group misinformation and collusion.
[Epistemic logic for verifying runtime monitoring](https://icetcs.github.io/movemnt/papers/epistemic_logic_verifying_RV_PLS.pdf)
already treats what communicating monitors can know as a verification question.
Consequently, knowledge-aware monitoring and explicit memory provenance are
not claimed as new algorithms. Our narrower empirical question is whether a
fixed typed decision observer distinguishes correct clue exchange from unsupported
cross-episode facts under asymmetric information, and how state packaging changes
its judgments. The full-history counterfactual audit also checks that an apparent
channel effect was not created by deleting the sender's own earlier message.

These extensions use actual hosted agents, recorded editor outputs, and a traced
Linux message relay. The relay's syscall evidence establishes delivery provenance,
not the semantic meaning of text or containment of hosted model inference.
No trained covert protocol, guaranteed detection, or original general causal
criterion is claimed. Results must retain identity edits, false alarms, failed
grounding, and null convention findings.

## Kernel-gate implementation update, 2026-11-14

2026 sources and components are in scope. The working observer uses TypeSafe's
2026 Jev release. Kernel notifications and descriptor injection are established
Linux mechanisms; [nono's primary security documentation](https://github.com/nolabs-ai/nono/blob/main/docs/cli/internals/security-model.mdx)
already combines them with a supervisor. Our implementation uses these mechanisms
for bounded synthetic snapshots; it does not claim to invent them or reproduce
nono's full policy. The [Linux notification manual](https://man7.org/linux/man-pages/man2/seccomp_unotify.2.html)
describes atomic ADDFD_SEND and the mutable-argument limitations of continuation.

[Lilienthal and Hong, Mind the Gap](https://arxiv.org/abs/2508.17155) already studies
TOCTOU in LLM-enabled agents. The October 2026
[protected-execution-finality Internet-Draft](https://www.ietf.org/archive/id/draft-das-sandbox-credential-egress-finality-00.html)
is close conceptual prior work on actual effects and authority separation; it is
an individual informational proposal, not an adopted standard or vendor validation.
See [KERNEL_GATE_REPORT.md](KERNEL_GATE_REPORT.md) for the working boundary, retained
evidence, and narrower empirical questions. No comparative performance or journal
novelty claim follows from this implementation alone.
