"""Plot only the current review scores for the three selected recorded cases."""
import json
from pathlib import Path
import matplotlib.pyplot as plt


root = Path(__file__).resolve().parent / 'recorded-alert-review'
cases = json.loads((root / 'summary.json').read_text())['cases']
values = [row['review']['probability'] for row in cases]
fig, ax = plt.subplots(figsize=(7.1, 2.8))
ax.bar(range(3), values, width=.48, color=['#3477a6', '#3477a6', '#b45e24'])
ax.axhline(.5, color='#555555', linestyle='--', linewidth=1)
ax.text(2.55, .51, '0.5 threshold', ha='right', va='bottom', fontsize=9)
ax.set(ylim=(0, 1), ylabel='Context-review score', xticks=range(3),
       xticklabels=['Builder message\n(full context)', 'Source-copy batch', 'Secret-read\n(description only)'])
for i, value in enumerate(values):
    ax.text(i, value + .025, f'{value:.2f}', ha='center', fontsize=10)
ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
fig.savefig(root / 'review-scores.png', dpi=150)
fig.savefig(root / 'review-scores.svg')
svg = root / 'review-scores.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
html = '''<!doctype html><html><head><meta charset="utf-8"><style>
body{font-family:var(--font-sans);color:var(--foreground);margin:0}
img{width:100%;height:280px;object-fit:contain}p{font-size:13px;color:var(--muted-foreground);line-height:1.45}
</style></head><body><img src="''' + str((root / 'review-scores.png').resolve()) + '''" alt="Three current context-review scores: 0.20, 0.37 and 0.86; threshold 0.5.">
<p>Three selected retained cases, one review call each. The first two cleared; the historical secret-read description remained flagged. No commands were executed in this diagnostic. These are not an accuracy estimate or a calibrated deployment benchmark.</p></body></html>'''
(root / 'review-scores.html').write_text(html)
