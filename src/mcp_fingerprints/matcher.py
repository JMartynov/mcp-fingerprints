"""Tri-Layer Fingerprint Matcher and in-memory knowledge base registry."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mcp_fingerprints.canonicalizer import (
    compute_toolset_canonical_hash,
    extract_tool_signature,
)
from mcp_fingerprints.distance import (
    compute_capability_similarity,
    compute_version_topology_similarity,
)
from mcp_fingerprints.index import FingerprintFastIndex
from mcp_fingerprints.models import (
    FingerprintMatchResult,
    ServerPackageSpec,
    VersionFingerprint,
)

logger = logging.getLogger("mcp_fingerprints.matcher")


class FingerprintMatcher:
    """High-performance Tri-Layer matching engine with O(1) multi-indexing."""

    def __init__(self, index: FingerprintFastIndex | None = None) -> None:
        self.fast_index = index or FingerprintFastIndex()

    @property
    def _packages(self) -> dict[str, ServerPackageSpec]:
        return self.fast_index.packages

    @property
    def _by_toolset_hash(self) -> dict[str, list[tuple[str, VersionFingerprint]]]:
        return self.fast_index.by_toolset_hash

    @property
    def _by_tool_name(self) -> dict[str, set[str]]:
        return self.fast_index.by_tool_name

    @property
    def total_packages(self) -> int:
        return len(self.fast_index.packages)

    @property
    def total_version_signatures(self) -> int:
        return sum(len(p.versions) for p in self.fast_index.packages.values())

    def register_package(self, spec: ServerPackageSpec) -> None:
        """Add or update a ServerPackageSpec in the in-memory fingerprint registry."""
        self.fast_index.register_package(spec)

    def load_from_directory(self, directory: str | Path, use_cache: bool = True) -> int:
        """Load and index all JSON fingerprint files using fast binary cache."""
        return self.fast_index.load_from_directory(directory, use_cache=use_cache)

    def match(
        self,
        tools: list[dict[str, Any]],
        prompts: list[dict[str, Any]] | None = None,
        resources: list[dict[str, Any]] | None = None,
        server_name_hint: str | None = None,
        min_confidence_threshold: float = 0.65,
    ) -> FingerprintMatchResult:
        """Match observed tools/prompts/resources against the fingerprint knowledge base.

        Evaluates across 3 layers:
        - Layer 1: Exact canonical toolset contract hash.
        - Layer 2: Tool/schema topology Jaccard distance.
        - Layer 3: Protocol capability vector (prompts & resources).
        """
        if not tools:
            return FingerprintMatchResult(
                matched=False,
                confidence_score=0.0,
                match_layer="NONE",
            )

        observed_tool_sigs = tuple(
            sorted((extract_tool_signature(t) for t in tools), key=lambda x: x.name)
        )
        observed_toolset_hash = compute_toolset_canonical_hash(tools)
        observed_tool_names = [t.name for t in observed_tool_sigs]

        observed_prompt_names = tuple(
            p.get("name", "") for p in prompts or [] if isinstance(p, dict)
        )
        observed_resource_uris = tuple(
            r.get("uriTemplate") or r.get("uri", "") for r in resources or [] if isinstance(r, dict)
        )

        # ---------------------------------------------------------------------
        # LAYER 1: Exact Canonical Toolset Hash Match (Fast-Path)
        # ---------------------------------------------------------------------
        if observed_toolset_hash in self._by_toolset_hash:
            candidates = self._by_toolset_hash[observed_toolset_hash]
            best_pkg_name, best_ver = candidates[0]
            if server_name_hint:
                # If multiple packages share the identical hash, pick matching hint
                for pkg_name, ver in candidates:
                    if server_name_hint.lower() in pkg_name.lower():
                        best_pkg_name, best_ver = pkg_name, ver
                        break

            pkg_spec = self._packages.get(best_pkg_name)
            return FingerprintMatchResult(
                matched=True,
                package_name=best_pkg_name,
                purl=pkg_spec.purl if pkg_spec else None,
                matched_version=best_ver.version,
                confidence_score=1.0,
                match_layer="LAYER_1_EXACT",
                layer1_exact_match=True,
                layer2_topology_score=1.0,
                layer3_capability_score=1.0,
                matched_tool_count=len(observed_tool_sigs),
                total_observed_tools=len(observed_tool_sigs),
            )

        # ---------------------------------------------------------------------
        # LAYER 2 & 3: Fuzzy Topology & Protocol Capability Similarity
        # ---------------------------------------------------------------------
        best_match: FingerprintMatchResult | None = None
        highest_score = 0.0

        # Narrow candidate packages by tool name overlap or server name hint
        candidate_pkg_names: set[str] = set()
        if server_name_hint:
            norm_hint = server_name_hint.strip().lower()
            for p_name in self._packages:
                if norm_hint in p_name.lower():
                    candidate_pkg_names.add(p_name)

        if not candidate_pkg_names:
            for t_name in observed_tool_names:
                for p_name in self._by_tool_name.get(t_name, ()):
                    candidate_pkg_names.add(p_name)

        # If still empty, evaluate all packages in registry
        if not candidate_pkg_names:
            candidate_pkg_names = set(self._packages.keys())

        for p_name in candidate_pkg_names:
            pkg_spec = self._packages[p_name]
            for ver_sig in pkg_spec.versions:
                topo_score, unmatched_obs, missing_known = compute_version_topology_similarity(
                    observed_tools=observed_tool_sigs,
                    known_version=ver_sig,
                )

                cap_score = compute_capability_similarity(
                    observed_prompts=observed_prompt_names,
                    observed_resources=observed_resource_uris,
                    known_version=ver_sig,
                )

                # Composite score: 70% topology + 30% capabilities
                composite_score = 0.7 * topo_score + 0.3 * cap_score

                if composite_score > highest_score:
                    highest_score = composite_score
                    matched_count = len(observed_tool_names) - len(unmatched_obs)
                    best_match = FingerprintMatchResult(
                        matched=composite_score >= min_confidence_threshold,
                        package_name=p_name,
                        purl=pkg_spec.purl,
                        matched_version=ver_sig.version,
                        confidence_score=composite_score,
                        match_layer="LAYER_2_TOPOLOGY"
                        if topo_score >= cap_score
                        else "LAYER_3_CAPABILITY",
                        layer1_exact_match=False,
                        layer2_topology_score=topo_score,
                        layer3_capability_score=cap_score,
                        matched_tool_count=max(0, matched_count),
                        total_observed_tools=len(observed_tool_sigs),
                        unmatched_observed_tools=unmatched_obs,
                        missing_expected_tools=missing_known,
                    )

        if best_match and best_match.confidence_score >= min_confidence_threshold:
            return best_match

        return FingerprintMatchResult(
            matched=False,
            confidence_score=highest_score,
            match_layer="NONE",
            total_observed_tools=len(observed_tool_sigs),
            unmatched_observed_tools=observed_tool_names,
        )
