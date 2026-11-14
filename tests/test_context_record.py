import json
from pathlib import Path
import tempfile
import unittest

from context_record import make_record, record_turn, verify_record


class ContextRecordTests(unittest.TestCase):
    def fixture(self):
        return {'send': {'runId': 'run-1', 'threadId': 'subject-1'},
                'run': {'runId': 'run-1', 'status': 'completed', 'providerInstanceId': 'fixture', 'model': 'fixture'},
                'activity': [{'runId': 'run-1', 'sourceThreadId': 'subject-1', 'type': kind, 'text': value,
                              'textTruncated': False} for kind, value in
                             (('user_message', '{"task":"normal work"}'), ('assistant_message', '{"result":"ok"}'))]}

    def record(self, metadata):
        return make_record(json.dumps(metadata).encode(), b'{"task":"normal work"}', b'{"result":"ok"}')

    def test_same_thread_or_large_prompt_does_not_establish_context_pressure(self):
        metadata = self.fixture()
        metadata['run']['ordinal'] = 10000
        record = self.record(metadata)
        self.assertEqual(record['context_condition'], 'retention_unverified')
        self.assertEqual(record['context_pressure'], 'unmeasured')
        self.assertIsNone(record['context_limit_exceeded'])
        self.assertIsNone(record['provider_reported_usage'])
        prompt = json.dumps({'task': 'normal work ' + 'x' * 8192}).encode()
        metadata['activity'][0]['text'] = prompt.decode()
        large = make_record(json.dumps(metadata).encode(), prompt, b'{"result":"ok"}')
        self.assertGreater(large['recorded_request_utf8_bytes'], 8192)
        self.assertIsNone(large['context_limit_exceeded'])

    def test_explicit_resets_and_unverified_retention_are_distinguished(self):
        metadata = self.fixture()
        metadata['controls'] = {'freshContext': True}
        self.assertEqual(self.record(metadata)['context_condition'], 'declared_reset')
        metadata['controls']['freshContext'] = False
        self.assertEqual(self.record(metadata)['context_condition'], 'retention_unverified')

    def test_reported_usage_is_retained_without_inventing_counting_scope(self):
        metadata = self.fixture()
        metadata['run'].update(usage={'input_tokens': 990}, context_capacity_tokens=1000)
        record = self.record(metadata)
        self.assertEqual(record['provider_reported_usage']['input_tokens'], 990)
        self.assertEqual(record['context_pressure'], 'unmeasured')

    def test_wrong_run_subject_prompt_reply_and_truncation_are_rejected(self):
        changes = [lambda m: m['send'].update(runId='other'),
                   lambda m: m['activity'][0].update(sourceThreadId='other'),
                   lambda m: m['activity'][0].update(text='{"task":"different"}'),
                   lambda m: m['activity'][1].update(text='wrong reply'),
                   lambda m: m['activity'][0].update(textTruncated=True)]
        for change in changes:
            metadata = self.fixture()
            change(metadata)
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                self.record(metadata)

    def test_frozen_artifacts_detect_source_and_record_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {'metadata.json': json.dumps(self.fixture()).encode(),
                     'prompt.json': b'{"task":"normal work"}', 'reply.txt': b'{"result":"ok"}'}
            for name, content in files.items():
                (root / name).write_bytes(content)
            target = root / 'recorded'
            record_turn(target, root / 'metadata.json', root / 'prompt.json', root / 'reply.txt')
            verify_record(target)
            with self.assertRaises(FileExistsError):
                record_turn(target, root / 'metadata.json', root / 'prompt.json', root / 'reply.txt')
            for name in ('prompt.json', 'record.json'):
                path = target / name
                raw = path.read_bytes()
                path.write_text('{}')
                with self.assertRaises(ValueError):
                    verify_record(target)
                path.write_bytes(raw)
