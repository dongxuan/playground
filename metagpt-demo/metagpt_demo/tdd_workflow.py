from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .agents import ArchitectAgent, DeveloperAgent, ProductManagerAgent, TesterAgent
from .coding_rules import CodingRuleEngine, RuleConfig


@dataclass
class WorkflowResult:
    output_dir: Path
    phase_log: list[str]
    rule_violations: list[str]
    tests_passed: bool
    test_output: str


class TDDOrchestrator:
    def __init__(self, rule_config: RuleConfig | None = None) -> None:
        self.pm = ProductManagerAgent()
        self.architect = ArchitectAgent()
        self.developer = DeveloperAgent()
        self.tester = TesterAgent()
        self.rule_engine = CodingRuleEngine(rule_config or RuleConfig())

    def run(self, requirement: str, output_dir: str | Path) -> WorkflowResult:
        output_path = Path(output_dir)
        src_dir = output_path / "src"
        tests_dir = output_path / "tests"
        src_dir.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)

        phase_log: list[str] = []

        phase_log.append("PM: analyzing requirement")
        product_spec = self.pm.analyze(requirement)

        phase_log.append("Architect: creating design")
        architecture_spec = self.architect.design(product_spec)

        phase_log.append("Tester: generating tests first (TDD)")
        test_code = self.tester.generate_tests(architecture_spec)
        test_file = tests_dir / f"test_{architecture_spec.module_name}.py"
        test_file.write_text(test_code, encoding="utf-8")

        phase_log.append("Developer: implementing feature")
        impl_code = self.developer.implement(architecture_spec)

        phase_log.append("RuleEngine: checking static coding rules")
        rule_violations = self.rule_engine.check(impl_code)

        impl_file = src_dir / f"{architecture_spec.module_name}.py"
        impl_file.write_text(impl_code, encoding="utf-8")
        (src_dir / "__init__.py").write_text("", encoding="utf-8")
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")

        phase_log.append("Runner: executing unit tests")
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=output_path,
            check=False,
            capture_output=True,
            text=True,
        )
        tests_passed = completed.returncode == 0
        test_output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")

        return WorkflowResult(
            output_dir=output_path,
            phase_log=phase_log,
            rule_violations=rule_violations,
            tests_passed=tests_passed,
            test_output=test_output.strip(),
        )
