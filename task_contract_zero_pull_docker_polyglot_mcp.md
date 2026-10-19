# Task 45: Zero-Pull Docker Hub & Polyglot (Rust/Go) MCP Ingestion Engine

## 1. Context & Objectives
Extend `mcp-fingerprints` discovery and synchronizer (`src/mcp_fingerprints/synchronizer.py`) to ingest containerized and compiled MCP servers (like CodeScene, Rust, Go) efficiently without downloading gigabytes of layers or cloning entire git trees:

1. **Headless Docker Hub / OCI Registry V2 Inspection**:
   - Query Docker Hub API (`hub.docker.com/v2/repositories/?search=mcp`) and Docker Registry V2 API for MCP container images.
   - Extract repository descriptions, tags, and OCI image metadata/labels without pulling layers or executing containers.
   - Parse Docker Hub README overview for tool schemas and usage examples.

2. **Targeted Polyglot GitHub Discovery (Rust, Go)**:
   - Search GitHub repositories using topic filters: `topic:mcp-server`, `topic:model-context-protocol` with `language:rust` and `language:go`.
   - Use GitHub Contents/Trees API or raw content URLs to fetch *only* `Cargo.toml`, `go.mod`, and `README.md`.
   - Strictly avoid running `git clone` or downloading full source archives.

3. **Multi-Tier Tool Signature Extraction**:
   - Primary: Parse documentation and tool tables via `mcp_fingerprints.doc_parser: parse_markdown_tool_docs`.
   - Secondary: Extract tool names and schemas from release assets or manifest metadata.
   - Synthesize valid `ServerPackageSpec` passports with complete fingerprints.

4. **Passport Generation & Validation**:
   - Save ingested servers to `data/fingerprints/<package_name>.json`.
   - Validate all generated passports against `McpServerValidator`.
   - Register the new crawlers into `PassportSynchronizer.discover_new_mcps()` and CLI `sync --docker --polyglot`.

5. **Testing & Invariants**:
   - Add unit tests mocking Docker Hub API responses and GitHub raw API tree responses.
   - Zero unauthorized dependencies; use standard library and existing dependencies.
   - Non-interactive completion: finalize with summary without open-ended questions.
