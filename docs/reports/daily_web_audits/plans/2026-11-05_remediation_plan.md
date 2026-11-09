# Daily Web Card Audit Remediation Plan — 2026-11-05

## 1. Overview
The daily audit run on 2026-11-05 highlighted several discrepancies. These are primarily grouped into two main areas requiring code and parsing fixes:
1. False Positives extracted from design and specification documents.
2. Missing extraction from static documentation tables, TypeScript registrations, and JSON configurations.

## 2. Root Causes Identified

### Auditor False Positives
The `DeepZeroToolAuditor` currently scans a wide array of markdown files without selectively excluding design docs or planning materials. This causes standard tables within files under `docs/design/`, `skills/`, or ending in `-plan.md` to be incorrectly parsed as MCP tool definitions.

### Real Parser Gaps
- **Markdown Tables**: Need to ensure the auditor can correctly identify valid markdown tools and ignore non-tool documents via path exclusions.
- **Explicit Registrations / Configurations**: Tool extraction logic must encompass files like `server.json` and `.well-known/mcp/server-card.json`. The TS parsers also need robust support for `server.registerTool()` patterns (which should ideally be handled by the AST parsing layer if not already, or surfaced via the Deep Zero Tool Auditor's extractions).

## 3. Targeted Code Modifications

### `src/mcp_fingerprints/deep_zero_tool_auditor.py`
- Modify path evaluation logic to explicitly exclude documentation paths known to yield false positives.
- Add exclusions for:
  - `"docs/design/"`
  - `"/design/"`
  - `"-plan.md"`
  - `"skills/"`
- Ensure this filtering applies to `secondary_patterns` or during file traversal.

### `src/mcp_fingerprints/doc_parser.py`
- Review table parsing logic to see if strict validation needs enhancing. However, path exclusions in the auditor may be sufficient to resolve the observed false positives. If necessary, we will add content-based heuristics to reject generic tables.

## 4. Unit Testing Strategy

### `tests/test_audit_remediation_2026_11_05.py`
- **Path Exclusions**: Test the Deep Zero Tool Auditor with mock file trees containing `docs/design/visimark-simulate-mcp-tool-plan.md`, `skills/references/autoloop.md`, and `skills/image-prompting/SKILL.md` to confirm these files are excluded.
- **Markdown Extraction**: Test valid `README.md` file extraction versus excluded ones.
- **Status Mapping**: Verify that the tool maps missing source packages to `UNRESOLVED_SOURCE` and confirms 0-tool packages appropriately based on source contents (like Remote Gateways generating a `MISMATCH`).

We will implement this plan and test via `pytest tests/test_audit_remediation_2026_11_05.py -q`.