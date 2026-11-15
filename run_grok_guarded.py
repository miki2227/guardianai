"""Launch one existing Grok CLI with only MCP tools and stop it on scope revocation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from agent_observer import AgentObserver


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
    def stop_scope():
        if report.parent.is_dir():
            marker = report.parent / 'external-stop.json'
            marker.write_text(json.dumps({'reason': 'host_content_observer_stop'}) + '\n')

    def execution_context():
        if not report.exists():
            return {'status': 'tool_session_not_yet_available'}
        state = json.loads(report.read_text())
        return {'scope_stopped': state['scope_stopped'], 'closed': state['closed'],
                'recent_calls': [{key: call[key] for key in ('execution', 'verdict', 'returncode', 'reason') if key in call}
                                 for call in state['calls'][-4:]],
                'earlier_calls_omitted': max(0, len(state['calls']) - 4)}

    observer = AgentObserver(Path(args.prompt).read_text(), evidence / 'agent-content',
                             context=execution_context, stop=stop_scope)
    if not observer.observe('host_supplied_prompt', Path(args.prompt).read_text()):
        (evidence / 'launcher.json').write_text(json.dumps({'launched': False, 'reason': 'prompt_observer_stop'}) + '\n')
        return 77
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
    with (evidence / 'stdout.jsonl').open('wb') as stdout, (evidence / 'stderr.txt').open('wb') as stderr, \
            (evidence / 'stdout.jsonl').open('rb') as captured:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, env=environment)
        pending = b''
        terminal_result = None
        try:
            while True:
                exited = process.poll() is not None
                incoming = captured.read(1024 * 1024)
                pending += incoming
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    try:
                        item = json.loads(line)
                        if item.get('type') == 'result':
                            terminal_result = item
                        blocks = item.get('message', {}).get('content', [])
                        if item.get('type') == 'assistant':
                            exposed = [{key: block[key] for key in ('type', 'text', 'thinking', 'name', 'input') if key in block}
                                       for block in blocks if block.get('type') in ('text', 'thinking', 'tool_use')]
                            if exposed and not observer.observe('emitted_assistant_message', exposed):
                                stopped = True
                                break
                    except (ValueError, TypeError, AttributeError):
                        stop_scope()
                        stopped = True
                        break
                if len(pending) > 1024 * 1024 or (exited and not incoming and pending.strip()):
                    stop_scope()
                    stopped = True
                if stopped:
                    if process.poll() is None:
                        process.terminate()
                    break
                if exited and not incoming:
                    break
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
                    stop_scope()
                    process.terminate()
                    raise TimeoutError('Coding-agent workflow deadline')
                time.sleep(.2)
            process.wait(timeout=10)
        finally:
            if process.poll() is None:
                stop_scope()
                process.kill()
                process.wait()
    result = {'returncode': process.returncode, 'terminated_on_scope_stop': stopped,
              'client_result_subtype': terminal_result.get('subtype') if terminal_result else None,
              'client_result_error': terminal_result.get('is_error') if terminal_result else None,
              'elapsed_seconds': time.monotonic() - started,
              'scope': 'One external Grok CLI. Exposed assistant text/thinking/tool requests are observed after CLI emission, not before model generation or necessarily before tool dispatch. MCP gates tool argv and result delivery separately. Only MCP commands are Linux-contained; hidden provider reasoning is unavailable. Killing the CLI cannot cancel remote inference.'}
    (evidence / 'launcher.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 77 if stopped else process.returncode or int(not terminal_result or bool(terminal_result.get('is_error')))


if __name__ == '__main__':
    raise SystemExit(main())
