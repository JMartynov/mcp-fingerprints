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

---

## 14. Ingestion Hardening & Malformed Tool Sanitization (Daily CI Fix)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzg_5O_8`
- **Category**: Ingestion & Data Quality
- **Status**: Done

### 1. Architectural Context & Objective
Daily scheduled sync runs (`.github/workflows/daily_sync.yml`) scrape and index MCP packages from npm and PyPI registries. In real-world ecosystems, upstream repositories frequently publish malformed tool schemas—such as missing `name` strings, non-dictionary `inputSchema` objects, null property values, invalid JSON types, or unparseable AST constructs. When encountering these, the ingestion pipeline should never crash or abort the sync job.
This task hardens the ingestion pipeline in `src/mcp_fingerprints/ast_parser.py`, `src/mcp_fingerprints/synchronizer.py`, and `src/mcp_fingerprints/validator.py` with robust tool sanitization, defensive default fallbacks, schema normalization, and quarantine logging to guarantee 100% resilient daily CI execution.

### 2. Technical Implementation Specifications
1. **Tool Sanitization Utility (`src/mcp_fingerprints/validator.py`)**:
   - Implemented `sanitize_tool_definition(tool: dict[str, Any]) -> dict[str, Any] | None`:
     - Validates tool name: non-empty string, strips extraneous whitespace and control characters `[\x00-\x1F\x7F]`.
     - Validates `inputSchema`: if missing or not a dict, normalizes to standard schema `{"type": "object", "properties": {}}`.
     - Validates property schemas: ensures properties dictionary is well-formed, normalizing null or malformed definitions to `{}`.
     - Validates description: ensures string representation; defaults to `""`.
     - Rejects unrecoverable tool objects cleanly with a warning rather than raising unhandled exceptions.
2. **Synchronizer & Parser Ingestion Defense (`src/mcp_fingerprints/synchronizer.py` & `ast_parser.py`)**:
   - Wrapped tool extraction loops in PyPI wheel/sdist and npm tarball processing with `sanitize_tool_definition`.
   - Guarded `parse_python_mcp_ast` visitor traversal against unhandled AST syntax exceptions.
   - Guarded `ToolContractSignature.from_dict` against malformed schema structures.
3. **Comprehensive Unit Tests (`tests/test_ingestion_sanitization.py`)**:
   - Tests covering valid tools, invalid/non-string names, control character stripping, schema normalization, and defensive `from_dict`.

### 3. Clear Acceptance Criteria
- [x] `sanitize_tool_definition` gracefully handles missing fields, non-string names, and invalid schema types.
- [x] Normalizes malformed `inputSchema` into compliant JSON Schema dictionary.
- [x] Ingestion pipeline in `synchronizer.py` continues smoothly when encountering malformed tools without raising unhandled exceptions.
- [x] `ToolContractSignature` construction remains stable with corrupted or non-standard tool dicts.
- [x] Full unit test suite in `tests/test_ingestion_sanitization.py` passes 100%.

---

## 15. CLI Audit Autofix Integration (`mcp-fingerprints audit-config --fix`)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzg_5PDU`
- **Category**: Security & CLI Tools
- **Status**: Done

### 1. Architectural Context & Objective
Currently, `mcp-fingerprints audit-config` inspects client configurations (Claude Desktop, Cursor, Cline, Zed) for collisions and security risks, but requires users to run a separate command (`mcp-fingerprints fix-advisories --apply`) to remediate vulnerabilities.
This task unifies the developer experience by integrating an automated `--fix` flag directly into `mcp-fingerprints audit-config`. When invoked with `--fix`, the CLI automatically audits the configuration, detects vulnerabilities and collisions, presents an action plan, and safely patches the target configuration file while preserving client-specific schemas and comments.

### 2. Technical Implementation Specifications
1. **CLI Argument Parser Extension (`src/mcp_fingerprints/cli.py`)**:
   - Added `--fix` flag to `audit-config` subparser.
   - Added `--strategy` option (`upgrade`, `replace`, `all`, default: `all`).
   - Added `--dry-run` flag to display proposed modifications without writing to disk.
   - Added `--backup` / `--no-backup` option to create a timestamped backup before modifying files.
2. **Remediation Integration**:
   - Connected `audit_client_config` with `remediation_advisor.evaluate_client_config`.
   - When `--fix` is passed:
     - Runs audit and detects both collisions and known CVE/OSV advisories.
     - Safely rewrites client configuration file with upgrade/replacement recommendations.
     - Displays formatted summary of applied fixes.
3. **Unit Tests (`tests/test_audit_config_autofix.py`)**:
   - Verifies `--fix --dry-run` preview behavior, in-place patching, backup creation, and schema preservation across Claude Desktop, Cursor, and Cline configs.

### 3. Clear Acceptance Criteria
- [x] `mcp-fingerprints audit-config --help` shows `--fix`, `--strategy`, and `--dry-run` options.
- [x] Running `audit-config --fix` on a vulnerable configuration safely updates the file to safe package versions.
- [x] `--dry-run` simulates the remediation without touching disk.
- [x] Preserves client JSON structure across Claude Desktop, Cursor, and Cline configuration schemas.
- [x] Unit tests in `tests/test_audit_config_autofix.py` pass 100%.

---

## 16. Web Catalog Deep Linking & Security Advisory Badges
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzg_5PIA`
- **Category**: Web Catalog & UI
- **Status**: Done

### 1. Architectural Context & Objective
The static web catalog (`web/index.html` + `web/app.js` + `web/catalog.json`) serves as the primary searchable portal for 5,031+ MCP servers deployed to GitHub Pages. However, users previously could not share links to specific servers or filtered views because the page lacked URL routing/deep linking. Furthermore, servers with known security advisories or high risk did not visibly highlight OSV advisory references.
This task adds URL deep linking and interactive security advisory badges to the web catalog. Users can link directly to any server (`#server=<name>` or `?server=<name>`) or search state (`?q=<query>&eco=<ecosystem>`). The catalog entries and UI cards are enriched with security advisory badges and direct links to advisory details.

### 2. Technical Implementation Specifications
1. **Catalog Entry Enrichment (`scripts/generate_web_catalog.py`)**:
   - Included advisory metadata in catalog entries: `advisories` (list of CVE/OSV IDs) and `advisory_count`.
2. **Web Deep Linking & State Sync (`web/app.js`)**:
   - Reads URL hash and search params on page load (`URLSearchParams` and `window.location.hash`).
   - If `server` param is present, filters or scrolls to and highlights the targeted server card.
   - If `q` or `eco` params are present, pre-fills search input and ecosystem filter tabs.
   - Updates URL dynamically when user searches or filters using `history.replaceState`.
   - Added direct copyable share links per server card.
3. **Security Advisory Badges UI (`web/index.html` & `web/app.js`)**:
   - Renders distinct security advisory badge (`badge-advisory`) when `advisory_count > 0`.
   - Clicking badge links directly to OSV database (`https://osv.dev/vulnerability/<ID>`).
4. **Unit Tests (`tests/test_web_catalog.py`)**:
   - Verifies `build_catalog_entry` extracts advisories, and `app.js` and `index.html` contain deep-linking and advisory badge elements.

### 3. Clear Acceptance Criteria
- [x] `scripts/generate_web_catalog.py` populates advisory information in `web/catalog.json`.
- [x] `web/app.js` initializes search query and ecosystem filters from URL search params.
- [x] Deep linking to `?server=<name>` or `#server=<name>` highlights the specified server.
- [x] Servers with known vulnerabilities display clear security advisory badges with advisory links.
- [x] Unit tests in `tests/test_web_catalog.py` validate catalog building and deep-linking DOM logic.

---

## 17. Open-Source Community Polish (CONTRIBUTING.md & Release Template)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzg_5PL4`
- **Category**: Community & Governance
- **Status**: Done

### 1. Architectural Context & Objective
With `mcp-fingerprints` approaching its v1.0.0 milestone, open-source governance and contributor workflows need to be formalized. Contributors submitting new MCP servers or bug fixes need clear setup instructions, code style standards, and structured GitHub issue/PR templates.
This task delivers comprehensive open-source community polish: a complete `CONTRIBUTING.md`, structured GitHub issue templates for bug reports, feature requests, and new server passport submissions, a pull request template, a release checklist template, and automated test validation.

### 2. Technical Implementation Specifications
1. **Contributor Guidelines (`CONTRIBUTING.md`)**:
   - Architecture overview: AST parsing, fingerprinting, vector indexing, and client configurations.
   - Local development environment setup: Python 3.10+, virtual environment, `pip install -e ".[dev]"`.
   - Code standards: `ruff`, `pre-commit`, typing, and `pytest`.
   - MCP Server Passport Submission Guide: how to add or update server passports in `data/fingerprints/`.
   - Security vulnerability reporting policy (responsible disclosure).
2. **GitHub Issue Templates (`.github/ISSUE_TEMPLATE/`)**:
   - `bug_report.md`: Structured form for reporting bugs with environment details, reproduction steps, and logs.
   - `feature_request.md`: Template for proposing new features and CLI commands.
   - `new_mcp_server.md`: Standardized checklist and metadata form for submitting a new MCP server passport.
3. **Pull Request Template (`.github/pull_request_template.md`)**:
   - PR description, linked issues, checklist (tests pass, documentation updated, no secrets committed).
4. **Release Checklist Template (`.github/RELEASE_TEMPLATE.md`)**:
   - Step-by-step checklist for release managers: pre-flight checks, TestPyPI dry-run verification, changelog generation, git tagging, and PyPI release steps.
5. **Community Health Unit Tests (`tests/test_community_health.py`)**:
   - Automated pytest assertions validating that all templates and guidelines exist and contain required sections.

### 3. Clear Acceptance Criteria
- [x] `CONTRIBUTING.md` exists and covers development setup, testing, passport submissions, and security reporting.
- [x] `.github/ISSUE_TEMPLATE/bug_report.md`, `feature_request.md`, and `new_mcp_server.md` exist and are valid.
- [x] `.github/pull_request_template.md` exists with clear contributor verification checkboxes.
- [x] `.github/RELEASE_TEMPLATE.md` exists detailing v1.0.0 release procedures.
- [x] Unit tests in `tests/test_community_health.py` pass 100%.



---

## 18. Clean Architecture: Codebase Structural Decoupling
- **Board Item ID**: `T18_CleanArchitectureCode`
- **Category**: Architecture & Refactoring
- **Status**: Done

### 1. Architectural Context & Objective
Remove vulnerability extraction (e.g. `OSV_DB_URL`, `OSVAdvisory` dataclass, `sync_advisories()`) from `mcp-fingerprints`, migrating these responsibilities to the `mcp-vulnerabilities` database. Also, move active remediation (e.g. `remediate()`, `PatchStrategy`) to `verity-mcp-auditor`. `mcp-fingerprints` must focus purely on being a static structural passport standard and knowledge base.

### 2. Technical Implementation Specifications
1. Strip out `OSV_DB_URL`, OSV/CVE extraction logic, and the `OSVAdvisory` dataclass.
2. Remove active remediation functions and `PatchStrategy`.
3. Update pure functions in `mcp_fingerprints/` and tests in `tests/`.

### 3. Clear Acceptance Criteria
- [x] No `OSV` or `CVE` references in core `mcp_fingerprints` logic.
- [x] No active `remediate()` logic.

---

## 19. Clean Architecture: Purify Data Models
- **Board Item ID**: `T19_CleanArchitectureModels`
- **Category**: Architecture & Refactoring
- **Status**: Done

### 1. Architectural Context & Objective
Modify core data models (`ServerPackageSpec`, `VersionFingerprint`) in `mcp_fingerprints/models.py` to remove vulnerability tracking fields (`advisories`, `vulnerabilities`) and security remediation attributes, ensuring the schema remains strictly structural.

### 2. Technical Implementation Specifications
1. Remove `advisories` and `vulnerabilities` fields from models.
2. Update JSON mock files in tests to reflect the new strict structural schema.
3. Fix all failing tests due to removed fields.

### 3. Clear Acceptance Criteria
- [x] Core models no longer track advisories.
- [x] Test mocks updated.

---

## 20. Clean Architecture: Refactor Build & Workflow Pipelines
- **Board Item ID**: `T20_CleanArchitecturePipelines`
- **Category**: Architecture & Refactoring
- **Status**: Done

### 1. Architectural Context & Objective
Remove automated CVE advisory fetching, OSV patching steps, and vulnerability scanning logic from GitHub Actions workflows, `scripts/generate_web_catalog.py`, `scripts/build_snapshot.py`, and the CLI.

### 2. Technical Implementation Specifications
1. Refactor `scripts/generate_web_catalog.py` and `scripts/build_snapshot.py`.
2. Refactor GitHub Actions (`daily_sync.yml`, `release.yml`, etc.) to remove OSV/CVE steps.
3. Clean up CLI commands to remove vulnerability patching commands.

### 3. Clear Acceptance Criteria
- [x] Workflows and scripts execute without fetching OSV/CVE data.
- [x] CLI is purified.

---

## 21. Clean Architecture: Ecosystem Boundary Documentation & Governance
- **Board Item ID**: `T21_CleanArchitectureGovernance`
- **Category**: Documentation & Governance
- **Status**: In Progress

### 1. Architectural Context & Objective
Formalize the Clean Architecture separation in project documentation, explicitly defining the ecosystem boundaries between `mcp-fingerprints`, `mcp-vulnerabilities`, and `verity-mcp-auditor`.

### 2. Technical Implementation Specifications
1. Update `docs/SPECIFICATION.md` to define boundaries.
2. Update `README.md` to clarify scope and update CLI tables.
3. Update `CONTRIBUTING.md` to explicitly declare out-of-scope PRs (vulnerabilities, runtime remediation).
4. Add Tasks 18, 19, 20, 21 to `docs/tasks/roadmap_board_specifications.md`.
5. Update `tests/test_community_health.py` to enforce governance documentation tests.

### 3. Clear Acceptance Criteria
- [x] `docs/SPECIFICATION.md` updated.
- [x] `README.md` updated.
- [x] `CONTRIBUTING.md` updated.
- [x] `docs/tasks/roadmap_board_specifications.md` updated.
- [x] `tests/test_community_health.py` validates new boundaries.

---

## 22. Automated Continuous PyPI Release on New Fingerprints Ingestion
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAV094`
- **Category**: Operations & Release
- **Status**: Done

### 1. Architectural Context & Objective
On each successful daily sync where new or updated MCP server fingerprints are ingested, automatically bump the patch version, create a GitHub release, and trigger publishing to PyPI. This guarantees that downstream consumers of the `mcp-fingerprints` PyPI package always have immediate access to the latest fingerprint database and structural signatures without manual maintainer intervention.

### 2. Technical Implementation Specifications
1. **Version Bumping Script (`scripts/bump_version.py`)**:
   - Robust Python script to read the current version from `pyproject.toml` and `src/mcp_fingerprints/__init__.py`.
   - Increment the patch version (e.g. 1.0.0 -> 1.0.1) using `packaging.version.Version`.
   - Support `--dry-run` to print the next version and `--apply` to rewrite `pyproject.toml` and `src/mcp_fingerprints/__init__.py`.
   - Support optional `--pyproject` and `--init-file` for flexible scripting and automated testing.
2. **PyPI Release Reusable Workflow (`.github/workflows/release.yml`)**:
   - Add `workflow_call:` trigger under `on:` so the release job can be triggered as a reusable workflow or via published releases and `workflow_dispatch`.
3. **Daily Sync Automated Continuous Release Integration (`.github/workflows/daily_sync.yml`)**:
   - After compiling new snapshot, check if new or modified fingerprints were added (`git status --porcelain data/fingerprints/`).
   - If changes exist:
     - Run `python scripts/bump_version.py --dry-run` to determine `$NEW_VERSION`.
     - Run `python scripts/bump_version.py --apply`.
     - Git commit: `chore(release): bump version to v<NEW_VERSION> and sync MCP fingerprints`.
     - Tag git release `v<NEW_VERSION>`.
     - Push commit and tag to `origin/main --tags`.
     - Create GitHub release with `gh release create v<NEW_VERSION> --title "v<NEW_VERSION>: Automated Fingerprint Sync Release" --generate-notes`.
     - Pass outputs `release_created=true` and trigger reusable workflow job `pypi-release` with `id-token: write` permissions.
4. **Test Suite (`tests/test_automated_release_trigger.py`)**:
   - Test version bumping logic, regex/semver replacement, file synchronization between `pyproject.toml` and `src/mcp_fingerprints/__init__.py`, CLI `--dry-run` and `--apply`, and workflow trigger configurations.

### 3. Clear Acceptance Criteria
- [x] `scripts/bump_version.py` supports `--dry-run` and `--apply`, correctly bumping patch version using `packaging.version.Version` and keeping `pyproject.toml` and `src/mcp_fingerprints/__init__.py` in sync.
- [x] `.github/workflows/release.yml` includes `workflow_call:` trigger under `on:`.
- [x] `.github/workflows/daily_sync.yml` detects fingerprint updates, runs `bump_version.py --apply`, commits, tags `v<NEW_VERSION>`, pushes, creates GitHub release, and triggers PyPI release workflow.
- [x] `tests/test_automated_release_trigger.py` passes 100% and validates version bumping, synchronization, and workflow triggers.
- [x] Full project test suite passes cleanly with `PYTHONPATH=src pytest` (214 passed, 4 skipped).


---

---



## 23. Hierarchical JSON Partitioning & Ephemeral DuckDB Acceleration
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAY4ic`
- **Category**: Storage & Indexing
- **Status**: Completed



### 1. Architectural Context & Technical Objective

`mcp_fingerprints` stores tool fingerprints and metadata as raw JSON files in `data/fingerprints/`. As the repository grows to thousands of fingerprints, a flat directory structure poses issues with inode scaling, git tree performance, and traversal overhead. Furthermore, doing live searches over thousands of JSON files strictly via Python dictionaries and standard loops can result in higher latency.

The objective is to implement a hierarchical directory structure (partitioning) for JSON files based on ecosystem and package name to prevent single-directory scaling issues. Alongside this, an `EphemeralDBEngine` leveraging DuckDB (when available) will be implemented to act as an on-demand, `:memory:` or `.cache/` backed query acceleration engine over these JSON files without introducing tracked binary files into git, keeping the JSON structure as the canonical source of truth.



### 2. Technical Implementation Specifications

1. **Partitioning Engine**: `src/mcp_fingerprints/partitioner.py` handles computing hierarchical path based on ecosystem and first char of namespace/package.

2. **Ephemeral DB Engine**: `src/mcp_fingerprints/db_engine.py` using DuckDB (with fallback to SQLite/Dict) to accelerate `search_packages` and `find_by_hash`.

3. **Repository Updates**: `.gitignore` configured to ignore binary caches and DB files, keeping git clean.



### 3. Clear Acceptance Criteria

- [x] Hierarchical partitioning logic implemented and unit tested.

- [x] DuckDB query acceleration implemented with `read_json_auto`.

- [x] Fallback mechanisms are stable.

- [x] Zero git footprint constraints enforced.



## 24. Resilient Network Ingestion Engine (`tenacity` & HTTP 429 Queues)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAYXnc`
- **Category**: Ingestion & Resilience
- **Status**: Backlog

### 1. Architectural Context & Technical Objective
Currently, the ingestion engine in `mcp_fingerprints` (specifically when downloading and verifying MCP repositories or interacting with external package registries) lacks robust handling of transient network failures and rate limits. The current implementation can fail pipelines when encountering HTTP 429 (Too Many Requests) or HTTP 500 errors.
The objective of this task is to integrate the `tenacity` library to provide resilient retry logic with exponential backoff and jitter, specifically tailored for network ingestion tasks in `src/mcp_fingerprints/ingestion.py` (or similar modules), ensuring our data pipelines and CI/CD jobs don't randomly fail due to transient external issues. All data ingestion must remain memory-safe and zero-disk-footprint as per architecture guidelines.

### 2. Technical Implementation Specifications
1. Introduce `tenacity` as a dependency in `pyproject.toml`.
2. Implement a new class or module `ResilientIngestionEngine` in `src/mcp_fingerprints/ingestion_engine.py`.
3. Wrap external network calls (e.g., `requests.get` or `httpx.AsyncClient`) with `@retry` decorators using `tenacity`.
4. Configure retry logic:
   - Handle HTTP 429 and HTTP 5xx explicitly.
   - Use `wait_exponential_jitter`.
   - Max retries: 5.
   - Timeout: 60 seconds.
5. Create an asynchronous queue mechanism for bulk ingestion to distribute load and respect rate limits dynamically.

### 3. Clear Acceptance Criteria
- [ ] `tenacity` is added to `pyproject.toml`.
- [ ] Network ingestion calls are wrapped in `tenacity` retry loops.
- [ ] HTTP 429 and 5xx errors trigger retries with exponential backoff and jitter.
- [ ] Bulk ingestion uses an async queue mechanism.

### 4. Unit Test Plan
1. **Mock Setup:** Use `responses` or `pytest-httpx` to mock external endpoints.
2. **Retry Verification:** Mock a sequence of 3 HTTP 429 responses followed by a 200 OK. Assert the function succeeds and the mock was called 4 times.
3. **Failure Verification:** Mock a sequence of 6 HTTP 500 responses. Assert the function eventually raises a retry error after 5 retries.
4. **Queue Verification:** Assert that bulk ingestion processes items concurrently but with a limited concurrency pool (e.g., max 10 concurrent requests).

### 5. Live Acceptance Test Plan
Run `uv run python -c "from mcp_fingerprints.ingestion_engine import fetch_with_retry; fetch_with_retry('http://httpbin.org/status/429,200')"` and observe logs to verify that the retry happens automatically before successfully completing, entirely without mocks.

---

## 25. Automated Semantic Embeddings Cache CI Synchronization
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAYXqA`
- **Category**: CI/CD & Automation
- **Status**: Backlog

### 1. Architectural Context & Technical Objective
The `mcp_fingerprints` repository includes a pre-computed semantic embeddings index (`data/embeddings.npz`) for MCP tool fingerprints using `fastembed` and `numpy`. Currently, this cache must be manually updated when new fingerprints are added.
The objective is to automate the synchronization of this embeddings cache within the CI/CD pipeline (e.g., in `.github/workflows/daily_sync.yml`). This ensures that the vector search remains perfectly in sync with the structural fingerprint database on every automated release.

### 2. Technical Implementation Specifications
1. Create a script `scripts/sync_embeddings.py` that utilizes `src/mcp_fingerprints/semantic_search.py` to regenerate `data/embeddings.npz`.
2. Update `.github/workflows/daily_sync.yml` to run `uv run python scripts/sync_embeddings.py` after new fingerprints are ingested.
3. Ensure the script only runs if new fingerprints are detected.
4. Add the updated `data/embeddings.npz` to the automated commit.
5. The `sync_embeddings.py` script must handle missing optional dependencies (`fastembed`, `numpy`) gracefully during isolated CI environments if not installed, though CI should install the `semantic` extra.

### 3. Clear Acceptance Criteria
- [ ] `scripts/sync_embeddings.py` is implemented and can regenerate `data/embeddings.npz`.
- [ ] `.github/workflows/daily_sync.yml` is updated to include the embedding sync step.
- [ ] Automated commits include the updated `data/embeddings.npz` file.
- [ ] CI uses `uv sync --all-extras` or equivalent to ensure `fastembed` is available.

### 4. Unit Test Plan
1. **Mock Generation:** Mock `fastembed` to return dummy vectors and assert that `sync_embeddings.py` writes an `.npz` file with the correct shape to a temporary directory.
2. **Missing Dependencies:** Run the sync function with `fastembed` mocked out as missing (e.g., `ImportError`) and verify it logs a warning and exits gracefully.
3. **No Changes Detected:** Ensure the script exits early if the existing embeddings cache already matches the latest fingerprints hash.

### 5. Live Acceptance Test Plan
Run `uv sync --all-extras` then manually add a dummy fingerprint to `data/fingerprints/`. Run `python scripts/sync_embeddings.py` and verify `data/embeddings.npz` is modified on disk using `git status`.

---

## 26. Interactive Terminal Setup Wizard (`mcp-fingerprints init`)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAYXsQ`
- **Category**: Developer Experience
- **Status**: Backlog

### 1. Architectural Context & Technical Objective
While `mcp_fingerprints.cli` provides powerful commands, onboarding new users requires them to manually configure their environments or learn complex flags. 
The objective is to implement a robust, interactive setup wizard (`mcp-fingerprints init`) that guides users through configuring their local MCP client integrations (e.g., Claude Desktop, Cursor), setting up semantic search, and bootstrapping their initial configuration file. The wizard must check `sys.stdin.isatty()` to gracefully degrade or abort in headless CI environments.

### 2. Technical Implementation Specifications
1. Add a new `init` command to `src/mcp_fingerprints/cli.py`.
2. Implement the interactive wizard in a new module: `src/mcp_fingerprints/wizard.py`.
3. Use the standard library (e.g., `input()`, `sys.stdout`) to ask users questions (e.g., "Do you want to configure Claude Desktop?", "Do you want to enable semantic search?").
4. Validate `sys.stdin.isatty()` at the start of the command. If false, raise a descriptive error or fall back to defaults.
5. Generate a default configuration file (e.g., `~/.mcp_fingerprints.toml` or similar) based on user input.

### 3. Clear Acceptance Criteria
- [ ] `mcp-fingerprints init` command exists.
- [ ] Wizard checks for interactive terminal (`sys.stdin.isatty()`).
- [ ] Prompts user for configurations (clients, features).
- [ ] Writes a configuration file based on the interactive session.
- [ ] No heavy external UI dependencies added.

### 4. Unit Test Plan
1. **Headless Environment:** Mock `sys.stdin.isatty()` to return `False` and assert the wizard raises a `RuntimeError` or exits gracefully with a message.
2. **Interactive Flow Mocking:** Use `unittest.mock.patch('builtins.input')` with `side_effect` to simulate user responses (e.g., `['y', 'n', 'y']`). Assert the correct configuration dictionary is generated.
3. **Config Write Verification:** Assert that the final configuration is written to the correct destination (mocking `open` or using a temporary directory).

### 5. Live Acceptance Test Plan
Run `uv run mcp-fingerprints init` in a real terminal. Answer the prompts interactively. Verify that the resulting configuration file is created successfully and matches your inputs. Pipe input via `echo "y" | uv run mcp-fingerprints init` to ensure non-TTY behavior handles it appropriately.

---

## 27. First-Class Zed, Cline & Windsurf Native Config Exporters
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAYXuM`
- **Category**: Developer Experience
- **Status**: Backlog

### 1. Architectural Context & Technical Objective
Currently, `mcp_fingerprints` primarily supports exporting client configurations for generic environments or Claude Desktop.
The objective is to expand `src/mcp_fingerprints/exporters.py` to natively support popular IDE extensions and clients like Zed, Cline, and Windsurf. These tools have specific configuration schemas (often JSONC) that require careful parsing and modification to preserve comments and structural integrity, avoiding destructive updates from standard `json.dumps`.

### 2. Technical Implementation Specifications
1. Expand `src/mcp_fingerprints/exporters.py` with specific exporter classes: `ZedExporter`, `ClineExporter`, `WindsurfExporter`.
2. Implement safe string manipulation or use a robust JSONC parsing method (if standard regex/string patching is viable as per project constraints) to inject MCP server configurations without destroying existing comments.
3. Update the CLI `export-config` command to support these new targets (e.g., `--target zed`).
4. Define the strict dictionary schemas expected by each tool based on their public documentation.

### 3. Clear Acceptance Criteria
- [ ] Exporter classes for Zed, Cline, and Windsurf exist.
- [ ] Configurations are patched safely without stripping JSONC comments.
- [ ] `export-config` CLI command supports `--target zed`, `--target cline`, `--target windsurf`.

### 4. Unit Test Plan
1. **JSONC Preservation:** Create mock JSONC strings containing comments. Pass them through the exporters and assert the output retains the comments and correctly inserts the new server config.
2. **Schema Validation:** Assert that the generated configuration dictionaries conform exactly to the known schemas of Zed, Cline, and Windsurf.
3. **CLI Integration:** Invoke the CLI runner programmatically with `--target zed` and verify it calls the correct exporter class.

### 5. Live Acceptance Test Plan
Create a dummy `zed_config.jsonc` file with comments. Run `uv run mcp-fingerprints export-config --target zed --config zed_config.jsonc --server my-server`. Open the file manually to verify comments are untouched and the new server is appended properly.

---

## 28. Web Catalog Offline PWA & Search Virtualization
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAYXwo`
- **Category**: Web & Frontend
- **Status**: Backlog

### 1. Architectural Context & Technical Objective
The static web catalog (`web/`) is currently a basic vanilla JS implementation. As the catalog grows to hundreds or thousands of fingerprints, DOM rendering can become slow. Furthermore, offline access is not supported.
The objective is to implement a Progressive Web App (PWA) Service Worker to cache the static catalog for offline use and implement DOM virtualization (windowing) for the search results list to maintain sub-16ms rendering performance even with 10,000+ entries, adhering strictly to vanilla JS without external frameworks.

### 2. Technical Implementation Specifications
1. Create `web/sw.js` (Service Worker) to cache `index.html`, `app.js`, CSS, and the JSON catalog snapshot.
2. Update `web/index.html` to register the Service Worker.
3. Modify `web/app.js` to implement list virtualization:
   - Calculate total height based on item count.
   - Render only the subset of list items visible in the viewport plus a small buffer.
   - Use absolute positioning within a scrollable container.
4. Ensure the `scripts/generate_web_catalog.py` includes a mechanism to inject the current cache version into `sw.js` to trigger updates.

### 3. Clear Acceptance Criteria
- [ ] Service worker (`sw.js`) successfully caches the web catalog.
- [ ] The web catalog is accessible offline.
- [ ] `app.js` utilizes DOM virtualization for search results.
- [ ] Vanilla JS is maintained; no React/Vue/Svelte dependencies.

### 4. Unit Test Plan
1. **Virtualization Logic:** Unit test the index calculation functions (e.g., `getVisibleRange(scrollTop, containerHeight, itemHeight)`) in a standard JS test runner (or via Playwright evaluating functions) to ensure accurate start and end indices are returned.
2. **Service Worker Versioning:** Test that `generate_web_catalog.py` correctly updates the cache version string in `sw.js` when generating the site.

### 5. Live Acceptance Test Plan
Use `uv run python scripts/generate_web_catalog.py`. Start a local HTTP server (`python -m http.server -d web`). Open the browser, verify virtualization by inspecting the DOM (only a few elements should exist). Disconnect the server (stop script), refresh the page, and verify it still loads offline via the Service Worker. Finally, use Playwright frontend verification instructions to capture a screenshot of the catalog rendering correctly.

---

## 29. True Isolated Container Sandbox with Dual Support for BOTH Docker and Incus (`--probe-runtime --sandbox=[auto|docker|incus|incus-vm|host]`)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAYXzE`
- **Category**: Security & Sandboxing
- **Status**: Backlog

### 1. Architectural Context & Technical Objective
While `mcp_fingerprints` extracts static AST data efficiently, the current runtime probe (`probe` command) executes servers directly via `stdio` using standard library `subprocess`. Even with environment sanitization, running untrusted or closed-source MCP server binaries directly on the host poses significant security risks.
The objective is to implement a true isolated container sandbox using Docker and Incus for runtime probing. When `--sandbox=[auto|docker|incus|incus-vm|host]` is specified (default `auto`), the engine will dynamically construct an ephemeral container (or microVM), map only the necessary stdio pipes, execute the server, and immediately destroy the container.

### 2. Technical Implementation Specifications
1. Create `src/mcp_fingerprints/sandbox_drivers.py`.
2. Implement a `BaseSandboxRunner` abstract base class with `run_handshake(command: list[str], timeout: float = 5.0, env: dict[str, str] | None = None) -> list[dict[str, Any]]`.
3. Implement `DockerSandboxRunner` that invokes the `docker` CLI directly via `subprocess`. Example command: `docker run -i --rm --network none --memory 512m <image> <cmd>`. Validate with `shutil.which("docker")`.
4. Implement `IncusSandboxRunner` that invokes `incus`. Example command: `incus launch docker:<image> <instance_name> --ephemeral -c limits.memory=512MB -c limits.cpu=1` and `incus exec <instance_name> -- <command>`. Support microVM with `--vm`. Validate with `shutil.which("incus")`.
5. Implement `HostSandboxRunner` executing via sanitized host stdio.
6. Implement `AutoSandboxRunner` which falls back from incus -> docker -> host.
7. Update CLI `probe` and `sync` commands to accept `--sandbox=[auto|docker|incus|incus-vm|host]`.

### 3. Clear Acceptance Criteria
- [ ] `DockerSandboxRunner` is implemented via standard `subprocess` calling the `docker` executable.
- [ ] `IncusSandboxRunner` is implemented for container and microVM execution.
- [ ] Container runs without network access (`--network none`).
- [ ] CLI supports `--sandbox=[auto|docker|incus|incus-vm|host]`.
- [ ] Fallback to `host` runner if docker is missing or requested.
- [ ] Auto-detection logic (prefers Incus/Docker when present, falls back gracefully to host).
- [ ] Fallback to `host` runner if docker is missing or requested.

### 4. Unit Test Plan
1. **Command Generation:** Unit test that `DockerSandboxRunner` generates the exact expected `docker run` command string, specifically asserting the presence of `-i`, `--rm`, and `--network none`.
2. **Missing Docker CLI:** Mock `shutil.which('docker')` to return `None` and assert the runner raises an appropriate environment error.
3. **Timeout Handling:** Mock `subprocess.Popen` to simulate a timeout and verify the runner forcibly kills the docker process.

### 5. Live Acceptance Test Plan
Ensure Docker is running locally. Run `uv run mcp-fingerprints probe --sandbox=docker <test-server-image>`. Verify the probe successfully extracts tools and cleanly exits. Verify via `docker ps` that no lingering containers remain.

---

## 30. SARIF Export for GitHub Code Scanning (`audit-config --format sarif`)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAYX1U`
- **Category**: Integration & Ecosystem
- **Status**: Backlog

### 1. Architectural Context & Technical Objective
The current configuration auditing (`audit-config`) command provides basic JSON or terminal output. To seamlessly integrate `mcp_fingerprints` into enterprise CI/CD pipelines and vulnerability management workflows (like GitHub Advanced Security Code Scanning), it needs to export structural risk findings in the standard SARIF (Static Analysis Results Interchange Format) format.
The objective is to implement a SARIF v2.1.0 exporter that translates the static AST tool capability risk profiles (e.g., exposed shell execution tools) into SARIF rules and results. Note: As per Clean Architecture, this export is strictly for *structural risks* found via AST, not external CVE vulnerabilities.

### 2. Technical Implementation Specifications
1. Create `src/mcp_fingerprints/sarif_exporter.py`.
2. Define the basic structural SARIF schema dictionaries (Rules, Results, Runs) adhering to the SARIF v2.1.0 specification.
3. Map internal static risk profiles (e.g., `ToolCapabilityRisk`) to SARIF `rules`.
4. Update `src/mcp_fingerprints/cli.py` `audit-config` command to support `--format sarif`.
5. Ensure zero external dependencies (no heavy schema validation libraries) are required for generation.

### 3. Clear Acceptance Criteria
- [ ] SARIF v2.1.0 generator implemented using plain python dictionaries.
- [ ] `audit-config` CLI command supports `--format sarif`.
- [ ] Output is valid JSON.
- [ ] Outputs only structural risks, adhering to Clean Architecture.

### 4. Unit Test Plan
1. **Schema Structure:** Generate a SARIF output from a mock audit result and assert the presence of required root keys (`version`, `$schema`, `runs`).
2. **Rule Mapping:** Assert that a specific `ToolCapabilityRisk` is correctly mapped to a `result` object referencing the correct `ruleId`.
3. **Empty Results:** Test that an audit with zero risks produces a valid SARIF file with an empty `results` array.

### 5. Live Acceptance Test Plan
Run `uv run mcp-fingerprints audit-config --config my_config.json --format sarif > out.sarif`. Open `out.sarif` and manually verify it is valid JSON and follows the expected structure. Optionally, attempt to upload the file to a GitHub repository's Code Scanning interface to verify compatibility natively.

---

## 31. MCP Server Software Bill of Materials (SBOM / CycloneDX)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAYX3s`
- **Category**: Integration & Ecosystem
- **Status**: Backlog

### 1. Architectural Context & Technical Objective
While `mcp_fingerprints` tracks the structural layout of MCP servers via passports, it does not currently generate standard Software Bill of Materials (SBOMs) for the servers themselves.
The objective is to implement an SBOM generation module that exports an MCP server's structural metadata and tool lists into the CycloneDX 1.5 JSON specification. This allows the structural data extracted by `mcp-fingerprints` to be easily ingested by standard enterprise supply chain tooling without blurring the lines into active vulnerability scanning.

### 2. Technical Implementation Specifications
1. Create `src/mcp_fingerprints/sbom.py`.
2. Map `ServerPackageSpec` and `VersionFingerprint` data to a CycloneDX 1.5 JSON structure.
   - Component type: `application`.
   - Include tools as nested components or properties.
3. Add a new CLI command `mcp-fingerprints sbom <package_name> --format cyclonedx`.
4. Ensure generation relies only on standard Python dictionaries and standard library `json`.

### 3. Clear Acceptance Criteria
- [ ] `src/mcp_fingerprints/sbom.py` generates valid CycloneDX 1.5 JSON dictionaries.
- [ ] CLI `sbom` command implemented.
- [ ] Structural data correctly mapped to CycloneDX components.

### 4. Unit Test Plan
1. **Spec Generation:** Pass a mocked `ServerPackageSpec` to the generator. Assert the output dict contains `bomFormat: "CycloneDX"` and `specVersion: "1.5"`.
2. **Component Mapping:** Assert that the primary package name and version are correctly mapped to the main component's `name` and `version` fields.
3. **PURL Validation:** Ensure the package's PURL is correctly injected into the component `purl` field.

### 5. Live Acceptance Test Plan
Run `uv run mcp-fingerprints sbom my-mcp-server --format cyclonedx > sbom.json`. Manually inspect `sbom.json` to ensure the format is valid JSON and structurally resembles standard CycloneDX format for the specified server.

---

## 32. Strict JSON-RPC 2.0 & MCP Protocol Conformance Validator
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhAYX6A`
- **Category**: Validation & Conformance
- **Status**: Backlog

### 1. Architectural Context & Technical Objective
The Model Context Protocol operates over JSON-RPC 2.0 via `stdio` or HTTP/SSE. Currently, `mcp_fingerprints` assumes servers behave correctly during extraction or probing.
The objective is to implement a strict protocol conformance validator tool (`validate-protocol`) that actively probes a running server and asserts its responses adhere perfectly to the JSON-RPC 2.0 specification (e.g., correct `jsonrpc` version string, proper handling of `id`, valid `error` object structures) and the specific MCP initialization handshake sequence.

### 2. Technical Implementation Specifications
1. Create `src/mcp_fingerprints/protocol_validator.py`.
2. Implement specific test suites for JSON-RPC 2.0 compliance:
   - Missing `jsonrpc: "2.0"` field.
   - Malformed `id` reflection.
   - Structured Error handling (Code, Message).
3. Implement specific test suites for MCP compliance:
   - Proper `initialize` request and response structure.
   - Proper `notifications/initialized` sequence.
4. Update the CLI with a `validate-protocol` command.

### 3. Clear Acceptance Criteria
- [ ] Protocol validation test suites implemented for JSON-RPC 2.0 and MCP handshake.
- [ ] CLI command `validate-protocol` exists.
- [ ] Validator detects missing `jsonrpc` fields and malformed errors.
- [ ] Zero reliance on heavy third-party JSON schema libraries.

### 4. Unit Test Plan
1. **Valid Sequence:** Provide a mock sequence of valid JSON-RPC strings representing a perfect initialization handshake. Assert the validator returns success.
2. **Missing jsonrpc Field:** Provide a mock response missing `"jsonrpc": "2.0"`. Assert the validator flags a strict JSON-RPC 2.0 violation.
3. **Invalid Error Object:** Provide an error response missing the `code` integer field. Assert the validator flags an invalid error object structure.

### 5. Live Acceptance Test Plan
Use `uv run mcp-fingerprints validate-protocol <path-to-test-server-binary>`. The command should spawn the server, perform the handshake, deliberately send a malformed request, and verify the server's error response compliance, printing a pass/fail report to stdout.

### 5. Live Acceptance Test Plan
Ensure Docker is running locally. Run `uv run mcp-fingerprints probe --sandbox=docker <test-server-image>`. Verify the probe successfully extracts tools and cleanly exits. Verify via `docker ps` that no lingering containers remain.

---

## 33. Pure Structural Models, ParameterMetadata & Protocol Annotations Schema
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBPoPQ`
- **Category**: Schema & Core Models
- **Status**: Done

### 1. Architectural Context & Technical Objective
Define high-fidelity, pure structural data models representing MCP tools, parameters, resources, prompts, and protocol annotations without any security or vulnerability fields. Expand `src/mcp_fingerprints/models.py` to introduce `ParameterMetadata` (parameter name, JSON Schema type, description, required boolean, default value, enum values, nested properties/items), `PromptDefinition` (name, description, arguments), `ResourceDefinition` (uri, name, mimeType, description), and `ProtocolAnnotations` (readOnly, destructive, idempotency, streaming). Purge any residual security attributes (`threat_score`, `risk_level`, `cve_refs`) from the core fingerprint models to enforce Clean Architecture ecosystem boundaries. Update `schemas/fingerprint_v1.json` and ensure full bidirectional serialization/deserialization.

### 2. Target Files & Documentation to Update
- `src/mcp_fingerprints/models.py`
- `src/mcp_fingerprints/schema_validator.py`
- `schemas/fingerprint_v1.json`
- `tests/test_models.py`
- `docs/schema_specification.md`
- `README.md`

### 3. EULIS Implementation & Branch Review Workflow
- Branch: `jules/review-task33`
- Implementation PR: `jules-gate pr --skip-ci`
- Offload Mode 2 EULIS Code Review: `jules-gate review-branch`
- Review verification: check `docs/reviews/review_task33.md`
- Test verification: run test suite via isolated subagent (`jules-gate verify`)
- Merge: `jules-gate pr-merge --skip-ci`

### 4. Clear Acceptance Criteria
- [x] Structural models (`ParameterMetadata`, `PromptDefinition`, `ResourceDefinition`, `ProtocolAnnotations`) implemented in `models.py`.
- [x] All residual security attributes (`risk_score`, `threat_level`, `cve_refs`) purged from structural models.
- [x] `schemas/fingerprint_v1.json` updated with pure structural schema definitions and validated against standard draft-07 / 2020-12 meta-schemas.
- [x] Bidirectional JSON serialization and deserialization roundtrip tests pass in `tests/test_models.py`.
- [x] Schema validator in `schema_validator.py` validates new structural models with zero regressions.
- [x] Documentation updated in `docs/schema_specification.md` and `README.md`.


---

## 34. Deep Python & TS/JS AST Parameter, Prompt, Resource & Env Extractor
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBPoTI`
- **Category**: AST & Introspection Engine
- **Status**: Done

### 1. Architectural Context & Technical Objective
Deepen the static AST extraction engine (`src/mcp_fingerprints/ast_parser.py` and `doc_parser.py`) for both Python and TypeScript/JavaScript MCP server implementations. For Python, inspect AST nodes of `@mcp.tool()` or `FastMCP.tool` functions to extract type annotations, default parameter values, docstrings (Sphinx, Google, NumPy styles), prompt definitions (`@mcp.prompt()`), static resources (`@mcp.resource()`), and accessed environment variables (`os.environ`, `os.getenv`). For TypeScript/JavaScript, parse `server.tool(...)`, `McpServer`, and Zod schema objects (`z.object({...})`) to extract detailed parameter types, descriptions, `.optional()`, `.default(...)`, and `process.env` references.

### 2. Target Files & Documentation to Update
- `src/mcp_fingerprints/ast_parser.py`
- `src/mcp_fingerprints/doc_parser.py`
- `tests/test_ast_parser.py`
- `tests/fixtures/python_servers/`
- `tests/fixtures/ts_servers/`
- `docs/ast_extraction_guide.md`

### 3. EULIS Implementation & Branch Review Workflow
- Branch: `jules/review-task34`
- Implementation PR: `jules-gate pr --skip-ci`
- Offload Mode 2 EULIS Code Review: `jules-gate review-branch`
- Review verification: check `docs/reviews/review_task34.md`
- Test verification: run test suite via isolated subagent (`jules-gate verify`)
- Merge: `jules-gate pr-merge --skip-ci`

### 4. Clear Acceptance Criteria
- [x] Python AST parser extracts parameter type hints, default values, and required constraints from tool definitions.
- [x] Docstring parser extracts per-parameter descriptions across Google, Sphinx, and NumPy docstring conventions.
- [x] Prompt templates (`@mcp.prompt()`) and Resource definitions (`@mcp.resource()`) extracted into `PromptDefinition` and `ResourceDefinition`.
- [x] Environment variable accesses (`os.environ`, `os.getenv`, `process.env`) detected and recorded in `required_env_vars`.
- [x] TypeScript/JavaScript AST parser extracts Zod schemas and tool parameters from `McpServer` and `server.tool`.
- [x] 100% test pass on sample Python and TS fixtures in `tests/test_ast_parser.py`.


---

## 35. Multi-File Registry & Tarball Synchronizer Enrichment
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBPoW8`
- **Category**: Ingestion & Package Discovery
- **Status**: Done

### 1. Architectural Context & Technical Objective
Enhance repository synchronizer and package ingestion engine (`src/mcp_fingerprints/synchronizer.py`, `ingestion_engine.py`, `monorepo_prober.py`) to support distributed, multi-file server packages and tarball unpacking. When analyzing npm `.tgz` or PyPI `.tar.gz`/`.whl` archives, safely unpack them into an ephemeral sandboxed directory with zip-slip path traversal guards. Traverse multi-file module import hierarchies (following relative imports and barrel exports like `index.ts` / `__init__.py`) to discover tools, prompts, and resources split across multiple source files or nested subpackages.

### 2. Target Files & Documentation to Update
- `src/mcp_fingerprints/synchronizer.py`
- `src/mcp_fingerprints/ingestion_engine.py`
- `src/mcp_fingerprints/monorepo_prober.py`
- `tests/test_synchronizer.py`
- `tests/test_monorepo_prober.py`
- `docs/synchronization_pipeline.md`

### 3. EULIS Implementation & Branch Review Workflow
- Branch: `jules/review-task35`
- Implementation PR: `jules-gate pr --skip-ci`
- Offload Mode 2 EULIS Code Review: `jules-gate review-branch`
- Review verification: check `docs/reviews/review_task35.md`
- Test verification: run test suite via isolated subagent (`jules-gate verify`)
- Merge: `jules-gate pr-merge --skip-ci`

### 4. Clear Acceptance Criteria
- [x] Safe in-memory/ephemeral tarball and wheel unpacker with zip-slip path traversal (`..`) prevention.
- [x] Multi-file AST walker traverses internal module imports to discover tools declared across helper files.
- [x] Monorepo package prober isolates sub-projects within pnpm/npm/lerna workspaces without cross-contamination.
- [x] Synchronizer successfully extracts complete multi-file tool catalogs from sample npm and PyPI tarball packages.
- [x] Comprehensive unit tests in `tests/test_synchronizer.py` and `tests/test_monorepo_prober.py`.


---

## 36. Security Module Purge & Pure Structural CLI/TUI Refactoring
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBPoak`
- **Category**: CLI & Architecture Governance
- **Status**: Done

### 1. Architectural Context & Technical Objective
Purge residual security and vulnerability scanning modules (`security_classifier.py`, `sarif_exporter.py`, etc., which are being migrated to `mcp-vulnerabilities`). Refactor the CLI (`src/mcp_fingerprints/cli.py`) and TUI (`src/mcp_fingerprints/tui.py`) to concentrate solely on pure structural MCP passport introspection, schema inspection, AST diffing, protocol validation, and registry browsing. Remove `--audit-risk`, `--sarif`, and CVE search commands, replacing them with deprecation notices directing users to `mcp-vulnerabilities`.

### 2. Target Files & Documentation to Update
- `src/mcp_fingerprints/cli.py`
- `src/mcp_fingerprints/tui.py`
- `src/mcp_fingerprints/security_classifier.py (purged/deprecated)`
- `src/mcp_fingerprints/sarif_exporter.py (purged/deprecated)`
- `tests/test_cli.py`
- `tests/test_tui.py`
- `docs/cli_reference.md`
- `README.md`

### 3. EULIS Implementation & Branch Review Workflow
- Branch: `jules/review-task36`
- Implementation PR: `jules-gate pr --skip-ci`
- Offload Mode 2 EULIS Code Review: `jules-gate review-branch`
- Review verification: check `docs/reviews/review_task36.md`
- Test verification: run test suite via isolated subagent (`jules-gate verify`)
- Merge: `jules-gate pr-merge --skip-ci`

### 4. Clear Acceptance Criteria
- [x] Deprecated security classification and SARIF modules removed or replaced with clear migration warnings pointing to `mcp-vulnerabilities`.
- [x] CLI commands (`inspect`, `diff`, `schema`, `validate-protocol`, `browse`) refactored for pure structural analysis.
- [x] TUI terminal browser renders rich parameter tables, prompt arguments, and resource trees without security ratings.
- [x] Unit tests in `tests/test_cli.py` and `tests/test_tui.py` updated and 100% passing.
- [x] Documentation updated in `docs/cli_reference.md` and `README.md`.


---

## 37. Enriched Non-Security Web Catalog & Interactive Parameter Inspector UI
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBPodc`
- **Category**: Static Web Directory
- **Status**: Done

### 1. Architectural Context & Technical Objective
Overhaul the static web catalog (`web/index.html`, `web/app.js`, `web/style.css`, `web/catalog.json`) to showcase enriched structural metadata. Implement an interactive tool parameter inspector drawer/modal in the browser that allows users to drill down into any server, view full JSON Schema parameter definitions, types, required flags, default values, docstrings, prompt templates, and resource endpoints. Strip all vulnerability scores, CVE badges, and threat filters from the catalog UI. Optimize `src/mcp_fingerprints/snapshot.py` to compile an efficient, non-bloated `catalog.json`.

### 2. Target Files & Documentation to Update
- `web/index.html`
- `web/app.js`
- `web/style.css`
- `src/mcp_fingerprints/snapshot.py`
- `tests/test_web_catalog.py`
- `docs/web_catalog.md`

### 3. EULIS Implementation & Branch Review Workflow
- Branch: `jules/review-task37`
- Implementation PR: `jules-gate pr --skip-ci`
- Offload Mode 2 EULIS Code Review: `jules-gate review-branch`
- Review verification: check `docs/reviews/review_task37.md`
- Test verification: run test suite via isolated subagent (`jules-gate verify`)
- Merge: `jules-gate pr-merge --skip-ci`

### 4. Clear Acceptance Criteria
- [x] Interactive tool parameter inspector drawer/modal implemented with clean responsive CSS.
- [x] Parameter type badges, required indicators, default values, and docstrings rendered clearly.
- [x] Prompt templates and resource URIs displayed in dedicated tabs or expandable accordions.
- [x] All security risk badges, CVE indicators, and vulnerability filters removed from the UI.
- [x] `snapshot.py` generates minified, high-performance `catalog.json` for 5,000+ servers.
- [x] Browser search, filtering, and copy client configuration snippets verified functional.


---

## 38. Passport Dataset Sanitization, Sync-State Reset & Documentation Purification
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBPogo`
- **Category**: Data Governance & Operations
- **Status**: Done

### 1. Architectural Context & Technical Objective
Sanitize the existing passport dataset in `data/` by writing an automated migration script (`scripts/sanitize_passports.py`) that strips all legacy security fields, risk scores, and vulnerability annotations, ensuring every passport strictly conforms to the pure structural schema. Cleanly reset the sync tracking state (`data/sync_state.json`) to allow a fresh, idempotent re-sync. Purify all repository documentation, architectural diagrams, and README files to firmly establish `mcp-fingerprints` as the canonical structural source of truth.

### 2. Target Files & Documentation to Update
- `data/ (passport JSON files)`
- `scripts/sanitize_passports.py`
- `data/sync_state.json`
- `src/mcp_fingerprints/partitioner.py`
- `docs/architecture.md`
- `docs/dataset_spec.md`
- `README.md`

### 3. EULIS Implementation & Branch Review Workflow
- Branch: `jules/review-task38`
- Implementation PR: `jules-gate pr --skip-ci`
- Offload Mode 2 EULIS Code Review: `jules-gate review-branch`
- Review verification: check `docs/reviews/review_task38.md`
- Test verification: run test suite via isolated subagent (`jules-gate verify`)
- Merge: `jules-gate pr-merge --skip-ci`

### 4. Clear Acceptance Criteria
- [x] Automated migration script `scripts/sanitize_passports.py` created and tested.
- [x] All passport records in `data/` sanitized, with 0 legacy security fields remaining.
- [x] `sync_state.json` cleanly reset to trigger idempotent structural re-sync.
- [x] All sanitized passports validate against `schemas/fingerprint_v1.json` via `schema_validator.py`.
- [x] Architecture diagrams and documentation in `docs/` and `README.md` purified.


---

## 39. Sync Update Delta Tracker, What's New Web Page (web/updates.html) & PyPI Auto-Release Hardening
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBPokY`
- **Category**: Ingestion & Release Engineering
- **Status**: Done

### 1. Architectural Context & Technical Objective
Implement an automated sync update delta tracker (`src/mcp_fingerprints/delta_tracker.py`) that executes at the conclusion of daily ingestion cycles. It detects newly discovered MCP servers, version upgrades, new tools, and modified parameter signatures, saving the results in a rolling history log (`data/updates_history.json`). Create a dedicated static 'What's New' page (`web/updates.html` + `web/updates.js`) providing an ecosystem change feed. Harden `.github/workflows/daily_sync.yml` and `.github/workflows/release.yml` to automatically trigger a PyPI release when substantive fingerprint updates exceed release thresholds.

### 2. Target Files & Documentation to Update
- `src/mcp_fingerprints/delta_tracker.py`
- `web/updates.html`
- `web/updates.js`
- `.github/workflows/daily_sync.yml`
- `.github/workflows/release.yml`
- `tests/test_delta_tracker.py`
- `docs/releases_and_updates.md`

### 3. EULIS Implementation & Branch Review Workflow
- Branch: `jules/review-task39`
- Implementation PR: `jules-gate pr --skip-ci`
- Offload Mode 2 EULIS Code Review: `jules-gate review-branch`
- Review verification: check `docs/reviews/review_task39.md`
- Test verification: run test suite via isolated subagent (`jules-gate verify`)
- Merge: `jules-gate pr-merge --skip-ci`

### 4. Clear Acceptance Criteria
- [x] `DeltaTracker` accurately computes additions, version bumps, and signature changes between sync runs.
- [x] `data/updates_history.json` tracks chronological delta records with timestamps and commit hashes.
- [x] `web/updates.html` presents a responsive timeline of ecosystem arrivals with filtering and search.
- [x] Daily sync workflow commits update logs and conditionally triggers PyPI release pipeline.
- [x] Unit tests in `tests/test_delta_tracker.py` pass with 100% coverage.


---

## 43. Local Machine MCP Config Discovery & Interactive Inventory (`scan-configs`)
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBf5xA`
- **Draft Issue ID**: `DI_lAHOD-xmQM4BmPbTzgLZvts`
- **Category**: Discovery & Client Workflows
- **Status**: Todo

### 1. Architectural Context & Technical Objective
Implement automated configuration discovery (`src/mcp_fingerprints/config_scanner.py`) across local developer workstations. Traverses standard OS and client paths (Claude Desktop, Cursor global `~/.cursor/mcp.json`, project-level `.cursor/mcp.json`, Windsurf, Zed, Cline) to parse declared MCP servers. Connects to and probes active servers via `stdio` or HTTP/SSE, extracts runtime schemas, matches them against the passport knowledge base, and outputs both a clean terminal summary table and a structured JSON schema inventory.

### 2. Concrete Real-World Problem & Workflow
- **The Problem**: A developer or security specialist has dozens of MCP servers configured across several IDEs and repositories. They have lost track of which tools are active, what capabilities are exposed, and where they were downloaded from.
- **What it Finds**: Discovers all declared servers, extracts their live tool contracts, identifies their official package names/versions, and flags unindexed custom servers.
- **How it Solves It**: Provides a single one-line audit (`mcp-fingerprints scan-configs --auto`) to inventory all local MCP assets instantly.

### 3. Target Files & Documentation to Update
- `src/mcp_fingerprints/config_scanner.py`
- `src/mcp_fingerprints/cli.py`
- `src/mcp_fingerprints/__init__.py`
- `tests/test_config_scanner.py`
- `README.md`
- `docs/tasks/task_43_local_mcp_config_discovery_and_inventory.md`

### 4. Clear Acceptance Criteria
- [ ] Resolves standard config locations for Claude Desktop, Cursor (global + project), and Windsurf across macOS/Linux/Windows.
- [ ] Probes live servers and extracts runtime tool contracts.
- [ ] Matches servers against passport database (`passports.json.gz`).
- [ ] CLI command `scan-configs` outputs formatted terminal table and optional JSON export.
- [ ] Unit tests pass with 100% coverage.

---

## 44. Stateful Inventory Snapshot & Differential Drift Tracker
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBf5yM`
- **Draft Issue ID**: `DI_lAHOD-xmQM4BmPbTzgLZvtw`
- **Category**: Asset Integrity & Governance
- **Status**: Todo

### 1. Architectural Context & Technical Objective
Implement stateful snapshot persistence and differential comparison (`src/mcp_fingerprints/snapshot_diff.py`). Persists the determined local machine schema inventory to a versioned snapshot file (e.g. `mcp-inventory.json`) and compares subsequent scans against this baseline to report newly added servers, uninstalled servers, and mutated/drifted tool schemas or package versions.

### 2. Concrete Real-World Problem & Workflow
- **The Problem**: Over time, local or repository MCP configurations change silently: a git pull introduces a new MCP server, or an auto-updated npm package alters a tool parameter or adds dangerous capabilities without notice.
- **What it Finds**: Detects additions (`+`), removals (`-`), and contract mutations (drifted parameter types, added parameters, altered descriptions) between runs.
- **How it Solves It**: Enables pre-commit hooks or local audits (`mcp-fingerprints scan-configs --compare-snapshot baseline.json --fail-on-drift`) to prevent untracked MCP drift.

### 3. Target Files & Documentation to Update
- `src/mcp_fingerprints/snapshot_diff.py`
- `src/mcp_fingerprints/cli.py`
- `src/mcp_fingerprints/__init__.py`
- `tests/test_snapshot_diff.py`
- `README.md`
- `docs/tasks/task_44_stateful_inventory_snapshot_and_drift_tracker.md`

### 4. Clear Acceptance Criteria
- [ ] `InventorySnapshot` serializes and deserializes local inventory schemas to versioned JSON.
- [ ] `InventoryDiffer` cleanly surfaces added, removed, and modified servers.
- [ ] Parametric mutations (added parameters, type changes) are surfaced with exact diffs.
- [ ] `--fail-on-drift` flag properly returns exit code 2 when drift is detected.
- [ ] Comprehensive unit tests pass in `tests/test_snapshot_diff.py`.

---

## 45. Dual-Transport Live Prober & Public Python Library SDK
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBf5zM`
- **Draft Issue ID**: `DI_lAHOD-xmQM4BmPbTzgLZvt0`
- **Category**: Core Engine & SDK Integration
- **Status**: Todo

### 1. Architectural Context & Technical Objective
Implement native HTTP/SSE and Streamable HTTP probing (`McpHttpProber` in `src/mcp_fingerprints/prober.py`) using Python's standard library (`urllib.request` / `http.client`) with zero heavy networking dependencies. Unify `stdio` and `http` probing under a single interface and expose a public Python SDK (`identify_stdio`, `identify_http`, `McpIdentifier`) in `mcp_fingerprints/__init__.py` for seamless embedding into AI gateways, proxies, and automation harnesses.

### 2. Concrete Real-World Problem & Workflow
- **The Problem**: AI gateways (Cloudflare, Portkey, Envoy) and agent harnesses need to identify and verify MCP servers over both local process pipes and remote URLs before routing agent tool requests, without spawning shell CLI commands or pulling in heavy dependencies.
- **What it Finds**: Queries remote HTTP/SSE endpoints, extracts tool signatures, and matches against the 5,058+ passport index in < 15ms.
- **How it Solves It**: Provides a clean 3-line Python importable SDK with zero added dependencies.

### 3. Target Files & Documentation to Update
- `src/mcp_fingerprints/prober.py`
- `src/mcp_fingerprints/__init__.py`
- `src/mcp_fingerprints/cli.py`
- `tests/test_http_prober.py`
- `README.md`
- `docs/tasks/task_45_dual_transport_prober_and_python_sdk.md`

### 4. Clear Acceptance Criteria
- [ ] `McpHttpProber` handles both Streamable HTTP JSON-RPC and SSE streams without third-party dependencies.
- [ ] Authenticated endpoints supported via custom request headers.
- [ ] Top-level `mcp_fingerprints` exports `identify_stdio`, `identify_http`, and `McpIdentifier`.
- [ ] CLI `probe` command seamlessly handles both `--url` and stdio commands.
- [ ] Unit tests pass in `tests/test_http_prober.py`.

---

## 46. Attribution Enrichment & Multi-Format Reporting
- **Board Item ID**: `PVTI_lAHOD-xmQM4BmPbTzhBf50E`
- **Draft Issue ID**: `DI_lAHOD-xmQM4BmPbTzgLZvt8`
- **Category**: User Experience & Reporting
- **Status**: Todo

### 1. Architectural Context & Technical Objective
Enrich `ProbeReport` with actionable package metadata from `ServerPackageSpec` (repository URLs, official download/install commands, maintainers, latest registry versions). Implement flexible output formatting across CLI commands: `--format short` (1-to-3 line compact summary for CI / prompt alerts), `--format long` (full schema & drift report), `--format table`, and `--format json`.

### 2. Concrete Real-World Problem & Workflow
- **The Problem**: A user probes an unknown MCP command; the tool identifies the package name, but doesn't tell them where the official repository is, how to install it in another client, or whether it's up to date. In CI pipelines, multiline reports clutter the logs.
- **What it Finds**: Links matches back to the rich passport spec, generating canonical install commands (`npx -y ...`, `pip install ...`) and comparing observed version vs latest registry release.
- **How it Solves It**: Provides immediate actionable download/repository links and adapts verbosity cleanly (`--format short` vs `--format long`).

### 3. Target Files & Documentation to Update
- `src/mcp_fingerprints/models.py`
- `src/mcp_fingerprints/reporter.py`
- `src/mcp_fingerprints/cli.py`
- `tests/test_reporter.py`
- `README.md`
- `docs/tasks/task_46_enriched_attribution_and_multi_format_reporting.md`

### 4. Clear Acceptance Criteria
- [ ] `ProbeReport` populates `repository_url`, `install_command`, and `latest_version` from passport specs.
- [ ] `--format short` outputs clean 3-line terminal summary.
- [ ] `--format long` provides complete tool schemas and protocol annotations.
- [ ] `--format table` formats clean ASCII tables of capabilities.
- [ ] Unit tests in `tests/test_reporter.py` pass.
