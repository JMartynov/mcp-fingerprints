""".NET / C# MCP SDK static parser."""

from __future__ import annotations

import re
from typing import Any


def parse_dotnet_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from C#/.NET source code."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    def add_tool(name: str, desc: str, props: dict[str, Any], req: list[str]) -> None:
        if not name or name in seen_names:
            return
        seen_names.add(name)
        extracted.append(
            {
                "name": name,
                "description": desc or name,
                "inputSchema": {
                    "type": "object",
                    "properties": props,
                    "required": sorted(req),
                },
            }
        )

    # Pattern 1: Attributes on methods [McpTool("name", "description")], [McpFunction("name")], [McpServerTool(Name = "name")], or [KernelFunction]
    # Handle multiple attributes separated by comma or newlines within brackets, or consecutive brackets
    # e.g., [KernelFunction, Description("Multiply numbers")]

    # We find method declarations, then look backwards for attributes.
    # We also avoid matching `new McpTool(...)` by requiring a return type that isn't `new`.
    method_regex = re.compile(
        r"(?:public|private|protected|internal)?\s*(?:static\s+)?(?:async\s+)?(?:virtual\s+)?(?:override\s+)?(?:Task\s*<[^>]+>\s+|Task\s+|[\w<>\[\]\?]+\s+)([a-zA-Z0-9_]+)\s*\(",
        re.MULTILINE,
    )

    for method_match in method_regex.finditer(code):
        name = method_match.group(1)
        full_match = method_match.group(0).strip()
        if full_match.startswith("new "):
            continue
        start_idx = method_match.start()

        # Look at the previous 300 characters to find attributes
        prev_chunk = code[max(0, start_idx - 300) : start_idx]

        # Check if it has any tool attribute
        if not re.search(
            r"\[(?:McpTool|McpFunction|McpServerTool|KernelFunction)\b", prev_chunk
        ):
            continue

        desc = ""

        # Split by previous method closing brace if any, to isolate attributes
        if "}" in prev_chunk:
            prev_chunk = prev_chunk[prev_chunk.rfind("}") + 1 :]

        # Try to extract Name/Description from attributes
        attr_str = "".join(prev_chunk.splitlines())

        name_m = re.search(r'(?:Name|name)\s*=\s*["\']([^"\']+)["\']', attr_str)
        if name_m:
            name = name_m.group(1)

        desc_m = re.search(
            r'(?:Description|description)\s*\(\s*["\']([^"\']+)["\']\s*\)', attr_str
        )
        if desc_m:
            desc = desc_m.group(1)
        else:
            desc_m = re.search(
                r'(?:Description|description)\s*=\s*["\']([^"\']+)["\']', attr_str
            )
            if desc_m:
                desc = desc_m.group(1)

        # Look for [McpTool("name", "description")] or [McpFunction("name", "description")]
        mcp_tool_m = re.search(
            r'\[(?:McpTool|McpFunction)\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']+)["\'])?\s*\)\]',
            attr_str,
        )
        if mcp_tool_m:
            name = mcp_tool_m.group(1)
            if mcp_tool_m.group(2):
                desc = mcp_tool_m.group(2)

        if not desc:
            desc = name

        # method_match.end() is right after '('
        params_start = method_match.end()
        chunk = code[params_start : params_start + 600]

        if not name:
            name = method_match.group(1)
            desc = name

        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        open_parens = 1
        params_end = -1
        for i in range(len(chunk)):
            if chunk[i] == "(":
                open_parens += 1
            elif chunk[i] == ")":
                open_parens -= 1
                if open_parens == 0:
                    params_end = i
                    break

        if params_end != -1:
            params_str = chunk[:params_end]
            params = []
            current_param = []
            nesting = 0
            in_string = False
            for char in params_str:
                if char == '"' and nesting == 0:
                    in_string = not in_string
                if not in_string:
                    if char in "<[":
                        nesting += 1
                    elif char in ">]":
                        nesting -= 1
                    elif char == "," and nesting == 0:
                        params.append("".join(current_param).strip())
                        current_param = []
                        continue
                current_param.append(char)
            if current_param:
                params.append("".join(current_param).strip())

            for param in params:
                param = param.strip()
                if not param:
                    continue
                has_default = "=" in param
                is_nullable = "?" in param

                param_desc = ""
                param_desc_m = re.search(
                    r'\[Description\s*\(\s*["\']([^"\']+)["\']\s*\)\]', param
                )
                if param_desc_m:
                    param_desc = param_desc_m.group(1)

                param_clean = re.sub(r"\[[^\]]+\]\s*", "", param.split("=")[0]).strip()
                parts = param_clean.rsplit(" ", 1)
                if len(parts) >= 2:
                    pname = parts[1].strip()
                    ptype_raw = parts[0].strip().split("<")[0].replace("?", "").lower()
                    schema_type = "string"
                    if ptype_raw in (
                        "int",
                        "long",
                        "short",
                        "byte",
                        "float",
                        "double",
                        "decimal",
                    ):
                        schema_type = "number"
                    elif ptype_raw in ("bool", "boolean"):
                        schema_type = "boolean"
                    elif ptype_raw in ("list", "ienumerable", "ilist", "array"):
                        schema_type = "array"
                    elif ptype_raw in ("dictionary", "idictionary", "object"):
                        schema_type = "object"

                    prop_schema = {"type": schema_type}
                    if param_desc:
                        prop_schema["description"] = param_desc

                    properties[pname] = prop_schema
                    if not has_default and not is_nullable:
                        required.append(pname)

        add_tool(name, desc, properties, required)

    # Pattern 2: server.AddTool("name", "desc", ...)
    for match in re.finditer(
        r'(?:server|app)\.AddTool\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']+)["\'])?',
        code,
    ):
        add_tool(match.group(1), match.group(2) or match.group(1), {}, [])

    # Pattern 3: new McpTool("name", "desc")
    for match in re.finditer(
        r'new\s+McpTool\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']+)["\'])?', code
    ):
        add_tool(match.group(1), match.group(2) or match.group(1), {}, [])

    return extracted




