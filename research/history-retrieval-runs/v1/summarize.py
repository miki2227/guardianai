"""Check live retrieval receipts and exact source spans from the real build."""
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    run = root / 'build-run'
    evidence = run / 'session/evidence'
    session = json.loads((evidence / 'coding-session.json').read_text())
    assert session['closed'] and all(c['verdict'] == 'no_observed_violation' and c['returncode'] == 0 for c in session['calls'])
    observations = []
    hits, maximum_state, inputs_with_hits = 0, 0, 0
    for path in sorted((evidence / '_observer').glob('input-*.json'), key=lambda p: int(p.stem.split('-')[1])):
        raw = path.read_bytes()
        assert len(raw) <= 20 * 1024
        maximum_state = max(maximum_state, len(raw))
        state = json.loads(raw)
        index = int(path.stem.split('-')[1])
        receipt = json.loads((path.parent / f'decision-{index}.json').read_text())
        assert digest(path) == receipt['input_sha256']
        history = state['history_retrieval']
        assert history['matched_records_omitted'] == history['matched_records'] - len(history['hits'])
        assert history['indexed_records'] == index
        inputs_with_hits += bool(history['hits'])
        for hit in history['hits']:
            source = path.parent / history['root_relative_to_input'] / hit['source']
            assert digest(source) == hit['sha256']
            text = source.read_bytes().decode()
            start = hit['start_character']
            assert text[start:start + len(hit['excerpt'])] == hit['excerpt']
            earlier = int(source.stem.split('-')[1])
            assert index - earlier >= 9
            hits += 1
        observations.append({'input': path.name, 'indexed_records': history['indexed_records'],
                             'matched_records': history['matched_records'], 'returned': len(history['hits']),
                             'matched_records_omitted': history['matched_records_omitted'], 'state_bytes': len(raw)})
    with sqlite3.connect(evidence / '_observer/history.sqlite3') as db:
        assert db.execute('SELECT COUNT(*) FROM documents').fetchone()[0] == len(observations)
    report, = (run / 'session/public/results').glob('step-*/build-report.json')
    build = json.loads(report.read_text())
    assert digest(report.parent / build['archive']) == build['sha256']
    with zipfile.ZipFile(report.parent / build['archive']) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        for name, expected in manifest['files_sha256'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected
            if (run / 'source' / name).is_file():
                assert digest(run / 'source' / name) == expected
    result = {'commands': session['calls'], 'closed': session['closed'], 'build': build,
              'runtime_observer_inputs': len(observations), 'inputs_with_retrieval': inputs_with_hits,
              'verified_retrieved_spans': hits, 'maximum_state_bytes': maximum_state,
              'observations': observations,
              'scope': 'Live Jev build and inspection. Retrieved native states precede the last-eight-input window, with source hashes and exact spans verified. No detection improvement, context saturation or complete-history visibility claim. No new Grok agents.'}
    (root / 'live-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('closed', 'runtime_observer_inputs', 'inputs_with_retrieval', 'verified_retrieved_spans', 'maximum_state_bytes', 'build')}, indent=2))


if __name__ == '__main__':
    main()
