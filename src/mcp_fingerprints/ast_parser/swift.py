"""Swift MCP SDK static parser."""

from __future__ import annotations

import re
from typing import Any


def parse_swift_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from Swift source code."""
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

    def extract_docstring_before(pos: int) -> str:
        """Extract preceding triple-slash docstring comment (/// ...) before pos."""
        preceding = code[:pos].rstrip()
        lines = preceding.split("\n")
        doc_lines = []
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith("///"):
                doc_lines.append(stripped[3:].strip())
            elif not stripped:
                continue
            else:
                break
        doc_lines.reverse()
        return " ".join(doc_lines).strip()

    # Helper to parse arguments/properties from a chunk of swift code
    def parse_swift_args(args_chunk: str) -> tuple[dict[str, Any], list[str]]:
        props: dict[str, Any] = {}
        req: list[str] = []

        # Look for `let name: Type` or `var name: Type`, supporting property wrappers like @Option, @Argument, @Flag
        var_regex = re.compile(
            r'(?:@[a-zA-Z0-9_]+(?:\([^)]*\))?\s*)*(?:let|var)\s+([a-zA-Z0-9_]+)\s*:\s*([a-zA-Z0-9_\[\]\:\?\s<>\.]+?)(?=\n|;|,|=(?!>)|$)'
        )

        for match in var_regex.finditer(args_chunk):
            pname = match.group(1)
            ptype_raw = match.group(2).strip()

            is_optional = "?" in ptype_raw or "Optional<" in ptype_raw
            ptype_clean = ptype_raw.replace("?", "").replace(" ", "")

            schema_type = "string"
            if ptype_clean in ("Int", "Int32", "Int64", "UInt", "UInt32", "UInt64"):
                schema_type = "integer"
            elif ptype_clean in ("Double", "Float", "Decimal"):
                schema_type = "number"
            elif ptype_clean in ("Bool", "Boolean"):
                schema_type = "boolean"
            elif ptype_clean.startswith("[") and ptype_clean.endswith("]"):
                if ":" in ptype_clean:
                    schema_type = "object"  # e.g. [String: Any]
                else:
                    schema_type = "array"
            elif ptype_clean in ("String", "URL", "Date", "UUID", "Data", "FilePath"):
                schema_type = "string"

            # Check if property wrapper has help/description
            wrapper_match = re.search(r'help\s*:\s*["\']([^"\']+)["\']', match.group(0))
            prop_def: dict[str, Any] = {"type": schema_type}
            if wrapper_match:
                prop_def["description"] = wrapper_match.group(1)

            props[pname] = prop_def
            if not is_optional:
                req.append(pname)

        return props, req

    # Pattern 1: Structs/Classes/Actors conforming to Tool, MCPTool, ToolDefinition
    type_regex = re.compile(
        r'(?:final\s+|public\s+|internal\s+)*(?:struct|class|actor)\s+[a-zA-Z0-9_]+\s*:\s*(?:[a-zA-Z0-9_]+,\s*)*(?:Tool|MCPTool|ToolDefinition)(?:\s*,\s*[a-zA-Z0-9_]+)*\s*\{'
    )
    for type_match in type_regex.finditer(code):
        start_idx = type_match.end()
        doc_desc = extract_docstring_before(type_match.start())

        open_braces = 1
        body_end = -1
        for i in range(start_idx, len(code)):
            if code[i] == '{':
                open_braces += 1
            elif code[i] == '}':
                open_braces -= 1
                if open_braces == 0:
                    body_end = i
                    break
        if body_end != -1:
            body = code[start_idx:body_end]

            name = ""
            desc = ""
            name_m = re.search(r'(?:let|var)\s+name(?:\s*:\s*String)?\s*(?:=|{)\s*["\']([^"\']+)["\']', body)
            if name_m:
                name = name_m.group(1)

            desc_m = re.search(r'(?:let|var)\s+description(?:\s*:\s*String)?\s*(?:=|{)\s*["\']([^"\']+)["\']', body)
            if desc_m:
                desc = desc_m.group(1)
            elif doc_desc:
                desc = doc_desc

            # Look for nested Arguments or Input structs
            args_struct_m = re.search(r'struct\s+(?:Arguments|Input)\s*:\s*(?:Codable|Decodable)\s*\{([^}]+)\}', body)
            props = {}
            req = []
            if args_struct_m:
                props, req = parse_swift_args(args_struct_m.group(1))

            if name:
                add_tool(name, desc, props, req)

    # Pattern 2: Macro/Attribute definitions @McpTool(name: "...", description: "...") or @Tool or #mcpTool
    func_regex = re.compile(
        r'([@#](?:McpTool|Tool|mcpTool)(?:\([^)]+\))?)\s*(?:public\s+|private\s+|internal\s+)?func\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)',
        re.MULTILINE
    )
    for func_match in func_regex.finditer(code):
        attr = func_match.group(1)
        name = func_match.group(2)
        args_str = func_match.group(3)
        doc_desc = extract_docstring_before(func_match.start())
        desc = doc_desc or name

        name_m = re.search(r'name\s*:\s*["\']([^"\']+)["\']', attr)
        if name_m:
            name = name_m.group(1)

        desc_m = re.search(r'description\s*:\s*["\']([^"\']+)["\']', attr)
        if desc_m:
            desc = desc_m.group(1)

        props = {}
        req = []
        if args_str.strip():
            # Parse func arguments
            # e.g. path: String, limit: Int?
            # Also handle argument labels e.g. _ path: String
            for arg_part in args_str.split(','):
                arg_part = arg_part.strip()
                if not arg_part:
                    continue
                parts = arg_part.split(':')
                if len(parts) >= 2:
                    name_part = parts[0].strip()
                    type_part = ':'.join(parts[1:]).strip()

                    # Name might have labels: `_ path` or `with path`
                    pname = name_part.split()[-1]

                    is_optional = "?" in type_part or "Optional<" in type_part or " = " in type_part
                    ptype_clean = type_part.split('=')[0].replace("?", "").replace(" ", "")

                    schema_type = "string"
                    if "Int" in ptype_clean:
                        schema_type = "integer"
                    elif "Double" in ptype_clean or "Float" in ptype_clean or "Decimal" in ptype_clean:
                        schema_type = "number"
                    elif "Bool" in ptype_clean or "Boolean" in ptype_clean:
                        schema_type = "boolean"
                    elif ptype_clean.startswith("[") and ptype_clean.endswith("]"):
                        if ":" in ptype_clean:
                            schema_type = "object"
                        else:
                            schema_type = "array"
                    elif ptype_clean in ("String", "URL", "Date", "UUID", "Data", "FilePath"):
                        schema_type = "string"

                    props[pname] = {"type": schema_type}
                    if not is_optional:
                        req.append(pname)

        add_tool(name, desc, props, req)

    # Pattern 3: server.registerTool("name", description: "...") { ... }
    reg_regex = re.compile(
        r'(?:server|app)\.registerTool\s*\(\s*["\']([^"\']+)["\']\s*,\s*description\s*:\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    for reg_match in reg_regex.finditer(code):
        add_tool(reg_match.group(1), reg_match.group(2), {}, [])

    # Pattern 4: CallToolRequest switch dispatch
    switch_dispatch_regex = re.compile(
        r'switch\s+(?:request\.)?(?:params\.)?name\s*\{([^}]+)\}',
        re.MULTILINE
    )
    for switch_match in switch_dispatch_regex.finditer(code):
        switch_body = switch_match.group(1)
        for case_match in re.finditer(r'case\s+["\']([^"\']+)["\']\s*:', switch_body):
            tool_name = case_match.group(1)
            add_tool(tool_name, tool_name, {}, [])

    return extracted


