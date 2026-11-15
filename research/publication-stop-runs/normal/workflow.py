"""Complete the same source-hash/ZIP workload without operator cancellation."""
import json
from pathlib import Path
import shutil
import subprocess


def main():
    previous = Path('/home/pratz/guardianai-publication-stop-v3')
    base = Path('/home/pratz/guardianai-publication-stop-normal-v1')
    base.mkdir()
    command = json.loads((previous / 'command.json').read_text())
    command[command.index('--session') + 1] = str(base / 'session')
    requests = (previous / 'requests.jsonl').read_text()
    (base / 'command.json').write_text(json.dumps(command, indent=2)+'\n')
    (base / 'requests.jsonl').write_text(requests)
    result = subprocess.run(command, input=requests, text=True, capture_output=True, timeout=180)
    (base / 'responses.jsonl').write_text(result.stdout)
    (base / 'stderr.txt').write_text(result.stderr)
    replies = [json.loads(row) for row in result.stdout.splitlines()]
    values = [json.loads(row['result']['content'][0]['text']) for row in replies[1:]]
    state = json.loads((base / 'session/evidence/coding-session.json').read_text())
    summary = {'server_returncode': result.returncode, 'worker_returncodes': [row.get('returncode') for row in values],
               'verdicts': [row['verdict'] for row in values], 'client_errors': [row['result']['isError'] for row in replies[1:]],
               'publication_exists': (base / 'session/public/results/step-001/source-hashes.zip').is_file(),
               'worker_calls': len(state['calls']), 'closed': state['closed'],
               'scope': 'The same task, source snapshot, packaged runtime and requests as corrected cancellation, without an external-stop request. No model subject or new attack scenario.'}
    (base / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    shutil.copytree(base, Path(__file__).resolve().parent / 'run')
    print(json.dumps(summary, indent=2))
    assert result.returncode == 0 and summary['worker_returncodes'] == [0, 0]
    assert summary['verdicts'] == ['no_observed_violation', 'no_observed_violation'] and not any(summary['client_errors'])
    assert summary['publication_exists'] and summary['worker_calls'] == 2 and summary['closed']


if __name__ == '__main__': main()
