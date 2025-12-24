"""Simple MCP server for listing GitHub repositories.

Environment variables:
    GITHUB_TOKEN: personal access token used for authentication.
    GITHUB_API_URL: base API URL (default: https://api.github.com).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load .env file
load_dotenv()


APP_NAME = "github-mcp-demo"
DEFAULT_API_URL = "https://api.github.com"

app = FastMCP(APP_NAME)


def get_settings() -> tuple[str, str]:
    """Load GitHub-related settings from environment."""
    api_url = os.environ.get("GITHUB_API_URL", DEFAULT_API_URL).rstrip("/")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is required to list repositories. "
            "Create a Personal Access Token and export it before running the MCP server."
        )
    return api_url, token


def format_repo(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Pick a compact subset of repo fields for MCP output."""
    return {
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "description": repo.get("description"),
        "private": repo.get("private"),
        "visibility": repo.get("visibility"),
        "html_url": repo.get("html_url"),
        "ssh_url": repo.get("ssh_url"),
        "clone_url": repo.get("clone_url"),
        "default_branch": repo.get("default_branch"),
        "updated_at": repo.get("updated_at"),
    }


def curl_request(url: str, token: str) -> List[Dict[str, Any]]:
    """Execute curl command to fetch data from GitHub API."""
    cmd = [
        "curl",
        "-k",  # Ignore SSL certificate verification
        "-s",  # Silent mode
        "-H", f"Accept: application/vnd.github+json",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"User-Agent: {APP_NAME}/0.1",
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

    if result.returncode == 401 or result.returncode == 403:
        raise RuntimeError(
            "GitHub authentication failed. Check GITHUB_TOKEN or permissions."
        )

    if result.returncode != 0:
        raise RuntimeError(f"curl failed with code {result.returncode}: {result.stderr}")

    try:
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON response: {e}\nResponse: {result.stdout}")


async def fetch_repos(
    visibility: Optional[str],
    affiliation: Optional[str],
    per_page: int = 100,
) -> List[Dict[str, Any]]:
    """Fetch repositories for the authenticated user using curl."""
    api_url, token = get_settings()

    # Build query parameters
    params = [f"per_page={per_page}", "page=1"]
    if visibility:
        params.append(f"visibility={visibility}")
    if affiliation:
        params.append(f"affiliation={affiliation}")

    query_string = "&".join(params)
    url = f"{api_url}/user/repos?{query_string}"

    repos: List[Dict[str, Any]] = []
    page = 1

    while True:
        # Update page number in URL
        params_with_page = [p for p in params if not p.startswith("page=")]
        params_with_page.append(f"page={page}")
        query_string = "&".join(params_with_page)
        url = f"{api_url}/user/repos?{query_string}"

        batch = curl_request(url, token)

        if not batch:
            break

        repos.extend(format_repo(repo) for repo in batch)

        # If we got less than per_page results, we're done
        if len(batch) < per_page:
            break

        page += 1

    return repos


@app.tool()
async def list_repositories(
    visibility: Optional[str] = None,
    affiliation: Optional[str] = None,
    per_page: int = 100,
) -> List[Dict[str, Any]]:
    """List repositories for the authenticated user.

    Args:
        visibility: Optional filter: 'all', 'public', or 'private'.
        affiliation: Filter by affiliations, e.g. 'owner,collaborator,organization_member'.
        per_page: Page size for the GitHub API (max 100).
    """

    repos = await fetch_repos(visibility, affiliation, per_page=per_page)
    return repos


async def test_list(visibility: Optional[str] = None, affiliation: Optional[str] = None):
    """Test function to list repos directly."""
    try:
        repos = await list_repositories(visibility, affiliation)
        print(f"\n找到 {len(repos)} 个仓库:\n")
        for repo in repos:
            print(f"  - {repo['full_name']} ({repo['visibility']})")
            if repo.get('description'):
                print(f"    {repo['description']}")
        print()
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    import sys

    # Check for test mode
    if "--test" in sys.argv:
        # Parse simple args for test
        visibility = None
        affiliation = None
        args = sys.argv[1:]
        for i, arg in enumerate(args):
            if arg == "--visibility" and i + 1 < len(args):
                visibility = args[i + 1]
            elif arg == "--affiliation" and i + 1 < len(args):
                affiliation = args[i + 1]

        print("测试模式: 列出仓库...")
        asyncio.run(test_list(visibility, affiliation))
    else:
        # Run as MCP server
        asyncio.run(app.run())
