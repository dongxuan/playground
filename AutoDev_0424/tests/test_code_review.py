import tempfile
import unittest
from pathlib import Path

from actions.code_review import apply_review_response


class CodeReviewTests(unittest.TestCase):
    def test_applies_test_fix_when_generated_test_contradicts_design(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            result = apply_review_response(
                project=project,
                response='''```json
                {
                  "decision": "TEST_FIX",
                  "files": [
                    {"path": "tests/test_unit.py", "content": "def test_unit():\\n    assert True"},
                    {"path": "tests/test_integration.py", "content": "def test_integration():\\n    assert True"}
                  ]
                }
                ```''',
            )

            self.assertTrue(result.changed)
            self.assertEqual(result.target, "tests")
            self.assertEqual(len(result.paths), 2)
            self.assertIn("test_unit", (project / "tests/test_unit.py").read_text())
            self.assertIn("test_integration", (project / "tests/test_integration.py").read_text())


if __name__ == "__main__":
    unittest.main()
