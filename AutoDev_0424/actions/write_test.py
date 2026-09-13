from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_nonempty
from tools.project_utils import extract_python, write_project_file


class WriteTest(Action):
    name: str = "WriteTest"

    async def run(self, project: Path, prd: str, design: str) -> tuple[Path, str]:
        prompt = f"""你是 QA 工程师，严格执行 TDD：实现代码尚不存在，请先写 pytest 测试。
测试必须从 `src.feature_B` 导入 PRD 定义的公开接口并验证需求。
只使用 pytest 和标准库，最多写 10 个聚焦行为的测试。只输出一个 ```python 代码块，不要解释。

PRD：
{prd}

设计：
{design}
"""
        content = extract_python(await ask_nonempty(self, prompt))
        path = write_project_file(project, "tests/test_generated.py", content)
        return path, content
