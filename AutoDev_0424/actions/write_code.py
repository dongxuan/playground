from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_nonempty
from tools.project_utils import extract_python, write_project_file


class WriteCode(Action):
    name: str = "WriteCode"

    async def run(self, project: Path, design: str, tests: str, snapshot: str) -> tuple[Path, str]:
        prompt = f"""你是开发工程师。根据设计和已经先写好的测试，给出使测试通过的最小实现。
目标文件固定为 src/feature_B.py。只用 Python 标准库；不要修改测试。
只输出一个 ```python 代码块，不要解释。

设计：
{design}

测试：
{tests}

已有代码：
{snapshot}
"""
        content = extract_python(await ask_nonempty(self, prompt))
        path = write_project_file(project, "src/feature_B.py", content)
        return path, content
