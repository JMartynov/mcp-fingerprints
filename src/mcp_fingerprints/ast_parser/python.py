"""Python FastMCP & MCP SDK static AST parser."""

from __future__ import annotations

import ast
import re
from typing import Any

from .base import AstBundleResult, logger


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



