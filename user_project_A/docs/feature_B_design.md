# 技术设计：`task_summary` 任务统计（需求 B）

## 1. 落点与边界

| 项 | 约定 |
| --- | --- |
| 实现 | `src/feature_B.py`，唯一公开函数 `task_summary` |
| 测试 | `tests/test_generated.py`，覆盖 AC1–AC11 |
| 冻结 | 不改 `src/todo.py` 的 `add_task` / `pending_titles` 签名与行为；不做 re-export |
| 依赖 | 运行时仅标准库（`typing` 仅用于标注，`dict[...]`/`list[...]` 属内建泛型）；测试仅用 `pytest` |
| 验证 | `python -m pytest tests -q` 全绿 |

## 2. 公开接口

```python
def task_summary(tasks: Iterable[Mapping[str, object]]) -> dict[str, int]: ...
```

- **入参**：可迭代的 `Mapping` 集合（任务 dict），口径与 `pending_titles` 一致；容器类型不受限（list / tuple / generator / `iter(...)` / `map(...)`）。
- **返回**：每次调用新建的 `dict`，键精确为 `total`、`completed`、`pending`，值均满足 `type(v) is int`。
- **不变式**：`total == completed + pending`，`total >= 0`，`completed >= 0`，`pending >= 0`。
- **空输入**：`{"total": 0, "completed": 0, "pending": 0}`。
- **副作用**：无。不修改入参容器与任务 dict，不缓存，无全局状态；调用方修改返回值不影响后续调用。
- **遍历次数**：恰好一次，因此单次可迭代对象（生成器等）可用且被耗尽。

## 3. 数据流与算法

```python
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
```

```text
tasks: Iterable[Mapping] ──► for task in tasks        （仅一次迭代，不 len()、不索引、不二次遍历）
                              total += 1
                              value = task.get("completed", False)
                              isinstance(value, bool)? ──否──► raise ValueError
                              value is True? ──是──► completed += 1
                          ◄── pending = total - completed
                              {"total", "completed", "pending"}
```

关键决策：

- `task.get("completed", False)` 与 `pending_titles` 的取值口径严格一致：缺失键按 `False` 处理，且**不回填**任务 dict。
- `isinstance(value, bool)` 同时接受 `True`/`False`、拒绝 `1`/`0`（`bool` 是 `int` 子类，但反向不成立，故 `1` 必被拒）；先校验后计数，非法值不进入累计。
- 只维护 `total` 与 `completed` 两个计数，`pending` 由末尾一次减法得出，保证不变式恒成立且成本最低。
- 计数变量以 `int` 字面量 `0` 起算、由 `int` 加法累加，不会引入 `bool`，满足 AC10 的 `type(v) is int` 严格判定。
- 返回字面量 dict，天然满足「返回值独立」。

## 4. 错误处理

| 情形 | 行为 |
| --- | --- |
| `completed` 键缺失 | 按 `False`，计入 `pending`；不抛错、不回填 |
| `completed is True` | 计入 `completed` |
| `completed is False` | 计入 `pending` |
| `"yes"` / `None` / `1` / `0` / `2.5` / `""` / `[]` / `{}` | 立即 `raise ValueError` |
| 非法值出现在末尾（前面已有合法任务） | 同样抛错，不返回部分统计 |
| 元素非 `Mapping`（无 `.get`） | 自然抛 `AttributeError`，不包装容错（调用方违约） |

规则：

- 校验位于累计之前，异常点即函数出口；`return` 在循环之后，故异常路径**不存在**部分统计结果，调用方赋值变量保持原值。
- 异常消息不承诺固定文案，仅保证可定位非法取值；`!r` 便于区分 `1` 与 `True`。
- 不定义自定义异常、不 `try/except` 吞异常、不做宽松兜底。

## 5. 测试策略：`tests/test_generated.py`

纯断言 + 参数化；`task_summary` 从 `src.feature_B` 导入，一致性用例以 `src.todo.pending_titles` 为对照，回归依赖 `tests/test_todo.py` 既有用例。辅助构造器 `_task(title, completed=_MISSING)` 用于区分「缺失键」与「值为 `None`」。

| 验收项 | 测试要点 |
| --- | --- |
| AC1 / AC3 | 混合态 `[a:True, b:False, c:False]` → `3/1/2`；全完成 → `pending == 0` 且 `completed == total`；全未完成（含缺失键）→ `completed == 0` 且 `pending == total` |
| AC2 | `[]` 返回全零；改写首次返回值后再调用仍全零，且 `second is not first` |
| AC4 | 缺失键计入 `pending` 且不抛错；调用后任务 dict 仍不含 `completed` 键 |
| AC5 | 参数化 `"yes"`、`None`、`1`、`0`、`2.5`、`""`、`[]`、`{}`，**逐值独立** `pytest.raises(ValueError)`，防短路掩盖；断言 `isinstance(True, int) is True` 但 `1`/`0` 仍被拒；非法值位于末尾同样抛错 |
| AC6 | 非法输入下调用方变量保持 `None`，无部分统计 |
| AC7 | 调用前 `copy.deepcopy` → 调用 → 与原快照相等；逐元素比对 `keys()` 与内容；确认缺失键仍缺失 |
| AC8 | `list` / `iter(list)` / `map(...)` 结果正确；同一生成器调用后 `list(generator) == []`，再次调用返回全零——反证「仅遍历一次」 |
| AC9 | `completed` 全为布尔值或缺失的数据集下，`task_summary(tasks)["pending"] == len(pending_titles(tasks))`（含 `iter(...)` 版本） |
| AC10 | `isinstance(result, dict)`；`set(result) == {"total","completed","pending"}`；每值 `type(v) is int`（非 `isinstance`，排除 `bool` 误写）；`total == completed + pending` 且 `total >= 0` |
| AC11 | `tests/test_todo.py` 既有用例保持通过；集成：`add_task` 两条 → `0/2`，`tasks[0]["completed"] = True` → `1/1`，两次均与 `pending_titles` 长度对齐 |

注意点：

- AC10 严格用 `type(v) is int`，避免 `isinstance` 放行 `bool` 而掩盖计数误写。
- AC9 数据集需含 `title` 键，否则 `pending_titles` 会抛 `KeyError`（其实现读 `task["title"]`）。
- 实现改动（如引入 `len()`、二次遍历、用真值判断替代 `isinstance`）都会由 AC8 / AC5 / AC10 之一捕获，无需额外用例。

## 6. 明确不做

不新增 CLI、配置或序列化；不做持久化与全局状态；不加 `Task` 类 / `dataclass` / 类型重构；不做缓存与增量统计；不新增统计维度（去重、排序、过滤等）；不约束 `ValueError` 文案、不定义自定义异常；不修改 `src/todo.py` 的签名、行为与导入路径。
