import subprocess
import sys
from datetime import datetime
from pathlib import Path

from metagpt.actions import Action


class RunTests(Action):
    name: str = "RunTests"

    async def run(self, project: Path, log_dir: Path) -> tuple[int, str, Path]:
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        output = (process.stdout + process.stderr).strip()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"pytest_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.log"
        log_path.write_text(output + "\n", encoding="utf-8")
        return process.returncode, output, log_path
