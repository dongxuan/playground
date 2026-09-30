from datetime import datetime
from pathlib import Path

from actions.code_review import ReviewResult
from actions.run_tests import RunTests
from actions.static_check import StaticCheck
from actions.test_result import TestReport, TestResult
from roles.architect import Architect
from roles.developer import Developer
from roles.human_reviewer import HumanReviewer
from roles.product_manager import ProductManager
from roles.qa_engineer import QAEngineer
from tools.project_utils import feature_name_from_requirement, project_name, scan_project
from tools.workflow_tracker import WorkflowTracker


class AutoDevTeam:
    """A small, explicit MetaGPT role/action pipeline for an existing project."""

    def __init__(self, project: Path, requirement: str, auto_approve: bool, max_fix_rounds: int) -> None:
        if isinstance(max_fix_rounds, bool) or not isinstance(max_fix_rounds, int) or max_fix_rounds < 0:
            raise ValueError("max_fix_rounds must be a non-negative integer")
        self.project = project.resolve()
        self.requirement = requirement
        self.feature_name = feature_name_from_requirement(requirement)
        self.max_fix_rounds = max_fix_rounds
        self.pm = ProductManager()
        self.architect = Architect()
        self.qa = QAEngineer()
        self.developer = Developer()
        self.reviewer = HumanReviewer(auto_approve=auto_approve)
        self.run_tests = RunTests()
        self.static_check = StaticCheck()
        self.test_result = TestResult()
        log_name = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.log_dir = Path(__file__).parent / "logs"
        self.tracker = WorkflowTracker(self.log_dir / log_name)

    async def _run_reviewed(self, stage, actor, action, arguments):
        """Repeat only this action, carrying feedback and its last output forward."""
        opinions = []
        feedback = ""
        while True:
            self.tracker.record(actor, "started", stage)
            result = await action.run(*arguments(), feedback=feedback)
            artifacts = result.paths if isinstance(result, ReviewResult) else result[0]
            paths = [artifacts] if isinstance(artifacts, Path) else list(artifacts)
            display = ", ".join(str(path) for path in paths) or "无修改"
            self.tracker.record(actor, "completed", f"{stage}: {display}")
            decision = await self.reviewer.review(stage, display)
            self.tracker.record(
                "Human Reviewer", "approved" if decision.approved else "rejected",
                f"{stage}: {display}; feedback={decision.feedback}",
            )
            if decision.approved:
                return result
            opinions.append(decision.feedback or "未填写意见，请重新检查并改进当前产物。")
            previous = result.content if isinstance(result, ReviewResult) else result[1]
            feedback = "历次修改意见：\n" + "\n".join(
                f"{index}. {opinion}" for index, opinion in enumerate(opinions, 1)
            ) + f"\n\n上一版产物：\n{previous}"
            self.tracker.record(actor, "retrying", f"{stage}: 人工要求重做第 {len(opinions)} 次")

    async def run(self) -> TestReport:
        if not self.project.is_dir():
            raise FileNotFoundError(f"Target project does not exist: {self.project}")

        self.tracker.record(
            "Team",
            "started",
            f"project={project_name(self.project)} requirement={self.requirement} "
            f"feature_name={self.feature_name} max_fix_rounds={self.max_fix_rounds}",
        )
        _, prd = await self._run_reviewed(
            "PRD", self.pm.profile, self.pm.actions[0],
            lambda: (self.project, self.requirement, scan_project(self.project), self.feature_name),
        )
        _, design = await self._run_reviewed(
            "技术设计", self.architect.profile, self.architect.actions[0],
            lambda: (self.project, prd, scan_project(self.project), self.feature_name),
        )
        _, tests = await self._run_reviewed(
            "测试用例", self.qa.profile, self.qa.actions[0],
            lambda: (self.project, prd, design, scan_project(self.project)),
        )
        # Record the test-first (red) result before implementing the requirement.
        await self._test("实现前测试（TDD Red）")
        await self._run_reviewed(
            "实现代码", self.developer.profile, self.developer.actions[0],
            lambda: (self.project, design, tests, scan_project(self.project)),
        )

        syntax_ok, syntax_output = await self.static_check.run(self.project)
        self.tracker.record("Static Check", "passed" if syntax_ok else "failed", syntax_output)

        report = await self._test()
        for round_number in range(1, self.max_fix_rounds + 1):
            if report.passed:
                break
            self.tracker.record("Code Review & Fix", "started", f"修复轮次 {round_number}")
            try:
                review = await self._run_reviewed(
                    f"审查修复 {round_number}", "Code Review & Fix", self.developer.actions[1],
                    lambda: (self.project, design, scan_project(self.project), report.output, self.requirement, prd),
                )
            except (RuntimeError, ValueError) as error:
                self.tracker.record("Code Review & Fix", "unavailable", str(error))
                break
            self.tracker.record(
                "Code Review & Fix",
                "completed",
                f"changed={review.changed} target={review.target} paths={','.join(str(path) for path in review.paths)}",
            )
            # Earlier rejected attempts may already have changed files, even if
            # the final approved review says NO_CHANGES. Always test the current files.
            report = await self._test()
            if not review.changed and not report.passed:
                self.tracker.record("Code Review & Fix", "stopped", "审查未产生修改，停止无进展重试")
                break

        self.tracker.record("Team", "completed" if report.passed else "failed", f"pytest log={report.log_path}")
        return report

    async def _test(self, stage: str = "实现后测试") -> TestReport:
        self.tracker.record("Run Tests", "started", f"{stage}: 执行 pytest -q")
        returncode, output, log_path = await self.run_tests.run(self.project, self.log_dir)
        report = await self.test_result.run(returncode, output, log_path)
        self.tracker.record("Run Tests", "passed" if report.passed else "failed", str(log_path))
        return report
