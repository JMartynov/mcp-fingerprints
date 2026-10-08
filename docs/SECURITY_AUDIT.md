# MCP Fingerprints: Security Architecture & Auditing

The MCP Fingerprints platform is designed not just to extract and catalog Model Context Protocol (MCP) tool contracts, but to provide a robust security auditing layer (Verity Red-Team). This document details our architecture for extracting metadata safely, analyzing the risk profile of tools, sandboxing execution environments, and tracking the lifecycle of upstream packages.

## 1. Multi-Language AST Extraction Coverage

To safely parse source code from untrusted upstream packages, we rely exclusively on static Abstract Syntax Tree (AST) analysis. This ensures we never execute potentially malicious code during the crawling and extraction phase.

Our parser implementations target a zero-eval, zero-import execution profile, currently spanning the following ecosystems:

* **TypeScript/JavaScript**: Static traversal of NPM packages, targeting popular tooling like `zod` schema definitions.
* **Python**: Strict use of `ast.parse()` to extract tool signatures and `@tool` decorators without loading modules into the runtime.
* **Go & Rust**: Parsing of exported structs and function signatures in strongly-typed ecosystems.
* **JVM & .NET**: Scanning compiled bytecodes/IL or source annotations to rebuild the schema representation.

By reading files strictly as data rather than executing them, we defend against supply-chain attacks attempting to execute code upon import.

## 2. Tool Parameter Risk Indicators

Not all MCP tools present the same risk. We automatically evaluate tools and assign a risk tier based on their capabilities and parameter surface area.

* **Critical**: Tools that present immediate system compromise risks.
  * Indicators: Commands containing `bash`, `exec`, `shell`, `system`, or unbounded file writes.
* **High**: Tools with broad access to sensitive data or the local network.
  * Indicators: `sql`, `query`, URL endpoints permitting potential Server-Side Request Forgery (SSRF), or functions reading arbitrary environment variables.
* **Medium**: Scoped utilities that can read or write files, but are constrained to specific directories or operations.
  * Indicators: File path operations, controlled external API connections.
* **Low**: Immutable or read-only tools.
  * Indicators: Pure computations, tightly validated inputs with constrained enum types, safe string manipulations.

We emphasize parameter injection defenses—ensuring schemas tightly constrain inputs (e.g., regex patterns, max lengths, enums) before they ever reach the underlying execution engine.

## 3. Sandboxed Stdio Runtime Handshake Methodology

For closed-source binaries or compiled MCP servers, static AST parsing is not possible. In these scenarios, we must initialize the server to perform the standard MCP handshake and request the tool list directly. This presents an enormous risk if not handled correctly.

Our Sandboxed Runtime Methodology employs a strict "zero trust" execution profile:

1. **Environment Sanitization**: Before execution, the environment is stripped of all sensitive host variables. We actively filter out:
   * Cloud credentials: `AWS_*`, `GCP_*`, `AZURE_*`
   * API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`
   * System auth: `SSH_*`
2. **Execution via stdio**: Servers are executed using standard input/output (stdio) streams rather than exposing a network port (SSE/HTTP), significantly reducing the potential attack surface.
3. **Execution Context**: The process is isolated. No network egress is permitted by default.
4. **Immediate Termination**: Once the `initialize` handshake completes and the `tools/list` request is fulfilled, the process is forcefully terminated. We never leave idle servers running.

## 4. 404 Tombstoning & Supply-Chain Deprecation

In the fast-moving AI ecosystem, repositories change owners, packages are deleted, and malicious actors sometimes perform typosquatting or package hijacking. Our daily sync explicitly tracks these lifecycle events.

* **Tombstoning**: If a previously indexed package returns a 404 from a registry (NPM, PyPI, Smithery), we mark it as `tombstoned`. We *do not* immediately delete the historical signature. This preserves a historical record of what the package *was* doing before it disappeared.
* **Hash Fingerprints**: We maintain strict SHA-256 hashes of the tool schemas. If an upstream server drastically changes its tool output between versions, the fingerprint mismatch immediately triggers an audit alert.
* **Supply-Chain Deprecation Tracking**: Packages that are marked as deprecated upstream are explicitly flagged in our data feeds, ensuring clients using `mcp_fingerprints.cli export-config` are warned before integrating potentially abandoned servers.
