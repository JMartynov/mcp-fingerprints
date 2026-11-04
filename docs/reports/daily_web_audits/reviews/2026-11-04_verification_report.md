# Verification Report for 2026-11-04 Daily Web Card Audit

## 1. Triage of Mismatch (@llamaventures/cli)
- **Classification**: CONFIRMED_ZERO_TOOLS: REMOTE_GATEWAY_OR_SDK.
- **Root Cause**: The `@llamaventures/cli` card in `web/catalog.json` claimed 27 tools, but upstream repository exposes no local tools, acting as a remote gateway or SDK which inherently has 0 tools. This is a false positive by the auditor flagging it as a mismatch, when the expected tools are 0 and the card has 27. It's an issue with the catalog, and the auditor correctly identified it as 0.

## 2. Triage of MISSED_TOOLS (38 cards)
- **Classification**: Auditor False Positives.
- **Root Cause**: The `DeepZeroToolAuditor` and `doc_parser.py` are mistakenly extracting tables from non-MCP tool files, resulting in inflated tool counts for "Source Truth".
- **Sources of False Positives**:
    - `.agents/skills/` (e.g. `michal-niedzwiedzki/visimark`, `@codescene/codehealth-mcp`)
    - `.claude/skills/` (e.g. `@fruggr/zendesk-mcp-server`)
    - `configs/` (e.g. `@enderfga/claw-orchestrator/configs/autoloop-coder-prompt.md`)
    - `eval/` or `RESULTS.md` (e.g. `@browsermcp/mcp/packages/mcp/eval/RESULTS.md`)
    - `CONTRIBUTING.md`, `RELEASE_NOTES.md`
- **Resolution**: Exclude these paths from being analyzed by `doc_parser.py` in `deep_zero_tool_auditor.py`. Also, harden `doc_parser.py` to ensure only real MCP tables are parsed.

## 3. Triage of UNRESOLVED_SOURCE (54 cards)
- **Classification**: Unresolved Sources (Catalog issue).
- **Root Cause**: Missing valid GitHub source repository links or requiring fallback registry resolution.
- **Resolution**: These are correctly flagged by the auditor since the source truth cannot be determined due to missing/invalid repository URLs. No changes needed to the auditor for these, as it properly flags them as `UNRESOLVED_SOURCE`.
