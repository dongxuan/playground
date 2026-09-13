import json
from datetime import datetime, timezone
from pathlib import Path


class WorkflowTracker:
    """Append human-readable events to a machine-readable JSON Lines log."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.sequence = 0
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.write_text("", encoding="utf-8")

    def record(self, actor: str, status: str, detail: str) -> None:
        self.sequence += 1
        event = {
            "sequence": self.sequence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "status": status,
            "detail": detail,
        }
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        print(f"[{self.sequence:02d}] {actor} | {status} | {detail}")
