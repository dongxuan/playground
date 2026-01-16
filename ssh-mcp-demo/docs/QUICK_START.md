# SSH MCP 快速开始指南

## 🚀 快速安装（推荐使用虚拟环境）

### 步骤 1: 运行自动化安装脚本

```bash
cd ssh-mcp-demo
setup_venv.bat
```

这个脚本会自动:
- ✅ 创建虚拟环境
- ✅ 安装所有依赖（避免版本冲突）
- ✅ 显示配置说明

### 步骤 2: 配置 SSH 连接

```bash
copy config.json.example config.json
```

然后编辑 `config.json`，填入你的服务器信息:
```json
{
  "host": "your.server.com",
  "port": 22,
  "username": "your_username",
  "password": "your_password"
}
```

### 步骤 3: 配置 Claude Code

编辑文件: `%USERPROFILE%\.claude\claude_code_config.json`

添加以下配置（**注意替换路径**）:
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

### 步骤 4: 重启 Claude Code

按 `Ctrl+Shift+P` → 输入 "Reload Window" → 回车

### 步骤 5: 测试

在 Claude Code 中输入:
```
列出可用的 SSH 工具
```

你应该看到:
- upload_file
- execute_remote_script
- upload_and_execute
- list_remote_directory

---

## 📝 使用示例

### 上传文件
```
把 examples/my.py 上传到远程服务器的 /home/user/scripts 目录
```

### 执行脚本
```
执行远程服务器上的 /home/user/scripts/run.sh
```

### 上传并执行
```
上传 examples/my.py 到 /home/user/scripts，然后执行 run.sh
```

---

## 🔧 验证安装

运行测试脚本:
```bash
test_server.bat
```

如果看到 "✓ All dependencies installed successfully"，说明安装成功！

---

## ❗ 常见问题

### Q: 为什么要用虚拟环境？
A: 避免依赖冲突。你遇到的 typer、httpx 版本冲突就是因为不同包需要不同版本。虚拟环境可以为这个项目创建独立的 Python 环境。

### Q: 如何激活虚拟环境？
A: 运行 `activate_venv.bat` 或 `venv\Scripts\activate.bat`

### Q: 配置文件在哪里？
A: Windows 系统在 `%USERPROFILE%\.claude\claude_code_config.json`

### Q: 如何查看错误日志？
A: 在 VSCode 中查看 Output 面板，选择 "Claude Code" 频道

---

## 📚 详细文档

- 完整配置指南: [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md)
- 使用说明: [README.md](README.md)
