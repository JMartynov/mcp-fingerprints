# Task 30: SARIF Export for GitHub Code Scanning (`audit-config --format sarif`)

### 1. Architectural Context & Technical Objective
The current configuration auditing (`audit-config`) command provides basic JSON or terminal output. To seamlessly integrate `mcp_fingerprints` into enterprise CI/CD pipelines and issue management workflows (like GitHub Advanced Security Code Scanning), it needs to export structural risk findings in the standard SARIF (Static Analysis Results Interchange Format) format.
The objective is to implement a SARIF v2.1.0 exporter that translates the static AST tool capability risk profiles (e.g., exposed shell execution tools) into SARIF rules and results. Note: As per Clean Architecture, this export is strictly for *structural risks* found via AST, not external CVE vulnerabilities.

### 2. Technical Implementation Specifications
1. Create `src/mcp_fingerprints/sarif_exporter.py`.
2. Define the basic structural SARIF schema dictionaries (Rules, Results, Runs) adhering to the SARIF v2.1.0 specification.
3. Map internal static risk profiles (e.g., `ToolCapabilityRisk`) to SARIF `rules`.
4. Update `src/mcp_fingerprints/cli.py` `audit-config` command to support `--format sarif`.
5. Ensure zero external dependencies (no heavy schema validation libraries) are required for generation.

### 3. Clear Acceptance Criteria
- [ ] SARIF v2.1.0 generator implemented using plain python dictionaries.
- [ ] `audit-config` CLI command supports `--format sarif`.
- [ ] Output is valid JSON.
- [ ] Outputs only structural risks, adhering to Clean Architecture.

### 4. Unit Test Plan
1. **Schema Structure:** Generate a SARIF output from a mock audit result and assert the presence of required root keys (`version`, `$schema`, `runs`).
2. **Rule Mapping:** Assert that a specific `ToolCapabilityRisk` is correctly mapped to a `result` object referencing the correct `ruleId`.
3. **Empty Results:** Test that an audit with zero risks produces a valid SARIF file with an empty `results` array.

### 5. Live Acceptance Test Plan
Run `uv run mcp-fingerprints audit-config --config my_config.json --format sarif > out.sarif`. Open `out.sarif` and manually verify it is valid JSON and follows the expected structure. Optionally, attempt to upload the file to a GitHub repository's Code Scanning interface to verify compatibility natively.
