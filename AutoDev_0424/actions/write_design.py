from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_nonempty, with_feedback
from tools.project_utils import clean_markdown, write_project_file


class WriteDesign(Action):
    name: str = "WriteDesign"

    async def run(
        self,
        project: Path,
        prd: str,
        snapshot: str,
        feature_name: str,
        feedback: str = "",
    ) -> tuple[Path, str]:
        prompt = f"""你是架构师。根据 PRD 和已有代码写最小技术设计。
先分析项目现有模块、职责和测试约定，再决定文件方案。需求可能修改原有代码，也可能新增一个或多个文件；不要默认创建 feature_B.py。
明确列出每个需要新增或修改的相对路径及理由。优先复用现有模块，只有职责清晰且确有必要时才新增文件。
Python 标准库优先，并说明公开接口、数据流、错误处理和测试策略。
项目尚无代码时，设计最小可运行的 Python 项目布局、公开接口、入口及 pytest 导入方式。
只输出 Markdown 正文。

需求简称：{feature_name}
PRD：
{prd}

已有代码：
{snapshot}
"""
        content = clean_markdown(await ask_nonempty(self, with_feedback(prompt, feedback)))
        path = write_project_file(project, f"docs/{feature_name}_design.md", content)
        return path, content
