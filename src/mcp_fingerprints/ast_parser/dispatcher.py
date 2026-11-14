"""Language detection and dispatch entrypoint for polyglot MCP source parsing."""

from __future__ import annotations

import re
from typing import Any

from .dotnet import parse_dotnet_mcp_code
from .golang import parse_golang_mcp_code
from .jvm import parse_jvm_mcp_code, parse_kotlin_mcp_code
from .php import parse_php_mcp_code
from .python import parse_python_mcp_ast
from .ruby import parse_ruby_mcp_code
from .rust import parse_rust_mcp_code
from .swift import parse_swift_mcp_code
from .typescript import parse_typescript_mcp_ast


def parse_mcp_source_code(code: str, language: str | None = None) -> list[dict[str, Any]]:
    """Parse MCP source code and return extracted tool signatures."""
    if language:
        lang = language.lower()
        if lang in ("python", "py"):
            return parse_python_mcp_ast(code)
        elif lang in ("typescript", "ts", "javascript", "js", "mjs"):
            return parse_typescript_mcp_ast(code)
        elif lang in ("go", "golang"):
            return parse_golang_mcp_code(code)
        elif lang in ("rust", "rs"):
            return parse_rust_mcp_code(code)
        elif lang == "java":
            return parse_jvm_mcp_code(code)
        elif lang in ("kt", "kotlin"):
            return parse_kotlin_mcp_code(code)
        elif lang in ("cs", "csharp", "dotnet"):
            return parse_dotnet_mcp_code(code)
        elif lang in ("swift",):
            return parse_swift_mcp_code(code)
        elif lang in ("php",):
            return parse_php_mcp_code(code)
        elif lang in ("ruby", "rb"):
            return parse_ruby_mcp_code(code)
        elif lang in ("openapi", "swagger", "json", "yaml", "yml"):
            from mcp_fingerprints.manifest_parser import parse_manifest_mcp_tools
            manifest_res = parse_manifest_mcp_tools(code)
            if manifest_res:
                return manifest_res
            from mcp_fingerprints.openapi_parser import parse_openapi_spec
            return parse_openapi_spec(code)
            
    # Heuristics if language is unknown or not matched
    from mcp_fingerprints.manifest_parser import parse_manifest_mcp_tools
    manifest_res = parse_manifest_mcp_tools(code)
    if manifest_res:
        return manifest_res
    if "openapi" in code or "swagger" in code or "paths:" in code:
        from mcp_fingerprints.openapi_parser import parse_openapi_spec
        oa_res = parse_openapi_spec(code)
        if oa_res:
            return oa_res

    if "fun " in code and ("val " in code or "var " in code or "data class " in code or "@Tool" in code or "mcpServer {" in code):
        res = parse_kotlin_mcp_code(code)
        if res: return res

    if "@Tool" in code or "@McpFunction" in code:
        res = parse_jvm_mcp_code(code)
        if res: return res

    if (
        "using ModelContextProtocol" in code
        or "[McpTool" in code
        or "[McpFunction" in code
        or "[McpServerTool" in code
        or "[KernelFunction" in code
        or "new McpTool" in code
    ):
        res = parse_dotnet_mcp_code(code)
        if res: return res

    if code.startswith("package ") or "mcp.NewTool" in code:
        res = parse_golang_mcp_code(code)
        if res: return res
        
    if "fn main()" in code or "use rmcp" in code or "#[mcp_tool" in code:
        res = parse_rust_mcp_code(code)
        if res: return res

    if (
        "import Foundation" in code
        or "import MCP" in code
        or "@McpTool" in code
        or re.search(r'struct\s+[a-zA-Z0-9_]+\s*:\s*(?:[a-zA-Z0-9_]+,\s*)*(?:Tool|MCPTool|ToolDefinition)', code)
    ):
        res = parse_swift_mcp_code(code)
        if res: return res

    if "<?php" in code or "namespace " in code or "$server->registerTool" in code or "#[McpTool" in code:
        res = parse_php_mcp_code(code)
        if res: return res

    if (
        "def " in code and "end" in code
        and ("< MCP::Tool" in code or "< Tool" in code or "server.register_tool" in code or "require \"mcp\"" in code or "require 'mcp'" in code or " tool :" in code or " tool \"" in code or " tool '" in code)
    ):
        res = parse_ruby_mcp_code(code)
        if res: return res

    # Try python and ts fallbacks
    py_res = parse_python_mcp_ast(code)
    if py_res: return py_res
    
    return parse_typescript_mcp_ast(code)
