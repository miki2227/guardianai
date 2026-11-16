"""Check front matter and PDF geometry, then render every page for visual review."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import fitz
from PIL import Image, ImageDraw
import yaml


def normalized(text):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKC', text).lower())


def main():
    folder = Path(__file__).resolve().parent
    fixed = json.loads((folder / 'frontmatter.json').read_text())
    _, header, _ = (folder / 'paper.md').read_text(encoding='utf-8').split('---', 2)
    assert yaml.safe_load(header) == fixed
    doc = fitz.open(folder / 'output/pdf/main.pdf')
    first = doc[0].get_text()
    abstract = first.split('Abstract', 1)[1].split('Keywords', 1)[0]
    keywords = first.split('Keywords', 1)[1].split('I. INTRODUCTION', 1)[0]
    checks = {'title': normalized(fixed['title']) in normalized(first),
              'authors': all(normalized(name) in normalized(first) for name in fixed['authors']),
              'abstract': normalized(abstract) == normalized(fixed['abstract']),
              'keywords': normalized(keywords) == normalized(fixed['keywords'])}
    assert all(checks.values()), checks
    outside, replacements, fonts = [], [], set()
    for index, page in enumerate(doc):
        assert (page.rect.width, page.rect.height) == (612, 792)
        text = page.get_text()
        assert '[?]' not in text
        if '\ufffd' in text: replacements.append(index + 1)
        for block in page.get_text('blocks'):
            if block[4].strip() and (block[0] < -1 or block[1] < -1 or block[2] > 613 or block[3] > 793):
                outside.append({'page': index + 1, 'box': block[:4]})
        for font in page.get_fonts():
            fonts.add(font[3])
            assert doc.extract_font(font[0])[3], ('font_not_embedded', font[3])
    assert not outside and not replacements
    last = doc[-1]
    blocks = [block for block in last.get_text('blocks') if block[4].strip()]
    left = max(block[3] for block in blocks if (block[0] + block[2]) / 2 < 306)
    right = max(block[3] for block in blocks if (block[0] + block[2]) / 2 >= 306)
    assert abs(left - right) < 18, ('last_columns_unbalanced', left, right)
    tmp = folder / 'tmp/pdfs'; tmp.mkdir(parents=True, exist_ok=True)
    tiles = []
    for index, page in enumerate(doc):
        target = tmp / f'page-{index+1:02d}.png'
        page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False).save(target)
        picture = Image.open(target).convert('RGB'); picture.thumbnail((510, 690))
        tile = Image.new('RGB', (530, 725), '#e9ecef')
        tile.paste(picture, ((530 - picture.width) // 2, 25))
        ImageDraw.Draw(tile).text((12, 7), f'Page {index+1}', fill='black'); tiles.append(tile)
    sheet = Image.new('RGB', (1060, 725 * ((len(tiles) + 1) // 2)), '#d5d9dd')
    for index, tile in enumerate(tiles): sheet.paste(tile, ((index % 2) * 530, (index // 2) * 725))
    sheet.save(folder / 'output/pdf/qa-contact-sheet.png')
    report = {'pages': len(doc), 'page_size_points': [612, 792], 'frontmatter_preserved': checks,
              'source_frontmatter_exact': True, 'pdf_comparison': 'NFKC letters/digits after layout hyphenation; exact source punctuation is checked separately.',
              'text_boxes_outside_page': outside, 'replacement_glyph_pages': replacements, 'fonts_embedded': True,
              'fonts': sorted(fonts), 'last_column_bottom_difference_points': round(abs(left - right), 3),
              'pdf_sha256': hashlib.sha256((folder / 'output/pdf/main.pdf').read_bytes()).hexdigest(),
              'scope': 'Automated content/geometry checks and page renders. A separate visual inspection is required; this does not prove research validity.'}
    (folder / 'pdf-check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
