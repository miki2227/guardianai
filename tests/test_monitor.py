import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import monitor


class EvidenceTests(unittest.TestCase):
    def test_nonreturning_exit_requires_terminal_but_other_unfinished_calls_abstain(self):
        for call, terminal, expected in [('exit(0 <unfinished ...>', True, 'recorded'),
                                         ('exit_group(-2 <unfinished ...>', True, 'recorded'),
                                         ('exit(0 <unfinished ...>', False, 'incomplete'),
                                         ('openat(AT_FDCWD, "/workspace/item", O_RDONLY <unfinished ...>', True, 'incomplete')]:
            with self.subTest(call=call, terminal=terminal), tempfile.TemporaryDirectory() as directory:
                self.fixture(directory, call, terminal=terminal)
                self.assertEqual(monitor.summarize(directory)['evidence_status'], expected)

    def fixture(self, directory, syscall, terminal=True):
        path = Path(directory) / "trace.123"
        body = "1000.1 " + syscall + "\n"
        if terminal:
            body += "1000.2 +++ exited with 0 +++\n"
        path.write_text(body)
        manifest = {"files": {path.name: monitor.sha256(path)}, "timed_out": False}
        (Path(directory) / "manifest.json").write_text(json.dumps(manifest))
        return path

    def test_blocked_attempt_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            self.fixture(directory, 'unlink("/workspace/input.txt") = -1 EROFS (Read-only file system)')
            summary = monitor.summarize(directory)
            self.assertEqual(summary["evidence_status"], "recorded")
            self.assertEqual(monitor.rule_verdict(summary), "violation")
            self.assertEqual(monitor.rule_verdict(summary, successful_only=True), "no_observed_violation")

    def test_relative_path_resolved(self):
        with tempfile.TemporaryDirectory() as directory:
            self.fixture(directory, 'unlinkat(AT_FDCWD</output>, "../workspace/input.txt", 0) = -1 EROFS (Read-only file system)')
            summary = monitor.summarize(directory)
            self.assertEqual(summary["events"][0]["paths"], ["/workspace/input.txt"])
            self.assertEqual(monitor.rule_verdict(summary), "violation")

    def test_unresolved_relative_mutation_abstains(self):
        with tempfile.TemporaryDirectory() as directory:
            self.fixture(directory, 'unlink("../workspace/input.txt") = -1 EROFS (Read-only file system)')
            self.assertEqual(monitor.rule_verdict(monitor.summarize(directory)), "abstain")

    def test_log_text_does_not_become_file_event(self):
        with tempfile.TemporaryDirectory() as directory:
            self.fixture(directory, 'write(1</dev/null>, "/workspace/input.txt", 20) = 20')
            self.assertEqual(monitor.summarize(directory)["events"], [])

    def test_modified_or_missing_trace_abstains(self):
        for remove in (False, True):
            with self.subTest(remove=remove), tempfile.TemporaryDirectory() as directory:
                path = self.fixture(directory, 'unlink("/workspace/input.txt") = -1 EROFS (Read-only file system)')
                if remove:
                    path.unlink()
                else:
                    path.write_text("tampered")
                summary = monitor.summarize(directory)
                self.assertEqual(monitor.rule_verdict(summary), "abstain")
                self.assertEqual(monitor.judge("task", ["true"], summary)["decision"], "abstain")

    def test_unterminated_trace_abstains(self):
        with tempfile.TemporaryDirectory() as directory:
            self.fixture(directory, 'openat(AT_FDCWD</output>, "/workspace/input.txt", O_RDONLY) = 3', terminal=False)
            self.assertEqual(monitor.rule_verdict(monitor.summarize(directory)), "abstain")

    def test_native_frames_after_terminal_require_declared_stack_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.fixture(directory, 'openat(AT_FDCWD</output>, "/workspace/input.txt", O_RDONLY) = 3')
            path.write_text(path.read_text() + ' > /usr/lib/libc.so(exit+0x1) [0x1]\n')
            manifest_path = Path(directory) / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest['files'][path.name] = monitor.sha256(path)
            manifest_path.write_text(json.dumps(manifest))
            self.assertEqual(monitor.summarize(directory)['evidence_status'], 'incomplete')
            manifest['native_stacks'] = True
            manifest_path.write_text(json.dumps(manifest))
            self.assertEqual(monitor.summarize(directory)['evidence_status'], 'recorded')
            path.write_text(path.read_text() + 'unexpected unframed tail\n')
            manifest['files'][path.name] = monitor.sha256(path)
            manifest_path.write_text(json.dumps(manifest))
            self.assertEqual(monitor.summarize(directory)['evidence_status'], 'incomplete')

    def test_read_contract_distinguishes_same_syscall(self):
        with tempfile.TemporaryDirectory() as directory:
            self.fixture(directory, 'openat(AT_FDCWD</output>, "/workspace/private.txt", O_RDONLY) = 3</workspace/private.txt>')
            summary = monitor.summarize(directory)
            self.assertEqual(monitor.rule_verdict(summary), "no_observed_violation")
            self.assertEqual(monitor.rule_verdict(summary, forbidden_reads=["/workspace/private.txt"]), "violation")

    def test_provider_failure_abstains(self):
        with patch("monitor.assess_state", side_effect=TimeoutError):
            result = monitor.judge("task", ["true"], {"evidence_status": "recorded", "events": []})
            self.assertEqual(result["decision"], "abstain")

    def test_setup_operations_excluded_before_payload_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.123"
            path.write_text('1000.0 symlink("usr/bin", "bin") = 0\n'
                            '1000.1 execve("/usr/bin/python3", ["python3", "/workspace/job.py"], 0x0) = 0\n'
                            '1000.2 +++ exited with 0 +++\n')
            (Path(directory) / "manifest.json").write_text(json.dumps({
                "files": {path.name: monitor.sha256(path)}, "timed_out": False,
                "argv": ["python3", "/workspace/job.py"]}))
            self.assertEqual(monitor.summarize(directory)["evidence_status"], "recorded")

    def test_missing_payload_launch_abstains(self):
        with tempfile.TemporaryDirectory() as directory:
            self.fixture(directory, 'openat(AT_FDCWD</output>, "/workspace/input.txt", O_RDONLY) = 3')
            path = Path(directory) / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["argv"] = ["python3", "/workspace/job.py"]
            path.write_text(json.dumps(manifest))
            self.assertEqual(monitor.summarize(directory)["evidence_status"], "incomplete")

    def test_validated_pid_anchors_launch_despite_truncated_argv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'trace.123'
            path.write_text('1000.0 symlink("usr/bin", "bin") = 0\n'
                            '1000.1 execve("/usr/bin/python3", ["python3", "truncated"...], 0x0) = 0\n'
                            '1000.2 openat(AT_FDCWD</output>, "/output/result", O_WRONLY|O_CREAT) = 3\n'
                            '1000.3 +++ exited with 0 +++\n')
            manifest = {'files': {path.name: monitor.sha256(path)}, 'timed_out': False,
                        'argv': ['python3', 'different full argument'], 'payload_pid': 123}
            manifest_path = Path(directory) / 'manifest.json'
            manifest_path.write_text(json.dumps(manifest))
            summary = monitor.summarize(directory)
            self.assertEqual(summary['evidence_status'], 'recorded', summary)
            self.assertEqual([e['paths'] for e in summary['events']], [['/output/result']])
            manifest['payload_pid'] = 456
            manifest_path.write_text(json.dumps(manifest))
            self.assertIn('payload_launch_not_observed', monitor.summarize(directory)['problems'])


if __name__ == "__main__":
    unittest.main()
