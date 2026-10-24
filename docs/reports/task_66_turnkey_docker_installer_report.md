# Task 66: Turnkey Docker-Sandboxed Server Installer Report

## Overview

As identified in the ecosystem gap analysis and benchmark report, `mcp-fingerprints` historically excelled in scanning and analyzing MCP configurations across developer workstations (such as Claude Desktop, Cursor, and Zed), but lacked the mechanism to immediately distribute and execute those tools in an isolated sandbox. This gap required manual configuration patching and system environment manipulation on the user's end.

Task 66 rectifies this by integrating a Turnkey Installer (`mcp-fingerprints install`) into the `mcp-fingerprints` CLI suite. This feature resolves standard `ServerPackageSpec` passports into directly executable endpoints, injecting configurations dynamically into supported IDEs while maintaining the integrity of original user settings and comments.

## Architecture

The installer architecture leverages three primary components:

1.  **`DockerSandboxBuilder`:** Given a known `ServerPackageSpec`, this builder abstracts the complex logic of constructing least-privilege Docker runtime commands. It interprets the ecosystem (npm, pypi, or native docker) to select an appropriate lightweight base image (`node:20-alpine`, `uv:python3.12-alpine`, etc.). When running in `--sandbox docker`, the builder strictly enforces:
    *   **Network Isolation:** (`--network none`) ensures the server cannot communicate with external services if unneeded.
    *   **Filesystem Constraints:** Read-only mode (`--read-only`) with a volatile `tmpfs` limits persistent storage writes.
    *   **Privilege Dropping:** Appending `--cap-drop=ALL` and `--security-opt=no-new-privileges`.

2.  **`ClientInstaller`:** Handles resolution of target tools and orchestrates the patching of the configuration into the target CLI tools or IDEs (like Claude, Cursor, Windsurf, Zed, and Cline). By extracting environmental requirements and run commands using `DockerSandboxBuilder`, the installer abstracts deployment friction.

3.  **`config_exporter.py` Integration:** Uses lossless JSONC parsing via regex-based `patch_jsonc`. Standard JSON manipulation tools rewrite the entire DOM, dropping `//` and `/* */` comments common in configurations like `settings.json`. The string-injection mechanism protects unrelated configuration directives and developer notes.

## Ecosystem Gap Closure (Competitive Benchmarking)

*   **Compared to Smithery:** While `@smithery/cli install` overwrites target `mcpServers` settings directly via basic JSON stringification, `mcp-fingerprints` safely injects configurations and preserves pre-existing comments. It also enables explicit docker sandboxing instead of relying purely on remote hosted proxies or raw host execution.
*   **Compared to Docker MCP Toolkit:** While Docker's solution requires a UI to click and install desktop extensions, this approach unifies multi-agent workstation targeting directly from a terminal command, generating hardened ephemeral container arguments natively rather than abstracting them purely within Docker Desktop logic.

## Engineering Findings & Quality Assurance

### High Findings
*   **Automated Environmental Overrides:** Hardened ephemeral Docker commands (`--cap-drop=ALL`, `--network none`) significantly limit execution capabilities for untrusted code execution scenarios.

### Medium Findings
*   **Missing Sandbox Fallbacks on Unsupported Ecosystems:** If a `ServerPackageSpec` explicitly declares an unmapped ecosystem (e.g., `cargo` or `go`), the `DockerSandboxBuilder` currently falls back to `alpine:latest`. This might cause runtime failures if the executable assumes dependencies pre-packaged in those images. A future patch should align Rust/Go ecosystems to specific scratch/slim images.
*   **Start-up Command Extraction:** When `sandbox == SandboxMode.NONE`, the system relies on hard-coded `npx` and `uvx` overrides instead of parsing raw `startup_command` directives from alternative environments (e.g., custom `.sh` bootstrap scripts), requiring downstream IDE validation.

### Low Findings
*   **Default Target Behavior:** The CLI defaults to `all` clients if no specific client is passed. This may clutter configurations if developers use only one primary IDE but keep several installed. The dry-run feature adequately surfaces this context for the user before execution.
*   **Dry-Run Iterator Re-Read Issue:** When running `--dry-run` and defaulting to `--client all` concurrently with an explicit `--config-path`, the configuration iterator repeatedly reads the original unmodified content from disk, so the output log might only highlight the final operation rather than cumulating updates correctly in the preview buffer.

## Conclusion

The Turnkey Docker-Sandboxed Installer transforms `mcp-fingerprints` from a passive detection and analysis registry into an active deployment utility. By bringing secure containerization defaults natively to the installation command, the user is safeguarded by default against unintended execution access from untrusted MCP tools.
