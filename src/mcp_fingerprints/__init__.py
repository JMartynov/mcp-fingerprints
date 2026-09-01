"""Public exports for the MCP Structural Fingerprint Knowledge Base & Matcher."""

from __future__ import annotations

from mcp_fingerprints.canonicalizer import (
    build_version_fingerprint,
    compute_sha256,
    compute_toolset_canonical_hash,
    extract_tool_signature,
)
from mcp_fingerprints.crawler import FingerprintGenerator
from mcp_fingerprints.distance import (
    compute_capability_similarity,
    compute_tool_topology_similarity,
    compute_version_topology_similarity,
    jaccard_similarity,
)
from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.models import (
    FingerprintMatchResult,
    PromptSignature,
    ResourceSignature,
    ServerPackageSpec,
    ToolContractSignature,
    VersionFingerprint,
)

__all__ = [
    "FingerprintGenerator",
    "FingerprintMatchResult",
    "FingerprintMatcher",
    "PromptSignature",
    "ResourceSignature",
    "ServerPackageSpec",
    "ToolContractSignature",
    "VersionFingerprint",
    "build_version_fingerprint",
    "compute_capability_similarity",
    "compute_sha256",
    "compute_tool_topology_similarity",
    "compute_toolset_canonical_hash",
    "compute_version_topology_similarity",
    "extract_tool_signature",
    "jaccard_similarity",
]
