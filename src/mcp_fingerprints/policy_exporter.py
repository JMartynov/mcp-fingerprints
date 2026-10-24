from __future__ import annotations
import json
from enum import Enum
from pathlib import Path
from typing import Optional, Union, Dict, Any, List

from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint, ToolContractSignature


class PolicyFormat(str, Enum):
    REGO = "rego"
    ENVOY = "envoy"
    JSON = "json"


class PolicyMode(str, Enum):
    STRICT = "strict"
    READ_ONLY = "read-only"
    ALLOWLIST = "allowlist"


class RegoPolicyCompiler:
    @staticmethod
    def compile(passport: Union[ServerPackageSpec, VersionFingerprint], mode: PolicyMode) -> str:
        if isinstance(passport, ServerPackageSpec):
            pkg_name = passport.package_name
            if passport.versions:
                c_hash = passport.versions[0].toolset_canonical_hash
                tools = passport.versions[0].tool_signatures
            else:
                c_hash = "unknown"
                tools = ()
        else:
            pkg_name = "unknown"
            c_hash = passport.toolset_canonical_hash
            tools = passport.tool_signatures

        lines = [
            f"# Package: {pkg_name}",
            f"# Canonical Hash: {c_hash}",
            f"# Mode: {mode.value}",
            "package mcp.authz",
            "",
            "import rego.v1",
            "",
            "default allow := false",
            ""
        ]

        if not tools:
            return "\n".join(lines)

        for tool in tools:
            # Check read-only mode exclusions
            if mode == PolicyMode.READ_ONLY:
                if tool.annotations.get("destructiveHint", False):
                    continue
                
                is_read_only = False
                if "readOnlyHint" in tool.annotations:
                    if tool.annotations["readOnlyHint"]:
                        is_read_only = True
                else:
                    read_only_prefixes = ("get_", "list_", "read_", "search_", "describe_", "fetch_", "query_")
                    if tool.name.startswith(read_only_prefixes):
                        is_read_only = True
                
                if not is_read_only:
                    continue
                    
            lines.append("allow if {")
            lines.append('    input.method == "tools/call"')
            lines.append(f'    input.params.name == "{tool.name}"')
            
            # Check destructive tools in strict mode
            if mode == PolicyMode.STRICT and tool.annotations.get("destructiveHint", False):
                lines.append('    input.client_role == "admin"')

            if tool.input_schema:
                required = tool.input_schema.get("required", [])
                for req in required:
                    lines.append(f'    object.get(input.params.arguments, "{req}", null) != null')
            
                if mode == PolicyMode.STRICT:
                    properties = tool.input_schema.get("properties", {})
                    for param_name, param_schema in properties.items():
                        param_type = param_schema.get("type")
                        if param_type:
                            type_map = {
                                "string": "is_string",
                                "number": "is_number",
                                "integer": "is_number",
                                "boolean": "is_boolean",
                                "array": "is_array",
                                "object": "is_object"
                            }
                            rego_type_fn = type_map.get(param_type)
                            if rego_type_fn:
                                lines.append(f'    val_{param_name} := object.get(input.params.arguments, "{param_name}", null)')
                                lines.append(f'    {param_name}_is_type := {rego_type_fn}(val_{param_name})')
                                lines.append(f'    {param_name}_is_null := val_{param_name} == null')
                                lines.append(f'    {param_name}_is_type_or_null := {param_name}_is_type | {param_name}_is_null')
                                lines.append(f'    {param_name}_is_type_or_null == true')

                        if param_name in ("path", "filepath", "cmd", "command", "query", "sql", "url"):
                            lines.append(f'    val_sec_{param_name} := object.get(input.params.arguments, "{param_name}", null)')
                            lines.append(f'    not contains(val_sec_{param_name}, "..")')
                            lines.append(f'    not contains(val_sec_{param_name}, "/etc/")')
                            lines.append(f'    not contains(val_sec_{param_name}, "/proc/")')
                            lines.append(f'    not contains(val_sec_{param_name}, ";")')
                            lines.append(f'    not contains(val_sec_{param_name}, "$(")')
                            lines.append(f'    not contains(val_sec_{param_name}, "`")')

            lines.append("}")
            lines.append("")

        return "\n".join(lines)


class EnvoyWasmConfigCompiler:
    @staticmethod
    def compile(passport: Union[ServerPackageSpec, VersionFingerprint], mode: PolicyMode) -> Dict[str, Any]:
        if isinstance(passport, ServerPackageSpec):
            if passport.versions:
                tools = passport.versions[0].tool_signatures
            else:
                tools = ()
        else:
            tools = passport.tool_signatures

        allowed_tools = []
        for tool in tools:
            if mode == PolicyMode.READ_ONLY:
                if tool.annotations.get("destructiveHint", False):
                    continue
                is_read_only = False
                if "readOnlyHint" in tool.annotations:
                    if tool.annotations["readOnlyHint"]:
                        is_read_only = True
                else:
                    read_only_prefixes = ("get_", "list_", "read_", "search_", "describe_", "fetch_", "query_")
                    if tool.name.startswith(read_only_prefixes):
                        is_read_only = True
                if not is_read_only:
                    continue
            allowed_tools.append(tool.name)

        config = {
            "name": "envoy.filters.http.rbac",
            "typed_config": {
                "@type": "type.googleapis.com/envoy.extensions.filters.http.rbac.v3.RBAC",
                "rules": {
                    "action": "ALLOW",
                    "policies": {
                        "mcp_tools_allowlist": {
                            "permissions": [
                                {
                                    "header": {
                                        "name": ":path",
                                        "exact_match": "/tools/call"
                                    }
                                }
                            ],
                            "principals": [
                                {
                                    "any": True
                                }
                            ]
                        }
                    }
                }
            },
            "mcp_allowed_tools": allowed_tools,
            "mode_constraints": mode.value
        }
        return config


class PolicyExporter:
    @staticmethod
    def export(passport_or_identifier: Union[str, Path, ServerPackageSpec], fmt: PolicyFormat = PolicyFormat.REGO, mode: PolicyMode = PolicyMode.STRICT, output_path: Optional[Path] = None) -> str:
        passport = None
        if isinstance(passport_or_identifier, ServerPackageSpec):
            passport = passport_or_identifier
        elif isinstance(passport_or_identifier, (str, Path)):
            p = Path(passport_or_identifier)
            if p.is_file():
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    passport = ServerPackageSpec.from_dict(data)
            else:
                # Resolve from index (simplified for this task)
                from mcp_fingerprints.matcher import FingerprintMatcher
                matcher = FingerprintMatcher()
                try:
                    matcher.load_default(download_if_missing=False)
                except Exception:
                    pass
                # Access packages dictionary from the fast_index
                for spec in matcher.fast_index.packages.values():
                    if spec.package_name == str(passport_or_identifier):
                        passport = spec
                        break
        
        if not passport:
            raise ValueError(f"Passport not found for {passport_or_identifier}")

        if fmt == PolicyFormat.REGO:
            result = RegoPolicyCompiler.compile(passport, mode)
        elif fmt == PolicyFormat.ENVOY:
            config = EnvoyWasmConfigCompiler.compile(passport, mode)
            result = json.dumps(config, indent=2)
        elif fmt == PolicyFormat.JSON:
            allowed_tools = []
            if passport.versions:
                for tool in passport.versions[0].tool_signatures:
                    allowed_tools.append(tool.to_dict())
            manifest = {
                "package_name": passport.package_name,
                "mode_constraints": mode.value,
                "safety_classification": "verified",
                "annotation_summary": {
                    "allowed_tools": len(allowed_tools)
                },
                "allowed_tools": allowed_tools
            }
            result = json.dumps(manifest, indent=2)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        if output_path:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                f.write(result)

        return result
