import urllib.request
import urllib.error
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

def query_crates_io(query: str, page: int = 1, per_page: int = 50) -> list[dict[str, Any]]:
    url = f"https://crates.io/api/v1/crates?q={query}&page={page}&per_page={per_page}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "VerityRedTeam-MCPPassportSync/1.0"
    })
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("crates", [])
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch from crates.io: {e}")
        return []

def get_mcp_crates() -> list[dict[str, Any]]:
    crates = []
    
    # Query 'mcp'
    crates.extend(query_crates_io("mcp"))
    
    # Query by keyword 'mcp'
    url = "https://crates.io/api/v1/crates?keyword=mcp&page=1&per_page=50"
    req = urllib.request.Request(url, headers={
        "User-Agent": "VerityRedTeam-MCPPassportSync/1.0"
    })
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            crates.extend(data.get("crates", []))
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch keyword mcp from crates.io: {e}")
        
    url2 = "https://crates.io/api/v1/crates?keyword=model-context-protocol&page=1&per_page=50"
    req2 = urllib.request.Request(url2, headers={
        "User-Agent": "VerityRedTeam-MCPPassportSync/1.0"
    })
    try:
        with urllib.request.urlopen(req2) as response:
            data = json.loads(response.read().decode("utf-8"))
            crates.extend(data.get("crates", []))
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch keyword model-context-protocol from crates.io: {e}")

    # Deduplicate crates by name
    seen = set()
    unique_crates = []
    for crate in crates:
        name = crate.get("name")
        if name and name not in seen:
            seen.add(name)
            unique_crates.append(crate)
            
    return unique_crates
