"""
Mock GitHub MCP server

This MCP server exposes the endpoints described in mock-github-mcp-server/openapi-spec.json
as tools. Each tool issues an HTTP request to the mock GitHub API at
https://githubmockdaservice.azurewebsites.net and returns the parsed JSON response (or
an error object on failure).

Usage:
    python server.py
    # or run via MCP tools like `uv run mcp dev server.py` or install into Claude Desktop

Environment:
    - MOCK_GITHUB_BASE_URL: optional base URL to override the default API host
    - GITHUB_TOKEN: optional bearer token to include in requests
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional

import requests
from mcp.server.fastmcp import FastMCP


logger = logging.getLogger("mock_github_mcp_server")
logging.basicConfig(level=logging.INFO)

# Base URL - read from environment to make testing easier
BASE_URL = os.environ.get("MOCK_GITHUB_BASE_URL", "https://githubmockdaservice.azurewebsites.net").rstrip("/")
DEFAULT_TIMEOUT = float(os.environ.get("MOCK_GITHUB_TIMEOUT", "30"))

mcp = FastMCP("Mock GitHub (OpenAPI)", host="0.0.0.0", port=3001)


def _request(
    method: str, path: str, params: Optional[Dict[str, Any]] = None, json_body: Optional[Any] = None
) -> Any:
    """Helper to perform an HTTP request against the mock GitHub service.

    Returns the parsed JSON response when available. On HTTP error status codes this
    function returns a dictionary with isError=True (so the tool call can provide
    the model with an error object instead of causing a protocol-level failure).
    """
    url = f"{BASE_URL}{path if path.startswith('/') else '/' + path}"

    headers: Dict[str, str] = {}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("MOCK_GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Use synchronous requests to avoid async/await complexity
    logger.debug("HTTP %s %s params=%s json=%s", method, url, params, json_body)
    try:
        resp = requests.request(method, url, params=params, json=json_body, headers=headers, timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.Timeout:
        return {"isError": True, "message": "Request timed out", "url": url, "method": method}
    except requests.exceptions.RequestException as e:
        return {"isError": True, "message": f"Request failed: {e}", "url": url, "method": method}

    # Try to parse JSON; fall back to raw text
    try:
        data = resp.json()
    except Exception:
        data = resp.text

    if resp.status_code >= 400:
        # Return an explicit error object for the tool result
        return {
            "isError": True,
            "status": resp.status_code,
            "content": data,
            "url": url,
            "method": method,
        }

    return data


# Tool: GET /issues
@mcp.tool()
def list_issues(
    filter: str = "assigned",
    state: str = "open",
    labels: Optional[str] = None,
    sort: str = "created",
    direction: str = "desc",
    since: Optional[str] = None,
    pulls: bool = False,
    per_page: int = 5,
    page: int = 1,
) -> Any:
    """List issues assigned to the user across repositories.

    Maps to GET /issues
    """
    params: Dict[str, Any] = {
        "filter": filter,
        "state": state,
        "labels": labels,
        "sort": sort,
        "direction": direction,
        "since": since,
        "pulls": str(pulls).lower(),
        "per_page": per_page,
        "page": page,
    }
    # Remove keys with None values
    params = {k: v for k, v in params.items() if v is not None}

    return _request("GET", "/issues", params=params)


# Tool: GET /repos/{owner}/{repo}/issues
@mcp.tool()
def list_repo_issues(
    owner: str,
    repo: str,
    milestone: Optional[str] = None,
    state: str = "open",
    assignee: Optional[str] = None,
    creator: Optional[str] = None,
    mentioned: Optional[str] = None,
    labels: Optional[str] = None,
    sort: str = "created",
    direction: str = "desc",
    since: Optional[str] = None,
    per_page: int = 5,
    page: int = 1,
) -> Any:
    """List issues in a repository.

    Maps to GET /repos/{owner}/{repo}/issues
    """
    params: Dict[str, Any] = {
        "milestone": milestone,
        "state": state,
        "assignee": assignee,
        "creator": creator,
        "mentioned": mentioned,
        "labels": labels,
        "sort": sort,
        "direction": direction,
        "since": since,
        "per_page": per_page,
        "page": page,
    }
    params = {k: v for k, v in params.items() if v is not None}

    path = f"/repos/{owner}/{repo}/issues"
    return _request("GET", path, params=params)


# Tool: GET /repos/{owner}/{repo}/issues/{issue_number}
@mcp.tool()
def get_issue(owner: str, repo: str, issue_number: int) -> Any:
    """Get a specific issue by number.

    Maps to GET /repos/{owner}/{repo}/issues/{issue_number}
    """
    path = f"/repos/{owner}/{repo}/issues/{issue_number}"
    return _request("GET", path)


# Tool: PATCH /repos/{owner}/{repo}/issues/{issue_number}
@mcp.tool()
def update_issue(
    owner: str,
    repo: str,
    issue_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    state_reason: Optional[str] = None,
    assignees: Optional[List[str]] = None,
    labels: Optional[List[str]] = None,
    milestone: Optional[int] = None,
) -> Any:
    """Update an issue's attributes.

    Maps to PATCH /repos/{owner}/{repo}/issues/{issue_number}
    Only non-None fields are sent in the request body.
    """
    payload: Dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if body is not None:
        payload["body"] = body
    if state is not None:
        payload["state"] = state
    if state_reason is not None:
        payload["state_reason"] = state_reason
    if assignees is not None:
        payload["assignees"] = assignees
    if labels is not None:
        payload["labels"] = labels
    if milestone is not None:
        payload["milestone"] = milestone

    if not payload:
        return {"isError": True, "message": "No update fields provided"}

    path = f"/repos/{owner}/{repo}/issues/{issue_number}"
    return _request("PATCH", path, json_body=payload)


# Tool: GET /repos/{owner}/{repo}/pulls
@mcp.tool()
def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 5,
    page: int = 1,
) -> Any:
    """List pull requests in a repository.

    Maps to GET /repos/{owner}/{repo}/pulls
    """
    params: Dict[str, Any] = {
        "state": state,
        "sort": sort,
        "direction": direction,
        "per_page": per_page,
        "page": page,
    }
    path = f"/repos/{owner}/{repo}/pulls"
    return _request("GET", path, params=params)


if __name__ == "__main__":
    # Default: run using the stdio transport (works with the MCP Inspector and uv run mcp dev)
    # For HTTP-based testing use mcp.run(transport='streamable-http') instead.
    mcp.run(transport='streamable-http')
