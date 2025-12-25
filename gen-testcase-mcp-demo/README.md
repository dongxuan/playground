# TestCase Generator MCP Server

一个基于 FastMCP 的自动测试用例生成服务，可以为代码文件或整个项目目录生成测试用例。

## 功能特性

- 🚀 支持单个文件或整个目录的测试用例生成
- 🔍 自动列出已生成的测试用例
- 💻 跨平台支持（Windows/Linux/macOS）
- 🧪 内置测试模式，方便验证功能

## 安装依赖

```bash
pip install mcp
```

## 配置自定义脚本

**重要：** 如果你想使用工作区中的自定义脚本，请配置脚本路径！

支持两种配置方式：

### 方式 1：配置文件（推荐）

编辑 `config.json`：
```json
{
  "script_path": "/home/user/my-workspace/scripts/gen_testcase.sh"
}
```

### 方式 2：环境变量

```bash
export TESTCASE_SCRIPT_PATH="/path/to/your/gen_testcase.sh"
```

详细配置指南请查看：
- **[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)** - 完整的配置指南
- **[config.example.json](config.example.json)** - 配置示例

## Remote SSH 场景

如果你使用 VSCode Remote SSH（Windows 连接 Linux 服务器），请查看：
- **[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)** - 远程工作区脚本配置（推荐）
- **[REMOTE_SSH_GUIDE.md](REMOTE_SSH_GUIDE.md)** - MCP 部署位置说明

## 使用方法

### 1. 测试模式（推荐先运行）

支持三种测试模式：

**Demo 模式（自动创建测试文件和目录）：**
```bash
python server.py --test
```
这将创建一个 test_demo 目录，生成示例文件，并验证所有功能是否正常。

**测试单个文件：**
```bash
python server.py --test path/to/your/file.py
python server.py --test example_code.py
```
直接为指定文件生成测试用例。

**测试整个目录：**
```bash
python server.py --test path/to/your/directory
python server.py --test ./src
```
为目录中的所有文件生成测试用例。

### 2. 作为 MCP Server 运行

```bash
python server.py
```

### 3. 配置到 Claude Desktop

在 Claude Desktop 的配置文件中添加：

**Windows** (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "testcase-generator": {
      "command": "python",
      "args": ["D:\\path\\to\\server.py"]
    }
  }
}
```

**macOS/Linux** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "testcase-generator": {
      "command": "python3",
      "args": ["/path/to/server.py"]
    }
  }
}
```

## 可用工具

### `generate_testcase(path: str)`

为指定的文件或文件夹生成测试用例。

**示例：**
- 单个文件：`generate_testcase("src/utils.py")`
- 整个目录：`generate_testcase("src/")`

### `list_generated_testcases(directory: str)`

列出指定目录下所有生成的测试用例文件（文件名包含 `-test`）。

**示例：**
- `list_generated_testcases("src/")`
- `list_generated_testcases(".")`  # 当前目录

## 工作原理

1. MCP Server 接收文件或目录路径
2. 调用对应平台的脚本（`gen_testcase.sh` 或 `gen_testcase.cmd`）
3. 脚本复制源文件并重命名为 `{filename}-test.{ext}` 格式
4. 返回生成结果给客户端

## 文件说明

- `server.py` - FastMCP 服务器主文件
- `gen_testcase.sh` - Linux/macOS 测试用例生成脚本
- `gen_testcase.cmd` - Windows 测试用例生成脚本

## 示例输出

### Demo 模式
```
=== TestCase Generator MCP Server - Test Mode ===

1. Checking script: gen_testcase.cmd
   [OK] Script exists

2. Running demo mode (no path provided)

3. Created test file: test_demo\example.py
   [OK] File created successfully

4. Testing single file generation: test_demo\example.py
   Result: Test cases generated successfully!
   [OK] Generated: test_demo\example-test.py

=== Test completed ===
```

### 测试指定文件
```
=== TestCase Generator MCP Server - Test Mode ===

1. Checking script: gen_testcase.cmd
   [OK] Script exists

2. Using provided path: example_code.py
   [INFO] Target is a file

3. Generating test case for file: example_code.py
   Result: Test cases generated successfully!
   [OK] Generated: example_code-test.py

4. Listing test cases in: .
   找到以下测试用例文件:
     - example_code-test.py

=== Test completed ===
```

## 注意事项

- 当前脚本为 Demo 版本，仅复制文件并重命名
- 生产环境中，`gen_testcase.sh` 应该实现真正的测试用例生成逻辑
- 测试文件会与源文件在同一目录下

## 扩展建议

要实现真正的测试用例生成，可以在脚本中：
- 使用 AST 解析分析代码结构
- 调用 AI 模型生成测试用例
- 集成测试框架模板（pytest, unittest, jest 等）
- 添加代码覆盖率分析


## 提示词
使用 gen-testcase-mcp-demo 这个mcp，给当前文件生成测试用例，生成的测试用例你也不需要进行检查，只需要告诉我，是否成功生成了对应的文件即可。

使用 gen-testcase-mcp-demo 这个mcp，给当前文件所在文件夹生成测试用例，生成的测试用例你也不需要进行检查，只需要告诉我，是否成功生成了对应的文件即可。
