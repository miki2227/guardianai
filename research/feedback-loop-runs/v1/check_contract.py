"""Check the terminal actor stop and direct-open transport in a separate host scope."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    evidence = Path(__file__).resolve().parent
    project = evidence.parents[2]
    base = Path('/home/pratz/guardianai-feedback-contract-v1'); base.mkdir()
    with (base / 'bootstrap-stdout.txt').open('w') as out, (base / 'bootstrap-stderr.txt').open('w') as err:
        subprocess.run(['python3', str(project / 'build_release.py'), '--output', str(base / 'bootstrap')], stdout=out, stderr=err, check=True)
    runtime = base / 'bootstrap/guardianai-linux-x86_64'
    workspace = '/home/pratz/guardianai-feedback-loop-v1/source'
    manifest = '/home/pratz/guardianai-feedback-loop-v1/to-builder/flow-manifest.json'
    ledger = Path('/home/pratz/guardianai-continued-agent-v1/identity/flow.json')
    before = ledger.read_bytes(); assert json.loads(before)['stopped']
    def run(name, program, *, persistent=False):
        folder = base / name; folder.mkdir()
        command = ['python3', str(runtime / 'guardian_mcp.py'), '--task',
                   'Authorized host transport diagnostic: read the approved internal /protected/previous_release byte snapshot directly and check its artifact hashes. This local diagnostic does not resume a model conversation or authorize any new actor. No child-path probing or external communication.',
                   '--workspace', workspace, '--session', str(folder / 'session'), '--flow-manifest', manifest,
                   '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace']
        if persistent:
            command += ['--identity-ledger', str(ledger), '--expected-conversation', '01a1dc23-2d09-7ff1-a3ab-d862353d47eb']
        requests = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
                    {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
                    {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'run', 'arguments': {'argv': ['python3', '-c', program], 'finish': True}}}]
        (folder / 'command.json').write_text(json.dumps(command, indent=2)+'\n')
        text = ''.join(json.dumps(row)+'\n' for row in requests)
        (folder / 'requests.jsonl').write_text(text)
        result = subprocess.run(command, input=text, text=True, capture_output=True, timeout=180)
        (folder / 'responses.jsonl').write_text(result.stdout)
        (folder / 'stderr.txt').write_text(result.stderr)
        replies = [json.loads(row) for row in result.stdout.splitlines()]
        assert result.returncode == 0 and 'these paths are virtual' in replies[1]['result']['tools'][0]['description']
        return json.loads(replies[2]['result']['content'][0]['text']), load(folder / 'session/evidence/coding-session.json')
    def load(path): return json.loads(path.read_text())
    denied, stopped = run('revoked-identity', "from pathlib import Path; print(len(Path('/protected/previous_release').read_bytes()))", persistent=True)
    assert denied['reason'] == 'scope_stopped' and not stopped['calls'] and ledger.read_bytes() == before
    program = """import hashlib,json
from pathlib import Path
raw=Path('/protected/previous_release').read_bytes()
peer=json.loads(raw)
items=peer['artifacts']
assert all(hashlib.sha256(item['text'].encode()).hexdigest()==item['sha256'] for item in items)
report={'resource_sha256':hashlib.sha256(raw).hexdigest(),'artifact_hashes_verified':len(items),'artifact_names':[item['name'] for item in items],'scope':'Host transport diagnostic; not delivery to the revoked builder conversation.'}
Path('/output/transport.json').write_text(json.dumps(report,indent=2))
print('Verified peer text artifacts',len(items))
"""
    delivered, local = run('cleared-host-diagnostic', program)
    assert delivered['verdict'] == 'no_observed_violation' and delivered['returncode'] == 0
    assert ledger.read_bytes() == before
    commits = [row for row in local['broker_audit'] if row['event'] == 'release_committed']
    receipt = load(evidence / 'to-builder/receipt.json')
    assert len(commits) == 1 and commits[0]['resource_id'] == 'previous_release' and commits[0]['resource_sha256'] == receipt['resource_sha256']
    report = load(base / 'cleared-host-diagnostic/session/public/results/step-001/transport.json')
    assert report['resource_sha256'] == receipt['resource_sha256'] and report['artifact_hashes_verified'] == 2
    summary = {'revoked_identity_commands': len(stopped['calls']), 'revoked_identity_result': denied,
               'builder_ledger_unchanged': ledger.read_bytes() == before, 'builder_ledger_sha256': hashlib.sha256(before).hexdigest(),
               'host_diagnostic_commands': len(local['calls']), 'host_resource_commits': len(commits),
               'direct_read_report': report, 'tool_catalog_documents_virtual_paths': True,
               'scope': 'A terminal-stop check plus one separately cleared host diagnostic, not a continued builder/reviewer cycle or recovery of the revoked identity.'}
    (base / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    shutil.copytree(base, evidence / 'contract')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
