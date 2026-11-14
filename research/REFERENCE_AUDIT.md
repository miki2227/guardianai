# Audit of the supplied references

Checked 2026-11-14. Primary landing pages and abstracts establish the limited
comparisons below; this is not a full replication or systematic review. The
original supplied bibliography is retained in the attachment. This table supplies
stable primary links and avoids carrying unverified metadata into new claims.

| Brief | Primary record | Implication for this project |
|---|---|---|
| 1 | [Motwani et al., Secret Collusion](https://arxiv.org/abs/2402.07510) | Covert-agent communication and threat models already studied. |
| 2 | [Mathew et al., Hidden in Plain Text](https://aclanthology.org/2025.ijcnlp-long.34/) | Emergence under optimization and imperfect monitoring/paraphrasing are prior work. |
| 3 | [Bonjour et al.](https://proceedings.mlr.press/v180/bonjour22a.html) | Information-theoretic collusion detection from repeated game records predates this project. |
| 4 | [Bai et al.](https://arxiv.org/abs/2405.09090) | LLM-based linguistic steganalysis is not new. |
| 5 | [Tang et al.](https://arxiv.org/abs/2406.04218) | Generative and classification modes for steganalysis are prior work; not reproduced here. |
| 6 | [Meier et al., TrojanStego](https://aclanthology.org/2025.emnlp-main.1386/) | Its threat model involves adversarial fine-tuning; our subjects receive no such training. |
| 7 | [Rippin et al.](https://arxiv.org/abs/2606.28425) | Tool-enabled schemes and compatibility are distinct from incidental errors in a text-only study. |
| 8 | [Golechha and Garriga-Alonso, Among Us](https://arxiv.org/abs/2504.04072) | Rich agentic social-deduction deception environments already exist. Our three-suspect game is much smaller. |
| 9 | [Li et al., social-deduction behavior](https://aclanthology.org/2026.findings-acl.2043/) | Interactive adversarial behavior without explicit prompt injection is already evaluated. |
| 10 | [Rose et al., HELIOS/NARCBench](https://arxiv.org/abs/2604.01151) | Joint activation-based detection and transfer already studied. Current version has six authors, including Sahar Abdelnabi and Philip Torr, omitted from the supplied abbreviated listing. Hosted Grok activations are unavailable here. |
| 11 | [Shinn et al., Reflexion](https://arxiv.org/abs/2303.11366) | Linguistic feedback without weight updates supports a fixed-weight design; no training is needed here. |
| 12 | [Madaan et al., Self-Refine](https://arxiv.org/abs/2303.17651) | Iterative self-feedback is established; carrying a compact note is not a novel learning algorithm. |
| 13 | [Heo et al., authors' university report](https://eng.snu.ac.kr/communication/promotion/news?bbsidx=8488&md=v) | Confirms the construction-bidding paper and DOI 10.1061/JMENEA.MEENG-7144. Full publisher text was not audited here; no numerical comparison is made. |
| 14 | [Huang et al., Whispering Agents](https://ojs.aaai.org/index.php/AAAI/article/view/40380) | Engineered event-driven channels already studied. Complete DOI: 10.1609/aaai.v40i37.40380. |

TypeSafe's [official launch](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
defines RLCD as Reinforcement Learning for Calibrated Decisions and describes Jev's
typed probabilistic outputs. That is the provider's training method; it is not an
additional training step in GuardianAI. Typed decisions do not logically imply
correct semantic judgments for every state. Our study measures actual mistakes
and abstentions instead of assuming immunity.

See [LITERATURE.md](LITERATURE.md) for the kernel evidence survey, close epistemic
monitoring prior art, and the narrower empirical contribution boundary. Combining
known components is an implementation contribution; publication-level novelty is
not established by this audit.
