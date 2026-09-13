#!/usr/bin/env python3
import argparse
import asyncio
from pathlib import Path

from tools.deepseek_pricing import register

register()

from team import AutoDevTeam


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Use MetaGPT roles to implement a requirement with a TDD workflow.")
    parser.add_argument("project", type=Path, help="existing Python project path")
    parser.add_argument("requirement", help="new requirement B")
    parser.add_argument("--auto-approve", action="store_true", help="simulate approval by the human reviewer")
    parser.add_argument("--max-fix-rounds", type=int, default=2)
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()
    report = await AutoDevTeam(
        project=args.project,
        requirement=args.requirement,
        auto_approve=args.auto_approve,
        max_fix_rounds=args.max_fix_rounds,
    ).run()
    print("\n" + report.output)
    print(f"pytest log: {report.log_path}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
