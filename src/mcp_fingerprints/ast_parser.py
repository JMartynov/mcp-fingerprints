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
    ) -> None:
        raw_tools = list(tools or [])
        super().__init__(raw_tools)
        self.tools = raw_tools
        self.prompts = list(prompts or [])
        self.resources = list(resources or [])
        self.env_vars = tuple(sorted(set(env_vars or ())))
        self.required_env_vars = self.env_vars

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
        self.extracted_prompts: list[dict[str, Any]] = []
        self.extracted_resources: list[dict[str, Any]] = []
        self.extracted_env_vars: set[str] = set()
        self.pydantic_models: dict[str, dict[str, Any]] = dict(pydantic_models or {})

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
        if isinstance(func, ast.Name) and func.id in ("Tool", "types_Tool"):
            is_tool_call = True
        elif isinstance(func, ast.Attribute) and func.attr == "Tool":
            is_tool_call = True

        if is_tool_call:
            name = None
            desc = ""
            properties: dict[str, Any] = {}
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
            if base_name in ("BaseTool", "Tool"):
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
                            if target.id == "name" and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                                name = item.value.value
                            elif target.id == "description" and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                                desc = item.value.value
                            elif target.id == "args_schema" and isinstance(item.value, ast.Name):
                                args_schema_name = item.value.id
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    if item.target.id == "name" and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                        name = item.value.value
                    elif item.target.id == "description" and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                        desc = item.value.value
                    elif item.target.id == "args_schema" and isinstance(item.value, ast.Name):
                        args_schema_name = item.value.id

            if not name:
                name = node.name

            if args_schema_name and args_schema_name in self.pydantic_models:
                model_info = self.pydantic_models[args_schema_name]
                properties = dict(model_info.get("properties", {}))
                required = list(model_info.get("required", []))

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

            if dec_name in ("tool", "mcp_tool") or (isinstance(func_node, ast.Attribute) and func_node.attr == "tool"):
                is_tool = True
            elif isinstance(func_node, ast.Attribute) and func_node.attr in ("tool", "register"):
                val_id = getattr(func_node.value, "id", "")
                if "tool" in val_id or "server" in val_id or "mcp" in val_id:
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

    # Pass 1: Parse AST and collect Pydantic models across all files
    for fname, code in files.items():
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

    return AstBundleResult(tools=extracted, env_vars=env_vars)


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


def parse_jvm_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from Java/Kotlin source code."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    annotation_regex = re.compile(r"@(?:Tool|McpFunction)\s*(?:\(([^)]*)\))?", re.DOTALL)

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
            r"(?:public|private|protected|internal)?\s*(?:open|override|final|suspend)?\s*(?:fun|[\w<>\[\]\?]+)\s+([a-zA-Z0-9_]+)\s*\(",
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
            params_start = method_match.end()
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

                    has_default = "=" in param
                    param_clean = param.split("=")[0].strip()

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
                            ptype_raw = re.sub(r'@[A-Za-z0-9_]+\s*', '', parts[0]).strip().split("<")[0]
                        else:
                            continue

                    pname = pname.strip()
                    ptype_base = ptype_raw.strip().lower().split("<")[0].split("[")[0].replace("?", "")

                    schema_type = "string"
                    if ptype_base in ("int", "integer", "long", "short", "byte", "float", "double", "number"):
                        schema_type = "number"
                    elif ptype_base in ("boolean", "bool"):
                        schema_type = "boolean"
                    elif ptype_base in ("list", "set", "collection", "array", "iterable"):
                        schema_type = "array"
                    elif ptype_base in ("map", "dictionary", "object", "record", "jsonnode", "objectnode"):
                        schema_type = "object"

                    properties[pname] = {"type": schema_type}
                    required.append(pname)

        extracted.append({
            "name": name,
            "description": desc,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": sorted(required),
            },
        })

    return extracted


def parse_dotnet_mcp_code(code: str) -> list[dict[str, Any]]:
    """Statically extract MCP tool definitions from C#/.NET source code."""
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
        })

    # Pattern 1: Attributes on methods [McpTool("name", "description")] or [McpFunction("name")]
    attr_regex = re.compile(r"\[(?:McpTool|McpFunction)\s*\(([^)]*)\)\]", re.DOTALL)
    for match in attr_regex.finditer(code):
        attrs = match.group(1).strip()
        strings = re.findall(r'["\']([^"\']+)["\']', attrs)
        name = strings[0] if strings else ""
        desc = strings[1] if len(strings) > 1 else ""

        start_idx = match.end()
        chunk = code[start_idx : start_idx + 600]

        desc_attr = re.search(r'\[Description\s*\(\s*["\']([^"\']+)["\']\s*\)\]', chunk)
        if desc_attr and not desc:
            desc = desc_attr.group(1)

        method_match = re.search(
            r"(?:public|private|protected|internal)?\s*(?:static|async|virtual|override)?\s*[\w<>\[\]\?]+\s+([a-zA-Z0-9_]+)\s*\(",
            chunk,
        )

        if not name:
            if method_match:
                name = method_match.group(1)
            else:
                continue

        properties: dict[str, dict[str, str]] = {}
        required: list[str] = []

        if method_match:
            params_start = method_match.end()
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
                    has_default = "=" in param
                    is_nullable = "?" in param
                    param_clean = param.split("=")[0].strip()
                    parts = param_clean.rsplit(" ", 1)
                    if len(parts) >= 2:
                        pname = parts[1].strip()
                        ptype_raw = parts[0].strip().split("<")[0].replace("?", "").lower()
                        schema_type = "string"
                        if ptype_raw in ("int", "long", "short", "byte", "float", "double", "decimal"):
                            schema_type = "number"
                        elif ptype_raw in ("bool", "boolean"):
                            schema_type = "boolean"
                        elif ptype_raw in ("list", "ienumerable", "ilist", "array"):
                            schema_type = "array"
                        elif ptype_raw in ("dictionary", "idictionary", "object"):
                            schema_type = "object"
                        properties[pname] = {"type": schema_type}
                        if not has_default and not is_nullable:
                            required.append(pname)

        add_tool(name, desc, properties, required)

    # Pattern 2: server.AddTool("name", "desc", ...)
    for match in re.finditer(r'(?:server|app)\.AddTool\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']+)["\'])?', code):
        add_tool(match.group(1), match.group(2) or match.group(1), {}, [])

    # Pattern 3: new McpTool("name", "desc")
    for match in re.finditer(r'new\s+McpTool\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']+)["\'])?', code):
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
        elif lang in ("openapi", "swagger", "json", "yaml", "yml"):
            from mcp_fingerprints.openapi_parser import parse_openapi_spec
            return parse_openapi_spec(code)
            
    # Heuristics if language is unknown or not matched
    if "openapi" in code or "swagger" in code or "paths:" in code:
        from mcp_fingerprints.openapi_parser import parse_openapi_spec
        oa_res = parse_openapi_spec(code)
        if oa_res:
            return oa_res

    if "@Tool" in code or "@McpFunction" in code:
        res = parse_jvm_mcp_code(code)
        if res: return res

    if "using ModelContextProtocol" in code or "[McpTool" in code or "[McpFunction" in code or "new McpTool" in code:
        res = parse_dotnet_mcp_code(code)
        if res: return res

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
