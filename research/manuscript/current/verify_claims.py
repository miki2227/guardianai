"""Verify pinned source bytes and selected descriptive paper facts, not security."""
import hashlib
import json
from pathlib import Path


def main():
    folder = Path(__file__).resolve().parent
    project = folder.parents[2]
    ledger = json.loads((folder / 'claims.json').read_text(encoding='utf-8'))
    documents = {}
    for item in ledger['sources']:
        path = project / item['path']
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item['sha256'], item['path']
        if path.suffix == '.json':
            documents[item['path']] = json.loads(raw)
    for claim in ledger['facts']:
        data = documents[claim['source']]
        if claim.get('derive') == 'phase_command_sum':
            actual = sum(phase['commands'] for phase in data['phases'])
        elif claim.get('derive') == 'phase_count':
            actual = len(data['phases'])
        elif claim.get('derive') == 'conversation_count':
            actual = len({phase['conversation'] for phase in data['phases']})
        else:
            actual = data
            for part in claim['pointer'].lstrip('/').split('/'):
                part = part.replace('~1', '/').replace('~0', '~')
                actual = actual[int(part)] if isinstance(actual, list) else actual[part]
        assert actual == claim['expected'], (claim['id'], actual, claim['expected'])
    historical = project / 'research/manuscript'
    assert (folder / 'figures/context-inputs.png').read_bytes() == (project / 'research/continued-agent-runs/v1/context-inputs.png').read_bytes()
    for name, expected in documents['research/manuscript/draft-manifest.json'].items():
        assert hashlib.sha256((historical / name).read_bytes()).hexdigest() == expected, name
    result = {'source_files_verified': len(ledger['sources']), 'facts_verified': len(ledger['facts']),
              'historical_draft_unchanged': True, 'data_revision': ledger['data_revision'],
              'scope': 'Hash and selected field/derivation consistency only. Not semantic claim validity, statistical replication, a formal proof or an automatic source refresh.'}
    (folder / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
