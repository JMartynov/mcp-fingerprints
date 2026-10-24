# Task 65 Technical Report: CycloneDX 1.6 AI-Tool SBOM Export & Sigstore Keyless Attestation

## Executive Summary
This report outlines the implementation and architectural decisions for Task 65, bringing the `mcp-fingerprints` catalog into compliance with enterprise supply-chain standards via CycloneDX 1.6 and SPDX 2.3 SBOM generation, along with detached Sigstore OIDC keyless attestation for release provenance.

## Architecture

### 1. `CycloneDXExporter` (SBOM Generation)
The exporter operates as an out-of-band module (`src/mcp_fingerprints/sbom_exporter.py`), taking in `ServerPackageSpec` objects to generate standards-compliant SBOM JSON payloads.

- **Component Mapping**: Root `ServerPackageSpec` components map to `type: "application"`, while internal `ToolContractSignature` elements within a `VersionFingerprint` map to nested `type: "library"` components.
- **PURL Mapping**: Derives valid Package URLs (`pkg:npm/...`, `pkg:pypi/...`, `pkg:cargo/...`, `pkg:golang/...`, `pkg:generic/...`) based on the ecosystem field.
- **Deterministic Serial Numbers**: A reproducible `serialNumber` (e.g. `urn:uuid:...`) is derived using UUIDv5 computed securely from a concatenation of canonical toolset hashes across all cataloged servers.
- **Safety Metadata**: MCP tool parameters such as `mcp:tool:name` and `mcp:tool:parameter_count` are propagated securely to the `properties` sub-element for nested tools.

### 2. `SigstoreBundleVerifier`
Implements offline cryptographic provenance verification without mutating the structural domain.

- Computes a live SHA-256 digest of an artifact (e.g. `passports.json.gz`).
- Parses `.sigstore.json` structured blobs (validating media types such as `application/vnd.dev.sigstore.bundle+json`).
- Checks internal structure (such as `messageSignature.messageDigest.hash` or `verificationMaterial`) against the live digest.
- Defers to the local `cosign verify-blob` CLI utility when `use_cosign_cli=True` is provided and the environment supports it.

### 3. CI/CD OIDC Integration
The GitHub Actions release workflow (`.github/workflows/release.yml`) was enhanced:
- `sigstore/cosign-installer@v3` action runs after Python wheel/sdist builds.
- Signs built distributions and `data/passports.json.gz` using keyless GitHub Actions OIDC identity (`cosign sign-blob --yes --bundle <artifact>.sigstore.json <artifact>`).
- Detached bundles are uploaded alongside artifacts.

## Findings & Risk Classifications

### High
* **Missing Tool Hashes**: Some older or dynamically crawled tools may lack `schema_hash` at runtime. The exporter calculates an ephemeral hash via `canonicalize_json` during SBOM emission, ensuring downstream engines don't break, while preventing direct state mutation inside `ServerPackageSpec`.

### Medium
* **PURL Ambiguity**: Certain generic ecosystems might lack unambiguous namespaces in Package URLs (e.g. Deno modules or direct GitHub URLs). We fallback to `pkg:generic/...` to maintain valid syntax, but downstream platforms might reject missing resolution metadata.

### Low
* **Cosign Binary Dependency**: Fully verified `SigstoreBundleVerifier` usage expects an external `cosign` binary on the host environment. When unavailable, it uses heuristic digest matching which is faster but delegates deep certificate ASN.1 chain parsing to external auditing processes.
