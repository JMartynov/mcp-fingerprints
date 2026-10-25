# Codebase Audit and Gap Analysis Report

**Project:** `mcp-fingerprints`
**Date:** 2024-05
**Scope:** Exhaustive critical codebase review and gap analysis covering unimplemented features, friction points, fragile subsystems, architectural/ecosystem gaps, and a roadmap for Wave 8 / v1.1.0.

---

## 1. WHAT IS NOT IMPLEMENTED OR INCOMPLETE

### A. Missing Advertised Features vs. Code
- **Client Exporter Edge Cases**: While `mcp_fingerprints.cli export-config` handles Claude Desktop and Cursor explicitly, the README also mentions `Cline` and `Zed`. However, looking closely at `config_exporter.py` and the CLI arguments, specific explicit support or format handling for `Cline` or `Zed` does not exist (it exports standard configs, but distinct native schemas for these clients are not fully implemented).
- **Runtime Sandbox Probing (`--probe-runtime`)**: The `probe_runtime_passports` in `synchronizer.py` attempts a basic `stdio` handshake, but it relies on simple `subprocess` calls without real containerization (like Docker/gVisor), making "sandbox" a slight misnomer—it executes natively (even checking if the command is `python` or `node`). It filters environment variables (e.g., `AWS_*`, `GITHUB_TOKEN`), but there are gaps in handling sophisticated malicious code that could circumvent these weak OS-level checks (e.g. creating rogue processes or downloading execution payloads).
- **Semantic Search FastEmbed Caching**: The semantic indexer (`semantic_index_builder.py`) builds and precomputes `data/embeddings.npz`, but `semantic_search.py` seems to only perform naive numpy argpartition/dot-products on query time. If FastEmbed is not installed, it gracefully falls back, but the error handling around malformed index files or missing cache files (`data/embeddings.npz`) simply skips semantic scoring or fails silently back to lexical, which might confuse users expecting deep search results.

### B. Incomplete Ecosystems & Extractors
- **Go, Rust, JVM, .NET Crawling**: `docs/SECURITY_AUDIT.md` promises Go, Rust, JVM, and .NET coverage ("Scanning compiled bytecodes/IL or source annotations"). However, the codebase mostly relies on `ast_parser.py` (Python) and regex/AST routines for TypeScript/NPM (`npm_tarball_extractor.py`). There is no true byte-code scanner or comprehensive AST parser implemented for Rust, Go, or JVM inside the source directory (`src/mcp_fingerprints/golang_rust_parser.py` or similar do exist in test files like `test_golang_rust_parser.py`, but examining the tests shows they are largely regex or stubbed text parsing rather than rigorous static AST engines).
- **Error Handling**: `cli.py` makes broad use of bare `except Exception: pass` during directory scanning (e.g., searching for packages), which masks filesystem permission errors, corrupt JSON data, and other critical failures.

---

## 2. WHAT WORKS NOT WELL (FRICTION POINTS & FRAGILITIES)

### A. Performance & Scalability
- **JSON File Sprawl vs. Single DB**: The system relies on iterating over 5,000+ discrete `*.json` files across nested directories (`output_dir.rglob("*.json")`). Reading and deserializing thousands of files on every CLI search or sync operation creates massive IO bottlenecks and high memory usage (loading all dicts into RAM). A consolidated index format like **DuckDB, SQLite, or Parquet** is desperately needed for read/write scaling.
- **AST Enrichment Memory Spikes**: The `enrich_zero_tool_passports` downloads entire NPM tarballs (`npm_tarball_extractor.py`) or GitHub repos into memory to perform AST extraction. This breaks the "zero disk footprint" policy if archives are huge, causing immense RAM spikes, especially when using `ProcessPoolExecutor` with `max_workers=12` in `synchronizer.py`.

### B. Ingestion Robustness
- **Network Retries & Rate-limits**: The `_fetch_github_api_with_retry` and general `fetch_json` methods have basic timeout handling, but lack advanced backoff strategies (e.g., handling HTTP 429 Too Many Requests smoothly). GitHub rate limiting can quickly block the entire sync pipeline since no token rotation or smart queueing is deeply implemented.
- **Malformed Schema Resilience**: If an MCP server returns non-standard JSON, the crawler can break. `tests/test_runtime_sandbox.py` handles malformed JSON from sandboxes, but the overall `ServerPackageSpec` enforces strict freezing, meaning unexpected/novel fields from upstream servers are entirely dropped rather than preserved in an "extras" dictionary.

### C. Testing Coverage & Skipped Tests
- **4 Skipped Tests**: `test_live_clusters.py` skips 4 tests by default because they require `RUN_LIVE_INTEGRATION_TESTS=1`. This makes sense for CI speeds, but means the actual network connectivity logic to Smithery, NPM, PyPI, and GitHub is largely unverified during local pre-commit checks.
- **Weak Coverage**: The CLI `except Exception: pass` blocks in `mcp_fingerprints/cli.py` lack coverage for edge cases, making it difficult to detect when a command like `export-config` fails silently because a passport is malformed.

### D. CLI Ergonomics
- The CLI outputs plain JSON dumps by default unless `args.json` is checked in some places, while in others it prints formatted reports. Error messaging is often sparse (e.g., `ERROR: Package 'foo' not found` with no suggestion of similar packages).

---

## 3. WHAT WE MISSED (ARCHITECTURAL & ECOSYSTEM GAPS)

### A. Ecosystem Tooling Gaps
- **Missing `mcp-fingerprints init` Wizard**: New users have no interactive way to generate a baseline configuration or initial passport. They must rely on the CLI to export existing ones, rather than scaffolding their own server.
- **No bi-directional integration with `mcp-anomalies`**: The current system fetches advisories via `structural anomalyEnricher`, but cannot push newly detected risky signatures back to a central structural anomaly database or format.
- **SBOM / SARIF / CycloneDX Support**: The security classifier evaluates tools (High, Medium, Critical risks) and detects overlapping CVEs, but there is no way to export this data in an industry-standard format (SARIF, CycloneDX) for ingestion into platforms like GitHub Advanced Security or Datadog.

### B. Protocol Validation
- **JSON-RPC 2.0 Compliance**: The project parses tools and schemas but does not enforce or verify strict JSON-RPC 2.0 standard protocol compliance when running `--probe-runtime`. It just looks for the `initialize` and `tools/list` payloads, ignoring strict JSON-RPC envelope validation.

---

## 4. REMEDIATION STEPS FOR WAVE 8 AND v1.1.0 ROADMAP

**Priority 1: High (Immediate Friction/Stability)**
1. **Migrate Backend to SQLite/DuckDB**:
   - Replace the discrete `rglob("*.json")` loading mechanism with a consolidated `sqlite3` database or `DuckDB` backend. Update `ServerPackageSpec` to serialize directly to rows.
   - *Action*: Create `mcp_fingerprints.db_backend` module and deprecate raw JSON iteration in `cli.py` and `search.py`.
2. **Implement Resilient Network Backoff**:
   - Introduce `tenacity` or a robust exponential backoff handler in `fetch_json` and HTTP client calls to gracefully survive GitHub/NPM 429 Rate Limits.
   - *Action*: Update `synchronizer.py` HTTP methods.

**Priority 2: Medium (Features & Ecosystem)**
3. **True Security Export Standards (SARIF/SBOM)**:
   - Extend `cli.py audit-config` to accept `--format sarif` and `--format cyclonedx`.
   - *Action*: Create `mcp_fingerprints.exporters.sarif` to map internal risk scores to standard OASIS SARIF output.
4. **Interactive Setup Wizard**:
   - Implement `python -m mcp_fingerprints.cli init` using `rich` or standard `input()` prompts to help users scaffold local `.mcp_passports/` configs.
5. **Add Explicit Support for Zed and Cline**:
   - Update `config_exporter.py` to generate the exact JSON structures required by Zed and Cline MCP client configurations.

**Priority 3: Low (Enhancements & Hardening)**
6. **Enhance Runtime Sandbox**:
   - Transition `--probe-runtime` from local `subprocess` calls to utilizing `docker run` or `bwrap` (Bubblewrap) for actual network and filesystem isolation, truly honoring the "sandbox" terminology.
7. **Fix Silent CLI Errors**:
   - Remove `except Exception: pass` anti-patterns in `cli.py`. Replace with `logger.debug("Failed to parse %s: %s", file, exc)` so developers can debug missing/malformed passports.
