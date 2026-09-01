"""Distance, similarity metrics, and topology vector calculators for MCP contracts."""

from __future__ import annotations

from typing import Any

from mcp_fingerprints.models import ToolContractSignature, VersionFingerprint


def jaccard_similarity(set_a: set[Any], set_b: set[Any]) -> float:
    """Compute standard Jaccard similarity index between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    if union == 0:
        return 1.0
    return float(intersection) / float(union)


def compute_tool_topology_similarity(
    sig_a: ToolContractSignature,
    sig_b: ToolContractSignature,
) -> float:
    """Compute structural similarity between two tools with identical or similar names."""
    if sig_a.name != sig_b.name:
        return 0.0

    # If canonical hash matches exactly
    if sig_a.canonical_hash == sig_b.canonical_hash:
        return 1.0

    # 1. Properties Jaccard similarity
    props_a = set(sig_a.property_keys)
    props_b = set(sig_b.property_keys)
    j_props = jaccard_similarity(props_a, props_b)

    # 2. Required fields Jaccard similarity
    req_a = set(sig_a.required_keys)
    req_b = set(sig_b.required_keys)
    j_req = jaccard_similarity(req_a, req_b)

    # 3. Type compatibility
    matching_types = 0
    common_props = props_a.intersection(props_b)
    for p in common_props:
        if sig_a.parameter_types.get(p) == sig_b.parameter_types.get(p):
            matching_types += 1
    type_score = float(matching_types) / float(len(common_props)) if common_props else 1.0

    return 0.4 * j_props + 0.3 * j_req + 0.3 * type_score


def compute_version_topology_similarity(
    observed_tools: tuple[ToolContractSignature, ...],
    known_version: VersionFingerprint,
) -> tuple[float, list[str], list[str]]:
    """Compute Layer 2 toolset topology similarity and track missing/extra tools."""
    obs_names = {t.name for t in observed_tools}
    known_names = {t.name for t in known_version.tool_signatures}

    j_names = jaccard_similarity(obs_names, known_names)
    if j_names == 0.0:
        return 0.0, list(obs_names), list(known_names)

    # Compute pairwise tool similarity for shared tools
    obs_map = {t.name: t for t in observed_tools}
    known_map = {t.name: t for t in known_version.tool_signatures}

    tool_scores: list[float] = []
    common_names = obs_names.intersection(known_names)
    for name in common_names:
        score = compute_tool_topology_similarity(obs_map[name], known_map[name])
        tool_scores.append(score)

    avg_tool_score = sum(tool_scores) / float(len(tool_scores)) if tool_scores else 0.0

    # Topology score combines toolset coverage and individual schema consistency
    final_score = 0.5 * j_names + 0.5 * avg_tool_score

    unmatched_obs = sorted(list(obs_names - known_names))
    missing_known = sorted(list(known_names - obs_names))

    return final_score, unmatched_obs, missing_known


def compute_capability_similarity(
    observed_prompts: tuple[str, ...],
    observed_resources: tuple[str, ...],
    known_version: VersionFingerprint,
) -> float:
    """Compute Layer 3 protocol capability similarity for prompts and resources."""
    known_prompts = {p.name for p in known_version.prompt_signatures}
    known_resources = {r.uri_template for r in known_version.resource_signatures}

    j_prompts = jaccard_similarity(set(observed_prompts), known_prompts)
    j_resources = jaccard_similarity(set(observed_resources), known_resources)

    # If neither observed nor known has prompts/resources, neutral 1.0
    if (
        not observed_prompts
        and not known_prompts
        and not observed_resources
        and not known_resources
    ):
        return 1.0

    return 0.5 * j_prompts + 0.5 * j_resources
