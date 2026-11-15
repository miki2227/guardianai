"""Prepare a labelled, digest-pinned peer resource in private host storage."""
import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path

from agent_observer import AgentObserver
from flow_policy import FlowPolicy
from guarded_handoff import snapshot_text_artifacts
from guardian_mcp import identity_lease
from release_broker import MAX_RESOURCE_BYTES


def prepare(plan, evidence):
    required = {'task', 'producer_ledger', 'producer_session', 'producer_conversation',
                'recipient_ledger', 'recipient_conversation', 'recipient_clearance',
                'workspace', 'session', 'artifacts'}
    if set(plan) != required:
        raise ValueError('Use the documented trusted peer-handoff plan')
    evidence = Path(evidence).resolve()
    source, target = [Path(plan[key]).resolve() for key in ('producer_ledger', 'recipient_ledger')]
    workspace, session = Path(plan['workspace']).resolve(), Path(plan['session']).resolve()
    if source == target or any(evidence.is_relative_to(root) or root.is_relative_to(evidence)
                               for root in (workspace, session, Path(__file__).resolve().parent)):
        raise ValueError('Use distinct identities and private handoff storage')
    clearance = plan['recipient_clearance']
    if not isinstance(clearance, list) or any(type(label) is not str or not label for label in clearance):
        raise ValueError('Recipient clearance must be explicit label strings')
    evidence.mkdir(parents=True, exist_ok=False)
    with ExitStack() as locks:
        for path in sorted((source, target)):
            locks.enter_context(identity_lease(path, workspace, session))
        source_bytes = source.read_bytes()
        state = json.loads(source_bytes)
        if state['stopped'] or state.get('active_session') is not None:
            raise PermissionError('Producer identity is stopped or not cleanly closed')
        if state.get('provider_conversation') != plan['producer_conversation']:
            raise PermissionError('Producer conversation does not match its ledger')
        producer_session = Path(plan['producer_session']).resolve()
        producer = json.loads((producer_session / 'evidence/coding-session.json').read_text())
        if (not producer['closed'] or not producer['scope_stopped']
                or Path(producer['identity_ledger']).resolve() != source
                or producer['client_binding'].get('status') != 'verified'
                or producer['client_binding'].get('expected_conversation') != plan['producer_conversation']):
            raise PermissionError('Use a verified completed producer session')
        labels = sorted(set(state['labels']['coding-worker']) | set(state['labels']['coding-client']))
        receipt = {'producer': plan['producer_conversation'], 'recipient': plan['recipient_conversation'],
                   'source_labels': labels, 'recipient_clearance': clearance,
                   'producer_ledger_sha256': hashlib.sha256(source_bytes).hexdigest(),
                   'prepared': False, 'scope': 'Private resource preparation is not receiver exposure or model consumption.'}
        if not set(labels) <= set(clearance):
            receipt['reason'] = 'recipient_clearance'
        else:
            paths = list(map(Path, plan['artifacts']))
            published = producer_session / 'public/results'
            if any(not path.resolve().is_relative_to(published) for path in paths):
                raise ValueError('Peer artifacts must come from the producer publication tree')
            snapshots = snapshot_text_artifacts(paths)
            payload = {'provenance': {key: value for key, value in receipt.items() if key != 'prepared'}, 'artifacts': [
                {'name': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'text': raw.decode('utf-8')}
                for name, raw in snapshots.items()]}
            raw = json.dumps(payload).encode()
            if len(raw) > MAX_RESOURCE_BYTES:
                raise ValueError('Combined peer resource exceeds the broker snapshot bound')
            source_flow = FlowPolicy(source, state['policy']['clearances'], state['policy']['resources'], on_stop=lambda: None)
            target_flow = FlowPolicy(target,
                {'coding-worker': clearance, 'coding-client': clearance}, {'peer_handoff': labels}, on_stop=lambda: None)
            if target_flow.state['stopped'] or target_flow.state.get('active_session') is not None:
                raise PermissionError('Recipient identity is stopped or not cleanly closed')
            target_flow.bind_conversation(plan['recipient_conversation'])
            def stop():
                try: source_flow.stop()
                finally: target_flow.stop()
            observer = AgentObserver(plan['task'], evidence / 'observer', context=lambda: receipt.copy(), stop=stop)
            if observer.observe('peer_resource_before_publication', payload):
                resource = evidence / 'peer-resource.json'
                resource.write_bytes(raw)
                digest = hashlib.sha256(raw).hexdigest()
                manifest = {'resources': {'peer_handoff': {'path': str(resource), 'labels': labels, 'sha256': digest}},
                            'worker_clearance': clearance, 'client_clearance': clearance}
                (evidence / 'flow-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
                receipt.update(prepared=True, resource_sha256=digest,
                               files_sha256={name: hashlib.sha256(data).hexdigest() for name, data in snapshots.items()})
            else:
                receipt['reason'] = 'content_observer_stop'
        (evidence / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--evidence', required=True)
    args = parser.parse_args()
    result = prepare(json.loads(Path(args.plan).read_text()), args.evidence)
    print(json.dumps(result))
    return 0 if result['prepared'] else 77


if __name__ == '__main__':
    raise SystemExit(main())
