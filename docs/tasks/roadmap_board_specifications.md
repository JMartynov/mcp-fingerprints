# MCP Fingerprints: Board Task Specifications & Acceptance Criteria

This document mirrors the private GitHub Project Task Board ([Project #3](https://github.com/users/JMartynov/projects/3)) linked to `JMartynov/mcp-fingerprints`.

---

## 1. Live GitHub Pages First Run & Automated Daily Trigger
- **Board Item ID**: `DI_lAHOD-xmQM4BmPbTzgLUhiI`
- **Category**: Operations & Release

### Context & Objective
The repository includes a static web catalog (`web/index.html` + `web/catalog.json`) and a deployment workflow (`.github/workflows/deploy_pages.yml`). Currently, GitHub Pages must be configured in GitHub repository settings to enable deployment via GitHub Actions, and an initial deployment needs to be verified live. Furthermore, `.github/workflows/deploy_pages.yml` should be triggered automatically whenever daily sync completes.

### Implementation Steps
1. **GitHub Repository Settings**:
   - Ensure repository `JMartynov/mcp-fingerprints` has GitHub Pages enabled with `Source: GitHub Actions`.
2. **Workflow Interconnection**:
   - In `.github/workflows/deploy_pages.yml`, add `workflow_run` trigger listening for completed runs of `Daily MCP Fingerprint & Passport Sync` on `main`.
3. **Execution & Live Verification**:
   - Trigger manual run: `gh workflow run deploy_pages.yml --ref main`.
   - Monitor run completion via `gh run watch`.
   - Verify HTTP 200 and live response at `https://jmartynov.github.io/mcp-fingerprints/`.
   - Confirm search, filtering, and copy snippets function properly in production.

### Acceptance Criteria
- [x] GitHub Pages source is configured to GitHub Actions for `JMartynov/mcp-fingerprints`.
- [x] Workflow `.github/workflows/deploy_pages.yml` completes with green status on GitHub Actions.
- [x] `https://jmartynov.github.io/mcp-fingerprints/` returns HTTP 200 with 5,031+ searchable MCP servers.
- [x] `deploy_pages.yml` triggers automatically after daily sync updates.

---

## 2. PyPI Trusted Publishing Setup & Tag v1.0.0 Release
- **Board Item ID**: `DI_lAHOD-xmQM4BmPbTzgLUhiY`
- **Category**: Operations & Release

### Context & Objective
`pyproject.toml` is configured with complete metadata (classifiers, keywords, URLs, entry points), and `.github/workflows/release.yml` utilizes official OpenID Connect (OIDC) trusted publishing (`pypa/gh-action-pypi-publish@release/v1`). To enable publishing without managing static API tokens, PyPI must be configured to trust the GitHub repository, followed by creating the first release tag `v1.0.0`.

### Implementation Steps
1. **PyPI Trusted Publisher Configuration**:
   - In PyPI account management: Add Pending Publisher for repository `JMartynov/mcp-fingerprints`, workflow name `release.yml`, environment name `pypi`.
2. **Local Build Dry-Run Validation**:
   - Run `python -m pip install build twine && python -m build` locally.
   - Run `twine check dist/*` to verify package description rendering and metadata compliance.
   - Verify that package excludes test artifacts and only includes `src/mcp_fingerprints` and schema data.
3. **Tagging & Workflow Execution**:
   - Tag release: `git tag -a v1.0.0 -m "Release v1.0.0: Open-Source MCP Server Passport Knowledge Base"`.
   - Push tag: `git push origin v1.0.0`.
   - Create GitHub release: `gh release create v1.0.0 --title "v1.0.0" --generate-notes`.
   - Monitor `.github/workflows/release.yml` execution and verify package availability on `https://pypi.org/project/mcp-fingerprints/`.

### Acceptance Criteria
- [x] `python -m build` builds clean sdist (`.tar.gz`) and wheel (`.whl`) without errors.
- [x] `twine check dist/*` passes with `PASSED`.
- [ ] `.github/workflows/release.yml` finishes successfully via OIDC trusted publishing.
- [ ] `pip install mcp-fingerprints==1.0.0` installs successfully in a clean virtual environment.
- [ ] `mcp-fingerprints --version` and CLI entry points execute properly.

---

## 3. Local Pre-Commit Dogfooding & Quality Assurance
- **Board Item ID**: `DI_lAHOD-xmQM4BmPbTzgLUhik`
- **Category**: Dogfooding & Quality Gates

### Context & Objective
`.pre-commit-hooks.yaml` exposes `mcp-audit-config` for external repositories. To practice dogfooding and enforce strict quality standards locally, this repository needs its own `.pre-commit-config.yaml`. It should enforce fast ruff formatting/linting and run our own `mcp-audit-config` hook whenever local client settings or MCP fixtures are modified.

### Implementation Steps
1. **Pre-Commit Configuration (`.pre-commit-config.yaml`)**:
   - Add `astral-sh/ruff-pre-commit` for ruff lint and format.
   - Add local repo hook targeting `mcp-audit-config` using `python -m mcp_fingerprints.cli audit-config`.
   - Add standard hygiene hooks: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`.
2. **README Documentation**:
   - Add a "Pre-Commit Integration" section in `README.md` explaining how developers and agent builders can install and use pre-commit with `mcp-fingerprints`.
3. **Unit Tests**:
   - Update `tests/test_action_and_hooks.py` to ensure `.pre-commit-config.yaml` is valid YAML and compatible.

### Acceptance Criteria
- [x] `.pre-commit-config.yaml` is present in the repository root.
- [x] `pre-commit run --all-files` runs cleanly across all files in the repository.
- [x] Modifying a fixture MCP config triggers `mcp-audit-config` verification.
- [x] `README.md` includes clear instructions for setting up pre-commit.
- [x] All unit tests pass.

---

## 4. Reusable Action CI Integration & Self-Testing
- **Board Item ID**: `DI_lAHOD-xmQM4BmPbTzgLUhis`
- **Category**: Dogfooding & Quality Gates

### Context & Objective
`action.yml` is defined as a reusable composite GitHub Action allowing downstream repositories to audit their MCP configurations in CI. We need to create an automated integration test workflow (`.github/workflows/test_action.yml`) in this repository that exercises `uses: ./` against sample valid and invalid MCP configuration fixtures to prevent breaking downstream CI users.

### Implementation Steps
1. **Fixture Creation (`tests/fixtures/configs/`)**:
   - Provide `valid_claude_desktop_config.json` (no collisions).
   - Provide `colliding_cursor_config.json` (contains tool collisions across servers).
2. **Workflow Creation (`.github/workflows/test_action.yml`)**:
   - Trigger on push and pull requests affecting `action.yml`, `src/mcp_fingerprints/conflict_detector.py`, or `cli.py`.
   - Step 1: Run `uses: ./` on valid config expecting success (exit code 0).
   - Step 2: Run `uses: ./` on colliding config with `fail-on-critical: false` expecting clean exit with report.
   - Step 3: Run `uses: ./` on colliding config with `fail-on-critical: true` verifying failure step behavior.
3. **Action Documentation**:
   - Add usage snippet in `README.md` showing how to invoke `JMartynov/mcp-fingerprints@v1` in GitHub Actions.

### Acceptance Criteria
- [x] `.github/workflows/test_action.yml` created and passing on GitHub Actions.
- [x] Composite action `uses: ./` tested for both passing and collision-failing scenarios.
- [x] Action execution time is fast (<1 minute on Ubuntu latest).
- [x] Usage instructions in `README.md` verified.

---

## 5. Automated Conflict Resolver & Namespacing (`mcp-fingerprints resolve-config`)
- **Board Item ID**: `DI_lAHOD-xmQM4BmPbTzgLUhi0`
- **Category**: Advanced Features (Wave 4)

### Context & Objective
Currently, `conflict_detector.py` and `mcp-fingerprints audit-config` identify exact collisions and shadowing (e.g. both `filesystem` and `github` declaring `read_file`). However, users must manually edit configs or figure out how to namespace them. We need an automated resolver command (`mcp-fingerprints resolve-config`) that ingests a client configuration, resolves collisions by auto-namespacing conflicting tool names or rewriting server arguments, and outputs a sanitized client config.

### Implementation Steps
1. **Core Resolver Module (`src/mcp_fingerprints/conflict_resolver.py`)**:
   - `resolve_client_config(config_path: Path, strategy: str = "prefix", output_path: Path | None = None) -> ResolveResult`.
   - Strategies:
     - `prefix`: Rewrites server commands/env or wraps them with server prefixes (e.g. `github__<tool>`).
     - `priority`: Uses passport stars/reputation to prioritize official/high-star servers.
     - `filter`: Generates client configs with duplicate tools explicitly disabled where supported.
2. **CLI Command (`src/mcp_fingerprints/cli.py`)**:
   - Add `mcp-fingerprints resolve-config <path/to/config.json> --strategy [prefix|priority] --output <path>`.
   - Support colored diff preview in terminal.
3. **Unit Tests (`tests/test_conflict_resolver.py`)**:
   - Test resolving configurations with 2+ colliding servers.
   - Verify non-colliding server definitions and arguments remain untouched.
   - Test CLI roundtrip and JSON schema compliance.

### Acceptance Criteria
- [x] `mcp-fingerprints resolve-config --help` exposes strategy options and output paths.
- [x] Colliding tools are successfully identified and disambiguated.
- [x] Non-conflicting server definitions and arguments are preserved with 100% fidelity.
- [x] Full unit test coverage in `tests/test_conflict_resolver.py` without regressions.

---

## 6. Web Catalog: In-Browser Multi-Server Config Builder
- **Board Item ID**: `DI_lAHOD-xmQM4BmPbTzgLUhi8`
- **Category**: Advanced Features (Wave 4)

### Context & Objective
The web directory (`web/index.html`) currently allows searching 5,031+ servers and copying individual client snippets. To make MCP adoption frictionless, we should allow users to multi-select multiple servers (e.g. Postgres + Filesystem + GitHub + Slack), run client-side collision detection in JavaScript, and generate a unified, conflict-free `claude_desktop_config.json`, `cursor_settings.json`, or Cline config with 1-click download/copy.

### Implementation Steps
1. **Catalog UI Additions (`web/index.html` & `web/app.js`)**:
   - Add selection checkbox on each server card.
   - Add sticky floating drawer ('Selected Servers (N)') with a 'Build Config' action.
   - Display modal with target client tabs (Claude Desktop, Cursor, Cline, Zed, Windsurf, Docker).
2. **Client-Side Collision Engine (`web/app.js`)**:
   - Implement client-side collision detector comparing tools across selected servers.
   - Surface collision warning badges directly in the modal if duplicate tool names exist.
3. **1-Click Copy & Download**:
   - 1-click 'Copy Combined Config'.
   - 1-click 'Download config.json'.
4. **Validation & Tests**:
   - Add unit tests in `tests/test_web_catalog.py` verifying combined config generation logic.

### Acceptance Criteria
- [x] Users can select multiple servers across search queries without losing selections.
- [x] Multi-server builder generates valid JSON for Claude, Cursor, Cline, Zed, and Windsurf.
- [x] Duplicate tool names across selected servers trigger a clear warning in the builder UI.
- [x] 1-click clipboard copy and file download function without browser errors.

---

## 7. Automate Drift Alerts & Tamper Warnings in Daily CI
- **Board Item ID**: `DI_lAHOD-xmQM4BmPbTzgLUhjQ`
- **Category**: Advanced Features (Wave 4)

### Context & Objective
`src/mcp_fingerprints/drift_detector.py` provides complete supply-chain drift detection, tamper verification (`toolset_canonical_hash` changes without version bump), and webhook notifications. However, it is not yet invoked inside the scheduled `.github/workflows/daily_sync.yml`. We need to wire drift detection into the daily CI pipeline so that comparing previous `passports.json.gz` against new synchronizer output automatically posts a markdown warning to GitHub Step Summary, triggers webhook notifications if `WEBHOOK_URL` is set, and opens an automated GitHub issue on critical tamper events.

### Implementation Steps
1. **Pipeline Integration (`.github/workflows/daily_sync.yml`)**:
   - Before compiling new snapshot, preserve previous snapshot as `previous_passports.json.gz`.
   - Run drift detection: `python -m mcp_fingerprints.cli detect-drift --old previous_passports.json.gz --new data/fingerprints --output drift_report.json`.
   - Append formatted drift report to `$GITHUB_STEP_SUMMARY`.
2. **Automated Issue Filing on Critical Tamper**:
   - If critical hash tampering or unannounced tool additions are detected, use `gh issue create` to alert maintainers.
3. **Webhook Notifications**:
   - Pass optional `SECURITY_WEBHOOK_URL` secret to `detect-drift` for Discord/Slack alerts.
4. **Unit Tests**:
   - Update `tests/test_ci_pipeline.py` asserting proper step ordering and environment variables.

### Acceptance Criteria
- [x] `.github/workflows/daily_sync.yml` runs `detect-drift` on every scheduled execution.
- [x] Drift summary is published to GitHub Step Summary.
- [x] Critical tampering triggers automated notifications/issues.
- [x] CI pipeline test suite passes without regressions.

---

## 8. Semantic & Embedding-Based Tool Search
- **Board Item ID**: `DI_lAHOD-xmQM4BmPbTzgLUhkQ`
- **Category**: Advanced Features (Wave 4)

### Context & Objective
`src/mcp_fingerprints/search.py` and `cli.py` currently implement fast keyword, token overlap, and prefix BM25-style searching. When an agent or developer searches for high-level capabilities like 'read spreadsheet', 'manage pull requests', or 'transcribe audio', keyword search may fail if the server's tools are named `sheets_get_range`, `gh_pr_review`, or `whisper_infer`. We need an optional semantic search module leveraging lightweight local embeddings (e.g. FastEmbed / BAAI/bge-small-en or quantized embeddings) to support high-accuracy semantic intent matching across all 5,000+ indexed servers.

### Implementation Steps
1. **Semantic Search Module (`src/mcp_fingerprints/semantic_search.py`)**:
   - Optional dependency group in `pyproject.toml`: `mcp-fingerprints[semantic] = ["fastembed>=0.3.0"]`.
   - Embed tool descriptions and names into lightweight vector representations (`embeddings.npz` or local SQLite cache).
   - `semantic_search(query: str, passports: list[dict], top_k: int = 10) -> list[tuple[dict, float]]`.
   - Graceful fallback to lexical search if `fastembed` is absent.
2. **CLI Integration (`src/mcp_fingerprints/cli.py`)**:
   - Add `--semantic` flag to `mcp-fingerprints search <query>`.
   - Informative error/hint if optional dependencies are not installed.
3. **Index Pre-Computation Script (`scripts/build_semantic_index.py`)**:
   - Generate embeddings for catalog to support sub-10ms queries.
4. **Unit Tests (`tests/test_semantic_search.py`)**:
   - Test semantic matching using mock vectors.
   - Test fallback behavior and CLI arguments.

### Acceptance Criteria
- [x] `mcp-fingerprints search 'read spreadsheet' --semantic` identifies spreadsheet tools despite lexical divergence.
- [x] Core package remains zero-bloat; `fastembed` is an optional extra.
- [x] Graceful fallback to lexical search occurs cleanly when semantic dependencies are omitted.
- [x] Full unit test coverage in `tests/test_semantic_search.py`.


---

## 9. Pre-computed Semantic Embeddings Cache & Vector Index
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzg_qa_0`
- **Category**: Performance & Optimization
- **Status**: Done

### 1. Architectural Context & Objective
`src/mcp_fingerprints/semantic_search.py` introduced intent-based semantic tool search using FastEmbed (`BAAI/bge-small-en-v1.5`). However, computing embeddings on-the-fly across 5,061 passports during an interactive query takes 4–8 seconds, which degrades CLI and agent usability.
This task builds an offline vector index compiler (`scripts/build_semantic_index.py`) that pre-computes 384-dimensional normalized vector embeddings for all indexed servers and tools, storing them in a compressed NumPy archive (`data/embeddings.npz`). The runtime search module is upgraded to automatically load this cache via memory mapping or direct array load, enabling sub-5ms cosine similarity dot products over 5,000+ servers.

### 2. Technical Implementation Specifications
1. **Embedding Compilation Script (`scripts/build_semantic_index.py`)**:
   - Traverses `data/fingerprints/**/*.json` (handling nested scoped directories like `@modelcontextprotocol/`).
   - For each passport, synthesizes an embedding document string:
     `Document = "{package_name} | {description} | Tools: {tool_1_name}: {tool_1_desc}..."`.
   - Batches text encoding (batch size: 128) using `fastembed.TextEmbedding(model_name="BAAI/bge-small-en-v1.5")`.
   - Normalizes embeddings with $L_2$ norm so cosine similarity is computed as a pure matrix-vector dot product $S = E \cdot q$.
   - Writes `data/embeddings.npz` containing `vectors` (float32), `package_names`, and `metadata`.
2. **Runtime Engine Integration (`src/mcp_fingerprints/semantic_search.py`)**:
   - `load_precomputed_index(index_path=None) -> tuple[np.ndarray, list[str]] | None`.
   - If `data/embeddings.npz` is present: encodes only query vector $q$, runs matrix dot product, and uses `argpartition` for top-$K$ selection in $O(N)$ time.
   - If missing: falls back to on-the-fly embedding with clear guidance.
3. **CLI Integration (`src/mcp_fingerprints/cli.py`)**:
   - Add command `mcp-fingerprints build-index [--passports-dir <dir>] [--output <path>]`.
   - Update `mcp-fingerprints search --semantic` to display index utilization status.
4. **CI Scheduled Generation (`.github/workflows/daily_sync.yml`)**:
   - Add step after snapshot compilation: `python scripts/build_semantic_index.py`.

### 3. Clear Acceptance Criteria
- [x] `scripts/build_semantic_index.py` executes cleanly over all 5,061 passports and generates `data/embeddings.npz`.
- [x] `data/embeddings.npz` contains valid `vectors` (float32, normalized), `package_names`, and `metadata` arrays.
- [x] Compressed archive size is less than 15MB.
- [x] `mcp-fingerprints search "<query>" --semantic` automatically detects and uses the cached index.
- [x] Semantic query response latency is under 15ms.
- [x] Graceful fallback to dynamic calculation operates if `data/embeddings.npz` is deleted or absent.
- [x] Unit tests in `tests/test_semantic_index_builder.py` achieve 100% passing rate with mock embeddings.

---

## 10. Automated Vulnerability Remediation Advisor (`mcp-fingerprints fix-advisories`)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzg_qbKY`
- **Category**: Security & Compliance
- **Status**: Done

### 1. Architectural Context & Objective
The passport repository tracks 508+ OSV and CVE vulnerability advisories attached to packages via `security_advisories`. While `mcp-fingerprints detect-drift` and `audit-config` alert maintainers to compromised packages, users currently receive no actionable guidance on how to fix them.
This task implements an automated remediation advisor (`src/mcp_fingerprints/remediation_advisor.py`) and a new CLI command (`mcp-fingerprints fix-advisories`). It parses client configuration files (Claude Desktop, Cursor, Cline, Zed, Windsurf), inspects declared server packages against the OSV advisory database, and generates exact remediation pathways: either minimum safe version upgrades or semantically equivalent alternative MCP packages for deprecated or abandoned vulnerable servers.

### 2. Technical Implementation Specifications
1. **Core Remediation Advisor (`src/mcp_fingerprints/remediation_advisor.py`)**:
   - `class RemediationAction`: defines `package_name`, `current_version`, `cve_list`, `action_type` (`"upgrade"` | `"replace"`), `target_package`, `target_version`, and `similarity_score`.
   - `evaluate_client_config(config_path, passport_dir) -> RemediationReport`.
   - Pathway 1 (Version Upgrade): searches passport versions for the lowest version $> \text{current}$ that is free of known CVEs.
   - Pathway 2 (Alternative Server): if no clean version exists, searches passports for alternative servers with overlapping tool sets (Jaccard tool similarity + high stars).
2. **Configuration Rewriter & CLI Interface (`src/mcp_fingerprints/cli.py`)**:
   - Command: `mcp-fingerprints fix-advisories <config.json> [--apply] [--strategy upgrade|replace|all] [--output <path>]`.
   - Default: renders ASCII table with CVE IDs, severity, and proposed actions.
   - `--apply`: atomically updates configuration file updating commands, arguments, and environment variables.
3. **Multi-IDE Schema Preservation**:
   - Preserves structures across Claude Desktop, Cursor, Cline, and Zed.
4. **Unit Tests (`tests/test_remediation_advisor.py`)**:
   - Test version upgrade resolution against fixture packages with known CVE ranges.
   - Test alternative server recommendation when a package has no safe releases.
   - Test CLI roundtrip with `--apply` verifying syntax preservation.

### 3. Clear Acceptance Criteria
- [x] `mcp-fingerprints fix-advisories --help` is registered and documents all options.
- [x] Accurately identifies package versions vulnerable to recorded CVEs in fixture configs.
- [x] Recommends minimal safe version bumps that bypass vulnerable semver ranges.
- [x] Successfully proposes healthy alternative servers with matching tool capabilities when a package has no safe release.
- [x] `--apply` updates the configuration file in-place or writes to `--output` without corrupting non-vulnerable servers.
- [x] Preserves all client-specific top-level keys and formatting across Claude, Cursor, Cline, and Zed.
- [x] Returns exit code 1 if unaddressed vulnerabilities remain without safe remediation, and 0 on clean configs or successful remediation.
- [x] Full unit test suite passes with 100% code coverage across `remediation_advisor.py`.

---

## 11. Remote SSE & WebSocket Cloud Transport Indexing & Export
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzg_qbXY`
- **Category**: Protocol & Specifications
- **Status**: Done

### 1. Architectural Context & Objective
The Model Context Protocol specification supports both local standard I/O (`stdio`) and remote transports: Server-Sent Events (`sse`) over HTTP and bidirectional WebSockets (`websocket`). Currently, our passports and synchronizer predominantly model local process execution commands (`npx`, `uvx`, `docker`). As enterprise and cloud-hosted MCP servers proliferate, we must expand our passport data model, crawler, validator, and configuration exporters to index, validate, and export remote cloud MCP endpoints.

### 2. Technical Implementation Specifications
1. **Pydantic Data Models & Schema (`src/mcp_fingerprints/models.py`)**:
   - `TransportType = Literal["stdio", "sse", "websocket"]`.
   - In `ServerPackageSpec` & `VersionFingerprint`:
     - `transport: TransportType = "stdio"`
     - `remote_endpoint: str | None = None`
     - `auth_type: Literal["none", "bearer", "api-key", "oauth2"] = "none"`
     - `headers_schema: dict[str, str] = Field(default_factory=dict)`
2. **Crawler & Synchronizer Ingestion (`src/mcp_fingerprints/crawler.py` & `synchronizer.py`)**:
   - Detect `url`, `sse`, or `websocket` declarations in Smithery and Official Registry manifests.
   - Validate URI schemes (`https://` or `wss://`), rejecting unencrypted endpoints unless localhost.
3. **IDE Client Exporters (`src/mcp_fingerprints/config_exporter.py`)**:
   - Update Claude Desktop exporter: output `"transport": "sse"`, `"url": "..."`, and `"headers": {...}` blocks when `transport == "sse"`.
   - Update Cursor, Cline, and Zed exporters for remote endpoint formats.
4. **Validation Engine (`src/mcp_fingerprints/validator.py`)**:
   - Ensure that if `transport == "sse"`, `remote_endpoint` is a valid parseable HTTPS URL.
5. **Unit Tests (`tests/test_remote_transports.py`)**:
   - Test passport validation with SSE/WebSocket definitions and config export across all clients.

### 3. Clear Acceptance Criteria
- [x] `ServerPackageSpec` and `VersionFingerprint` support `transport`, `remote_endpoint`, `auth_type`, and `headers_schema`.
- [x] Passports with `transport: "sse"` validate successfully against schema invariants.
- [x] Remote URLs must adhere to HTTPS/WSS (rejecting plain HTTP unless localhost).
- [x] `export-config` generates valid Claude Desktop JSON with `url` and `headers` for SSE servers.
- [x] `export-config` generates valid Cursor and Zed configurations for remote servers.
- [x] Existing 5,061 `stdio` passports continue to pass 100% of invariant tests without modification.
- [x] Comprehensive unit tests in `tests/test_remote_transports.py` pass cleanly.

---

## 12. Interactive Terminal TUI Browser (`mcp-fingerprints browse`)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzg_qbfY`
- **Category**: Developer Tooling & UX
- **Status**: Done

### 1. Architectural Context & Objective
Developers, DevOps engineers, and security analysts working in remote SSH sessions or terminal-based workflows currently rely on `mcp-fingerprints search <query>` or must open a browser to access the GitHub Pages catalog.
This task creates an interactive, zero-dependency Terminal User Interface (`src/mcp_fingerprints/tui.py`) using Python standard library `curses` and adds `mcp-fingerprints browse`. It gives terminal users instant keyboard navigation, live fuzzy searching across 5,000+ servers, ecosystem filtering tabs, tool schema and parameter inspection panes, and 1-click clipboard export for client configurations.

### 2. Technical Implementation Specifications
1. **Interactive TUI Core (`src/mcp_fingerprints/tui.py`)**:
   - `class MCPCatalogBrowser` built using Python `curses`.
   - Responsive multi-pane layout:
     - Header: Live search bar + Ecosystem filter tabs (`[All]`, `[NPM]`, `[PyPI]`, `[GitHub]`).
     - Left Pane: Scrollable server list (package name, version, stars, risk badges).
     - Right Pane: Server details: description, repository links, tool signatures, parameter schemas, and security advisories.
     - Footer: Keyboard shortcuts help bar (`[↑/↓]` Navigate, `[Tab]` Switch Pane, `[C]` Copy Config, `[Q]` Quit).
   - Window resize handling (`curses.KEY_RESIZE`) maintaining minimum readable bounds.
2. **Clipboard & Export Actions**:
   - Pressing `C` generates and copies selected server's Claude Desktop JSON block to system clipboard.
3. **CLI Integration (`src/mcp_fingerprints/cli.py`)**:
   - Add command: `mcp-fingerprints browse [--dir <dir>] [--query <initial_search>]`.
   - Checks `sys.stdin.isatty()`: exits cleanly with informative message in non-interactive / CI pipelines.
4. **Unit Tests (`tests/test_tui.py`)**:
   - Test data filtering, search matching, and keyboard event state machines with mock headless test harness.

### 3. Clear Acceptance Criteria
- [x] `mcp-fingerprints browse --help` displays command options and usage.
- [x] Running in an interactive TTY launches the curses-based split-pane browser.
- [x] Live search filters the server list instantaneously as keystrokes are received.
- [x] Left/Right pane navigation accurately displays tools, signatures, and risk badges for the selected server.
- [x] Pressing `Q` or `Ctrl+C` cleanly restores terminal state without cursor distortion.
- [x] Detects non-interactive environments (CI, pipes) and exits gracefully without raising `curses.error`.
- [x] Zero heavy third-party dependencies required; operates cleanly on standard Python libraries.
- [x] Unit tests pass in headless test mode.

---

## 13. Automated TestPyPI Dry-Run Workflow (`.github/workflows/test_release.yml`)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzg_qbsk`
- **Category**: CI/CD & Operations
- **Status**: Done

### 1. Architectural Context & Objective
`.github/workflows/release.yml` directly targets the production Python Package Index (`https://upload.pypi.org/legacy/`) using OpenID Connect (OIDC) trusted publishing when release tags are pushed. Before cutting production release tag `v1.0.0`, any mismatch in OIDC claims, permissions, environment names, or packaging metadata could cause public release failures or burn version numbers.
This task creates an automated TestPyPI verification pipeline (`.github/workflows/test_release.yml`). It runs on `workflow_dispatch` (with optional candidate version suffix like `1.0.0rc1`), builds clean sdist/wheel artifacts, validates them with `twine check`, publishes to `https://test.pypi.org/legacy/` using trusted publishing, and executes an automated smoke test verifying that `pip install` from TestPyPI installs cleanly into an isolated container.

### 2. Technical Implementation Specifications
1. **GitHub Actions Workflow (`.github/workflows/test_release.yml`)**:
   - Triggers: `workflow_dispatch` with `version_suffix` and `skip_smoke_test` inputs.
   - Permissions: `id-token: write`, `contents: read`.
   - Environment: `testpypi`.
   - Jobs:
     - `build`: checks out repo, setups Python 3.12, builds sdist/wheel via `python -m build`, and runs `twine check dist/*`.
     - `publish`: uses `pypa/gh-action-pypi-publish@release/v1` with `repository-url: https://test.pypi.org/legacy/`.
     - `smoke-test`: runs in clean container: `pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-fingerprints`, then runs `mcp-fingerprints --version`.
2. **Unit Tests (`tests/test_packaging_metadata.py`)**:
   - Update tests to parse `.github/workflows/test_release.yml` with `pyyaml`.
   - Validate triggers, permissions (`id-token: write`), TestPyPI repository URL, and job dependencies.

### 3. Clear Acceptance Criteria
- [x] `.github/workflows/test_release.yml` exists and is valid GitHub Actions workflow YAML.
- [x] Defines `workflow_dispatch` with customizable version suffix input.
- [x] Correctly targets `https://test.pypi.org/legacy/` with trusted publishing OIDC tokens.
- [x] Includes automated smoke test validating post-publish `pip install` from TestPyPI.
- [x] Automated tests in `tests/test_packaging_metadata.py` pass verifying workflow structure.
- [x] Documentation added to `README.md` explaining how to execute a TestPyPI dry run.

