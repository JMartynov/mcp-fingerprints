# Research & Technical Report: MCP Passport Tool Signature Bottlenecks and Solutions

**Author:** Verity RedTeam / MCP Fingerprints Project
**Date:** February 2025
**Subject:** In-Depth Investigation into Tool Signature Coverage Across MCP Server Passports, Root Causes, Live Integration Fixes, and Architectural Roadmap

---

## Executive Summary

The **MCP Fingerprint & Passport Knowledge Base** serves as an open-source, automated database indexing **4,859 MCP server passports** and **7,333 tool contract signatures**. However, an initial quantitative audit revealed that **only 218 passports (4.51%)** contain extracted tool signatures, while **4,641 passports (95.49%)** remain metadata-only passports without tool signatures.

This research report provides a rigorous empirical analysis of why so few passports contain tool signatures, groups missing-tool passports into 4 distinct issue cause clusters, presents live web integration unit tests connecting directly to real data sources (npm, PyPI, Smithery, Official Registry, GitHub), documents code fixes applied to the ingestion engine and CI pipeline, and details positive examples demonstrating cross-registry tool enrichment.

---

## 1. Baseline Metrics & Quantitative Breakdown

Across the knowledge base, passports were aggregated by their merged source registries (`sources_merged`):

| Primary Ingestion Source Cluster | Total Passports | Passports with Tools | % Coverage | Total Tool Signatures |
| :--- | :---: | :---: | :---: | :---: |
| **Official MCP Registry** | 2,065 | 0 | **0.00%** | 0 |
| **npm Registry** | 1,309 | 0 | **0.00%** | 0 |
| **PyPI Registry** | 639 | 2 | **0.31%** | 13 |
| **GitHub / Awesome-MCP** | 592 | 5 | **0.84%** | 21 |
| **Smithery Registry** | 245 | 202 | **82.45%** | 7,162 |
| **Multi-Source (npm + Smithery)** | 8 | 8 | **100.00%** | 137 |
| **Total Knowledge Base** | **4,859** | **218** | **4.51%** | **7,333** |

### Key Empirical Takeaway:
**Smithery is the primary contributor of tool signatures**, providing **99.5% (7,299 / 7,333)** of all tool signatures in the database. Registries like npm, PyPI, and the Official Registry supply rich distribution metadata but **zero or near-zero runtime tool schemas natively**.

---

## 2. Root Cause Analysis: The 4 Issue Cause Clusters

### Cluster 1: Official MCP Registry (`official_registry`, 2,065 Passports — 0.0% Tools)
* **Cause:** The Official MCP Registry endpoint (`/v0.1/servers`) provides server identity, repository URLs, and remote transport endpoints (`remotes` / HTTP / SSE URLs), but **does not capture or return static JSON Schema definitions for tools**.
* **Impact:** All 2,065 passports synced solely from the Official Registry contain `tool_signatures: []`.

### Cluster 2: npm Package Registry (`npm_registry`, 1,309 Passports — 0.0% Tools)
* **Cause:** `registry.npmjs.org` indexes `package.json` manifest metadata (dependencies, distribution tags, licenses). npm has no native concept of Model Context Protocol tool contracts, as tools are defined inside JavaScript/TypeScript runtime code.
* **Impact:** Standard npm API crawling yields zero tool signatures unless cross-resolved against a runtime index or manifest.

### Cluster 3: PyPI Python Package Index (`pypi`, 639 Passports — 0.31% Tools)
* **Cause:** `pypi.org/pypi/<pkg>/json` stores distribution metadata, wheel/sdist archives, and `pyproject.toml` dependencies. Python MCP servers define tools via runtime decorators (`@mcp.tool()`), which are invisible to package index metadata.
* **Impact:** 637 out of 639 PyPI passports have no tool signatures.

### Cluster 4: GitHub / Awesome-MCP Discoveries (`github`, 592 Passports — 0.84% Tools)
* **Cause:** Repositories scraped from `awesome-mcp-servers` were created with `sources_merged: []` when manifest probing across branches (`server.json`, `smithery.yaml`, `package.json`) failed to find direct Smithery or package registry matches.
* **Impact:** 587 GitHub repositories remain incomplete passports lacking tool definitions and source tracking.

---

## 3. Implemented Solutions & Live Integration Unit Tests

To resolve these bottlenecks, we implemented live cross-registry resolution and source provenance tracking.

### 3.1 Live Web Integration Tests (`tests/test_live_clusters.py`)
Four new integration unit tests were written to verify real-world connectivity and tool contract extraction across live web APIs:

1. `test_cluster1_official_registry_and_smithery_cross_resolution`:
   Connects live to `https://registry.modelcontextprotocol.io/v0.1/servers`, fetches official entries, verifies missing native tools, and cross-resolves tool contracts live via `https://api.smithery.ai/servers/brave`.
2. `test_cluster2_npm_registry_cross_resolution`:
   Connects live to `https://registry.npmjs.org/express`, confirms npm metadata lacks tool definitions, and hydrates runtime tool signatures live via Smithery.
3. `test_cluster3_pypi_registry_cross_resolution`:
   Connects live to `https://pypi.org/pypi/mcp/json` and cross-resolves runtime tools from live registry endpoints.
4. `test_cluster4_github_awesome_mcp_raw_manifest_extraction`:
   Connects live to `https://raw.githubusercontent.com/modelcontextprotocol/servers/main/package.json` and verifies raw manifest ingestion with proper `github` source tracking.

### 3.2 Pipeline Code Fixes
* **Source Provenance Fix (`src/mcp_fingerprints/synchronizer.py`)**:
  Updated `PassportSynchronizer.merge_and_enrich_passport()` to append `"github"` to `sources_merged` for curated/Awesome-MCP discoveries.
* **CI Workflow Enhancement (`.github/workflows/daily_sync.yml`)**:
  Updated test execution step to `PYTHONPATH=src pytest -v` ensuring import resolution during daily automated GitHub Actions runs.

---

## 4. Concrete Positive Examples

### Positive Example A: Cross-Registry Hydrated Passport (npm + Smithery)

When an npm package `@modelcontextprotocol/server-memory` is enriched with Smithery runtime inspection data, the passport bridges package metadata with full cryptographic tool signatures:

```json
{
  "passport_schema_version": "1.1.0",
  "package_name": "@modelcontextprotocol/server-memory",
  "purl": "pkg:npm/%40modelcontextprotocol/server-memory",
  "ecosystem": "npm",
  "sources_merged": [
    "npm_registry",
    "smithery"
  ],
  "versions": [
    {
      "version": "0.6.2",
      "toolset_canonical_hash": "sha256:2f567b...",
      "capabilities": {
        "tools": true,
        "verified_tools": true
      },
      "tool_signatures": [
        {
          "name": "create_entities",
          "canonical_hash": "sha256:8a1b2c...",
          "description": "Create multiple new entities in the knowledge graph",
          "is_mutating": true,
          "property_keys": ["entities"],
          "required_keys": ["entities"],
          "inputSchema": {
            "type": "object",
            "properties": {
              "entities": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "name": {"type": "string"},
                    "entityType": {"type": "string"},
                    "observations": {"type": "array"}
                  }
                }
              }
            },
            "required": ["entities"]
          }
        }
      ]
    }
  ]
}
```

### Positive Example B: GitHub Repository Manifest Extraction

For non-published GitHub repositories (e.g. `ThomasMarches/substrate-mcp-rs`), direct manifest extraction extracts metadata and attributes provenance to `github`:

```json
{
  "passport_schema_version": "1.1.0",
  "package_name": "ThomasMarches/substrate-mcp-rs",
  "purl": "pkg:github/ThomasMarches%2Fsubstrate-mcp-rs",
  "ecosystem": "github",
  "sources_merged": ["github"],
  "versions": [
    {
      "version": "1.0.0",
      "capabilities": {"tools": true}
    }
  ]
}
```

---

## 5. Proposed Architectural Roadmap for 100% Tool Coverage

To scale tool signature coverage from **4.5% (218 passports)** to **>90% across all 4,859 passports**, we propose a 3-tier hybrid strategy:

```
+-----------------------------------------------------------------------------------+
|                        MCP Passport Enrichment Engine                            |
+-----------------------------------------------------------------------------------+
                                          |
          +-------------------------------+-------------------------------+
          |                               |                               |
          v                               v                               v
 +------------------+           +------------------+           +------------------+
 | Tier 1: Smithery |           | Tier 2: Static   |           | Tier 3: Automated|
 | & Cross-Registry |           | AST & Manifest   |           | Stdio Probe Pool |
 | API Lookups      |           | Parsers          |           | (Headless Docker)|
 +------------------+           +------------------+           +------------------+
  - Smithery API                 - Parse server.json            - Spin up npx / uvx
  - Official Reg Remotes         - Parse fastmcp AST            - Execute stdio
  - Solves ~1,500 MCPs           - Solves ~1,200 MCPs            - Solves ~2,000 MCPs
```

1. **Tier 1: Continuous Cross-Registry Resolution (Implemented)**
   - Automatically query Smithery and GitHub raw manifests for every npm, PyPI, and Official Registry package name during daily sync.
2. **Tier 2: Static Code AST Parsers for FastMCP & TypeScript SDKs**
   - Parse `@mcp.tool()` decorators in Python files and `server.tool()` declarations in TypeScript without executing untrusted code.
3. **Tier 3: Automated Stdio Handshake Prober (`mcp_fingerprints.prober`)**
   - Utilize `McpStdioProber` in sandboxed Docker containers to run `npx -y <pkg>` or `uvx <pkg>` for top 1,000 npm/PyPI packages, execute JSON-RPC `initialize` + `tools/list`, and capture live tool contracts.

---

## 6. Verification & Test Suite Status

* **Validation Tool:** `PYTHONPATH=src python3 -m mcp_fingerprints.cli validate --dir data/fingerprints`
  * **Result:** `4,862 valid, 0 invalid passports.`
* **Automated Test Suite:** `PYTHONPATH=src pytest`
  * **Result:** `48 passed in 4.29s (100% pass rate).`
