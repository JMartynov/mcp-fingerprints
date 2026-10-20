import json
import os
import urllib.parse

def test_json_exists():
    assert os.path.exists("docs/research/mcp_candidates_by_group.json")

def test_groups_exist_and_len():
    with open("docs/research/mcp_candidates_by_group.json", "r") as f:
        data = json.load(f)
        
    expected_groups = [
        "rust_systems",
        "go_cloud_native",
        "jvm_dotnet_enterprise",
        "regional_international",
        "monorepo_docker_emerging"
    ]
    
    for group in expected_groups:
        assert group in data, f"Group {group} missing"
        assert len(data[group]) == 200, f"Group {group} has {len(data[group])} items, expected 200"

def test_urls_well_formed():
    with open("docs/research/mcp_candidates_by_group.json", "r") as f:
        data = json.load(f)
        
    for group, items in data.items():
        for item in items:
            url = item.get("location")
            assert isinstance(url, str), f"Location {url} is not a string"
            assert url.startswith("http://") or url.startswith("https://"), f"Location {url} does not start with http:// or https://"
            parsed = urllib.parse.urlparse(url)
            assert parsed.scheme in ["http", "https"], f"Invalid scheme in {url}"
            assert parsed.netloc != "", f"Empty netloc in {url}"

def test_zero_duplicates():
    with open("docs/research/mcp_candidates_by_group.json", "r") as f:
        data = json.load(f)
        
    seen_urls = set()
    for group, items in data.items():
        for item in items:
            url = item.get("location")
            assert url not in seen_urls, f"Duplicate URL found: {url}"
            seen_urls.add(url)
            
    assert len(seen_urls) == 1000, f"Expected 1000 unique URLs, got {len(seen_urls)}"
