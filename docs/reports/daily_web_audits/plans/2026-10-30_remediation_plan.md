# Action Plan for Daily Audit Remediation (2026-10-30)

## 1. Problem Statement
The daily audit run for 2026-10-30 identified multiple discrepancies between web catalog cards and the actual source truth:
1. Catalog cards claim non-zero tool counts for servers that act as Remote Gateways or SDK wrappers (which inherently have 0 local MCP tools).
2. The auditor misses tools documented strictly in Markdown tables or defined via explicit dynamic registrations.
3. 119 cards suffer from missing, unreachable, or private source repositories.

## 2. Targeted Modifications
To resolve these issues, we will make updates to the synchronization and parsing engines.

### A. Synchronizer & Auditor Updates
1. **Module**: `src/mcp_fingerprints/deep_zero_tool_auditor.py` (and relevant synchronizer/parser modules).
2. **Action**: Implement logic to accurately identify and tag Remote Gateways and SDK wrappers. If a source repository is confirmed to be a zero-tool gateway/SDK, the auditor should properly classify it and the catalog card should be updated to reflect 0 tools, preventing future mismatches.
3. **Action**: Enhance `src/mcp_fingerprints/doc_parser.py` (and integration with the synchronizer) to reliably parse Markdown tables. If `doc_parser.py` finds more tools in the `README.md` than the AST parser finds in source code, the auditor should use the Markdown tool count.
4. **Action**: Enhance AST parsing (`src/mcp_fingerprints/ast_parser.py` and language specific parsers) to catch dynamic tool registrations and non-standard wrappers (e.g. `@theyahia/tgstat-mcp`).

### B. Catalog Card Corrections
1. **Action**: Update the catalog/card generation logic to enforce 0 tool counts for servers confirmed as REMOTE_GATEWAY_OR_SDK.
2. **Action**: For `UNRESOLVED_SOURCE` cards (e.g., `smithery.ai` links without GitHub links), enhance fallback resolution to check NPM/PyPI registries using the package name.

## 3. Unit Test & Verification Requirements
1. **Unit Tests**:
   - Write tests in `tests/test_deep_zero_tool_auditor.py` and parser tests to ensure `doc_parser.py` correctly extracts tools from Markdown tables.
   - Write tests to verify that remote gateways are correctly identified and report 0 tools, overriding false web card claims.
2. **Passport Re-indexing**:
   - After implementing parser enhancements, re-run the extraction across all cached passports (`data/fingerprints/`) to apply the new Markdown parsing and dynamic registration logic.
   - Update `data/.passport_cache.json`.

## 4. Acceptance Criteria
- [ ] `docs/reports/daily_web_audits/reviews/2026-10-30_verification_report.md` exists and is detailed.
- [ ] `docs/reports/daily_web_audits/plans/2026-10-30_remediation_plan.md` exists and is detailed.
- [ ] The plan covers remote gateway handling, Markdown table parsing, and testing/re-indexing requirements.

