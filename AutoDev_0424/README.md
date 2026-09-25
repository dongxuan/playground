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
docs/feature_B_prd.md       # 固定：PRD
docs/feature_B_design.md    # 固定：技术设计与文件方案
<一个或多个测试文件>        # QA 根据现有测试布局决定新增或修改
<一个或多个产品代码文件>    # Developer 根据设计决定新增或修改
```

代码与测试文件不再固定为 `src/feature_B.py` 和 `tests/test_generated.py`。架构师会先分析
项目职责与目录结构，再明确文件方案；QA、Developer 和 Code Review 使用结构化多文件变更集，
一次运行可以安全地修改原文件并新增多个文件。所有写入都限制在目标项目目录内。

流程 JSONL 与 pytest 完整输出保存在 `logs/`。运行日志仅保留在本地并被 `.gitignore` 排除，
避免完整 prompt 或项目源码被误提交。

`tools/deepseek_pricing.py` 会把 DeepSeek 模型登记到 MetaGPT 的本地成本表，避免
`Model deepseek-flash not found in TOKEN_COSTS` 警告；它不读取或保存 API key。

## 为不同角色配置不同的大模型

默认情况下，所有角色都使用 `~/.metagpt/config2.yaml` 顶层 `llm` 中配置的模型。
MetaGPT 0.8.2 也支持在 `models` 中定义多个模型别名，再通过 Action 的
`llm_name_or_type` 为不同阶段选择模型。

### 1. 在 MetaGPT 用户配置中定义模型

编辑 `~/.metagpt/config2.yaml`。下面以 DeepSeek 的 OpenAI 兼容接口为例；请把
`<YOUR_DEEPSEEK_API_KEY>` 和模型 ID 替换成自己的配置：

```yaml
# 没有单独指定模型时使用的默认配置
llm:
  api_type: openai
  base_url: https://api.deepseek.com
  api_key: "<YOUR_DEEPSEEK_API_KEY>"
  model: deepseek-chat
  timeout: 120

# 名称可自定义，代码通过这些别名选择模型
models:
  pm_model:
    api_type: openai
    base_url: https://api.deepseek.com
    api_key: "<YOUR_DEEPSEEK_API_KEY>"
    model: deepseek-chat
    temperature: 0.3
    timeout: 120

  architect_model:
    api_type: openai
    base_url: https://api.deepseek.com
    api_key: "<YOUR_DEEPSEEK_API_KEY>"
    model: deepseek-reasoner
    temperature: 0.1
    timeout: 180

  qa_model:
    api_type: openai
    base_url: https://api.deepseek.com
    api_key: "<YOUR_DEEPSEEK_API_KEY>"
    model: deepseek-chat
    temperature: 0.1
    timeout: 120

  developer_model:
    api_type: openai
    base_url: https://api.deepseek.com
    api_key: "<YOUR_DEEPSEEK_API_KEY>"
    model: deepseek-reasoner
    temperature: 0.1
    timeout: 180

  reviewer_model:
    api_type: openai
    base_url: https://api.deepseek.com
    api_key: "<YOUR_DEEPSEEK_API_KEY>"
    model: deepseek-reasoner
    temperature: 0
    timeout: 180
```

同一个供应商可以复用同一把 API key。`model` 必须是供应商实际支持的模型 ID；
如果使用其他 OpenAI 兼容服务，只需相应修改 `base_url`、`api_key` 和 `model`。

### 2. 在角色的 Action 上选择模型

在 `roles/` 中创建 Action 时传入对应的模型别名。例如产品经理使用：

```python
actions=[WritePRD(llm_name_or_type="pm_model")]
```

其他角色可按相同方式配置：

```python
# Architect
actions=[WriteDesign(llm_name_or_type="architect_model")]

# QA Engineer
actions=[WriteTest(llm_name_or_type="qa_model")]

# Developer：实现和审查可以使用不同模型
actions=[
    WriteCode(llm_name_or_type="developer_model"),
    CodeReview(llm_name_or_type="reviewer_model"),
]
```

模型选择与当前工作流的对应关系如下：

| 阶段 | Action | 配置别名 |
| --- | --- | --- |
| 产品需求分析 | `WritePRD` | `pm_model` |
| 技术设计 | `WriteDesign` | `architect_model` |
| 测试设计 | `WriteTest` | `qa_model` |
| 代码实现 | `WriteCode` | `developer_model` |
| 失败后的审查与修复 | `CodeReview` | `reviewer_model` |

`HumanReviewer` 通过终端交互进行人工确认，使用 `--auto-approve` 时自动确认，因此不需要
配置 AI 模型。模型别名必须与 `config2.yaml` 中 `models` 下的键完全一致；别名拼写错误时，
MetaGPT 0.8.2 可能回退到默认 `llm`。

### API key 安全

真实 API key 只应保存在项目仓库之外的 `~/.metagpt/config2.yaml` 中，不要写入本项目的
README、源码、`.env` 或日志。建议限制该文件的访问权限：

```bash
chmod 600 ~/.metagpt/config2.yaml
```

项目源码中只保存 `pm_model`、`developer_model` 等不含密钥的模型别名，可以正常提交到 Git。

## 自测

```bash
python -m pytest -q tests
```
