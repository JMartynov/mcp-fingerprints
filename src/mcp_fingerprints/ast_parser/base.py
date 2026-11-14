"""Static AST Code Parsers for FastMCP Python and TypeScript/JavaScript SDKs."""

from __future__ import annotations

import ast
import logging
import re
from typing import Any

logger = logging.getLogger("mcp_fingerprints.ast_parser")


class AstBundleResult(list):
    """Result list of extracted MCP tools with bundle-level properties for prompts, resources, and env vars."""

    def __init__(
        self,
        tools: list[dict[str, Any]] | None = None,
        prompts: list[dict[str, Any]] | None = None,
        resources: list[dict[str, Any]] | None = None,
        env_vars: set[str] | list[str] | tuple[str, ...] | None = None,
        dependencies: list[str] | None = None,
    ) -> None:
        raw_tools = list(tools or [])
        super().__init__(raw_tools)
        self.tools = raw_tools
        self.prompts = list(prompts or [])
        self.resources = list(resources or [])
        self.env_vars = tuple(sorted(set(env_vars or ())))
        self.required_env_vars = self.env_vars
        self.dependencies = list(dependencies or [])

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            if key == "tools":
                return self.tools
            if key == "prompts":
                return self.prompts
            if key == "resources":
                return self.resources
            if key in ("env_vars", "required_env_vars"):
                return list(self.env_vars)
            if key == "dependencies":
                return self.dependencies
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "tools":
            return self.tools
        if key == "prompts":
            return self.prompts
        if key == "resources":
            return self.resources
        if key in ("env_vars", "required_env_vars"):
            return list(self.env_vars)
        if key == "dependencies":
            return self.dependencies
        return default


