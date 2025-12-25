# 配置指南 - 远程工作区脚本

## 需求场景

你使用 VSCode + Roo Code 远程连接到 Linux 服务器工作区，希望：
- MCP server 调用工作区中的自定义 `gen_testcase.sh` 脚本
- 脚本路径可以灵活配置
- 不管 MCP 运行在哪里，都调用远程 Linux 工作区的脚本

## 配置方式

支持两种配置方式（按优先级排序）：

### 方式 1：环境变量（推荐用于临时测试）

设置环境变量 `TESTCASE_SCRIPT_PATH` 指向你的脚本：

**Linux/macOS:**
```bash
export TESTCASE_SCRIPT_PATH="/home/user/workspace/scripts/gen_testcase.sh"
python server.py --check-env
```

**Windows PowerShell:**
```powershell
$env:TESTCASE_SCRIPT_PATH = "C:\workspace\scripts\gen_testcase.sh"
python server.py --check-env
```

### 方式 2：配置文件（推荐用于生产环境）

编辑 `config.json` 文件：

```json
{
  "script_path": "/home/user/workspace/my-project/gen_testcase.sh",
  "description": "指向你工作区中的实际脚本路径"
}
```

**注意：**
- 使用绝对路径
- 支持 `~` 符号（会自动展开为用户主目录）
- 路径必须存在，否则会回退到默认脚本

## 针对 Remote SSH 的配置步骤

### 场景：VSCode (Windows) → SSH → Linux 服务器工作区

假设你的工作区结构：
```
/home/user/my-workspace/
├── src/
├── scripts/
│   └── gen_testcase.sh    # 你的自定义脚本
└── .vscode/
```

### 步骤 1: 上传 MCP Server 到 Linux 服务器

```bash
# SSH 到你的 Linux 服务器
ssh user@your-server

# 创建 MCP 目录
mkdir -p ~/.config/mcp-servers/testcase-generator
cd ~/.config/mcp-servers/testcase-generator

# 上传文件（使用 scp 或直接创建）
# 需要的文件：server.py, config.json
```

### 步骤 2: 配置脚本路径

编辑 `~/.config/mcp-servers/testcase-generator/config.json`：

```json
{
  "script_path": "/home/user/my-workspace/scripts/gen_testcase.sh"
}
```

或者使用相对于用户主目录的路径：

```json
{
  "script_path": "~/my-workspace/scripts/gen_testcase.sh"
}
```

### 步骤 3: 验证配置

```bash
cd ~/.config/mcp-servers/testcase-generator
python3 server.py --check-env
```

应该看到：
```
=== Environment Check ===

Operating System: Linux
Configuration:
  config.json script_path: /home/user/my-workspace/scripts/gen_testcase.sh

Script to use: /home/user/my-workspace/scripts/gen_testcase.sh
Script exists: True
Script extension: .sh
```

### 步骤 4: 配置 Roo Code

在 Linux 服务器上配置 Roo Code 的 MCP 设置：

通常位置：`~/.config/roo-code/settings.json` 或类似位置

```json
{
  "mcpServers": {
    "testcase-generator": {
      "command": "python3",
      "args": ["/home/user/.config/mcp-servers/testcase-generator/server.py"]
    }
  }
}
```

### 步骤 5: 测试

```bash
# 在工作区测试
cd ~/my-workspace
python3 ~/.config/mcp-servers/testcase-generator/server.py --test src/example.py
```

## 脚本路径解析优先级

1. **环境变量** `TESTCASE_SCRIPT_PATH`（最高优先级）
2. **配置文件** `config.json` 中的 `script_path`
3. **默认路径**（最低优先级）
   - Windows: `gen_testcase.cmd`
   - Linux: `gen_testcase.sh`

## 示例配置

### 示例 1: 工作区脚本

```json
{
  "script_path": "~/projects/my-app/tools/gen_testcase.sh"
}
```

### 示例 2: 系统级脚本

```json
{
  "script_path": "/usr/local/bin/gen_testcase.sh"
}
```

### 示例 3: 项目特定脚本

```json
{
  "script_path": "/home/user/workspace/current-project/scripts/custom_test_gen.sh"
}
```

## 常见问题

### Q1: 配置了路径但还是用默认脚本？

**A:** 检查：
1. 路径是否正确且文件存在
2. 运行 `--check-env` 查看实际使用的路径
3. 检查是否有警告信息

### Q2: 权限问题

**A:** 确保脚本有执行权限：
```bash
chmod +x /path/to/your/gen_testcase.sh
```

### Q3: Windows 上执行 .sh 脚本？

**A:**
- 确保安装了 Git Bash 或 WSL
- Bash 必须在 PATH 中
- 或者直接让 MCP 运行在 Linux 服务器上（推荐）

### Q4: 如何在不同项目间切换？

**A:** 两种方式：
1. 每个项目配置独立的 MCP server
2. 使用环境变量，每次切换项目时重新设置

### Q5: 相对路径支持吗？

**A:** 不推荐使用相对路径，因为工作目录可能变化。如果必须使用，相对于 MCP server 的运行目录。

## 调试技巧

### 1. 检查配置是否生效

```bash
python server.py --check-env
```

### 2. 查看详细错误

查看 stderr 输出，所有警告都会输出到标准错误流。

### 3. 测试脚本独立运行

```bash
bash /path/to/your/gen_testcase.sh /path/to/test/file.py
```

### 4. 验证路径

```bash
# Linux
ls -la /path/to/your/gen_testcase.sh

# 检查权限
stat /path/to/your/gen_testcase.sh
```

## 最佳实践

1. **使用绝对路径** - 避免路径混淆
2. **版本控制配置** - 将 `config.json` 加入 `.gitignore`，提供 `config.example.json`
3. **文档化脚本位置** - 在项目 README 中说明脚本位置
4. **测试脚本** - 独立测试脚本后再集成到 MCP
5. **MCP 在服务器运行** - 对于 Remote SSH 场景，始终让 MCP 运行在服务器上
