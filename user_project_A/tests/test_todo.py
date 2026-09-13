from src.todo import add_task, pending_titles


def test_add_and_list_pending_task() -> None:
    tasks: list[dict] = []
    add_task(tasks, "write demo")
    assert pending_titles(tasks) == ["write demo"]
