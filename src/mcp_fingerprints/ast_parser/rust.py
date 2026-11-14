"""Rust rmcp / MCP SDK static parser."""

from __future__ import annotations

import re
from typing import Any


def parse_rust_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from Rust source code."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    
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
            }
        })
        

    # Pattern 1: #[mcp_tool(name = "...", description = "...")]
    for match in re.finditer(r'#\[mcp_tool\s*\((.*?)\)\]', code, re.DOTALL):
        attrs = match.group(1)
        name_m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', attrs)
        if name_m:
            name = name_m.group(1)
            desc_m = re.search(r'description\s*=\s*["\']([^"\']+)["\']', attrs)
            desc = desc_m.group(1) if desc_m else name
            add_tool(name, desc, {}, [])

    # Pattern 1.5: #[tool(description = "...")] or #[tool]
    # for rmcp macros
    tool_attr_regex = re.compile(r'#\[tool(?:\s*\((.*?)\))?\]', re.DOTALL)
    for match in tool_attr_regex.finditer(code):
        attrs = match.group(1) or ""
        
        # Next function signature
        start_idx = match.end()
        chunk = code[start_idx:start_idx+600]
        
        fn_match = re.search(r'(?:async\s+)?fn\s+([a-zA-Z0-9_]+)\s*\(', chunk)
        if not fn_match:
            continue
            
        name = fn_match.group(1)
        desc_m = re.search(r'description\s*=\s*["\']([^"\']+)["\']', attrs)
        desc = desc_m.group(1) if desc_m else name
        
        properties = {}
        required = []
        
        # parse parameters
        params_start = fn_match.end()
        open_parens = 1
        params_end = -1
        for i in range(params_start, len(chunk)):
            if chunk[i] == "(":
                open_parens += 1
            elif chunk[i] == ")":
                open_parens -= 1
                if open_parens == 0:
                    params_end = i
                    break
                    
        if params_end != -1:
            params_str = chunk[params_start:params_end]
            params = []
            current_param = []
            nesting = 0
            for char in params_str:
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
                if not param:
                    continue
                
                parts = param.split(":")
                if len(parts) >= 2:
                    pname = parts[0].strip()
                    ptype_raw = parts[1].strip()
                    
                    if pname in ("&self", "self", "mut self"):
                        continue
                        
                    ptype_base = ptype_raw.lower().split("<")[1].split(">")[0].strip() if "option<" in ptype_raw.lower() else ptype_raw.lower().split("<")[0].replace("&", "").strip()
                    
                    schema_type = "string"
                    if ptype_base in ("i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "f32", "f64", "usize", "isize"):
                        schema_type = "number"
                    elif ptype_base == "bool":
                        schema_type = "boolean"
                    elif ptype_base in ("vec", "slice", "array"):
                        schema_type = "array"
                    elif ptype_base in ("hashmap", "btreemap", "json", "value"):
                        schema_type = "object"
                        
                    properties[pname] = {"type": schema_type}
                    
                    # Assume required unless Option
                    if not ptype_raw.startswith("Option<"):
                        required.append(pname)
                        
        add_tool(name, desc, properties, required)

            
    # Pattern 2: define_tool!("name", "description", ...)
    for match in re.finditer(r'define_tool!\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']', code):
        name = match.group(1)
        desc = match.group(2)
        add_tool(name, desc, {}, [])
        
    # Pattern 3: Tool { name: "...", description: "..." }
    for match in re.finditer(r'Tool\s*\{\s*[^{}]*?name\s*:\s*["\']([^"\']+)["\'](?:\.into\(\)|\.to_string\(\))?[^{}]*?description\s*:\s*["\']([^"\']+)["\'](?:\.into\(\)|\.to_string\(\))?', code, re.DOTALL):
        name = match.group(1)
        desc = match.group(2)
        add_tool(name, desc, {}, [])

    # Pattern 3 reverse: Tool { description: "...", name: "..." }
    for match in re.finditer(r'Tool\s*\{\s*[^{}]*?description\s*:\s*["\']([^"\']+)["\'](?:\.into\(\)|\.to_string\(\))?[^{}]*?name\s*:\s*["\']([^"\']+)["\'](?:\.into\(\)|\.to_string\(\))?', code, re.DOTALL):
        desc = match.group(1)
        name = match.group(2)
        add_tool(name, desc, {}, [])
        
    return extracted



