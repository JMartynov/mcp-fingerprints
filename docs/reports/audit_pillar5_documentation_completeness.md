# Pillar 5 Audit: Documentation Completeness & Architecture Alignment

## 1. CLI & Python SDK: `docs/SPECIFICATION.md` & `README.md` vs Code

### Discrepancies and Undocumented Features
- The `export-sbom` command is documented in several secondary reports and task files but is entirely missing from the main CLI documentation sections of `docs/SPECIFICATION.md` and `docs/README.md`.
- The `build-index` command exists in `cli.py` and `__init__.py` but is undocumented.
- The `detect-drift` command is mentioned briefly in the context of task reports but not explicitly defined in the main CLI specifications.
- The `scan-configs` (and alias `scan`) command is implemented in `cli.py` and exported in `__init__.py` (as `scan_local_configs` / `scan_config_file`) but is undocumented in `docs/SPECIFICATION.md` and `docs/README.md`.
- The `validate-protocol` command exists in `cli.py` but is missing from the main documentation.
- The `init` command is present in `cli.py` but missing from the main documentation.
- The `export-config` command is present in `cli.py` but missing from the main documentation.

### Recommended Update Tasks
- **Task**: Update `docs/SPECIFICATION.md` and `docs/README.md` to include all currently supported CLI commands: `init`, `export-sbom`, `build-index`, `detect-drift`, `scan-configs` (and `scan`), `validate-protocol`, and `export-config`.
- **Task**: Update SDK documentation in `docs/SPECIFICATION.md` and `docs/README.md` to document the exported Python functions: `scan_local_configs`, `scan_config_file`, and `McpIdentifier` class functionality.

## 2. Data Model & Schema: Passport JSON Format vs Canonicalizer/Models

### Discrepancies
- **`ServerPackageSpec` Model**:
  - Code includes `remote_endpoint`, `auth_type`, and `headers_schema` in `models.py`, which are completely undocumented in `docs/SPECIFICATION.md`.
- **`VersionFingerprint` Model**:
  - Code includes `prompt_signatures`, `resource_signatures`, `transport`, `remote_endpoint`, `auth_type`, `headers_schema`, and `required_env_vars` which are partially documented, but `transport`, `remote_endpoint`, `auth_type`, `headers_schema`, and `required_env_vars` are entirely missing from `docs/SPECIFICATION.md`.
- **`ToolContractSignature` Model**:
  - Code includes `parameters` and `annotations`, which are undocumented in `docs/SPECIFICATION.md`.
- **`PromptSignature` Model**:
  - Code includes `required_arguments` and `arguments_schema`, which are undocumented in `docs/SPECIFICATION.md`.
- **`ResourceSignature` Model**:
  - Code uses `uri_template` instead of `uri`. `docs/SPECIFICATION.md` documents `uri: string (or URI template)`. `mime_type` is documented as `mimeType`.

### Recommended Update Tasks
- **Task**: Update `docs/SPECIFICATION.md` schema hierarchy block to accurately reflect all fields in `ServerPackageSpec`, `VersionFingerprint`, `ToolContractSignature`, `PromptSignature`, and `ResourceSignature` models, specifically adding network transport and authentication fields, prompt schemas, and tool contract annotations.

## 3. Protocol Documentation: `task_88` Alignment

### Discrepancies
- The daily audit AI protocol in `docs/tasks/task_88_daily_audit_ai_workflow_and_resolution_protocol.md` correctly models the autonomous triage lifecycle. However, the report explicitly states the agent must not assume 100% accuracy and should cross-reference registries (npm, PyPI) and manual AST parsing. This is well-aligned with actual operational practices, as demonstrated by the codebase's reliance on fallback registries and markdown parsing to resolve 0-tool findings.

## 4. Release History Audit

### Discrepancies
- Releases up to `v1.1.7` exist as tags in Git. However, there are many tags (e.g., `v1.0.1` to `v1.0.23`, `v1.1.1`, `v1.1.2`, `v1.1.4`) that do not have corresponding markdown files in `docs/releases/`. Only `v1.1.0.md`, `v1.1.3.md`, `v1.1.5.md`, `v1.1.6.md`, and `v1.1.7.md` exist in the `docs/releases/` directory.

### Recommended Update Tasks
- **Task**: Generate missing release note markdown files in `docs/releases/` for all tagged versions to ensure a complete changelog history, or consolidate them into a single `CHANGELOG.md` file.

