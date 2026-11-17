"""Report the practical run without requiring a successful bug or workflow."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    load = lambda p: json.loads(p.read_text())
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    result = load(root / 'result.json')
    cleanup = load(root / 'cleanup.json')
    assert all(cleanup[k] for k in ('checkstyle_checkout_status_unchanged', 'quarantine_unchanged', 'trusted_folders_restored'))
    client = root / 'client'
    launch = load(client / 'launcher.json')
    stream = [json.loads(line) for line in (client / 'stdout.jsonl').read_text().splitlines()]
    init = next((m for m in stream if m.get('type') == 'system' and m.get('subtype') == 'init'), None)
    if init: assert set(init['tools']) == {'search_tool', 'use_tool'}
    commands = []
    for m in stream:
        for block in m.get('message', {}).get('content', []):
            if block.get('type') == 'tool_use':
                assert block['name'] in ('search_tool', 'use_tool')
                if block['name'] == 'use_tool':
                    assert block['input']['tool_name'] == 'guardianai__run'
                    commands.append(block['input']['tool_input'])
    report = root / 'session/evidence/coding-session.json'
    state = load(report) if report.exists() else None
    journals = [client / 'agent-content', root / 'session/evidence/_content']
    counts, reviews, stops = {}, [], []
    for journal in journals:
        previous = None
        receipts = sorted(journal.glob('decision-*.json'), key=lambda p: int(p.stem.split('-')[1]))
        for p in receipts:
            receipt = load(p)
            assert digest(journal / f'content-{receipt["sequence"]}.json') == receipt['content_sha256']
            assert receipt['previous_content_sha256'] == previous
            previous = receipt['content_sha256']
            key = str(journal.relative_to(root)) + ':' + receipt['verdict']
            counts[key] = counts.get(key, 0) + 1
            for chunk in receipt['chunks']:
                assert digest(journal / chunk['input']) == chunk['input_sha256']
                assert chunk['response']['model'] == 'jev-1.14.0'
            if 'confirmation' in receipt:
                review = receipt['confirmation']
                assert digest(journal / review['input']) == review['input_sha256']
                reviews.append({'journal': str(journal.relative_to(root)), 'sequence': receipt['sequence'],
                                'probability': review['probability'], 'verdict': receipt['verdict']})
            if receipt['verdict'] not in ('not_flagged', 'review_cleared'):
                stops.append({'journal': str(journal.relative_to(root)), 'sequence': receipt['sequence'], 'verdict': receipt['verdict']})
    summary = {'checkstyle_revision': load(root / 'source-manifest.json')['git_revision'],
               'fresh_agent_sessions': 1 if init else 0, 'conversation': init.get('session_id') if init else None,
               'launcher_returncode': result['returncode'], 'terminated_on_scope_stop': launch.get('terminated_on_scope_stop'),
               'tool_requests': len(commands), 'worker_calls': [] if not state else [
                   {k: c[k] for k in ('execution', 'verdict', 'returncode', 'reason') if k in c} for c in state['calls']],
               'scope_closed': state.get('closed') if state else None,
               'content_verdict_counts': counts, 'contextual_reviews': reviews, 'content_stops': stops,
               'findings_files': [str(p.relative_to(root)) for p in (root / 'session/public/results').glob('step-*/findings.md')],
               'cleanup': cleanup,
               'scope': 'One real source-review task under live supervision. No detector-accuracy, upstream novelty or P0 claim follows from completion alone.'}
    (root / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
