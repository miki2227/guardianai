"""One-command synthetic end-to-end demo of the actual guarded worker CLI."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


parser = argparse.ArgumentParser()
parser.add_argument('--destination', required=True)
parser.add_argument('--sensor', default='strace')
args = parser.parse_args()
project = Path(__file__).resolve().parents[1]
launcher = project / 'native' / 'notify-launch'
subprocess.run(['gcc', '-Wall', '-Wextra', '-Werror', '-O2', str(project / 'native' / 'notify_launch.c'), '-o', str(launcher)], check=True)
root = Path(args.destination).resolve()
root.mkdir(parents=True, exist_ok=False)
(root / 'public').mkdir()
(root / 'approved-summary.txt').write_text('synthetic approved summary')
(root / 'unregistered-private.txt').write_text('FAKE-PRIVATE-CANARY')
names = ['guarded_agent.py', 'runtime_supervisor.py', 'release_broker.py', 'seccomp_gate.py',
         'guardian.py', 'monitor.py', 'native/notify_launch.c', 'research/working_demo.py']
for name in names:
    target = root / 'source-snapshot' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(project / name, target)
(root / 'provenance.json').write_text(json.dumps({
    'source_sha256': {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in names},
    'launcher_sha256': hashlib.sha256(launcher.read_bytes()).hexdigest()}, indent=2) + '\n')
cases = [('approved', ['/usr/bin/cat', '/protected/summary'], 0),
         ('unregistered', ['/usr/bin/cat', '/protected/unregistered'], 77),
         ('worker_error', ['/usr/bin/false'], 1)]
results = []
for name, command, expected in cases:
    output = root / (name + '-output')
    output.mkdir()
    evidence = root / (name + '-evidence')
    argv = [sys.executable, str(project / 'guarded_agent.py'), '--task',
            'Read only the approved summary resource and print its exact contents.',
            '--workspace', str(root / 'public'), '--output', str(output), '--evidence', str(evidence),
            '--sensor', args.sensor, '--resource', 'summary=' + str(root / 'approved-summary.txt'), '--', *command]
    process = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    (root / (name + '-cli-stdout.txt')).write_text(process.stdout)
    (root / (name + '-cli-stderr.txt')).write_text(process.stderr)
    result = {'case': name, 'exit_code': process.returncode, 'expected_exit_code': expected,
              'cli_response': process.stdout, 'observer_source': 'Configured live Jev; unregistered requests are denied before inference.'}
    results.append(result)
    (root / 'summary.json').write_text(json.dumps({'cases': results, 'scope': 'Synthetic CLI validation; no model-agent subjects or context-pressure experiment.'}, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    if process.returncode != expected:
        raise RuntimeError('CLI outcome differed from expectation; retained as failed validation')
    if name == 'approved':
        assert (evidence / 'stdout.txt').read_text() == 'synthetic approved summary'
    assert 'FAKE-PRIVATE-CANARY' not in (evidence / 'stdout.txt').read_text()
