## Remediation Fix Report (2026-11-06)

**Related Task**: Task 88 Daily Web Card Audit Remediation for 2026-11-06 (PR #96)

**References**:
- [docs/reports/daily_web_audits/runs/2026-11-06_081219.md](file:///docs/reports/daily_web_audits/runs/2026-11-06_081219.md)
- [docs/reports/daily_web_audits/reviews/2026-11-06_verification_report.md](file:///docs/reports/daily_web_audits/reviews/2026-11-06_verification_report.md)
- [docs/reports/daily_web_audits/plans/2026-11-06_remediation_plan.md](file:///docs/reports/daily_web_audits/plans/2026-11-06_remediation_plan.md)

**Modified Files**:
- [src/mcp_fingerprints/deep_zero_tool_auditor.py](file:///src/mcp_fingerprints/deep_zero_tool_auditor.py)
- [data/fingerprints/ai.ankidecks_ankidecks.json](file:///data/fingerprints/ai.ankidecks_ankidecks.json)
- [tests/test_audit_remediation_2026_11_06.py](file:///tests/test_audit_remediation_2026_11_06.py)

**Summary of Fixes**:
1. Added `"skills/"`, `"claude.md"`, and `".claude"` to the exclusion list (`secondary_patterns`) in `DeepZeroToolAuditor.inspect_file` to prevent false positive extraction of MCP tools from narrative documentation and agent skills files.
2. Cleaned `data/fingerprints/ai.ankidecks_ankidecks.json` by removing the two bogus markdown tools extracted from its `README.md` and correctly recalculated `toolset_canonical_hash` for version 1.0.0. Checked other repositories as well.
3. Added isolated unit tests in `tests/test_audit_remediation_2026_11_06.py` which successfully pass and verify that markdown files matching `skills/`, `CLAUDE.md`, or `.claude` are rejected and ignore any mock narrative tables inside. 

**Verification**:
```
$ uv run pytest tests/test_audit_remediation_2026_11_06.py -q
.                                                                        [100%]
1 passed in 0.14s
```
