"""Data models for the Full-Fidelity MCP Structural Fingerprint & Passport Knowledge Base."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

TransportType = Literal["stdio", "sse", "streamable-http", "websocket"]


@dataclass(frozen=True)
class ParameterMetadata:
    """Rich parameter metadata for a tool argument."""

    name: str
    type: str
    description: str | None = None
    required: bool = False
    default: Any = None
    enum: tuple[Any, ...] | None = None
    format: str | None = None
    items_type: str | None = None
    nested_properties: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "enum": list(self.enum) if self.enum is not None else None,
            "format": self.format,
            "items_type": self.items_type,
            "nested_properties": self.nested_properties,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParameterMetadata:
        raw_enum = data.get("enum")
        enum_val = tuple(raw_enum) if isinstance(raw_enum, (list, tuple)) else None
        return cls(
            name=str(data.get("name", "")),
            type=str(data.get("type", "string")),
            description=data.get("description"),
            required=bool(data.get("required", False)),
            default=data.get("default"),
            enum=enum_val,
            format=data.get("format"),
            items_type=data.get("items_type"),
            nested_properties=data.get("nested_properties"),
        )


@dataclass(frozen=True)
class ToolContractSignature:
    """Structural signature of a single MCP tool contract with full JSON Schema fidelity."""

    name: str
    canonical_hash: str
    description: str = ""
    is_mutating: bool = False
    property_keys: tuple[str, ...] = ()
    required_keys: tuple[str, ...] = ()
    parameter_types: dict[str, str] = field(default_factory=dict)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] | None = None
    description_hash: str | None = None
    parameters: tuple[ParameterMetadata, ...] = ()
    annotations: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "canonical_hash": self.canonical_hash,
            "description": self.description,
            "is_mutating": self.is_mutating,
            "property_keys": list(self.property_keys),
            "required_keys": list(self.required_keys),
            "parameter_types": self.parameter_types,
            "inputSchema": self.input_schema,
            "outputSchema": self.output_schema,
            "description_hash": self.description_hash,
            "parameters": [p.to_dict() for p in self.parameters],
            "annotations": self.annotations,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolContractSignature:
        if not isinstance(data, dict):
            data = {}
        property_keys = data.get("property_keys")
        if not isinstance(property_keys, (list, tuple)):
            property_keys = ()
        else:
            property_keys = tuple(str(k) for k in property_keys)

        required_keys = data.get("required_keys")
        if not isinstance(required_keys, (list, tuple)):
            required_keys = ()
        else:
            required_keys = tuple(str(k) for k in required_keys)

        parameter_types = data.get("parameter_types")
        if not isinstance(parameter_types, dict):
            parameter_types = {}

        input_schema = data.get("inputSchema")
        if not isinstance(input_schema, dict):
            input_schema = {}

        output_schema = data.get("outputSchema")
        if not isinstance(output_schema, dict):
            output_schema = None

        raw_params = data.get("parameters")
        parameters: list[ParameterMetadata] = []
        if isinstance(raw_params, (list, tuple)) and len(raw_params) > 0:
            for p in raw_params:
                if isinstance(p, ParameterMetadata):
                    parameters.append(p)
                elif isinstance(p, dict):
                    parameters.append(ParameterMetadata.from_dict(p))
        elif isinstance(input_schema.get("properties"), dict):
            props = input_schema["properties"]
            for k in sorted(props.keys()):
                v = props[k]
                if isinstance(v, dict):
                    raw_enum = v.get("enum")
                    enum_tuple = tuple(raw_enum) if isinstance(raw_enum, (list, tuple)) else None
                    items_type = v.get("items", {}).get("type") if isinstance(v.get("items"), dict) else None
                    nested_properties = v.get("properties") if isinstance(v.get("properties"), dict) else None
                    parameters.append(
                        ParameterMetadata(
                            name=str(k),
                            type=str(v.get("type", "string")),
                            description=v.get("description"),
                            required=k in required_keys,
                            default=v.get("default"),
                            enum=enum_tuple,
                            format=v.get("format"),
                            items_type=items_type,
                            nested_properties=nested_properties,
                        )
                    )

        raw_annotations = data.get("annotations")
        annotations: dict[str, bool] = {}
        if isinstance(raw_annotations, dict):
            for ak, av in raw_annotations.items():
                annotations[str(ak)] = bool(av)

        return cls(
            name=str(data.get("name", "")),
            canonical_hash=str(data.get("canonical_hash", "")),
            description=str(data.get("description", "") or ""),
            is_mutating=bool(data.get("is_mutating", False)),
            property_keys=property_keys,
            required_keys=required_keys,
            parameter_types=parameter_types,
            input_schema=input_schema,
            output_schema=output_schema,
            description_hash=data.get("description_hash"),
            parameters=tuple(parameters),
            annotations=annotations,
        )



@dataclass(frozen=True)
class PromptSignature:
    """Structural signature of an MCP prompt template."""

    name: str
    description: str = ""
    argument_keys: tuple[str, ...] = ()
    required_arguments: tuple[str, ...] = ()
    arguments_schema: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "argument_keys": list(self.argument_keys),
            "required_arguments": list(self.required_arguments),
            "arguments": self.arguments_schema,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptSignature:
        args_schema = data.get("arguments") or data.get("parameters") or data.get("args") or []
        arg_keys = list(data.get("argument_keys", ()))
        req_args = list(data.get("required_arguments", ()))
        if not arg_keys and isinstance(args_schema, list):
            for a in args_schema:
                if isinstance(a, dict) and "name" in a:
                    arg_keys.append(str(a["name"]))
                    if a.get("required"):
                        req_args.append(str(a["name"]))
                elif isinstance(a, str):
                    arg_keys.append(a)
        return cls(
            name=str(data.get("name", "")),
            description=data.get("description", ""),
            argument_keys=tuple(arg_keys),
            required_arguments=tuple(req_args),
            arguments_schema=args_schema if isinstance(args_schema, list) else [],
        )


@dataclass(frozen=True)
class ResourceSignature:
    """Structural signature of an exposed MCP resource."""

    uri_template: str
    name: str | None = None
    description: str = ""
    mime_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri_template": self.uri_template,
            "name": self.name,
            "description": self.description,
            "mime_type": self.mime_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceSignature:
        return cls(
            uri_template=data.get("uri_template")
            or data.get("uriTemplate")
            or data.get("uri")
            or "",
            name=data.get("name"),
            description=data.get("description", ""),
            mime_type=data.get("mime_type") or data.get("mimeType"),
        )


@dataclass(frozen=True)
class VersionFingerprint:
    """Fingerprint signature for a specific version release of an MCP server."""

    version: str
    toolset_canonical_hash: str
    tool_signatures: tuple[ToolContractSignature, ...] = ()
    prompt_signatures: tuple[PromptSignature, ...] = ()
    resource_signatures: tuple[ResourceSignature, ...] = ()
    release_date: str | None = None
    dependencies: dict[str, str] = field(default_factory=dict)
    connections: list[dict[str, Any]] = field(default_factory=list)
    capabilities: dict[str, bool] = field(default_factory=dict)
    transport: TransportType = "stdio"
    remote_endpoint: str | None = None
    auth_type: Literal["none", "bearer", "api-key", "oauth2"] = "none"
    headers_schema: dict[str, str] = field(default_factory=dict)
    required_env_vars: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "toolset_canonical_hash": self.toolset_canonical_hash,
            "release_date": self.release_date,
            "dependencies": self.dependencies,
            "connections": self.connections,
            "capabilities": self.capabilities,
            "transport": self.transport,
            "remote_endpoint": self.remote_endpoint,
            "auth_type": self.auth_type,
            "headers_schema": self.headers_schema,
            "required_env_vars": list(self.required_env_vars),
            "tool_signatures": [t.to_dict() for t in self.tool_signatures],
            "prompt_signatures": [p.to_dict() for p in self.prompt_signatures],
            "resource_signatures": [r.to_dict() for r in self.resource_signatures],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VersionFingerprint:
        raw_env = data.get("required_env_vars", ())
        if isinstance(raw_env, (list, tuple)):
            env_vars = tuple(str(e) for e in raw_env)
        else:
            env_vars = ()
        return cls(
            version=data["version"],
            toolset_canonical_hash=data["toolset_canonical_hash"],
            release_date=data.get("release_date"),
            dependencies=data.get("dependencies", {}),
            connections=data.get("connections", []),
            capabilities=data.get("capabilities", {}),
            transport=data.get("transport", "stdio"),
            remote_endpoint=data.get("remote_endpoint"),
            auth_type=data.get("auth_type", "none"),
            headers_schema=data.get("headers_schema", {}),
            required_env_vars=env_vars,
            tool_signatures=tuple(
                ToolContractSignature.from_dict(t) for t in data.get("tool_signatures", ())
            ),
            prompt_signatures=tuple(
                PromptSignature.from_dict(p) for p in data.get("prompt_signatures", ())
            ),
            resource_signatures=tuple(
                ResourceSignature.from_dict(r) for r in data.get("resource_signatures", ())
            ),
        )


@dataclass(frozen=True)
class ServerPackageSpec:
    """Catalog specification of an MCP server package and all its known version fingerprints.

    Note: Pure structural model without mutable external issue metadata.
    """

    package_name: str
    purl: str
    ecosystem: str
    display_name: str | None = None
    description: str | None = None
    author: str | None = None
    repository_url: str | None = None
    homepage_url: str | None = None
    license: str | None = None
    keywords: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    sources_merged: tuple[str, ...] = ()
    dist_tags: dict[str, str] = field(default_factory=dict)
    versions: tuple[VersionFingerprint, ...] = ()
    transport: TransportType = "stdio"
    remote_endpoint: str | None = None
    auth_type: Literal["none", "bearer", "api-key", "oauth2"] = "none"
    headers_schema: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passport_schema_version": "1.1.0",
            "package_name": self.package_name,
            "purl": self.purl,
            "ecosystem": self.ecosystem,
            "display_name": self.display_name,
            "description": self.description,
            "author": self.author,
            "repository_url": self.repository_url,
            "homepage_url": self.homepage_url,
            "license": self.license,
            "keywords": list(self.keywords),
            "aliases": list(self.aliases),
            "sources_merged": list(self.sources_merged),
            "dist_tags": self.dist_tags,
            "versions": [v.to_dict() for v in self.versions],
            "transport": self.transport,
            "remote_endpoint": self.remote_endpoint,
            "auth_type": self.auth_type,
            "headers_schema": self.headers_schema,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServerPackageSpec:
        return cls(
            package_name=data["package_name"],
            purl=data["purl"],
            ecosystem=data["ecosystem"],
            display_name=data.get("display_name"),
            description=data.get("description"),
            author=data.get("author"),
            repository_url=data.get("repository_url"),
            homepage_url=data.get("homepage_url"),
            license=data.get("license"),
            keywords=tuple(data.get("keywords", ())),
            aliases=tuple(data.get("aliases", ())),
            sources_merged=tuple(data.get("sources_merged", ())),
            dist_tags=data.get("dist_tags", {}),
            versions=tuple(VersionFingerprint.from_dict(v) for v in data.get("versions", ())),
            transport=data.get("transport", "stdio"),
            remote_endpoint=data.get("remote_endpoint"),
            auth_type=data.get("auth_type", "none"),
            headers_schema=data.get("headers_schema", {}),
        )


@dataclass
class FingerprintMatchResult:
    """Outcome of evaluating observed tools against the fingerprint knowledge base."""

    matched: bool
    package_name: str | None = None
    purl: str | None = None
    matched_version: str | None = None
    confidence_score: float = 0.0
    match_layer: str = "NONE"  # LAYER_1_EXACT, LAYER_2_TOPOLOGY, LAYER_3_CAPABILITY, NONE
    layer1_exact_match: bool = False
    layer2_topology_score: float = 0.0
    layer3_capability_score: float = 0.0
    matched_tool_count: int = 0
    total_observed_tools: int = 0
    unmatched_observed_tools: list[str] = field(default_factory=list)
    missing_expected_tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "package_name": self.package_name,
            "purl": self.purl,
            "matched_version": self.matched_version,
            "confidence_score": round(self.confidence_score, 4),
            "match_layer": self.match_layer,
            "layer1_exact_match": self.layer1_exact_match,
            "layer2_topology_score": round(self.layer2_topology_score, 4),
            "layer3_capability_score": round(self.layer3_capability_score, 4),
            "matched_tool_count": self.matched_tool_count,
            "total_observed_tools": self.total_observed_tools,
            "unmatched_observed_tools": self.unmatched_observed_tools,
            "missing_expected_tools": self.missing_expected_tools,
        }
