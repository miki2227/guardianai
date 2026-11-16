"""Check pinned bytes and descriptive fields without inference or refreshed hashes."""
import hashlib
import json
from pathlib import Path
import subprocess


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    folder = Path(__file__).resolve().parent
    project = folder.parents[2]
    ledger = json.loads((folder / 'claims.json').read_text())
    documents, raw_sources = {}, {}
    for source in ledger['sources']:
        raw = subprocess.check_output(['git', 'show', ledger['data_revision'] + ':' + source['path']], cwd=project)
        assert sha(raw) == source['sha256'], source['path']
        raw_sources[source['path']] = raw
        if source['path'].endswith('.json'): documents[source['path']] = json.loads(raw)
    for claim in ledger['facts']:
        value = documents[claim['source']]
        if claim.get('derive') == 'phase_command_sum': value = sum(phase['commands'] for phase in value['phases'])
        elif claim.get('derive') == 'phase_count': value = len(value['phases'])
        elif claim.get('derive') == 'conversation_count': value = len({phase['conversation'] for phase in value['phases']})
        else:
            for part in claim['pointer'].lstrip('/').split('/'):
                part = part.replace('~1', '/').replace('~0', '~')
                value = value[int(part)] if isinstance(value, list) else value[part]
        assert value == claim['expected'], (claim['id'], value, claim['expected'])
    for item in ledger['source_assertions']:
        assert item['contains'] in raw_sources[item['source']].decode(), item
    fixed = json.loads(raw_sources['research/manuscript/current/frontmatter.json'])
    assert (folder / 'frontmatter.json').read_bytes() == raw_sources['research/manuscript/current/frontmatter.json']
    assert json.loads((folder / 'frontmatter.json').read_text()) == fixed
    for base, manifest in (('research/manuscript', documents['research/manuscript/draft-manifest.json']),
                           ('research/manuscript/current', documents['research/manuscript/current/artifact-manifest.json'])):
        for name, expected in manifest.items(): assert sha((project / base / name).read_bytes()) == expected, (base, name)
    old_report = documents['research/manuscript/current/artifact-report.json']
    assert sha((project / 'research/manuscript/current/GuardianAI-current-draft.zip').read_bytes()) == old_report['archive_sha256']
    assert (folder / 'figures/context-inputs.png').read_bytes() == (project / 'research/manuscript/current/figures/context-inputs.png').read_bytes()
    figure = json.loads((folder / 'figures/context-fields.json').read_text())
    assert figure['values'] == documents['research/continued-agent-runs/v1/audit.json']['largest_message_input_field_sum_by_phase']
    assert figure['zero_based_axis']
    result = {'data_revision': ledger['data_revision'], 'source_files_verified': len(ledger['sources']),
              'selected_facts_verified': len(ledger['facts']), 'source_assertions_verified': len(ledger['source_assertions']),
              'earlier_manuscripts_unchanged': True, 'fixed_frontmatter_source_preserved': True,
              'scope': 'Git-pinned bytes, literal source statements and selected descriptive fields. No inference, current actor poll, semantic claim proof, accuracy estimate or formal security verification. Expected hashes are not refreshed.'}
    (folder / 'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
