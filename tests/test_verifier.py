import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1]


class VerifierAttackTests(unittest.TestCase):
    def make_candidate(self):
        temporary = tempfile.TemporaryDirectory()
        candidate = Path(temporary.name) / "candidate"
        shutil.copytree(SOURCE, candidate, ignore=shutil.ignore_patterns(".git", "evidence", "__pycache__"))
        return temporary, candidate

    def verify(self, candidate):
        return subprocess.run(
            ["python3", "verifier.py"], cwd=candidate, text=True, capture_output=True
        )

    def test_valid_package_passes(self):
        temporary, candidate = self.make_candidate()
        self.addCleanup(temporary.cleanup)
        self.assertEqual(self.verify(candidate).returncode, 0)

    def test_missing_document_is_blocked(self):
        temporary, candidate = self.make_candidate()
        self.addCleanup(temporary.cleanup)
        (candidate / "packages/example-package/example-package.md").unlink()
        result = self.verify(candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing file", result.stdout)

    def test_undeclared_file_is_blocked(self):
        temporary, candidate = self.make_candidate()
        self.addCleanup(temporary.cleanup)
        (candidate / "packages/example-package/hidden.txt").write_text("undeclared")
        result = self.verify(candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("differ from actual", result.stdout)

    def test_incorrect_behavior_is_blocked(self):
        temporary, candidate = self.make_candidate()
        self.addCleanup(temporary.cleanup)
        executable = candidate / "packages/example-package/example-package.py"
        executable.write_text(executable.read_text().replace(
            'return {"sum": payload["left"] + payload["right"]}',
            'return {"sum": 999}',
        ))
        result = self.verify(candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output mismatch", result.stdout)

    def test_escaping_path_is_blocked(self):
        temporary, candidate = self.make_candidate()
        self.addCleanup(temporary.cleanup)
        config_path = candidate / "packages/example-package/example-package.json"
        config = json.loads(config_path.read_text())
        config["parts"]["document"] = "../outside.md"
        config_path.write_text(json.dumps(config))
        result = self.verify(candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("path escapes repository", result.stdout)

    def test_digest_drift_is_blocked(self):
        temporary, candidate = self.make_candidate()
        self.addCleanup(temporary.cleanup)
        document = candidate / "packages/example-package/example-package.md"
        document.write_text(document.read_text() + "\nunapproved drift\n")
        result = self.verify(candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("digest mismatch: document", result.stdout)

    def test_nonconforming_filename_is_blocked(self):
        temporary, candidate = self.make_candidate()
        self.addCleanup(temporary.cleanup)
        source = candidate / "packages/example-package/example-package.md"
        renamed = candidate / "packages/example-package/readme.md"
        source.rename(renamed)
        config_path = candidate / "packages/example-package/example-package.json"
        config = json.loads(config_path.read_text())
        config["parts"]["document"] = "packages/example-package/readme.md"
        config_path.write_text(json.dumps(config))
        result = self.verify(candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("nonconforming filename", result.stdout)

    def test_control_room_gives_action(self):
        temporary, candidate = self.make_candidate()
        self.addCleanup(temporary.cleanup)
        result = self.verify(candidate)
        self.assertEqual(result.returncode, 0)
        control_room = (candidate / "CONTROL-ROOM.md").read_text()
        self.assertIn("## Action required", control_room)
        self.assertIn("Review and approve the exact GitHub pull request", control_room)


if __name__ == "__main__":
    unittest.main()
