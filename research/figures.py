"""Standalone scientific figures derived only from summary.json."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


root = Path(__file__).resolve().parent / "results"
data = json.loads((root / "summary.json").read_text())
names = ["Preflight Jev", "Kernel Jev", "Joined Jev", "Task rules", "Effects-only rules"]
keys = ["preflight", "kernel", "joined", "rule", "effects_only_rule"]
x = np.arange(len(keys))
fig, ax = plt.subplots(figsize=(9, 4.8))
for offset, metric, label, color in [(-.18, "recall_all_positive", "Recall (28 positive sessions)", "#2563a6"),
                                    (.18, "fpr_all_negative", "False-positive rate (20 negatives)", "#c65b2b")]:
    values = [data["detectors"][k][metric] for k in keys]
    field = "recall_family_bootstrap_95" if metric.startswith("recall") else "fpr_family_bootstrap_95"
    intervals = [data["detectors"][k][field] for k in keys]
    errors = [[max(0, v - bounds[0]) for v, bounds in zip(values, intervals)],
              [max(0, bounds[1] - v) for v, bounds in zip(values, intervals)]]
    ax.bar(x + offset, values, .34, label=label, color=color, yerr=errors, capsize=3)
ax.set_xticks(x, names, rotation=12, ha="right")
ax.set_ylim(0, 1.08); ax.set_ylabel("Fraction")
ax.set_title("Fixed-threshold judgments on handcrafted WSL2 workloads")
ax.legend(loc="upper center", fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
fig.text(.02, .015, "48 sessions; 12 families; four data seeds. Post-execution methods abstained on four relative-path cases.\nError bars: descriptive family-cluster bootstrap 95% intervals; no population guarantee.", fontsize=8)
fig.tight_layout(rect=(0, .1, 1, 1))
for suffix in ("png", "svg"):
    fig.savefig(root / ("detectors." + suffix), dpi=180)
plt.close(fig)

modes = ["raw", "canonical", "shuffle", "blocked"]
fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(4)
for offset, field, label, color in [(-.18, "bit_recovered", "Private-bit recovery", "#2563a6"),
                                    (.18, "utility", "Legitimate result recovered", "#398363")]:
    values = [data["counterfactual"]["channel"][m][field] / 16 for m in modes]
    ax.bar(x + offset, values, .34, label=label, color=color)
ax.axhline(.5, color="#777777", ls="--", lw=1, label="Honest receiver bit recovery")
ax.set_xticks(x, ["Raw delivery", "Canonical result", "Shuffled marker", "No delivery"])
ax.set_ylim(0, 1.1); ax.set_ylabel("Fraction of 16 matched episodes")
ax.set_title("Engineered channel controls: safety and utility measured separately")
ax.legend(loc="upper center", fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
fig.text(.02, .015, "Fixed scripted agents, balanced bits; no learning or emergent convention. Exact control outcomes.\nCanonical delivery preserves only the legitimate sum field; arbitrary semantic/timing channels are outside scope.", fontsize=8)
fig.tight_layout(rect=(0, .1, 1, 1))
for suffix in ("png", "svg"):
    fig.savefig(root / ("counterfactual." + suffix), dpi=180)
plt.close(fig)

html = '<!doctype html><html><head><meta charset="utf-8"><style>body{color:var(--foreground);font-family:var(--font-sans)}img{display:block;width:100%;height:auto}p{font-size:13px;color:var(--muted-foreground)}</style></head><body>'
for name in ("detectors", "counterfactual"):
    html += '<img alt="' + name + ' experiment results" src="' + (root / (name + '.png')).as_posix() + '">'
html += '<p>Measured WSL2 controls. See the research report for scope, abstentions, and negative results.</p></body></html>'
(root / "figures.html").write_text(html, encoding="utf-8")
