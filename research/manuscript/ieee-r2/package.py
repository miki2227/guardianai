"""Package the inspected IEEE source and PDF, excluding full execution data."""
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    folder = Path(__file__).resolve().parent
    names = ['README.md', 'paper.md', 'frontmatter.json', 'main.tex', 'build_ieee.py', 'build_figures.py',
             'claims.json', 'create_ledger.py', 'verify_claims.py', 'verification.json', 'reference-audit.json',
             'inspect_pdf.py', 'package.py', 'compile-report.json', 'pdf-check.json', 'visual-review.json',
             'figures/architecture.pdf', 'figures/architecture.png', 'figures/context-inputs.png',
             'figures/context-fields.pdf', 'figures/context-fields.png', 'figures/context-fields.json',
             'output/pdf/main.pdf', 'output/pdf/qa-contact-sheet.png']
    check = json.loads((folder / 'pdf-check.json').read_text())
    assert all(check['frontmatter_preserved'].values())
    assert check['pdf_sha256'] == hashlib.sha256((folder / 'output/pdf/main.pdf').read_bytes()).hexdigest()
    visual = json.loads((folder / 'visual-review.json').read_text())
    assert visual['pdf_sha256'] == check['pdf_sha256'] and visual['pages_inspected'] == check['pages']
    manifest = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in names}
    (folder / 'artifact-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    archive = folder / 'GuardianAI-ieee-r2.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for name in names + ['artifact-manifest.json']: bundle.write(folder / name, name)
    with zipfile.ZipFile(archive) as bundle:
        assert all(hashlib.sha256(bundle.read(name)).hexdigest() == digest for name, digest in manifest.items())
    result = {'pdf_pages': check['pages'], 'pdf_sha256': check['pdf_sha256'],
              'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'package_members': len(names) + 1,
              'frontmatter_preserved': check['frontmatter_preserved'], 'scope': 'Authoring package and retained checks; full execution data remain in the pinned repository.'}
    (folder / 'artifact-report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
