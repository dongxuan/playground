# MetaGPT TDD Demo

这是一个使用 **Python** 实现的“模拟 MetaGPT 多智能体 TDD 开发流程”示例。

## 功能概览

- 4 个 Agent：
  - 产品经理（Product Manager）
  - 架构师（Architect）
  - 代码开发（Developer）
  - 测试工程师（Tester）
- 按 TDD 流程执行：
  1. 需求分析
  2. 架构设计
  3. **先生成测试用例**
  4. 再生成实现代码
  5. 运行测试验证是否通过
- 支持自定义 coding rules（静态规则检查）：
  - 最大行长度
  - 禁止 `print`
  - 禁止 `from x import *`
  - 要求函数带类型注解

## 目录结构

```text
metagpt-demo/
├── README.md
├── run_demo.py
├── metagpt_demo/
│   ├── __init__.py
│   ├── agents.py
│   ├── coding_rules.py
│   └── tdd_workflow.py
└── tests/
    └── test_workflow.py
```

## 快速开始

```bash
cd metagpt-demo
python run_demo.py --requirement "实现两个整数相加函数" --output-dir ./generated_app
```

执行完成后会在 `generated_app/` 中看到：
- `src/tdd_target.py`（实现代码）
- `tests/test_tdd_target.py`（先生成的测试）

并在终端看到：
- 流程日志（各 agent 输出）
- 静态规则检查结果
- 单元测试是否通过

## 自定义规则示例

```bash
python run_demo.py \
  --requirement "实现两个整数相加函数" \
  --output-dir ./generated_app \
  --max-line-length 100 \
  --forbid-print \
  --require-type-hints
```

