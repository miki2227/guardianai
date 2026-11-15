"""Expose supervised Linux commands to an existing coding agent over MCP stdio."""
import argparse
import copy
from contextlib import contextmanager
import json
import hashlib
import math
import os
from pathlib import Path
import shutil
import signal
import sys
import threading
import time
import uuid

from agent_observer import AgentObserver

from flow_policy import FlowPolicy
from guarded_agent import load_resources, run_worker
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


@contextmanager
def identity_lease(path, workspace, session):
    if path is None:
        yield None
        return
    import fcntl
    if not Path(path).is_absolute():
        raise ValueError('Identity ledger must be an absolute host path')
    ledger = Path(path).resolve()
    roots = [Path(workspace).resolve(), Path(session).resolve(), Path(__file__).resolve().parent,
             *[Path(p).resolve() for p in ('/usr', '/bin', '/lib', '/lib64') if Path(p).exists()]]
    if any(ledger.is_relative_to(root) for root in roots):
        raise ValueError('Identity ledger must stay outside worker/session/runtime mounts')
    # Lock a stable sidecar: the ledger itself is atomically replaced on save.
    descriptor = os.open(str(ledger) + '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'a+b') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield ledger


class CodingSession:
    def __init__(self, task, workspace, session, sensor, command_timeout=30, *, flow_manifest=None, identity_ledger=None, expected_conversation=None):
        if sys.platform != 'linux' or not os.environ.get('TYPESAFE_API_KEY'):
            raise RuntimeError('Linux and the trusted supervisor credential are required')
        if not math.isfinite(command_timeout) or not 0 < command_timeout <= 600:
            raise ValueError('Use a finite command deadline between zero and 600 seconds')
        if identity_ledger is not None and flow_manifest is None:
            raise ValueError('Persistent identity requires a trusted flow manifest')
        if expected_conversation is not None and (identity_ledger is None or not expected_conversation
                                                  or len(expected_conversation) > 128 or '\0' in expected_conversation):
            raise ValueError('Conversation binding requires an identity ledger and bounded ID')
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
        self.launcher = runtime / 'native/notify-launch'
        resources, config = {}, None
        if flow_manifest is not None:
            config = json.loads(Path(flow_manifest).read_text())
            if set(config) != {'resources', 'worker_clearance', 'client_clearance'}:
                raise ValueError('Flow manifest requires resources and worker/client clearances')
            if not isinstance(config['resources'], dict) or any(
                    not isinstance(item, dict) or set(item) not in ({'path', 'labels'}, {'path', 'labels', 'sha256'})
                    or not isinstance(item['path'], str) or not Path(item['path']).is_absolute()
                    for item in config['resources'].values()):
                raise ValueError('Resources require absolute host paths and label arrays')
            collections = [config['worker_clearance'], config['client_clearance'],
                           *[item['labels'] for item in config['resources'].values()]]
            if any(not isinstance(labels, list) or any(type(label) is not str or not label for label in labels)
                   for labels in collections):
                raise ValueError('Clearances and labels must be arrays of nonempty strings')
            roots = [workspace, session, runtime, *[Path(p).resolve() for p in
                     ('/usr', '/bin', '/lib', '/lib64') if Path(p).exists()]]
            resources = load_resources({name: item['path'] for name, item in config['resources'].items()},
                                       roots, self.launcher)
            for name, item in config['resources'].items():
                if 'sha256' in item and hashlib.sha256(resources[name]).hexdigest() != item['sha256']:
                    raise ValueError('Protected resource differs from its pinned SHA-256')
        self.broker = ReleaseBroker(task, resources, {})
        self.identity_ledger = identity_ledger
        if identity_ledger is not None and any(identity_ledger == Path(item['path']).resolve()
                                               for item in config['resources'].values()):
            raise ValueError('Identity ledger cannot also be a protected input')
        self.flow = None if config is None else FlowPolicy(
            self.evidence / 'flow-policy.json' if identity_ledger is None else identity_ledger,
            {'coding-worker': config['worker_clearance'], 'coding-client': config['client_clearance']},
            {name: item['labels'] for name, item in config['resources'].items()}, on_stop=self.broker.revoke)
        self.identity_at_start = None if self.flow is None else {
            'labels': copy.deepcopy(self.flow.state['labels']), 'stopped': self.flow.state['stopped'],
            'active_session': self.flow.state.get('active_session'),
            'exposure_count': len(self.flow.state['exposures']), 'transfer_count': len(self.flow.state['transfers'])}
        expected_conversation = expected_conversation or (self.flow.state.get('provider_conversation') if self.flow else None)
        if expected_conversation is not None:
            self.flow.bind_conversation(expected_conversation)
        self.client_binding = ({'expected_conversation': expected_conversation, 'request_id': str(uuid.uuid4()),
                                'status': 'pending'} if expected_conversation else {'status': 'unbound'})
        if identity_ledger is not None:
            self.flow.begin_session(str(session))
        self.stop = self.broker.revoke if self.flow is None else self.flow.stop
        if self.flow is not None:
            self.broker.exposure = lambda principal, resource, digest: self.flow.expose('coding-worker', resource, digest)
        self.observer = SessionObserver(self.broker, self.evidence,
                                       flow_context=None if self.flow is None else lambda principal: self.flow.exposure_context('coding-worker'))
        self.broker.observer = self.observer.authorize
        self.calls = []
        self.closed = False
        self.save_lock = threading.RLock()
        self.content_observer = AgentObserver(task, self.evidence / '_content',
                                              context=self.content_context, stop=self.stop)
        self.save()

    def content_context(self):
        with self.observer.lock:
            context = self.observer._context()
        if self.flow is not None:
            context['information_flow'] = self.flow.context('coding-worker', 'coding-client')
        return context

    def save(self):
        with self.save_lock:
            with self.broker.lock:
                state = {'task': self.task, 'calls': [dict(call) for call in self.calls],
                         'scope_stopped': self.broker.stop_event.is_set(), 'closed': self.closed,
                         'command_timeout_seconds': self.command_timeout,
                         'broker_audit': copy.deepcopy(self.broker.audit),
                         'identity_ledger': None if self.identity_ledger is None else str(self.identity_ledger),
                         'identity_at_start': self.identity_at_start,
                         'client_binding': dict(self.client_binding),
                         'information_flow': {'mode': 'untracked'} if self.flow is None else self.flow.context('coding-worker', 'coding-client'),
                         'scope': 'Sequential local tool executions from one external coding-agent client. The model and its host harness are outside Linux containment. A fresh worker namespace per call is not a fresh model context.'}
            snapshot = self.evidence / 'coding-session.tmp'
            snapshot.write_text(json.dumps(state, indent=2) + '\n')
            snapshot.replace(self.evidence / 'coding-session.json')

    def verify_client_binding(self):
        if self.client_binding['status'] in ('unbound', 'verified'):
            return True
        deadline = time.monotonic() + 2
        permit = None
        while time.monotonic() < deadline and not self.broker.stop_event.is_set():
            try:
                permit = json.loads((self.evidence / 'client-binding.json').read_text())
                break
            except FileNotFoundError:
                time.sleep(.02)
            except (ValueError, OSError):
                break
        with self.save_lock:
            verified = (isinstance(permit, dict)
                        and not self.broker.stop_event.is_set()
                        and permit.get('request_id') == self.client_binding['request_id']
                        and permit.get('session_id') == self.client_binding['expected_conversation']
                        and permit.get('source') == 'grok_cli_system_init')
            self.client_binding.update(status='verified' if verified else 'refused',
                                       checked_monotonic=time.monotonic())
            if not verified:
                self.stop()
            self.save()
        return verified

    def finish(self):
        with self.save_lock:
            if not self.closed:
                if self.identity_ledger is None:
                    self.stop()
                else:
                    if not self.broker.stop_event.is_set():
                        self.flow.end_session(str(self.root))
                    self.broker.revoke()
                self.closed = True
            self.save()

    def acknowledge_stop(self):
        with self.save_lock:
            request = json.loads((self.evidence / 'external-stop.json').read_text())
            acknowledgement = self.evidence / 'external-stop-ack.json'
            if acknowledgement.exists() and json.loads(acknowledgement.read_text()).get('request_id') == request['request_id']:
                return
            self.stop()
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
        if not self.verify_client_binding():
            return {'verdict': 'abstain', 'reason': 'client_binding_unverified'}
        if len(self.calls) >= 16:
            self.stop()
            self.save()
            return {'verdict': 'abstain', 'reason': 'session_command_budget'}
        name = f'step-{len(self.calls) + 1:03d}'
        output = self.root / (name + '-output')
        output.mkdir()
        evidence = self.evidence / name
        self.broker.grants[name] = frozenset(self.broker.resources)
        call = {'execution': name, 'argv': argv, 'verdict': 'abstain', 'accepted_monotonic': time.monotonic()}
        call['client_binding'] = {key: self.client_binding[key] for key in ('status', 'expected_conversation') if key in self.client_binding}
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
            result['results_directory'] = '/workspace/results/' + name
            def publish(decision):
                output.rename(destination)
                result['information_flow'] = decision
            if report['verdict'] != 'no_observed_violation':
                self.stop()
                call['reason'] = 'runtime_withheld_tool_result'
                result = dict(call)
            elif self.flow is not None and not self.flow.context('coding-worker', 'coding-client')['permitted']:
                decision = self.flow.transfer('coding-worker', 'coding-client', publish)
                call.update(verdict='abstain', reason='information_flow_withheld_tool_result', information_flow=decision)
                result = dict(call)
            elif not self.content_observer.observe('tool_result_before_delivery', result):
                call.update(verdict='abstain', reason='content_observer_withheld_tool_result')
                result = dict(call)
            elif self.flow is None:
                publish({'mode': 'untracked'})
            else:
                decision = self.flow.transfer('coding-worker', 'coding-client', publish)
                if decision['delivered']:
                    result['information_flow'] = decision
                    call['information_flow'] = decision
                else:
                    call.update(verdict='abstain', reason='information_flow_withheld_tool_result', information_flow=decision)
                    result = dict(call)
            (evidence / 'tool-result.json').write_text(json.dumps(result, indent=2) + '\n')
        except Exception as error:
            self.broker.lose_evidence()
            self.stop()
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
        if session.identity_ledger is not None and not session.closed:
            session.stop()  # Only an explicit successful finish can resume an identity.
        session.finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('task', 'workspace', 'session'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--sensor', default='strace')
    parser.add_argument('--flow-manifest', help='Trusted protected-resource paths, labels and worker/client clearances; see FLOW.md')
    parser.add_argument('--identity-ledger', help='Host-owned absolute ledger retained across sessions; requires --flow-manifest and explicit finish')
    parser.add_argument('--expected-conversation', help='Require launcher approval of this CLI session ID before executing commands')
    parser.add_argument('--command-timeout', type=float, default=30,
                        help='Trusted per-command execution deadline in seconds, at most 600')
    args = parser.parse_args()
    def terminate(signum, frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminate)
    if args.identity_ledger is not None and args.flow_manifest is None:
        parser.error('--identity-ledger requires --flow-manifest')
    with identity_lease(args.identity_ledger, args.workspace, args.session) as ledger:
        serve(CodingSession(args.task, args.workspace, args.session, args.sensor, args.command_timeout,
                            flow_manifest=args.flow_manifest, identity_ledger=ledger,
                            expected_conversation=args.expected_conversation))


if __name__ == '__main__':
    main()
