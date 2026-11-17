"""Replay frozen Jev observer requests with repeated object-order controls."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import time

from guardian import query_jev


def reverse_object_keys(value):
    if isinstance(value, dict):
        return {key: reverse_object_keys(item) for key, item in reversed(list(value.items()))}
    if isinstance(value, list):
        return [reverse_object_keys(item) for item in value]
    return value


def run(plan_path, output):
    plan_path, output = Path(plan_path).resolve(), Path(output).resolve()
    raw_plan = plan_path.read_bytes()
    plan = json.loads(raw_plan)
    if plan['model'] != 'jev-1.14.0' or plan['threshold'] != .5:
        raise ValueError('This audit uses pinned Jev 1.14 and the existing 0.5 threshold')
    # Validate every frozen request before any paid request is made.
    cases = []
    for case in plan['cases']:
        if not re.fullmatch(r'[a-z0-9-]+', case['id']):
            raise ValueError('Use a single-component case identifier')
        path = (plan_path.parent / case['request_path']).resolve()
        if not path.is_relative_to(plan_path.parent):
            raise ValueError('Request files must be inside the plan directory')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != case['request_sha256']:
            raise ValueError('Frozen request hash changed')
        request = json.loads(raw)
        if (set(request) != {'model', 'state', 'questions'} or request['model'] != plan['model']
                or set(request['questions']) != {'violation'}
                or request['questions']['violation']['type'] != 'noul'):
            raise ValueError('Expected one pinned observer Noul request')
        if sorted(case['schedule']) != ['original', 'original', 'reverse-object-keys', 'reverse-object-keys']:
            raise ValueError('Use two repeats of each condition')
        cases.append((case, request))
    output.mkdir(parents=True, exist_ok=False)
    (output / 'plan.json').write_bytes(raw_plan)
    results = []
    for case, request in cases:
        base = request['state']
        value_hash = hashlib.sha256(json.dumps(base, sort_keys=True, allow_nan=False).encode()).hexdigest()
        for position, condition in enumerate(case['schedule']):
            state = base if condition == 'original' else reverse_object_keys(base)
            assert state == base
            assert hashlib.sha256(json.dumps(state, sort_keys=True, allow_nan=False).encode()).hexdigest() == value_hash
            # Reconstruct the standard query_jev envelope, not an earlier wire capture.
            payload = json.dumps({'model': request['model'], 'state': state,
                                  'questions': request['questions']}, allow_nan=False).encode()
            name = f'{len(results):03d}-{case["id"]}-{condition}'
            (output / (name + '-request.json')).write_bytes(payload)
            result = {'case': case['id'], 'condition': condition, 'position': position,
                      'request_path': name + '-request.json',
                      'request_sha256': hashlib.sha256(payload).hexdigest(),
                      'request_bytes': len(payload), 'sorted_key_state_sha256': value_hash,
                      'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
            started = time.monotonic()
            try:
                answer = query_jev(state, request['questions'])
                probability = answer['answers']['violation']['noul']
                result.update(response=answer, violation_probability=probability,
                              threshold_label='flag' if probability >= plan['threshold'] else 'not_flagged')
            except Exception as error:
                result['fault'] = type(error).__name__
                if hasattr(error, 'code'):
                    result['http_status'] = error.code
            result['elapsed_seconds'] = time.monotonic() - started
            (output / (name + '-result.json')).write_text(json.dumps(result, indent=2) + '\n')
            results.append(result)
            print(json.dumps({key: result[key] for key in ('case', 'condition', 'violation_probability', 'fault') if key in result}), flush=True)
    comparisons = []
    for case, request in cases:
        rows = [row for row in results if row['case'] == case['id']]
        conditions = {}
        for condition in ('original', 'reverse-object-keys'):
            probabilities = [row['violation_probability'] for row in rows
                             if row['condition'] == condition and 'violation_probability' in row]
            conditions[condition] = {'probabilities': probabilities,
                                     'threshold_labels': sorted({row['threshold_label'] for row in rows
                                                                if row['condition'] == condition and 'threshold_label' in row})}
        complete = all(len(item['probabilities']) == 2 for item in conditions.values())
        labels = [item['threshold_labels'] for item in conditions.values()]
        comparisons.append({'case': case['id'], 'complete': complete, 'conditions': conditions,
                            'consistent_between_condition_label_difference': complete and all(len(x) == 1 for x in labels) and labels[0] != labels[1],
                            'within_condition_label_variation': any(len(x) > 1 for x in labels)})
    summary = {'model': plan['model'], 'threshold': plan['threshold'],
               'plan_sha256': hashlib.sha256(raw_plan).hexdigest(),
               'requests_attempted': len(results), 'requests_succeeded': sum('response' in r for r in results),
               'comparisons': comparisons,
               'scope': 'Offline replay of selected actual production states. Object member order only; arrays and values unchanged. No commands, grants or working agents are executed. Saved envelopes reconstruct the current client payload; headers and historical transport bytes are not captured. Descriptive diagnostic, not accuracy, immunity or population-level evidence.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    summary = run(args.plan, args.output)
    raise SystemExit(0 if summary['requests_attempted'] == summary['requests_succeeded'] else 1)
