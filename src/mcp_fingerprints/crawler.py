"""Ecosystem crawler and signature generator for extracting fingerprints from MCP toolsets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp_fingerprints.canonicalizer import (
    build_version_fingerprint,
)
from mcp_fingerprints.models import (
    ServerPackageSpec,
    VersionFingerprint,
)


class FingerprintGenerator:
    """Utilities for generating, building, and persisting structural MCP fingerprints."""

    @classmethod
    def generate_server_spec(
        cls,
        package_name: str,
        ecosystem: str,
        purl: str,
        version: str,
        tools: list[dict[str, Any]],
        prompts: list[dict[str, Any]] | None = None,
        resources: list[dict[str, Any]] | None = None,
        repository_url: str | None = None,
        description: str | None = None,
        release_date: str | None = None,
    ) -> ServerPackageSpec:
        """Create a ServerPackageSpec with an initial version fingerprint."""
        ver_fp = build_version_fingerprint(
            version=version,
            tools=tools,
            prompts=prompts,
            resources=resources,
            release_date=release_date,
        )
        return ServerPackageSpec(
            package_name=package_name,
            purl=purl,
            ecosystem=ecosystem,
            repository_url=repository_url,
            description=description,
            versions=(ver_fp,),
        )

    @classmethod
    def add_version_to_spec(
        cls,
        existing_spec: ServerPackageSpec,
        version: str,
        tools: list[dict[str, Any]],
        prompts: list[dict[str, Any]] | None = None,
        resources: list[dict[str, Any]] | None = None,
        release_date: str | None = None,
    ) -> ServerPackageSpec:
        """Append or update a version fingerprint within an existing package specification."""
        ver_fp = build_version_fingerprint(
            version=version,
            tools=tools,
            prompts=prompts,
            resources=resources,
            release_date=release_date,
        )
        # Filter out existing version if present
        updated_versions: list[VersionFingerprint] = [
            v for v in existing_spec.versions if v.version != version
        ]
        updated_versions.append(ver_fp)
        # Sort versions
        return ServerPackageSpec(
            package_name=existing_spec.package_name,
            purl=existing_spec.purl,
            ecosystem=existing_spec.ecosystem,
            repository_url=existing_spec.repository_url,
            description=existing_spec.description,
            versions=tuple(sorted(updated_versions, key=lambda x: x.version)),
        )

    @classmethod
    def save_spec_to_file(cls, spec: ServerPackageSpec, output_path: str | Path) -> None:
        """Serialize and write a ServerPackageSpec to formatted JSON file."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = spec.to_dict()
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
