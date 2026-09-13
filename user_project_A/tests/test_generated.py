import copy

import pytest

from src.feature_B import task_summary
from src.todo import add_task, pending_titles

_MISSING = object()


def _task(title, completed=_MISSING):
    """Build a task dict; omit `completed` entirely when not provided."""
    task = {"title": title}
    if completed is not _MISSING:
        task["completed"] = completed
    return task


# AC1 / AC3
def test_mixed_and_uniform_status_counts():
    assert task_summary(
        [_task("a", True), _task("b", False), _task("c", False)]
    ) == {"total": 3, "completed": 1, "pending": 2}

    all_done = [_task("a", True), _task("b", True), _task("c", True)]
    result = task_summary(all_done)
    assert result["completed"] == result["total"] == 3
    assert result["pending"] == 0

    none_done = [_task("a", False), _task("b"), _task("c", False)]
    result = task_summary(none_done)
    assert result["completed"] == 0
    assert result["pending"] == result["total"] == 3


# AC2
def test_empty_input_all_zero_and_each_call_returns_fresh_dict():
    first = task_summary([])
    assert first == {"total": 0, "completed": 0, "pending": 0}

    first["total"] = 99
    first["pending"] = 99
    second = task_summary([])
    assert second == {"total": 0, "completed": 0, "pending": 0}
    assert second is not first

    tasks = [_task("a", True)]
    r1 = task_summary(tasks)
    r2 = task_summary(tasks)
    assert r1 == r2
    assert r1 is not r2


# AC4
def test_missing_completed_key_counts_as_pending_and_is_not_backfilled():
    tasks = [_task("a"), _task("b", True)]
    result = task_summary(tasks)
    assert result == {"total": 2, "completed": 1, "pending": 1}
    assert "completed" not in tasks[0]
    assert set(tasks[0]) == {"title"}


# AC5
@pytest.mark.parametrize(
    "bad_value",
    ["yes", None, 1, 0, 2.5, "", [], {}],
    ids=["str", "none", "int-1", "int-0", "float", "empty-str", "list", "dict"],
)
def test_non_bool_completed_value_raises_value_error(bad_value):
    with pytest.raises(ValueError):
        task_summary([_task("a", bad_value)])


# AC5 (bool/int nuance, value at the end) + AC6
def test_error_path_rejects_ints_and_leaves_no_partial_result():
    assert isinstance(True, int) is True

    result = None
    with pytest.raises(ValueError):
        result = task_summary(
            [_task("a", True), _task("b", False), _task("c", "yes")]
        )
    assert result is None

    with pytest.raises(ValueError):
        task_summary([_task("a", 1)])
    with pytest.raises(ValueError):
        task_summary([_task("a", 0)])


# AC7
def test_inputs_are_not_mutated():
    tasks = [_task("a", True), _task("b", False), _task("c")]
    snapshot = copy.deepcopy(tasks)

    task_summary(tasks)

    assert tasks == snapshot
    assert set(tasks[2]) == {"title"}
    for task, snap in zip(tasks, snapshot):
        assert list(task.keys()) == list(snap.keys())


# AC8
def test_single_pass_iterables_supported_and_consumed_once():
    tasks = [_task("a", True), _task("b", False)]
    expected = {"total": 2, "completed": 1, "pending": 1}

    assert task_summary(tasks) == expected
    assert task_summary(iter(tasks)) == expected
    assert task_summary(map(lambda t: t, tasks)) == expected

    def gen():
        for task in tasks:
            yield task

    generator = gen()
    assert task_summary(generator) == expected
    assert list(generator) == []
    assert task_summary(generator) == {"total": 0, "completed": 0, "pending": 0}


# AC9
def test_pending_count_matches_pending_titles():
    tasks = [_task("a", True), _task("b", False), _task("c"), _task("d", True)]

    assert task_summary(tasks)["pending"] == len(pending_titles(tasks))
    assert task_summary(iter(tasks))["pending"] == len(pending_titles(tasks))


# AC10
def test_result_shape_types_and_invariants():
    result = task_summary([_task("a", True), _task("b", False), _task("c")])

    assert isinstance(result, dict)
    assert set(result) == {"total", "completed", "pending"}
    for value in result.values():
        assert type(value) is int

    assert result["total"] == result["completed"] + result["pending"]
    assert result["total"] >= 0
    assert result["completed"] >= 0
    assert result["pending"] >= 0


# AC11
def test_integration_with_add_task_and_pending_titles():
    tasks = []
    add_task(tasks, "one")
    add_task(tasks, "two")

    assert task_summary(tasks) == {"total": 2, "completed": 0, "pending": 2}
    assert task_summary(tasks)["pending"] == len(pending_titles(tasks))

    tasks[0]["completed"] = True

    assert task_summary(tasks) == {"total": 2, "completed": 1, "pending": 1}
    assert task_summary(tasks)["pending"] == len(pending_titles(tasks))
