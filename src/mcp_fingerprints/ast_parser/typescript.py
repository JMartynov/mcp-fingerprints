"""TypeScript / JavaScript MCP SDK static AST/regex parser."""

from __future__ import annotations

import re
from typing import Any

from .base import AstBundleResult, logger


def _extract_balanced_braces(text: str, start_pos: int = 0) -> str:
    """Extract content inside the first balanced pair of curly braces '{' ... '}' starting at start_pos."""
    start_idx = text.find("{", start_pos)
    if start_idx == -1:
        return ""
    depth = 0
    in_quote: str | None = None
    for i in range(start_idx, len(text)):
        ch = text[i]
        if in_quote:
            if ch == in_quote:
                in_quote = None
            continue
        if ch in ("'", '"', "`"):
            in_quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start_idx + 1 : i]
    return ""


def _parse_balanced_zod_schema(zod_body: str) -> tuple[dict[str, Any], list[str]]:
    """Balanced-delimiter parser for Zod object schema definitions.

    Accurately handles nested z.object({...}), z.array(...), .describe(...), .default(...),
    .enum([...]), and .optional().
    """
    properties: dict[str, Any] = {}
    required: list[str] = []

    raw_props: list[str] = []
    current: list[str] = []
    paren_depth = 0
    brace_depth = 0
    bracket_depth = 0
    in_quote: str | None = None

    for ch in zod_body:
        if in_quote:
            current.append(ch)
            if ch == in_quote:
                in_quote = None
            continue

        if ch in ("'", '"', "`"):
            in_quote = ch
            current.append(ch)
        elif ch == "(":
            paren_depth += 1
            current.append(ch)
        elif ch == ")":
            paren_depth = max(0, paren_depth - 1)
            current.append(ch)
        elif ch == "{":
            brace_depth += 1
            current.append(ch)
        elif ch == "}":
            brace_depth = max(0, brace_depth - 1)
            current.append(ch)
        elif ch == "[":
            bracket_depth += 1
            current.append(ch)
        elif ch == "]":
            bracket_depth = max(0, bracket_depth - 1)
            current.append(ch)
        elif ch == "," and paren_depth == 0 and brace_depth == 0 and bracket_depth == 0:
            prop_str = "".join(current).strip()
            if prop_str:
                raw_props.append(prop_str)
            current = []
        else:
            current.append(ch)

    if current:
        prop_str = "".join(current).strip()
        if prop_str:
            raw_props.append(prop_str)

    for item in raw_props:
        if ":" not in item:
            continue
        parts = item.split(":", 1)
        p_name = parts[0].strip()
        expr = parts[1].strip()

        outer_expr = expr
        stype = "string"
        nested_props = None
        items_dict = None
        if "z.object" in expr:
            stype = "object"
            z_idx = expr.find("z.object")
            brace_body = _extract_balanced_braces(expr, z_idx)
            if brace_body:
                nested_props, _ = _parse_balanced_zod_schema(brace_body)
                first_brace = expr.find("{", z_idx)
                closing_brace = first_brace + len(brace_body) + 1
                outer_expr = expr[closing_brace:]
        elif re.search(r"z\.(?:array|list)", expr):
            stype = "array"
            arr_inner = re.search(r"z\.(?:array|list)\s*\(\s*z\.([a-zA-Z0-9]+)", expr)
            if arr_inner:
                inner_name = arr_inner.group(1).lower()
                i_type = "number" if inner_name in ("number", "int") else ("boolean" if inner_name in ("bool", "boolean") else "string")
                items_dict = {"type": i_type}
            else:
                items_dict = {"type": "string"}
        elif re.search(r"z\.(?:number|int|float)", expr):
            stype = "number"
        elif re.search(r"z\.(?:boolean|bool)", expr):
            stype = "boolean"

        prop_dict: dict[str, Any] = {"type": stype}
        if items_dict:
            prop_dict["items"] = items_dict
        if nested_props:
            prop_dict["properties"] = nested_props

        # Parse .describe("...")
        desc_m = re.search(r'\.describe\s*\(\s*["\'`]([^"\'`]+)["\'`]\s*\)', outer_expr)
        if desc_m:
            prop_dict["description"] = desc_m.group(1)

        # Parse .default(...)
        default_m = re.search(r'\.default\s*\(\s*([^)]+)\s*\)', outer_expr)
        has_default = False
        if default_m:
            raw_def = default_m.group(1).strip()
            has_default = True
            if raw_def.startswith(('"', "'", "`")) and raw_def.endswith(('"', "'", "`")):
                prop_dict["default"] = raw_def[1:-1]
            elif raw_def.lower() in ("true", "false"):
                prop_dict["default"] = raw_def.lower() == "true"
            else:
                try:
                    prop_dict["default"] = int(raw_def) if "." not in raw_def else float(raw_def)
                except ValueError:
                    prop_dict["default"] = raw_def

        # Parse .enum([...]) or z.enum([...])
        enum_m = re.search(r'\.(?:enum|nativeEnum)\s*\(\s*\[([^\]]+)\]\s*\)', expr)
        if not enum_m:
            enum_m = re.search(r'z\.enum\s*\(\s*\[([^\]]+)\]\s*\)', expr)
        if enum_m:
            raw_enum_items = [re.sub(r'["\'`\s]', '', x) for x in enum_m.group(1).split(',')]
            prop_dict["enum"] = [x for x in raw_enum_items if x]

        properties[p_name] = prop_dict

        # Determine if required: not optional and no default
        is_optional = ".optional()" in outer_expr
        if not is_optional and not has_default:
            required.append(p_name)

    return properties, required


def parse_typescript_mcp_ast(code: str) -> AstBundleResult:
    """Statically extract MCP tool definitions from TypeScript/JavaScript source code."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    env_vars: set[str] = set()

    # Capture process.env variables
    for m in re.finditer(r'process\.env\.([a-zA-Z_][a-zA-Z0-9_]*)', code):
        env_vars.add(m.group(1))
    for m in re.finditer(r'process\.env\[["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']\]', code):
        env_vars.add(m.group(1))

    def add_tool(name: str, desc: str, props: dict[str, Any], req: list[str]) -> None:
        if not name or name in seen_names:
            return
        seen_names.add(name)
        extracted.append({
            "name": name,
            "description": desc or name,
            "inputSchema": {
                "type": "object",
                "properties": props,
                "required": sorted(req),
            },
            "property_keys": sorted(props.keys()),
            "required_keys": sorted(req),
        })

    # Pattern 1: server.tool("name", "desc", { schema }, handler) or server.tool("name", { schema }, handler)
    tool_call_regex = re.compile(
        r'(?:server|mcp|app)\.tool\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\'`]([^"\'`]+)["\'`])?\s*(?:,\s*|\))',
        re.MULTILINE,
    )

    for match in tool_call_regex.finditer(code):
        tool_name = match.group(1)
        tool_desc = match.group(2) or tool_name
        start_pos = match.end()
        rest = code[start_pos : start_pos + 100].lstrip()
        if rest.startswith("{") or rest.startswith("z.object"):
            zod_body = _extract_balanced_braces(code, start_pos)
            properties, required = _parse_balanced_zod_schema(zod_body)
            add_tool(tool_name, tool_desc, properties, required)
        else:
            add_tool(tool_name, tool_desc, {}, [])

    # Pattern 2: server.registerTool("name", { title: "...", description: "...", inputSchema: { ... } }, handler)
    register_tool_regex = re.compile(
        r'(?:server|mcp|app)\.registerTool\s*\(\s*["\']([^"\']+)["\']\s*,\s*\{',
        re.MULTILINE,
    )
    for m in register_tool_regex.finditer(code):
        t_name = m.group(1)
        if t_name in seen_names:
            continue
        start_idx = m.end() - 1
        chunk = code[start_idx : start_idx + 2500]
        desc_m = re.search(r'description\s*:\s*["\'`]([^"\'`]+)["\'`]', chunk)
        t_desc = desc_m.group(1) if desc_m else t_name
        properties = {}
        required = []
        schema_pos = chunk.find("inputSchema")
        if schema_pos != -1:
            schema_body = _extract_balanced_braces(chunk, schema_pos)
            if schema_body:
                properties, required = _parse_balanced_zod_schema(schema_body)

        add_tool(t_name, t_desc, properties, required)

    # Pattern 4: Object literal array declaration [{ name: "...", description: "...", inputSchema: ... }]
    # E.g. tools = [{ name: "read_file", ... }]
    for match in re.finditer(r'(?:\{|,)\s*name\s*:\s*["\']([a-zA-Z0-9_\-]+)["\']', code):
        t_name = match.group(1)
        if t_name in seen_names or t_name.startswith("$"):
            continue

        pre_code = code[max(0, match.start() - 40) : match.start()]
        if "new Server" in pre_code or "new McpServer" in pre_code:
            continue

        start_idx = match.start()
        chunk = code[start_idx : start_idx + 2500]

        # Isolate this object up to next tool definition if possible
        next_tool_match = re.search(r'(?:\{|,)\s*name\s*:\s*["\']', chunk[10:])
        if next_tool_match:
            chunk = chunk[:next_tool_match.start() + 10]

        desc_m = re.search(
            r'description\s*:\s*([\'"`].*?[\'"`](?:\s*\+\s*[\'"`].*?[\'"`])*)',
            chunk,
            re.DOTALL,
        )
        schema_m = re.search(r'(?:inputSchema|parameters)\s*:\s*\{', chunk)

        # Must have either description or inputSchema/parameters to be a tool definition
        if not desc_m and not schema_m:
            continue

        # Ignore server metadata objects ({ name: "server", version: "1.0.0" })
        if re.search(r'\bversion\s*:\s*["\']', chunk) and not schema_m:
            continue

        if desc_m:
            raw_desc = desc_m.group(1)
            cleaned_desc = re.sub(r'[\'"`]\s*\+\s*[\'"`]', '', raw_desc)
            t_desc = re.sub(r'\s+', ' ', cleaned_desc).strip('\'"` \n') or t_name
        else:
            t_desc = t_name

        properties = {}
        required = []

        if schema_m:
            schema_chunk = chunk[schema_m.end() - 1 :]
            for p_match in re.finditer(r'([a-zA-Z0-9_$]+)\s*:\s*\{([^{}]+)\}', schema_chunk, re.DOTALL):
                p_name = p_match.group(1)
                p_body = p_match.group(2)
                t_match = re.search(r'type\s*:\s*["\']([^"\']+)["\']', p_body)
                if t_match:
                    properties[p_name] = {"type": t_match.group(1)}

            for z_match in re.finditer(r'([a-zA-Z0-9_$]+)\s*:\s*z\.([a-zA-Z0-9]+)', schema_chunk):
                p_name = z_match.group(1)
                p_ztype = z_match.group(2).lower()
                stype = "string"
                if p_ztype in ("number", "int", "float"):
                    stype = "number"
                elif p_ztype in ("boolean", "bool"):
                    stype = "boolean"
                elif p_ztype in ("array", "list"):
                    stype = "array"
                elif p_ztype in ("object", "record"):
                    stype = "object"
                if p_name not in properties:
                    properties[p_name] = {"type": stype}

            req_match = re.search(r'required\s*:\s*\[([^\]]*?)\]', schema_chunk, re.DOTALL)
            if req_match:
                req_str = req_match.group(1)
                for req_item in req_str.split(","):
                    req_item_clean = req_item.strip().strip('"\' \n\t')
                    if req_item_clean:
                        required.append(req_item_clean)

        add_tool(t_name, t_desc, properties, required)

    # Pattern 5: Standalone / helper function tool declarations:
    helper_tool_regex = re.compile(
        r'(?<!\.)\b(?:tool|createTool|defineTool)\s*\(\s*["\']([a-zA-Z0-9_\-]+)["\']\s*(?:,\s*(?:["\'`]([^"\'`]+)["\'`]|z\.object|\{))?',
        re.MULTILINE,
    )
    for m in helper_tool_regex.finditer(code):
        t_name = m.group(1)
        t_desc = m.group(2) or t_name
        if t_name not in seen_names and not t_name.startswith("$"):
            add_tool(t_name, t_desc, {}, [])

    # Pattern 5: CallToolRequest router switch/if dispatch table
    if any(k in code for k in ("CallToolRequest", "request.params.name", "tools/call", "setRequestHandler")):
        ignored_names = {"initialize", "initialized", "ping", "error", "cancelled", "cancel", "list", "schema", "default"}
        for cm in re.finditer(r'case\s+["\']([a-zA-Z0-9_\-]+)["\']\s*:', code):
            c_name = cm.group(1)
            if c_name not in seen_names and c_name.lower() not in ignored_names:
                add_tool(c_name, f"Execute {c_name}", {}, [])

        for im in re.finditer(r'(?:request\.params\.name|params\.name|\bname)\s*===\s*["\']([a-zA-Z0-9_\-]+)["\']', code):
            i_name = im.group(1)
            if i_name not in seen_names and i_name.lower() not in ignored_names:
                add_tool(i_name, f"Execute {i_name}", {}, [])

    # Pattern 6: Dynamic Array Resolution in ListToolsRequestSchema handlers
    # Find list tools request handlers returning `tools: IDENTIFIER`
    list_tools_handlers = re.finditer(r'ListToolsRequestSchema[\s\S]*?return\s+\{[\s\S]*?tools\s*:\s*([a-zA-Z_$][0-9a-zA-Z_$]*)', code)
    for m in list_tools_handlers:
        identifier = m.group(1)
        # Search the module scope for `const IDENTIFIER = [...]` or `let IDENTIFIER = [...]`
        # Also match the tools inside it by using the regex used in Pattern 4
        # We can locate the assignment block and search within it.
        escaped_identifier = re.escape(identifier)
        array_decl_match = re.search(rf'(?:const|let|var)\s+{escaped_identifier}\s*(?::\s*[^=]+)?\s*=\s*\[', code)
        if array_decl_match:
            start_idx = array_decl_match.end()
            # Extract tools by searching from start_idx in `code` using Pattern 4 regex
            chunk = code[start_idx : start_idx + 10000] # large enough chunk
            
            # Use same match logic as pattern 4, inside this chunk
            for match in re.finditer(r'(?:\{|,)\s*name\s*:\s*["\']([a-zA-Z0-9_\-]+)["\']', chunk):
                t_name = match.group(1)
                if t_name in seen_names or t_name.startswith("$"):
                    continue

                sub_start_idx = match.start()
                sub_chunk = chunk[sub_start_idx : sub_start_idx + 2500]

                # Isolate this object up to next tool definition if possible
                next_tool_match = re.search(r'(?:\{|,)\s*name\s*:\s*["\']', sub_chunk[10:])
                if next_tool_match:
                    sub_chunk = sub_chunk[:next_tool_match.start() + 10]

                desc_m = re.search(
                    r'description\s*:\s*([\'"`].*?[\'"`](?:\s*\+\s*[\'"`].*?[\'"`])*)',
                    sub_chunk,
                    re.DOTALL,
                )
                schema_m = re.search(r'(?:inputSchema|parameters)\s*:\s*\{', sub_chunk)

                if desc_m:
                    raw_desc = desc_m.group(1)
                    cleaned_desc = re.sub(r'[\'"`]\s*\+\s*[\'"`]', '', raw_desc)
                    t_desc = re.sub(r'\s+', ' ', cleaned_desc).strip('\'"` \n') or t_name
                else:
                    t_desc = t_name

                properties = {}
                required = []

                if schema_m:
                    schema_chunk = sub_chunk[schema_m.end() - 1 :]
                    for p_match in re.finditer(r'([a-zA-Z0-9_$]+)\s*:\s*\{([^{}]+)\}', schema_chunk, re.DOTALL):
                        p_name = p_match.group(1)
                        p_body = p_match.group(2)
                        t_match = re.search(r'type\s*:\s*["\']([^"\']+)["\']', p_body)
                        if t_match:
                            properties[p_name] = {"type": t_match.group(1)}

                add_tool(t_name, t_desc, properties, required)

    return AstBundleResult(tools=extracted, env_vars=env_vars)


