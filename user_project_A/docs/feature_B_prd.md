# PRD：`task_summary` 任务统计（需求 B）

## 1. 背景

`user_project_A` 是一个仅使用 Python 标准库的极小任务列表示例。现有 `src/todo.py` 提供两个能力：

- `add_task(tasks, title)`：向列表追加 `{"title": ..., "completed": False}` 并返回该任务 dict；
- `pending_titles(tasks)`：以 `task.get("completed", False)` 判断，返回未完成任务的标题列表。

当前有两个缺口：

1. 只能列出未完成任务标题，没有数量统计。调用方要得到总任务数 / 已完成 / 未完成，只能自己再遍历一次。
2. `completed` 取值无校验。当它被写成 `"yes"`、`None`、`1` 时，`pending_titles` 会按真值 / 假值静默判断，产生「看似正常、实际错误」的结果。

需求 B：新增 `task_summary(tasks)`，一次遍历给出 `total`、`completed`、`pending`，并在 `completed` 不是布尔值时抛出 `ValueError`。

## 2. 用户故事

1. 作为调用方开发者，我希望调用一次 `task_summary(tasks)` 就拿到 `total`、`completed`、`pending`，以便直接展示进度，而不必自己写遍历。
2. 作为调用方开发者，当任务数据中的 `completed` 不是布尔值时，我希望立即收到 `ValueError`，以便回到数据源头修正，而不是拿到一个貌似正常的错误统计。
3. 作为维护者，我希望 `add_task`、`pending_titles` 的签名与行为完全不变，以便新功能不引入回归。

## 3. 范围

### 3.1 接口

- 新增公开函数 `task_summary(tasks: Iterable[Mapping[str, object]]) -> dict[str, int]`。
- 入参：可迭代的 `Mapping` 集合（元素为任务 dict），口径与 `pending_titles` 一致。
- 返回：新 `dict`，键精确为 `total`、`completed`、`pending`，值均为 `int`。

### 3.2 统计与校验规则

- `total`：遍历到的任务总数。
- `completed`：`completed` 为 `True` 的任务数。
- `pending`：`total - completed`，即 `completed` 为 `False` 或该键缺失的任务数。
- 恒满足 `total == completed + pending` 且 `total >= 0`。
- `completed` 键缺失视为 `False`，与 `pending_titles` 的 `task.get("completed", False)` 一致；不回填该键。
- 仅校验 `completed` 字段，判定以 `isinstance(value, bool)` 为准：`True` / `False` 合法；`1` / `0` 非法（`bool` 虽是 `int` 子类，此处不接受）。
- 取值非法时抛 `ValueError`，函数立即结束，不返回部分统计结果；异常消息文案不作强约束，但需能指出非法取值。
- 空输入返回 `{"total": 0, "completed": 0, "pending": 0}`。

### 3.3 行为约束

- 不修改入参列表与任务 dict；无副作用、无缓存、无全局状态；每次调用返回新 `dict`。
- 单次遍历，支持 list、生成器、`iter(...)`、`map(...)` 等单次可迭代对象。
- `src/` 运行时仅使用标准库（`typing` 仅用于类型标注）；测试仅使用 `pytest`。

### 3.4 产出位置（固定约定）

| 项 | 落点 |
| --- | --- |
| 实现 | `src/feature_B.py`，唯一公开函数 `task_summary` |
| 测试 | `tests/test_generated.py`，覆盖 AC1–AC11 |
| 不改动 | `src/todo.py`（`add_task`、`pending_titles` 签名与行为冻结），不做 re-export |

验证方式（无额外配置）：

```bash
python -m pytest tests -q
```

## 4. 验收标准

| 编号 | 验收项 | 判定方式 |
| --- | --- | --- |
| AC1 | 混合状态统计正确 | `[a:True, b:False, c:False]` → `{"total":3,"completed":1,"pending":2}` |
| AC2 | 空输入与返回值独立 | `[]` → 全零；修改首次返回值后再调用仍为全零，且非同一对象 |
| AC3 | 全完成 / 全未完成 | 分别满足 `pending == 0`（`completed == total`）与 `completed == 0`（`pending == total`） |
| AC4 | 缺失 `completed` 键 | 计入 `pending` 且不抛异常；调用后该任务 dict 仍不含 `completed` 键 |
| AC5 | 非布尔值报错 | `"yes"`、`None`、`1`、`0`、`2.5`、`""`、`[]`、`{}` 逐个独立断言抛 `ValueError`；另断言 `isinstance(True, int)` 为真但 `1` 仍被拒；非法值位于末尾时同样抛错 |
| AC6 | 报错时不返回结果 | 非法输入下调用方赋值变量保持 `None`，无部分统计 |
| AC7 | 不修改入参 | 调用前 `copy.deepcopy` → 调用 → 与原深拷贝相等；任务 dict 键集合与内容不变 |
| AC8 | 支持单次遍历迭代器 | 生成器、`iter(list)`、`map(...)` 统计正确；生成器调用后被耗尽，二次消费为空（再次调用返回全零） |
| AC9 | 与现有能力一致 | 合法数据集下 `task_summary(tasks)["pending"] == len(pending_titles(tasks))` |
| AC10 | 返回值形态 | `isinstance(result, dict)`；`set(result) == {"total","completed","pending"}`；每个值 `type(v) is int`（非 `isinstance`，以排除 `bool`）；`total == completed + pending` |
| AC11 | 无回归 | `tests/test_todo.py` 既有用例保持通过；集成用例：`add_task` 两条 → `0/2`，其中一条置 `True` → `1/1`，且 `pending` 与 `pending_titles` 长度对齐 |

## 5. 非目标

- 不引入第三方依赖，`src/` 仍只使用标准库（`typing` 仅用于类型标注）。
- 不新增 CLI、Web 接口、配置项或输出格式（打印、JSON 序列化由调用方自行处理）。
- 不做持久化：不读写文件、不接数据库、不维护全局状态。
- 不修改 `add_task`、`pending_titles` 的签名、行为与导入路径；不改动任务数据结构（仍为 dict）。
- 不新增其他统计维度或筛选能力（按标题去重、排序、关键词过滤、截止时间统计等均不做）。
- 不新增 `Task` 类、`dataclass` 或类型重构。
- 不约束 `ValueError` 的具体文案，不定义自定义异常类型。
- 不对非 `Mapping` 元素（缺 `.get`）做包装容错，其自然抛出的 `AttributeError` 属调用方违约。
- 不做性能优化、缓存或增量统计（示例级数据量，单次遍历即可）。
