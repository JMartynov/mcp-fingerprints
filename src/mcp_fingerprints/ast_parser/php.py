"""PHP MCP SDK static parser."""

from __future__ import annotations

import re
from typing import Any


def parse_php_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from PHP source code."""
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

    def extract_docblock_params(doc: str) -> tuple[str, dict[str, dict[str, str]]]:
        """Extract general description and @param types/descriptions from docblock."""
        param_docs: dict[str, dict[str, str]] = {}
        lines = [line.strip().lstrip('*').strip() for line in doc.split('\n')]
        desc_lines = []
        for line in lines:
            if not line:
                continue
            if line.startswith('@param'):
                # @param type $name description... or @param $name description...
                m = re.match(r"@param\s+(?:([\w\\|?\[\]<>]+)\s+)?\$([\w]+)(?:\s+(.*))?", line)
                if m:
                    ptype, pname, pdesc = m.groups()
                    param_docs[pname] = {
                        "type": ptype or "",
                        "description": (pdesc or "").strip(),
                    }
            elif not line.startswith('@'):
                desc_lines.append(line)
        return " ".join(desc_lines).strip(), param_docs

    def map_php_type(type_raw: str) -> str:
        t = type_raw.lower().lstrip("?").strip()
        if "|" in t:
            parts = [p.strip() for p in t.split("|") if p.strip() != "null"]
            if all(p in ("int", "integer", "float", "double") for p in parts):
                return "number"
            if any(p in ("array", "iterable") or "[]" in p for p in parts):
                return "array"
            return "string"
        if t in ("int", "integer"):
            return "integer"
        if t in ("float", "double"):
            return "number"
        if t in ("bool", "boolean"):
            return "boolean"
        if t in ("array", "iterable") or t.endswith("[]") or t.startswith("array<"):
            return "array"
        if t in ("object", "stdclass"):
            return "object"
        return "string"

    def parse_php_params_chunk(chunk: str, doc_params: dict[str, dict[str, str]]) -> tuple[dict[str, Any], list[str]]:
        properties: dict[str, Any] = {}
        required: list[str] = []

        open_parens = 1
        params_end = -1
        in_string = False
        for i in range(len(chunk)):
            if chunk[i] in '\"\'':
                if i == 0 or chunk[i-1] != '\\':
                    in_string = not in_string
            if not in_string:
                if chunk[i] == "(":
                    open_parens += 1
                elif chunk[i] == ")":
                    open_parens -= 1
                    if open_parens == 0:
                        params_end = i
                        break

        if params_end == -1:
            return properties, required

        params_str = chunk[:params_end]
        params_list = []
        curr_param = []
        nest = 0
        for char in params_str:
            if char in "([<": nest += 1
            elif char in ")]>": nest -= 1
            elif char == "," and nest == 0:
                params_list.append("".join(curr_param))
                curr_param = []
                continue
            curr_param.append(char)
        if curr_param:
            params_list.append("".join(curr_param))

        for p in params_list:
            p = p.strip()
            if not p:
                continue
            has_default = "=" in p
            is_nullable = "?" in p or "= null" in p.lower() or "=null" in p.lower()

            parts = p.split("=")
            decl = parts[0].strip()

            param_name = ""
            type_raw = ""

            decl_parts = [dp for dp in decl.split() if dp.strip()]
            for dp in decl_parts:
                if dp.startswith("$"):
                    param_name = dp.lstrip("$")
                elif not dp.startswith("#["):
                    type_raw = dp

            if not param_name:
                continue

            doc_info = doc_params.get(param_name, {})
            if not type_raw and doc_info.get("type"):
                type_raw = doc_info["type"]

            final_type = map_php_type(type_raw) if type_raw else "string"
            prop_schema: dict[str, Any] = {"type": final_type}
            if doc_info.get("description"):
                prop_schema["description"] = doc_info["description"]

            properties[param_name] = prop_schema
            if not has_default and not is_nullable:
                required.append(param_name)

        return properties, required

    # 1. Attributes on methods/functions: #[McpTool], #[Tool], #[AsTool], #[AsMcpTool]
    attr_regex = re.compile(
        r"#\[\s*(?:McpTool|Tool|AsTool|AsMcpTool)\s*(?:\(\s*(.*?)\s*\))?\s*\](?:\s|/\*.*?\*/|//[^\n]*)*?(?:public\s+|private\s+|protected\s+)?(?:static\s+)?function\s+([a-zA-Z0-9_]+)\s*\(",
        re.DOTALL
    )
    for match in attr_regex.finditer(code):
        attr_content = match.group(1) or ""
        func_name = match.group(2)

        name = ""
        desc = ""

        # Preceding docblock
        preceding = code[max(0, match.start() - 600):match.start()]
        docblock_m = re.search(r"/\*\*(.*?)\*/\s*$", preceding, re.DOTALL)
        doc_desc, doc_params = ("", {})
        if docblock_m:
            doc_desc, doc_params = extract_docblock_params(docblock_m.group(1))

        name_m = re.search(r"(?:name\s*:\s*)?['\"]([^'\"]+)['\"]", attr_content)
        if name_m:
            name = name_m.group(1)
        else:
            name = func_name

        desc_m = re.search(r"description\s*:\s*['\"]([^'\"]+)['\"]", attr_content)
        if desc_m:
            desc = desc_m.group(1)
        else:
            pos_m = re.search(r"['\"][^'\"]+['\"]\s*,\s*(?:description\s*:\s*)?['\"]([^'\"]+)['\"]", attr_content)
            if pos_m:
                desc = pos_m.group(1)
            elif doc_desc:
                desc = doc_desc

        params_start = match.end()
        chunk = code[params_start : params_start + 1200]
        properties, required = parse_php_params_chunk(chunk, doc_params)

        add_tool(name, desc, properties, required)

    # 2. Class-based tools & Invokable Classes (__invoke)
    class_regex = re.compile(
        r"(?:/\*\*(.*?)\*/\s*)?(?:#\[\s*(?:AsTool|AsMcpTool|McpTool|Tool)\s*(?:\(\s*(.*?)\s*\))?\s*\]\s*)?class\s+([a-zA-Z0-9_]+)\s*(?:extends\s+[a-zA-Z0-9_\\]*Tool|implements\s+[a-zA-Z0-9_\\]*(?:McpToolInterface|ToolInterface)|extends\s+[a-zA-Z0-9_\\]*McpTool)?[^{]*\{",
        re.DOTALL
    )
    for class_match in class_regex.finditer(code):
        class_doc = class_match.group(1) or ""
        class_attr = class_match.group(2) or ""
        class_name = class_match.group(3)

        start_idx = class_match.end()
        body = ""
        open_braces = 1
        for i in range(start_idx, len(code)):
            if code[i] == "{": open_braces += 1
            elif code[i] == "}":
                open_braces -= 1
                if open_braces == 0:
                    body = code[start_idx:i]
                    break

        name = ""
        desc = ""
        properties_c: dict[str, Any] = {}
        required_c: list[str] = []

        if class_attr:
            attr_name_m = re.search(r"(?:name\s*:\s*)?['\"]([^'\"]+)['\"]", class_attr)
            if attr_name_m:
                name = attr_name_m.group(1)
            attr_desc_m = re.search(r"description\s*:\s*['\"]([^'\"]+)['\"]", class_attr)
            if attr_desc_m:
                desc = attr_desc_m.group(1)

        name_m = re.search(r"(?:protected|public)\s+(?:string\s+)?\$name\s*=\s*['\"]([^'\"]+)['\"]", body)
        if name_m:
            name = name_m.group(1)
        elif not name:
            name_func = re.search(r"public\s+function\s+getName\s*\(\)\s*(?::\s*string)?\s*\{\s*return\s*['\"]([^'\"]+)['\"];", body, re.DOTALL)
            if name_func:
                name = name_func.group(1)

        desc_m = re.search(r"(?:protected|public)\s+(?:string\s+)?\$description\s*=\s*['\"]([^'\"]+)['\"]", body)
        if desc_m:
            desc = desc_m.group(1)

        doc_desc, doc_params = extract_docblock_params(class_doc)
        if not desc and doc_desc:
            desc = doc_desc

        if not desc:
            inner_doc_m = re.search(r"/\*\*(.*?)\*/", body, re.DOTALL)
            if inner_doc_m:
                inner_desc, _ = extract_docblock_params(inner_doc_m.group(1))
                if inner_desc:
                    desc = inner_desc

        # Check for invokable __invoke(...) method
        invoke_match = re.search(
            r"(?:/\*\*(.*?)\*/\s*)?public\s+function\s+__invoke\s*\(",
            body,
            re.DOTALL
        )
        if invoke_match:
            invoke_doc = invoke_match.group(1) or ""
            invoke_doc_desc, invoke_doc_params = extract_docblock_params(invoke_doc)
            if not desc and invoke_doc_desc:
                desc = invoke_doc_desc
            merged_doc_params = {**doc_params, **invoke_doc_params}
            invoke_start = invoke_match.end()
            properties_c, required_c = parse_php_params_chunk(body[invoke_start : invoke_start + 1200], merged_doc_params)
            if not name:
                # Convert ClassName to snake_case
                s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', class_name)
                name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        if not name:
            continue

        add_tool(name, desc, properties_c, required_c)

    # 3. Method registration: $server->registerTool('name', ...)
    reg_regex = re.compile(
        r"\$(?:server|mcp)->registerTool\s*\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*(?:function\s*\(.*?\)|['\"][^'\"]*['\"]))?",
        re.DOTALL
    )
    for reg_match in reg_regex.finditer(code):
        name = reg_match.group(1)
        desc = name
        properties_r: dict[str, dict[str, str]] = {}
        required_r: list[str] = []
        add_tool(name, desc, properties_r, required_r)

    return extracted


