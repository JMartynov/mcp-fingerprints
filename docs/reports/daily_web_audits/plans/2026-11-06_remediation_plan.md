## Remediation Action Plan

1. Root causes: Unexcluded markdown paths (`skills/`, `claude.md`) in `DeepZeroToolAuditor` causing false positive tool extraction from skill definitions and project instructions; invalid tool name strings extracted from narrative documentation tables.
2. Targeted module modifications:
   - `src/mcp_fingerprints/deep_zero_tool_auditor.py`: Add `"skills/"`, `"claude.md"`, `".claude"` to `secondary_patterns` path exclusions.
   - Clean up invalid tool artifacts in affected passport JSON:
     - `data/fingerprints/ai.ankidecks_ankidecks.json`: Clear the 2 bogus tool signatures (`"The upload box..."` and `"Transport"`) that were falsely extracted from README narrative text, setting `tool_signatures` to `[]` (or clean valid tools).
     - Check `data/fingerprints/blockrunai_blockrun-mcp.json` and `data/fingerprints/bvisible_mcp-ssh-manager.json`.
3. Unit test design for `tests/test_audit_remediation_2026_11_06.py`.
4. Acceptance criteria and verification commands.
