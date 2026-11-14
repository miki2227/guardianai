"""Import the eight corrected historical social episodes; no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from context_record import record_turn, verify_record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    root = args.destination.resolve()
    root.mkdir(parents=True, exist_ok=False)
    project = Path(__file__).resolve().parents[1]
    episodes = ['full-history-s103', 'fixed-s104', 'fixed-s105', 'fixed-s106',
                'context-s103', 'context-s104', 'context-s105', 'context-s106']
    records = []
    for episode in episodes:
        folder = project / 'research/social-runs' / episode
        for role in ('sender', 'receiver'):
            destination = root / (episode + '-' + role)
            record = record_turn(destination, folder / (role + '-metadata.json'),
                                 folder / (role + '-prompt.json'), folder / (role + '-reply.txt'))
            verify_record(destination)
            records.append({key: record[key] for key in ('run_id', 'subject_thread_id', 'context_condition',
                                                        'provider_reported_usage', 'context_pressure')})
    result = {'records': records, 'verified_records': len(records),
              'declared_resets': sum(r['context_condition'] == 'declared_reset' for r in records),
              'reported_usage_available': sum(r['provider_reported_usage'] is not None for r in records),
              'scope': 'Retrospective import of the corrected historical block; no new inference, retained-context measurement or context exhaustion.'}
    for name in ('context_record.py', 'research/context_import.py'):
        target = root / 'source-snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project / name, target)
    (root / 'source-sha256.json').write_text(json.dumps({name: hashlib.sha256((project / name).read_bytes()).hexdigest()
                                                      for name in ('context_record.py', 'research/context_import.py')}, indent=2) + '\n')
    (root / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'records'}))
