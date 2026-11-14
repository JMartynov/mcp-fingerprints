"""Backward-compatible re-export shim for mcp_fingerprints.mcp_classifier."""

from __future__ import annotations

from mcp_fingerprints.mcp_classifier import (
    CORE_MCP_DEPENDENCIES,
    FALSE_POSITIVE_KEYWORDS,
    McpServerClassifier,
    McpServerValidator,
    OFFICIAL_SCOPES,
    sanitize_tool_definition,
)

__all__ = [
    "CORE_MCP_DEPENDENCIES",
    "FALSE_POSITIVE_KEYWORDS",
    "McpServerClassifier",
    "McpServerValidator",
    "OFFICIAL_SCOPES",
    "sanitize_tool_definition",
]
