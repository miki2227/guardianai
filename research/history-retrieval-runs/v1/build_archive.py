"""Build and query an evidence archive from the actual completed paired workflow."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT))
from evidence_memory import EvidenceMemory, fit_history


def main():
    root = Path(__file__).resolve().parent
    stored = root / 'stored-sources'
    stored.mkdir()
    previous = PROJECT / 'research/paired-workflow-runs/v2'
    summary = json.loads((previous / 'summary.json').read_text())
    manifest = []
    memory = EvidenceMemory(root)
    for phase in summary['phases']:
        for location, pattern, kind in [(previous / (phase['scope'] + '-client/agent-content'), 'content-*.json', 'host_agent_content'),
                                         (previous / phase['evidence_scope'] / 'session/evidence/_content', 'content-*.json', 'tool_content'),
                                         (previous / phase['evidence_scope'] / 'session/evidence/_observer', 'input-*.json', 'runtime_state')]:
            for source in sorted(location.glob(pattern), key=lambda p: int(p.stem.split('-')[1])):
                relative = source.relative_to(previous)
                target = stored / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                memory.record(target, kind)
                manifest.append({'source': str(source.relative_to(PROJECT)), 'stored': str(target.relative_to(root)),
                                 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'phase': phase['phase'], 'kind': kind})
    for folder in previous.glob('handoff-observer*'):
        for source in sorted(folder.glob('content-*.json'), key=lambda p: int(p.stem.split('-')[1])):
            target = stored / source.relative_to(previous)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            memory.record(target, 'agent_handoff')
            manifest.append({'source': str(source.relative_to(PROJECT)), 'stored': str(target.relative_to(root)),
                             'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'phase': 'handoff', 'kind': 'agent_handoff'})
    (root / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # Exclude the final phase so these queries must recover earlier evidence.
    excluded = [root / row['stored'] for row in manifest if row['phase'] == 'final']
    final = next(p for p in (previous / 'final-recovery/session/public/results').glob('step-*/release-decision.json'))
    queries = [('published_archive_hash', summary['build']['sha256']), ('final_review_decision', final.read_text())]
    results = []
    for name, text in queries:
        state = {'current_content': text, 'history_retrieval': memory.lookup(text, exclude=excluded)}
        fit_history(state)
        for hit in state['history_retrieval']['hits']:
            raw = (root / hit['source']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == hit['sha256']
            start = hit['start_character']
            assert raw.decode()[start:start + len(hit['excerpt'])] == hit['excerpt']
            assert all(hit['source'] != str(p.relative_to(root)) for p in excluded)
        (root / (name + '-context.json')).write_text(json.dumps(state, indent=2) + '\n')
        results.append({'query': name, 'matched_records': state['history_retrieval']['matched_records'],
                        'returned_records': len(state['history_retrieval']['hits']),
                        'matched_records_omitted': state['history_retrieval']['matched_records_omitted'],
                        'context_bytes': len(json.dumps(state).encode())})
    outcome = {'indexed_records': len(manifest), 'queries': results, 'source_hashes_and_excerpt_spans_verified': True,
               'scope': 'Actual archived agent/tool/runtime evidence; lexical search with final-phase sources excluded. Import order is not a global causal clock. No new Jev or Grok calls, no synthetic messages, no claim of detection improvement or provider context exhaustion.'}
    (root / 'archive-summary.json').write_text(json.dumps(outcome, indent=2) + '\n')
    print(json.dumps(outcome, indent=2))


if __name__ == '__main__':
    main()
