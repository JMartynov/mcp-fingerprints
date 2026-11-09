# Verification Report for Daily Audit 2026-11-08

## Phase 1 & 2: Finding Triage and Discrepancy Verification

### Triage of Mismatches (8 Cards)
The following packages reported mismatches but have been verified as either frameworks, SDKs, remote gateways, or completely unrelated to MCP tool providers. Therefore, they legitimately expose 0 MCP tools at their source root, consistent with `CONFIRMED_ZERO_TOOLS`:
- `@sumup/mcp`: Framework/SDK
- `@clipwright/mcp-server`: Framework/SDK
- `@ateam-ai/mcp`: Remote Gateway/SDK
- `eslint-plugin-mcp-sdk-security`: ESLint plugin package
- `nexus-mcp-ci`: Remote Gateway/SDK
- `knowledge-rag`: Remote Gateway/SDK
- `passbaton`: Remote Gateway/SDK
- `mcp-remote`: Remote Gateway/SDK

### Triage of MISSED_TOOLS & Auditor Tool Duplication Bug
In numerous occurrences (e.g. 13 vs 26, 34 vs 53, 18 vs 33, 42 vs 94), the number of tools discovered in the source drastically doubled or significantly exceeded the claimed card tool count.
**Root Cause identified:**
The core issue originates from two places where deduplication is missing:
1. `src/mcp_fingerprints/doc_parser.py`: In markdown extraction, tools are scraped from both markdown tables and markdown lists. If a documentation file lists tools in a summary table and later expands on them in a bulleted list, they are incorrectly appended twice.
2. `src/mcp_fingerprints/deep_zero_tool_auditor.py`: During repository scanning (`audit` / `inspect_file`), tools discovered across multiple source files (like `README.md`, `docs/tools.md`, or TS source files) are accumulated into an `all_tools` list using `extend()`. Since there is no deduplication step by tool name, the final list inflates the actual total number of unique tools, triggering false `MISSED_TOOLS` discrepancies.

### Triage of UNRESOLVED_SOURCE (55 Cards)
There are 55 cards flagged with `UNRESOLVED_SOURCE`, indicating a missing GitHub repository link or unresolvable registry URL. This means the engine could not locate the source of truth to extract tool data, leading to failed validation against the claimed tool counts on the catalog cards.

### Confirmed Perfect Matches (5 Cards)
The following 5 cards successfully matched `0` expected vs `0` observed tools, correctly being flagged as `PERFECT_MATCH`:
- `neurocode-ai`
- `tensorfeed`
- `a11y-toolkit`
- `cosmergon-agent`
- `@vruum/mcp`
