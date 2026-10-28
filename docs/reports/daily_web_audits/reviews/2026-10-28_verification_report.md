# Phase 2 Verification Report - 2026-10-28

## Overview
This report provides an item-by-item analysis across all 87 cards checked in the `2026-10-28_071611.md` audit run.

- **Total Cards Verified:** 87
- **UNRESOLVED_SOURCE:** 64
- **MISMATCH entries:** 18
- **PERFECT_MATCH entries:** 5

## Category Breakdown

### 1. Confirmed Gaps (Parser Missing Real Tools)
While many mismatches initially appear as missing zero-tool servers, investigations reveal they actually contain tools using patterns the parser currently misses.

### 2. Auditor False Positives (The 18 Mismatches)
The following 18 repositories were flagged as `MISMATCH` (expecting 0 tools, but finding >0 in the cards):
- `@zvid/mcp`
- `giorgio44/gateonai-mcp-server`
- `api-auto-mcp-server`
- `@1mcp/agent`
- `@fodx/codelens`
- `@fruggr/zendesk-mcp-server`
- `@jrpool/kilotest`
- `@mojomo/mcp-server`
- `@openephemeris/mcp-server`
- `@automatelab/content-distribution-mcp`
- `mcp-searxng`
- `audionaut-mcp`
- `mcp-ssh-manager`
- `eslint-plugin-mcp-sdk-security`
- `health-export-mcp`
- `notion-mcp-server`
- `capsulemcp`
- `ssh-mcp`

**Root Cause Analysis:**
These are NOT genuine zero-tool packages. The AST parser and `inspect_file` missed the tools because of unhandled patterns:
- TypeScript `server.registerTool(...)` (e.g. `@zvid/mcp`, `capsulemcp`, `notion-mcp-server`).
- TypeScript `server.tool(...)`.
- Python `Tool(name=...)` instantiation (e.g. `gateonai-mcp-server`).
- Tools buried in subdirectories not checked deeply enough, such as `src/tools/`, `Tools/audionaut-mcp/`, or `lib/tools/`.

### 3. Dead/Unreachable Repositories
The 64 `UNRESOLVED_SOURCE` entries indicate packages where the GitHub repository could not be resolved or reached, either because they are private, deleted, or the URL in the catalog is missing/incorrect and could not be recovered via PyPI/npm API lookups.
