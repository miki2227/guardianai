"""Deliver host-selected text snapshots only after content observation."""
import hashlib
import json
from pathlib import Path


def deliver(observer, sender, recipient, artifacts, destination):
    """Identities and artifact paths come from the trusted workflow, not agents.

    Snapshot before judging; publish those same bytes. This does not authorize
    arbitrary paths, execute transferred content or inspect binary artifacts.
    """
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Use a new handoff directory')
    snapshots = {}
    for path in map(Path, artifacts):
        if path.name == 'handoff-receipt.json' or path.name in snapshots or path.is_symlink() or not path.is_file():
            raise ValueError('Handoffs require distinct regular text files')
        with path.open('rb') as stream:
            raw = stream.read(32769)
        if len(raw) > 32768:
            raise ValueError('Handoff file exceeds 32 KiB')
        raw.decode('utf-8')
        snapshots[path.name] = raw
    if not snapshots or sum(map(len, snapshots.values())) > 65536:
        raise ValueError('Use between one and 64 KiB of text artifacts')
    content = {'sender': sender, 'recipient': recipient,
               'artifacts': [{'name': name, 'text': raw.decode('utf-8'),
                              'sha256': hashlib.sha256(raw).hexdigest()} for name, raw in snapshots.items()],
               'boundary': 'Authorized task handoff between the named collaborators. Only these snapshots are delivered; no external network or additional resource access is granted.'}
    sequence = observer.sequence
    if not observer.observe('agent_to_agent_handoff', content):
        return {'delivered': False, 'observer_sequence': sequence}
    destination.mkdir(parents=True)
    for name, raw in snapshots.items():
        (destination / name).write_bytes(raw)
    receipt = {'delivered': True, 'sender': sender, 'recipient': recipient,
               'observer_sequence': sequence,
               'files_sha256': {name: hashlib.sha256(raw).hexdigest() for name, raw in snapshots.items()}}
    (destination / 'handoff-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt
