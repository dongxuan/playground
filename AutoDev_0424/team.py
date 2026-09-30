from datetime import datetime
from pathlib import Path

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

    async def _approve(self, stage: str, artifacts: Path | list[Path] | tuple[Path, ...]) -> None:
        paths = [artifacts] if isinstance(artifacts, Path) else list(artifacts)
        display = ", ".join(str(path) for path in paths)
        approved = await self.reviewer.review(stage, display)
        self.tracker.record("Human Reviewer", "approved" if approved else "rejected", f"{stage}: {display}")
        if not approved:
            raise RuntimeError(f"Human reviewer rejected {stage}")

    async def run(self) -> TestReport:
        if not self.project.is_dir():
            raise FileNotFoundError(f"Target project does not exist: {self.project}")

        self.tracker.record(
            "Team",
            "started",
            f"project={project_name(self.project)} requirement={self.requirement} "
            f"feature_name={self.feature_name} max_fix_rounds={self.max_fix_rounds}",
        )
        snapshot = scan_project(self.project)

        self.tracker.record(self.pm.profile, "started", "分析已有代码并编写 PRD")
        prd_path, prd = await self.pm.actions[0].run(
            self.project,
            self.requirement,
            snapshot,
            self.feature_name,
        )
        self.tracker.record(self.pm.profile, "completed", str(prd_path))
        await self._approve("PRD", prd_path)

        self.tracker.record(self.architect.profile, "started", "编写技术设计")
        design_path, design = await self.architect.actions[0].run(
            self.project,
            prd,
            snapshot,
            self.feature_name,
        )
        self.tracker.record(self.architect.profile, "completed", str(design_path))
        await self._approve("技术设计", design_path)

        self.tracker.record(self.qa.profile, "started", "先编写测试")
        test_paths, tests = await self.qa.actions[0].run(self.project, prd, design, snapshot)
        self.tracker.record(self.qa.profile, "completed", ", ".join(str(path) for path in test_paths))
        await self._approve("测试用例", test_paths)

        self.tracker.record(self.developer.profile, "started", "根据设计和测试编写实现")
        code_paths, _ = await self.developer.actions[0].run(
            self.project, design, tests, scan_project(self.project)
        )
        self.tracker.record(self.developer.profile, "completed", ", ".join(str(path) for path in code_paths))
        await self._approve("实现代码", code_paths)

        syntax_ok, syntax_output = await self.static_check.run(self.project)
        self.tracker.record("Static Check", "passed" if syntax_ok else "failed", syntax_output)

        report = await self._test()
        for round_number in range(1, self.max_fix_rounds + 1):
            if report.passed:
                break
            self.tracker.record("Code Review & Fix", "started", f"修复轮次 {round_number}")
            try:
                review = await self.developer.actions[1].run(
                    self.project, design, scan_project(self.project), report.output
                )
            except (RuntimeError, ValueError) as error:
                self.tracker.record("Code Review & Fix", "unavailable", str(error))
                break
            self.tracker.record(
                "Code Review & Fix",
                "completed",
                f"changed={review.changed} target={review.target} paths={','.join(str(path) for path in review.paths)}",
            )
            if not review.changed:
                self.tracker.record("Code Review & Fix", "stopped", "审查未产生修改，停止无进展重试")
                break
            await self._approve(f"{review.target} 修复 {round_number}", review.paths)
            report = await self._test()

        self.tracker.record("Team", "completed" if report.passed else "failed", f"pytest log={report.log_path}")
        return report

    async def _test(self) -> TestReport:
        self.tracker.record("Run Tests", "started", "执行 pytest -q")
        returncode, output, log_path = await self.run_tests.run(self.project, self.log_dir)
        report = await self.test_result.run(returncode, output, log_path)
        self.tracker.record("Run Tests", "passed" if report.passed else "failed", str(log_path))
        return report
