"""Simple MCP server for listing GitHub repositories.

Environment variables:
    GITHUB_TOKEN: personal access token used for authentication.
    GITHUB_API_URL: base API URL (default: https://api.github.com).
    GITHUB_VERIFY_SSL: set to "false" to skip TLS verification (not recommended).
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# Load .env file
load_dotenv()


APP_NAME = "github-mcp-demo"
DEFAULT_API_URL = "https://api.github.com"

app = FastMCP(APP_NAME)


def get_settings() -> tuple[str, str, bool]:
    """Load GitHub-related settings from environment."""
    api_url = os.environ.get("GITHUB_API_URL", DEFAULT_API_URL).rstrip("/")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is required to list repositories. "
            "Create a Personal Access Token and export it before running the MCP server."
        )
    verify = False
    return api_url, token, verify


def get_github_client() -> httpx.AsyncClient:
    """Return a configured HTTPX client for the GitHub API."""
    api_url, token, verify = get_settings()

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{APP_NAME}/0.1",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    transport = httpx.AsyncHTTPTransport(retries=2)
    return httpx.AsyncClient(
        base_url=api_url,
        headers=headers,
        verify=False,
        transport=transport,
        timeout=httpx.Timeout(15.0, read=30.0),
    )


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


async def fetch_repos(
    visibility: Optional[str],
    affiliation: Optional[str],
    per_page: int = 100,
) -> List[Dict[str, Any]]:
    """Fetch repositories for the authenticated user."""
    params: Dict[str, Any] = {"per_page": per_page, "page": 1}
    if visibility:
        params["visibility"] = visibility
    if affiliation:
        params["affiliation"] = affiliation

    repos: List[Dict[str, Any]] = []
    async with get_github_client() as client:
        while True:
            response = await client.get("/user/repos", params=params)
            if response.status_code == 401:
                raise RuntimeError(
                    "GitHub authentication failed. Check GITHUB_TOKEN or permissions."
                )
            response.raise_for_status()
            batch = response.json()
            repos.extend(format_repo(repo) for repo in batch)
            if "next" not in response.links:
                break
            params["page"] += 1
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
