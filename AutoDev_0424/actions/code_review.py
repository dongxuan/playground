import json
import re
from dataclasses import dataclass
from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_nonempty
from tools.project_utils import apply_file_changes, format_file_changes, parse_file_changes


@dataclass(frozen=True)
class ReviewResult:
    changed: bool
    target: str
    paths: tuple[Path, ...]
    content: str


def apply_review_response(
    project: Path,
    response: str,
) -> ReviewResult:
    """Apply a structured review decision to code or AI-generated tests."""
    match = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
    payload = (match.group(1) if match else response).strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError(f"Review returned invalid JSON: {error}") from error
    decision = data.get("decision") if isinstance(data, dict) else None
    if decision == "NO_CHANGES":
        return ReviewResult(False, "none", (), "")
    if decision not in {"TEST_FIX", "CODE_FIX"}:
        raise ValueError("Review decision must be CODE_FIX, TEST_FIX, or NO_CHANGES")

    changes = parse_file_changes(payload)
    paths = tuple(apply_file_changes(project, changes))
    target = "tests" if decision == "TEST_FIX" else "code"
    return ReviewResult(True, target, paths, format_file_changes(changes))


class CodeReview(Action):
    name: str = "CodeReview"

    async def run(
        self,
        project: Path,
        design: str,
        snapshot: str,
        test_output: str,
    ) -> ReviewResult:
        prompt = f"""你是代码与测试审查工程师。先以技术设计为权威依据定位失败原因。
实现或测试可能涉及一个或多个已有/新增文件，不要假设固定文件名。只允许因为测试与设计矛盾而修改测试，不能为迎合错误实现而弱化测试。
只输出合法 JSON，不要解释。格式：
{{"decision":"CODE_FIX|TEST_FIX|NO_CHANGES","files":[{{"path":"项目相对路径","content":"修改后的完整文件内容"}}]}}
NO_CHANGES 时 files 必须为空；其他决策至少包含一个文件。不得增加第三方依赖。

设计：
{design}

当前项目：
{snapshot}

pytest 输出：
{test_output}
"""
        response = await ask_nonempty(self, prompt)
        return apply_review_response(project, response)
