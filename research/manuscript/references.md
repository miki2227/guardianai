# Primary references and verification scope

Checked 15 November 2026. This is a targeted related-work set, not a systematic review or a proof of novelty. Sources are cited only for their own contributions or documented mechanisms; GuardianAI outcomes come from the local artifact ledger.

1. Spencer King, Zhilu Zhang, Mikhail Kuznetsov, Kay Liu, Baris Coskun and Wei Ding. **On the Effectiveness of Kernel-Level Evidence for Agent Security.** arXiv:2609.28915, 2026. [Primary abstract](https://arxiv.org/abs/2609.28915). Supports existing paired application/kernel evidence work. No head-to-head reproduction of its detector study is claimed here.

2. nono contributors. **nono v0.81.0 security model and release.** 2026. [Pinned documentation](https://github.com/nolabs-ai/nono/blob/v0.81.0/docs/cli/internals/security-model.mdx), [release](https://github.com/nolabs-ai/nono/releases/tag/v0.81.0). Source commit `b2d859deeb7a65f9ca5b334eb8726637ba76c866`; retained installation provenance is in [release metadata](../baseline-runs/nono-release-v0.81.0/release-metadata.json). Supports treating supervisor delegation and descriptor injection as prior mechanisms. Our recorded baseline uses static grants rather than its complete feature set.

3. Derek Lilienthal and Sanghyun Hong. **Mind the Gap: Time-of-Check to Time-of-Use Vulnerabilities in LLM-Enabled Agents.** arXiv:2508.17155, 2025. [Primary abstract](https://arxiv.org/abs/2508.17155). Supports prior agent TOCTOU research; the manuscript does not reuse its benchmark numbers as GuardianAI measurements.

4. Sumeet Ramesh Motwani, Mikhail Baranchuk, Martin Strohmeier, Vijay Bolina, Philip H. S. Torr, Lewis Hammond and Christian Schroeder de Witt. **Secret Collusion among AI Agents: Multi-Agent Deception via Steganography.** arXiv:2402.07510, first submitted 2024; latest displayed revision 2025. [Primary record](https://arxiv.org/abs/2402.07510). Supports established collusion capability/threat-model work. GuardianAI does not claim to replicate its capability study.

5. Yohan Mathew, Ollie Matthews, Robert McCarthy, Joan Velja, Christian Schroeder de Witt, Dylan Cope and Nandi Schoots. **Hidden in Plain Text: Emergence & Mitigation of Steganographic Collusion in LLMs.** IJCNLP–AACL, 2025, pp. 585–624. DOI `10.18653/v1/2025.ijcnlp-long.34`. [ACL Anthology](https://aclanthology.org/2025.ijcnlp-long.34/). Supports prior emergence/mitigation work. No parameter-training arm is added to GuardianAI.

6. Diogo Almeida / TypeSafe AI. **Introducing System One Models & Jev.** 15 September 2026. [Official introduction](https://typesafe.ai/blog/introducing-system-one-models-and-jev). Source for the provider's RLCD name and model framing, not independent proof of accuracy or adversarial immunity.

7. Linux kernel documentation. **Seccomp BPF.** [Official documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html). Source for existing filter actions, inheritance and precedence. The manuscript does not claim those semantics as a new algorithm.

8. Linux man-pages project. **seccomp_unotify(2).** [Manual](https://man7.org/linux/man-pages/man2/seccomp_unotify.2.html). Source for notifications, atomic descriptor addition/reply and mutable-argument limitations. This does not certify GuardianAI's full interposition implementation.

9. Linux man-pages project. **pid_namespaces(7).** [Manual](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html). Source for namespace-init termination semantics. Local implementation checks remain a separate evidence requirement.

10. TypeSafe documentation. **Models; Request rules and errors.** [Models](https://docs.typesafe.ai/models), [errors](https://docs.typesafe.ai/api/errors). Source for documented model context limits and the context-overflow error class. A byte count in the local traces is not converted into a token count.

11. Kentaroh Toyoda, Alex Leung and Bhuvaneswari U. **guardscope: Measuring Which Actions Runtime Controls Check in LLM Agent Systems.** arXiv:2611.15223v1, 11 November 2026. [Primary full text](https://arxiv.org/html/2611.15223v1). Coverage measurement; no GuardianAI reproduction claimed.

12. Yuvraj Sehgal, Mahsa Panahandeh and Naser Ezzati-Jivan. **Context Is a Pipeline, Not a Window: Information Attrition in LLM Agent Harnesses.** arXiv:2610.36114v1, 26 October 2026. [Primary full text](https://arxiv.org/html/2610.36114v1). Evidence-delivery loss; distinct from our observer overflow.

13. Kai Wang et al. **ClawSentry: A Progressive Multi-Tier Security Monitor for Safeguarding Autonomous LLM Agents.** arXiv:2608.21101v1, 21 August 2026. [Primary full text](https://arxiv.org/html/2608.21101v1). External supervision and session-aware mediation; no comparative outcome claimed.

14. Phat T. Tran-Truong, Ha Vo, Nhut Tran, Khang Vo and Thai-Minh Truong. **DelegateGuard: Purpose-Bound Capabilities for Delegated LLM Agent Workflows.** arXiv:2610.16005v1, 12 October 2026. [Primary full text](https://arxiv.org/html/2610.16005v1). Capability/revocation prior work with stated mediation limits.

See [PRIOR_ART_UPDATE.md](PRIOR_ART_UPDATE.md) for the inspected sections and effects on the contribution claim. Additional closely related work and earlier reference checks remain in [LITERATURE.md](../LITERATURE.md) and [REFERENCE_AUDIT.md](../REFERENCE_AUDIT.md). They are not silently promoted into verified publication claims by this bibliography.
