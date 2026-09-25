import tempfile
import unittest
from pathlib import Path

from tools.project_utils import apply_file_changes, parse_file_changes


class FileChangesTests(unittest.TestCase):
    def test_applies_multiple_new_and_existing_project_files(self) -> None:
        response = '''```json
        {
          "files": [
            {"path": "src/existing.py", "content": "VALUE = 2"},
            {"path": "src/new_module.py", "content": "def feature():\\n    return True"}
          ]
        }
        ```'''

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            existing = project / "src/existing.py"
            existing.parent.mkdir(parents=True)
            existing.write_text("VALUE = 1\n")

            changes = parse_file_changes(response)
            paths = apply_file_changes(project, changes)

            self.assertEqual(len(paths), 2)
            self.assertEqual(existing.read_text(), "VALUE = 2\n")
            self.assertEqual(
                (project / "src/new_module.py").read_text(),
                "def feature():\n    return True\n",
            )


if __name__ == "__main__":
    unittest.main()
