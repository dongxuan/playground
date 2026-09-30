from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_nonempty, with_feedback
from tools.project_utils import clean_markdown, write_project_file


class WritePRD(Action):
    name: str = "WritePRD"

    async def run(
        self,
        project: Path,
        requirement: str,
        snapshot: str,
        feature_name: str,
        feedback: str = "",
    ) -> tuple[Path, str]:
        prompt = f"""你是产品经理。请基于 Python 项目和需求编写简洁、可测试的 PRD。
项目为空时按全新项目分析需求，不要假设已有实现。
必须包含：背景、用户故事、范围、验收标准、非目标。不要虚构项目中不存在的能力。
不要预设实现文件；文件方案由架构师分析现有项目后决定。
只输出 Markdown 正文。

项目路径：{project}
需求简称：{feature_name}
新需求 B：{requirement}
已有代码：
{snapshot}
"""
        content = clean_markdown(await ask_nonempty(self, with_feedback(prompt, feedback)))
        path = write_project_file(project, f"docs/{feature_name}_prd.md", content)
        return path, content
