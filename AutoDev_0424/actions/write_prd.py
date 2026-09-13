from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_nonempty
from tools.project_utils import clean_markdown, write_project_file


class WritePRD(Action):
    name: str = "WritePRD"

    async def run(self, project: Path, requirement: str, snapshot: str) -> tuple[Path, str]:
        prompt = f"""你是产品经理。请基于已有 Python 项目和新需求 B 编写简洁、可测试的 PRD。
必须包含：背景、用户故事、范围、验收标准、非目标。不要虚构项目中不存在的能力。
固定产出约定：实现位于 src/feature_B.py，测试位于 tests/test_generated.py。
只输出 Markdown 正文。

项目路径：{project}
新需求 B：{requirement}
已有代码：
{snapshot}
"""
        content = clean_markdown(await ask_nonempty(self, prompt))
        path = write_project_file(project, "docs/feature_B_prd.md", content)
        return path, content
