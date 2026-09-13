from typing import Iterable, Mapping


def task_summary(tasks: Iterable[Mapping[str, object]]) -> dict[str, int]:
    """Return total, completed, and pending task counts."""
    total = 0
    completed = 0

    for task in tasks:
        total += 1
        value = task.get("completed", False)

        if not isinstance(value, bool):
            raise ValueError(f"completed must be bool, got {value!r}")

        if value:
            completed += 1

    pending = total - completed
    return {"total": total, "completed": completed, "pending": pending}
