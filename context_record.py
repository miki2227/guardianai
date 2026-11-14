"""Record observed subject I/O without treating a logical thread as retained context."""
import argparse
import hashlib
import json
from pathlib import Path


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def make_record(metadata_bytes, prompt_bytes, reply_bytes):
    metadata = json.loads(metadata_bytes)
    run = metadata['run']
    sent = metadata['send']
    if run['status'] != 'completed' or sent['runId'] != run['runId']:
        raise ValueError('A completed matching run is required')
    activity = [item for item in metadata['activity'] if item.get('runId') == run['runId']]
    requests = [item for item in activity if item['type'] == 'user_message']
    responses = [item for item in activity if item['type'] == 'assistant_message']
    if len(requests) != 1 or len(responses) != 1:
        raise ValueError('Expected one observed request and response for this run')
    request, response = requests[0], responses[0]
    if any(item.get('textTruncated') or item.get('sourceThreadId') != sent['threadId']
           for item in (request, response)):
        raise ValueError('Incomplete or mismatched subject exposure')
    # Stored pretty-printing may differ; retain the actual dispatched string.
    if json.loads(request['text']) != json.loads(prompt_bytes):
        raise ValueError('Stored prompt does not match the observed request')
    if response['text'].strip() != reply_bytes.decode('utf-8').strip():
        raise ValueError('Stored reply does not match the observed response')
    controls = metadata.get('controls', {})
    fresh = controls.get('freshContext')
    if fresh is not None and type(fresh) is not bool:
        raise ValueError('Invalid context reset declaration')
    usage = run.get('usage')
    capacity = run.get('context_capacity_tokens')
    # Keep provider-reported data as data. Its counting scope may be unknown.
    return {'run_id': run['runId'], 'subject_thread_id': sent['threadId'],
            'provider': run['providerInstanceId'], 'requested_model': run['model'],
            'executed_model': run.get('executedModel'),
            'request_message_id': request.get('messageId'), 'response_message_id': response.get('messageId'),
            'fresh_context_declared': fresh,
            'context_condition': 'declared_reset' if fresh is True else 'retention_unverified',
            'recorded_request_utf8_bytes': len(request['text'].encode('utf-8')),
            'recorded_request_sha256': sha256(request['text'].encode('utf-8')),
            'request_text': request['text'], 'response_text': response['text'],
            'provider_reported_usage': usage, 'provider_reported_context_capacity_tokens': capacity,
            'context_pressure': 'unmeasured',
            'context_limit_exceeded': None,
            'scope': 'Observed request/reply only; provider system context, retained history and token-counting scope are not established. Logical thread continuity is not evidence of context retention.',
            'artifacts_sha256': {'metadata.json': sha256(metadata_bytes), 'prompt.json': sha256(prompt_bytes),
                                 'reply.txt': sha256(reply_bytes)}}


def record_turn(destination, metadata, prompt, reply):
    raw = {name: Path(path).read_bytes() for name, path in
           (('metadata.json', metadata), ('prompt.json', prompt), ('reply.txt', reply))}
    record = make_record(raw['metadata.json'], raw['prompt.json'], raw['reply.txt'])
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in raw.items():
        (destination / name).write_bytes(value)
    (destination / 'record.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def verify_record(folder):
    folder = Path(folder)
    expected = make_record(*( (folder / name).read_bytes() for name in ('metadata.json', 'prompt.json', 'reply.txt')))
    if json.loads((folder / 'record.json').read_text()) != expected:
        raise ValueError('Record differs from its source artifacts')
    return expected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('metadata', 'prompt', 'reply', 'destination'):
        parser.add_argument('--' + field, type=Path, required=True)
    args = parser.parse_args()
    result = record_turn(args.destination, args.metadata, args.prompt, args.reply)
    print(json.dumps({'run_id': result['run_id'], 'context_condition': result['context_condition'],
                      'context_pressure': result['context_pressure']}))
