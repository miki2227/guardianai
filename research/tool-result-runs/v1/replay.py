"""Replay retained real CLI messages through the production host observer adapter.

No agent CLI, MCP process, worker or conversation recovery is started.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT))
from agent_observer import AgentObserver
from run_grok_guarded import observe_message


def main():
    saved = Path(__file__).resolve().parent
    run = saved / 'run'
    run.mkdir(exist_ok=False)
    source = PROJECT / 'research/continued-agent-runs/v1/correction-client'
    stream = source / 'stdout.jsonl'
    prompt = source / 'agent-content/content-0.json'
    ledger = Path(r'\\wsl.localhost\kali-linux\home\pratz\guardianai-continued-agent-v1\identity\flow.json')
    before = hashlib.sha256(ledger.read_bytes()).hexdigest()
    assert json.loads(ledger.read_text())['stopped'] is True
    for name in ('run_grok_guarded.py', 'agent_observer.py', 'guardian.py', 'decision_review.py', 'evidence_memory.py'):
        shutil.copyfile(PROJECT / name, run / name)
    manifest = {str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (stream, prompt)}
    (run / 'sources.json').write_text(json.dumps(manifest, indent=2) + '\n')
    stops = []
    def stop():
        stops.append({'reason': 'replay_observer_stop', 'workers_started': 0})
        return stops[-1]
    observer = AgentObserver(json.loads(prompt.read_text())['content'], run / 'agent-content',
                             context=lambda: {'mode': 'retained_cli_replay', 'workers_started': 0,
                                              'scope': 'Historical messages, not live execution or new model-agent behavior.'},
                             stop=stop)
    events = []
    allowed = observer.observe('host_supplied_prompt', json.loads(prompt.read_text())['content'])
    for line_number, line in enumerate(stream.read_text().splitlines(), 1):
        if not allowed:
            break
        item = json.loads(line)
        sequence = observer.sequence
        allowed = observe_message(observer, item)
        if observer.sequence != sequence:
            event = {'source_line': line_number, 'event_type': item['type'], 'sequence': sequence,
                     'continue': allowed}
            events.append(event)
            print(json.dumps(event), flush=True)
    after = hashlib.sha256(ledger.read_bytes()).hexdigest()
    assert before == after
    result = {'source_files_sha256': manifest, 'events': events, 'completed': allowed,
              'stops': stops, 'canonical_ledger_before': before, 'canonical_ledger_after': after,
              'agent_invocations': 0, 'worker_commands': 0,
              'scope': 'Live Jev decisions on retained real CLI messages. Not a new agent workflow, prospective delivery gate or detector accuracy benchmark.'}
    (run / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return 0 if allowed else 77


if __name__ == '__main__':
    raise SystemExit(main())
