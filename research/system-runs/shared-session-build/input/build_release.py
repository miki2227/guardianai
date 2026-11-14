"""Build a local Linux x86-64 core-runtime distribution from this checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    stage = output / 'guardianai-linux-x86_64'
    stage.mkdir(exist_ok=False)
    (stage / 'native').mkdir()
    names = ['guardian.py', 'monitor.py', 'runtime_supervisor.py', 'release_broker.py',
             'seccomp_gate.py', 'guarded_agent.py', 'guarded_session.py', 'build_release.py', 'native/notify_launch.c']
    for name in names:
        shutil.copyfile(project / name, stage / name)
    command = ['gcc', '-Wall', '-Wextra', '-Werror', '-O2', str(stage / 'native/notify_launch.c'),
               '-o', str(stage / 'native/notify-launch')]
    subprocess.run(command, check=True)
    abi = json.loads(subprocess.check_output([str(stage / 'native/notify-launch'), '--abi']))
    if abi.get('policy_version') != 3:
        raise RuntimeError('Built launcher policy does not match this release')
    (stage / 'RUNNING.txt').write_text(
        'GuardianAI core runtime for Linux x86-64\n\n'
        'Requires Python 3.10+, Bubblewrap with user namespaces, and strace with native stack support.\n'
        'Provide TYPESAFE_API_KEY only to the trusted supervisor environment.\n'
        'Use a dedicated public input directory, an empty output directory and a new evidence directory.\n'
        'Keep protected resources outside every public/runtime mount; snapshots are limited to 32 KiB.\n\n'
        'python3 guarded_agent.py --task "Read the approved summary" --workspace /path/to/public '
        '--output /path/to/empty-output --evidence /path/to/new-evidence --sensor /path/to/strace '
        '--resource summary=/path/to/private/summary.txt -- /usr/bin/cat /protected/summary\n\n'
        'Workers cannot install their own seccomp filters in this profile.\n'
        'For multiple workers: python3 guarded_session.py --manifest /path/to/session.json --evidence /path/to/new-evidence --sensor /path/to/strace\n'
        'Session manifests are trusted host configuration with task, resources, and workers. Each worker supplies name, workspace, output, command, and resource-name array resources.\n'
        'Exit 77: detected violation. Exit 78: abstention. Otherwise the worker exit status is preserved.\n'
        'This archive contains the core runtime; historical research evidence is retained in the source project.\n'
        'OS evidence observes execution and cannot reveal latent model thoughts.\n')
    files = sorted(p for p in stage.rglob('*') if p.is_file())
    manifest = {'architecture': 'Linux x86-64', 'native_policy': abi['policy_version'],
                'files_sha256': {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                'compiler_argv': command,
                'scope': 'Core runtime distribution, excluding historical research datasets and credentials.'}
    (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    archive = output / 'GuardianAI-linux-x86_64.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(p for p in stage.rglob('*') if p.is_file()):
            bundle.write(path, path.relative_to(stage))
    report = {'archive': archive.name, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'bytes': archive.stat().st_size, 'native_policy': abi['policy_version'],
              'file_count': len(manifest['files_sha256']) + 1}
    (output / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
