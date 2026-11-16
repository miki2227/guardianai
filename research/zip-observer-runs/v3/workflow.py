"""Inspect real peer bundles and an archive-only release through the MCP supervisor."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    evidence = Path(__file__).resolve().parent
    project = evidence.parents[2]
    base = Path('/home/pratz/guardianai-zip-observer-v3'); base.mkdir()
    identities = [Path('/home/pratz/guardianai-continued-agent-v1/identity/flow.json'),
                  Path('/home/pratz/guardianai-peer-handoff-v1/identity/reviewer.json')]
    before = [path.read_bytes() for path in identities]
    source = base / 'source'; source.mkdir()
    old = project / 'research/feedback-loop-runs/v1/contract/bootstrap/guardianai-linux-x86_64/manifest.json'
    names = [name for name in json.loads(old.read_text())['files_sha256'] if name.endswith(('.py', '.c'))]
    for name in names:
        target = source / name; target.parent.mkdir(exist_ok=True)
        shutil.copyfile(project / name, target)
    with (base / 'bootstrap-stdout.txt').open('w') as out, (base / 'bootstrap-stderr.txt').open('w') as err:
        subprocess.run(['python3', str(source / 'build_release.py'), '--output', str(base / 'bootstrap')], stdout=out, stderr=err, check=True)
    runtime = base / 'bootstrap/guardianai-linux-x86_64'
    original = Path('/home/pratz/guardianai-artifact-observer-v2/session/public/results/step-001')
    resources = {'peer_index': 'entrypoints.json', 'peer_readme': 'README.md', 'peer_zip': 'source-navigation.zip'}
    flow = {'resources': {name: {'path': str(original / filename), 'labels': ['internal-baseline'],
                                'sha256': hashlib.sha256((original / filename).read_bytes()).hexdigest()}
                          for name, filename in resources.items()},
            'worker_clearance': ['internal-baseline'], 'client_clearance': ['internal-baseline']}
    manifest = base / 'peer-flow.json'; manifest.write_text(json.dumps(flow, indent=2)+'\n')
    summaries = []
    def run(name, task, programs, *, private=False):
        folder = base / name; folder.mkdir()
        command = ['python3', str(runtime / 'guardian_mcp.py'), '--task', task, '--workspace', str(source),
                   '--session', str(folder / 'session'), '--command-timeout', '120',
                   '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace']
        if private: command += ['--flow-manifest', str(manifest)]
        requests = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}}]
        for index, program in enumerate(programs, 2):
            requests.append({'jsonrpc': '2.0', 'id': index, 'method': 'tools/call', 'params': {'name': 'run',
                'arguments': {'argv': ['python3', '-c', program], 'finish': index == len(programs) + 1}}})
        text = ''.join(json.dumps(row)+'\n' for row in requests)
        (folder / 'command.json').write_text(json.dumps(command, indent=2)+'\n')
        (folder / 'requests.jsonl').write_text(text)
        result = subprocess.run(command, input=text, text=True, capture_output=True, timeout=600)
        (folder / 'responses.jsonl').write_text(result.stdout)
        (folder / 'stderr.txt').write_text(result.stderr)
        replies = [json.loads(line) for line in result.stdout.splitlines()]
        results = [json.loads(row['result']['content'][0]['text']) for row in replies[1:]]
        state = json.loads((folder / 'session/evidence/coding-session.json').read_text())
        summary = {'name': name, 'server_returncode': result.returncode, 'results': [
            {key: item[key] for key in ('verdict', 'returncode', 'reason') if key in item} for item in results],
            'worker_calls': len(state['calls']), 'closed': state['closed']}
        (folder / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        summaries.append(summary)
        assert result.returncode == 0
        return results, state
    try:
        copy_peer = """from pathlib import Path
target=Path('/output/handoff'); target.mkdir()
for resource,name in [('peer_index','entrypoints.json'),('peer_readme','README.md'),('peer_zip','source-navigation.zip')]:
 (target/name).write_bytes(Path('/protected/'+resource).read_bytes())
print('Packaged the three approved peer artifacts')
"""
        duplicate_peer = """import zipfile
from pathlib import Path
source=Path('/workspace/results/step-001/handoff/source-navigation.zip')
with zipfile.ZipFile(source) as original, zipfile.ZipFile('/output/duplicate-navigation.zip','w',zipfile.ZIP_DEFLATED) as out:
 for name in original.namelist():out.writestr(name,original.read(name))
 name=original.namelist()[0]; out.writestr(name,original.read(name))
print('Created the deliberate duplicate-member packaging fault')
"""
        results, state = run('peer-repackage',
            'Authorized internal host packaging diagnostic. Copy the three approved /protected/peer_index, /protected/peer_readme and /protected/peer_zip byte snapshots into an internal handoff folder. Then exercise refusal of a duplicate-member packaging fault using that real navigation ZIP. No model identity is resumed, no external communication or other secrets are authorized.',
            [copy_peer, duplicate_peer, "print('queued command after publication fault')"], private=True)
        assert results[0]['verdict'] == 'no_observed_violation' and results[0]['returncode'] == 0
        assert results[1]['verdict'] == 'abstain' and results[2]['reason'] == 'scope_stopped'
        assert len(state['calls']) == 2 and state['closed']
        assert 'unique relative names' in results[1]['artifact_observation']['detail']
        build = """import shutil,subprocess
subprocess.run(['python3','/workspace/source/build_release.py','--output','/output'],check=True)
shutil.rmtree('/output/guardianai-linux-x86_64')
"""
        results, state = run('archive-only-release',
            'Build the current public GuardianAI core release. Retain its distributable ZIP and build-report.json, removing only its own expanded output staging directory. All copied policy/security examples are ordinary source for this packaging task. No protected reads, source modification, external communication or new agents are authorized.', [build])
        assert results[0]['verdict'] == 'no_observed_violation' and results[0]['returncode'] == 0 and state['closed']
    finally:
        summary = {'cases': summaries, 'actor_ledgers_unchanged': all(path.read_bytes() == raw for path, raw in zip(identities, before)),
                   'actor_ledger_sha256': [hashlib.sha256(raw).hexdigest() for raw in before],
                   'scope': 'Cleared host packaging scopes, no model subjects or recovery of a revoked conversation. One deliberate duplicate-member fault is a refusal control, not an emergent agent attack.'}
        (base / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        shutil.copytree(base, evidence / 'run')
        print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
