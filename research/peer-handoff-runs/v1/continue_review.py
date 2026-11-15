"""Continue only the unlaunched reviewer phase; preserve the failed controller run."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main():
    project = Path(__file__).resolve().parents[3]
    evidence = Path(__file__).resolve().parent
    native = '/home/pratz/guardianai-peer-handoff-v1'
    root = Path(r'\\wsl.localhost\kali-linux\home\pratz\guardianai-peer-handoff-v1')
    assert json.loads((evidence / 'peer-internal/receipt.json').read_text())['prepared']
    ledger = root / 'identity/reviewer.json'
    state = json.loads(ledger.read_text())
    assert not state['stopped'] and state.get('active_session') is None
    stage = root / 'review-recovery'; stage.mkdir()
    client = Path(r'C:\Users\sayal\.t3\userdata\guardianai-paired-reviewer-v1')
    config = client / '.grok/config.toml'; config.parent.mkdir(parents=True, exist_ok=True)
    old = config.read_bytes() if config.exists() else None
    trust = Path.home() / '.grok/trusted_folders.toml'; prior_trust = trust.read_bytes()
    stanza = ("\n[folders.'" + str(client) + "']\ntrusted = true\ndecided_at = " + str(int(time.time())) + '\n').encode()
    add_trust = str(client).encode() not in prior_trust
    task = (evidence / 'review-prompt.txt').read_text()
    conversation = state['provider_conversation']
    args = ['-d', 'kali-linux', '--', 'python3', native + '/bootstrap/guardianai-linux-x86_64/guardian_mcp.py',
            '--task', task, '--workspace', native + '/source', '--session', native + '/review-recovery/session',
            '--command-timeout', '90', '--sensor', '/home/pratz/guardianai-tools/unpacked/usr/bin/strace',
            '--flow-manifest', native + '/peer-internal/flow-manifest.json',
            '--identity-ledger', native + '/identity/reviewer.json', '--expected-conversation', conversation]
    configured = ('[plugins]\ndisabled = ["pentest-ai-agents-ca8c1ba6"]\n\n[mcp_servers.guardianai]\n'
                  'command = "C:\\\\Windows\\\\System32\\\\wsl.exe"\nargs = ' + json.dumps(args) + '\n'
                  'startup_timeout_sec = 30\ntool_timeout_sec = 180\n'
                  'env = { TYPESAFE_API_KEY = "${TYPESAFE_API_KEY}", WSLENV = "TYPESAFE_API_KEY/u" }\n').encode()
    (evidence / 'review-recovery-client.toml').write_bytes(configured)
    environment = dict(os.environ)
    environment['WSLENV'] = ':'.join([x for x in environment.get('WSLENV', '').split(':') if x and x.split('/')[0] != 'TYPESAFE_API_KEY']+['TYPESAFE_API_KEY/u'])
    config.write_bytes(configured)
    if add_trust: trust.write_bytes(prior_trust + stanza)
    try:
        result = subprocess.run([sys.executable, str(project / 'run_grok_guarded.py'),
            '--grok', r'C:\Users\sayal\.grok\bin\grok.exe', '--client', str(client),
            '--prompt', str(evidence / 'review-prompt.txt'), '--report', str(stage / 'session/evidence/coding-session.json'),
            '--evidence', str(evidence / 'review-recovery-client'), '--resume', conversation,
            '--require-binding', '--history-root', str(evidence)], env=environment, timeout=700)
    finally:
        if config.read_bytes() != configured: raise RuntimeError('Client config changed concurrently')
        if old is None: config.unlink()
        else: config.write_bytes(old)
        if add_trust:
            current = trust.read_bytes()
            if stanza not in current: raise RuntimeError('Temporary trust record changed concurrently')
            trust.write_bytes(current.replace(stanza, b'', 1))
        (evidence / 'review-recovery-cleanup.json').write_text(json.dumps({
            'config_restored': not config.exists() if old is None else config.read_bytes() == old,
            'trust_restored': trust.read_bytes() == prior_trust}, indent=2)+'\n')
        if (stage / 'session').exists(): shutil.copytree(stage / 'session', evidence / 'review-recovery/session')
        (evidence / 'reviewer-identity-after.json').write_bytes(ledger.read_bytes())
    (evidence / 'review-recovery-result.json').write_text(json.dumps({'returncode': result.returncode,
        'conversation': conversation, 'scope': 'Same reviewer conversation; only the unlaunched phase resumed.'}, indent=2)+'\n')
    return result.returncode


if __name__ == '__main__': raise SystemExit(main())
