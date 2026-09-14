from __future__ import annotations

import argparse

from metagpt_demo.coding_rules import RuleConfig
from metagpt_demo.tdd_workflow import TDDOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MetaGPT-style TDD workflow demo")
    parser.add_argument("--requirement", required=True, help="Feature requirement text")
    parser.add_argument("--output-dir", default="./generated_app", help="Output directory")
    parser.add_argument("--max-line-length", type=int, default=120, help="Max line length")
    parser.add_argument("--forbid-print", action="store_true", help="Forbid print() usage")
    parser.add_argument(
        "--require-type-hints",
        action="store_true",
        help="Require function type hints",
    )
    parser.add_argument(
        "--forbid-wildcard-import",
        action="store_true",
        help="Forbid wildcard imports",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = RuleConfig(
        max_line_length=args.max_line_length,
        forbid_print=args.forbid_print,
        require_type_hints=args.require_type_hints,
        forbid_wildcard_import=args.forbid_wildcard_import,
    )

    orchestrator = TDDOrchestrator(rule_config=config)
    result = orchestrator.run(requirement=args.requirement, output_dir=args.output_dir)

    print("=== Phase Log ===")
    for phase in result.phase_log:
        print(f"- {phase}")

    print("\n=== Static Rule Violations ===")
    if not result.rule_violations:
        print("No violations")
    else:
        for violation in result.rule_violations:
            print(f"- {violation}")

    print("\n=== Test Result ===")
    print("PASSED" if result.tests_passed else "FAILED")
    print(result.test_output)


if __name__ == "__main__":
    main()
