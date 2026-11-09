## Independent Item-by-Item Verification Report (2026-11-06)

1. **MISSED_TOOLS Analysis (3 discrepancies flagged)**:
   - `ai.ankidecks/ankidecks` (Card Tools: 0, Source Tools: 2): The auditor extracted 2 fake tools from README.md ("The upload box is an [MCP App](https", "Transport"). These are markdown text/table false positives, not MCP tools. The upstream repository exposes remote web/HTTP endpoints and OAuth, not local tool declarations.
   - `@blockrun/mcp` (Card Tools: 34, Source Tools: 68): Auditor inspected `skills/image-prompting/SKILL.md` and extracted table rows as MCP tools. Agent skills definitions under `skills/` are prompt templates, not MCP server tools. This inflated the tool count by 34 (34 real tools vs 68 detected).
   - `mcp-ssh-manager` (Card Tools: 8, Source Tools: 43): Auditor inspected `CLAUDE.md` and extracted prompt/command guidance table rows as MCP tools. Project developer instructions and CLAUDE.md documentation are not MCP tools.
2. **UNREACHABLE_REPO Analysis (40 servers)**:
   - Upstream repositories return HTTP 404, are private, or have been renamed/deleted.
   - Retain historical passport metadata without deletion.
3. **UNRESOLVED_SOURCE Analysis (54 servers)**:
   - Packages on npm/PyPI lacking repository URLs or requiring fallback resolution.
   - Correctly flagged as UNRESOLVED_SOURCE.
