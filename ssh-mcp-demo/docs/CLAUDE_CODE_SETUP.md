# Claude Code 中使用 SSH MCP 服务器

## 配置步骤

### 1. 安装依赖（推荐使用虚拟环境）

**方法 A: 使用虚拟环境（推荐，避免依赖冲突）**

运行自动化安装脚本:
```bash
cd ssh-mcp-demo
setup_venv.bat
```

这个脚本会:
- 创建独立的虚拟环境
- 安装所有依赖
- 显示 Claude Code 配置说明

**方法 B: 全局安装（可能有依赖冲突）**

如果你确定要全局安装:
```bash
cd ssh-mcp-demo
pip install -r requirements.txt
```

**注意**: 如果遇到依赖冲突错误，强烈建议使用方法 A（虚拟环境）。

### 2. 配置 SSH 连接信息

复制配置示例文件:
```bash
cp config.json.example config.json
```

编辑 `config.json`，填入你的服务器信息:
```json
{
  "host": "your.server.com",
  "port": 22,
  "username": "your_username",
  "password": "your_password"
}
```

或者使用 SSH 密钥（更安全）:
```json
{
  "host": "your.server.com",
  "port": 22,
  "username": "your_username",
  "key_file": "C:\\Users\\YourName\\.ssh\\id_rsa"
}
```

### 3. 配置 Claude Code

Claude Code 的 MCP 服务器配置文件位置:
- **Windows**: `%USERPROFILE%\.claude\claude_code_config.json`
- **macOS/Linux**: `~/.claude/claude_code_config.json`

打开或创建配置文件，添加 SSH MCP 服务器:

**如果使用虚拟环境（推荐）:**
```json
{
  "mcpServers": {
    "ssh-server": {
      "command": "d:\\code\\private\\playground\\ssh-mcp-demo\\venv\\Scripts\\python.exe",
      "args": [
        "d:\\code\\private\\playground\\ssh-mcp-demo\\server.py"
      ]
    }
  }
}
```

**如果全局安装:**
```json
{
  "mcpServers": {
    "ssh-server": {
      "command": "python",
      "args": [
        "d:\\code\\private\\playground\\ssh-mcp-demo\\server.py"
      ]
    }
  }
}
```

**注意**: 将路径替换为你的实际项目路径。使用虚拟环境时，必须使用虚拟环境中的 Python 解释器路径。

### 4. 重启 Claude Code

配置完成后，需要重启 Claude Code 或重新加载窗口:
- 按 `Ctrl+Shift+P` (或 `Cmd+Shift+P`)
- 输入 "Reload Window"
- 或直接重启 VSCode

### 5. 验证 MCP 服务器

重启后，Claude Code 应该会自动加载 MCP 服务器。你可以通过以下方式验证:

在 Claude Code 中询问:
```
列出可用的 MCP 工具
```

你应该能看到以下工具:
- `upload_file` - 上传文件到远程服务器
- `execute_remote_script` - 执行远程脚本
- `upload_and_execute` - 上传并执行
- `list_remote_directory` - 列出远程目录

## 使用示例

### 示例 1: 上传文件

```
帮我把 examples/my.py 上传到远程服务器的 /home/user/scripts 目录
```

### 示例 2: 执行远程脚本

```
执行远程服务器上的 /home/user/scripts/run.sh 脚本
```

### 示例 3: 上传并执行

```
上传 examples/my.py 到远程服务器的 /home/user/scripts，
然后执行 /home/user/scripts/run.sh
```

### 示例 4: 查看远程目录

```
列出远程服务器 /home/user/scripts 目录的内容
```

## 故障排除

### 问题 1: MCP 服务器未加载

**检查清单:**
1. 确认配置文件路径正确
2. 确认 Python 路径正确（可以用 `where python` 或 `which python` 查看）
3. 确认已安装依赖包
4. 查看 Claude Code 的输出面板是否有错误信息

### 问题 2: ModuleNotFoundError

如果看到 `No module named 'paramiko'` 或 `No module named 'fastmcp'` 错误:

```bash
pip install fastmcp paramiko
```

### 问题 3: 连接失败

**检查:**
1. `config.json` 中的服务器信息是否正确
2. 网络连接是否正常
3. SSH 端口是否开放
4. 防火墙设置

### 问题 4: 认证失败

**检查:**
1. 用户名和密码是否正确
2. SSH 密钥文件路径是否正确
3. 密钥文件权限（Linux/macOS 需要 600）

### 手动测试服务器

在命令行中直接运行服务器测试:

```bash
cd ssh-mcp-demo
python server.py
```

如果看到类似以下输出，说明服务器启动成功:
```
FastMCP server running...
```

## 配置文件完整示例

`claude_code_config.json` 完整示例（可以配置多个 MCP 服务器）:

```json
{
  "mcpServers": {
    "ssh-server": {
      "command": "python",
      "args": [
        "d:\\code\\private\\playground\\ssh-mcp-demo\\server.py"
      ]
    },
    "another-server": {
      "command": "node",
      "args": [
        "/path/to/another/server.js"
      ]
    }
  }
}
```

## 安全提示

1. **不要提交 `config.json`**: 该文件包含敏感信息，已在 `.gitignore` 中排除
2. **使用 SSH 密钥**: 相比密码，SSH 密钥更安全
3. **限制权限**: 确保配置文件只有你能读取
4. **定期更新**: 定期更新密码和密钥

## 高级配置

### 使用虚拟环境

如果你使用 Python 虚拟环境:

```json
{
  "mcpServers": {
    "ssh-server": {
      "command": "d:\\code\\private\\playground\\ssh-mcp-demo\\venv\\Scripts\\python.exe",
      "args": [
        "d:\\code\\private\\playground\\ssh-mcp-demo\\server.py"
      ]
    }
  }
}
```

### 添加环境变量

```json
{
  "mcpServers": {
    "ssh-server": {
      "command": "python",
      "args": [
        "d:\\code\\private\\playground\\ssh-mcp-demo\\server.py"
      ],
      "env": {
        "SSH_CONFIG_PATH": "d:\\code\\private\\playground\\ssh-mcp-demo\\config.json"
      }
    }
  }
}
```
