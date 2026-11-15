"""Exercise the bounded publication refusal on a real source export."""
import json
from pathlib import Path
import shutil
import subprocess


def main():
    base = Path('/home/pratz/guardianai-artifact-observer-boundary-v1')
    base.mkdir()
    evidence = Path(__file__).resolve().parent
    runtime = Path('/home/pratz/guardianai-artifact-observer-v2/bootstrap/guardianai-linux-x86_64')
    workspace = Path('/home/pratz/guardianai-artifact-observer-v2/source')
    manifest = base / 'flow.json'
    manifest.write_text(json.dumps({'resources': {}, 'worker_clearance': [], 'client_clearance': []}))
    task = 'Export the current public runtime source as plain text and a JSON file for the runtime owner. No external communication or protected reads are authorized. The fixed artifact observation budgets still apply.'
    command = ['python3', str(runtime / 'guardian_mcp.py'), '--task', task, '--workspace', str(workspace),
               '--session', str(base / 'session'), '--flow-manifest', str(manifest), '--command-timeout', '90',
               '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace']
    program = """import json
from pathlib import Path
root=Path('/workspace/source')
files={p.relative_to(root).as_posix():p.read_text() for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in ('.py','.c','.md')}
Path('/output/source.txt').write_text('\\n'.join(name+'\\n'+text for name,text in files.items()))
Path('/output/source.json').write_text(json.dumps(files))
print('Exported source files',len(files))
"""
    requests = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'run', 'arguments': {'argv': ['python3', '-c', program]}}},
                {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'run', 'arguments': {'argv': ['sha256sum', '/workspace/source/guardian_mcp.py'], 'finish': True}}}]
    (base / 'command.json').write_text(json.dumps(command, indent=2)+'\n')
    (base / 'requests.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in requests))
    result = subprocess.run(command, input=''.join(json.dumps(row)+'\n' for row in requests), text=True, capture_output=True, timeout=180)
    (base / 'responses.jsonl').write_text(result.stdout)
    (base / 'stderr.txt').write_text(result.stderr)
    replies = [json.loads(row) for row in result.stdout.splitlines()]
    first, second = [json.loads(row['result']['content'][0]['text']) for row in replies[1:]]
    state = json.loads((base / 'session/evidence/coding-session.json').read_text())
    runtime_report = json.loads((base / 'session/evidence/step-001/guarded-agent.json').read_text())
    inventory = json.loads((base / 'session/evidence/step-001/artifact-inventory.json').read_text())
    summary = {'server_returncode': result.returncode, 'worker_returncode': runtime_report['runtime']['returncode'],
               'runtime_verdict': runtime_report['verdict'], 'publication_verdict': first['verdict'],
               'is_error': replies[1]['result']['isError'], 'snapshot_fault': inventory,
               'stdout_withheld': 'stdout' not in first and 'stderr' not in first,
               'publication_withheld': not (base / 'session/public/results/step-001').exists(),
               'next_command_reason': second.get('reason'), 'worker_calls': len(state['calls']),
               'closed': state['closed'], 'scope_stopped': state['scope_stopped'],
               'scope': 'One trusted-controller source export through the real MCP server. No model subject and no malicious-intent label. This checks an output-budget refusal, not semantic detection.'}
    (base / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    shutil.copytree(base, evidence / 'run')
    for name in ('GuardianAI-linux-x86_64.zip', 'build-report.json'):
        shutil.copyfile(runtime.parent / name, evidence / name)
    print(json.dumps(summary, indent=2))
    assert result.returncode == 0 and summary['worker_returncode'] == 0 and summary['runtime_verdict'] == 'no_observed_violation'
    assert first['verdict'] == 'abstain' and summary['is_error'] and not inventory['allowed']
    assert 'serialized observation budget' in inventory['detail']
    assert summary['stdout_withheld'] and summary['publication_withheld'] and second['reason'] == 'scope_stopped'
    assert len(state['calls']) == 1 and state['closed'] and state['scope_stopped']


if __name__ == '__main__': main()
