"""Run a trusted multi-worker manifest under shared Jev/kernel supervision."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from guarded_agent import load_resources, run_worker
from guardian import sandbox_argv
from release_broker import ReleaseBroker


def run(manifest, *, evidence, sensor='strace'):
    if sys.platform != 'linux' or not os.environ.get('TYPESAFE_API_KEY'):
        raise RuntimeError('Linux and the trusted supervisor Jev credential are required')
    from seccomp_gate import SeccompGate
    raw = Path(manifest).read_bytes()
    config = json.loads(raw)
    if set(config) != {'task', 'resources', 'workers'} or not isinstance(config['task'], str) or not config['task'].strip():
        raise ValueError('Manifest requires task, resources and workers')
    workers = config['workers']
    if not isinstance(workers, list) or not 1 <= len(workers) <= 16:
        raise ValueError('Use between one and sixteen local workers')
    evidence = Path(evidence).resolve()
    names, outputs, public_roots, grants = set(), [], [], {}
    for worker in workers:
        if set(worker) != {'name', 'workspace', 'output', 'command', 'resources'}:
            raise ValueError('Each worker requires name, workspace, output, command and resources')
        name = worker['name']
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}', name) or name in names:
            raise ValueError('Worker names must be unique single components')
        names.add(name)
        if not isinstance(worker['command'], list) or not worker['command'] or any(type(a) is not str for a in worker['command']):
            raise ValueError('Worker commands must be nonempty argv arrays')
        sandbox_argv(worker['workspace'], worker['command'], output=worker['output'])
        workspace, output = Path(worker['workspace']).resolve(), Path(worker['output']).resolve()
        public_roots.append(workspace)
        outputs.append(output)
        if not isinstance(worker['resources'], list) or any(type(r) is not str for r in worker['resources']):
            raise ValueError('Worker resources must be resource-name arrays')
        grants[name] = set(worker['resources'])
    for i, output in enumerate(outputs):
        for other in [*public_roots, *outputs[:i]]:
            if output.is_relative_to(other) or other.is_relative_to(output):
                raise ValueError('Worker outputs must be disjoint from all inputs and other outputs')
    public_roots += outputs
    for path in public_roots:
        if path.is_relative_to(evidence) or evidence.is_relative_to(path):
            raise ValueError('Session evidence must be disjoint from every worker mount')
    launcher = Path(__file__).resolve().parent / 'native/notify-launch'
    public_roots += [Path(p).resolve() for p in ('/usr', '/bin', '/lib', '/lib64') if Path(p).exists()]
    if not isinstance(config['resources'], dict):
        raise ValueError('Session resources must map names to protected host files')
    snapshots = load_resources(config['resources'], public_roots, launcher)
    if any(not value.issubset(snapshots) for value in grants.values()):
        raise ValueError('Worker grant names must refer to provisioned resources')
    broker = ReleaseBroker(config['task'], snapshots, grants)
    SeccompGate(broker, workers[0]['name'], launcher)  # Refuse incompatible helpers before any worker starts.
    evidence.mkdir(parents=True, exist_ok=False)
    (evidence / 'manifest.json').write_bytes(raw)
    results = {}
    def worker_run(worker):
        name = worker['name']
        try:
            return run_worker(config['task'] + ' Current worker: ' + name + '.', worker['workspace'],
                              worker['command'], output=worker['output'], evidence=evidence / name,
                              sensor=sensor, broker=broker, principal=name, launcher=launcher)
        except Exception as error:
            broker.lose_evidence()
            return {'verdict': 'abstain', 'principal': name, 'reason': type(error).__name__}
    with ThreadPoolExecutor(max_workers=len(workers)) as executor:
        futures = {executor.submit(worker_run, worker): worker['name'] for worker in workers}
        try:
            for future in as_completed(futures):
                results[futures[future]] = future.result()
        except BaseException:
            broker.lose_evidence()
            raise
    verdicts = {r['verdict'] for r in results.values()}
    verdict = 'abstain' if 'abstain' in verdicts else 'violation' if 'violation' in verdicts else 'no_observed_violation'
    with broker.lock:
        audit = copy.deepcopy(broker.audit)
    result = {'verdict': verdict, 'workers': results, 'broker_audit': audit,
              'manifest_sha256': hashlib.sha256(raw).hexdigest(),
              'scope': 'Declared local workers only; shared terminal revocation, bounded streamed Jev event batches, no latent-thought visibility.'}
    (evidence / 'session.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--evidence', required=True)
    parser.add_argument('--sensor', default='strace')
    args = parser.parse_args()
    try:
        result = run(args.manifest, evidence=args.evidence, sensor=args.sensor)
        print(json.dumps({'verdict': result['verdict'], 'workers': list(result['workers']), 'evidence': str(Path(args.evidence).resolve())}))
        status = 78 if result['verdict'] == 'abstain' else 77 if result['verdict'] == 'violation' else int(any(
            worker['runtime']['returncode'] != 0 for worker in result['workers'].values()))
    except Exception as error:
        print(json.dumps({'verdict': 'abstain', 'reason': type(error).__name__}))
        status = 78
    sys.exit(status)
