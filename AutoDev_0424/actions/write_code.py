from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_file_changes
from tools.project_utils import apply_file_changes, format_file_changes


class WriteCode(Action):
    name: str = "WriteCode"

    async def run(self, project: Path, design: str, tests: str, snapshot: str) -> tuple[list[Path], str]:
        prompt = f"""你是开发工程师。根据设计和已经先写好的测试，给出使测试通过的最小实现。
严格遵循架构师基于现有项目确定的文件方案：可以修改原有代码，也可以新增一个或多个代码文件，不要默认创建 feature_B.py。
只改产品代码，不要修改测试；优先使用 Python 标准库。每个 files 项必须包含项目相对路径和该文件修改后的完整内容。
只输出合法 JSON，不要解释：
{{"files":[{{"path":"src/module.py","content":"完整文件内容"}}]}}

设计：
{design}

测试：
{tests}

已有代码：
{snapshot}
"""
        changes = await ask_file_changes(self, prompt)
        paths = apply_file_changes(project, changes)
        return paths, format_file_changes(changes)
