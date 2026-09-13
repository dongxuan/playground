from dataclasses import dataclass
from pathlib import Path

from metagpt.actions import Action


@dataclass(frozen=True)
class TestReport:
    passed: bool
    output: str
    log_path: Path


class TestResult(Action):
    name: str = "TestResult"

    async def run(self, returncode: int, output: str, log_path: Path) -> TestReport:
        return TestReport(returncode == 0, output, log_path)
