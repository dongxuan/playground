from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_nonempty
from tools.project_utils import clean_markdown, write_project_file


class WriteDesign(Action):
    name: str = "WriteDesign"

    async def run(self, project: Path, prd: str, snapshot: str) -> tuple[Path, str]:
        prompt = f"""你是架构师。根据 PRD 和已有代码写最小技术设计。
约束：Python 标准库优先；实现放在 src/feature_B.py；测试放在 tests/test_generated.py；说明公开接口、数据流、错误处理和测试策略。
只输出 Markdown 正文。

PRD：
{prd}

已有代码：
{snapshot}
"""
        content = clean_markdown(await ask_nonempty(self, prompt))
        path = write_project_file(project, "docs/feature_B_design.md", content)
        return path, content
