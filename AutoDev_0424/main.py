#!/usr/bin/env python3
import argparse
import asyncio
from pathlib import Path
from typing import Sequence

from tools.config import DEFAULT_CONFIG_PATH, load_max_fix_rounds, validate_max_fix_rounds
from tools.deepseek_pricing import register

register()

from team import AutoDevTeam


def non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
        return validate_max_fix_rounds(parsed, "--max-fix-rounds")
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Use MetaGPT roles to implement a requirement with a TDD workflow.")
    parser.add_argument("project", type=Path, help="existing Python project path")
    parser.add_argument("requirement", help="new requirement B")
    parser.add_argument("--auto-approve", action="store_true", help="simulate approval by the human reviewer")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="AutoDev YAML config path")
    parser.add_argument(
        "--max-fix-rounds",
        type=non_negative_int,
        default=None,
        help="override tdd.max_fix_rounds from config.yaml",
    )
    return parser.parse_args(argv)


def resolve_max_fix_rounds(args: argparse.Namespace) -> int:
    if args.max_fix_rounds is not None:
        return args.max_fix_rounds
    return load_max_fix_rounds(args.config)


async def async_main() -> int:
    args = parse_args()
    max_fix_rounds = resolve_max_fix_rounds(args)
    print(f"AutoDev config: max_fix_rounds={max_fix_rounds}")
    report = await AutoDevTeam(
        project=args.project,
        requirement=args.requirement,
        auto_approve=args.auto_approve,
        max_fix_rounds=max_fix_rounds,
    ).run()
    print("\n" + report.output)
    print(f"pytest log: {report.log_path}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
