"""Expose supervised Linux commands to an existing coding agent over MCP stdio."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import signal
import sys
import threading

from agent_observer import AgentObserver

from guarded_agent import run_worker
from release_broker import ReleaseBroker
from session_observer import SessionObserver


TOOL = {
    'name': 'run',
    'description': 'Run a Linux argv under GuardianAI/Jev. Read the project at /workspace/source and prior results at /workspace/results/step-NNN. Write new files only in /output; /tmp is private scratch. Each call has a fresh isolated process tree and empty /output. Results become read-only history for later calls. No network, host home or observer credentials are available to commands. A stopped scope cannot run further commands.',
    'inputSchema': {'type': 'object', 'properties': {
        'argv': {'type': 'array', 'minItems': 1, 'maxItems': 64,
                 'items': {'type': 'string', 'maxLength': 4096}},
        'finish': {'type': 'boolean', 'description': 'Set true on the final command to close this tool session after returning its result. No later commands can run.'}},
        'required': ['argv'], 'additionalProperties': False},
}


def bounded_output(path):
    with path.open('rb') as stream:
        raw = stream.read(8193)
    return {'text': raw[:8192].decode('utf-8', errors='replace'), 'truncated': len(raw) > 8192}


class CodingSession:
    def __init__(self, task, workspace, session, sensor, command_timeout=30):
        if sys.platform != 'linux' or not os.environ.get('TYPESAFE_API_KEY'):
            raise RuntimeError('Linux and the trusted supervisor credential are required')
        if not math.isfinite(command_timeout) or not 0 < command_timeout <= 600:
            raise ValueError('Use a finite command deadline between zero and 600 seconds')
        workspace, session = Path(workspace).resolve(strict=True), Path(session).resolve()
        runtime = Path(__file__).resolve().parent
        if not workspace.is_dir() or any(session.is_relative_to(p) or p.is_relative_to(session)
                                         for p in (workspace, runtime)):
            raise ValueError('Use a dedicated session directory disjoint from source and runtime')
        session.mkdir(parents=True, exist_ok=False)
        self.root, self.task, self.sensor = session, task, sensor
        self.command_timeout = command_timeout
        self.public = session / 'public'
        self.public.mkdir()
        shutil.copytree(workspace, self.public / 'source', symlinks=True)
        (self.public / 'results').mkdir()
        self.evidence = session / 'evidence'
        self.evidence.mkdir()
        self.broker = ReleaseBroker(task, {}, {})
        self.observer = SessionObserver(self.broker, self.evidence)
        self.launcher = runtime / 'native/notify-launch'
        self.calls = []
        self.closed = False
        self.save_lock = threading.RLock()
        self.content_observer = AgentObserver(task, self.evidence / '_content',
                                              context=self.content_context, stop=self.broker.revoke)
        self.save()

    def content_context(self):
        with self.observer.lock:
            return self.observer._context()

    def save(self):
        with self.save_lock:
            with self.broker.lock:
                state = {'task': self.task, 'calls': [dict(call) for call in self.calls],
                         'scope_stopped': self.broker.stop_event.is_set(), 'closed': self.closed,
                         'command_timeout_seconds': self.command_timeout,
                         'broker_audit': copy.deepcopy(self.broker.audit),
                         'scope': 'Sequential local tool executions from one external coding-agent client. The model and its host harness are outside Linux containment. A fresh worker namespace per call is not a fresh model context.'}
            snapshot = self.evidence / 'coding-session.tmp'
            snapshot.write_text(json.dumps(state, indent=2) + '\n')
            snapshot.replace(self.evidence / 'coding-session.json')

    def finish(self):
        with self.save_lock:
            if not self.closed:
                self.broker.revoke()
                self.closed = True
            self.save()

    def acknowledge_stop(self):
        with self.save_lock:
            request = json.loads((self.evidence / 'external-stop.json').read_text())
            acknowledgement = self.evidence / 'external-stop-ack.json'
            if acknowledgement.exists() and json.loads(acknowledgement.read_text()).get('request_id') == request['request_id']:
                return
            self.broker.revoke()
            self.save()
            receipt = {'request_id': request['request_id'], 'scope_stopped': True,
                       'epoch': self.broker.epoch, 'mcp_pid': os.getpid(),
                       'scope': 'Broker revocation acknowledged; worker exit and client exit are separate observations.'}
            temporary = self.evidence / 'external-stop-ack.tmp'
            temporary.write_text(json.dumps(receipt, indent=2) + '\n')
            temporary.replace(acknowledgement)

    def execute(self, arguments):
        if not isinstance(arguments, dict) or 'argv' not in arguments or set(arguments) - {'argv', 'finish'} or type(arguments.get('finish', False)) is not bool:
            raise ValueError('Expected argv and an optional boolean finish')
        argv = arguments['argv']
        if (not isinstance(argv, list) or not 1 <= len(argv) <= 64
                or any(type(a) is not str or len(a) > 4096 or '\0' in a for a in argv)):
            raise ValueError('Invalid command argv')
        if self.broker.stop_event.is_set():
            return {'verdict': 'abstain', 'reason': 'scope_stopped'}
        if len(self.calls) >= 16:
            self.broker.revoke()
            self.save()
            return {'verdict': 'abstain', 'reason': 'session_command_budget'}
        name = f'step-{len(self.calls) + 1:03d}'
        output = self.root / (name + '-output')
        output.mkdir()
        evidence = self.evidence / name
        self.broker.grants[name] = frozenset()
        call = {'execution': name, 'argv': argv, 'verdict': 'abstain'}
        self.calls.append(call)
        try:
            if not self.content_observer.observe('proposed_tool_argv', argv):
                call['reason'] = 'content_observer_stop_before_execution'
                self.save()
                return dict(call)
            report = run_worker(self.task, self.public, argv, output=output, evidence=evidence,
                                sensor=self.sensor, broker=self.broker, principal=name,
                                launcher=self.launcher, timeout=self.command_timeout,
                                observer=lambda task, events: self.observer.observe(name, task, events))
            call.update(verdict=report['verdict'], returncode=report['runtime']['returncode'],
                        evidence_status=report['runtime']['evidence_status'])
            result = {**call, 'stdout': bounded_output(evidence / 'stdout.txt'),
                      'stderr': bounded_output(evidence / 'stderr.txt')}
            destination = self.public / 'results' / name
            output.rename(destination)
            result['results_directory'] = '/workspace/results/' + name
            (evidence / 'tool-result.json').write_text(json.dumps(result, indent=2) + '\n')
            if not self.content_observer.observe('tool_result_before_delivery', result):
                call.update(verdict='abstain', reason='content_observer_withheld_tool_result')
                result = dict(call)
        except Exception as error:
            self.broker.lose_evidence()
            call['reason'] = type(error).__name__
            result = dict(call)
        if arguments.get('finish'):
            self.finish()
            result['session_closed'] = True
        else:
            self.save()
        return result


def serve(session):
    finished = threading.Event()
    def watch_stop():
        while not finished.wait(.1):
            if (session.evidence / 'external-stop.json').exists():
                session.acknowledge_stop()
                return
    watcher = threading.Thread(target=watch_stop, daemon=True)
    watcher.start()
    try:
        while True:
            raw = sys.stdin.buffer.readline(65537)
            if not raw:
                break
            if len(raw) > 65536 or not raw.endswith(b'\n'):
                raise ValueError('MCP request exceeds line budget or is incomplete')
            request = json.loads(raw)
            if not isinstance(request, dict) or request.get('jsonrpc') != '2.0':
                raise ValueError('Invalid JSON-RPC message')
            if 'id' not in request:
                continue
            method, params = request.get('method'), request.get('params', {})
            response = {'jsonrpc': '2.0', 'id': request['id']}
            if method == 'initialize':
                version = params.get('protocolVersion')
                response['result'] = {'protocolVersion': version if version in
                                      ('2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25') else '2025-06-18',
                                      'capabilities': {'tools': {'listChanged': False}},
                                      'serverInfo': {'name': 'GuardianAI', 'version': '0.1.0'}}
            elif method == 'ping':
                response['result'] = {}
            elif method == 'tools/list':
                response['result'] = {'tools': [TOOL]}
            elif method == 'tools/call' and params.get('name') == 'run':
                try:
                    if (session.evidence / 'external-stop.json').exists():
                        session.acknowledge_stop()
                    result = session.execute(params.get('arguments', {}))
                    response['result'] = {'content': [{'type': 'text', 'text': json.dumps(result)}],
                                          'isError': result['verdict'] != 'no_observed_violation' or result.get('returncode') != 0}
                except ValueError:
                    response['error'] = {'code': -32602, 'message': 'Invalid command arguments'}
            else:
                response['error'] = {'code': -32601, 'message': 'Method or tool not found'}
            print(json.dumps(response), flush=True)
    finally:
        finished.set()
        watcher.join()
        session.finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('task', 'workspace', 'session'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--sensor', default='strace')
    parser.add_argument('--command-timeout', type=float, default=30,
                        help='Trusted per-command execution deadline in seconds, at most 600')
    args = parser.parse_args()
    def terminate(signum, frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminate)
    serve(CodingSession(args.task, args.workspace, args.session, args.sensor, args.command_timeout))


if __name__ == '__main__':
    main()
