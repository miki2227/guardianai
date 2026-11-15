"""Generate IEEE conference LaTeX from the current editable Markdown draft."""
import re
import json
import subprocess
from pathlib import Path

import yaml


def latex(text):
    return subprocess.run(['pandoc', '-f', 'markdown', '-t', 'latex', '--wrap=none'],
                          input=text, text=True, encoding='utf-8', capture_output=True, check=True).stdout.strip()


def main():
    folder = Path(__file__).resolve().parent
    _, header, body = (folder / 'paper.md').read_text(encoding='utf-8').split('---', 2)
    meta = yaml.safe_load(header)
    fixed = json.loads((folder / 'frontmatter.json').read_text(encoding='utf-8'))
    assert all(meta[key].strip() == fixed[key] for key in ('title', 'abstract', 'keywords'))
    assert meta['authors'] == fixed['authors']
    body, references = body.split('# References', 1)
    body = body.replace('```{=latex}\n\\clearpage\n```', '')
    table = re.search(r'\| Case \|.*?(?=\n\n)', body, re.S)
    rows = [line.split('|')[1:-1] for line in table.group().splitlines()[2:]]
    tabular = '\n'.join(' & '.join(latex(cell.strip()) for cell in row) + r' \\' for row in rows)
    table_tex = (r'\begin{table*}[t]\caption{Separately scoped development cases}\label{tab:cases}'
                 r'\centering\begin{tabular}{p{.055\textwidth}p{.24\textwidth}p{.62\textwidth}}\hline '
                 r'Case & Workload & Recorded outcome \\\hline ' + tabular +
                 r'\hline\end{tabular}\end{table*}')
    body = body[:table.start()] + '\n```{=latex}\n' + table_tex + '\n```\n' + body[table.end():]
    body = re.sub(r'\[([1-8])\]', lambda m: r'\cite{r' + m[1] + '}', body)
    entries = re.findall(r'^\d+\. (.+)$', references, re.M)
    assert len(entries) == 8
    bibliography = '\n'.join(r'\bibitem{r' + str(i) + '}' + latex(entry) for i, entry in enumerate(entries, 1))
    source = (r'\documentclass[conference]{IEEEtran}' '\n'
              r'\usepackage{cite,amsmath,amssymb,graphicx,array,booktabs}' '\n'
              r'\usepackage[T1]{fontenc}\usepackage{mathptmx}' '\n'
              r'\usepackage[hyphens]{url}\usepackage{xurl}\usepackage[hidelinks]{hyperref}' '\n'
              r'\providecommand{\pandocbounded}[1]{#1}' '\n'
              r'\begin{document}\title{' + latex(meta['title']) + r'}\author{' +
              r'\and '.join(r'\IEEEauthorblockN{' + latex(name) + '}' for name in fixed['authors']) +
              r'}\maketitle' '\n'
              r'\begin{abstract}' + latex(meta['abstract']) + r'\end{abstract}' '\n'
              r'\renewcommand{\IEEEkeywordsname}{Keywords}' '\n'
              r'\begin{IEEEkeywords}' + latex(fixed['keywords']) + r'\end{IEEEkeywords}' '\n'
              + latex(body) + '\n' + r'\begin{thebibliography}{8}' + bibliography +
              r'\end{thebibliography}\end{document}' '\n')
    (folder / 'main.tex').write_text(source, encoding='utf-8')


if __name__ == '__main__':
    main()
