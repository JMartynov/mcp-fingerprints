import hashlib
import json
import logging
import subprocess
import shutil
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint
from mcp_fingerprints.canonicalizer import canonicalize_json

logger = logging.getLogger(__name__)

class SBOMFormat(str, Enum):
    CYCLONEDX = "cyclonedx"
    SPDX = "spdx"

@dataclass
class CycloneDXExporter:
    """Exports MCP tool specifications to CycloneDX 1.6 or SPDX 2.3 SBOM formats."""

    @staticmethod
    def _generate_uuid(spec_or_specs: Union[ServerPackageSpec, Iterable[ServerPackageSpec]]) -> str:
        """Generates a deterministic UUIDv5 based on canonical hashing of the input specs."""
        specs = [spec_or_specs] if isinstance(spec_or_specs, ServerPackageSpec) else list(spec_or_specs)
        combined_hash_content = ""
        for spec in specs:
            latest_version = CycloneDXExporter._get_latest_version(spec)
            hash_val = latest_version.toolset_canonical_hash if latest_version else spec.package_name
            combined_hash_content += f"{spec.package_name}:{hash_val}|"
        
        namespace_uuid = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        generated_uuid = uuid.uuid5(namespace_uuid, combined_hash_content)
        return f"urn:uuid:{generated_uuid}"

    @staticmethod
    def _get_latest_version(spec: ServerPackageSpec) -> Optional[VersionFingerprint]:
        if not spec.versions:
            return None
        return sorted(spec.versions, key=lambda v: v.version)[-1]

    @staticmethod
    def _derive_purl(spec: ServerPackageSpec) -> str:
        if spec.purl:
            return spec.purl
        # Fallback heuristic
        eco = spec.ecosystem.lower()
        if eco == "npm":
            return f"pkg:npm/{spec.package_name}"
        elif eco == "pypi":
            return f"pkg:pypi/{spec.package_name}"
        elif eco == "cargo":
            return f"pkg:cargo/{spec.package_name}"
        elif eco == "golang" or eco == "go":
            return f"pkg:golang/{spec.package_name}"
        return f"pkg:generic/{spec.package_name}"

    @staticmethod
    def _build_cyclonedx(specs: list[ServerPackageSpec]) -> dict[str, Any]:
        components = []
        for spec in specs:
            latest = CycloneDXExporter._get_latest_version(spec)
            version_str = latest.version if latest else "0.0.0"
            
            purl = CycloneDXExporter._derive_purl(spec)
            
            comp: dict[str, Any] = {
                "type": "application",
                "name": spec.package_name,
                "version": version_str,
                "purl": purl,
            }
            if spec.description:
                comp["description"] = spec.description
            
            hashes = []
            if latest and latest.toolset_canonical_hash:
                hashes.append({"alg": "SHA-256", "content": latest.toolset_canonical_hash})
            if hashes:
                comp["hashes"] = hashes
                
            if spec.repository_url:
                comp["externalReferences"] = [{"type": "vcs", "url": spec.repository_url}]
                
            if latest and latest.tool_signatures:
                sub_components = []
                for tool in latest.tool_signatures:
                    tool_hash = getattr(tool, "schema_hash", None)
                    if not tool_hash:
                        # Fallback compute if schema_hash missing
                        # In the real model, we might compute based on tool to_dict
                        canonical = canonicalize_json(tool.to_dict())
                        tool_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                    
                    sub = {
                        "type": "library",
                        "bom-ref": f"{spec.package_name}#tool:{tool.name}",
                        "name": f"mcp-tool:{tool.name}",
                        "hashes": [{"alg": "SHA-256", "content": tool_hash}],
                        "properties": [
                            {"name": "mcp:tool:name", "value": tool.name},
                            {"name": "mcp:tool:parameter_count", "value": str(len(tool.input_schema.get("properties", {})) if tool.input_schema else 0)},
                        ]
                    }
                    if tool.description:
                        sub["description"] = tool.description
                    sub_components.append(sub)
                if sub_components:
                    comp["components"] = sub_components
            
            components.append(comp)
            
        doc = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "serialNumber": CycloneDXExporter._generate_uuid(specs),
            "version": 1,
            "metadata": {
                "tools": {
                    "components": [
                        {
                            "type": "application",
                            "name": "mcp-fingerprints",
                            "version": "latest"
                        }
                    ]
                }
            },
            "components": components
        }
        
        # When single package, it can be the primary component
        if len(specs) == 1:
            doc["metadata"]["component"] = {
                "type": "application",
                "name": specs[0].package_name,
                "version": CycloneDXExporter._get_latest_version(specs[0]).version if CycloneDXExporter._get_latest_version(specs[0]) else "0.0.0"
            }
            
        return doc

    @staticmethod
    def _build_spdx(specs: list[ServerPackageSpec]) -> dict[str, Any]:
        packages = []
        relationships = []
        doc_spdx_id = "SPDXRef-DOCUMENT"
        
        for spec in specs:
            latest = CycloneDXExporter._get_latest_version(spec)
            version_str = latest.version if latest else "0.0.0"
            spdx_id = f"SPDXRef-Package-{spec.package_name.replace('/', '-').replace('@', '')}"
            
            pkg: dict[str, Any] = {
                "SPDXID": spdx_id,
                "name": spec.package_name,
                "versionInfo": version_str,
                "downloadLocation": spec.repository_url or "NOASSERTION",
                "licenseConcluded": spec.license or "NOASSERTION",
                "licenseDeclared": spec.license or "NOASSERTION",
                "copyrightText": "NOASSERTION"
            }
            purl = CycloneDXExporter._derive_purl(spec)
            pkg["externalRefs"] = [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": purl
                }
            ]
            if latest and latest.toolset_canonical_hash:
                pkg["checksums"] = [{"algorithm": "SHA256", "checksumValue": latest.toolset_canonical_hash}]
                
            packages.append(pkg)
            relationships.append({
                "spdxElementId": doc_spdx_id,
                "relatedSpdxElement": spdx_id,
                "relationshipType": "DESCRIBES"
            })
            
        return {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": doc_spdx_id,
            "name": "MCP Tool Catalog SBOM",
            "documentNamespace": "http://spdx.org/spdxdocs/mcp-catalog",
            "creationInfo": {
                "creators": ["Tool: mcp-fingerprints"],
            },
            "packages": packages,
            "relationships": relationships
        }

    @staticmethod
    def export(spec_or_specs: Union[ServerPackageSpec, Iterable[ServerPackageSpec]], format: Union[str, SBOMFormat] = SBOMFormat.CYCLONEDX) -> dict[str, Any]:
        specs = [spec_or_specs] if isinstance(spec_or_specs, ServerPackageSpec) else list(spec_or_specs)
        fmt = SBOMFormat(format)
        if fmt == SBOMFormat.SPDX:
            return CycloneDXExporter._build_spdx(specs)
        return CycloneDXExporter._build_cyclonedx(specs)

