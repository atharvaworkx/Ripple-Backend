"""Official GitHub API client for Pull Request metadata and file retrieval."""

import re
import os
import httpx
from typing import Dict, Any, List, Optional, Tuple

PR_URL_REGEX = re.compile(
    r"^https?://(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)/pull/(\d+)/?$"
)

def parse_github_pr_url(url: str) -> Optional[Tuple[str, str, int]]:
    """Validate and extract owner, repo, pull_number from GitHub PR URL."""
    if not url:
        return None
    match = PR_URL_REGEX.match(url.strip())
    if not match:
        return None
    owner, repo, pr_num = match.groups()
    return owner, repo, int(pr_num)

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Ripple-Impact-Analyzer/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def fetch_pr_details(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Fetch PR metadata from GitHub REST API."""
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=self.headers)

                if resp.status_code == 404:
                    return {
                        "success": False,
                        "error": f"Repository or Pull Request not found. It may be private or deleted (URL: github.com/{owner}/{repo}/pull/{pull_number}).",
                        "status_code": 404
                    }
                elif resp.status_code == 403 and "rate limit" in resp.text.lower():
                    return {
                        "success": False,
                        "error": "GitHub API rate limit exceeded. Please configure a personal access token (GITHUB_TOKEN) for higher limits.",
                        "status_code": 403
                    }
                elif resp.status_code != 200:
                    return {
                        "success": False,
                        "error": f"GitHub API error (HTTP {resp.status_code}): {resp.text[:200]}",
                        "status_code": resp.status_code
                    }

                data = resp.json()
                return {
                    "success": True,
                    "pr_number": pull_number,
                    "title": data.get("title", ""),
                    "state": data.get("state", "open"),
                    "author": data.get("user", {}).get("login", "unknown"),
                    "base_ref": data.get("base", {}).get("ref", "main"),
                    "base_sha": data.get("base", {}).get("sha", ""),
                    "head_ref": data.get("head", {}).get("ref", ""),
                    "head_sha": data.get("head", {}).get("sha", ""),
                    "html_url": data.get("html_url", ""),
                    "diff_url": data.get("diff_url", ""),
                    "changed_files_count": data.get("changed_files", 0)
                }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": f"Network error connecting to GitHub: {str(e)}",
                "status_code": 500
            }

    def fetch_pr_files(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Fetch changed files list and individual patches."""
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files"
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.get(url, headers=self.headers)
                if resp.status_code != 200:
                    return {"success": False, "error": f"Failed to fetch PR files: {resp.text[:200]}"}

                files = resp.json()
                parsed_files = []
                for f in files:
                    filename = f.get("filename", "")
                    parsed_files.append({
                        "filename": filename,
                        "status": f.get("status", "modified"),
                        "additions": f.get("additions", 0),
                        "deletions": f.get("deletions", 0),
                        "changes": f.get("changes", 0),
                        "patch": f.get("patch", ""),
                        "raw_url": f.get("raw_url", "")
                    })

                return {"success": True, "files": parsed_files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fetch_file_content(self, raw_url: str) -> Optional[str]:
        """Download raw file content with bounded size."""
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(raw_url, headers=self.headers)
                if resp.status_code == 200:
                    # Bound to 500KB per file
                    if len(resp.content) > 500 * 1024:
                        return None
                    return resp.text
        except Exception:
            pass
        return None
