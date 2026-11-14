"""Expose supervised Linux commands to an existing coding agent over MCP stdio."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import sys

from guarded_agent import run_worker
from release_broker import ReleaseBroker
from session_observer import SessionObserver


TOOL = {
    'name': 'run',
    'description': 'Run a Linux argv under GuardianAI/Jev. Read the project at /workspace/source and prior results at /workspace/results/step-NNN. Write new files only in /output; /tmp is private scratch. Each call has a fresh isolated process tree and empty /output. Results become read-only history for later calls. No network, host home or observer credentials are available to commands. A stopped scope cannot run further commands.',
    'inputSchema': {'type': 'object', 'properties': {
        'argv': {'type': 'array', 'minItems': 1, 'maxItems': 64,
                 'items': {'type': 'string', 'maxLength': 4096}}},
        'required': ['argv'], 'additionalProperties': False},
}


def bounded_output(path):
    with path.open('rb') as stream:
        raw = stream.read(8193)
    return {'text': raw[:8192].decode('utf-8', errors='replace'), 'truncated': len(raw) > 8192}


class CodingSession:
    def __init__(self, task, workspace, session, sensor):
        if sys.platform != 'linux' or not os.environ.get('TYPESAFE_API_KEY'):
            raise RuntimeError('Linux and the trusted supervisor credential are required')
        workspace, session = Path(workspace).resolve(strict=True), Path(session).resolve()
        runtime = Path(__file__).resolve().parent
        if not workspace.is_dir() or any(session.is_relative_to(p) or p.is_relative_to(session)
                                         for p in (workspace, runtime)):
            raise ValueError('Use a dedicated session directory disjoint from source and runtime')
        session.mkdir(parents=True, exist_ok=False)
        self.root, self.task, self.sensor = session, task, sensor
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
        self.save()

    def save(self):
        snapshot = self.evidence / 'coding-session.tmp'
        snapshot.write_text(json.dumps({
            'task': self.task, 'calls': self.calls, 'scope_stopped': self.broker.stop_event.is_set(),
            'closed': self.closed,
            'broker_audit': self.broker.audit,
            'scope': 'Sequential local tool executions from one external coding-agent client. The model and its host harness are outside Linux containment. A fresh worker namespace per call is not a fresh model context.'}, indent=2) + '\n')
        snapshot.replace(self.evidence / 'coding-session.json')

    def execute(self, arguments):
        if not isinstance(arguments, dict) or set(arguments) != {'argv'}:
            raise ValueError('Expected argv only')
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
            report = run_worker(self.task, self.public, argv, output=output, evidence=evidence,
                                sensor=self.sensor, broker=self.broker, principal=name,
                                launcher=self.launcher,
                                observer=lambda task, events: self.observer.observe(name, task, events))
            call.update(verdict=report['verdict'], returncode=report['runtime']['returncode'],
                        evidence_status=report['runtime']['evidence_status'])
            result = {**call, 'stdout': bounded_output(evidence / 'stdout.txt'),
                      'stderr': bounded_output(evidence / 'stderr.txt')}
            destination = self.public / 'results' / name
            output.rename(destination)
            result['results_directory'] = '/workspace/results/' + name
            (evidence / 'tool-result.json').write_text(json.dumps(result, indent=2) + '\n')
        except Exception as error:
            self.broker.lose_evidence()
            call['reason'] = type(error).__name__
            result = dict(call)
        self.save()
        return result


def serve(session):
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
                    result = session.execute(params.get('arguments', {}))
                    response['result'] = {'content': [{'type': 'text', 'text': json.dumps(result)}],
                                          'isError': result['verdict'] != 'no_observed_violation' or result.get('returncode') != 0}
                except ValueError:
                    response['error'] = {'code': -32602, 'message': 'Invalid command arguments'}
            else:
                response['error'] = {'code': -32601, 'message': 'Method or tool not found'}
            print(json.dumps(response), flush=True)
    finally:
        session.broker.revoke()
        session.closed = True
        session.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('task', 'workspace', 'session'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--sensor', default='strace')
    args = parser.parse_args()
    def terminate(signum, frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminate)
    serve(CodingSession(args.task, args.workspace, args.session, args.sensor))


if __name__ == '__main__':
    main()
