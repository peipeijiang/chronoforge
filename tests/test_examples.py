from __future__ import annotations

import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ExampleContracts(unittest.TestCase):
    def run_script(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_story_example(self) -> None:
        result = self.run_script(
            "validate_story.py", str(ROOT / "assets" / "story-truth.example.json")
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_timeline_example(self) -> None:
        result = self.run_script(
            "validate_timeline.py", str(ROOT / "assets" / "timeline.example.json")
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_omni_request_example(self) -> None:
        result = self.run_script(
            "updrama_runtime.py",
            "validate",
            str(ROOT / "assets" / "omni-request.example.json"),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
