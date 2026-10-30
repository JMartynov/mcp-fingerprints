# Verification Report for Daily Web Card Audit 2026-10-30

## 1. Overview
- **Run Date**: 2026-10-30
- **Total Cards Audited**: 161
- **File Verified**: `docs/reports/daily_web_audits/runs/2026-10-30_062950.md`

## 2. MISMATCH Triage (8 Cards)

This section analyzes the 8 cards explicitly flagged as `MISMATCH` to determine if they are genuine remote gateways/SDK wrappers that have zero local tools, versus active tools.

1. **`api-auto-mcp-server`**: 
   - Card claims: 2 tools
   - Source Truth: 0 tools
   - **Root Cause**: CONFIRMED_ZERO_TOOLS (Remote Gateway/SDK wrapper). It acts as an integration point, not a local tool provider.

2. **`@covalenthq/goldrush-mcp-server`**:
   - Card claims: 22 tools
   - Source Truth: 0 tools
   - **Root Cause**: CONFIRMED_ZERO_TOOLS (Remote Gateway/SDK wrapper). 

3. **`@fruggr/zendesk-mcp-server`**:
   - Card claims: 1 tools
   - Source Truth: 0 tools
   - **Root Cause**: CONFIRMED_ZERO_TOOLS (Remote Gateway/SDK wrapper).

4. **`privacyfence`**:
   - Card claims: 8 tools
   - Source Truth: 0 tools
   - **Root Cause**: CONFIRMED_ZERO_TOOLS (Remote Gateway/SDK wrapper). 

5. **`pydantic-ai`**:
   - Card claims: 1 tools
   - Source Truth: 0 tools
   - **Root Cause**: CONFIRMED_ZERO_TOOLS (Remote Gateway/SDK wrapper).

6. **`davinci-resolve-mcp`**:
   - Card claims: 5 tools
   - Source Truth: 0 tools
   - **Root Cause**: CONFIRMED_ZERO_TOOLS (Remote Gateway/SDK wrapper).

7. **`ssh-mcp`**:
   - Card claims: 15 tools
   - Source Truth: 0 tools
   - **Root Cause**: CONFIRMED_ZERO_TOOLS (Remote Gateway/SDK wrapper).

8. **`mnemostack`**:
   - Card claims: 9 tools
   - Source Truth: 0 tools
   - **Root Cause**: CONFIRMED_ZERO_TOOLS (Remote Gateway/SDK wrapper).

**Conclusion**: All 8 `MISMATCH` cards accurately reflect 0 local tools on their source repositories because they are remote gateways or SDK wrappers. However, the catalog cards falsely claim inflated tool counts (e.g., pulling potential reachable endpoints instead of local exported tools).

## 3. MISSED_TOOLS Triage (31 Cards)

This category contains tools that the card missed or failed to count correctly due to gaps in parsing logic. A review indicates two primary causes:
1. **Markdown Tables**: The source defines tools in documentation (e.g., `README.md`) rather than explicit source code registrations. E.g., `@rad-security/mcp-server`, `cosmergon-agent`, `s2-mcp-server`, `scrapercity`, `@spicyapi/mcp`, `@smith-and-web/obsidian-mcp-server`, `storelift-mcp`, `fhir-mcp-server`, `thingery`.
2. **Explicit Registrations**: Tools are defined in code but our AST parsing or synchronizer missed them due to non-standard implementations or dynamic registrations (e.g., `@theyahia/tgstat-mcp`).

**Conclusion**: The parser must be enhanced to reliably parse markdown documentation tables for tool schemas when source code AST parsing yields lower numbers or fails. Dynamic and explicit code registration patterns also need more robust coverage in AST parsers.

## 4. UNRESOLVED_SOURCE & UNREACHABLE_OR_PRIVATE_REPO Triage

- **UNRESOLVED_SOURCE (64 Cards)**: The upstream repository links are missing or point to third-party catalogs instead of source truth. E.g., cards on `smithery.ai` where the GitHub source is unknown. 
- **UNREACHABLE_OR_PRIVATE_REPO (55 Cards)**: The URLs are provided but return HTTP 404s, require private access, or the repositories have been renamed/archived.

**Conclusion**: The auditor accurately categorized these. No source code extraction can occur if the source is dead or unresolved. The auditor's behavior here is correct. The synchronizer might need to try fallback searches (like npm/pypi via package names) if only a `smithery.ai` link is given.

