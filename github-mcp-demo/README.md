# GitHub MCP Demo

一个基于 Python 的简易 MCP 服务器示例，用来列出当前 GitHub 用户的仓库列表。支持自定义 GitHub Enterprise Host（通过 API URL 设置）。

## 主要能力
- MCP 工具 `list_repositories`：列出当前认证用户的仓库（支持 `visibility` 与 `affiliation` 过滤）。
- 支持通过环境变量配置 GitHub Token、API Host、TLS 校验。

## 目录结构
- `server.py`：MCP 服务器入口与工具实现。
- `requirements.txt`：运行所需依赖列表。

## 先决条件
- Python 3.10+
- 已安装 `pip` / `venv`，或使用 `uv` 等工具管理环境。
- 需要一个具备 `repo` / `read:user` 权限的 GitHub Token。

## 安装
```bash
cd github-mcp-demo
pip install -r requirements.txt
```

如果使用 `uv`：
```bash
uv pip install -r requirements.txt
```

## 配置
- `GITHUB_TOKEN`：GitHub Personal Access Token（必需，访问 `/user/repos` 需要认证）。
- `GITHUB_API_URL`：GitHub API 地址，默认 `https://api.github.com`，GitHub Enterprise 常见为 `https://<your-host>/api/v3`。
- `GITHUB_VERIFY_SSL`：设为 `false` 可跳过 TLS 校验（默认 `true`，仅在内部自签证书场景下使用）。

在启动前可以在终端设置环境变量：
```bash
export GITHUB_TOKEN=<your-token>
export GITHUB_API_URL=https://github.mycompany.com/api/v3   # 如使用 GHE
export GITHUB_VERIFY_SSL=true
```

也可以复制 `.env.example` 为 `.env`，并填入自己的配置：
```bash
cp .env.example .env
# 或在 Windows:
# copy .env.example .env
```

## 运行
```bash
python server.py
```

`FastMCP` 会在标准输入输出上运行 MCP 服务器。将其注册到支持 MCP 的客户端（例如通过 Claude Desktop / VS Code 扩展等）时，入口命令即为上面的启动命令。

## 使用示例（工具）
- `list_repositories(visibility="private")`
- `list_repositories(affiliation="owner,organization_member")`

工具返回的字段包含：
- `name`、`full_name`
- `description`
- `private`、`visibility`
- `html_url`、`ssh_url`、`clone_url`
- `default_branch`
- `updated_at`

## 故障排查
- **401 / 403**：检查 `GITHUB_TOKEN` 是否正确、是否具备访问权限，或者企业实例是否启用 SSO。
- **证书问题**：内部自签证书可暂时设置 `GITHUB_VERIFY_SSL=false`，更推荐导入可信根证书。
- **没有结果**：确认 Token 具备访问当前用户仓库的权限，或调整 `affiliation` / `visibility` 过滤参数。

## 在 VS Code 中配置使用（以 Claude for VS Code 为例）
可以直接在 VS Code 的 `settings.json` 里给 MCP 服务器传递环境变量，从而不需要在系统环境里设置：
```jsonc
"claude.mcpServers": {
  "github-mcp-demo": {
    "command": "python",
    "args": ["server.py"],
    "cwd": "${workspaceFolder}/github-mcp-demo",
    "env": {
      "GITHUB_TOKEN": "ghp_xxxx",
      "GITHUB_API_URL": "https://api.github.com", // 或 GHE: https://your-host/api/v3
      "GITHUB_VERIFY_SSL": "true"
    }
  }
}
```

步骤：
- 在 VS Code 安装并登录 Claude for VS Code（或其他支持 MCP 的扩展）。
- 将上述片段放入 VS Code 设置（用户级或工作区级 `settings.json`）。
- 确保 `github-mcp-demo` 目录存在且依赖已安装（见上文安装步骤）。
- 重新加载 VS Code 后，Claude 将自动启动该 MCP 服务器，工具列表里会出现 `list_repositories`，可直接在对话中调用。
