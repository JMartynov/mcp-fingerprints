"""Static AST Code Parsers for FastMCP Python and TypeScript/JavaScript SDKs."""

from __future__ import annotations

import ast
import re
from typing import Any


def _python_type_to_schema_type(annotation_node: ast.expr | None) -> str:
    """Convert Python AST type annotation to JSON schema type string."""
    if annotation_node is None:
        return "string"
    if isinstance(annotation_node, ast.Name):
        id_str = annotation_node.id.lower()
        if id_str in ("str", "text"):
            return "string"
        if id_str in ("int", "integer"):
            return "integer"
        if id_str in ("float", "number"):
            return "number"
        if id_str in ("bool", "boolean"):
            return "boolean"
        if id_str in ("list", "sequence", "tuple", "set"):
            return "array"
        if id_str in ("dict", "mapping", "object"):
            return "object"
    elif isinstance(annotation_node, ast.Subscript):
        if isinstance(annotation_node.value, ast.Name):
            id_str = annotation_node.value.id.lower()
            if id_str in ("list", "sequence", "set", "iterable"):
                return "array"
            if id_str in ("dict", "mapping"):
                return "object"
            if id_str in ("optional", "union"):
                # Inspect slice argument
                slice_val = annotation_node.slice
                if isinstance(slice_val, ast.Name):
                    return _python_type_to_schema_type(slice_val)
    elif isinstance(annotation_node, ast.Constant):
        val = str(annotation_node.value).lower()
        if val in ("str", "int", "float", "bool", "list", "dict"):
            return _python_type_to_schema_type(ast.Name(id=val))
    return "string"


class FastMcpAstVisitor(ast.NodeVisitor):
    """AST Visitor extracting @mcp.tool() and @fastmcp.tool() decorated functions."""

    def __init__(self) -> None:
        self.extracted_tools: list[dict[str, Any]] = []

    @staticmethod
    def _is_tool_decorator(decorator: ast.expr) -> tuple[bool, str | None, str | None]:
        """Check if decorator matches @mcp.tool, @app.tool, @fastmcp.tool, or @tool()."""
        is_tool = False
        custom_name = None
        custom_desc = None

        if isinstance(decorator, ast.Call):
            func_node = decorator.func
            # Extract keywords like name="...", description="..."
            for kw in decorator.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    custom_name = kw.value.value
                elif kw.arg == "description" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    custom_desc = kw.value.value
        else:
            func_node = decorator

        if isinstance(func_node, ast.Attribute):
            if func_node.attr == "tool":
                is_tool = True
        elif isinstance(func_node, ast.Name):
            if func_node.id in ("tool", "mcp_tool"):
                is_tool = True

        return is_tool, custom_name, custom_desc

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node)
        self.generic_visit(node)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        tool_found = False
        extracted_name = None
        extracted_desc = None

        for dec in node.decorator_list:
            is_tool, c_name, c_desc = self._is_tool_decorator(dec)
            if is_tool:
                tool_found = True
                if c_name:
                    extracted_name = c_name
                if c_desc:
                    extracted_desc = c_desc

        if not tool_found:
            return

        tool_name = extracted_name or node.name
        docstring = ast.get_docstring(node) or ""
        tool_desc = extracted_desc or docstring.strip().split("\n")[0] or tool_name

        # Extract arguments and inputSchema
        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        # Process function positional arguments (excluding 'self', 'cls', 'ctx', 'context')
        for arg in node.args.args:
            arg_name = arg.arg
            if arg_name in ("self", "cls", "ctx", "context"):
                continue

            schema_type = _python_type_to_schema_type(arg.annotation)
            properties[arg_name] = {"type": schema_type}

            # Check if arg has a default value (non-required)
            num_defaults = len(node.args.defaults)
            args_without_defaults = len(node.args.args) - num_defaults
            arg_idx = node.args.args.index(arg)
            if arg_idx < args_without_defaults:
                required.append(arg_name)

        # Process keyword-only arguments
        for idx, kwarg in enumerate(node.args.kwonlyargs):
            kwarg_name = kwarg.arg
            if kwarg_name in ("self", "cls", "ctx", "context"):
                continue
            schema_type = _python_type_to_schema_type(kwarg.annotation)
            properties[kwarg_name] = {"type": schema_type}
            if idx >= len(node.args.kw_defaults) or node.args.kw_defaults[idx] is None:
                required.append(kwarg_name)

        input_schema = {
            "type": "object",
            "properties": properties,
            "required": sorted(required),
        }

        self.extracted_tools.append({
            "name": tool_name,
            "description": tool_desc,
            "inputSchema": input_schema,
            "property_keys": sorted(properties.keys()),
            "required_keys": sorted(required),
        })


def parse_python_mcp_ast(code: str) -> list[dict[str, Any]]:
    """Parse Python source code and return statically extracted MCP tool definitions."""
    try:
        tree = ast.parse(code)
    except Exception:
        return []

    visitor = FastMcpAstVisitor()
    visitor.visit(tree)
    return visitor.extracted_tools


def parse_typescript_mcp_ast(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from TypeScript/JavaScript source code."""
    extracted: list[dict[str, Any]] = []

    # Pattern 1: server.tool("name", "desc", { schema }, handler) or server.tool("name", { schema }, handler)
    tool_call_regex = re.compile(
        r'(?:server|mcp|app)\.tool\s*\(\s*["\']([^"\']+)["\']\s*,\s*(?:["\']([^"\']+)["\']\s*,\s*)?(?:z\.object\s*\(\s*\{([^}]*)\}\s*\)|\{([^}]*)\})',
        re.DOTALL | re.MULTILINE,
    )

    for match in tool_call_regex.finditer(code):
        tool_name = match.group(1)
        tool_desc = match.group(2) or tool_name
        zod_body = match.group(3) or match.group(4) or ""

        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        if zod_body:
            # Parse property key and type (e.g., query: z.string().describe(...))
            prop_lines = zod_body.split(",")
            for line in prop_lines:
                p_match = re.search(r'([a-zA-Z0-9_$]+)\s*:\s*z\.([a-zA-Z0-9]+)', line)
                if p_match:
                    p_name = p_match.group(1)
                    p_ztype = p_match.group(2).lower()
                    stype = "string"
                    if p_ztype in ("number", "int", "float"):
                        stype = "number"
                    elif p_ztype in ("boolean", "bool"):
                        stype = "boolean"
                    elif p_ztype in ("array", "list"):
                        stype = "array"
                    elif p_ztype in ("object", "record"):
                        stype = "object"
                    properties[p_name] = {"type": stype}
                    if "optional" not in line:
                        required.append(p_name)

        input_schema = {
            "type": "object",
            "properties": properties,
            "required": sorted(required),
        }

        extracted.append({
            "name": tool_name,
            "description": tool_desc,
            "inputSchema": input_schema,
            "property_keys": sorted(properties.keys()),
            "required_keys": sorted(required),
        })

    # Pattern 2: Object literal declaration [{ name: "...", description: "...", inputSchema: ... }]
    obj_literal_regex = re.compile(
        r'\{\s*name\s*:\s*["\']([^"\']+)["\']\s*,\s*description\s*:\s*["\']([^"\']+)["\']',
        re.DOTALL | re.MULTILINE,
    )
    for match in obj_literal_regex.finditer(code):
        t_name = match.group(1)
        t_desc = match.group(2)
        if not any(t["name"] == t_name for t in extracted):
            extracted.append({
                "name": t_name,
                "description": t_desc,
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "property_keys": [],
                "required_keys": [],
            })

    return extracted


def parse_mcp_source_code(code: str, language: str = "python") -> list[dict[str, Any]]:
    """Parse MCP source code in Python or TypeScript/JavaScript and return extracted tool signatures."""
    if language.lower() in ("python", "py"):
        return parse_python_mcp_ast(code)
    elif language.lower() in ("typescript", "ts", "javascript", "js"):
        return parse_typescript_mcp_ast(code)
    return []
