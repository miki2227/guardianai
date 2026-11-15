"""Plot observed input fields without asserting context capacity or saturation."""
import base64
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def main():
    root = Path(__file__).resolve().parent
    audit = json.loads((root / 'audit.json').read_text())
    values = audit['largest_message_input_field_sum_by_phase']
    fig, ax = plt.subplots(figsize=(8, 3.8), layout='constrained')
    ax.plot(list(values), list(values.values()), marker='o', color='#245a81', linewidth=2)
    for x, value in enumerate(values.values()):
        ax.annotate(f'{value:,}', (x, value), xytext=(0, 9), textcoords='offset points', ha='center')
    ax.set_ylim(0, 100000)
    ax.set_xlim(-.3, 2.3)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, position: f'{value/1000:.0f}k'))
    ax.set_ylabel('Reported input-field sum (tokens)')
    ax.set_title('One continuing conversation', loc='left', pad=15)
    ax.grid(axis='y', alpha=.2)
    ax.spines[['right', 'top']].set_visible(False)
    fig.savefig(root / 'context-inputs.png', dpi=180)
    fig.savefig(root / 'context-inputs.svg')
    svg = root / 'context-inputs.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    plt.close(fig)
    encoded = base64.b64encode((root / 'context-inputs.png').read_bytes()).decode()
    (root / 'context-inputs.html').write_text(
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        'body{margin:0;font-family:var(--font-sans);color:var(--foreground)}'
        'img{display:block;width:100%;height:330px;object-fit:contain}'
        'p{font-size:13px;color:var(--muted-foreground);line-height:1.5;margin:8px 0}'
        '</style></head><body><img alt="Maximum reported per-message input-field sums: '
        'index 70,106; build 76,277; correction 81,101 tokens." src="data:image/png;base64,' + encoded + '">'
        '<p>Maximum per-message input + cache-read + cache-creation fields in each invocation. '
        'These are provider-reported fields, not verified context occupancy or a saturation result.</p></body></html>')


if __name__ == '__main__':
    main()
