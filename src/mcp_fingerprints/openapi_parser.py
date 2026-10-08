"""OpenAPI and Swagger Specification parser for MCP tool contract extraction."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger("mcp_fingerprints.openapi_parser")


def _safe_parse_spec(content: str | dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(content, dict):
        return content
    if not isinstance(content, str) or not content.strip():
        return None

    # Try JSON first
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Try PyYAML if available
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return None


def _parse_yaml_spec_regex(content: str) -> list[dict[str, Any]]:
    """Zero-dependency fallback parser for OpenAPI / Swagger specifications in YAML format."""
    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    lines = content.splitlines()
    in_paths = False
    paths_indent = -1
    current_path = ""
    path_indent = -1
    current_method = ""
    method_indent = -1
    op_id = ""
    description = ""
    properties: dict[str, Any] = {}
    required: list[str] = []

    def flush_op():
        nonlocal op_id, description, properties, required
        if not current_path or not current_method:
            return
        final_op_id = op_id
        if not final_op_id:
            clean_path = re.sub(r"[{}]", "", current_path).replace("/", "_").strip("_")
            final_op_id = f"{current_method}_{clean_path}" if clean_path else current_method
        final_op_id = re.sub(r"[^a-zA-Z0-9_-]", "_", final_op_id)
        if final_op_id and final_op_id not in seen_names:
            seen_names.add(final_op_id)
            extracted.append({
                "name": final_op_id,
                "description": description or f"Execute {current_method.upper()} on {current_path}",
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": sorted(set(required)),
                },
            })
        op_id = ""
        description = ""
        properties = {}
        required = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        if not in_paths:
            if stripped.startswith("paths:"):
                in_paths = True
                paths_indent = indent
            continue

        if indent <= paths_indent:
            flush_op()
            break

        path_match = re.match(r"^['\"]?(/[^:'\"]+)['\"]?:\s*$", stripped)
        if path_match and (path_indent == -1 or indent <= path_indent):
            flush_op()
            current_path = path_match.group(1)
            path_indent = indent
            current_method = ""
            method_indent = -1
            continue

        method_match = re.match(r"^(get|post|put|delete|patch|options|head):\s*$", stripped, re.IGNORECASE)
        if method_match and (method_indent == -1 or indent <= method_indent):
            flush_op()
            current_method = method_match.group(1).lower()
            method_indent = indent
            continue

        if current_method and indent > method_indent:
            op_match = re.match(r"^operationId:\s*['\"]?([a-zA-Z0-9_-]+)['\"]?$", stripped)
            if op_match:
                op_id = op_match.group(1)
                continue
            desc_match = re.match(r"^(?:summary|description):\s*['\"]?([^'\"#\n\r]+)['\"]?$", stripped)
            if desc_match and not description:
                description = desc_match.group(1).strip()
                continue
            param_match = re.match(r"^-\s+name:\s*['\"]?([a-zA-Z0-9_-]+)['\"]?$", stripped)
            if param_match:
                pname = param_match.group(1)
                properties[pname] = {"type": "string"}
                continue

    flush_op()
    return extracted


def parse_openapi_spec(content: str | dict[str, Any]) -> list[dict[str, Any]]:
    """Parse OpenAPI 3.x or Swagger 2.0 document into standardized MCP tool contract dicts."""
    spec = _safe_parse_spec(content)
    if not spec or not isinstance(spec, dict):
        if isinstance(content, str) and "paths:" in content:
            return _parse_yaml_spec_regex(content)
        return []

    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return []

    extracted: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method in ("get", "post", "put", "delete", "patch", "options", "head"):
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue

            op_id = op.get("operationId")
            if not op_id:
                clean_path = re.sub(r"[{}]", "", path).replace("/", "_").strip("_")
                op_id = f"{method}_{clean_path}" if clean_path else method

            # Normalize tool name
            op_id = re.sub(r"[^a-zA-Z0-9_-]", "_", op_id)
            if not op_id or op_id in seen_names:
                continue
            seen_names.add(op_id)

            description = (
                op.get("description")
                or op.get("summary")
                or f"Execute {method.upper()} on {path}"
            )

            properties: dict[str, Any] = {}
            required: list[str] = []

            # 1. Process parameters (query, path, header, or Swagger 2.0 body)
            params = op.get("parameters", [])
            if isinstance(params, list):
                for param in params:
                    if not isinstance(param, dict) or "name" not in param:
                        continue
                    pname = param["name"]
                    p_in = param.get("in", "")

                    if p_in == "body" and "schema" in param and isinstance(param["schema"], dict):
                        # Swagger 2.0 body param
                        body_props = param["schema"].get("properties", {})
                        if isinstance(body_props, dict):
                            for bpname, bpval in body_props.items():
                                properties[bpname] = bpval if isinstance(bpval, dict) else {"type": "string"}
                        for req_f in param["schema"].get("required", []):
                            if req_f not in required:
                                required.append(req_f)
                    else:
                        pschema = param.get("schema", {})
                        ptype = pschema.get("type", "string") if isinstance(pschema, dict) else param.get("type", "string")
                        pdesc = param.get("description", "")
                        prop_def: dict[str, Any] = {"type": ptype}
                        if pdesc:
                            prop_def["description"] = pdesc
                        properties[pname] = prop_def
                        if param.get("required"):
                            required.append(pname)

            # 2. Process OpenAPI 3.x requestBody
            req_body = op.get("requestBody", {})
            if isinstance(req_body, dict):
                content_map = req_body.get("content", {})
                if isinstance(content_map, dict):
                    json_media = content_map.get("application/json", {})
                    if isinstance(json_media, dict):
                        b_schema = json_media.get("schema", {})
                        if isinstance(b_schema, dict):
                            b_props = b_schema.get("properties", {})
                            if isinstance(b_props, dict):
                                for bpname, bpval in b_props.items():
                                    properties[bpname] = bpval if isinstance(bpval, dict) else {"type": "string"}
                            for req_f in b_schema.get("required", []):
                                if req_f not in required:
                                    required.append(req_f)

            extracted.append({
                "name": op_id,
                "description": description,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": sorted(set(required)),
                },
            })

    return extracted
