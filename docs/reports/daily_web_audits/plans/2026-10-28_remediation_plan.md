# Phase 3 Remediation Action Plan - 2026-10-28

## Problem Statement
The daily audit from `2026-10-28` identified 18 `MISMATCH` false positives. These occurred because `inspect_file` in `src/mcp_fingerprints/deep_zero_tool_auditor.py` failed to identify explicit tool registration patterns (`server.registerTool`, `server.tool`, `Tool(name=...)`) and failed to discover tools nested in standard subdirectories (`src/tools/`, `Tools/`, `lib/tools/`). Additionally, Python 3.14 environment SSL contexts occasionally fail for registry lookups.

## Technical Specifications (Phase 4)

1. **Enhance `inspect_file` in `src/mcp_fingerprints/deep_zero_tool_auditor.py`**:
   - Add Regex checks for TypeScript/JavaScript:
     - `server\.registerTool\s*\(`
     - `server\.tool\s*\(`
   - Add Regex checks for Python:
     - `Tool\s*\(\s*name\s*=\s*['"]([^'"]+)['"]`
   - Map these to corresponding `format` and `remedy` dictionaries.

2. **Support Recursive Subdirectory Scanning**:
   - The current auditor must iterate or recursively check subdirectories like `src/tools/`, `Tools/`, and `lib/tools/` for TS/JS/Python files if it's inspecting a repository clone or structure.
   - For `audit`, if it clones or fetches files, it should fetch them from these common paths or extract deeply if using an API. *(Note: need to check how `audit` currently fetches files—usually it queries GitHub API or raw files).* Let's update the GitHub API file-fetching logic in `audit` to scan deeper.

3. **Add SSL unverified context fallback in `urllib.request.urlopen`**:
   - To support Python 3.14 environments, add an SSL unverified context:
     ```python
     import ssl
     ctx = ssl.create_default_context()
     ctx.check_hostname = False
     ctx.verify_mode = ssl.CERT_NONE
     ```
     Pass `context=ctx` to `urllib.request.urlopen`.

4. **Regression Unit Tests in `tests/test_deep_zero_tool_auditor.py`**:
   - Test TypeScript `server.registerTool(...)`.
   - Test TypeScript `server.tool(...)`.
   - Test Python `Tool(name="...")`.
   - Test subdirectory fetching/scanning (mocking the API/filesystem).

## Acceptance Criteria
- Unit tests pass.
- Network calls are mocked or guarded.
- All code follows strict AI isolation rules.
