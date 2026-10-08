"""Static AST Code Parsers for FastMCP Python and TypeScript/JavaScript SDKs."""

from __future__ import annotations

import ast
import re
from typing import Any


def _python_type_to_schema_type(annotation_node: ast.expr | None) -> str:
    """Convert Python AST type annotation to JSON schema type string."""
    if annotation_node is None:
        return "string"
    if isinstance(annotation_node, ast.Name):
        id_str = annotation_node.id.lower()
        if id_str in ("str", "text"):
            return "string"
        if id_str in ("int", "integer"):
            return "integer"
        if id_str in ("float", "number"):
            return "number"
        if id_str in ("bool", "boolean"):
            return "boolean"
        if id_str in ("list", "sequence", "tuple", "set"):
            return "array"
        if id_str in ("dict", "mapping", "object"):
            return "object"
    elif isinstance(annotation_node, ast.Subscript):
        if isinstance(annotation_node.value, ast.Name):
            id_str = annotation_node.value.id.lower()
            if id_str in ("list", "sequence", "set", "iterable"):
                return "array"
            if id_str in ("dict", "mapping"):
                return "object"
            if id_str in ("optional", "union"):
                # Inspect slice argument
                slice_val = annotation_node.slice
                if isinstance(slice_val, ast.Name):
                    return _python_type_to_schema_type(slice_val)
    elif isinstance(annotation_node, ast.Constant):
        val = str(annotation_node.value).lower()
        if val in ("str", "int", "float", "bool", "list", "dict"):
            return _python_type_to_schema_type(ast.Name(id=val))
    return "string"


class FastMcpAstVisitor(ast.NodeVisitor):
    """AST Visitor extracting @mcp.tool() and @fastmcp.tool() decorated functions."""

    def __init__(self) -> None:
        self.extracted_tools: list[dict[str, Any]] = []
        self.pydantic_models: dict[str, dict[str, Any]] = {}

    def visit_Module(self, node: ast.Module) -> None:
        """First pass to find Pydantic models."""
        for stmt in node.body:
            if isinstance(stmt, ast.ClassDef):
                is_pydantic = False
                for base in stmt.bases:
                    if isinstance(base, ast.Name) and base.id == "BaseModel":
                        is_pydantic = True
                        break
                    elif isinstance(base, ast.Attribute) and base.attr == "BaseModel":
                        is_pydantic = True
                        break
                
                fields: dict[str, dict[str, str]] = {}
                required: list[str] = []
                has_annotations = False
                
                for item in stmt.body:
                    if isinstance(item, ast.AnnAssign):
                        has_annotations = True
                        if isinstance(item.target, ast.Name):
                            field_name = item.target.id
                            schema_type = _python_type_to_schema_type(item.annotation)
                            fields[field_name] = {"type": schema_type}
                            # Check if it has a default value
                            if item.value is None:
                                required.append(field_name)
                
                if is_pydantic or has_annotations:
                    self.pydantic_models[stmt.name] = {
                        "properties": fields,
                        "required": required
                    }
                    
        self.generic_visit(node)

    @staticmethod
    def _is_tool_decorator(decorator: ast.expr) -> tuple[bool, str | None, str | None]:
        """Check if decorator matches @mcp.tool, @app.tool, @fastmcp.tool, or @tool()."""
        is_tool = False
        custom_name = None
        custom_desc = None

        if isinstance(decorator, ast.Call):
            func_node = decorator.func
            # Extract keywords like name="...", description="..."
            for kw in decorator.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    custom_name = kw.value.value
                elif kw.arg == "description" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    custom_desc = kw.value.value
        else:
            func_node = decorator

        if isinstance(func_node, ast.Attribute):
            if func_node.attr == "tool":
                is_tool = True
        elif isinstance(func_node, ast.Name):
            if func_node.id in ("tool", "mcp_tool"):
                is_tool = True

        return is_tool, custom_name, custom_desc

    def visit_Call(self, node: ast.Call) -> None:
        """Handle low-level Tool(name="...", description="...", inputSchema={...}) or types.Tool(...)."""
        is_tool_call = False
        if isinstance(node.func, ast.Name) and node.func.id in ("Tool", "types_Tool"):
            is_tool_call = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "Tool":
            is_tool_call = True

        if is_tool_call:
            name = None
            desc = ""
            properties: dict[str, dict[str, str]] = {}
            required: list[str] = []

            for kw in node.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    name = kw.value.value
                elif kw.arg == "description" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    desc = kw.value.value
                elif kw.arg == "inputSchema" and isinstance(kw.value, ast.Dict):
                    for k, v in zip(kw.value.keys, kw.value.values):
                        if isinstance(k, ast.Constant) and k.value == "properties" and isinstance(v, ast.Dict):
                            for pk in v.keys:
                                if isinstance(pk, ast.Constant) and isinstance(pk.value, str):
                                    properties[pk.value] = {"type": "string"}
                        elif isinstance(k, ast.Constant) and k.value == "required" and isinstance(v, ast.List):
                            for item in v.elts:
                                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                                    required.append(item.value)

            if name and not any(t["name"] == name for t in self.extracted_tools):
                self.extracted_tools.append({
                    "name": name,
                    "description": desc or name,
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": sorted(required),
                    },
                    "property_keys": sorted(properties.keys()),
                    "required_keys": sorted(required),
                })

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node)
        self.generic_visit(node)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        tool_found = False
        extracted_name = None
        extracted_desc = None

        for dec in node.decorator_list:
            is_tool, c_name, c_desc = self._is_tool_decorator(dec)
            if is_tool:
                tool_found = True
                if c_name:
                    extracted_name = c_name
                if c_desc:
                    extracted_desc = c_desc

        if not tool_found:
            return

        tool_name = extracted_name or node.name
        docstring = ast.get_docstring(node) or ""
        tool_desc = extracted_desc or docstring.strip().split("\n")[0] or tool_name

        # Extract arguments and inputSchema
        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        # Process function positional arguments (excluding 'self', 'cls', 'ctx', 'context')
        for arg in node.args.args:
            arg_name = arg.arg
            if arg_name in ("self", "cls", "ctx", "context"):
                continue

            is_model = False
            if getattr(arg, "annotation", None) and isinstance(arg.annotation, ast.Name):
                type_name = arg.annotation.id
                if type_name in self.pydantic_models:
                    model_info = self.pydantic_models[type_name]
                    properties.update(model_info["properties"])
                    required.extend(model_info["required"])
                    is_model = True

            if not is_model:
                schema_type = _python_type_to_schema_type(arg.annotation)
                properties[arg_name] = {"type": schema_type}

                # Check if arg has a default value (non-required)
                num_defaults = len(node.args.defaults)
                args_without_defaults = len(node.args.args) - num_defaults
                arg_idx = node.args.args.index(arg)
                if arg_idx < args_without_defaults:
                    required.append(arg_name)

        # Process keyword-only arguments
        for idx, kwarg in enumerate(node.args.kwonlyargs):
            kwarg_name = kwarg.arg
            if kwarg_name in ("self", "cls", "ctx", "context"):
                continue

            is_model = False
            if getattr(kwarg, "annotation", None) and isinstance(kwarg.annotation, ast.Name):
                type_name = kwarg.annotation.id
                if type_name in self.pydantic_models:
                    model_info = self.pydantic_models[type_name]
                    properties.update(model_info["properties"])
                    required.extend(model_info["required"])
                    is_model = True

            if not is_model:
                schema_type = _python_type_to_schema_type(kwarg.annotation)
                properties[kwarg_name] = {"type": schema_type}
                if idx >= len(node.args.kw_defaults) or node.args.kw_defaults[idx] is None:
                    required.append(kwarg_name)

        input_schema = {
            "type": "object",
            "properties": properties,
            "required": sorted(required),
        }

        self.extracted_tools.append({
            "name": tool_name,
            "description": tool_desc,
            "inputSchema": input_schema,
            "property_keys": sorted(properties.keys()),
            "required_keys": sorted(required),
        })


def parse_python_mcp_ast(code: str) -> list[dict[str, Any]]:
    """Parse Python source code and return statically extracted MCP tool definitions."""
    try:
        tree = ast.parse(code)
    except Exception:
        return []

    visitor = FastMcpAstVisitor()
    visitor.visit(tree)
    return visitor.extracted_tools


def parse_typescript_mcp_ast(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from TypeScript/JavaScript source code."""
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
            },
            "property_keys": sorted(props.keys()),
            "required_keys": sorted(req),
        })

    # Pattern 1: server.tool("name", "desc", { schema }, handler) or server.tool("name", { schema }, handler)
    tool_call_regex = re.compile(
        r'(?:server|mcp|app)\.tool\s*\(\s*["\']([^"\']+)["\']\s*,\s*(?:["\']([^"\']+)["\']\s*,\s*)?(?:z\.object\s*\(\s*\{([^}]*)\}\s*\)|\{([^}]*)\})',
        re.DOTALL | re.MULTILINE,
    )

    for match in tool_call_regex.finditer(code):
        tool_name = match.group(1)
        tool_desc = match.group(2) or tool_name
        zod_body = match.group(3) or match.group(4) or ""

        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        if zod_body:
            # Parse property key and type (e.g., query: z.string().describe(...))
            prop_lines = zod_body.split(",")
            for line in prop_lines:
                p_match = re.search(r'([a-zA-Z0-9_$]+)\s*:\s*z\.([a-zA-Z0-9]+)', line)
                if p_match:
                    p_name = p_match.group(1)
                    p_ztype = p_match.group(2).lower()
                    stype = "string"
                    if p_ztype in ("number", "int", "float"):
                        stype = "number"
                    elif p_ztype in ("boolean", "bool"):
                        stype = "boolean"
                    elif p_ztype in ("array", "list"):
                        stype = "array"
                    elif p_ztype in ("object", "record"):
                        stype = "object"
                    properties[p_name] = {"type": stype}
                    if "optional" not in line:
                        required.append(p_name)

        add_tool(tool_name, tool_desc, properties, required)

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
        chunk = code[start_idx : start_idx + 1500]
        desc_m = re.search(r'description\s*:\s*["\']([^"\']+)["\']', chunk)
        t_desc = desc_m.group(1) if desc_m else t_name
        properties = {}
        required = []
        # We need a safe boundary for inputSchema properties, usually ending at the next `}` or `},` or `});`
        # Using a reluctant quantifier up to the next structural brace or end of object literal.
        # Alternatively, search only within `inputSchema: { ... }` where `...` doesn't contain the start of the next tool or closing of the current registerTool.
        schema_m = re.search(r'inputSchema\s*:\s*\{([^{}]*?(?:\{[^{}]*\}[^{}]*?)*)\}', chunk, re.DOTALL)
        if schema_m:
            schema_chunk = schema_m.group(1)
            # Find zod definitions like `repo_name: z.string()`
            for pm in re.finditer(r'([a-zA-Z0-9_$]+)\s*:\s*z\.([a-zA-Z0-9]+)', schema_chunk):
                pname = pm.group(1)
                ptype = pm.group(2).lower()
                
                stype = "string"
                if ptype in ("number", "int", "float"):
                    stype = "number"
                elif ptype in ("boolean", "bool"):
                    stype = "boolean"
                elif ptype in ("array", "list"):
                    stype = "array"
                elif ptype in ("object", "record"):
                    stype = "object"
                    
                properties[pname] = {"type": stype}
                
                # Check if it has .optional() following it on the same line or before next property
                # simple heuristic: just check the line containing the match
                line_match = re.search(rf'{pname}\s*:\s*z\.[^,]+', schema_chunk)
                if line_match and "optional" not in line_match.group(0):
                    required.append(pname)

        add_tool(t_name, t_desc, properties, required)

    # Pattern 3: Object literal array declaration [{ name: "...", description: "...", inputSchema: ... }]
    # E.g. tools = [{ name: "read_file", ... }]
    obj_literal_regex = re.compile(
        r'\{\s*(?:[^{}]*?\bname\s*:\s*[\'"]([a-zA-Z0-9_\-]+)[\'"][^{}]*?\bdescription\s*:\s*([\'"][^,;\}]+[\'"])|[^{}]*?\bdescription\s*:\s*([\'"][^,;\}]+[\'"][^{}]*?\bname\s*:\s*[\'"]([a-zA-Z0-9_\-]+)[\'"]))',
        re.MULTILINE,
    )
    for match in obj_literal_regex.finditer(code):
        t_name = match.group(1) or match.group(4)
        raw_desc = match.group(2) or match.group(3) or ""
        cleaned_desc = re.sub(r'[\'"]\s*\+\s*[\'"]', '', raw_desc)
        t_desc = re.sub(r'\s+', ' ', cleaned_desc).strip('\'" \n') or t_name
        
        # Look ahead for inputSchema to get properties and required
        chunk = code[match.start():match.start() + 1500]
        properties = {}
        required = []
        
        # Simple extraction of properties and required fields within the chunk
        # We need a safe boundary for properties block to avoid consuming other tools' schemas.
        # Find the start of the `properties:` block for this tool. 
        # By searching only the first properties block within the object literal representing the tool.
        # Let's extract up to the end of properties block by matching nested structures up to depth 1 or looking for next keyword like required
        
        # Limit chunk to just this tool by stopping at the next 'name:' or next array element boundary
        schema_m = re.search(r'inputSchema\s*:\s*\{(.*)', chunk, re.DOTALL)
        if schema_m:
            schema_chunk = schema_m.group(1)
            
            # Prevent greediness by cutting off at the start of the next tool (usually "name:")
            next_name_idx = schema_chunk.find('name:')
            if next_name_idx != -1:
                schema_chunk = schema_chunk[:next_name_idx]
            
            # Find innermost { ... } blocks that contain type: "..." within schema chunk
            for p_match in re.finditer(r'([a-zA-Z0-9_$]+)\s*:\s*\{([^{}]+)\}', schema_chunk, re.DOTALL):
                p_name = p_match.group(1)
                p_body = p_match.group(2)
                t_match = re.search(r'type\s*:\s*["\']([^"\']+)["\']', p_body)
                if t_match:
                    properties[p_name] = {"type": t_match.group(1)}
            
            # Extract required array from schema chunk
            req_match = re.search(r'required\s*:\s*\[([^\]]*?)\]', schema_chunk, re.DOTALL)
            if req_match:
                req_str = req_match.group(1)
                for req_item in req_str.split(","):
                    req_item_clean = req_item.strip().strip('"\' \n\t')
                    if req_item_clean:
                        required.append(req_item_clean)
            
        add_tool(t_name, t_desc, properties, required)

    return extracted


def parse_golang_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from Golang source code."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for match in re.finditer(r'mcp\.NewTool\s*\(\s*["\']([^"\']+)["\']', code):
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
        desc_match = re.search(r'mcp\.WithDescription\s*\(\s*["\']([^"\']+)["\']\s*\)', body)
        if desc_match:
            desc = desc_match.group(1)
            
        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []
        
        param_regex = re.compile(
            r'mcp\.With(String|Number|Boolean|Object|Array|Float|Int)\s*\(\s*["\']([^"\']+)["\']\s*(.*?)\)',
            re.DOTALL
        )
        for p_match in param_regex.finditer(body):
            ptype_raw = p_match.group(1).lower()
            pname = p_match.group(2)
            p_args = p_match.group(3)
            
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
            if "mcp.Required" in p_args or "Required:" in p_args:
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


def parse_mcp_source_code(code: str, language: str | None = None) -> list[dict[str, Any]]:
    """Parse MCP source code and return extracted tool signatures."""
    if language:
        lang = language.lower()
        if lang in ("python", "py"):
            return parse_python_mcp_ast(code)
        elif lang in ("typescript", "ts", "javascript", "js", "mjs"):
            return parse_typescript_mcp_ast(code)
        elif lang in ("go", "golang"):
            return parse_golang_mcp_code(code)
        elif lang in ("rust", "rs"):
            return parse_rust_mcp_code(code)
            
    # Heuristics if language is unknown or not matched
    if code.startswith("package ") or "mcp.NewTool" in code:
        res = parse_golang_mcp_code(code)
        if res: return res
        
    if "fn main()" in code or "use rmcp" in code or "#[mcp_tool" in code:
        res = parse_rust_mcp_code(code)
        if res: return res

    # Try python and ts fallbacks
    py_res = parse_python_mcp_ast(code)
    if py_res: return py_res
    
    return parse_typescript_mcp_ast(code)
