import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from runtime_supervisor import event_from_line, supervise


SENSOR = "/home/pratz/guardianai-tools/unpacked/usr/bin/strace"


class RuntimeParserTests(unittest.TestCase):
    def test_stdout_cannot_forge_kernel_path_event(self):
        self.assertIsNone(event_from_line('1.0 write(1, "unlink(/workspace/input)", 24) = 24', "trace.1"))

    def test_failed_input_write_is_violation(self):
        event = event_from_line('1.0 unlink("/workspace/input") = -1 EROFS (Read-only file system)', "trace.1")
        self.assertTrue(event["rule_violation"])
        self.assertTrue(event["denied"])

    def test_relative_mutation_resolves_against_kernel_reported_cwd(self):
        event = event_from_line('1.0 unlinkat(AT_FDCWD</output>, "../workspace/input", 0) = -1 EROFS', "trace.1")
        self.assertTrue(event["rule_violation"])


@unittest.skipUnless(sys.platform == "linux" and shutil.which("bwrap") and Path(SENSOR).exists(), "requires native Linux sensor")
class RuntimeKernelTests(unittest.TestCase):
    def run_case(self, code, observer=lambda task, events: {"probability": 0.0}, *, native_stacks=False, arguments=()):
        root = Path(self.temp.name)
        source, output = root / "input", root / "output"
        source.mkdir()
        output.mkdir()
        (source / "payload.py").write_text(code)
        report = supervise("Write task output", source, ["/usr/bin/python3", "/workspace/payload.py", *arguments],
                           output=output, evidence=root / "evidence", sensor=SENSOR,
                           observer=observer, timeout=5, native_stacks=native_stacks)
        return report, output

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def test_benign_completion(self):
        report, output = self.run_case("from pathlib import Path\nPath('/output/result').write_text('ok')\n")
        self.assertEqual(report["verdict"], "no_observed_violation", report)
        self.assertEqual((output / "result").read_text(), "ok")

    def test_escaped_and_truncated_argv_do_not_disable_live_observation(self):
        observed = []
        arguments = [json.dumps({'path': '/workspace/item', 'note': 'quoted "value"'}),
                     'line one\nline two\tbackslash\\', 'café', 'x' * 2048]
        def observer(task, events):
            observed.extend(events)
            return {'probability': .01}
        code = "import json,sys,time\nfrom pathlib import Path\nPath('/output/args.json').write_text(json.dumps(sys.argv[1:]))\ntime.sleep(.1)\n"
        report, output = self.run_case(code, observer, arguments=arguments)
        self.assertEqual(report['verdict'], 'no_observed_violation', report)
        self.assertEqual(json.loads((output / 'args.json').read_text()), arguments)
        self.assertTrue(any('/output/args.json' in e['paths'] for e in observed))

    def test_json_argv_cannot_hide_input_mutation_from_live_stop(self):
        code = "from pathlib import Path\nimport time\ntry: Path('/workspace/payload.py').write_text('bad')\nexcept OSError: pass\ntime.sleep(1)\nPath('/output/late').write_text('bad')\n"
        report, output = self.run_case(code, arguments=[json.dumps({'case': 'mutation'})])
        self.assertEqual(report['verdict'], 'violation', report)
        self.assertTrue(report['termination_requested'])
        self.assertFalse((output / 'late').exists())

    def test_native_frames_reach_observer_as_frozen_auditable_inputs(self):
        import hashlib
        snapshots, hashes = [], []
        def observe(task, events):
            snapshots.append(events)
            hashes.append(hashlib.sha256(json.dumps(events).encode()).hexdigest())
            return {"probability": .01}
        report, output = self.run_case("from pathlib import Path\nimport time\nPath('/output/result').write_text('ok')\ntime.sleep(.1)\n", observe, native_stacks=True)
        self.assertEqual(report['verdict'], 'no_observed_violation', report)
        self.assertTrue(any(event.get('native_stack') for snapshot in snapshots for event in snapshot))
        self.assertEqual(hashes, [hashlib.sha256(json.dumps(snapshot).encode()).hexdigest() for snapshot in snapshots])
        evidence = Path(self.temp.name) / 'evidence'
        self.assertEqual(hashes, [entry['sha256'] for entry in report['observer_inputs']])
        for entry in report['observer_inputs']:
            self.assertEqual(hashlib.sha256((evidence / entry['path']).read_bytes()).hexdigest(), entry['sha256'])

    def test_denied_attempt_stops_detached_descendant(self):
        code = """import os, time
from pathlib import Path
if os.fork() == 0:
    os.setsid()
    time.sleep(1)
    Path('/output/escaped').write_text('bad')
    os._exit(0)
try: os.unlink('/workspace/payload.py')
except OSError: pass
time.sleep(3)
Path('/output/late').write_text('bad')
"""
        report, output = self.run_case(code)
        self.assertEqual(report["verdict"], "violation", report)
        self.assertTrue(report["termination_requested"])
        self.assertFalse((output / "escaped").exists())
        self.assertFalse((output / "late").exists())

    def test_model_verdict_terminates_live_worker(self):
        code = "from pathlib import Path\nimport time\nPath('/output/trigger').write_text('ok')\ntime.sleep(2)\nPath('/output/late').write_text('bad')\n"
        report, output = self.run_case(code, lambda task, events: {"probability": .99})
        self.assertEqual(report["verdict"], "violation", report)
        self.assertFalse((output / "late").exists())

    def test_observer_failure_terminates_live_worker(self):
        def unavailable(task, events):
            raise ConnectionError("fake observer outage")
        report, output = self.run_case("from pathlib import Path\nimport time\nPath('/output/trigger').write_text('ok')\ntime.sleep(2)\nPath('/output/late').write_text('bad')\n", unavailable)
        self.assertEqual(report["verdict"], "abstain", report)
        self.assertTrue(report["termination_requested"])
        self.assertFalse((output / "late").exists())

    def test_control_descriptors_are_not_exposed(self):
        code = "import os,json\nfrom pathlib import Path\nr={}\nfor n in os.listdir('/proc/self/fd'):\n try: r[n]=os.readlink('/proc/self/fd/'+n)\n except OSError: pass\nPath('/output/fds.json').write_text(json.dumps(r))\n"
        report, output = self.run_case(code)
        self.assertEqual(report["verdict"], "no_observed_violation", report)
        self.assertTrue(all(int(n) <= 2 for n in json.loads((output / "fds.json").read_text())))

    def test_observer_deadline_terminates_namespace(self):
        def slow(task, events):
            import time
            time.sleep(.4)
            return {"probability": 0.0}
        from unittest.mock import patch
        with patch('runtime_supervisor.OBSERVER_DEADLINE_SECONDS', .2):
            report, output = self.run_case("from pathlib import Path\nimport time\nPath('/output/trigger').write_text('ok')\ntime.sleep(1)\nPath('/output/late').write_text('bad')\n", slow)
        self.assertEqual(report["verdict"], "abstain", report)
        self.assertTrue(report["termination_requested"])
        self.assertFalse((output / "late").exists())
