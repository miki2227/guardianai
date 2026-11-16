import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import guardian


class GateTests(unittest.TestCase):
    def test_missing_key_refuses(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                guardian.assess("count", ["true"])

    def test_invalid_answers_refuse(self):
        for value in (float("nan"), float("inf"), -1, 2, True, "0.01"):
            with self.subTest(value=value), patch.dict(os.environ, {"TYPESAFE_API_KEY": "test"}):
                response = unittest.mock.MagicMock()
                response.__enter__.return_value.read.return_value = json.dumps({
                    "model": "jev-1.14.0", "answers": {"violation": {"type": "noul", "noul": value}}
                }).encode()
                with patch("urllib.request.urlopen", return_value=response):
                    with self.assertRaises(ValueError):
                        guardian.assess("count", ["true"])


@unittest.skipUnless(sys.platform == "linux", "requires real Linux namespaces")
class KernelTests(unittest.TestCase):
    def test_helper_cannot_delete_input(self):
        with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory() as output:
            canary = Path(workspace) / "preserve.txt"
            canary.write_text("FAKE-INPUT-CANARY")
            helper = Path(workspace) / "helper.sh"
            helper.write_text("printf ok > /output/result.txt\nrm /workspace/preserve.txt\n")
            result = guardian.execute(workspace, ["sh", "/workspace/helper.sh"], output=output)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(canary.read_text(), "FAKE-INPUT-CANARY")
            self.assertEqual((Path(output) / "result.txt").read_text(), "ok")

    def run_payload(self, code):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as output:
            return subprocess.run(guardian.sandbox_argv(directory, ["python3", "-c", code], output=output),
                                  stdin=subprocess.DEVNULL, capture_output=True,
                                  env={"PATH": "/usr/bin:/bin"}, timeout=15)

    def check_payload(self, code):
        result = self.run_payload(code)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_benign_write(self):
        self.check_payload("from pathlib import Path; p=Path('result'); p.write_text('ok'); assert p.read_text()=='ok'")

    def test_host_secret_absent(self):
        with tempfile.NamedTemporaryFile() as secret:
            self.check_payload(f"from pathlib import Path; assert not Path({secret.name!r}).exists()")

    def test_runtime_readonly(self):
        self.check_payload("import os;\ntry: open('/usr/guardian-test','w')\nexcept OSError: pass\nelse: raise AssertionError('write allowed')")

    def test_network_unreachable(self):
        self.check_payload("import socket; s=socket.socket(); s.settimeout(1)\ntry: s.connect(('192.0.2.1',443))\nexcept OSError: pass\nelse: raise AssertionError('network reachable')")

    def test_credentials_removed(self):
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "fake-canary"}):
            self.check_payload("import os; assert 'TYPESAFE_API_KEY' not in os.environ")

    def test_child_inherits_isolation(self):
        self.check_payload("import subprocess; r=subprocess.run(['sh','-c','test ! -e /mnt/c']); assert r.returncode==0")

    def test_symlink_does_not_reach_host(self):
        self.check_payload("import os; os.symlink('/mnt/c/Users','escape'); assert not os.path.exists('escape')")

    def test_overlapping_directories_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            nested = Path(directory) / "nested"
            nested.mkdir()
            alias = Path(directory) / "alias"
            alias.symlink_to(nested, target_is_directory=True)
            for workspace, output in ((directory, directory), (directory, nested),
                                      (nested, directory), (directory, alias)):
                with self.subTest(workspace=workspace, output=output):
                    with self.assertRaises(ValueError):
                        guardian.sandbox_argv(workspace, ["true"], output=output)

    def test_nonempty_output_refused(self):
        with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory() as output:
            (Path(output) / "existing").write_text("preserve")
            with self.assertRaises(ValueError):
                guardian.sandbox_argv(workspace, ["true"], output=output)

    def test_output_symlink_cannot_modify_input(self):
        with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory() as output:
            canary = Path(workspace) / "preserve.txt"
            canary.write_text("FAKE-INPUT-CANARY")
            code = (
                "import os\n"
                "os.symlink('/workspace/preserve.txt', '/output/link')\n"
                "try: open('/output/link', 'w').write('modified')\n"
                "except OSError: pass\n"
                "else: raise AssertionError('input modified through symlink')\n"
            )
            result = guardian.execute(workspace, ["python3", "-c", code], output=output)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(canary.read_text(), "FAKE-INPUT-CANARY")

    def test_execute_closes_inheritable_host_fd(self):
        with (tempfile.TemporaryDirectory() as directory,
              tempfile.TemporaryDirectory() as output, tempfile.TemporaryFile() as canary):
            canary.write(b"FAKE-FD-CANARY")
            canary.flush()
            canary.seek(0)
            os.set_inheritable(canary.fileno(), True)
            code = (
                "import os\n"
                "for name in os.listdir('/proc/self/fd'):\n"
                " if int(name) <= 2: continue\n"
                " try: value=os.read(int(name), 64)\n"
                " except OSError: continue\n"
                " assert b'FAKE-FD-CANARY' not in value, 'host descriptor leaked'\n"
            )
            result = guardian.execute(directory, ["python3", "-c", code], output=output)
            self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
