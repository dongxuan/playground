import asyncio
import json
from collections import defaultdict
from unittest.mock import AsyncMock, Mock, patch

import pytest
from metagpt.actions import Action

import main
from actions.code_review import apply_review_response
from roles.human_reviewer import HumanReview, HumanReviewer
from tools.workflow_tracker import WorkflowTracker


@pytest.mark.parametrize("opinion", ["", "请增加边界情况"])
def test_rejection_collects_optional_feedback(opinion):
    with patch("builtins.input", side_effect=["n", opinion]):
        result = asyncio.run(HumanReviewer().review("测试", "tests/test_x.py"))
    assert result == HumanReview(False, opinion)


def test_auto_approval_does_not_prompt():
    with patch("builtins.input", side_effect=AssertionError("unexpected input")):
        assert asyncio.run(HumanReviewer(auto_approve=True).review("PRD", "prd.md")).approved


@pytest.mark.parametrize("answer", ["n", "", EOFError()])
def test_declining_new_project_does_not_start_team(tmp_path, answer):
    target = tmp_path / "new_project"
    args = main.parse_args([str(target), "create calculator", "--auto-approve", "--max-fix-rounds", "1"])
    with patch("main.parse_args", return_value=args), patch("main.AutoDevTeam") as team:
        with patch("builtins.input", side_effect=[answer]):
            assert asyncio.run(main.async_main()) == 1
    team.assert_not_called()
    assert not target.exists()


def test_existing_project_and_file_paths(tmp_path):
    with patch("builtins.input", side_effect=AssertionError("unexpected input")):
        assert asyncio.run(main.prepare_project(tmp_path))
    file = tmp_path / "file.py"
    file.write_text("# existing", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        asyncio.run(main.prepare_project(file))
    assert file.read_text() == "# existing"


def test_empty_requirement_is_rejected():
    with pytest.raises(SystemExit):
        main.parse_args(["project", "   "])


def test_joint_review_writes_code_and_tests(tmp_path):
    response = json.dumps({"decision": "CODE_AND_TEST_FIX", "files": [
        {"path": "calc.py", "content": "def add(a, b): return a + b"},
        {"path": "test_calc.py", "content": "from calc import add\ndef test_add(): assert add(1, 2) == 3"},
    ]})
    result = apply_review_response(tmp_path, response)
    assert result.target == "code_and_tests"
    assert result.changed
    assert len(result.paths) == 2
    assert all(path.is_file() for path in result.paths)


@pytest.mark.parametrize("final_no_changes", [False, True])
def test_new_project_retries_every_stage_and_repairs_code_and_tests(tmp_path, final_no_changes):
    """Use real Actions/files/pytest; replace only LLM responses and terminal input."""
    project = tmp_path / "nested" / "calculator"
    log_dir = tmp_path / "logs"
    counts = defaultdict(int)
    prompts = defaultdict(list)
    bad_test = "from calc import add\ndef test_add():\n    assert add(1, 2) == 5\n"
    good_test = bad_test.replace("== 5", "== 3")

    async def answer(action, prompt, *args, **kwargs):
        counts[action.name] += 1
        prompts[action.name].append(prompt)
        if action.name == "WritePRD":
            return f"# PRD revision {counts[action.name]}\nadd(a, b) 返回两数之和。"
        if action.name == "WriteDesign":
            assert "PRD revision 3" in prompt
            return f"# Design revision {counts[action.name]}\ncalc.py 的 add(a, b) 返回 a + b。测试使用 test_calc.py。"
        if action.name == "WriteTest":
            assert "Design revision 2" in prompt
            return json.dumps({"files": [{"path": "test_calc.py", "content": bad_test}]})
        if action.name == "WriteCode":
            return json.dumps({"files": [{"path": "calc.py", "content": "def add(a, b): return a - b"}]})
        assert action.name == "CodeReview"
        assert "原始需求" in prompt and "PRD revision 3" in prompt
        assert "FAILED" in prompt
        if final_no_changes and counts[action.name] == 2:
            return json.dumps({"decision": "NO_CHANGES", "files": []})
        return json.dumps({"decision": "CODE_AND_TEST_FIX", "files": [
            {"path": "calc.py", "content": "def add(a, b): return a + b"},
            {"path": "test_calc.py", "content": good_test},
        ]})

    inputs = [
        "y",  # Create missing directory.
        "n", "明确加法验收标准", "n", "", "y",  # PRD retries, including empty feedback.
        "n", "简化模块", "y",
        "n", "检查测试导入", "y",
        "n", "检查计算逻辑", "y",
        "n", "同时检查断言", "y",  # Retry review inside the same repair round.
    ]
    args = main.parse_args([str(project), "实现 add(a, b) 返回两数之和", "--max-fix-rounds", "1"])
    tracker = WorkflowTracker(log_dir / "workflow.jsonl")
    # Keep every generated artifact and log inside this test's temporary directory.
    from team import AutoDevTeam

    def make_team(**kwargs):
        team = AutoDevTeam(**kwargs)
        team.log_dir = log_dir
        return team

    with patch.object(Action, "_aask", new=answer), patch("team.WorkflowTracker", return_value=tracker):
        with patch("main.AutoDevTeam", side_effect=make_team), patch("main.parse_args", return_value=args):
            with patch("builtins.input", side_effect=inputs):
                assert asyncio.run(main.async_main()) == 0

    assert counts == {"WritePRD": 3, "WriteDesign": 2, "WriteTest": 2, "WriteCode": 2, "CodeReview": 2}
    assert "明确加法验收标准" in prompts["WritePRD"][2]
    assert "未填写意见" in prompts["WritePRD"][2]
    assert "PRD revision 2" in prompts["WritePRD"][2]
    for action, opinion in [("WriteDesign", "简化模块"), ("WriteTest", "检查测试导入"),
                            ("WriteCode", "检查计算逻辑"), ("CodeReview", "同时检查断言")]:
        assert opinion in prompts[action][1]
    assert (project / "test_calc.py").read_text() == good_test
    events = [json.loads(line) for line in tracker.log_path.read_text().splitlines()]
    outcomes = [event["status"] for event in events if event["actor"] == "Run Tests" and event["status"] != "started"]
    assert outcomes == ["failed", "failed", "passed"]
    red_index = next(i for i, event in enumerate(events) if "TDD Red" in event["detail"])
    code_index = next(i for i, event in enumerate(events) if event["actor"] == "Developer")
    assert red_index < code_index
    assert len(list(log_dir.glob("pytest_*.log"))) == 3


def test_no_changes_can_be_rejected_and_retried(tmp_path):
    from actions.code_review import ReviewResult
    from team import AutoDevTeam

    team = object.__new__(AutoDevTeam)
    team.tracker = Mock()
    team.reviewer = Mock(review=AsyncMock(side_effect=[HumanReview(False, "再次检查"), HumanReview(True)]))
    result = ReviewResult(False, "none", (), "")
    action = Mock(run=AsyncMock(return_value=result))
    assert asyncio.run(team._run_reviewed("修复", "Code Review", action, lambda: ())) == result
    assert action.run.await_count == 2
    assert "再次检查" in action.run.call_args.kwargs["feedback"]
