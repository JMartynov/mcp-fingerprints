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
            title = m.group(2).strip().lower()
            if title in ('tools', 'available tools'):
                in_tools_section = True
                section_level = level
            elif in_tools_section and level <= section_level:
                in_tools_section = False
        
        if in_tools_section:
            # Parse Markdown Table rows
            if line.startswith('|') and line.endswith('|'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 2:
                    name_clean = clean_markdown(parts[0])
                    # Skip header/separator rows
                    if name_clean.lower() not in ('tool', 'name') and not re.match(r'^[-:\s]+$', parts[0]):
                        desc = parts[1]
                        properties = {}
                        required = []
                        if len(parts) >= 3:
                            args_str = parts[2]
                            arg_matches = re.findall(r'([a-zA-Z0-9_]+)\s*(?::|\()?\s*([a-zA-Z0-9_]+)?\)?', clean_markdown(args_str))
                            for match in arg_matches:
                                arg_name, arg_type = match
                                if arg_name:
                                    properties[arg_name] = {"type": arg_type or "string"}
                                    required.append(arg_name)
                        tools.append({
                            "name": name_clean, 
                            "description": clean_markdown(desc), 
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
