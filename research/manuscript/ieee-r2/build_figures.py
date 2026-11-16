"""Draw the architecture as an editable, standalone vector publication figure."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


def main():
    folder = Path(__file__).resolve().parent / 'figures'
    plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 9,
                         'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.set(xlim=(0, 12), ylim=(0, 5)); ax.axis('off')
    ax.add_patch(Rectangle((.2, .2), 11.5, 3.25, fill=False, linewidth=.9,
                           linestyle=(0, (4, 3)), edgecolor='#727b83'))
    ax.text(.45, 3.2, 'Trusted host supervision (user space)', ha='left', va='center', fontsize=9)
    def box(x, y, width, height, text, fill='#f2f5f7'):
        ax.add_patch(FancyBboxPatch((x, y), width, height, boxstyle='round,pad=0.03,rounding_size=0.05',
                                   facecolor=fill, edgecolor='#293c4a', linewidth=.9))
        ax.text(x + width / 2, y + height / 2, text, ha='center', va='center', linespacing=1.35)
    def arrow(start, end, label=None, position=None, style='-|>'):
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=10,
                                     color='#293c4a', linewidth=.95))
        if label: ax.text(*position, label, fontsize=7.5, ha='left', va='center')
    box(.45, 3.85, 3.1, .9, 'Hosted agents / CLI\nno local weight updates', '#ffffff')
    box(8, 3.85, 3.1, .9, 'Jev API\ntyped observer decisions', '#ffffff')
    box(.5, 1.95, 3, .95, 'MCP admission\ntask + CLI binding')
    box(4, 1.95, 3.2, .95, 'Resource / flow broker\nlabels + snapshots + stop')
    box(8, 1.95, 3.1, .95, 'Content observation\nargv, results, file / ZIP text')
    box(.5, .55, 6.7, 1, 'Linux kernel + contained local workers\nnamespaces, capabilities, seccomp mediation', '#e8edf1')
    box(8, .55, 3.1, 1, 'Evidence and decisions\nhashes, spans, stop receipts')
    arrow((2, 3.85), (2, 2.9), 'tools / exposed content', (2.15, 3.6))
    arrow((9.5, 3.85), (9.5, 2.9), 'state / decisions', (9.65, 3.6), '<->')
    arrow((3.5, 2.42), (4, 2.42))
    arrow((7.2, 2.42), (8, 2.42))
    arrow((2, 1.95), (2, 1.55), 'commands', (2.1, 1.75))
    arrow((4.4, 1.95), (4.4, 1.55), 'revoke', (4.5, 1.75))
    arrow((6, 1.55), (6, 1.95), 'events / release', (6.1, 1.75))
    arrow((9.5, 1.95), (9.5, 1.55), 'receipts', (9.65, 1.75))
    arrow((7.2, 1.05), (8, 1.05))
    fig.subplots_adjust(left=.01, right=.99, bottom=.03, top=.99)
    fig.savefig(folder / 'architecture.pdf', bbox_inches='tight', pad_inches=.03)
    fig.savefig(folder / 'architecture.png', dpi=220, bbox_inches='tight', pad_inches=.03)
    plt.close(fig)
    ledger = json.loads((folder.parent / 'claims.json').read_text())
    values = next(item['expected'] for item in ledger['facts'] if item.get('pointer') == '/largest_message_input_field_sum_by_phase')
    names = ['index', 'build', 'correction']
    fig, ax = plt.subplots(figsize=(3.35, 1.8))
    ax.bar(range(3), [values[name] for name in names], width=.55, color='#476c86', zorder=3)
    for i, name in enumerate(names):
        ax.text(i, values[name] + 2200, f'{values[name]:,}', ha='center', fontsize=8.5)
    ax.set_xticks(range(3), ['Index', 'Build', 'Correction'], fontsize=8)
    ax.set_ylim(0, 93000); ax.set_yticks([0, 40000, 80000], ['0', '40k', '80k'], fontsize=8)
    ax.set_ylabel('Reported field sum', fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', color='#dde2e6', linewidth=.6, zorder=0)
    fig.tight_layout(pad=.5)
    fig.savefig(folder / 'context-fields.pdf', bbox_inches='tight', pad_inches=.03)
    fig.savefig(folder / 'context-fields.png', dpi=220, bbox_inches='tight', pad_inches=.03)
    plt.close(fig)
    (folder / 'context-fields.json').write_text(json.dumps({'source_claim': 'E5-25', 'values': values,
        'zero_based_axis': True, 'scope': 'Reported per-message input-field sums, not retained context occupancy or model capacity.'}, indent=2)+'\n')


if __name__ == '__main__': main()
