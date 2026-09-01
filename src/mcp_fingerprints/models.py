"""Data models for the Full-Fidelity MCP Structural Fingerprint & Passport Knowledge Base."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolContractSignature:
        return cls(
            name=data["name"],
            canonical_hash=data["canonical_hash"],
            description=data.get("description", ""),
            is_mutating=data.get("is_mutating", False),
            property_keys=tuple(data.get("property_keys", ())),
            required_keys=tuple(data.get("required_keys", ())),
            parameter_types=data.get("parameter_types", {}),
            input_schema=data.get("inputSchema", {}),
            output_schema=data.get("outputSchema"),
            description_hash=data.get("description_hash"),
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
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            argument_keys=tuple(data.get("argument_keys", ())),
            required_arguments=tuple(data.get("required_arguments", ())),
            arguments_schema=data.get("arguments", []),
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
            uri_template=data.get("uri_template") or data.get("uriTemplate", ""),
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "toolset_canonical_hash": self.toolset_canonical_hash,
            "release_date": self.release_date,
            "dependencies": self.dependencies,
            "connections": self.connections,
            "capabilities": self.capabilities,
            "tool_signatures": [t.to_dict() for t in self.tool_signatures],
            "prompt_signatures": [p.to_dict() for p in self.prompt_signatures],
            "resource_signatures": [r.to_dict() for r in self.resource_signatures],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VersionFingerprint:
        return cls(
            version=data["version"],
            toolset_canonical_hash=data["toolset_canonical_hash"],
            release_date=data.get("release_date"),
            dependencies=data.get("dependencies", {}),
            connections=data.get("connections", []),
            capabilities=data.get("capabilities", {}),
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
    """Catalog specification of an MCP server package and all its known version fingerprints."""

    package_name: str
    purl: str
    ecosystem: str
    display_name: str | None = None
    description: str | None = None
    repository_url: str | None = None
    homepage_url: str | None = None
    license: str | None = None
    keywords: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    sources_merged: tuple[str, ...] = ()
    dist_tags: dict[str, str] = field(default_factory=dict)
    versions: tuple[VersionFingerprint, ...] = ()
    security_profile: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passport_schema_version": "1.1.0",
            "package_name": self.package_name,
            "purl": self.purl,
            "ecosystem": self.ecosystem,
            "display_name": self.display_name,
            "description": self.description,
            "repository_url": self.repository_url,
            "homepage_url": self.homepage_url,
            "license": self.license,
            "keywords": list(self.keywords),
            "aliases": list(self.aliases),
            "sources_merged": list(self.sources_merged),
            "dist_tags": self.dist_tags,
            "versions": [v.to_dict() for v in self.versions],
            "security_profile": self.security_profile,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServerPackageSpec:
        return cls(
            package_name=data["package_name"],
            purl=data["purl"],
            ecosystem=data["ecosystem"],
            display_name=data.get("display_name"),
            description=data.get("description"),
            repository_url=data.get("repository_url"),
            homepage_url=data.get("homepage_url"),
            license=data.get("license"),
            keywords=tuple(data.get("keywords", ())),
            aliases=tuple(data.get("aliases", ())),
            sources_merged=tuple(data.get("sources_merged", ())),
            dist_tags=data.get("dist_tags", {}),
            versions=tuple(VersionFingerprint.from_dict(v) for v in data.get("versions", ())),
            security_profile=data.get("security_profile", {}),
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
