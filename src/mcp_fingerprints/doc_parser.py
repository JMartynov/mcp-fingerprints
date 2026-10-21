"""Markdown Document Parser for MCP Tool Extractions."""

from __future__ import annotations

import re
from typing import Any


def clean_markdown(text: str) -> str:
    """Removes basic markdown formatting like backticks and bold/italic asterisks."""
    return re.sub(r'[`*]', '', text).strip()


def parse_markdown_tool_docs(content: str) -> list[dict[str, Any]]:
    """
    Parses a markdown document, looking for "Tools" or "Available Tools" sections,
    and extracts tool definitions from markdown tables and lists.
    """
    tools = []
    
    in_tools_section = False
    section_level = 0
    
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for headers
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if re.search(r'(?i)\btools?\b', title):
                in_tools_section = True
                section_level = level
                table_headers = []
            elif in_tools_section and level <= section_level:
                in_tools_section = False
        
        if in_tools_section:
            # Parse Markdown Table rows
            if line.startswith('|') and line.endswith('|'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 2:
                    name_clean = clean_markdown(parts[0])
                    # Detect header rows dynamically
                    if not table_headers and re.match(r'^[a-zA-Z0-9\s_]+$', name_clean) and any(x.lower() in ('name', 'tool', 'function') for x in parts):
                        table_headers = [clean_markdown(p).lower() for p in parts]
                        i += 1
                        continue
                    
                    # Skip separator rows
                    if re.match(r'^[-:\s]+$', parts[0]):
                        i += 1
                        continue
                        
                    name_col_idx = 0
                    desc_col_idx = 1
                    params_col_idx = 2
                    
                    if table_headers:
                        for idx, h in enumerate(table_headers):
                            if h in ('name', 'tool', 'function'):
                                name_col_idx = idx
                            elif h in ('description', 'desc', 'summary'):
                                desc_col_idx = idx
                            elif h in ('parameters', 'params', 'arguments', 'args', 'schema'):
                                params_col_idx = idx
                                
                    if len(parts) > max(name_col_idx, desc_col_idx):
                        name_val = clean_markdown(parts[name_col_idx])
                        desc_val = parts[desc_col_idx]
                        properties = {}
                        required = []
                        if len(parts) > params_col_idx:
                            args_str = parts[params_col_idx]
                            arg_matches = re.findall(r'([a-zA-Z0-9_]+)\s*(?::|\()?\s*([a-zA-Z0-9_]+)?\)?', clean_markdown(args_str))
                            for match in arg_matches:
                                arg_name, arg_type = match
                                if arg_name:
                                    properties[arg_name] = {"type": arg_type or "string"}
                                    required.append(arg_name)
                        if name_val:
                            tools.append({
                                "name": name_val, 
                                "description": clean_markdown(desc_val), 
                                "inputSchema": {"type": "object", "properties": properties, "required": required}
                            })
            
            # Parse Markdown List items
            list_m = re.match(r'^[-*]\s+(.*)', line)
            if list_m:
                item_content = list_m.group(1)
                item_parts = item_content.split(':', 1)
                if len(item_parts) == 2:
                    name_clean = clean_markdown(item_parts[0])
                    desc_clean = clean_markdown(item_parts[1])
                    
                    properties = {}
                    required = []
                    
                    # Try to find params in parentheses in description
                    param_m = re.search(r'\((.*?)\)', desc_clean)
                    if param_m:
                        args_str = param_m.group(1)
                        if ':' in args_str:
                            arg_matches = re.findall(r'([a-zA-Z0-9_]+)\s*:\s*([a-zA-Z0-9_]+)', clean_markdown(args_str))
                            for arg_name, arg_type in arg_matches:
                                properties[arg_name] = {"type": arg_type}
                                required.append(arg_name)
                            desc_clean = desc_clean.replace(param_m.group(0), '').strip()

                    tools.append({
                        "name": name_clean, 
                        "description": desc_clean, 
                        "inputSchema": {"type": "object", "properties": properties, "required": required}
                    })
                    
        i += 1
        
    return tools
