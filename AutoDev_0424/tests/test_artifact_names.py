import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from actions.write_design import WriteDesign
from actions.write_prd import WritePRD
from tools.project_utils import feature_name_from_requirement


class ArtifactNameTests(unittest.IsolatedAsyncioTestCase):
    def test_uses_function_name_as_requirement_short_name(self) -> None:
        name = feature_name_from_requirement(
            "新增 task_summary(tasks)：返回 total、completed、pending 数量"
        )

        self.assertEqual(name, "task_summary")

    def test_falls_back_to_feature_timestamp_for_chinese_only_requirement(self) -> None:
        name = feature_name_from_requirement(
            "新增任务汇总功能",
            now=datetime(2026, 9, 30, 12, 34, 56),
        )

        self.assertEqual(name, "feature_20260930_123456")

    async def test_prd_and_design_use_the_same_requirement_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            feature_name = "task_summary"

            with patch("actions.write_prd.ask_nonempty", new=AsyncMock(return_value="# PRD")):
                prd_path, prd = await WritePRD().run(
                    project,
                    "新增 task_summary(tasks)",
                    "snapshot",
                    feature_name,
                )
            with patch("actions.write_design.ask_nonempty", new=AsyncMock(return_value="# Design")):
                design_path, _ = await WriteDesign().run(
                    project,
                    prd,
                    "snapshot",
                    feature_name,
                )

            self.assertEqual(prd_path.relative_to(project.resolve()), Path("docs/task_summary_prd.md"))
            self.assertEqual(design_path.relative_to(project.resolve()), Path("docs/task_summary_design.md"))


if __name__ == "__main__":
    unittest.main()
