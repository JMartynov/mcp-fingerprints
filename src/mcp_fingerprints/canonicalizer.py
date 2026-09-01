"""Canonicalization engine for computing deterministic order-independent MCP hashes."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from mcp_fingerprints.models import (
    PromptSignature,
    ResourceSignature,
    ToolContractSignature,
    VersionFingerprint,
)


def canonicalize_json(obj: Any) -> str:
    """Canonicalize a JSON-serializable Python data structure.

    Keys in dictionaries are sorted recursively.
    Separators are compact (',' and ':') without extraneous whitespace.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_sha256(data: str | bytes) -> str:
    """Compute standard sha256:<hex> digest of input string or bytes."""
    payload = data.encode("utf-8") if isinstance(data, str) else data
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


def extract_tool_signature(tool_def: dict[str, Any]) -> ToolContractSignature:
    """Extract structural parameters and compute canonical hash for an MCP tool definition."""
    name = str(tool_def.get("name", "")).strip()
    raw_desc = str(tool_def.get("description", ""))
    raw_schema = (
        tool_def.get("inputSchema")
        or tool_def.get("input_schema")
        or tool_def.get("parameters")
        or {}
    )
    input_schema = raw_schema if isinstance(raw_schema, dict) else {}
    output_schema = (
        tool_def.get("outputSchema")
        or tool_def.get("output_schema")
        or tool_def.get("returns")
    )
    output_schema = output_schema if isinstance(output_schema, dict) else None

    props = input_schema.get("properties", {})
    prop_keys = tuple(sorted(props.keys())) if isinstance(props, dict) else ()
    required = (
        tuple(sorted(input_schema.get("required", [])))
        if isinstance(input_schema.get("required"), list)
        else ()
    )

    param_types: dict[str, str] = {}
    if isinstance(props, dict):
        for k, v in props.items():
            if isinstance(v, dict) and "type" in v:
                param_types[k] = str(v["type"])

    # Canonical normalized tool payload (excluding volatile comments/formatting)
    canonical_payload = {
        "name": name,
        "inputSchema": {
            "type": input_schema.get("type", "object"),
            "properties": {
                k: {
                    "type": props[k].get("type") if isinstance(props[k], dict) else "any",
                    "description": props[k].get("description", "")
                    if isinstance(props[k], dict)
                    else "",
                }
                for k in prop_keys
            },
            "required": list(required),
        },
        "outputSchema": output_schema,
    }

    canonical_hash = compute_sha256(canonicalize_json(canonical_payload))
    desc_hash = compute_sha256(raw_desc.strip()) if raw_desc else None

    return ToolContractSignature(
        name=name,
        canonical_hash=canonical_hash,
        description=raw_desc,
        is_mutating=bool(tool_def.get("is_mutating", False)),
        property_keys=prop_keys,
        required_keys=required,
        parameter_types=param_types,
        input_schema=input_schema,
        output_schema=output_schema,
        description_hash=desc_hash,
    )


def compute_toolset_canonical_hash(tools: list[dict[str, Any]]) -> str:
    """Compute single aggregated order-independent canonical hash across all tools in a toolset."""
    signatures = [extract_tool_signature(t) for t in tools if isinstance(t, dict) and t.get("name")]
    # Sort tool signatures deterministically by tool name
    sorted_hashes = sorted(sig.canonical_hash for sig in signatures)
    combined = "|".join(sorted_hashes)
    return compute_sha256(combined)


def build_version_fingerprint(
    version: str,
    tools: list[dict[str, Any]] | None = None,
    prompts: list[dict[str, Any]] | None = None,
    resources: list[dict[str, Any]] | None = None,
    release_date: str | None = None,
    capabilities: dict[str, bool] | None = None,
) -> VersionFingerprint:
    """Construct a full VersionFingerprint object from raw protocol inspection results."""
    clean_tools = [t for t in (tools or []) if isinstance(t, dict)]
    tool_sigs = tuple(
        sorted((extract_tool_signature(t) for t in clean_tools), key=lambda x: x.name)
    )
    toolset_hash = compute_toolset_canonical_hash(clean_tools)

    prompt_sigs: list[PromptSignature] = []
    if prompts:
        for p in prompts:
            p_name = p.get("name", "")
            args = p.get("arguments", [])
            arg_keys = tuple(sorted(a.get("name", "") for a in args if isinstance(a, dict)))
            req_args = tuple(
                sorted(a.get("name", "") for a in args if isinstance(a, dict) and a.get("required"))
            )
            prompt_sigs.append(
                PromptSignature(name=p_name, argument_keys=arg_keys, required_arguments=req_args)
            )

    resource_sigs: list[ResourceSignature] = []
    if resources:
        for r in resources:
            uri = r.get("uriTemplate") or r.get("uri", "")
            resource_sigs.append(
                ResourceSignature(
                    uri_template=uri,
                    name=r.get("name"),
                    mime_type=r.get("mimeType"),
                )
            )

    caps = capabilities or {"tools": True, "prompts": bool(prompts), "resources": bool(resources)}

    return VersionFingerprint(
        version=version,
        toolset_canonical_hash=toolset_hash,
        tool_signatures=tool_sigs,
        prompt_signatures=tuple(prompt_sigs),
        resource_signatures=tuple(resource_sigs),
        release_date=release_date,
        capabilities=caps,
    )
