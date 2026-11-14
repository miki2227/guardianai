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
