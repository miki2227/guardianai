import functools
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import guarded_agent
from release_broker import ReleaseBroker
from runtime_supervisor import supervise


SENSOR = "/home/pratz/guardianai-tools/unpacked/usr/bin/strace"
LAUNCHER = Path(__file__).resolve().parents[1] / 'native' / 'notify-launch'


@unittest.skipUnless(sys.platform == 'linux' and Path(SENSOR).exists() and LAUNCHER.exists(), 'requires built Linux launcher')
class GuardedAgentTests(unittest.TestCase):
    def setup_case(self, root):
        public, output = root / 'public', root / 'output'
        public.mkdir()
        output.mkdir()
        private = root / 'summary.txt'
        private.write_text('synthetic approved summary')
        return public, output, private

    def test_default_launcher_is_bound_outside_worker_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            public, output, private = self.setup_case(root)
            fixture_broker = functools.partial(ReleaseBroker, observer=lambda state: {'probability': .01})
            fixture_runtime = functools.partial(supervise, observer=lambda task, events: {'probability': .01})
            with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture-not-a-real-key'}), \
                 patch.object(guarded_agent, 'ReleaseBroker', fixture_broker), \
                 patch.object(guarded_agent, 'supervise', fixture_runtime):
                result = guarded_agent.run('Read the approved summary', public, ['/usr/bin/cat', '/protected/summary'],
                                           output=output, evidence=root / 'evidence', resources={'summary': private}, sensor=SENSOR)
            self.assertEqual(result['verdict'], 'no_observed_violation', result)
            self.assertEqual((root / 'evidence' / 'stdout.txt').read_text(), 'synthetic approved summary')
            self.assertFalse(list(public.iterdir()))
            self.assertTrue(result['runtime']['native_stacks'])

    def test_missing_supervisor_key_refuses_before_execution(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ):
            root = Path(directory)
            public, output, private = self.setup_case(root)
            os.environ.pop('TYPESAFE_API_KEY', None)
            with self.assertRaises(RuntimeError):
                guarded_agent.run('Read summary', public, ['/usr/bin/true'], output=output,
                                  evidence=root / 'evidence', resources={'summary': private}, sensor=SENSOR)
            self.assertFalse((root / 'evidence').exists())

    def test_bad_or_already_exposed_resources_refuse_before_execution(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture-not-a-real-key'}):
            root = Path(directory)
            public, output, private = self.setup_case(root)
            exposed = public / 'already-visible.txt'
            exposed.write_text('fake')
            oversized = root / 'oversized.txt'
            oversized.write_bytes(b'x' * 32769)
            for resources in ({'summary': exposed}, {'../summary': private}, {'summary': oversized}):
                with self.subTest(resources=resources), self.assertRaises(ValueError):
                    guarded_agent.run('Read summary', public, ['/usr/bin/true'], output=output,
                                      evidence=root / 'evidence', resources=resources, sensor=SENSOR)
            self.assertFalse((root / 'evidence').exists())
