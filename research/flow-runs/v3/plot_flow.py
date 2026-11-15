"""Render the audited flow-policy outcomes as a small engineering diagram."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


root = Path(__file__).resolve().parent
audit = json.loads((root / 'audit.json').read_text())
assert audit['handoff_publications'] == [True, True, False, False]
fig, ax = plt.subplots(figsize=(8.2, 3.9))
ax.set(xlim=(0, 1), ylim=(0, 1))
ax.axis('off')
def box(x, y, text, width=.28):
    ax.add_patch(FancyBboxPatch((x-width/2, y-.075), width, .15,
                                boxstyle='round,pad=.012', facecolor='#eef2f5', edgecolor='#53616b'))
    ax.text(x, y, text, ha='center', va='center', fontsize=9)
def arrow(start, end, text, color, label):
    ax.annotate('', xy=end, xytext=start, arrowprops={'arrowstyle': '-|>', 'color': color, 'lw': 1.7})
    ax.text(*label, text, color=color, ha='center', fontsize=9,
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.5})
box(.26, .88, 'Protected manifest\ncontrolled internal label', .34)
box(.26, .57, 'Indexer\nexposure label: internal')
box(.78, .57, 'Builder\nexposure labels: none')
box(.20, .12, 'Internal recipient\nclearance: internal')
box(.76, .12, 'Public recipient\nclearance: none')
arrow((.26,.79),(.26,.66),'checkpoint before release','#53616b',(.48,.76))
arrow((.24,.48),(.20,.21),'allowed; label follows','#287148',(.14,.33))
arrow((.37,.49),(.65,.21),'blocked','#aa403b',(.46,.30))
arrow((.78,.48),(.76,.21),'allowed','#287148',(.85,.33))
fig.tight_layout(pad=.5)
fig.savefig(root / 'flow-diagram.png', dpi=160)
fig.savefig(root / 'flow-diagram.svg')
svg = root / 'flow-diagram.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
(root / 'flow-diagram.html').write_text('''<!doctype html><html><head><meta charset="utf-8"><style>
body{font-family:var(--font-sans);color:var(--foreground);margin:0}
img{width:100%;height:340px;object-fit:contain}p{font-size:13px;color:var(--muted-foreground);line-height:1.45}
</style></head><body><img src="''' + str((root / 'flow-diagram.png').resolve()) + '''" alt="A labelled private manifest goes to the indexer. Its internal handoff is allowed and public handoff blocked. The unexposed builder's public handoff is allowed.">
<p>Actual build/index artifacts under an experimental classification policy. Both workers had read permission, but only the indexer received the protected manifest. The denied public export revoked the shared scope; a later public retry was also refused. These are flow-policy outcomes, not detected malicious intentions.</p></body></html>''')
