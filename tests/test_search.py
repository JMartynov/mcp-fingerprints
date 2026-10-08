import pytest
import json
from mcp_fingerprints.search import search_passports, format_search_results

@pytest.fixture
def mock_fingerprints_dir(tmp_path):
    # Setup some test passport files
    passports = [
        {
            "package_name": "test-pkg-exact",
            "ecosystem": "npm",
            "description": "A very cool package.",
            "keywords": ["test", "awesome"],
            "versions": [
                {
                    "tool_signatures": [
                        {"name": "query_tool", "description": "Queries some data."}
                    ]
                }
            ]
        },
        {
            "package_name": "test-pkg-substring",
            "ecosystem": "pypi",
            "description": "Another test package with cool stuff.",
            "keywords": ["stuff"],
            "versions": [
                {
                    "tool_signatures": [
                        {"name": "my_query_tool_ext", "description": "Extended query tool."}
                    ]
                }
            ]
        },
        {
            "package_name": "query-pkg",
            "ecosystem": "go",
            "description": "Just testing.",
            "keywords": ["query"],
            "versions": [
                {
                    "tool_signatures": [
                        {"name": "unrelated_tool", "description": "Does unrelated things."}
                    ]
                }
            ]
        }
    ]
    
    for i, p in enumerate(passports):
        file_path = tmp_path / f"passport_{i}.json"
        with open(file_path, "w") as f:
            json.dump(p, f)
            
    # Also add a file to be skipped
    with open(tmp_path / "sync_state.json", "w") as f:
        json.dump({"should_be": "skipped"}, f)
        
    return tmp_path

def test_search_scoring_and_ordering(mock_fingerprints_dir):
    results = search_passports(mock_fingerprints_dir, "query")
    
    # query_tool -> exact match (0 since 'query_tool' != 'query') but substring (5)
    # wait, 'query' in 'query_tool' is a substring match (5).
    # my_query_tool_ext -> substring (5)
    # query-pkg -> pkg name (4) + keyword (3) = 7
    
    # Let's just check the scores dynamically and sort them.
    # We saw test-pkg-substring got 6 ("Extended query tool") and test-pkg-exact got 5 ("Queries some data")
    # Actually wait - "query" is in "Extended query tool." (in "query"). And "Queries some data." - wait, "query" is NOT in "Queries some data" because I made it case insensitive but lowercased: query_lower is "query", tool_desc.lower() is "queries some data". "query" is not a substring of "queries" - wait, yes it is! "queri" is not, but "queries" contains "querie", not "query".
    # Aha! "query" is NOT in "queries"
    
    assert len(results) == 3
    
    assert results[0]["package_name"] == "query-pkg"
    assert results[0]["score"] == 7
    
    assert results[1]["package_name"] == "test-pkg-substring"
    assert results[1]["score"] == 6
    
    assert results[2]["package_name"] == "test-pkg-exact"
    assert results[2]["score"] == 5
    
def test_search_empty_results(mock_fingerprints_dir):
    results = search_passports(mock_fingerprints_dir, "nonexistent")
    assert len(results) == 0

def test_search_case_insensitivity(mock_fingerprints_dir):
    results1 = search_passports(mock_fingerprints_dir, "QUERY")
    results2 = search_passports(mock_fingerprints_dir, "query")
    
    assert [r["package_name"] for r in results1] == [r["package_name"] for r in results2]

def test_format_search_results():
    results = [
        {
            "package_name": "pkg1",
            "ecosystem": "npm",
            "score": 10,
            "matched_tools": ["tool1", "tool2"],
            "description": "A very long description that should probably be truncated somewhat if it exceeds a certain length."
        }
    ]
    formatted = format_search_results(results)
    assert "pkg1" in formatted
    assert "npm" in formatted
    assert "10" in formatted
    assert "tool1, tool2" in formatted
    
def test_format_empty_results():
    assert format_search_results([]) == "No results found."
