"""Cancel a real source-index publication while its final Jev check is pending."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid
import zipfile


def main():
    evidence = Path(__file__).resolve().parent
    project = evidence.parents[2]
    base = Path('/home/pratz/guardianai-publication-stop-v2')
    base.mkdir()
    source = base / 'source'
    shutil.copytree('/home/pratz/guardianai-artifact-observer-v2/source', source)
    archive = project / 'research/artifact-observer-runs/publication-refusal/GuardianAI-linux-x86_64.zip'
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(base / 'runtime')
    runtime = base / 'runtime'
    (runtime / 'native/notify-launch').chmod(0o755)
    command = ['python3', str(runtime / 'guardian_mcp.py'), '--task',
               'Build a source-hash index and ZIP for the runtime owner from the supplied public source. No protected input, external communication or source modification is authorized.',
               '--workspace', str(source), '--session', str(base / 'session'),
               '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace', '--command-timeout', '90']
    program = """import hashlib,json,zipfile
from pathlib import Path
root=Path('/workspace/source')
index={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in ('.py','.c')}
out=Path('/output')
(out/'source-hashes.json').write_text(json.dumps(index,indent=2))
(out/'README.md').write_text('Source-hash navigation bundle. These SHA-256 values describe the supplied public snapshot. They do not certify behavior or semantic safety.')
with zipfile.ZipFile(out/'source-hashes.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ('source-hashes.json','README.md'):z.write(out/name,name)
print('Prepared source-hash bundle',len(index))
"""
    requests = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'run', 'arguments': {'argv': ['python3', '-c', program]}}},
                {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'run', 'arguments': {'argv': ['sha256sum', '/workspace/source/guardian_mcp.py'], 'finish': True}}}]
    (base / 'command.json').write_text(json.dumps(command, indent=2)+'\n')
    (base / 'requests.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in requests))
    journal = base / 'session/evidence/_content'
    acknowledgement = base / 'session/evidence/external-stop-ack.json'
    destination = base / 'session/public/results/step-001'
    observations, requested, acknowledged = [], False, False
    with (base / 'responses.jsonl').open('w') as out, (base / 'stderr.txt').open('w') as err:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True)
        process.stdin.write(''.join(json.dumps(row)+'\n' for row in requests))
        process.stdin.close()
        deadline = time.monotonic() + 180
        while process.poll() is None and time.monotonic() < deadline:
            if not requested and journal.exists():
                for path in journal.glob('input-*.json'):
                    try: item = json.loads(path.read_text())
                    except (OSError, ValueError): continue
                    if item.get('kind') != 'tool_result_before_delivery': continue
                    request = {'request_id': str(uuid.uuid4()), 'reason': 'operator_cancel_during_final_content_review'}
                    temporary = acknowledgement.parent / 'operator-stop.tmp'
                    temporary.write_text(json.dumps(request))
                    temporary.replace(acknowledgement.parent / 'external-stop.json')
                    observations.append({'event': 'stop_requested', 'monotonic': time.monotonic(),
                                         'input': path.name, 'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                         'destination_exists': destination.exists()})
                    requested = True
                    break
            if requested and not acknowledged and acknowledgement.exists():
                try: receipt = json.loads(acknowledgement.read_text())
                except (OSError, ValueError): continue
                observations.append({'event': 'stop_acknowledged', 'monotonic': time.monotonic(),
                                     'receipt': receipt, 'destination_exists': destination.exists()})
                acknowledged = True
            time.sleep(.005)
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=30)
    (base / 'observations.json').write_text(json.dumps(observations, indent=2)+'\n')
    responses = [json.loads(row) for row in (base / 'responses.jsonl').read_text().splitlines()]
    results = [json.loads(row['result']['content'][0]['text']) for row in responses[1:]]
    summary = {'server_returncode': process.returncode, 'stop_requested': requested, 'stop_acknowledged': acknowledged,
               'destination_exists_at_ack': next((row['destination_exists'] for row in observations if row['event']=='stop_acknowledged'), None),
               'destination_exists_after': destination.exists(), 'first_result_verdict': results[0]['verdict'],
               'first_result_stdout_present': 'stdout' in results[0], 'next_command_reason': results[1].get('reason'),
               'scope': 'Trusted operator cancellation during a real source-hash/ZIP task. No new model subjects or malicious objective. Timing observation is local to this controller.'}
    (base / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    shutil.copytree(base, evidence / 'run')
    print(json.dumps(summary, indent=2))
    assert requested and acknowledged and summary['destination_exists_at_ack'] is False


if __name__ == '__main__': main()
