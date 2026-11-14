"""Backward-compatible re-export shim for mcp_fingerprints.crawler.pkg_go_dev."""

from __future__ import annotations

from mcp_fingerprints.crawler.pkg_go_dev import _create_ssl_context, search_pkg_go_dev

__all__ = ["_create_ssl_context", "search_pkg_go_dev"]
