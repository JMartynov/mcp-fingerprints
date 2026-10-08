# Task Specification: Reusable GitHub Action & Pre-Commit Hook

## Objective
Package `mcp-fingerprints audit-config` as a reusable GitHub Action and pre-commit hook so developer teams and agent repositories can automatically block MCP tool collisions and high-risk shadowing in CI and local git hooks.

## Scope & Requirements
1. **Reusable GitHub Action** (`action.yml` in repository root):
   - Name: `Audit MCP Client Configuration`
   - Description: `Audit MCP client configurations (Claude, Cursor, Cline, Zed) for tool collisions and security shadowing.`
   - Inputs:
     - `config-file`: Path to the client config file (required).
     - `passports-dir`: Path to passport data directory (default: `data/fingerprints`).
     - `fail-on-critical`: Whether to fail the workflow if critical collisions are found (default: `"true"`).
     - `json-output`: Whether to output results as JSON (default: `"false"`).
   - Runs: `composite` action running `python -m mcp_fingerprints.cli audit-config`.
2. **Pre-Commit Hook Definition** (`.pre-commit-hooks.yaml` in repository root):
   - Hook ID: `mcp-audit-config`
   - Name: `MCP Client Configuration Auditor`
   - Description: `Audit MCP configurations for tool collisions and shadowing`
   - Entry: `mcp-fingerprints audit-config`
   - Language: `python`
   - Files: `.*mcp.*\.json$|claude_desktop_config\.json$|cursor_settings\.json$`
3. **Tests & Validation**:
   - Create `tests/test_action_and_hooks.py` testing that `action.yml` and `.pre-commit-hooks.yaml` parse as valid YAML and contain all required metadata and arguments.

## Acceptance Criteria
- [ ] `action.yml` is valid composite action YAML with documented inputs and outputs.
- [ ] `.pre-commit-hooks.yaml` provides a valid hook configuration for pre-commit.
- [ ] Unit tests pass verifying YAML validity and expected schema structure.
