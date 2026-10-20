"""Go module crawler for discovering cloud-native MCP servers."""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.parse
import ssl
from typing import Any

logger = logging.getLogger("verity.passport.sync.go")

def _create_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()

def search_pkg_go_dev(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Search for Go modules using GitHub search as a proxy for pkg.go.dev.
    Targets mcp-go, mcp-golang, and cloud-native toolings.
    """
    repos = []
    
    # We will search GitHub for these keywords and language Go
    q = f"{query} mcp server"
    github_search_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}+language:go&per_page={limit}"
    
    try:
        req = urllib.request.Request(
            github_search_url,
            headers={"User-Agent": "VerityRedTeam-Sync/1.0", "Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and "items" in data:
                repos = data["items"]
    except Exception as exc:
        logger.debug(f"Failed to search Go modules on GitHub: {exc}")
        
    return repos
