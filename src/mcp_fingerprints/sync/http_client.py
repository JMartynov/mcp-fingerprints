"""HTTP client, TLS context, and archive error definitions for synchronization."""

from __future__ import annotations

import json
import logging
import os
import ssl
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("mcp_fingerprints.synchronizer")


def _create_ssl_context() -> ssl.SSLContext:
    """Create a verified TLS SSLContext (with optional custom CA bundle via SSL_CERT_FILE)."""
    ca_file = os.environ.get("SSL_CERT_FILE")
    return ssl.create_default_context(cafile=ca_file) if ca_file else ssl.create_default_context()


def fetch_json(
    url: str,
    timeout: float = 8.0,
    headers: dict[str, str] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Fetch JSON from a remote URL with optional HTTP ETag caching.

    Returns (json_data, etag_header). If HTTP 304 Not Modified, returns (None, etag).
    """
    req_headers = {
        "User-Agent": "VerityRedTeam-MCPPassportSync/1.0",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, context=_create_ssl_context(), timeout=timeout) as resp:
            etag = resp.headers.get("ETag")
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, dict) else None, etag
    except urllib.error.HTTPError as he:
        if he.code == 304:
            return None, he.headers.get("ETag")
        logger.debug("HTTP %d for %s", he.code, url)
        return None, None
    except Exception as exc:
        logger.debug("Fetch failed for %s: %s", url, exc)
        return None, None


class ArchiveNotFoundError(Exception):
    """Raised when a repository or package returns 404 / Not Found."""


