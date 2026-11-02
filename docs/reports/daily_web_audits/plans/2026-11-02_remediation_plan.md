# Action Plan for Daily Audit Remediation (2026-11-02)

## 1. Problem Statement
The daily audit run for 2026-11-02 identified a few significant discrepancies between web catalog cards and the actual source truth:
1. False Positive Markdown parsing: The Markdown parser (`doc_parser.py`) is incorrectly extracting MCP tools from unrelated tables in ADR documents (Architecture Decision Records) and framework roadmap/feature matrices. This affected `privacyfence` and `fastmcp`.
2. `fastmcp` (and similar projects) are frameworks/SDKs, not standalone MCP servers, and should inherently have 0 local MCP tools.
3. 80 cards suffer from missing, unreachable, or private source repositories (`UNRESOLVED_SOURCE` and `UNREACHABLE_REPO`).

## 2. Targeted Modifications
To resolve these issues, we will make updates to the Markdown parser, framework detection, and fallback resolution mechanisms.

### A. Markdown Parser Guardrails
1. **Module**: `src/mcp_fingerprints/doc_parser.py` (and integration points like `deep_zero_tool_auditor.py`).
2. **Action**: Implement technical specifications to guard markdown documentation parsing from false positive tables.
   - Ignore files in paths like `docs/adr/`, `dev-docs/v3-notes/`, or containing keywords like `adr`, `roadmap`, `features` if they are not explicitly declaring tools.
   - Add heuristics to ensure the table header contains tool-related keywords (e.g., `tool`, `name`, `description`, `schema`) rather than generic columns.

### B. Framework/SDK Classification
1. **Module**: `src/mcp_fingerprints/deep_zero_tool_auditor.py` (and relevant catalog management tools).
2. **Action**: Define classification rules for framework/SDK repositories vs MCP servers.
   - Check the repository topics, `README.md`, or package metadata (`package.json`, `pyproject.toml`) for keywords like `framework`, `sdk`, `toolkit`.
   - Projects classified as `FRAMEWORK_OR_SDK` must have their tool counts overridden to 0 to prevent false tool attributions.

### C. Fallback Repository Resolution
1. **Module**: `src/mcp_fingerprints/hub_resolver.py` (or similar registry resolution module).
2. **Action**: Enhance registry resolution for `UNRESOLVED_SOURCE` cards.
   - For hub links (like `smithery.ai` or `glama.ai`) without direct GitHub links, attempt to resolve the package via NPM or PyPI using the package name to find the true source repository.

## 3. Unit Test & Verification Requirements
1. **Unit Tests**:
   - Write tests in `tests/test_doc_parser.py` to ensure ADRs and roadmap tables are ignored, and only valid tool definition tables are parsed.
   - Write tests to verify that Framework/SDK repositories are correctly classified and overridden to 0 tools.
   - Mock offline fixtures to verify fallback registry resolution strategies.
2. **Passport Re-indexing**:
   - Re-index affected passports under `data/fingerprints/` (`privacyfence`, `fastmcp`, etc.) using the updated logic.
   - Update `data/.passport_cache.json`.

## 4. Acceptance Criteria
- [ ] `docs/reports/daily_web_audits/reviews/2026-11-02_verification_report.md` exists and is detailed.
- [ ] `docs/reports/daily_web_audits/plans/2026-11-02_remediation_plan.md` exists and is detailed.
- [ ] The plan covers markdown false positive guardrails, SDK classification rules, fallback resolution strategies, and testing/re-indexing requirements.
