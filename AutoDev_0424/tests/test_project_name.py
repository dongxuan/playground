import unittest
from pathlib import Path

from tools.project_utils import extract_python, project_name


class ProjectNameTests(unittest.TestCase):
    def test_extracts_name_from_resolved_project_path(self) -> None:
        self.assertEqual(project_name(Path("/tmp/user_project_A/")), "user_project_A")

    def test_rejects_empty_generated_python(self) -> None:
        with self.assertRaises(ValueError):
            extract_python("   ")


if __name__ == "__main__":
    unittest.main()
