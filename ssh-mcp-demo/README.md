# SSH MCP Server

一个基于 FastMCP 和 Paramiko 的 SSH 文件传输和远程脚本执行服务器。

## 功能特性

- 📤 通过 SSH/SFTP 上传本地文件到远程服务器
- 🚀 执行远程服务器上的脚本
- 🔄 组合操作：上传文件并执行脚本
- 📁 列出远程目录内容
- 🔐 支持密码和密钥文件认证

## 安装

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置 SSH 连接信息:
```bash
cp config.json.example config.json
```

编辑 `config.json` 文件，填入你的服务器信息:
```json
{
  "host": "your.server.com",
  "port": 22,
  "username": "your_username",
  "password": "your_password",
  "key_file": "/path/to/your/private/key",
  "default_remote_dir": "/home/user/scripts",
  "default_script": "run.sh"
}
```

**配置说明:**
- `password` 和 `key_file` 可以二选一，如果使用密钥认证，请确保密钥文件路径正确
- `default_remote_dir`: 默认的远程上传目录，如果调用工具时不指定目录，将使用此默认值
- `default_script`: 默认的执行脚本名称，如果不指定脚本路径，将使用 `default_remote_dir/default_script`

## 使用方法

### 启动 MCP 服务器

```bash
python server.py
```

或者直接运行:
```bash
mcp run server.py
```

### 配置到 Claude Desktop

在 Claude Desktop 的配置文件中添加:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ssh-server": {
      "command": "python",
      "args": ["D:\\path\\to\\ssh-mcp-demo\\server.py"]
    }
  }
}
```

## 可用工具

### 1. upload_file
上传本地文件到远程服务器

**参数:**
- `local_file`: 本地文件路径（必需）
- `remote_dir`: 远程目录路径（可选，使用 config.json 的 default_remote_dir）
- `host`: SSH 主机 (可选，使用 config.json)
- `port`: SSH 端口 (可选，默认 22)
- `username`: SSH 用户名 (可选，使用 config.json)
- `password`: SSH 密码 (可选)
- `key_file`: SSH 私钥文件路径 (可选)

**示例:**
```
上传 my.py 到远程服务器（使用默认目录）
上传 my.py 到远程服务器的 /home/user/scripts 目录
```

### 2. execute_remote_script
执行远程服务器上的脚本

**参数:**
- `script_path`: 远程脚本路径（可选，使用 config.json 的 default_remote_dir/default_script）
- `args`: 脚本参数 (可选)
- 其他 SSH 连接参数同上

**示例:**
```
执行远程服务器上的默认脚本
执行远程服务器上的 /home/user/scripts/run.sh 脚本
```

### 3. upload_and_execute
上传文件并执行脚本的组合操作

**参数:**
- `local_file`: 本地文件路径（必需）
- `remote_dir`: 远程目录路径（可选，使用 config.json 的 default_remote_dir）
- `script_path`: 要执行的脚本路径（可选，使用 config.json 的 default_remote_dir/default_script）
- `script_args`: 脚本参数 (可选)
- 其他 SSH 连接参数同上

**示例:**
```
上传 my.py 并执行默认脚本（使用 config.json 的默认配置）
上传 my.py 到 /home/user/scripts，然后执行 /home/user/scripts/run.sh
```

### 4. list_remote_directory
列出远程目录内容

**参数:**
- `remote_dir`: 远程目录路径
- 其他 SSH 连接参数同上

**示例:**
```
列出远程服务器 /home/user/scripts 目录的内容
```

## 使用示例

### 在 Claude Desktop 中使用

1. **上传文件（使用默认目录）:**
```
帮我把本地的 test.py 上传到远程服务器
```

2. **上传文件（指定目录）:**
```
帮我把本地的 test.py 文件上传到远程服务器的 /home/user/scripts 目录
```

3. **执行默认脚本:**
```
执行远程服务器上的默认脚本
```

4. **执行指定脚本:**
```
执行远程服务器上的 /home/user/scripts/run.sh 脚本
```

5. **组合操作（使用默认配置）:**
```
上传本地的 my.py 并执行
```

6. **组合操作（指定路径）:**
```
上传本地的 my.py 到远程服务器的 /home/user/scripts，然后执行 run.sh 脚本
```

7. **查看远程目录:**
```
列出远程服务器 /home/user/scripts 目录的文件
```

## 安全建议

1. 不要将 `config.json` 提交到版本控制系统
2. 建议使用 SSH 密钥认证而不是密码
3. 确保远程服务器的 SSH 配置安全
4. 定期更新密钥和密码

## 故障排除

### 连接失败
- 检查 `config.json` 中的主机、端口、用户名是否正确
- 确认网络连接正常
- 验证 SSH 服务是否运行

### 认证失败
- 检查密码或密钥文件路径是否正确
- 确认用户有相应的权限

### 文件上传失败
- 确认远程目录存在或有创建权限
- 检查磁盘空间是否充足

### 脚本执行失败
- 确认脚本路径正确
- 检查脚本是否有执行权限 (`chmod +x script.sh`)
- 查看脚本执行的错误输出

## 许可证

MIT License
