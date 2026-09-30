# AutoDev_0424

AutoDev 是一个基于 MetaGPT 0.8.2 的多智能体 TDD 演示程序。它接收 Python 项目路径和一条需求，支持扩展已有项目，也支持确认后创建新项目，依次完成需求分析、技术设计、测试、实现和失败修复。

这个项目用于演示工作流，不是通用代码生成平台。运行前建议把目标项目提交到 Git，方便审阅和撤销 AI 产生的修改。

## 核心能力

- 分析已有项目，而不是假设固定目录结构。
- 先生成并运行测试，再生成实现代码并重新测试。
- 可以修改已有文件，也可以新增多个文件。
- 每个 AI 阶段后支持人工确认；拒绝后收集意见并重新执行当前 Action。
- pytest 失败时同时审查功能代码和测试，可在同一轮修复两者。
- 保存 PRD、技术设计、pytest 输出和完整工作流日志。

## 项目结构

```text
AutoDev_0424/
├── main.py                 # CLI 入口和参数解析
├── team.py                 # 工作流编排与修复循环
├── config.yaml             # AutoDev 工作流配置
├── requirements.txt        # Python 依赖
├── roles/                  # MetaGPT 角色
├── actions/                # PRD、设计、测试、开发和审查动作
├── tools/                  # 配置、文件、日志和静态检查工具
├── tests/                  # AutoDev 自身测试
├── logs/                   # 工作流和 pytest 日志，本地保留
└── workspace/              # 预留工作目录
```

`user_project_A` 是仓库根目录中的示例目标项目，不属于 AutoDev 源码。AutoDev 会直接读取和修改命令行指定的目标项目。

## 环境要求

- Python 3.11
- MetaGPT 0.8.2
- 可用的 OpenAI 兼容大模型 API
- 目标项目能够使用 pytest 运行测试

## 安装

如果已经安装 MetaGPT，可以直接使用现有虚拟环境。否则进入 AutoDev 目录后安装依赖：

```bash
cd AutoDev_0424
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

本机已有演示环境时，也可以使用：

```bash
source /Users/richard/metagpt-demo/.venv/bin/activate
```

## 配置概览

项目涉及两套配置，作用完全不同：

| 配置文件 | 用途 | 是否可以提交 Git |
| --- | --- | --- |
| `AutoDev_0424/config.yaml` | AutoDev 工作流参数 | 可以，不应包含密钥 |
| `~/.metagpt/config2.yaml` | MetaGPT 模型、服务地址和 API key | 不可以提交 |

## AutoDev 工作流配置

默认读取 [config.yaml](./config.yaml)。当前真正参与运行的配置是：

```yaml
tdd:
  max_fix_rounds: 2
```

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `tdd.max_fix_rounds` | 非负整数 | `2` | 实现后 pytest 失败时，Code Review & Fix 最多执行几轮 |

`0` 表示不进行自动审查修复；实现前和实现后的 pytest 仍会执行。人工拒绝导致的当前 Action 重做不占用自动修复轮数。

配置优先级如下：

```text
--max-fix-rounds 显式参数
        ↓ 未提供
--config 指向的 YAML 中 tdd.max_fix_rounds
        ↓ 字段缺失
内置默认值 2
```

程序启动时会打印最终生效值：

```text
AutoDev config: max_fix_rounds=2
```

当前 `config.yaml` 中的 `llm.provider` 只是说明性占位符。MetaGPT 不从这里读取模型配置。

当前 `tdd.test_command` 也尚未接入执行器。实际测试命令固定为当前 Python 解释器运行 `python -m pytest -q`，单次超时为 120 秒。

## 大模型配置

MetaGPT 从用户目录中的 `~/.metagpt/config2.yaml` 读取大模型配置。真实 API key 只能放在这个文件中，不要放进 AutoDev 仓库。

### 使用一个默认模型

下面是 DeepSeek OpenAI 兼容接口的示例。请替换 API key，并确认模型 ID 是供应商当前支持的名称。

```yaml
llm:
  api_type: openai
  base_url: https://api.deepseek.com
  api_key: "<YOUR_DEEPSEEK_API_KEY>"
  model: deepseek-chat
  temperature: 0.1
  timeout: 120
```

默认情况下，Product Manager、Architect、QA Engineer 和 Developer 都使用这个顶层 `llm` 配置。

### 为不同角色配置不同模型

先在 `~/.metagpt/config2.yaml` 的 `models` 下定义模型别名：

```yaml
llm:
  api_type: openai
  base_url: https://api.deepseek.com
  api_key: "<YOUR_DEEPSEEK_API_KEY>"
  model: deepseek-chat

models:
  general_model:
    api_type: openai
    base_url: https://api.deepseek.com
    api_key: "<YOUR_DEEPSEEK_API_KEY>"
    model: deepseek-chat
    temperature: 0.2
    timeout: 120

  reasoning_model:
    api_type: openai
    base_url: https://api.deepseek.com
    api_key: "<YOUR_DEEPSEEK_API_KEY>"
    model: deepseek-reasoner
    temperature: 0.1
    timeout: 180
```

然后在 `roles/` 中通过 Action 的 `llm_name_or_type` 选择别名：

```python
# Product Manager
actions=[WritePRD(llm_name_or_type="general_model")]

# Architect
actions=[WriteDesign(llm_name_or_type="reasoning_model")]

# QA Engineer
actions=[WriteTest(llm_name_or_type="general_model")]

# Developer：实现和修复可以使用不同模型
actions=[
    WriteCode(llm_name_or_type="reasoning_model"),
    CodeReview(llm_name_or_type="reasoning_model"),
]
```

`HumanReviewer` 通过终端输入进行人工确认，不调用大模型。使用 `--auto-approve` 时，它会自动批准所有阶段。

模型别名必须与 `models` 下的键完全一致。MetaGPT 0.8.2 遇到未知别名时可能回退到默认 `llm`，因此修改后应检查实际调用日志。

### API key 安全

限制 MetaGPT 配置文件的访问权限：

```bash
chmod 600 ~/.metagpt/config2.yaml
```

不要把真实 API key 写入 README、源码、项目内 `.env` 或可提交日志。代码仓库中只应出现 `general_model` 这类不含密钥的模型别名。

## 命令行参数

查看内置帮助：

```bash
python main.py --help
```

命令格式：

```text
python main.py [选项] PROJECT REQUIREMENT
```

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `PROJECT` | 是 | 无 | Python 项目路径，可用相对或绝对路径；不存在时询问是否创建 |
| `REQUIREMENT` | 是 | 无 | 非空需求描述，建议用引号包住完整描述 |
| `--auto-approve` | 否 | 关闭 | 自动批准各 Action 产物；新项目创建仍需单独确认 |
| `--config PATH` | 否 | `AutoDev_0424/config.yaml` | 指定另一份 AutoDev 工作流配置 |
| `--max-fix-rounds N` | 否 | 读取配置 | 临时覆盖最大自动修复轮数，必须是非负整数 |
| `-h`、`--help` | 否 | 无 | 显示帮助并退出 |

已有目录直接进入工作流；不存在的目录在明确输入 `y` 或 `yes` 后创建。若路径指向普通文件则报错。产物直接写入目标项目，不会复制到 `workspace/`。

## 运行示例

### 使用示例项目并保留人工确认

```bash
cd AutoDev_0424
source /Users/richard/metagpt-demo/.venv/bin/activate

python main.py ../user_project_A \
  "新增 task_summary(tasks)：返回 total、completed、pending 数量，并拒绝非布尔 completed 字段"
```

每个阶段完成后会出现类似提示：

```text
[Human Reviewer] PRD 已产出 ...。批准继续？[Y/n]
```

直接回车、输入 `y` 或 `yes` 表示批准。输入 `n` 或 `no` 后，会询问修改意见：

```text
请输入修改意见（可留空，回车后重做当前步骤）：
```

提交意见后，只重新执行当前 Action；留空也会重新执行。此前的意见和上一版产物会提供给模型，批准后的最新内容才传给下游阶段。无效选项会重新询问，按 Ctrl+C 可终止。

PRD、技术设计、测试、实现和审查修复均支持此交互。产物在确认前已经写入目标项目；拒绝不会回滚文件，重做会基于当前文件更新，模型未再列出的旧文件也不会自动删除。

### 从需求创建新项目

在 AutoDev 目录中执行，指定一个不存在的路径：

```bash
python main.py ../new_calculator \
  "创建一个 Python 计算器，提供 add(a, b) 和 divide(a, b)，除数为零时抛出 ValueError；使用 pytest 验证。"
```

程序显示完整路径并询问 `[y/N]`。输入 `y` 或 `yes` 创建目录（含缺失的父目录），然后按 PRD → Design → 测试 → 实现前测试 → 实现 → 实现后测试 → 失败修复的顺序运行。

输入 `n`、直接回车或没有交互输入时取消，不创建目录，也不启动 AI 工作流。即使设置 `--auto-approve`，新项目创建也需要这次确认；确认后各阶段可自动批准。

### 无人值守演示

```bash
python main.py ../user_project_A \
  "新增 task_summary(tasks)：返回 total、completed、pending 数量" \
  --auto-approve
```

### 覆盖最大修复轮数

```bash
python main.py ../user_project_A "新增任务导出功能" \
  --max-fix-rounds 5 \
  --auto-approve
```

### 使用另一份工作流配置

```bash
python main.py ../user_project_A "新增任务搜索功能" \
  --config ./config.demo.yaml \
  --auto-approve
```

## 工作流

| 顺序 | 角色或 Action | 输入 | 主要产出 |
| --- | --- | --- | --- |
| 1 | Product Manager / `WritePRD` | 新需求、项目快照 | PRD |
| 2 | Human Reviewer | PRD 路径 | 批准或拒绝 |
| 3 | Architect / `WriteDesign` | PRD、项目快照 | 技术设计和文件方案 |
| 4 | Human Reviewer | Design 路径 | 批准或拒绝 |
| 5 | QA Engineer / `WriteTest` | PRD、Design、项目快照 | 一个或多个 pytest 文件 |
| 6 | Human Reviewer | 测试文件路径 | 批准或拒绝 |
| 7 | `RunTests`（实现前） | QA 测试、目标项目 | TDD Red 阶段结果与日志 |
| 8 | Developer / `WriteCode` | Design、测试、项目快照 | 一个或多个产品代码文件 |
| 9 | Human Reviewer | 代码文件路径 | 批准或给意见重做 |
| 10 | `StaticCheck` | 目标项目 Python 文件 | Python 语法检查结果 |
| 11 | `RunTests`（实现后） | 目标项目 | pytest 结果和完整日志 |
| 12 | `CodeReview`（失败时） | 原始需求、PRD、Design、项目、pytest 输出 | 代码修复、测试修复、联合修复或不修改 |
| 13 | Human Reviewer → `RunTests` | 修复产物 | 批准后重新测试，失败时进入下一轮 |

QA 和 Developer 都返回结构化的多文件变更集。它们可以修改已有文件，也可以新增多个文件，不再固定写入 `src/feature_B.py` 或 `tests/test_generated.py`。

实现前测试的失败是正常的 TDD 反馈，会保存日志并继续生成实现；通过也会记录，不会人为制造失败。自动修复只针对实现后失败的测试。

Code Review 的 prompt 要求每次同时检查产品代码和测试（断言、数据、导入、fixture），依据原始需求、PRD 验收标准和技术设计决定修改范围。

| 审查决策 | 含义 |
| --- | --- |
| `CODE_FIX` | 只修复功能代码 |
| `TEST_FIX` | 只修复错误测试 |
| `CODE_AND_TEST_FIX` | 同一轮同时修复功能代码和测试 |
| `NO_CHANGES` | 当前审查没有新增修改 |

修改测试需有需求、验收标准或测试本身缺陷的依据。不得删除正确断言或跳过失败测试来制造通过；这些语义约束依赖模型执行和人工审阅，并非程序能自动证明。

`max_fix_rounds` 表示最大修复次数，不保证一定执行这么多轮。测试通过、审查无修改或审查调用失败时，循环都会提前结束。

## 生成产物

### 写入目标项目

PRD 和 Design 写入目标项目的 `docs/`：

```text
<目标项目>/
├── docs/
│   ├── <需求简称>_prd.md
│   └── <需求简称>_design.md
├── <一个或多个测试文件>
└── <一个或多个产品代码文件>
```

需求简称优先从函数名、反引号标识符、snake_case 或英文关键词中提取。

例如需求包含 `task_summary(tasks)` 时，会生成：

```text
docs/task_summary_prd.md
docs/task_summary_design.md
```

无法可靠提取简称时，使用同一次生成的系统时间：

```text
docs/feature_20260930_123456_prd.md
docs/feature_20260930_123456_design.md
```

测试和产品代码的路径由 Architect 根据现有项目决定，不保证位于 `tests/` 或 `src/` 的某个固定文件。

### 写入 AutoDev 日志目录

运行日志保存在 `AutoDev_0424/logs/`：

```text
logs/
├── workflow_YYYYMMDD_HHMMSS.jsonl
└── pytest_YYYYMMDD_HHMMSS_microseconds.log
```

`workflow_*.jsonl` 按顺序记录角色、状态、产物路径、需求简称、修复轮数、人工反馈和重做事件。反馈也会进入本地日志。

`pytest_*.log` 保存实现前、实现后和每轮修复后测试的标准输出和错误输出；可通过工作流事件区分阶段。控制台结束时打印最终 pytest 输出和日志路径。

这些运行日志可能包含需求、路径或部分项目内容，因此 `logs/*` 已被 `.gitignore` 排除，只保留 `.gitkeep`。

## 查看测试结果

运行结束时查看控制台：

```text
... pytest output ...
pytest log: /absolute/path/to/AutoDev_0424/logs/pytest_....log
```

也可以查看最新日志：

```bash
ls -lt logs/pytest_*.log | head
tail -n 100 logs/pytest_*.log
```

最终 pytest 返回码为 `0` 时，AutoDev 进程返回 `0`；测试仍失败时返回 `1`。

## 运行 AutoDev 自身测试

以下命令只测试 AutoDev 本身，不会调用大模型，也不会修改 `user_project_A`：

```bash
cd AutoDev_0424
python -m pytest -q
```

测试覆盖配置优先级、文档命名、多文件变更、人工反馈重做、新项目确认和联合修复。集成测试模拟模型响应与终端输入，在临时项目中真实执行 pytest 验证失败到通过的过程。

## 安全与限制

- AutoDev 只允许将 AI 返回的文件写入目标项目内部，并拒绝绝对路径和 `..` 路径穿越。
- AI 可以按设计覆盖目标项目中的已有文件，因此应先提交或备份目标项目。
- 项目快照默认最多向模型提供约 24,000 个字符，大型项目可能被截断。
- 静态检查只执行 Python 编译检查，不包含 Ruff、Mypy 或安全扫描。
- 自动测试固定使用 pytest，当前不能通过 `config.yaml` 更换测试框架或命令。
- `--auto-approve` 会跳过人工把关，只适合可恢复的演示环境。

## 常见问题

### `max_fix_rounds` 看起来没有执行指定次数

它是自动修复的最大次数。测试通过、审查无修改且测试仍失败，或审查异常时会提前结束。人工拒绝只重做当前 Action，不会直接终止工作流，也不消耗下一轮自动修复额度。

启动时检查下面这行，确认实际生效值：

```text
AutoDev config: max_fix_rounds=N
```

### `LLM returned an empty response twice`

模型连续两次返回空内容。检查 `~/.metagpt/config2.yaml` 中的 API key、`base_url`、模型 ID 和超时设置，并确认供应商接口可用。

### `Model ... not found in TOKEN_COSTS`

这是 MetaGPT 本地成本表缺少模型价格时的警告，不等同于请求失败。`tools/deepseek_pricing.py` 已登记演示使用的部分 DeepSeek 模型；其他自定义模型仍可能显示该警告。

### 在哪里看每个角色做了什么

查看 `logs/workflow_*.jsonl`。每行是一个 JSON 事件，包含执行顺序、UTC 时间、角色、状态和详情。

### 为什么没有生成固定的 `feature_B.py`

这是预期行为。Architect 会先分析目标项目，再决定修改已有代码还是新增文件；QA、Developer 和 Code Review 都遵循该文件方案。
