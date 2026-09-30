from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_file_changes, with_feedback
from tools.project_utils import apply_file_changes, format_file_changes


class WriteTest(Action):
    name: str = "WriteTest"

    async def run(self, project: Path, prd: str, design: str, snapshot: str, feedback: str = "") -> tuple[list[Path], str]:
        prompt = f"""你是 QA 工程师，遵循 TDD：请先为需求写 pytest 测试，已有实现可能尚未满足需求。
根据现有测试布局和技术设计，决定修改已有测试文件还是新增一个或多个测试文件。不要默认使用 tests/test_generated.py。
只改测试文件，不改产品代码；测试通过公开接口验证行为，只使用 pytest 和标准库。
每个 files 项必须包含项目相对路径和该文件修改后的完整内容。只输出合法 JSON，不要解释：
{{"files":[{{"path":"tests/test_x.py","content":"完整文件内容"}}]}}

PRD：
{prd}

设计：
{design}

现有项目：
{snapshot}
"""
        changes = await ask_file_changes(self, with_feedback(prompt, feedback))
        paths = apply_file_changes(project, changes)
        return paths, format_file_changes(changes)
