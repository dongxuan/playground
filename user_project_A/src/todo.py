from typing import Iterable, Mapping


def add_task(tasks: list[dict], title: str) -> dict:
    """Append and return a new pending task."""
    task = {"title": title.strip(), "completed": False}
    tasks.append(task)
    return task


def pending_titles(tasks: Iterable[Mapping[str, object]]) -> list[str]:
    """Return titles for tasks that are not completed."""
    return [str(task["title"]) for task in tasks if not task.get("completed", False)]
