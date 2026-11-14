"""Launch one existing Grok CLI with only MCP tools and stop it on scope revocation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('grok', 'client', 'prompt', 'report', 'evidence'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--resume', help='Resume an existing Grok conversation under a new GuardianAI scope')
    args = parser.parse_args()
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=False)
    report = Path(args.report)
    if report.exists():
        raise ValueError('Use a new coding session report')
    command = [args.grok, '--cwd', args.client, '--model', 'grok-4.7', '--reasoning-effort', 'low',
               '--tools', 'search_tool,use_tool', '--no-subagents', '--disable-web-search',
               '--permission-mode', 'dontAsk', '--allow', 'MCPTool(guardianai__run)',
               '--max-turns', '12', '--output-format', 'streaming-messages-json',
               '--prompt-file', args.prompt]
    if args.resume:
        command += ['--resume', args.resume]
    (evidence / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    stopped = False
    started = time.monotonic()
    environment = dict(os.environ)
    environment.update(GROK_WORKFLOWS='0', GROK_MEMORY='0', GROK_DISABLE_EXPERIMENTS='1')
    for source in ('CLAUDE', 'CURSOR'):
        for kind in ('AGENTS', 'HOOKS', 'MCPS', 'RULES', 'SKILLS'):
            environment[f'GROK_{source}_{kind}_ENABLED'] = '0'
    forwarded = [item for item in environment.get('WSLENV', '').split(':')
                 if item and item.split('/')[0] != 'TYPESAFE_API_KEY']
    environment['WSLENV'] = ':'.join(forwarded + ['TYPESAFE_API_KEY/u'])
    with (evidence / 'stdout.jsonl').open('wb') as stdout, (evidence / 'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, env=environment)
        try:
            while process.poll() is None:
                try:
                    state = json.loads(report.read_text())
                except (OSError, ValueError):
                    state = None
                if state and state['scope_stopped'] and (not state['closed'] or any(
                        call['verdict'] != 'no_observed_violation' for call in state['calls'])):
                    stopped = True
                    process.terminate()
                    break
                if time.monotonic() - started > 600:
                    process.terminate()
                    raise TimeoutError('Coding-agent workflow deadline')
                time.sleep(.2)
            process.wait(timeout=10)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
    result = {'returncode': process.returncode, 'terminated_on_scope_stop': stopped,
              'elapsed_seconds': time.monotonic() - started,
              'scope': 'One external Grok CLI; only GuardianAI MCP tool executions are Linux-contained. Killing this local CLI cannot cancel already-running remote inference.'}
    (evidence / 'launcher.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 77 if stopped else process.returncode


if __name__ == '__main__':
    raise SystemExit(main())
