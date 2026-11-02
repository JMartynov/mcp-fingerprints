# Verification Report for Daily Web Card Audit 2026-11-02

## 1. Overview
- **Run Date**: 2026-11-02
- **Total Cards Audited**: 82
- **File Verified**: `docs/reports/daily_web_audits/runs/2026-11-02_065028.md`

## 2. MISSED_TOOLS Triage (2 Cards)

This section analyzes the 2 cards flagged as `MISSED_TOOLS`, which had a zero tool count claimed by the card, but a high tool count detected in the source.

1. **`fastmcp`**:
   - Card claims: 0 tools
   - Source Truth (Parsed): 220 tools
   - **Root Cause**: FALSE_POSITIVE_MARKDOWN. The auditor extracted 220 "tools" from `dev-docs/v3-notes/v3-features.md`. `fastmcp` is an MCP framework/SDK, not a standalone MCP server with exposed tools. The table parsed from the v3 features notes was a roadmap or feature matrix, incorrectly identified as an MCP tool declaration table.

2. **`privacyfence`**:
   - Card claims: 9 tools
   - Source Truth (Parsed): 427 tools
   - **Root Cause**: FALSE_POSITIVE_MARKDOWN. The auditor extracted 427 "tools" from `docs/adr/0013-no-mcp-tool-mints-a-sign-in-credential.md`. This file is an Architecture Decision Record (ADR), not a tool definition document. The markdown parser erroneously identified a decision matrix or unrelated table as MCP tools.

**Conclusion**: The parser must be enhanced with strict guardrails to avoid scraping unrelated markdown files (such as ADRs, roadmaps, and framework release notes). Furthermore, the logic should properly classify repositories as Frameworks/SDKs rather than Servers, and enforce 0 tool counts for those.

## 3. UNRESOLVED_SOURCE & UNREACHABLE_REPO Triage

- **UNRESOLVED_SOURCE (49 Cards)**: The upstream repository links are missing or point to third-party catalogs instead of source truth (e.g., `smithery.ai` or missing `github.com` URLs). Examples include `lnbits-mcp-server`, `opnsense-mcp`, `goldbean`, `markmhendrickson/neotoma`, `ai.4ai/domains`, `coil-mcp`.
- **UNREACHABLE_REPO (31 Cards)**: URLs are provided but return HTTP 404s, require private access, or the repositories are dead/archived. Examples include `@zvid/mcp`, `giorgio44/gateonai-mcp-server`, `michal-niedzwiedzki/visimark`, `mcp-proxy`, `keep-mcp`, `excel-mcp-server`, `health-export-mcp`.

**Conclusion**: The auditor accurately categorized these. No source code extraction can occur if the source is dead or unresolved. The synchronizer must be enhanced to implement fallback registry lookups (e.g., npm, PyPI) to locate the source code for unresolved URLs like `smithery.ai` cards without GitHub links.
