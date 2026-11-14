"""Kotlin and Java JVM MCP SDK static parsers."""

from __future__ import annotations

import re
from typing import Any


def parse_kotlin_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from Kotlin source code."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    def add_tool(name: str, desc: str, schema: dict[str, Any]):
        if name and name not in seen_names:
            extracted.append({
                "name": name,
                "description": desc or f"Kotlin MCP Tool {name}",
                "inputSchema": schema
            })
            seen_names.add(name)

    def find_data_classes(code_text: str) -> dict[str, str]:
        classes = {}
        pattern = r'data\s+class\s+([a-zA-Z0-9_]+)\s*\('
        for match in re.finditer(pattern, code_text):
            name = match.group(1)
            start_idx = match.end()
            open_parens = 1
            body_end = -1
            for i in range(start_idx, len(code_text)):
                if code_text[i] == '(':
                    open_parens += 1
                elif code_text[i] == ')':
                    open_parens -= 1
                    if open_parens == 0:
                        body_end = i
                        break
            if body_end != -1:
                body = code_text[start_idx:body_end]
                classes[name] = body
        return classes

    data_classes = find_data_classes(code)

    def map_type(kt_type: str) -> str:
        kt_type = kt_type.replace('?', '').strip()
        if kt_type in ('Int', 'Long', 'Short', 'Byte'):
            return "integer"
        elif kt_type in ('Float', 'Double'):
            return "number"
        elif kt_type == 'Boolean':
            return "boolean"
        elif kt_type.startswith('List<') or kt_type.startswith('Array<'):
            return "array"
        elif kt_type.startswith('Map<') or kt_type.startswith('JsonNode'):
            return "object"
        return "string"

    def parse_parameters(params_str: str) -> dict[str, Any]:
        schema = {"type": "object", "properties": {}, "required": []}
        if not params_str.strip():
            return schema

        params = []
        current = []
        depth = 0
        in_string = False
        for char in params_str:
            if char == '"' and depth == 0:
                in_string = not in_string
            if not in_string:
                if char == '<': depth += 1
                elif char == '>': depth -= 1
                elif char == ',' and depth == 0:
                    params.append("".join(current).strip())
                    current = []
                    continue
            current.append(char)
        if current:
            params.append("".join(current).strip())

        for p in params:
            desc = None
            desc_m = re.search(r'@Description\s*\(\s*["\']([^"\']+)["\']\s*\)', p)
            if desc_m:
                desc = desc_m.group(1)
            
            p_clean = re.sub(r'@[A-Za-z0-9_]+(?:\([^)]*\))?\s*', '', p)
            p_clean = p_clean.strip()
            
            m = re.match(r'(?:val\s+|var\s+)?([a-zA-Z0-9_]+)\s*:\s*([^=]+)(?:=(.*))?', p_clean)
            if not m:
                p_clean = re.sub(r'\s+', ' ', p_clean).strip()
                m = re.match(r'(?:val\s+|var\s+)?([a-zA-Z0-9_]+)\s*:\s*([^=]+)(?:=(.*))?', p_clean)
                
            if m:
                p_name = m.group(1).strip()
                p_type_full = m.group(2).strip()
                p_default = m.group(3)
                
                is_nullable = '?' in p_type_full
                json_type = map_type(p_type_full)
                
                prop = {"type": json_type}
                if desc:
                    prop["description"] = desc

                p_type_base = p_type_full.replace('?', '').strip()
                if p_type_base in data_classes:
                    dc_schema = parse_parameters(data_classes[p_type_base])
                    prop = dc_schema
                    prop["type"] = "object" 

                schema["properties"][p_name] = prop
                
                if not is_nullable and not p_default:
                    schema["required"].append(p_name)
                    
        return schema


    annotation_regex = re.compile(
        r"@(?:Tool|McpTool|ToolMethod|McpFunction)\s*(?:\((.*?)\))?", re.DOTALL
    )

    for match in annotation_regex.finditer(code):
        attrs = (match.group(1) or "").strip()
        
        name = ""
        desc = ""
        
        name_m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', attrs)
        if name_m:
            name = name_m.group(1)
        
        desc_m = re.search(r'(?:description|value)\s*=\s*["\']([^"\']+)["\']', attrs)
        if desc_m:
            desc = desc_m.group(1)
            
        if not name_m and not desc_m and attrs.startswith('"') and attrs.endswith('"'):
            if "description" in attrs or "value" in attrs:
                pass
            else:
                 name_m_simple = re.match(r'^["\']([^"\']+)["\']$', attrs)
                 if name_m_simple:
                     name = name_m_simple.group(1)

        start_idx = match.end()
        chunk = code[start_idx:start_idx + 600]
        
        method_match = re.search(
            r"(?:public|private|protected|internal)?\s*(?:open|override|final|suspend|inline|\s)*\s*fun\s+(?:<[^>]+>\s+)?(?:[\w.]+\.)?([a-zA-Z0-9_]+)\s*\(",
            chunk, re.DOTALL
        )
        
        schema = {"type": "object", "properties": {}, "required": []}
        if method_match:
            if not name:
                name = method_match.group(1)
            
            p_start = method_match.end()
            open_parens = 1
            p_end = -1
            for i in range(p_start, len(chunk)):
                if chunk[i] == '(':
                    open_parens += 1
                elif chunk[i] == ')':
                    open_parens -= 1
                    if open_parens == 0:
                        p_end = i
                        break
            if p_end != -1:
                params_str = chunk[p_start:p_end]
                schema = parse_parameters(params_str)
            
        add_tool(name, desc, schema)

    dsl_regex = re.compile(
        r'tool\s*\(\s*["\']([^"\']+)["\'](?:.*?\{|\))', re.DOTALL
    )
    for match in dsl_regex.finditer(code):
        name = match.group(1)
        desc = ""
        
        start_idx = match.end()
        chunk = code[start_idx:start_idx + 500]
        
        desc_m = re.search(r'description\s*=\s*["\']([^"\']+)["\']', chunk)
        if desc_m:
            desc = desc_m.group(1)
            
        schema = {"type": "object", "properties": {}}
        add_tool(name, desc, schema)
        
    class_regex = re.compile(
        r'class\s+([a-zA-Z0-9_]+Tool)(?:\s*\([^)]*\))?\s*:\s*[a-zA-Z0-9_]*McpTool[a-zA-Z0-9_]*', re.DOTALL
    )
    for match in class_regex.finditer(code):
        class_name = match.group(1)
        name = class_name
        desc = ""
        
        start_idx = match.start()
        chunk = code[start_idx:start_idx + 500]
        
        name_m = re.search(r'override\s+val\s+name(?:\s*:\s*String)?\s*=\s*["\']([^"\']+)["\']', chunk)
        if name_m:
            name = name_m.group(1)
            
        desc_m = re.search(r'override\s+val\s+description(?:\s*:\s*String)?\s*=\s*["\']([^"\']+)["\']', chunk)
        if desc_m:
            desc = desc_m.group(1)
            
        schema = {"type": "object", "properties": {}}
        add_tool(name, desc, schema)
        
    return extracted


def parse_jvm_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from Java/Kotlin source code."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    annotation_regex = re.compile(
        r"@(?:Tool|McpFunction)\s*(?:\(([^)]*)\))?", re.DOTALL
    )

    for match in annotation_regex.finditer(code):
        attrs = (match.group(1) or "").strip()

        name = ""
        desc = ""

        name_m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', attrs)
        if name_m:
            name = name_m.group(1)

        desc_m = re.search(r'(?:description|value)\s*=\s*["\']([^"\']+)["\']', attrs)
        if desc_m:
            desc = desc_m.group(1)

        if not name_m and not desc_m and attrs.startswith('"') and attrs.endswith('"'):
            desc = attrs.strip('"')

        start_idx = match.end()
        chunk = code[start_idx : start_idx + 600]

        method_match = re.search(
            r"(?:public|private|protected|internal)?\s*(?:open|override|final|suspend)?\s*(?:fun|[\w<>\[\]\?]+)\s+([a-zA-Z0-9_]+)\s*\(\s*",
            chunk,
        )

        if not name:
            if method_match:
                name = method_match.group(1)
            else:
                continue

        if not desc:
            desc = name

        if name in seen_names:
            continue

        seen_names.add(name)

        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        if method_match:
            # Re-search to find end of parameters properly
            # chunk starts after annotation for Java, but for .NET chunk starts at method end
            # It's safer to search for the first '(' in chunk if params_start doesn't have it
            params_start = 0
            if "(" in chunk:
                params_start = chunk.find("(") + 1
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

                    param_desc = ""

                    param_desc_m = re.search(
                        r'@ToolParam\s*\(\s*(?:description\s*=\s*)?["\']([^"\']+)["\']',
                        param,
                    )
                    if param_desc_m:
                        param_desc = param_desc_m.group(1)

                    # Remove all annotations before trying to parse the name/type
                    param_clean = re.sub(
                        r"@[A-Za-z0-9_]+(?:\([^)]*\))?\s*", "", param
                    ).strip()
                    param_clean = param_clean.split("=")[0].strip()

                    if ":" in param_clean:
                        # Kotlin: name: Type
                        p_parts = param_clean.split(":", 1)
                        pname = p_parts[0].strip()
                        ptype_raw = p_parts[1].strip()
                    else:
                        # Java: Type name
                        parts = param_clean.rsplit(" ", 1)
                        if len(parts) >= 2:
                            pname = parts[1].strip()
                            ptype_raw = parts[0].strip().split("<")[0]
                        else:
                            continue

                    pname = pname.strip()
                    ptype_base = (
                        ptype_raw.strip()
                        .lower()
                        .split("<")[0]
                        .split("[")[0]
                        .replace("?", "")
                    )

                    schema_type = "string"
                    if ptype_base in (
                        "int",
                        "integer",
                        "long",
                        "short",
                        "byte",
                        "float",
                        "double",
                        "number",
                    ):
                        schema_type = "number"
                    elif ptype_base in ("boolean", "bool"):
                        schema_type = "boolean"
                    elif ptype_base in (
                        "list",
                        "set",
                        "collection",
                        "array",
                        "iterable",
                    ):
                        schema_type = "array"
                    elif ptype_base in (
                        "map",
                        "dictionary",
                        "object",
                        "record",
                        "jsonnode",
                        "objectnode",
                    ):
                        schema_type = "object"

                    prop_schema = {"type": schema_type}
                    if param_desc:
                        prop_schema["description"] = param_desc
                    properties[pname] = prop_schema
                    required.append(pname)

        extracted.append(
            {
                "name": name,
                "description": desc,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": sorted(required),
                },
            }
        )

    return extracted


