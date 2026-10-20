# Task Contract: Discover and Catalog 200 Real MCP Servers per Representative Group (1,000 Total)

## Context & Objectives
An investigation into why high-value servers like CodeScene MCP were missing from `mcp-fingerprints` revealed systemic blind spots in our internal crawlers (tag mismatches, missing GitHub topics, unindexed registries like Crates.io/NuGet/Maven, monorepos, and non-standard SDK patterns).

To systematically map and eliminate these blind spots, we require an independent, external empirical survey across **5 diverse representative groups**, cataloging **exactly 200 real, publicly verifiable MCP servers per group** (1,000 total).

## Methodological Rules
1. **Independent Discovery Only**: Candidates must be discovered from external sources (web search, package index APIs, GitHub API with varied search queries, alternative registries like Glama/PulseMCP/mcp.so, community awesome lists, regional dev platforms like Gitee/Qiita/Zenn). Do NOT rely on the repo's existing `synchronizer.py` queries.
2. **Real and Verifiable**: Every candidate must be a real Model Context Protocol server with a verifiable repository, package, or container URL.
3. **Exact Quotas**: Every one of the 5 groups must contain **exactly 200 unique entries** (total 1,000 entries). No duplicates across or within groups.

## The 5 Representative Groups (200 Each)

1. **Group 1: Rust & Systems Polyglot (200 servers)**
   - Technologies: Rust (`rmcp`, `mcp-sdk-rs`, custom JSON-RPC), C/C++, native binaries.
   - Sources: Crates.io, GitHub Rust projects, Homebrew formulas.
2. **Group 2: Go & Cloud-Native / Infrastructure (200 servers)**
   - Technologies: Go (`mark3labs/mcp-go`, `mcp-golang`), Kubernetes, Docker, cloud tooling.
   - Sources: `pkg.go.dev`, GitHub Go projects.
3. **Group 3: JVM (Java/Kotlin) & .NET (C#) Enterprise (200 servers)**
   - Technologies: Java, Kotlin, C#, F#, Spring AI MCP, Quarkus MCP, Microsoft Semantic Kernel MCP, vendor/enterprise tools.
   - Sources: Maven Central, NuGet, GitHub, vendor developer portals.
4. **Group 4: Regional & International Dev Communities (200 servers)**
   - Technologies: Polyglot servers originating from non-English developer hubs.
   - Sources: Gitee, GitHub Chinese dev communities (Dify plugins, WeChat/WeCom, Bilibili), Japanese platforms (Qiita, Zenn, Hatena), European/Latin American developer ecosystems.
5. **Group 5: Monorepos, Alternative Registries, Docker Containers & Emerging Ecosystems (200 servers)**
   - Technologies: Monorepo subdirectories (`packages/*-mcp`), Docker Hub standalone images, Swift, PHP, Elixir, standalone listings on Glama.ai/PulseMCP/mcp.so.
   - Sources: Docker Hub, Glama, PulseMCP, Packagist, Hex.pm, Swift Package Index, large GitHub monorepos.

## Deliverable Specifications

1. **Machine-Readable Registry**: `docs/research/mcp_candidates_by_group.json`
   Structure:
   ```json
   {
     "rust_systems": [
       {
         "name": "...",
         "location": "https://github.com/... or https://crates.io/crates/...",
         "ecosystem": "rust",
         "description": "...",
         "source": "crates.io"
       }
       // exactly 200 items
     ],
     "go_cloud_native": [ ... 200 items ... ],
     "jvm_dotnet_enterprise": [ ... 200 items ... ],
     "regional_international": [ ... 200 items ... ],
     "monorepo_docker_emerging": [ ... 200 items ... ]
   }
   ```
2. **Human-Readable Markdown Catalog**: `docs/research/mcp_candidates_by_group.md`
   - Detailed tables per group showing Name, Location, Ecosystem, and Discovery Source.
   - Summary statistics confirming exactly 200 entries per group.
3. **Automated Conformance Test**: `tests/test_candidate_groups_conformance.py`
   - Test asserts `docs/research/mcp_candidates_by_group.json` exists.
   - Asserts all 5 group keys exist.
   - Asserts `len(group) == 200` for each group.
   - Asserts all URLs are well-formed strings starting with `http://` or `https://`.
   - Asserts zero duplicates across the entire 1,000 dataset.

## Non-Interactive Completion Directive
Execute the external gathering, author the JSON dataset and markdown summary, create the test verification suite, verify all tests pass with `pytest tests/test_candidate_groups_conformance.py`, and finalize directly so the remote environment cleanly transitions to `Completed`.
