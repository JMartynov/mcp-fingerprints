# Task 31: MCP Server Software Bill of Materials (SBOM / CycloneDX)

### 1. Architectural Context & Technical Objective
While `mcp_fingerprints` tracks the structural layout of MCP servers via passports, it does not currently generate standard Software Bill of Materials (SBOMs) for the servers themselves.
The objective is to implement an SBOM generation module that exports an MCP server's structural metadata and tool lists into the CycloneDX 1.5 JSON specification. This allows the structural data extracted by `mcp-fingerprints` to be easily ingested by standard enterprise supply chain tooling without blurring the lines into active vulnerability scanning.

### 2. Technical Implementation Specifications
1. Create `src/mcp_fingerprints/sbom.py`.
2. Map `ServerPackageSpec` and `VersionFingerprint` data to a CycloneDX 1.5 JSON structure.
   - Component type: `application`.
   - Include tools as nested components or properties.
3. Add a new CLI command `mcp-fingerprints sbom <package_name> --format cyclonedx`.
4. Ensure generation relies only on standard Python dictionaries and standard library `json`.

### 3. Clear Acceptance Criteria
- [ ] `src/mcp_fingerprints/sbom.py` generates valid CycloneDX 1.5 JSON dictionaries.
- [ ] CLI `sbom` command implemented.
- [ ] Structural data correctly mapped to CycloneDX components.

### 4. Unit Test Plan
1. **Spec Generation:** Pass a mocked `ServerPackageSpec` to the generator. Assert the output dict contains `bomFormat: "CycloneDX"` and `specVersion: "1.5"`.
2. **Component Mapping:** Assert that the primary package name and version are correctly mapped to the main component's `name` and `version` fields.
3. **PURL Validation:** Ensure the package's PURL is correctly injected into the component `purl` field.

### 5. Live Acceptance Test Plan
Run `uv run mcp-fingerprints sbom my-mcp-server --format cyclonedx > sbom.json`. Manually inspect `sbom.json` to ensure the format is valid JSON and structurally resembles standard CycloneDX format for the specified server.
