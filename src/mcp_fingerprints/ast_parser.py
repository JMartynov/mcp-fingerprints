"""Static AST Code Parsers for FastMCP Python and TypeScript/JavaScript SDKs."""

from __future__ import annotations

import ast
import logging
import re
from typing import Any

logger = logging.getLogger("mcp_fingerprints.ast_parser")


class AstBundleResult(list):
    """Result list of extracted MCP tools with bundle-level properties for prompts, resources, and env vars."""

    def __init__(
        self,
        tools: list[dict[str, Any]] | None = None,
        prompts: list[dict[str, Any]] | None = None,
        resources: list[dict[str, Any]] | None = None,
        env_vars: set[str] | list[str] | tuple[str, ...] | None = None,
        dependencies: list[str] | None = None,
    ) -> None:
        raw_tools = list(tools or [])
        super().__init__(raw_tools)
        self.tools = raw_tools
        self.prompts = list(prompts or [])
        self.resources = list(resources or [])
        self.env_vars = tuple(sorted(set(env_vars or ())))
        self.required_env_vars = self.env_vars
        self.dependencies = list(dependencies or [])

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            if key == "tools":
                return self.tools
            if key == "prompts":
                return self.prompts
            if key == "resources":
                return self.resources
            if key in ("env_vars", "required_env_vars"):
                return list(self.env_vars)
            if key == "dependencies":
                return self.dependencies
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "tools":
            return self.tools
        if key == "prompts":
            return self.prompts
        if key == "resources":
            return self.resources
        if key in ("env_vars", "required_env_vars"):
            return list(self.env_vars)
        if key == "dependencies":
            return self.dependencies
        return default


def _extract_param_descriptions_from_docstring(docstring: str) -> dict[str, str]:
    """Parse parameter descriptions from Google, Sphinx, or NumPy docstring conventions."""
    if not docstring or not docstring.strip():
        return {}
    descriptions: dict[str, str] = {}
    lines = docstring.split("\n")

    # 1. Sphinx style: :param <name>: <desc> or :param <type> <name>: <desc>
    for line in lines:
        m = re.search(r":param\s+(?:[a-zA-Z0-9_\[\],\s]+\s+)?([a-zA-Z0-9_]+)\s*:\s*(.+)", line.strip())
        if m:
            descriptions[m.group(1)] = m.group(2).strip()

    # 2. Google style:
    # Args: / Arguments: / Parameters:
    in_google_args = False
    current_arg = None
    arg_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if lower in ("args:", "arguments:", "parameters:"):
            in_google_args = True
            current_arg = None
            continue
        if in_google_args:
            if stripped and not line.startswith((" ", "\t")):
                in_google_args = False
                if current_arg and arg_lines:
                    descriptions.setdefault(current_arg, " ".join(arg_lines).strip())
                current_arg = None
                arg_lines = []
                continue

            m = re.match(r"^\s*([a-zA-Z0-9_]+)(?:\s*\([^)]*\))?\s*:\s*(.*)", line)
            if m:
                if current_arg and arg_lines:
                    descriptions.setdefault(current_arg, " ".join(arg_lines).strip())
                current_arg = m.group(1)
                arg_lines = [m.group(2).strip()] if m.group(2).strip() else []
            elif current_arg and stripped:
                arg_lines.append(stripped)

    if current_arg and arg_lines:
        descriptions.setdefault(current_arg, " ".join(arg_lines).strip())

    # 3. NumPy style:
    # Parameters
    # ----------
    in_numpy_params = False
    numpy_header_seen = False
    curr_np_arg = None
    curr_np_lines: list[str] = []

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.lower() == "parameters" and idx + 1 < len(lines) and lines[idx + 1].strip().startswith("---"):
            in_numpy_params = True
            numpy_header_seen = True
            continue
        if numpy_header_seen and line.strip().startswith("---"):
            numpy_header_seen = False
            continue
        if in_numpy_params:
            if stripped and not line.startswith((" ", "\t")) and ":" not in stripped:
                in_numpy_params = False
                if curr_np_arg and curr_np_lines:
                    descriptions.setdefault(curr_np_arg, " ".join(curr_np_lines).strip())
                curr_np_arg = None
                curr_np_lines = []
                continue

            m = re.match(r"^\s*([a-zA-Z0-9_]+)\s*:\s*(.*)", line)
            if m:
                if curr_np_arg and curr_np_lines:
                    descriptions.setdefault(curr_np_arg, " ".join(curr_np_lines).strip())
                curr_np_arg = m.group(1)
                curr_np_lines = []
            elif curr_np_arg and stripped:
                curr_np_lines.append(stripped)

    if curr_np_arg and curr_np_lines:
        descriptions.setdefault(curr_np_arg, " ".join(curr_np_lines).strip())

    return descriptions


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
        val_node = annotation_node.value
        val_id = ""
        if isinstance(val_node, ast.Name):
            val_id = val_node.id.lower()
        elif isinstance(val_node, ast.Attribute):
            val_id = val_node.attr.lower()

        if val_id in ("list", "sequence", "set", "iterable"):
            return "array"
        if val_id in ("dict", "mapping"):
            return "object"
        if val_id in ("optional", "union"):
            slice_val = annotation_node.slice
            if isinstance(slice_val, ast.Tuple) and slice_val.elts:
                non_none = [e for e in slice_val.elts if not (isinstance(e, ast.Constant) and e.value is None)]
                if non_none:
                    return _python_type_to_schema_type(non_none[0])
            elif isinstance(slice_val, ast.expr):
                return _python_type_to_schema_type(slice_val)
        if val_id == "annotated":
            slice_val = annotation_node.slice
            if isinstance(slice_val, ast.Tuple) and slice_val.elts:
                return _python_type_to_schema_type(slice_val.elts[0])
            elif isinstance(slice_val, ast.expr):
                return _python_type_to_schema_type(slice_val)
        if val_id == "literal":
            return "string"
    elif isinstance(annotation_node, ast.Constant):
        val = str(annotation_node.value).lower()
        if val in ("str", "int", "float", "bool", "list", "dict"):
            return _python_type_to_schema_type(ast.Name(id=val))
    return "string"


def _extract_field_details(
    annotation_node: ast.expr | None,
    default_node: ast.expr | None = None,
) -> dict[str, Any]:
    """Extract schema type, description, default, enum, and items type from AST annotation and default nodes."""
    res: dict[str, Any] = {
        "type": "string",
        "description": None,
        "default": None,
        "has_default": False,
        "enum": None,
        "items": None,
    }

    # 1. Inspect default node
    if default_node is not None:
        if isinstance(default_node, ast.Constant):
            res["default"] = default_node.value
            res["has_default"] = True
        elif isinstance(default_node, ast.List):
            res["default"] = [e.value for e in default_node.elts if isinstance(e, ast.Constant)]
            res["has_default"] = True
        elif isinstance(default_node, ast.Dict):
            res["default"] = {}
            res["has_default"] = True
        elif isinstance(default_node, (ast.Tuple, ast.Set)):
            res["default"] = []
            res["has_default"] = True
        elif isinstance(default_node, ast.Call):
            func_name = getattr(default_node.func, "id", None) or getattr(default_node.func, "attr", None)
            if func_name == "Field":
                if default_node.args:
                    first_arg = default_node.args[0]
                    if isinstance(first_arg, ast.Constant) and first_arg.value is not Ellipsis:
                        res["default"] = first_arg.value
                        res["has_default"] = True
                    elif isinstance(first_arg, ast.Constant) and first_arg.value is Ellipsis:
                        res["has_default"] = False
                for kw in default_node.keywords:
                    if kw.arg == "description" and isinstance(kw.value, ast.Constant):
                        res["description"] = kw.value.value
                    elif kw.arg == "default" and isinstance(kw.value, ast.Constant):
                        if kw.value.value is not Ellipsis:
                            res["default"] = kw.value.value
                            res["has_default"] = True

    # 2. Inspect annotation node
    if annotation_node is not None:
        res["type"] = _python_type_to_schema_type(annotation_node)

        if isinstance(annotation_node, ast.Subscript):
            val_id = getattr(annotation_node.value, "id", None) or getattr(annotation_node.value, "attr", None)
            if val_id == "Literal":
                res["type"] = "string"
                slice_node = annotation_node.slice
                enum_vals: list[Any] = []
                if isinstance(slice_node, ast.Tuple):
                    for elt in slice_node.elts:
                        if isinstance(elt, ast.Constant):
                            enum_vals.append(elt.value)
                elif isinstance(slice_node, ast.Constant):
                    enum_vals.append(slice_node.value)
                if enum_vals:
                    res["enum"] = tuple(enum_vals)

            elif val_id in ("list", "List", "sequence", "Sequence"):
                res["type"] = "array"
                slice_node = annotation_node.slice
                if isinstance(slice_node, ast.expr):
                    item_type = _python_type_to_schema_type(slice_node)
                    res["items"] = {"type": item_type}

            elif val_id == "Annotated":
                slice_node = annotation_node.slice
                if isinstance(slice_node, ast.Tuple) and slice_node.elts:
                    res["type"] = _python_type_to_schema_type(slice_node.elts[0])
                    for extra in slice_node.elts[1:]:
                        if isinstance(extra, ast.Call):
                            extra_func = getattr(extra.func, "id", None) or getattr(extra.func, "attr", None)
                            if extra_func == "Field":
                                for kw in extra.keywords:
                                    if kw.arg == "description" and isinstance(kw.value, ast.Constant):
                                        res["description"] = kw.value.value
                                    elif kw.arg == "default" and isinstance(kw.value, ast.Constant):
                                        if kw.value.value is not Ellipsis:
                                            res["default"] = kw.value.value
                                            res["has_default"] = True

    return res


class FastMcpAstVisitor(ast.NodeVisitor):
    """AST Visitor extracting tools, prompts, resources, environment variables, and Pydantic models."""

    def __init__(self, pydantic_models: dict[str, dict[str, Any]] | None = None) -> None:
        self.extracted_tools: list[dict[str, Any]] = []
        self.constants: dict[str, Any] = {}
        self.extracted_prompts: list[dict[str, Any]] = []
        self.extracted_resources: list[dict[str, Any]] = []
        self.extracted_env_vars: set[str] = set()
        self.pydantic_models: dict[str, dict[str, Any]] = dict(pydantic_models or {})
        self._current_module_body: list[ast.stmt] = []


    def visit_Module(self, node: ast.Module) -> None:
        self._current_module_body = node.body
        self._current_module_node = node
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                self.constants[target.id] = node.value.value
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:

        """Capture os.environ['VAR']."""
        val = node.value
        if (isinstance(val, ast.Attribute) and val.attr == "environ") or (isinstance(val, ast.Name) and val.id == "environ"):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                self.extracted_env_vars.add(node.slice.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Capture os.getenv('VAR') or os.environ.get('VAR') and low-level Tool definitions."""
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr == "getenv" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                self.extracted_env_vars.add(node.args[0].value)
            elif func.attr == "get" and isinstance(func.value, (ast.Attribute, ast.Name)) and getattr(func.value, "attr", getattr(func.value, "id", None)) == "environ":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    self.extracted_env_vars.add(node.args[0].value)
        elif isinstance(func, ast.Name):
            if func.id == "getenv" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                self.extracted_env_vars.add(node.args[0].value)

        # Handle low-level Tool(name="...", description="...", inputSchema={...})
        is_tool_call = False
        if isinstance(func, ast.Name) and func.id in ("Tool", "types_Tool", "MCPToolDefinition", "ToolDefinition", "MCPTool"):
            is_tool_call = True
        elif isinstance(func, ast.Attribute) and func.attr in ("Tool", "MCPToolDefinition", "ToolDefinition", "MCPTool"):
            is_tool_call = True
        elif isinstance(func, ast.Attribute) and func.attr == "add_tool" and isinstance(func.value, ast.Name) and func.value.id in ("mcp", "server"):
            is_tool_call = True

        if is_tool_call:
            name = None
            desc = ""
            properties: dict[str, Any] = {}
            required: list[str] = []

            # Extract from positional args for add_tool if necessary
            if getattr(func, "attr", None) == "add_tool" and node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Name):
                    name = first_arg.id
                    # Try to extract description from function docstring if we can find it in the same scope
                    # We might need to walk the tree to find it if it's not at the top level module body
                    for n in ast.walk(self._current_module_node) if hasattr(self, "_current_module_node") else []:
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
                            docstring = ast.get_docstring(n)
                            if docstring:
                                desc = docstring
                            break

            for kw in node.keywords:
                if kw.arg == "name":
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        name = kw.value.value
                    elif isinstance(kw.value, ast.Name) and kw.value.id in self.constants:
                        name = self.constants[kw.value.id]
                elif kw.arg == "description" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    desc = kw.value.value
                elif kw.arg == "inputSchema" and isinstance(kw.value, ast.Dict):
                    for k, v in zip(kw.value.keys, kw.value.values):
                        if isinstance(k, ast.Constant) and k.value == "properties" and isinstance(v, ast.Dict):
                            for pk, pv in zip(v.keys, v.values):
                                if isinstance(pk, ast.Constant) and isinstance(pk.value, str):
                                    properties[pk.value] = {"type": "string"}
                        elif isinstance(k, ast.Constant) and k.value == "required" and isinstance(v, ast.List):
                            for item in v.elts:
                                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                                    required.append(item.value)
                elif kw.arg == "parameters" and isinstance(kw.value, (ast.List, ast.Tuple)):
                    for elt in kw.value.elts:
                        if isinstance(elt, ast.Call) and isinstance(elt.func, ast.Name) and elt.func.id == "MCPToolParameter":
                            p_name = None
                            p_desc = ""
                            p_req = False
                            p_type = "string"
                            for pkw in elt.keywords:
                                if pkw.arg == "name" and isinstance(pkw.value, ast.Constant):
                                    p_name = pkw.value.value
                                elif pkw.arg == "description" and isinstance(pkw.value, ast.Constant):
                                    p_desc = pkw.value.value
                                elif pkw.arg == "required" and isinstance(pkw.value, ast.Constant):
                                    p_req = bool(pkw.value.value)
                                elif pkw.arg == "type" and isinstance(pkw.value, ast.Attribute):
                                    if pkw.value.attr == "STRING": p_type = "string"
                                    elif pkw.value.attr == "NUMBER": p_type = "number"
                                    elif pkw.value.attr == "BOOLEAN": p_type = "boolean"
                                    elif pkw.value.attr == "OBJECT": p_type = "object"
                                    elif pkw.value.attr == "ARRAY": p_type = "array"
                            if p_name:
                                properties[p_name] = {"type": p_type}
                                if p_desc:
                                    properties[p_name]["description"] = p_desc
                                if p_req:
                                    required.append(p_name)

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

    def visit_Module(self, node: ast.Module) -> None:
        """First pass to discover Pydantic models."""
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

                fields: dict[str, dict[str, Any]] = {}
                required: list[str] = []
                has_annotations = False

                for item in stmt.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        has_annotations = True
                        field_name = item.target.id
                        details = _extract_field_details(item.annotation, item.value)
                        field_schema: dict[str, Any] = {"type": details["type"]}
                        if details["description"]:
                            field_schema["description"] = details["description"]
                        if details["has_default"]:
                            field_schema["default"] = details["default"]
                        if details["enum"]:
                            field_schema["enum"] = list(details["enum"])
                        if details["items"]:
                            field_schema["items"] = details["items"]

                        fields[field_name] = field_schema
                        if not details["has_default"]:
                            required.append(field_name)

                if is_pydantic or has_annotations:
                    self.pydantic_models[stmt.name] = {
                        "properties": fields,
                        "required": required,
                    }

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        is_tool_class = False
        for base in node.bases:
            base_name = getattr(base, "id", getattr(base, "attr", None))
            if base_name in ("BaseTool", "Tool", "MCPToolDefinition", "ToolDefinition", "MCPTool"):
                is_tool_class = True
                break

        if is_tool_class:
            name = None
            desc = ""
            args_schema_name = None
            properties: dict[str, Any] = {}
            required: list[str] = []

            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            if target.id == "name":
                                if isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                                    name = item.value.value
                                elif isinstance(item.value, ast.Name) and item.value.id in self.constants:
                                    name = self.constants[item.value.id]
                            elif target.id == "description" and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                                desc = item.value.value
                            elif target.id == "args_schema" and isinstance(item.value, ast.Name):
                                args_schema_name = item.value.id
                            elif target.id == "parameters" and isinstance(item.value, (ast.List, ast.Tuple)):
                                for elt in item.value.elts:
                                    if isinstance(elt, ast.Call) and isinstance(elt.func, ast.Name) and elt.func.id == "MCPToolParameter":
                                        p_name = None
                                        p_desc = ""
                                        p_req = False
                                        p_type = "string"
                                        for pkw in elt.keywords:
                                            if pkw.arg == "name" and isinstance(pkw.value, ast.Constant):
                                                p_name = pkw.value.value
                                            elif pkw.arg == "description" and isinstance(pkw.value, ast.Constant):
                                                p_desc = pkw.value.value
                                            elif pkw.arg == "required" and isinstance(pkw.value, ast.Constant):
                                                p_req = bool(pkw.value.value)
                                            elif pkw.arg == "type" and isinstance(pkw.value, ast.Attribute):
                                                if pkw.value.attr == "STRING": p_type = "string"
                                                elif pkw.value.attr == "NUMBER": p_type = "number"
                                                elif pkw.value.attr == "BOOLEAN": p_type = "boolean"
                                                elif pkw.value.attr == "OBJECT": p_type = "object"
                                                elif pkw.value.attr == "ARRAY": p_type = "array"
                                        if p_name:
                                            properties[p_name] = {"type": p_type}
                                            if p_desc:
                                                properties[p_name]["description"] = p_desc
                                            if p_req:
                                                required.append(p_name)
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    if item.target.id == "name":
                        if isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                            name = item.value.value
                        elif isinstance(item.value, ast.Name) and item.value.id in self.constants:
                            name = self.constants[item.value.id]
                    elif item.target.id == "description" and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                        desc = item.value.value
                    elif item.target.id == "args_schema" and isinstance(item.value, ast.Name):
                        args_schema_name = item.value.id

            if not name:
                name = node.name

            if args_schema_name and args_schema_name in self.pydantic_models:
                model_info = self.pydantic_models[args_schema_name]
                properties.update(model_info.get("properties", {}))
                required.extend(model_info.get("required", []))

            if name and not any(t["name"] == name for t in self.extracted_tools):
                self.extracted_tools.append({
                    "name": name,
                    "description": desc or name,
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": sorted(list(set(required))),
                    },
                    "property_keys": sorted(properties.keys()),
                    "required_keys": sorted(list(set(required))),
                })

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node)
        self.generic_visit(node)

    def _process_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        docstring = ast.get_docstring(node) or ""
        doc_param_descs = _extract_param_descriptions_from_docstring(docstring)

        is_tool = False
        is_prompt = False
        is_resource = False
        custom_name = None
        custom_desc = None
        custom_uri = None
        tool_annotations: dict[str, bool] = {}

        for dec in node.decorator_list:
            func_node = dec.func if isinstance(dec, ast.Call) else dec
            dec_name = getattr(func_node, "attr", getattr(func_node, "id", None))

            # Check args/keywords for Call decorators
            if isinstance(dec, ast.Call):
                if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                    if dec_name == "resource":
                        custom_uri = dec.args[0].value
                    else:
                        custom_name = dec.args[0].value

                for kw in dec.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        custom_name = kw.value.value
                    elif kw.arg == "description" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        custom_desc = kw.value.value
                    elif kw.arg == "uri" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        custom_uri = kw.value.value
                    elif kw.arg == "annotations" and isinstance(kw.value, ast.Dict):
                        for k, v in zip(kw.value.keys, kw.value.values):
                            if isinstance(k, ast.Constant) and isinstance(k.value, str) and isinstance(v, ast.Constant):
                                tool_annotations[k.value] = bool(v.value)

            if dec_name in ("tool", "mcp_tool", "action", "command") or (isinstance(func_node, ast.Attribute) and func_node.attr in ("tool", "action", "command")):
                is_tool = True
            elif isinstance(func_node, ast.Attribute) and func_node.attr in ("tool", "register", "action", "command"):
                val_id = getattr(func_node.value, "id", "")
                if "tool" in val_id or "server" in val_id or "mcp" in val_id or "action" in val_id or "command" in val_id:
                    is_tool = True
            elif dec_name in ("prompt", "mcp_prompt") or (isinstance(func_node, ast.Attribute) and func_node.attr == "prompt"):
                is_prompt = True
            elif dec_name in ("resource", "mcp_resource") or (isinstance(func_node, ast.Attribute) and func_node.attr == "resource"):
                is_resource = True

        name = custom_name or node.name
        desc = custom_desc or (docstring.strip().split("\n")[0] if docstring else name)

        # 1. Handle Prompt Extraction
        if is_prompt:
            prompt_args = []
            for arg in node.args.args:
                if arg.arg in ("self", "cls", "ctx", "context"):
                    continue
                p_desc = doc_param_descs.get(arg.arg, "")
                prompt_args.append({
                    "name": arg.arg,
                    "description": p_desc,
                    "required": True,
                })
            self.extracted_prompts.append({
                "name": name,
                "description": desc,
                "arguments": prompt_args,
            })

        # 2. Handle Resource Extraction
        if is_resource:
            self.extracted_resources.append({
                "uri_template": custom_uri or f"resource://{name}",
                "name": name,
                "description": desc,
                "mime_type": "text/plain",
            })

        # 3. Handle Tool Extraction
        if is_tool:
            properties: dict[str, Any] = {}
            required: list[str] = []

            # Map positional defaults
            num_defaults = len(node.args.defaults)
            args_without_defaults = len(node.args.args) - num_defaults

            for idx, arg in enumerate(node.args.args):
                arg_name = arg.arg
                if arg_name in ("self", "cls", "ctx", "context"):
                    continue

                default_node = None
                if idx >= args_without_defaults:
                    default_node = node.args.defaults[idx - args_without_defaults]

                # Check if annotation references a Pydantic model
                if arg.annotation and isinstance(arg.annotation, ast.Name) and arg.annotation.id in self.pydantic_models:
                    model_info = self.pydantic_models[arg.annotation.id]
                    properties.update(model_info["properties"])
                    required.extend(model_info["required"])
                    continue

                details = _extract_field_details(arg.annotation, default_node)
                p_desc = details["description"] or doc_param_descs.get(arg_name)

                prop_dict: dict[str, Any] = {"type": details["type"]}
                if p_desc:
                    prop_dict["description"] = p_desc
                if details["has_default"]:
                    prop_dict["default"] = details["default"]
                if details["enum"]:
                    prop_dict["enum"] = list(details["enum"])
                if details["items"]:
                    prop_dict["items"] = details["items"]

                properties[arg_name] = prop_dict
                if not details["has_default"]:
                    required.append(arg_name)

            # Keyword-only arguments
            for idx, kwarg in enumerate(node.args.kwonlyargs):
                kwarg_name = kwarg.arg
                if kwarg_name in ("self", "cls", "ctx", "context"):
                    continue

                default_node = None
                if idx < len(node.args.kw_defaults):
                    default_node = node.args.kw_defaults[idx]

                if kwarg.annotation and isinstance(kwarg.annotation, ast.Name) and kwarg.annotation.id in self.pydantic_models:
                    model_info = self.pydantic_models[kwarg.annotation.id]
                    properties.update(model_info["properties"])
                    required.extend(model_info["required"])
                    continue

                details = _extract_field_details(kwarg.annotation, default_node)
                p_desc = details["description"] or doc_param_descs.get(kwarg_name)

                prop_dict = {"type": details["type"]}
                if p_desc:
                    prop_dict["description"] = p_desc
                if details["has_default"]:
                    prop_dict["default"] = details["default"]
                if details["enum"]:
                    prop_dict["enum"] = list(details["enum"])
                if details["items"]:
                    prop_dict["items"] = details["items"]

                properties[kwarg_name] = prop_dict
                if not details["has_default"]:
                    required.append(kwarg_name)

            self.extracted_tools.append({
                "name": name,
                "description": desc,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": sorted(required),
                },
                "property_keys": sorted(properties.keys()),
                "required_keys": sorted(required),
                "annotations": tool_annotations,
            })


def parse_python_mcp_ast_bundle(files: dict[str, str]) -> AstBundleResult:
    """Parse multiple Python source files simultaneously, resolving cross-file Pydantic models.

    Aggregates extracted tools, prompts, resources, and required environment variables across
    all files in the bundle.
    """
    aggregated_models: dict[str, dict[str, Any]] = {}
    parsed_trees: dict[str, ast.Module] = {}
    all_dependencies: list[str] = []

    # Pass 1: Parse AST and collect Pydantic models across all files
    for fname, code in files.items():
        # Check for PEP 723 script block
        script_match = re.search(r'(?sm)^# /// script\s*$(.*?)^# ///\s*$', code)
        if script_match:
            script_content = script_match.group(1)
            cleaned_content = re.sub(r'(?m)^#\s?', '', script_content)
            deps_match = re.search(r'dependencies\s*=\s*\[(.*?)\]\s*\n', cleaned_content, re.DOTALL)
            if deps_match:
                deps_str = deps_match.group(1)
                deps = re.findall(r'["\']([^"\']+)["\']', deps_str)
                for dep in deps:
                    if dep not in all_dependencies:
                        all_dependencies.append(dep)
        try:
            tree = ast.parse(code)
            parsed_trees[fname] = tree
            pre_visitor = FastMcpAstVisitor()
            pre_visitor.visit(tree)
            aggregated_models.update(pre_visitor.pydantic_models)
        except Exception as exc:
            logger.debug("Failed to parse AST for %s: %s", fname, exc)

    # Pass 2: Extract tools, prompts, resources, and env vars using aggregated models
    all_tools: list[dict[str, Any]] = []
    all_prompts: list[dict[str, Any]] = []
    all_resources: list[dict[str, Any]] = []
    all_env_vars: set[str] = set()
    seen_tool_names: set[str] = set()

    for fname, tree in parsed_trees.items():
        visitor = FastMcpAstVisitor(pydantic_models=aggregated_models)
        try:
            visitor.visit(tree)
            for t in visitor.extracted_tools:
                if t["name"] not in seen_tool_names:
                    seen_tool_names.add(t["name"])
                    all_tools.append(t)
            all_prompts.extend(visitor.extracted_prompts)
            all_resources.extend(visitor.extracted_resources)
            all_env_vars.update(visitor.extracted_env_vars)
        except Exception as exc:
            logger.debug("Failed visiting AST for %s: %s", fname, exc)

    return AstBundleResult(
        tools=all_tools,
        prompts=all_prompts,
        resources=all_resources,
        env_vars=all_env_vars,
        dependencies=all_dependencies,
    )


def parse_python_mcp_ast(code: str) -> AstBundleResult:
    """Parse Python source code and return statically extracted MCP tool definitions."""
    return parse_python_mcp_ast_bundle({"<stdin>": code})



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


def parse_golang_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from Golang source code."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()

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

    # Helper to parse arguments/properties from a chunk of swift code
    def parse_swift_args(args_chunk: str) -> tuple[dict[str, Any], list[str]]:
        props: dict[str, Any] = {}
        req: list[str] = []
        
        # Look for `let name: Type` or `var name: Type`
        var_regex = re.compile(
            r'(?:let|var)\s+([a-zA-Z0-9_]+)\s*:\s*([a-zA-Z0-9_\[\]\:\?\s<>\.]+?)(?=\n|;|,|$)'
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
                    schema_type = "object" # e.g. [String: Any]
                else:
                    schema_type = "array"
            elif ptype_clean == "String":
                schema_type = "string"
                
            props[pname] = {"type": schema_type}
            if not is_optional:
                req.append(pname)
                
        return props, req

    # Pattern 1: Structs conforming to Tool, MCPTool, ToolDefinition
    struct_regex = re.compile(
        r'struct\s+[a-zA-Z0-9_]+\s*:\s*(?:[a-zA-Z0-9_]+,\s*)*(?:Tool|MCPTool|ToolDefinition)(?:\s*,\s*[a-zA-Z0-9_]+)*\s*\{'
    )
    for struct_match in struct_regex.finditer(code):
        start_idx = struct_match.end()
        # Extract body of the struct roughly
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
                
            # Look for nested Arguments or Input structs
            args_struct_m = re.search(r'struct\s+(?:Arguments|Input)\s*:\s*(?:Codable|Decodable)\s*\{([^}]+)\}', body)
            props = {}
            req = []
            if args_struct_m:
                props, req = parse_swift_args(args_struct_m.group(1))
                
            if name:
                add_tool(name, desc, props, req)
                
    # Pattern 2: Macro/Attribute definitions @McpTool(name: "...", description: "...") or @Tool
    func_regex = re.compile(
        r'(@(?:McpTool|Tool)(?:\([^)]+\))?)\s*(?:public\s+|private\s+|internal\s+)?func\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)',
        re.MULTILINE
    )
    for func_match in func_regex.finditer(code):
        attr = func_match.group(1)
        name = func_match.group(2)
        args_str = func_match.group(3)
        desc = name
        
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
                if not arg_part: continue
                parts = arg_part.split(':')
                if len(parts) >= 2: # to handle dictionary types that might have inner colons
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

    return extracted


def parse_dotnet_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from C#/.NET source code."""
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

    # Pattern 1: Attributes on methods [McpTool("name", "description")], [McpFunction("name")], [McpServerTool(Name = "name")], or [KernelFunction]
    # Handle multiple attributes separated by comma or newlines within brackets, or consecutive brackets
    # e.g., [KernelFunction, Description("Multiply numbers")]

    # We find method declarations, then look backwards for attributes.
    # We also avoid matching `new McpTool(...)` by requiring a return type that isn't `new`.
    method_regex = re.compile(
        r"(?:public|private|protected|internal)?\s*(?:static\s+)?(?:async\s+)?(?:virtual\s+)?(?:override\s+)?(?:Task\s*<[^>]+>\s+|Task\s+|[\w<>\[\]\?]+\s+)([a-zA-Z0-9_]+)\s*\(",
        re.MULTILINE,
    )

    for method_match in method_regex.finditer(code):
        name = method_match.group(1)
        full_match = method_match.group(0).strip()
        if full_match.startswith("new "):
            continue
        start_idx = method_match.start()

        # Look at the previous 300 characters to find attributes
        prev_chunk = code[max(0, start_idx - 300) : start_idx]

        # Check if it has any tool attribute
        if not re.search(
            r"\[(?:McpTool|McpFunction|McpServerTool|KernelFunction)\b", prev_chunk
        ):
            continue

        desc = ""

        # Split by previous method closing brace if any, to isolate attributes
        if "}" in prev_chunk:
            prev_chunk = prev_chunk[prev_chunk.rfind("}") + 1 :]

        # Try to extract Name/Description from attributes
        attr_str = "".join(prev_chunk.splitlines())

        name_m = re.search(r'(?:Name|name)\s*=\s*["\']([^"\']+)["\']', attr_str)
        if name_m:
            name = name_m.group(1)

        desc_m = re.search(
            r'(?:Description|description)\s*\(\s*["\']([^"\']+)["\']\s*\)', attr_str
        )
        if desc_m:
            desc = desc_m.group(1)
        else:
            desc_m = re.search(
                r'(?:Description|description)\s*=\s*["\']([^"\']+)["\']', attr_str
            )
            if desc_m:
                desc = desc_m.group(1)

        # Look for [McpTool("name", "description")] or [McpFunction("name", "description")]
        mcp_tool_m = re.search(
            r'\[(?:McpTool|McpFunction)\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']+)["\'])?\s*\)\]',
            attr_str,
        )
        if mcp_tool_m:
            name = mcp_tool_m.group(1)
            if mcp_tool_m.group(2):
                desc = mcp_tool_m.group(2)

        if not desc:
            desc = name

        # method_match.end() is right after '('
        params_start = method_match.end()
        chunk = code[params_start : params_start + 600]

        if not name:
            name = method_match.group(1)
            desc = name

        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        open_parens = 1
        params_end = -1
        for i in range(len(chunk)):
            if chunk[i] == "(":
                open_parens += 1
            elif chunk[i] == ")":
                open_parens -= 1
                if open_parens == 0:
                    params_end = i
                    break

        if params_end != -1:
            params_str = chunk[:params_end]
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
                has_default = "=" in param
                is_nullable = "?" in param

                param_desc = ""
                param_desc_m = re.search(
                    r'\[Description\s*\(\s*["\']([^"\']+)["\']\s*\)\]', param
                )
                if param_desc_m:
                    param_desc = param_desc_m.group(1)

                param_clean = re.sub(r"\[[^\]]+\]\s*", "", param.split("=")[0]).strip()
                parts = param_clean.rsplit(" ", 1)
                if len(parts) >= 2:
                    pname = parts[1].strip()
                    ptype_raw = parts[0].strip().split("<")[0].replace("?", "").lower()
                    schema_type = "string"
                    if ptype_raw in (
                        "int",
                        "long",
                        "short",
                        "byte",
                        "float",
                        "double",
                        "decimal",
                    ):
                        schema_type = "number"
                    elif ptype_raw in ("bool", "boolean"):
                        schema_type = "boolean"
                    elif ptype_raw in ("list", "ienumerable", "ilist", "array"):
                        schema_type = "array"
                    elif ptype_raw in ("dictionary", "idictionary", "object"):
                        schema_type = "object"

                    prop_schema = {"type": schema_type}
                    if param_desc:
                        prop_schema["description"] = param_desc

                    properties[pname] = prop_schema
                    if not has_default and not is_nullable:
                        required.append(pname)

        add_tool(name, desc, properties, required)

    # Pattern 2: server.AddTool("name", "desc", ...)
    for match in re.finditer(
        r'(?:server|app)\.AddTool\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']+)["\'])?',
        code,
    ):
        add_tool(match.group(1), match.group(2) or match.group(1), {}, [])

    # Pattern 3: new McpTool("name", "desc")
    for match in re.finditer(
        r'new\s+McpTool\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']+)["\'])?', code
    ):
        add_tool(match.group(1), match.group(2) or match.group(1), {}, [])

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
        elif lang in ("java", "kt", "kotlin"):
            return parse_jvm_mcp_code(code)
        elif lang in ("cs", "csharp", "dotnet"):
            return parse_dotnet_mcp_code(code)
        elif lang in ("swift",):
            return parse_swift_mcp_code(code)
        elif lang in ("openapi", "swagger", "json", "yaml", "yml"):
            from mcp_fingerprints.manifest_parser import parse_manifest_mcp_tools
            manifest_res = parse_manifest_mcp_tools(code)
            if manifest_res:
                return manifest_res
            from mcp_fingerprints.openapi_parser import parse_openapi_spec
            return parse_openapi_spec(code)
            
    # Heuristics if language is unknown or not matched
    from mcp_fingerprints.manifest_parser import parse_manifest_mcp_tools
    manifest_res = parse_manifest_mcp_tools(code)
    if manifest_res:
        return manifest_res
    if "openapi" in code or "swagger" in code or "paths:" in code:
        from mcp_fingerprints.openapi_parser import parse_openapi_spec
        oa_res = parse_openapi_spec(code)
        if oa_res:
            return oa_res

    if "@Tool" in code or "@McpFunction" in code:
        res = parse_jvm_mcp_code(code)
        if res: return res

    if (
        "using ModelContextProtocol" in code
        or "[McpTool" in code
        or "[McpFunction" in code
        or "[McpServerTool" in code
        or "[KernelFunction" in code
        or "new McpTool" in code
    ):
        res = parse_dotnet_mcp_code(code)
        if res: return res

    if code.startswith("package ") or "mcp.NewTool" in code:
        res = parse_golang_mcp_code(code)
        if res: return res
        
    if "fn main()" in code or "use rmcp" in code or "#[mcp_tool" in code:
        res = parse_rust_mcp_code(code)
        if res: return res

    if (
        "import Foundation" in code
        or "import MCP" in code
        or "@McpTool" in code
        or re.search(r'struct\s+[a-zA-Z0-9_]+\s*:\s*(?:[a-zA-Z0-9_]+,\s*)*(?:Tool|MCPTool|ToolDefinition)', code)
    ):
        res = parse_swift_mcp_code(code)
        if res: return res

    # Try python and ts fallbacks
    py_res = parse_python_mcp_ast(code)
    if py_res: return py_res
    
    return parse_typescript_mcp_ast(code)
