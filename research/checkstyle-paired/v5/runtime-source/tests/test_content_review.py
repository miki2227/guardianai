import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from decision_review import review_content
from run_grok_guarded import observe_message


class ContentReviewTests(unittest.TestCase):
    def test_late_part_violation_is_not_skipped(self):
        states = []
        def query(state, questions):
            states.append(state)
            return {'model': 'fixture', 'answers': {'violation': {'noul': .9 if 'LATE-MARKER' in state['current_content'] else .1}}}
        text = 'ordinary text ' * 3000 + 'LATE-MARKER'
        with tempfile.TemporaryDirectory() as folder, patch('decision_review.query_jev', query):
            result = review_content({'trusted_task': 'inspect all content', 'current_content': text}, Path(folder), 'review')
        self.assertEqual(result['mode'], 'overlapping_parts')
        self.assertEqual(result['probability'], .9)
        self.assertEqual(states[-1]['review_partition']['end_character'], len(text))
        self.assertTrue(all(len(json.dumps(s).encode()) <= 20 * 1024 for s in states))
        # Union of reviewed spans contains every character, including the final marker.
        covered = set()
        for s in states:
            covered.update(range(s['chunk_offset_characters'], s['review_partition']['end_character']))
        self.assertEqual(len(covered), len(text))

    def test_duplicate_wrapper_keys_are_not_silently_discarded(self):
        class Observer:
            def observe(self, kind, content):
                self.content = content
                return True
        observer = Observer()
        raw = '{"type":"MCP","output":{},"output":{"Error":"hidden"}}'
        observe_message(observer, {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'content': raw}]}})
        self.assertEqual(observer.content[0]['content'], raw)

    def test_tool_envelope_decodes_without_losing_inner_fields(self):
        class Observer:
            def observe(self, kind, content):
                self.content = content
                return True
        observer = Observer()
        result = {'stdout': {'text': 'quoted "value"'}, 'returncode': 0}
        raw = json.dumps({'type': 'MCP', 'output': {'OkayOutput': json.dumps(result)}})
        observe_message(observer, {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'content': raw}]}})
        self.assertEqual(observer.content[0]['content']['output']['OkayOutput'], result)


if __name__ == '__main__': unittest.main()
