# Task Contract: Task 65 — CycloneDX 1.6 AI-Tool SBOM Export & Sigstore Keyless Attestation (`mcp-fingerprints export-sbom`)

## 1. Problem Statement
In the Task 9 supply-chain benchmark ([`docs/reports/task9_sbom_attestation_supply_chain_report.md`](../reports/task9_sbom_attestation_supply_chain_report.md) and [`docs/reports/ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md`](../reports/ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md)), we identified two major enterprise adoption gaps:
1. **Proprietary Schema vs. Enterprise SBOM Standards**: Enterprise security platforms (OWASP Dependency-Track, Snyk, Chainguard, Anchore) ingest standardized **CycloneDX 1.6** or **SPDX 2.3** Software/AI Bills of Materials, whereas `mcp-fingerprints` exports only its internal `ServerPackageSpec` JSON format.
2. **Unsigned Passports vs. Cryptographic Provenance**: While `mcp-fingerprints` computes deterministic SHA-256 `toolset_canonical_hash` digests, `passports.json.gz` and release artifacts lack detached keyless **Sigstore Cosign OIDC** cryptographic attestations.

Crucially, **Pillar 2 (Pure Structural Domain Isolation)** strictly prohibits polluting `ServerPackageSpec` or `VersionPassport` with mutable build timestamps, dynamic CVE feeds, or ephemeral certificate blobs. Therefore, **Task 65** implements an out-of-band **CycloneDX 1.6 / SPDX 2.3 SBOM Exporter (`mcp-fingerprints export-sbom`)**, a detached **Sigstore Bundle Verifier**, and keyless Sigstore OIDC signing in `.github/workflows/release.yml`.

---

## 2. Technical Requirements & Deliverables

### A. SBOM Exporter & Sigstore Verifier (`src/mcp_fingerprints/sbom_exporter.py`)
Create `src/mcp_fingerprints/sbom_exporter.py` with the following components:

1. **`SBOMFormat` (`str, Enum`)**:
   - `"cyclonedx"` — CycloneDX v1.6 JSON specification (`bomFormat: "CycloneDX"`, `specVersion: "1.6"`).
   - `"spdx"` — SPDX v2.3 JSON specification (`spdxVersion: "SPDX-2.3"`, `dataLicense: "CC0-1.0"`).

2. **`CycloneDXExporter`**:
   - Converts a single `ServerPackageSpec` or an entire catalog (`Iterable[ServerPackageSpec]`) into a compliant CycloneDX 1.6 JSON document (or SPDX 2.3 JSON when `format="spdx"`):
     - Top-level fields: `"bomFormat": "CycloneDX"`, `"specVersion": "1.6"`, deterministic `"serialNumber": "urn:uuid:<uuid5_from_canonical_hash>"`, `"version": 1`.
     - `"metadata"`: `"tools"` entry identifying `mcp-fingerprints` and primary `"component"` when exporting a single package.
     - Package `"components"`:
       - `"type": "application"`, `"name": spec.package_name`, `"version": latest_version`, `"purl": <derived_or_explicit_purl>` (`pkg:npm/...`, `pkg:pypi/...`, `pkg:cargo/...`, `pkg:golang/...`, `pkg:github/...`).
       - `"hashes"`: `[{"alg": "SHA-256", "content": toolset_canonical_hash}]` (when non-empty).
       - `"externalReferences"`: `[{"type": "vcs", "url": spec.repository_url}]` (when `repository_url` is present).
       - Nested `"components"` or `"services"` for each `ToolContractSignature` in the version passport:
         - `"type": "library"`, `"bom-ref": f"{spec.package_name}#tool:{tool.name}"`, `"name": f"mcp-tool:{tool.name}"`, `"description": tool.description`.
         - `"hashes"`: `[{"alg": "SHA-256", "content": tool.schema_hash}]` (or computed SHA-256 of canonical tool schema).
         - `"properties"`: `mcp:tool:name`, `mcp:tool:parameter_count`, `mcp:tool:read_only_hint`, `mcp:tool:destructive_hint`, `mcp:tool:idempotent_hint`, `mcp:tool:open_world_hint`.

3. **`SigstoreBundleVerifier`**:
   - Validates detached Sigstore bundle JSON files (`*.sigstore.json` or `*.bundle`) against an artifact file (`passports.json.gz` or passport JSON):
     - Computes the artifact's SHA-256 digest.
     - Parses the detached Sigstore bundle structure (`mediaType` matching `application/vnd.dev.sigstore.bundle+json;version=0.1` or `0.2`/`0.3`, `verificationMaterial`, `messageSignature` or `dsseEnvelope`).
     - Verifies that any embedded message digest in `messageSignature.messageDigest` matches the artifact's actual SHA-256 digest (and optionally invokes `cosign verify-blob` if `shutil.which("cosign")` is available and requested).
     - Returns a structured `AttestationVerificationResult(verified: bool, artifact_sha256: str, signer_identity: Optional[str], rekor_log_index: Optional[int], reason: str)`.

### B. CLI Subcommand (`src/mcp_fingerprints/cli.py`)
Register the `export-sbom` subcommand in `src/mcp_fingerprints/cli.py`:
```bash
mcp-fingerprints export-sbom \
  [--passport <name_or_path> | --all] \
  --format [cyclonedx|spdx] \
  [--output <file>]
```
- If `--passport <name_or_path>` is passed, export the SBOM for that single server passport.
- If `--all` is passed, export a consolidated catalog SBOM across local passports.
- Output JSON to `--output <file>` or `stdout`.

### C. Release Workflow Keyless Attestation (`.github/workflows/release.yml`)
Update `.github/workflows/release.yml` so that release jobs have `id-token: write` permission and include a keyless Sigstore Cosign signing step (`sigstore/cosign-installer@v3`) that signs `data/passports.json.gz` (and built wheel/sdist artifacts) via `cosign sign-blob --yes --bundle <artifact>.sigstore.json <artifact>` and attaches the detached `.sigstore.json` bundle to the GitHub Release.

### D. Comprehensive Unit Tests (`tests/test_sbom_exporter.py`)
Create `tests/test_sbom_exporter.py` covering:
1. **CycloneDX 1.6 Schema Compliance & Determinism**:
   - Verify `bomFormat == "CycloneDX"`, `specVersion == "1.6"`, deterministic `serialNumber` (`urn:uuid:...`), `purl` generation across ecosystems (`npm`, `pypi`, `cargo`, `go`), `SHA-256` hash mapping from `toolset_canonical_hash`, `externalReferences`, and nested tool sub-components with MCP safety hint properties.
2. **SPDX 2.3 Export Support**:
   - Verify `--format spdx` generates a valid SPDX 2.3 JSON structure (`spdxVersion == "SPDX-2.3"`, `packages`, `relationships`).
3. **Detached Sigstore Bundle Verification**:
   - Verify `SigstoreBundleVerifier` accepts a valid synthetic Sigstore bundle matching an artifact's SHA-256 digest and rejects a tampered artifact or mismatched digest.
4. **CLI Integration & Domain Isolation**:
   - Verify `mcp-fingerprints export-sbom --passport <fixture> --format cyclonedx --output <tmp.json>` succeeds and that `ServerPackageSpec` in `models.py` retains strict domain isolation (`test_live_canonicalizer_snapshot_invariants.py`).

---

## 3. Non-Interactive Completion Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement all specified modules, workflow updates, CLI wiring, and unit tests autonomously. Run `pytest tests/test_sbom_exporter.py`, `pytest tests/test_live_canonicalizer_snapshot_invariants.py`, and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
