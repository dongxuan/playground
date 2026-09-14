from __future__ import annotations

from pathlib import Path

from metagpt_demo.coding_rules import CodingRuleEngine, RuleConfig
from metagpt_demo.tdd_workflow import TDDOrchestrator


def test_tdd_order_and_test_pass(tmp_path: Path) -> None:
    orchestrator = TDDOrchestrator(rule_config=RuleConfig())
    result = orchestrator.run("实现两个整数相加函数", tmp_path / "generated")

    assert result.tests_passed is True
    assert result.phase_log.index("Tester: generating tests first (TDD)") < result.phase_log.index(
        "Developer: implementing feature"
    )
    assert (tmp_path / "generated" / "tests" / "test_tdd_target.py").exists()
    assert (tmp_path / "generated" / "src" / "tdd_target.py").exists()


def test_rule_engine_detects_print_violation() -> None:
    engine = CodingRuleEngine(RuleConfig(forbid_print=True))
    violations = engine.check("def foo(a: int) -> int:\n    print(a)\n    return a\n")
    assert any("print() is forbidden" in violation for violation in violations)
