"""Ruby MCP SDK static parser."""

from __future__ import annotations

import re
from typing import Any


def parse_ruby_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from Ruby source code."""
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

    def parse_params(body: str, block_args_str: str = "") -> tuple[dict[str, Any], list[str]]:
        props: dict[str, Any] = {}
        req: list[str] = []

        if block_args_str:
            kwarg_regex = re.compile(r'([a-zA-Z0-9_]+):\s*([^,]*)')
            for param_match in kwarg_regex.finditer(block_args_str):
                pname = param_match.group(1)
                default_val = param_match.group(2).strip()
                props[pname] = {"type": "string"}
                if not default_val:
                    req.append(pname)
                else:
                    if default_val.lower() in ("true", "false"):
                        props[pname]["type"] = "boolean"
                    elif re.match(r'^\d+$', default_val) or re.match(r'^\d+\.\d+$', default_val):
                        props[pname]["type"] = "number"
                    elif default_val.startswith('"') or default_val.startswith("'"):
                        props[pname]["type"] = "string"

        param_regex = re.compile(
            r'(?:param|argument|attribute\??)\s+[:"\']?([a-zA-Z0-9_]+)["\']?\s*(?:,\s*(.*?))?(?:\n|#|$)',
            re.IGNORECASE,
        )

        for param_match in param_regex.finditer(body):
            pname = param_match.group(1)
            args_str = param_match.group(2) or ""

            ptype = "string"
            type_m = re.search(r'(?:type:\s*[:"\']?|Types::)([a-zA-Z0-9_]+)', args_str, re.IGNORECASE)
            if type_m:
                ptype_raw = type_m.group(1).lower()
                if ptype_raw in ("integer", "int", "fixnum", "numeric", "float"):
                    ptype = "number"
                elif ptype_raw in ("boolean", "bool", "trueclass", "falseclass"):
                    ptype = "boolean"
                elif ptype_raw in ("array", "list"):
                    ptype = "array"
                elif ptype_raw in ("hash", "dict", "object"):
                    ptype = "object"

            props[pname] = {"type": ptype}

            desc_m = re.search(r'(?:desc|description):\s*["\']([^"\']+)["\']', args_str)
            if desc_m:
                props[pname]["description"] = desc_m.group(1)

            req_m = re.search(r"required:\s*(true|false)", args_str, re.IGNORECASE)
            is_required = True
            if req_m and req_m.group(1).lower() == "false":
                is_required = False

            if param_match.group(0).lower().startswith("attribute?"):
                is_required = False

            if is_required:
                if pname not in req:
                    req.append(pname)
            elif pname in req:
                req.remove(pname)

        return props, req

    dsl_regex = re.compile(
        r'(?:(?:desc|description)\s+(?:["\']([^"\']+)["\']|<<[-~]?([\'"]?)([A-Za-z0-9_]+)\2\s*\n(.*?)\n\s*\3)\s+)?'
        r'(?:server\.register_tool|tool)\s*\(?\s*[:"\']([a-zA-Z0-9_]+)["\']?\s*(?:,\s*(.*?))?\)?\s*(?:do\b|\{)',
        re.DOTALL | re.IGNORECASE,
    )

    for match in dsl_regex.finditer(code):
        inline_desc = match.group(1)
        heredoc_desc = match.group(4)
        name = match.group(5)
        args_str = match.group(6) or ""
        start_idx = match.end()
        is_curly = match.group(0).strip().endswith("{")

        body = ""
        open_count = 1
        
        words_regex = r"\b(do|class|module|def|case|begin|if|unless|while|until|for|end)\b"
        if is_curly:
            words_regex = r"(\{|\})"
            
        words = re.finditer(words_regex, code[start_idx:])
        for w in words:
            word = w.group(1)
            if word in (
                "do", "class", "module", "def", "case", "begin", "if", "unless", "while", "until", "for", "{"
            ):
                open_count += 1
            elif word in ("end", "}"):
                open_count -= 1
                if open_count == 0:
                    body = code[start_idx : start_idx + w.start()]
                    break

        if not body:
            body = code[start_idx:]
            end_m = re.search(r"(\bend\b|\})", body)
            if end_m:
                body = body[: end_m.start()]

        block_args_str = ""
        if body.strip().startswith("|"):
            body_parts = body.split("|", 2)
            if len(body_parts) >= 3:
                block_args_str = body_parts[1]
                body = body_parts[2]

        desc = ""
        desc_kw_m = re.search(r'(?:description|desc):\s*(?:["\']([^"\']+)["\']|<<[-~]?([\'"]?)([A-Za-z0-9_]+)\2\s*\n(.*?)\n\s*\3)', args_str, re.DOTALL)
        if desc_kw_m:
            if desc_kw_m.group(1):
                desc = desc_kw_m.group(1)
            else:
                desc = desc_kw_m.group(4).strip()
        else:
            str_args = re.findall(r'["\']([^"\']+)["\']', args_str)
            if str_args:
                desc = str_args[0]
                
        if not desc:
            if heredoc_desc:
                desc = heredoc_desc.strip()
            elif inline_desc:
                desc = inline_desc.strip()

        if not desc:
            desc = name

        props, req = parse_params(body, block_args_str)
        add_tool(name, desc, props, req)

    class_regex = re.compile(
        r"class\s+[A-Z][a-zA-Z0-9_]*\s*<\s*(?:[A-Za-z0-9_]+::)*Tool\b", re.DOTALL
    )
    for match in class_regex.finditer(code):
        start_idx = match.end()
        body = ""
        open_count = 1
        words = re.finditer(
            r"\b(do|class|module|def|case|begin|if|unless|while|until|for|end)\b",
            code[start_idx:],
        )
        for w in words:
            word = w.group(1)
            if word in (
                "do", "class", "module", "def", "case", "begin", "if", "unless", "while", "until", "for"
            ):
                open_count += 1
            elif word == "end":
                open_count -= 1
                if open_count == 0:
                    body = code[start_idx : start_idx + w.start()]
                    break

        if not body:
            body = code[start_idx:]
            end_m = re.search(r"\bend\b", body)
            if end_m:
                body = body[: end_m.start()]

        name_m = re.search(
            r'(?:@?name\s*(?:=\s*)?|\bname\b\s+)["\']([a-zA-Z0-9_]+)["\']', body
        )
        name = name_m.group(1) if name_m else None
        if not name:
            continue

        desc_m = re.search(
            r'(?:@?description\s*(?:=\s*)?|\b(?:description|desc)\b\s+)(?:["\']([^"\']+)["\']|<<[-~]?([\'"]?)([A-Za-z0-9_]+)\2\s*\n(.*?)\n\s*\3)', body, re.DOTALL
        )
        desc = name
        if desc_m:
            if desc_m.group(1):
                desc = desc_m.group(1)
            else:
                desc = desc_m.group(4).strip()

        props, req = parse_params(body)
        add_tool(name, desc, props, req)

    return extracted



