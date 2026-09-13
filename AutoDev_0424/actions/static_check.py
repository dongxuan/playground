from pathlib import Path

from metagpt.actions import Action

from tools.linter import check_python


class StaticCheck(Action):
    name: str = "StaticCheck"

    async def run(self, project: Path) -> tuple[bool, str]:
        return check_python(project)
