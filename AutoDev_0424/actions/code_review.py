from dataclasses import dataclass
from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_nonempty
from tools.project_utils import extract_python, write_project_file


@dataclass(frozen=True)
class ReviewResult:
    changed: bool
    target: str
    path: Path
    content: str


def apply_review_response(
    project: Path,
    response: str,
    implementation: str,
    tests: str,
) -> ReviewResult:
    """Apply a structured review decision to code or AI-generated tests."""
    decision = response.strip()
    if decision.upper().startswith("NO_CHANGES"):
        return ReviewResult(False, "none", project / "src/feature_B.py", implementation)

    content = extract_python(decision)
    if decision.upper().startswith("TEST_FIX"):
        path = write_project_file(project, "tests/test_generated.py", content)
        return ReviewResult(True, "tests", path, content)
    if decision.upper().startswith("CODE_FIX"):
        path = write_project_file(project, "src/feature_B.py", content)
        return ReviewResult(True, "code", path, content)
    raise ValueError("Review response must start with CODE_FIX, TEST_FIX, or NO_CHANGES")


class CodeReview(Action):
    name: str = "CodeReview"

    async def run(
        self,
        project: Path,
        design: str,
        tests: str,
        implementation: str,
        test_output: str,
    ) -> ReviewResult:
        prompt = f"""你是代码与测试审查工程师。先以技术设计为权威依据定位失败原因。
严格选择且只输出以下一种格式：
1. 实现违背设计：CODE_FIX 后跟一个包含完整 src/feature_B.py 的 ```python 代码块。
2. AI 生成的测试违背设计：TEST_FIX 后跟一个包含完整 tests/test_generated.py 的 ```python 代码块。
3. 两者都无需修改或无法安全判断：NO_CHANGES。
只允许因为测试与设计矛盾而修改测试，不能为迎合错误实现而弱化测试。不得增加第三方依赖。

设计：
{design}

测试：
{tests}

当前实现：
{implementation}

pytest 输出：
{test_output}
"""
        response = await ask_nonempty(self, prompt)
        return apply_review_response(project, response, implementation, tests)
