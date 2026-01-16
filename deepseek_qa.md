我来为你创建一个使用 FastMCP 实现的 SSH 远程命令执行 MCP Server：

1. 安装依赖

首先创建 requirements.txt：

```txt
fastmcp>=1.0.0
paramiko>=3.4.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

2. 主要实现代码

创建 ssh_mcp_server.py：

```python
"""
SSH Remote Command Execution MCP Server
使用 FastMCP 实现远程 SSH 命令执行
"""

import os
import sys
import socket
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from contextlib import contextmanager
from pathlib import Path

import paramiko
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 定义数据模型
class SSHConnection(BaseModel):
  """SSH 连接配置"""
  hostname: str = Field(..., description="服务器主机名或IP地址")
  port: int = Field(22, description="SSH端口，默认为22")
  username: str = Field(..., description="用户名")
  password: Optional[str] = Field(None, description="密码（如果使用密钥认证则不需要）")
  key_filename: Optional[str] = Field(None, description="私钥文件路径")
  timeout: int = Field(10, description="连接超时时间（秒）")

class CommandRequest(BaseModel):
  """命令执行请求"""
  connection: SSHConnection
  command: str = Field(..., description="要执行的命令")
  sudo: bool = Field(False, description="是否使用sudo执行")
  sudo_password: Optional[str] = Field(None, description="sudo密码（如果需要）")
  timeout: int = Field(30, description="命令执行超时时间（秒）")

class CommandResult(BaseModel):
  """命令执行结果"""
  success: bool = Field(..., description="是否执行成功")
  stdout: str = Field("", description="标准输出")
  stderr: str = Field("", description="标准错误")
  exit_code: int = Field(..., description="退出码")
  error_message: Optional[str] = Field(None, description="错误信息")

@dataclass
class SSHManager:
  """SSH 连接管理器"""

  @contextmanager
  def get_connection(self, conn_config: SSHConnection):
      """获取SSH连接（上下文管理器）"""
      ssh = None
      try:
          ssh = paramiko.SSHClient()
          ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

          # 构建连接参数
          connect_kwargs = {
              'hostname': conn_config.hostname,
              'port': conn_config.port,
              'username': conn_config.username,
              'timeout': conn_config.timeout,
              'allow_agent': True,
              'look_for_keys': True,
          }

          # 根据认证方式添加参数
          if conn_config.password:
              connect_kwargs['password'] = conn_config.password
          elif conn_config.key_filename:
              connect_kwargs['key_filename'] = conn_config.key_filename

          ssh.connect(**connect_kwargs)
          yield ssh
      except paramiko.AuthenticationException as e:
          raise Exception(f"SSH认证失败: {str(e)}")
      except paramiko.SSHException as e:
          raise Exception(f"SSH连接错误: {str(e)}")
      except socket.timeout as e:
          raise Exception(f"连接超时: {str(e)}")
      except Exception as e:
          raise Exception(f"SSH连接异常: {str(e)}")
      finally:
          if ssh:
              ssh.close()

class SSHServer(FastMCP):
  """SSH MCP 服务器"""

  def __init__(self, name: str = "ssh-server"):
      super().__init__(name=name)
      self.ssh_manager = SSHManager()

      # 注册工具
      self.register_tools()

      # 预加载的服务器配置（可选）
      self.server_configs: Dict[str, SSHConnection] = self._load_server_configs()

  def _load_server_configs(self) -> Dict[str, SSHConnection]:
      """从环境变量加载服务器配置"""
      configs = {}

      # 示例：从环境变量加载配置
      # 环境变量格式：SSH_SERVERS=server1:host1:user1:password1,server2:host2:user2:password2
      servers_str = os.getenv("SSH_SERVERS", "")
      if servers_str:
          for server_def in servers_str.split(','):
              parts = server_def.split(':')
              if len(parts) >= 3:
                  name = parts[0]
                  hostname = parts[1]
                  username = parts[2]
                  password = parts[3] if len(parts) > 3 else None

                  configs[name] = SSHConnection(
                      hostname=hostname,
                      username=username,
                      password=password
                  )

      return configs

  def register_tools(self):
      """注册MCP工具"""

      @self.tool()
      async def execute_remote_command(
          hostname: str = Field(..., description="服务器主机名或IP地址"),
          username: str = Field(..., description="用户名"),
          command: str = Field(..., description="要执行的命令"),
          port: int = Field(22, description="SSH端口"),
          password: Optional[str] = Field(None, description="密码（可选）"),
          key_path: Optional[str] = Field(None, description="私钥文件路径（可选）"),
          sudo: bool = Field(False, description="是否使用sudo"),
          sudo_password: Optional[str] = Field(None, description="sudo密码（如果需要）"),
          timeout: int = Field(30, description="命令执行超时时间")
      ) -> CommandResult:
          """
          在远程服务器上执行命令

          此工具允许通过SSH连接到远程服务器并执行指定的命令。
          支持密码认证和密钥认证两种方式。
          """
          try:
              # 构建连接配置
              conn_config = SSHConnection(
                  hostname=hostname,
                  port=port,
                  username=username,
                  password=password,
                  key_filename=key_path,
                  timeout=10
              )

              return await self._execute_command(
                  conn_config,
                  command,
                  sudo,
                  sudo_password,
                  timeout
              )

          except Exception as e:
              return CommandResult(
                  success=False,
                  stdout="",
                  stderr="",
                  exit_code=-1,
                  error_message=f"执行失败: {str(e)}"
              )

      @self.tool()
      async def execute_on_named_server(
          server_name: str = Field(..., description="预配置的服务器名称"),
          command: str = Field(..., description="要执行的命令"),
          sudo: bool = Field(False, description="是否使用sudo"),
          sudo_password: Optional[str] = Field(None, description="sudo密码"),
          timeout: int = Field(30, description="命令执行超时时间")
      ) -> CommandResult:
          """
          在预配置的服务器上执行命令

          使用预配置的服务器连接信息执行命令。
          服务器配置需要预先在环境变量或配置文件中设置。
          """
          try:
              if server_name not in self.server_configs:
                  return CommandResult(
                      success=False,
                      stdout="",
                      stderr="",
                      exit_code=-1,
                      error_message=f"未找到服务器配置: {server_name}"
                  )

              conn_config = self.server_configs[server_name]
              return await self._execute_command(
                  conn_config,
                  command,
                  sudo,
                  sudo_password,
                  timeout
              )

          except Exception as e:
              return CommandResult(
                  success=False,
                  stdout="",
                  stderr="",
                  exit_code=-1,
                  error_message=f"执行失败: {str(e)}"
              )

      @self.tool()
      async def test_ssh_connection(
          hostname: str = Field(..., description="服务器主机名或IP地址"),
          username: str = Field(..., description="用户名"),
          port: int = Field(22, description="SSH端口"),
          password: Optional[str] = Field(None, description="密码"),
          key_path: Optional[str] = Field(None, description="私钥文件路径")
      ) -> Dict[str, Any]:
          """
          测试SSH连接

          测试到远程服务器的SSH连接是否正常。
          """
          try:
              conn_config = SSHConnection(
                  hostname=hostname,
                  port=port,
                  username=username,
                  password=password,
                  key_filename=key_path
              )

              with self.ssh_manager.get_connection(conn_config) as ssh:
                  # 执行一个简单的命令来测试连接
                  stdin, stdout, stderr = ssh.exec_command("echo 'SSH connection test successful'")
                  output = stdout.read().decode('utf-8').strip()
                  error = stderr.read().decode('utf-8').strip()
                  exit_code = stdout.channel.recv_exit_status()

                  return {
                      "success": exit_code == 0,
                      "message": output if exit_code == 0 else error,
                      "exit_code": exit_code
                  }

          except Exception as e:
              return {
                  "success": False,
                  "message": f"连接测试失败: {str(e)}",
                  "exit_code": -1
              }

      @self.tool()
      async def list_directory(
          hostname: str,
          username: str,
          directory: str = Field("/", description="要列出的目录路径"),
          password: Optional[str] = None,
          key_path: Optional[str] = None,
          port: int = 22
      ) -> List[str]:
          """
          列出远程服务器上的目录内容
          """
          try:
              conn_config = SSHConnection(
                  hostname=hostname,
                  port=port,
                  username=username,
                  password=password,
                  key_filename=key_path
              )

              result = await self._execute_command(
                  conn_config,
                  f"ls -la {directory}",
                  sudo=False,
                  timeout=10
              )

              if result.success:
                  # 解析输出并返回文件列表
                  lines = result.stdout.strip().split('\n')
                  if len(lines) > 1:
                      return lines[1:]  # 跳过第一行总计数
                  return []
              else:
                  return [f"Error: {result.error_message}"]

          except Exception as e:
              return [f"Error: {str(e)}"]

      @self.tool()
      async def check_disk_usage(
          hostname: str,
          username: str,
          password: Optional[str] = None,
          key_path: Optional[str] = None,
          port: int = 22
      ) -> Dict[str, str]:
          """
          检查远程服务器的磁盘使用情况
          """
          try:
              conn_config = SSHConnection(
                  hostname=hostname,
                  port=port,
                  username=username,
                  password=password,
                  key_filename=key_path
              )

              result = await self._execute_command(
                  conn_config,
                  "df -h",
                  sudo=False,
                  timeout=10
              )

              if result.success:
                  lines = result.stdout.strip().split('\n')
                  usage_info = {}
                  for line in lines[1:]:  # 跳过标题行
                      parts = line.split()
                      if len(parts) >= 6:
                          filesystem = parts[0]
                          usage = parts[4]
                          usage_info[filesystem] = usage
                  return usage_info
              else:
                  return {"error": result.error_message}

          except Exception as e:
              return {"error": str(e)}

  async def _execute_command(
      self,
      conn_config: SSHConnection,
      command: str,
      sudo: bool = False,
      sudo_password: Optional[str] = None,
      timeout: int = 30
  ) -> CommandResult:
      """执行远程命令的内部方法"""
      try:
          if sudo and sudo_password:
              # 如果使用sudo并需要密码
              command = f"echo '{sudo_password}' | sudo -S {command}"
          elif sudo:
              # 如果使用sudo但不需要密码（用户可能在sudoers中配置了NOPASSWD）
              command = f"sudo {command}"

          with self.ssh_manager.get_connection(conn_config) as ssh:
              # 执行命令
              stdin, stdout, stderr = ssh.exec_command(
                  command,
                  timeout=timeout,
                  get_pty=True if sudo else False
              )

              # 读取输出
              stdout_str = stdout.read().decode('utf-8', errors='ignore').strip()
              stderr_str = stderr.read().decode('utf-8', errors='ignore').strip()
              exit_code = stdout.channel.recv_exit_status()

              return CommandResult(
                  success=exit_code == 0,
                  stdout=stdout_str,
                  stderr=stderr_str,
                  exit_code=exit_code,
                  error_message=None if exit_code == 0 else f"命令执行失败，退出码: {exit_code}"
              )

      except socket.timeout:
          return CommandResult(
              success=False,
              stdout="",
              stderr="",
              exit_code=-1,
              error_message="命令执行超时"
          )
      except Exception as e:
          return CommandResult(
              success=False,
              stdout="",
              stderr="",
              exit_code=-1,
              error_message=f"执行异常: {str(e)}"
          )

def main():
  """主函数"""
  # 创建SSH服务器实例
  server = SSHServer(name="ssh-command-executor")

  # 运行服务器
  print("Starting SSH MCP Server...")
  print("Available tools:")
  print("  1. execute_remote_command - 在远程服务器上执行命令")
  print("  2. execute_on_named_server - 在预配置的服务器上执行命令")
  print("  3. test_ssh_connection - 测试SSH连接")
  print("  4. list_directory - 列出远程目录内容")
  print("  5. check_disk_usage - 检查磁盘使用情况")

  server.run()

if __name__ == "__main__":
  main()
```

3. 配置环境变量文件

创建 .env 文件（可选）：

```env
# SSH 服务器配置（可选）
# 格式：服务器名称:主机名:用户名:密码
SSH_SERVERS=web1:192.168.1.100:admin:mypassword,db1:192.168.1.101:root:dbpassword
```

4. 客户端测试脚本

创建 test_ssh_client.py：

```python
"""
测试 SSH MCP Server 的客户端
"""

import asyncio
import json
from fastmcp import FastMCPClient

async def test_ssh_server():
  """测试SSH服务器"""

  # 连接到MCP服务器
  client = FastMCPClient("ssh-command-executor")

  # 测试连接
  print("1. 测试SSH连接...")
  result = await client.test_ssh_connection(
      hostname="your-server-ip",
      username="your-username",
      password="your-password"  # 或使用 key_path="~/.ssh/id_rsa"
  )
  print(f"连接测试结果: {json.dumps(result, indent=2)}")

  # 执行命令
  print("\n2. 执行远程命令...")
  result = await client.execute_remote_command(
      hostname="your-server-ip",
      username="your-username",
      password="your-password",
      command="uname -a",
      timeout=10
  )

  print(f"命令执行结果:")
  print(f"  成功: {result.success}")
  print(f"  退出码: {result.exit_code}")
  print(f"  输出:\n{result.stdout}")
  if result.stderr:
      print(f"  错误:\n{result.stderr}")

  # 检查磁盘使用情况
  print("\n3. 检查磁盘使用情况...")
  disk_usage = await client.check_disk_usage(
      hostname="your-server-ip",
      username="your-username",
      password="your-password"
  )
  print(f"磁盘使用情况: {json.dumps(disk_usage, indent=2)}")

  # 列出目录
  print("\n4. 列出目录内容...")
  files = await client.list_directory(
      hostname="your-server-ip",
      username="your-username",
      password="your-password",
      directory="/tmp"
  )
  print("目录内容:")
  for file in files:
      print(f"  {file}")

if __name__ == "__main__":
  # 首先启动SSH MCP Server
  print("请先启动SSH MCP Server:")
  print("  python ssh_mcp_server.py")
  print("\n然后运行此测试脚本。")

  # 或者直接测试（需要server已经运行）
  # asyncio.run(test_ssh_server())
```

5. Docker 部署配置

创建 Dockerfile：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# 运行MCP服务器
CMD ["python", "ssh_mcp_server.py"]
```

创建 docker-compose.yml：

```yaml
version: '3.8'

services:
ssh-mcp-server:
  build: .
  ports:
    - "8000:8000"  # MCP服务器端口
  environment:
    - SSH_SERVERS=${SSH_SERVERS}
  volumes:
    - ./config:/app/config
    - ./logs:/app/logs
    - ~/.ssh:/home/mcpuser/.ssh:ro  # 挂载SSH密钥
  restart: unless-stopped
```

6. 使用说明

启动服务器：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器
python ssh_mcp_server.py
```

在 Claude Desktop 中配置：

在 Claude Desktop 的配置文件中添加：

```json
{
"mcpServers": {
  "ssh-server": {
    "command": "python",
    "args": ["/path/to/ssh_mcp_server.py"],
    "env": {
      "SSH_SERVERS": "web1:192.168.1.100:admin:password"
    }
  }
}
}
```

基本使用示例：

```python
# 在 Claude 中可以直接使用：
"""
请帮我检查服务器 web1 的磁盘使用情况。
"""

# 或者执行特定命令：
"""
在 web1 服务器上查看系统日志的最后10行：
tail -n 10 /var/log/syslog
"""
```

7. 安全注意事项

1. 敏感信息保护：
 · 不要将密码硬编码在代码中
 · 使用环境变量或密钥文件
 · 考虑使用 SSH 代理转发
2. 权限控制：
 · 为不同操作创建不同的 SSH 用户
 · 使用 sudo 限制可执行的命令
 · 实施最小权限原则
3. 审计日志：
 · 记录所有执行的命令
 · 监控异常访问模式

这个实现提供了完整的 SSH 远程命令执行功能，支持密码和密钥认证，包含了错误处理和连接管理，可以直接集成到 Claude Desktop 中使用。
