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
    parser.add_argument("project", type=Path, help="Python project path; ask to create it when missing")
    parser.add_argument("requirement", help="new requirement B")
    parser.add_argument("--auto-approve", action="store_true", help="simulate approval by the human reviewer")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="AutoDev YAML config path")
    parser.add_argument(
        "--max-fix-rounds",
        type=non_negative_int,
        default=None,
        help="override tdd.max_fix_rounds from config.yaml",
    )
    args = parser.parse_args(argv)
    if not args.requirement.strip():
        parser.error("requirement must not be empty")
    return args


def resolve_max_fix_rounds(args: argparse.Namespace) -> int:
    if args.max_fix_rounds is not None:
        return args.max_fix_rounds
    return load_max_fix_rounds(args.config)


async def prepare_project(project: Path) -> bool:
    project = project.resolve()
    if project.is_dir():
        return True
    if project.exists():
        raise NotADirectoryError(f"Project path is not a directory: {project}")
    while True:
        try:
            answer = (await asyncio.to_thread(
                input, f"项目目录不存在：{project}\n是否创建新 Python 项目并按 TDD 流程实现需求？[y/N] "
            )).strip().lower()
        except EOFError:
            print("未收到创建确认，已取消。")
            return False
        if answer in {"", "n", "no"}:
            print("已取消创建项目。")
            return False
        if answer in {"y", "yes"}:
            project.mkdir(parents=True, exist_ok=True)
            print(f"已创建项目目录：{project}")
            return True
        print("请输入 y 或 n。")


async def async_main() -> int:
    args = parse_args()
    max_fix_rounds = resolve_max_fix_rounds(args)
    if not await prepare_project(args.project):
        return 1
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
