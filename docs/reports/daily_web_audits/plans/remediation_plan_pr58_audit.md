# Action Plan: Remediation of Daily Web Cards Audit Discrepancies & False Positives (PR #58)

## 1. Root Cause Analysis
During the daily web cards audit in PR #58, two primary discrepancies were found:
1. **Auditor Engine False Positives (63 Servers)**: The `DeepZeroToolAuditor.audit()` function incorrectly assumes that if a repository URL is missing or not a direct `github.com` link, the package contains 0 source tools (`CONFIRMED_ZERO_TOOLS: UNKNOWN_SOURCE`). This generates false discrepancies for valid packages published on PyPI or npm that simply lack a GitHub URL in `catalog.json` (e.g., `lnbits-mcp-server`, `opnsense-mcp`, `goldbean`).
2. **Missing Tool Extraction Gaps (4 Servers)**: Certain servers document their tools inside Markdown tables (e.g., `@zvid/mcp`, `giorgio44/gateonai-mcp-server`, `@fruggr/zendesk-mcp-server`) or supplementary OpenAPI specs (e.g., `@jrpool/kilotest`) rather than purely inline in code. The current AST parser misses these, undercounting the true tool count.

## 2. Architectural Plan for Registry URL Resolution
To eliminate false positives stemming from missing GitHub URLs, `DeepZeroToolAuditor.audit()` must resolve the upstream repository by querying the respective package registry endpoints:
- **PyPI Integration**: When `pypi.org` is present or the ecosystem implies PyPI, query `https://pypi.org/pypi/<pkg>/json` and extract URLs from `info.project_urls.Source` or `info.project_urls.Repository`.
- **npm Integration**: When `npmjs.com` is present or the ecosystem implies npm, query `https://registry.npmjs.org/<pkg>` and extract the URL from `repository.url`.

If a valid repository URL is discovered via the registry, the audit proceeds normally.

## 3. Proper Classification Protocol for Unresolved Sources
If the repository URL genuinely cannot be resolved (either missing registry info, 404, or private), the auditor must NOT claim `0` tools.
- **Auditor Response Update**: `DeepZeroToolAuditor.audit()` must return `status: "SOURCE_UNRESOLVED: NO_UPSTREAM_REPOSITORY"`.
- **Status Mapping Update**: `map_audit_to_status()` (or its equivalent handling logic) must output `source_tools: "?"` and `match_status: "UNRESOLVED_SOURCE"` instead of artificially declaring a mismatch with 0 tools.

## 4. Integration of Markdown Table Extraction
To handle documentation-heavy repositories:
- Integrate Markdown table extraction (e.g., via a `doc_parser.py` module) into the audit and synchronization pipeline.
- When AST parsing yields fewer tools than expected (or fewer than documented), the parser should inspect `README.md`, `docs/`, or known documentation files for markdown tables describing tool signatures.
- **OpenAPI Supplementation**: For wrappers like `@jrpool/kilotest`, the parser must ingest operation IDs from `openapi.yaml` or `openapi.json` to supplement the AST findings.

## 5. Technical Contract & Test Criteria for Task 87
**Task 87** will implement this remediation plan.

### Functions to Update:
1. `src/mcp_fingerprints/deep_zero_tool_auditor.py` -> `DeepZeroToolAuditor.audit(repo_url)`
   - Add registry API lookups (using standard `requests` or `urllib`).
   - Change fallback status to `"SOURCE_UNRESOLVED: NO_UPSTREAM_REPOSITORY"`.
2. `src/mcp_fingerprints/deep_zero_tool_auditor.py` -> `map_audit_to_status(server, audit_result)`
   - Add handling for `"SOURCE_UNRESOLVED"` status to map to `UNRESOLVED_SOURCE` and `?` source tools.
3. Ast Parsing / Doc Parsing Pipeline
   - Implement `doc_parser.py` logic to regex/parse markdown tables.
   - Enhance the OpenAPI fallback in `inspect_file` to capture operation IDs.

### Acceptance Criteria:
- [ ] Mock PyPI and npm lookups correctly return GitHub repository URLs.
- [ ] An unresolvable repository outputs `match_status: "UNRESOLVED_SOURCE"` and `source_tools: "?"`, generating no discrepancy.
- [ ] A mock repository containing tools purely in a Markdown table successfully extracts those tool names.
- [ ] A mock OpenAPI spec successfully supplements the tool list.
- [ ] Ensure clean separation of concerns without modifying the core AST rules for other languages.
