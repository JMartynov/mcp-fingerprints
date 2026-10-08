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
- [ ] GitHub Pages source is configured to GitHub Actions for `JMartynov/mcp-fingerprints`.
- [ ] Workflow `.github/workflows/deploy_pages.yml` completes with green status on GitHub Actions.
- [ ] `https://jmartynov.github.io/mcp-fingerprints/` returns HTTP 200 with 5,031+ searchable MCP servers.
- [ ] `deploy_pages.yml` triggers automatically after daily sync updates.

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
- [ ] `python -m build` builds clean sdist (`.tar.gz`) and wheel (`.whl`) without errors.
- [ ] `twine check dist/*` passes with `PASSED`.
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
- [ ] `.pre-commit-config.yaml` is present in the repository root.
- [ ] `pre-commit run --all-files` runs cleanly across all files in the repository.
- [ ] Modifying a fixture MCP config triggers `mcp-audit-config` verification.
- [ ] `README.md` includes clear instructions for setting up pre-commit.
- [ ] All unit tests pass.

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
- [ ] `.github/workflows/test_action.yml` created and passing on GitHub Actions.
- [ ] Composite action `uses: ./` tested for both passing and collision-failing scenarios.
- [ ] Action execution time is fast (<1 minute on Ubuntu latest).
- [ ] Usage instructions in `README.md` verified.

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
- [ ] `mcp-fingerprints resolve-config --help` exposes strategy options and output paths.
- [ ] Colliding tools are successfully identified and disambiguated.
- [ ] Non-conflicting server definitions and arguments are preserved with 100% fidelity.
- [ ] Full unit test coverage in `tests/test_conflict_resolver.py` without regressions.

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
- [ ] Users can select multiple servers across search queries without losing selections.
- [ ] Multi-server builder generates valid JSON for Claude, Cursor, Cline, Zed, and Windsurf.
- [ ] Duplicate tool names across selected servers trigger a clear warning in the builder UI.
- [ ] 1-click clipboard copy and file download function without browser errors.

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
- [ ] `.github/workflows/daily_sync.yml` runs `detect-drift` on every scheduled execution.
- [ ] Drift summary is published to GitHub Step Summary.
- [ ] Critical tampering triggers automated notifications/issues.
- [ ] CI pipeline test suite passes without regressions.

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
- [ ] `mcp-fingerprints search 'read spreadsheet' --semantic` identifies spreadsheet tools despite lexical divergence.
- [ ] Core package remains zero-bloat; `fastembed` is an optional extra.
- [ ] Graceful fallback to lexical search occurs cleanly when semantic dependencies are omitted.
- [ ] Full unit test coverage in `tests/test_semantic_search.py`.
