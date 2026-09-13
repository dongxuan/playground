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
                response="TEST_FIX\n```python\ndef test_true_is_valid():\n    assert True\n```",
                implementation="def feature(): pass",
                tests="def test_wrong(): assert False",
            )

            self.assertTrue(result.changed)
            self.assertEqual(result.target, "tests")
            self.assertEqual(result.path, (project / "tests/test_generated.py").resolve())
            self.assertIn("test_true_is_valid", result.path.read_text())


if __name__ == "__main__":
    unittest.main()
