"""Maven Central and NuGet Indexer for MCP servers."""

import json
import logging
import urllib.request
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)


def fetch_json(url: str, timeout: int = 15) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "mcp-fingerprints-bot/1.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logger.debug("Failed to fetch %s: %s", url, exc)
    return None


class EnterpriseIndexer:
    """Crawler for JVM and .NET enterprise MCP ecosystems."""

    def discover_maven(self) -> list[dict[str, Any]]:
        """Query Maven Central for MCP-related artifacts."""
        results = []
        queries = [
            'g:"io.modelcontextprotocol"',
            'a:"spring-ai-mcp"',
            'a:"mcp-spring-boot-starter"',
        ]
        for query in queries:
            encoded_query = urllib.parse.quote(query)
            url = f"https://search.maven.org/solrsearch/select?q={encoded_query}&rows=100&wt=json"
            data = fetch_json(url)
            if data and "response" in data and "docs" in data["response"]:
                for doc in data["response"]["docs"]:
                    group_id = doc.get("g")
                    artifact_id = doc.get("a")
                    version = doc.get("latestVersion") or doc.get("v")
                    if group_id and artifact_id:
                        pkg_name = f"{group_id}:{artifact_id}"
                        results.append(
                            {
                                "name": pkg_name,
                                "version": version,
                                "description": f"Maven artifact {pkg_name}",
                                "purl": f"pkg:maven/{group_id}/{artifact_id}@{version}",
                                "ecosystem": "maven",
                            }
                        )
        return results

    def discover_nuget(self) -> list[dict[str, Any]]:
        """Query NuGet for MCP-related packages."""
        results = []
        queries = ["ModelContextProtocol", "McpServer"]
        for query in queries:
            url = f"https://azuresearch-usnc.nuget.org/query?q={urllib.parse.quote(query)}&take=100"
            data = fetch_json(url)
            if data and "data" in data:
                for pkg in data["data"]:
                    pkg_name = pkg.get("id")
                    version = pkg.get("version")
                    description = pkg.get("description", f"NuGet package {pkg_name}")
                    project_url = pkg.get("projectUrl", "")
                    if pkg_name:
                        results.append(
                            {
                                "name": pkg_name,
                                "version": version,
                                "description": description,
                                "repository_url": project_url,
                                "purl": f"pkg:nuget/{pkg_name}@{version}",
                                "ecosystem": "nuget",
                            }
                        )
        return results
