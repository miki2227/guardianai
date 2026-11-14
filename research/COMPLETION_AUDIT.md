# Research scope and completion audit

The goal is a reproducible study of two fixed pretrained agents under Jev
observation, grounded in the literature. A guaranteed detector for every possible
malicious activity cannot be established by a finite experiment. A research result
can instead measure specific observation failures, false alarms, utility costs,
and limits under an explicit threat model.

| Requirement | Artifact / current boundary |
|---|---|
| Jev as independent observer | `observer.py`, `social_experiment.py`; live pinned-model decisions retained |
| Linux through WSL2 | `guardian.py`, `monitor.py`; actual namespaces and syscall traces |
| Two real pretrained subjects | Five handoff episodes; eight corrected social episodes; development runs retained separately |
| No subject weight training | Fresh contexts plus optional own operational notes; no parameter-adaptation arm |
| No supplied covert code or malicious objective | Exact prompts retained; ordinary tasks, partial clues, game incentives |
| Fixed versus contextual interaction | Four matched cases per condition; one model pair, fixed delivery schedule |
| No-communication controls and actual editing | Empty-message controls; eight real editor outputs, including one identity edit |
| Closed-loop feedback | Task outcomes and public flags feed own-history condition; observer rules fixed in this pilot |
| Counterfactual convention validity | `convention.py` rejects unmatched exposed state and destructive semantic controls; no convention established |
| Memory-provenance ablation | Six-case, six-condition held-out protocol and saved randomized schedule; results must be retained including null effects |
| Observer-state ablation | Sixteen raw messages rejudged with frozen role-aware packaging; historical scores and rewards preserved |
| Literature novelty audit | `LITERATURE.md`, `REFERENCE_AUDIT.md`; close prior art prevents broad novelty claims |
| Reproducible evidence | Prompts, replies, provider metadata, observer scores, relay hashes/manifests, independent fact audit, source package |

The eight-episode social block is a pilot. Long-horizon emergence, adaptive
referee recalibration, independently replicated pairs, and new-partner/model-family
transfer remain unmeasured. No emergence time, persistence, recovery, or convention
transfer rate can be estimated when no convention has been validated. Providing
invented positive trajectories would not complete these requirements. The present
artifact must not be called a completed confirmation of the original full
longitudinal methodology or publication-ready novelty merely because its code
passes tests. Separate development flaws, controlled engineered channels, genuine
agent outputs, and unrun extensions in every report.

## Working OS boundary added on 2026-11-14

The [kernel-gate report](KERNEL_GATE_REPORT.md) and
[quickstart](WORKING_QUICKSTART.md) supersede earlier statements that native
stack observation or protected-open mediation are entirely unimplemented.
`guarded_agent.py` runs an unmodified command through the trusted native launcher;
approved protected opens receive an immutable descriptor, stale or ungranted
requests stop the scope, and bounded native execution frames reach the live
observer as frozen evidence. The full WSL suite passed 77 tests. Three live CLI
controls retain exit codes 0, 77 and 1; six separate kernel trials retain race and
revocation controls. One denied trial has an incomplete syscall capture, retained
as such. These trials use synthetic resources, with actual provider calls clearly
separated from fixture observers.

No additional Grok subject population was launched. No weight training is needed.
Persistent context-window pressure remains UNRUN; passing deterministic programs
does not demonstrate spontaneous misalignment, emergence or universal detection.
The close 2026 prior systems are permitted components and baselines, not a reason
to rename existing primitives as novelty. Current-system comparative measurements,
replicated agent trajectories and a distinct journal contribution remain required.

The [current-system baseline report](BASELINE_REPORT.md) now retains 30 randomized
actual nono/GuardianAI worker trials, three repeats per control and system, plus
15 successful native baseline audit verifications. Both systems blocked the
tested ungranted reads, input mutations and host TCP connection attempts. This
does not establish equal features or general security superiority. The baseline
exposed and drove a fix for live-observation startup recognition with JSON argv;
the updated full Linux suite passed 80 tests. Persistent context-pressure and
broader statistical/novelty requirements remain unmeasured.

The [context measurement report](CONTEXT_MEASUREMENT_REPORT.md) adds a working
exchange recorder and audits all 16 corrected historical sender/receiver calls.
All declare fresh contexts and expose no token usage; logical subject continuity
does not prove retained provider history. No further subject inference was launched.
The recorder detects mismatched run/subject/message evidence and preserves missing
context measurements. This is instrumentation progress, not completion of the
persistent-context arm.

The [release-order report](RELEASE_ORDER_REPORT.md) now retains 36 actual Linux
workers separating denied operations, delayed scope stopping, descriptor commits
and printed synthetic data. The original configuration sometimes committed a
protected read after a prohibited attempt. Native policy 2 moves `connect` and
`ptrace` denial into the notification path and stops shared authority before
returning to the caller. Tested post-correction sequences have zero protected
commits; approved controls succeed. Cross-worker pending-release and stale-helper
regressions pass; the full Linux suite passed 89 tests. Filter stacking and broader
mandatory observation coverage still need adversarial validation. This is a bounded
systems correction and measurement, not universal intent detection or established
journal novelty.

The [filter-stacking report](FILTER_STACK_REPORT.md) confirms and corrects the
next notification precondition: six policy-2 probes suppressed notifications and
released synthetic protected data after a denied operation. Policy 3 prevents the
worker from installing those filters, stops shared authority, rejects older helpers,
and preserves tested query utility. Twelve installation probes and three query
controls validate the correction; the full Linux suite passed 92 tests. This adds
a concrete compatibility restriction for applications requiring their own seccomp
sandbox. Wider observation completeness, persistent-context effects and publication
novelty remain unestablished.
