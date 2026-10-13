"""Software Bill of Materials (SBOM) generator for MCP Server Packages."""

from __future__ import annotations

import json
import uuid
from typing import Any

from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint


def generate_cyclonedx_sbom(
    spec: ServerPackageSpec, target_version: str | None = None
) -> dict[str, Any]:
    """Generate a CycloneDX 1.5 JSON Software Bill of Materials (SBOM).
    
    If target_version is provided, uses that specific version's data.
    Otherwise, uses the most recent version (assuming versions are sorted or picking the last one)
    or falls back to a generic representation if no versions exist.
    """
    version_obj: VersionFingerprint | None = None
    if target_version:
        for v in spec.versions:
            if v.version == target_version:
                version_obj = v
                break
    elif spec.versions:
        # Default to the last version in the list
        version_obj = spec.versions[-1]

    version_str = version_obj.version if version_obj else "unknown"

    main_component = {
        "type": "application",
        "name": spec.package_name,
        "version": version_str,
        "purl": spec.purl,
    }
    
    if spec.description:
        main_component["description"] = spec.description

    # Add properties/tools
    properties = []
    
    if version_obj:
        for tool in version_obj.tool_signatures:
            properties.append({
                "name": f"mcp.tool.{tool.name}",
                "value": tool.description or ""
            })
            
    if properties:
        main_component["properties"] = properties

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "component": main_component
        },
        "components": []
    }
    
    return sbom
