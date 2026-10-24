import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch

from mcp_fingerprints.models import (
    ServerPackageSpec,
    VersionFingerprint,
    ToolContractSignature,
    PromptSignature,
    ResourceSignature,
)
from mcp_fingerprints.canonicalizer import compute_toolset_canonical_hash
from mcp_fingerprints.distance import (
    jaccard_similarity,
    compute_tool_topology_similarity,
    compute_version_topology_similarity,
    compute_capability_similarity,
)
from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.index import FingerprintFastIndex
from mcp_fingerprints.semantic_search import semantic_search

def test_layer_1_exact_cryptographic_matching():
    """Verify O(1) hash lookup via FingerprintFastIndex._by_toolset_hash."""
    index = FingerprintFastIndex()
    
    # Create synthetic tools
    tool1 = ToolContractSignature(
        name="test_tool",
        canonical_hash="hash1",
        description="A test tool",
        property_keys=("prop1", "prop2"),
        required_keys=("prop1",),
        parameter_types={"prop1": "string", "prop2": "integer"}
    )
    toolset_hash = compute_toolset_canonical_hash([tool1.to_dict()])
    
    version = VersionFingerprint(
        version="1.0.0",
        toolset_canonical_hash=toolset_hash,
        tool_signatures=(tool1,)
    )
    spec = ServerPackageSpec(
        package_name="test-package",
        purl="pkg:npm/test-package@1.0.0",
        ecosystem="npm",
        versions=(version,)
    )
    
    index.register_package(spec)
    
    assert toolset_hash in index.by_toolset_hash
    candidates = index.by_toolset_hash[toolset_hash]
    assert len(candidates) == 1
    assert candidates[0][0] == "test-package"
    assert candidates[0][1].version == "1.0.0"

    matcher = FingerprintMatcher(index=index)
    match_result = matcher.match(tools=[tool1.to_dict()])
    assert match_result.matched
    assert match_result.match_layer == "LAYER_1_EXACT"
    assert match_result.package_name == "test-package"
    assert match_result.confidence_score == 1.0


def test_layer_2_topology_jaccard_distance():
    """Verify similarity scoring on tool names, parameters, and property types."""
    # Test jaccard
    assert jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0
    assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0
    # union of {a,b} and {a,c} is {a,b,c} (len 3). Intersection is {a} (len 1). Jaccard = 1/3
    assert abs(jaccard_similarity({"a", "b"}, {"a", "c"}) - 1/3) < 0.001
    
    tool1 = ToolContractSignature(
        name="test_tool",
        canonical_hash="hash1",
        property_keys=("prop1", "prop2", "prop3"),
        required_keys=("prop1", "prop2"),
        parameter_types={"prop1": "string", "prop2": "integer", "prop3": "boolean"}
    )
    
    tool2 = ToolContractSignature(
        name="test_tool",
        canonical_hash="hash2",
        property_keys=("prop1", "prop2", "prop4"),
        required_keys=("prop1",),
        parameter_types={"prop1": "string", "prop2": "string", "prop4": "boolean"}
    )
    
    score = compute_tool_topology_similarity(tool1, tool2)
    # props: jaccard({"prop1", "prop2", "prop3"}, {"prop1", "prop2", "prop4"}) -> union is 4, intersection is 2 -> 2/4 = 0.5
    # req: jaccard({"prop1", "prop2"}, {"prop1"}) -> union is 2, intersection is 1 -> 1/2 = 0.5
    # types: common {"prop1", "prop2"}, prop1 matches, prop2 differs -> 1/2 = 0.5
    # 0.4 * 0.5 + 0.3 * 0.5 + 0.3 * 0.5 = 0.2 + 0.15 + 0.15 = 0.5
    assert abs(score - 0.5) < 0.001

    # Boundary case: Names match but schemas differ significantly
    tool3 = ToolContractSignature(
        name="test_tool",
        canonical_hash="hash3",
        property_keys=("x", "y"),
        required_keys=("x",),
        parameter_types={"x": "number", "y": "number"}
    )
    score_diff = compute_tool_topology_similarity(tool1, tool3)
    # props = 0, req = 0, common props = empty -> type_score = 1.0
    # 0.4*0 + 0.3*0 + 0.3*1.0 = 0.3
    assert abs(score_diff - 0.3) < 0.001


def test_layer_3_composite_capability_matching():
    """Verify weighted similarity formula (0.7 * Topology + 0.3 * Capabilities)."""
    # 0.7 * topo + 0.3 * cap
    tool1 = ToolContractSignature(
        name="test_tool",
        canonical_hash="hash1",
        property_keys=("prop1",),
        required_keys=("prop1",),
        parameter_types={"prop1": "string"}
    )
    
    version = VersionFingerprint(
        version="1.0.0",
        toolset_canonical_hash="hash1",
        tool_signatures=(tool1,),
        prompt_signatures=(PromptSignature(name="prompt1"),),
        resource_signatures=(ResourceSignature(uri_template="res1", name="Res 1"),)
    )
    
    index = FingerprintFastIndex()
    spec = ServerPackageSpec(
        package_name="test-package",
        purl="pkg:npm/test-package@1.0.0",
        ecosystem="npm",
        versions=(version,)
    )
    index.register_package(spec)
    
    matcher = FingerprintMatcher(index=index)
    
    # Observe identical tool, but no prompts/resources
    obs_tool = tool1.to_dict()
    obs_tool["canonical_hash"] = "diff_hash" # Force layer 2/3 evaluation
    obs_tool["inputSchema"] = {
        "type": "object",
        "properties": {
            "prop1": {"type": "string"}
        },
        "required": ["prop1"]
    }
    
    match_result = matcher.match(
        tools=[obs_tool],
        prompts=[],
        resources=[],
        min_confidence_threshold=0.65
    )
    
    assert match_result.matched
    # Topo score calculation:
    # obs_names = {"test_tool"}, known_names = {"test_tool"}
    # j_names = 1.0
    # compute_tool_topology_similarity(tool1, tool1_reconstructed) 
    # extract_tool_signature is called on tools=[obs_tool].
    # j_props = 1.0, j_req = 1.0, type_score = 1.0 -> 1.0
    # topo = 0.5 * 1.0 + 0.5 * 1.0 = 1.0
    # cap = 0.5 * j_prompts(0.0) + 0.5 * j_resources(0.0) = 0.0
    # Composite = 0.7 * 1.0 + 0.3 * 0.0 = 0.7
    assert match_result.match_layer == "LAYER_2_TOPOLOGY"
    assert abs(match_result.confidence_score - 0.7) < 0.001


def test_semantic_search_fallback(tmp_path):
    """Test semantic_search.py fallback to lexical search when fastembed is unavailable."""
    # Create fake passport dir
    passport = {
        "package_name": "test-semantic-fallback",
        "ecosystem": "npm",
        "description": "Lexical test package",
        "keywords": ["test"],
        "versions": []
    }
    
    with open(tmp_path / "test.json", "w") as f:
        json.dump(passport, f)
        
    # Mock HAS_FASTEMBED to False
    with patch("mcp_fingerprints.semantic_search.HAS_FASTEMBED", False):
        results = semantic_search(
            query="Lexical",
            passports_dir=tmp_path,
            top_k=10
        )
        
        assert len(results) > 0
        assert results[0]["package_name"] == "test-semantic-fallback"
        # Should be lexical score, not float similarity
        assert isinstance(results[0]["score"], int)


def test_index_scalability():
    """Benchmark FingerprintFastIndex with 2,000 synthetic passports."""
    index = FingerprintFastIndex()
    
    start = time.perf_counter()
    for i in range(2000):
        tool = ToolContractSignature(
            name=f"tool_{i}",
            canonical_hash=f"hash_{i}",
            property_keys=(f"prop_{i}",),
            required_keys=(f"prop_{i}",),
            parameter_types={f"prop_{i}": "string"}
        )
        version = VersionFingerprint(
            version="1.0.0",
            toolset_canonical_hash=f"ts_hash_{i}",
            tool_signatures=(tool,)
        )
        spec = ServerPackageSpec(
            package_name=f"pkg_{i}",
            purl=f"pkg:npm/pkg_{i}@1.0.0",
            ecosystem="npm",
            versions=(version,)
        )
        index.register_package(spec)
        
    duration = time.perf_counter() - start
    # Ensure it's reasonably fast (e.g. under 1 second)
    assert duration < 2.0
    
    # Test latency of lookup
    start = time.perf_counter()
    res = index.find_package_by_hint_or_alias("pkg_1500")
    duration = time.perf_counter() - start
    
    assert res is not None
    assert res.package_name == "pkg_1500"
    assert duration < 0.01  # O(1) should be extremely fast
    
    # Test collision resistance (no dropped packages)
    assert len(index.packages) == 2000
    assert len(index.by_toolset_hash) == 2000
