# Changelog

All notable changes to the `mcp-fingerprints` project will be documented in this file.

# Release Notes - v1.4.5

> **Release Version**: `v1.4.5`  
> **Release Date**: 2026-11-13  
> **Status**: Production Release  
> **Package**: [`mcp-fingerprints`](https://pypi.org/project/mcp-fingerprints/)

---

## 🌟 Overview & Highlights

`v1.4.5` expands the passport catalog and hardens reliability, security, and packaging across the library:
1. **Catalog & Audit Expansion**: Consolidated 6,033 passports in `passports.json.gz` (5,862 individual files in `data/fingerprints/`) and reconciled master audit summaries.
2. **Runtime & Security Hardening**:
   - Fixed `.json.gz` dictionary iteration in `reporter.py` (`iter_passports()`).
   - Fixed `by_purl` lookup normalization in `index.py` (`find_package_by_hint_or_alias()`).
   - Fixed `db_engine.py` (`find_by_hash()`) to query canonical `"versions"` alongside legacy `"version_fingerprints"`.
   - Restored verified TLS SSL context and removed module-level `logging.basicConfig()` pollution in `synchronizer.py`.
   - Unified `McpStdioProber` onto `sanitize_environment()` and non-blocking threaded queue I/O to prevent pipe deadlocks and host secret leakage.
   - Replaced lexicographical version sorting with `packaging.version.parse` in `sbom_exporter.py` and `crawler/__init__.py`.
   - Guarded `config_scanner.py` scoped npm/npx directory traversal with `is_dir()`.
3. **Packaging & Exports**:
   - Fixed `from src.mcp_fingerprints...` wheel import errors across reindexers and tests.
   - Moved `playwright` / `pytest-playwright` to `[project.optional-dependencies] dev` and added `numpy` to `semantic`.
   - Exported `McpProber` and `ProbeReport` in `mcp_fingerprints.__all__` and cleaned up `crawler/__init__.py` exports.

---

# Release Notes - v1.3.0

> **Release Version**: `v1.3.0`  
> **Release Date**: 2026-11-01  
> **Status**: Production Release  
> **Package**: [`mcp-fingerprints`](https://pypi.org/project/mcp-fingerprints/)

---

## 🌟 Overview & Highlights

`v1.3.0` delivers full web catalog tool signature integration, automated Playwright headless browser CI workflows, PyPI packaging verification, and extensive tool extraction across 6 parallel Google Jules waves:
1. **Web App Tool Signature Bridge & Catalog Normalizer**: Bridged 74,793 tool signatures into `web/app.js` across 3,998 servers, enabled deep tool search, and added `scripts/normalize_catalog_tools.py`.
2. **Automated Playwright Headless Browser CI**: Created `.github/workflows/e2e.yml` and authored `tests/test_web_pwa_e2e.py` validating offline PWA caching, windowed DOM virtualization, and search responsiveness.
3. **Packaging & Daily Sync CI Verification**: Added `MANIFEST.in` and authored `tests/test_packaging_and_sync_ci.py`.
4. **Scaled Tool Extraction (Waves 1-6)**: Extracted AST tool schemas and recomputed canonical SHA-256 hashes across 80+ top MCP servers, updating `passports.json.gz` and `web/catalog.json`.
5. **Full Offline Test Suite**: 517 passed, 5 skipped (100% green).

---

# Release Notes - v1.2.0

> **Release Version**: `v1.2.0`  
> **Release Date**: 2026-10-31  
> **Status**: Production Release  
> **Package**: [`mcp-fingerprints`](https://pypi.org/project/mcp-fingerprints/)

---

## 🌟 Overview & Highlights

`v1.2.0` delivers system-wide hardening, enterprise resilience, and deep architectural alignment across all 5 core pillars:
1. **Data Pipeline & Registry Link Enrichment**: Upstream repository links populated for 82 passports via PyPI/NPM APIs; 51 dead repositories tagged `status: "unreachable_or_private"`.
2. **Web App PWA & Virtualization**: On-demand stale-while-revalidate caching in `web/sw.js`; windowed DOM recycling in `web/app.js` with capped memory footprints; mobile horizontal scroll guards.
3. **Core Toolset Hardening**: `max_depth=15` cyclic `$ref` guard in `openapi_parser.py`; line-by-line plaintext stdout log filtering in `prober.py`; 10MB subprocess buffer caps.
4. **Fault Injection Testing**: New test suite in `tests/test_fault_injection.py` testing mid-stream network drops and malformed JSON-RPC payloads.
5. **Documentation & Specification Parity**: All 7 CLI commands, SDK exports, and extended passport schema fields documented in `docs/SPECIFICATION.md` and `README.md`.
6. **Verified via Google Jules Mode 2 Review**: Complete audit and verification in Session `8394579379504931713` (Issue #92) with 505 tests passing offline.

---

# Release Notes - v1.1.7

> **Release Version**: `v1.1.7`  
> **Release Date**: 2026-10-31  
> **Status**: Production Release  
> **Package**: [`mcp-fingerprints`](https://pypi.org/project/mcp-fingerprints/)

---

## 🌟 Overview & Highlights

`v1.1.7` delivers complete tool re-indexing and canonical hash recalculation across **18 priority candidate servers** whose passports previously recorded 0 tools despite confirmed upstream definitions. It also includes an exhaustive Google Jules deep review (Task 108), verifying 100% data integrity, schema compliance, and offline test isolation.

---

## 🚀 Key Enhancements & Re-Indexed Passports

### 1. Re-Indexed Priority Passports (Task 107)
Successfully extracted and populated tool signatures and recomputed canonical SHA-256 hashes (`toolset_canonical_hash`) for 18 servers:
- **`SonAIengine_graph-tool-call.json`**: 7 tools (`sha256:af8fa7dd...`)
- **`domdomegg_airtable-mcp-server.json`**: 5 tools (`sha256:d1cffe1f...`)
- **`0xshellming_mcp-summarizer.json`**: 1 tool (`sha256:aac274b4...`)
- **`maxfain_basedagents.json`**: 60 tools (`sha256:df42174a...`)
- **`merterbak_Grok-MCP.json`**: 8 tools (`sha256:77d0b262...`)
- **`runekaagaard_mcp-alchemy.json`**: 4 tools (`sha256:7e0c77fd...`)
- **`orieg_gws-connector.json`**: 49 tools (`sha256:934cf9b5...`)
- **`Autario_autario-mcp.json`**: 58 tools (`sha256:9dd2fcd4...`)
- **`tatsuju_opdstar-nhi-mcp.json`**: 27 tools (`sha256:8b58cafa...`)
- **`@verygoodplugins_mcp-automem.json`**: 13 tools (`sha256:a6518faf...`)
- **`nimbus-agent_Nimbus.json`**: 3 tools (`sha256:dd01141f...`)
- **`github.json`**: 86 tools (`sha256:72dfefb3...`)
- **`slack.json`**: 11 tools (`sha256:5ba5dddf...`)
- **`mobile-next_mobile-mcp.json`**: 34 tools (`sha256:b1000415...`)
- **`sharozdawa_ai-visibility.json`**: 8 tools (`sha256:6d4229ed...`)
- **`engine-dj-mcp.json`**: 14 tools (`sha256:6c9f0bad...`)
- **`serkan-ozal_driflyte-mcp-server.json`**: 38 tools (`sha256:6b246f7b...`)
- **`dannote_figma-use.json`**: 1 tool (`sha256:0af7faff...`)

### 2. Deep Mode 2 Review & Verification (Task 108)
- Audited implementation in [`docs/reviews/review_task107_reindexed_passports.md`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/docs/reviews/review_task107_reindexed_passports.md).
- Verified valid JSON syntax, canonical hash alignment, and zero security domain pollution across all 18 updated passports.
- Confirmed `data/.passport_cache.json` synchronization.

### 3. Corpus Quality Metric Milestones
- **Passports with verified tool signatures (`> 0`)**: Rose from 2,983 to **3,001**.
- **Confirmed GitHub Upstreams**: **4,344** repositories.
- **Third-Party Hub Dependencies**: Dropped to **178**.

---

## 📦 Verification & Test Results

- **Unit Test Suite**: 499 passed, 5 skipped (100% green in 84.58s).
- **Harness Isolation**: Complete offline reliability with zero unmocked external socket leaks.


---

# Release Notes - v1.1.6

> **Release Version**: `v1.1.6`  
> **Release Date**: 2026-10-31  
> **Status**: Production Release  
> **Package**: [`mcp-fingerprints`](https://pypi.org/project/mcp-fingerprints/)

---

## 🌟 Overview & Highlights

`v1.1.6` expands our re-indexing architecture with full polyglot AST and documentation fallback extraction in [`reindex_sdk_passports.py`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/src/mcp_fingerprints/reindex_sdk_passports.py), enabling multi-language tool extraction across TypeScript, JavaScript, Python, Go, and Markdown. It includes a complete deep review (Task 106) and 6 new offline unit tests.

---

## 🚀 Key Enhancements & Features

### 1. Polyglot AST & Documentation Tool Extractor Engine
- Enhanced [`src/mcp_fingerprints/reindex_sdk_passports.py`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/src/mcp_fingerprints/reindex_sdk_passports.py):
  - Added multi-language AST extraction (`parse_mcp_source_code`) across `.ts`, `.js`, `.mjs`, `.py`, and `.go` source files.
  - Added primary documentation table extraction (`parse_markdown_tool_docs`) via `doc_parser.py` when source code AST discovers 0 tools.
  - Implemented GitHub file tree prioritization to inspect entry points (`server`, `mcp`, `tool`, `index`, `main`) before secondary directories.
  - Recalculates canonical SHA-256 hashes (`toolset_canonical_hash`) and updates passport version records cleanly.

### 2. Deep Mode 2 Review & Edge Case Hardening (Task 106)
- Audited implementation in [`docs/reviews/review_reindex_sdk_passports_and_ast_patterns.md`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/docs/reviews/review_reindex_sdk_passports_and_ast_patterns.md).
- Hardened extraction against edge cases:
  - Repositories with missing default branches or empty file trees (`test_extract_tools_from_repo_empty_tree`).
  - Extracted tools missing `inputSchema` or description properties (`test_extract_tools_from_repo_missing_fields`, `test_update_passport_tools_missing_schema`).
- Added internal method documentation and docstrings.

### 3. Offline Test Isolation & Harness Verification
- Added 6 new unit tests in [`tests/test_reindex_sdk_passports.py`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/tests/test_reindex_sdk_passports.py).
- 100% offline isolation: all network requests are mocked with `@patch`, strictly adhering to the socket block in `tests/conftest.py`.

---

## 📦 Verification & Test Results

- **Unit Test Suite**: 499 passed, 5 skipped (100% green in 87.31s).
- **Harness Isolation**: Complete offline reliability with zero unmocked external socket leaks.


---

# Release Notes - v1.1.5

> **Release Version**: `v1.1.5`  
> **Release Date**: 2026-10-31  
> **Status**: Production Release  
> **Package**: [`mcp-fingerprints`](https://pypi.org/project/mcp-fingerprints/)

---

## 🌟 Overview & Highlights

`v1.1.5` introduces automated third-party registry and hub repository resolution (`hub_resolver.py`), converting 120+ passports that previously pointed to aggregator hubs (`smithery.ai`, `glama.ai`) or lacked source links to genuine upstream GitHub repositories. It also features a full deep review of catalog reconciliation, offline test suites, and passport data integrity.

---

## 🚀 Key Enhancements & Features

### 1. Hub Link & Upstream Repository Resolution (`hub_resolver.py`)
- **Automated Registry Resolution**:
  - Added [`src/mcp_fingerprints/hub_resolver.py`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/src/mcp_fingerprints/hub_resolver.py) supporting automated package metadata inspection against PyPI and npm.
  - Queries PyPI `project_urls` (`Source`, `Repository`, `Code`, `Homepage`) and npm `repository.url` / `homepage`.
  - Supports npm shorthand syntax (`github:user/repo`).
- **URL Normalization**:
  - Strips transport prefixes (`git+`, `ssh://`, `git@`), removes trailing `.git`, and extracts standard GitHub HTTPS repository links.
- **Resilience & SSL Fallbacks**:
  - Implements bounded timeouts (5s) and unverified SSL context fallbacks (`ssl.CERT_NONE`) for corporate/proxy networks while suppressing errors cleanly.

### 2. Deep Review & Refinements (Task 103)
- Conducted deep code, data, and test review via Google Jules: [`docs/reviews/review_hub_resolver_and_repository_resolution.md`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/docs/reviews/review_hub_resolver_and_repository_resolution.md).
- Added support for shorthand string definitions in npm package metadata.
- Ensured 100% offline unit tests with `monkeypatch` on `urllib.request.urlopen`.

### 3. Passport & Catalog Data Quality
- Resolved and updated **120+ passports** under `data/fingerprints/`:
  - Increased confirmed GitHub upstreams from 4,221 to **4,344**.
  - Reduced third-party hub dependencies (`smithery.ai`/`glama.ai`) from 251 down to **178**.
- Synchronized compact single-line `web/catalog.json` with the newly resolved repository URLs.

---

## 📦 Verification & Test Suite

- **Unit Test Suite**: 493 passed, 5 skipped (100% green in 86.87s).
- **Network Isolation**: Complete offline reliability adhering strictly to the `tests/conftest.py` socket block.


---

# Release Notes - v1.1.3

> **Release Version**: `v1.1.3`  
> **Release Date**: 2026-10-31  
> **Status**: Production Release  
> **Package**: [`mcp-fingerprints`](https://pypi.org/project/mcp-fingerprints/)

---

## 🌟 Overview & Highlights

`v1.1.3` is a patch release focusing on catalog quality, zero-tool remote gateway enforcement, and enhanced tool discovery mechanisms identified during the daily web catalog audit protocols (Tasks 94–97 / PR #68 & PR #71).

---

## 🚀 Key Enhancements & Bug Fixes

### 1. Remote Gateway & SDK Zero-Tool Classification & Enforcement
- Explicitly classifies and enforces zero tool counts for servers acting purely as remote gateways, proxy relays, or SDK client wrappers (e.g., `api-auto-mcp-server`, `@fruggr/zendesk-mcp-server`, `pydantic-ai`, `davinci-resolve-mcp`, `ssh-mcp`, `mnemostack`, `@covalenthq/goldrush-mcp-server`).
- Prevents false-positive tool inflation where catalog metadata previously claimed non-zero tool counts on client SDKs without local MCP tools.

### 2. Registry Fallback Resolution for Third-Party Hubs
- Added automatic resolution in [`src/mcp_fingerprints/deep_zero_tool_auditor.py`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/src/mcp_fingerprints/deep_zero_tool_auditor.py) for package cards hosted on third-party registries and hubs (`smithery.ai`, `glama.ai`).
- Extracts package names and queries PyPI / npm registry APIs to reliably resolve genuine upstream GitHub repositories.

### 3. Documentation & Markdown Table Tool Extraction
- Filtered secondary documentation files (`CHANGELOG.md`, `MIGRATION.md`, `ROADMAP.md`, `.cursor/skills/`) to eliminate false-positive tool inflation from historical or release tables.
- Integrated primary documentation (`README.md`) Markdown table tool extraction into the auditor pipeline via `doc_parser.py` when source code lacks AST definitions.

### 4. Passport Re-indexing & Synchronization
- Re-indexed 11 affected server passports under `data/fingerprints/` to accurately reflect zero tools for confirmed remote gateways.

### 5. Test Suite & Network Guard Compliance
- Added new offline unit tests in [`tests/test_deep_zero_tool_auditor.py`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/tests/test_deep_zero_tool_auditor.py) covering hub URL fallback resolution, remote gateway zero-tool enforcement, and Markdown table extraction.
- Fully mocked network calls in strict compliance with the test isolation socket guard in `tests/conftest.py`.

---

## 📦 Verification

- **Unit Test Suite**: 483 passed, 5 skipped (100% green).
- **Harness Isolation**: Complete offline reliability with zero unmocked external socket leaks.


---

# Release Notes - v1.1.0

> **Release Version**: `v1.1.0`  
> **Release Date**: 2026-10-28  
> **Status**: Production Release  
> **Package**: [`mcp-fingerprints`](https://pypi.org/project/mcp-fingerprints/)

---

## 🌟 Overview & Highlights

`v1.1.0` is a major minor-version release delivering substantial improvements to static AST extraction, zero-tool auditing, test harness isolation, and automated daily quality workflows. It also incorporates full re-indexing of passports affected by modern TypeScript and Python MCP SDK registration patterns.

---

## 🚀 What's New & Key Enhancements

### 1. Modern MCP SDK AST Extraction Patterns (TypeScript & Python)
- **TypeScript `@modelcontextprotocol/sdk` Support**:
  - Added extraction pattern matching for `server.registerTool(...)` and `server.tool(...)`.
  - Added recursive inspection of nested subdirectories (e.g. `src/tools/`, `Tools/`, `lib/tools/`).
- **Python Official SDK Support**:
  - Added pattern matching for low-level SDK `Tool(name=...)` instantiations.
  - Preserved decorators (`@mcp.tool()`, `@action`, `@command`).

### 2. Autonomous Daily Web Audit & Quality Protocol (Task 88)
- Published the formal workflow specification: [`docs/tasks/task_88_daily_audit_ai_workflow_and_resolution_protocol.md`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/docs/tasks/task_88_daily_audit_ai_workflow_and_resolution_protocol.md).
- Strict 5-phase triage lifecycle:
  1. Ingestion & Triage
  2. Independent Item-by-Item Verification
  3. Action Plan Authoring
  4. Gated Implementation & Algorithmic Passport Re-indexing
  5. Post-Fix Verification & Delta Reporting
- Directory architecture separation: `runs/`, `reviews/`, `plans/`, and `fixes/`.

### 3. Re-Indexed SDK Passports (Task 93)
- Created dedicated re-indexing tool [`src/mcp_fingerprints/reindex_sdk_passports.py`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/src/mcp_fingerprints/reindex_sdk_passports.py).
- Successfully re-indexed candidate servers in `data/fingerprints/` that previously recorded 0 tools:
  - `soil-dev_capsulemcp.json`
  - `@zvid_mcp.json`
  - `giorgio44_gateonai-mcp-server.json`
  - `awkoy_notion-mcp-server.json`
  - `audionaut-mcp.json`
  - `PhilipAD_health-export-mcp.json`
  - `@fruggr_zendesk-mcp-server.json`
  - `AutomateLab-tech_content-distribution-mcp.json`
  - `eslint-plugin-mcp-sdk-security.json`
  - `bvisible_mcp-ssh-manager.json`
  - `1mcp-app_agent.json`
  - `@fodx_codelens.json`
  - `tufantunc_ssh-mcp.json`
- Synchronized `data/.passport_cache.json` with updated tool counts and canonical hashes.

### 4. Test Harness Hardening & Network Isolation Guard (Task 89)
- Intercepts external outbound socket connections during unit test execution in `tests/conftest.py`.
- Allows local IPC / loopback (`127.0.0.1`, `::1`, `localhost`, `AF_UNIX`) while blocking unexpected external HTTP requests.
- Provides `@pytest.mark.network` for tests requiring explicitly flagged live network calls.

### 5. Scratch & Temporary File Sanitizer (Task 90)
- Automated pre-commit sanitizer script [`bin/sanitize-scratch-files.sh`](file:///Users/ivan/Project/3t.tools.intellij/mcp-fingerprints/bin/sanitize-scratch-files.sh).
- Hardened `.gitignore` to prevent committing root scratch scripts (`/test_*.py`, `/scratch_*.py`, `/tmp_*.py`) and temporary data.

### 6. SSL & Registry Fallbacks for Python 3.14
- Added unverified SSL context fallback in `DeepZeroToolAuditor` for local environments and container runs encountering missing root certificate bundles.
- Automatic fallback to PyPI / npm registry metadata when package cards lack upstream GitHub links, classifying them cleanly as `UNRESOLVED_SOURCE`.

---

## 📊 Quality & Verification Metrics
- **Unit & Integration Test Suite**: 478 passed, 5 skipped (100% passing).
- **Network Isolation**: Verified offline-reliable.
- **Auditor Match Rate**: False positive mismatches reduced from 18 to 0 in daily runs.

---

## 📦 Migration & Upgrade Notes
- No breaking changes to existing public APIs (`FingerprintMatcher`, `ConfigScanner`, `FingerprintGenerator`).
- Upgrading to `v1.1.0` enables static discovery of `@modelcontextprotocol/sdk` TypeScript and low-level Python tool contracts without requiring runtime execution.


---

# Release Notes - v1.0.0

> **Release Version**: `v1.0.0`
> **Release Date**: 2026-10-15
> **Status**: Production Release
> **Package**: [`mcp-fingerprints`](https://pypi.org/project/mcp-fingerprints/)

---

## 🌟 Overview & Highlights

Initial production release of the `mcp-fingerprints` structural cataloging and fingerprinting system. Establishes the core automated database and knowledge base of Model Context Protocol (MCP) server passports, version signatures, and tool contract fingerprints.

---

## 🚀 Key Features

*   **Core Architecture**: Introduced pure structural AST extraction for Python, TypeScript/JavaScript, Go, and Rust.
*   **Cryptographic Fingerprinting**: Implemented deterministic, order-invariant `canonical_hash` and `toolset_canonical_hash` generation for strict verification.
*   **Interactive TUI**: Added `mcp-fingerprints interactive` command hub.
*   **Layered Matching Engine**: Built Tri-Layer matching system (Exact Cryptographic Match, Topological & Signature Similarity, Name/PURL Disambiguation).
*   **Initial Discovery Support**: Added workstation configuration discovery for common AI agents (Claude, Cursor, Zed).
*   **Test Suite**: Released the automated invariant verification test suite verifying 5 core pillars.

