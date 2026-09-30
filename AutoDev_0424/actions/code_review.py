import json
import re
from dataclasses import dataclass
from pathlib import Path

from metagpt.actions import Action

from actions.llm_utils import ask_nonempty, with_feedback
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
    targets = {"TEST_FIX": "tests", "CODE_FIX": "code", "CODE_AND_TEST_FIX": "code_and_tests"}
    if decision not in targets:
        raise ValueError("Review decision must be CODE_FIX, TEST_FIX, CODE_AND_TEST_FIX, or NO_CHANGES")

    changes = parse_file_changes(payload)
    paths = tuple(apply_file_changes(project, changes))
    target = targets[decision]
    return ReviewResult(True, target, paths, format_file_changes(changes))


class CodeReview(Action):
    name: str = "CodeReview"

    async def run(
        self,
        project: Path,
        design: str,
        snapshot: str,
        test_output: str,
        requirement: str = "",
        prd: str = "",
        feedback: str = "",
    ) -> ReviewResult:
        prompt = f"""你是代码与测试审查工程师。每次失败都同时检查产品代码和测试代码（断言、数据、导入、fixture）。
以原始需求和 PRD 验收标准为依据，结合技术设计定位失败；不能仅因为代码与测试一致就认定行为正确。
实现或测试可能涉及一个或多个已有/新增文件，不要假设固定文件名。
只改代码用 CODE_FIX，只改测试用 TEST_FIX，两者都有问题时用 CODE_AND_TEST_FIX，并在同一 files 列表返回所有修复文件。
测试修复必须有需求、验收标准或测试自身缺陷的依据；不得删除正确断言、跳过失败测试或为错误实现降低验收标准。
只输出合法 JSON，不要解释。格式：
{{"decision":"CODE_FIX|TEST_FIX|CODE_AND_TEST_FIX|NO_CHANGES","files":[{{"path":"项目相对路径","content":"修改后的完整文件内容"}}]}}
NO_CHANGES 时 files 必须为空；其他决策至少包含一个文件。不得增加第三方依赖。

原始需求：
{requirement}

PRD：
{prd}

设计：
{design}

当前项目：
{snapshot}

pytest 输出：
{test_output}
"""
        response = await ask_nonempty(self, with_feedback(prompt, feedback))
        return apply_review_response(project, response)
