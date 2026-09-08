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


if __name__ == "__main__":
    unittest.main()
