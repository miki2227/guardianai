"""Provision native WSL storage and retain the complete MCP workflow evidence."""
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    project = Path(__file__).resolve().parents[3]
    evidence = Path(__file__).resolve().parent
    native = '/home/pratz/guardianai-mcp-flow-v1'
    root = Path(r'\\wsl.localhost\kali-linux\home\pratz\guardianai-mcp-flow-v1')
    root.mkdir()
    source = root / 'source'
    source.mkdir()
    names = ['guardian.py', 'monitor.py', 'runtime_supervisor.py', 'release_broker.py',
             'seccomp_gate.py', 'guarded_agent.py', 'guarded_session.py', 'session_observer.py',
             'agent_observer.py', 'decision_review.py', 'evidence_memory.py', 'flow_policy.py',
             'guarded_handoff.py', 'guardian_mcp.py', 'build_release.py', 'native/notify_launch.c']
    for name in names:
        target = source / name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(project / name, target)
    shutil.copytree(source, evidence / 'source')
    (root / 'private').mkdir()
    baseline = project / 'research/history-retrieval-runs/v1/build-run/session/public/results/step-001/guardianai-linux-x86_64/manifest.json'
    shutil.copyfile(baseline, root / 'private/previous-manifest.json')
    (evidence / 'baseline-source.json').write_text(json.dumps({'source': str(baseline.relative_to(project)),
        'classification': 'Controlled internal-baseline label on real release metadata, not an actual secret'}, indent=2) + '\n')
    shutil.copyfile(evidence / 'workflow.py', root / 'workflow.py')
    environment = dict(os.environ)
    forwarding = [item for item in environment.get('WSLENV', '').split(':') if item and item.split('/')[0] != 'TYPESAFE_API_KEY']
    environment['WSLENV'] = ':'.join(forwarding + ['TYPESAFE_API_KEY/u'])
    subprocess.run(['wsl.exe', '-d', 'kali-linux', '--', 'python3', native + '/source/build_release.py',
                    '--output', native + '/bootstrap'], check=True, env=environment)
    with (evidence / 'stdout.txt').open('wb') as stdout, (evidence / 'stderr.txt').open('wb') as stderr:
        result = subprocess.run(['wsl.exe', '-d', 'kali-linux', '--', 'python3', native + '/workflow.py'],
                                 stdout=stdout, stderr=stderr, env=environment, timeout=300)
    for name in ('public-client', 'internal-client'):
        if (root / name).exists():
            shutil.copytree(root / name, evidence / name)
    (evidence / 'client.json').write_text(json.dumps({'returncode': result.returncode, 'native_root': native}, indent=2) + '\n')
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
