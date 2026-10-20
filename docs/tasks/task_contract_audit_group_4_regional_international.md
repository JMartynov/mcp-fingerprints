# Task Contract: Audit Group 4 (Regional & International Dev Communities)

## Objective
Audit the 200 Regional & International candidate MCP servers defined under `regional_international` in `docs/research/mcp_candidates_by_group.json` against the current repository index (`data/fingerprints/` and `passports.json.gz`). For every missing server, pinpoint the exact root cause / issue type and prescribe a specific technical remedy.

## Scope of Work

1. **Candidate Verification & Matching**:
   - Load the 200 candidates from `docs/research/mcp_candidates_by_group.json["regional_international"]`.
   - Cross-reference each candidate against `data/fingerprints/` and `passports.json.gz` using package names, repository URLs, aliases, and GitHub owner/repo patterns.
   - If present: record `in_repo = true` and `matched_passport = "<file>"`.

2. **Root Cause Diagnosis (for all missing servers)**:
   - For every missing server (`in_repo = false`), categorize into standardized issue types:
     * `REGIONAL_HOST_GITEE`: Hosted on Gitee rather than GitHub.
     * `NON_ENGLISH_METADATA_FILTER`: Non-English description or keywords causing false-positive heuristic rejections in crawlers.
     * `REGIONAL_PLATFORM_ECOSYSTEM`: Targeted at WeChat/WeCom, Bilibili, Dify plugins, Feishu/Lark, or Japanese platforms (Qiita/Zenn integrations) without standard npm/PyPI tags.
     * `MISSING_GITHUB_TOPICS`: Repo uses Chinese/Japanese/multilingual topics or no topics at all.
     * `CUSTOM_COMMUNITY_SDK`: Built with regional community SDKs or custom JSON-RPC wrappers.
   - Provide concrete technical explanation under `issue_details`.

3. **Formulate Specific Remedies**:
   - For each missing server, define the exact technical remedy:
     * Multilingual search query expansions (e.g. searching with Chinese/Japanese MCP keywords).
     * Gitee code host adapter or regional community seed indexing.
     * Sanitizer whitelist rules preventing false-positive rejection of international characters.

4. **Deliverables**:
   - `docs/research/audit_group_4_regional_international.json`: JSON array with all 200 audited candidates (fields: `name`, `location`, `ecosystem`, `in_repo`, `matched_passport`, `issue_type`, `issue_details`, `remedy`).
   - `docs/research/audit_group_4_regional_international.md`: Full markdown table (`| MCP Name | Location | Present in Repo? | Issue Type | Specific Technical Remedy |`) and category breakdown summary.
   - Conformance test `tests/test_audit_group_4.py`:
     * Asserts `docs/research/audit_group_4_regional_international.json` exists.
     * Asserts exactly 200 entries.
     * Asserts every missing entry has non-empty `issue_type` and `remedy`.
     * Passes `pytest tests/test_audit_group_4.py`.

## Non-Interactive Completion Directive
Execute the audit autonomously. Generate the JSON and markdown deliverables, create and run the test suite, and finalize directly so the remote environment transitions cleanly to `Completed`.
