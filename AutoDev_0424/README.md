# AutoDev_0424

一个面向已有 Python 项目的 MetaGPT 多智能体 TDD demo。

流程：Product Manager → Architect → QA（先写测试）→ Developer → pytest → 失败时 Code Review & Fix。`HumanReviewer` 的 `is_human=True`，每个 AI 阶段之后都会审阅；`--auto-approve` 仅用于无人值守演示。

## 运行

```bash
cd AutoDev_0424
source /Users/richard/metagpt-demo/.venv/bin/activate
python main.py ../user_project_A \
  "新增 task_summary(tasks)：返回 total、completed、pending 数量，并拒绝非布尔 completed 字段" \
  --auto-approve
```

MetaGPT 使用其标准配置 `~/.metagpt/config2.yaml`。运行后，目标项目会得到：

```text
docs/feature_B_prd.md
docs/feature_B_design.md
src/feature_B.py
tests/test_generated.py
```

流程 JSONL 与 pytest 完整输出保存在 `logs/`。

`tools/deepseek_pricing.py` 会把 DeepSeek 模型登记到 MetaGPT 的本地成本表，避免
`Model deepseek-flash not found in TOKEN_COSTS` 警告；它不读取或保存 API key。

## 自测

```bash
python -m pytest -q tests
```
