# Phase 2 Verification Report - 2026-10-29

## Overview
This report provides an item-by-item analysis across all 87 cards checked in the `2026-10-29_063053.md` audit run.

- **Total Cards Verified:** 87
- **PERFECT_MATCH entries:** 2
- **UNRESOLVED_SOURCE:** 53
- **MISMATCH entries:** 4
- **MISSED_TOOLS entries:** 18

## Category Breakdown

### 1. PERFECT_MATCH
2 repositories successfully matched zero tools both in the catalog card and the source code:
- `@juspay/neurolink`
- `aura-memory`

### 2. UNRESOLVED_SOURCE
53 repositories were flagged because the upstream GitHub repository could not be resolved or reached. This includes cases where package catalog metadata lacks a direct repository URL or points to a non-existent location, preventing validation.

### 3. MISMATCH Entries (4)
Four packages expected 0 tools based on source truth but found >0 tools on their cards:
- **`data-olympus` and `privacyfence`**:
  - The repository URLs listed in the cards are `https://smithery.ai/servers/data-olympus` and `https://smithery.ai/servers/privacyfence`.
  - The root cause is `CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK`.
  - While PyPI has repository metadata for these, the auditor failed to resolve them correctly because it treats Smithery hub links as direct GitHub equivalents. URL parsing must inspect PyPI/npm `project_urls` when `repository_url` is a registry or hub link rather than a direct GitHub repo.
- **`ssh-mcp` and `api-auto-mcp-server`**:
  - Also flagged as `CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK`.
  - These repos do not declare tools locally but act as gateways or SDKs that route to remote tool definitions, resulting in local ast/doc analysis correctly reporting 0 tools but creating a mismatch against the web card.

### 4. MISSED_TOOLS (18)
Eighteen repositories resulted in severe tool count inflation due to indiscriminately parsing markdown tables. A detailed triage reveals the tools were extracted from secondary documentation:

- **`giorgio44/gateonai-mcp-server`**: Card listed 67, Source jumped to 152. Cause: `CHANGELOG.md` had historical version tables.
- **`knowledge-rag`**: 67 tools extracted from `CHANGELOG.md`.
- **`a11y-toolkit`**: 38 tools extracted from `CHANGELOG.md`.
- **`notion-mcp-server`**: 76 tools extracted from `MIGRATION.md`.
- **`@1mcp/agent`**: 35 tools extracted from `docs/ROADMAP.md`.
- **`capsulemcp`**: 25 tools extracted from `OPTIMIZATIONS.md`.
- **`mushi-mushi`**: 3 tools extracted from `.cursor/skills/mushi-debug/SKILL.md`.

**Root Cause:**
Secondary documentation files (e.g., `CHANGELOG.md`, `ROADMAP.md`, `MIGRATION.md`, `.cursor/`) contain historical version tables, migration mappings, or planned features rather than currently active MCP tools. Indiscriminately aggregating markdown tables from these files causes drastically inflated tool counts.
Note that packages where `README.md` legitimately contains tool tables (e.g., `@zvid/mcp`, `@samsadch/adb-mcp`) are structurally correct but still affected by broader markdown table logic.
