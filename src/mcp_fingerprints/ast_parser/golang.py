"""Go MCP SDK static parser."""

from __future__ import annotations

import re
from typing import Any


def parse_golang_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from Golang source code."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    # 1. Parse constants mapping (single and block)
    constants: dict[str, str] = {}
    for match in re.finditer(r'const\s+([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*["\']([^"\']+)["\']', code):
        constants[match.group(1)] = match.group(2)
        
    for match in re.finditer(r'const\s*\(\s*(.*?)\s*\)', code, re.DOTALL):
        block = match.group(1)
        for line_match in re.finditer(r'([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*["\']([^"\']+)["\']', block):
            constants[line_match.group(1)] = line_match.group(2)

    # 2a. Extract Official SDK Literals (Go SDK parser)
    from mcp_fingerprints.go_sdk_parser import parse_official_go_tools
    official_tools = parse_official_go_tools(code)
    for t in official_tools:
        if t["name"] not in seen_names:
            seen_names.add(t["name"])
            extracted.append(t)

    # 2b. Match Official SDK Composite Literals (mcp.Tool{...}) - legacy for var assignments
    tool_pattern = re.compile(
        r'(?:[a-zA-Z0-9_]+\s*(?:=|:=)\s*&?)mcp\.Tool\s*\{([^\}]+)\}',
        re.DOTALL
    )
    for match in tool_pattern.finditer(code):
        body = match.group(1)
        
        name_match = re.search(r'Name\s*:\s*(?:["\']([^"\']+)["\']|([a-zA-Z0-9_]+))', body)
        name = None
        if name_match:
            name = name_match.group(1) if name_match.group(1) else constants.get(name_match.group(2), name_match.group(2))
            
        if not name:
            continue
            
        if name in seen_names:
            continue
            
        desc_match = re.search(r'Description\s*:\s*(?:["\']([^"\']+)["\']|([a-zA-Z0-9_]+))', body)
        desc = None
        if desc_match:
            desc = desc_match.group(1) if desc_match.group(1) else constants.get(desc_match.group(2), desc_match.group(2))
            
        title_match = re.search(r'Title\s*:\s*(?:["\']([^"\']+)["\']|([a-zA-Z0-9_]+))', body)
        title = None
        if title_match:
            title = title_match.group(1) if title_match.group(1) else constants.get(title_match.group(2), title_match.group(2))
            
        if not desc or len(desc) < 3:
            desc = title if title else name
            
        seen_names.add(name)
        extracted.append({
            "name": name,
            "description": desc,
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        })
        
    for match in re.finditer(r'mcp\.(?:NewTool|NewToolWithRawSchema)\s*\(\s*["\']([^"\']+)["\']', code):
        name = match.group(1)
        if name in seen_names:
            continue
        seen_names.add(name)
        
        start_idx = match.end()
        chunk = code[start_idx:start_idx + 1500]
        
        end_idx = -1
        open_parens = 1
        for i, char in enumerate(chunk):
            if char == '(':
                open_parens += 1
            elif char == ')':
                open_parens -= 1
                if open_parens == 0:
                    end_idx = i
                    break
        
        body = chunk[:end_idx] if end_idx != -1 else chunk
            
        desc = name
        
        # Check if description is passed as a positional argument right after NewTool("name", "description")
        inline_desc_match = re.match(r'^\s*,\s*mcp\.WithDescription\s*\(\s*["\']([^"\']+)["\']\s*\)', chunk)
        if not inline_desc_match:
            inline_desc_match = re.match(r'^\s*,\s*["\']([^"\']+)["\']', chunk)
        
        desc_match = re.search(r'mcp\.WithDescription\s*\(\s*["\']([^"\']+)["\']\s*\)', body)
        if inline_desc_match:
            desc = inline_desc_match.group(1)
        elif desc_match:
            desc = desc_match.group(1)
            
        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []
        
        param_regex = re.compile(
            r'mcp\.With(String|Number|Boolean|Object|Array|Float|Int)\s*\(\s*["\']([^"\']+)["\'](?:[,\s]*(.*?))?\)',
            re.DOTALL
        )
        for p_match in param_regex.finditer(body):
            ptype_raw = p_match.group(1).lower()
            pname = p_match.group(2)
            p_args = p_match.group(3) or ""
            
            schema_type = "string"
            if ptype_raw in ("number", "int", "float"):
                schema_type = "number"
            elif ptype_raw == "boolean":
                schema_type = "boolean"
            elif ptype_raw == "object":
                schema_type = "object"
            elif ptype_raw == "array":
                schema_type = "array"
                
            properties[pname] = {"type": schema_type}
            if "mcp.Required" in p_args or "Required:" in p_args or "Required()" in p_args:
                required.append(pname)
                
        extracted.append({
            "name": name,
            "description": desc,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": sorted(required),
            }
        })
        
    return extracted


