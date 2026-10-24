"""Public exports for the MCP Structural Fingerprint Knowledge Base & Matcher."""

from __future__ import annotations

from mcp_fingerprints.canonicalizer import (
    build_version_fingerprint,
    compute_sha256,
    compute_toolset_canonical_hash,
    extract_tool_signature,
)
from mcp_fingerprints.crawler import FingerprintGenerator
from mcp_fingerprints.distance import (
    compute_capability_similarity,
    compute_tool_topology_similarity,
    compute_version_topology_similarity,
    jaccard_similarity,
)
from mcp_fingerprints.config_scanner import ConfigScanner, LocalInventoryReport
from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.models import (
    FingerprintMatchResult,
    PromptSignature,
    ResourceSignature,
    ServerPackageSpec,
    ToolContractSignature,
    VersionFingerprint,
)
from mcp_fingerprints.snapshot_diff import compare_snapshots, InventorySnapshot
from mcp_fingerprints.sbom_exporter import SBOMFormat, CycloneDXExporter, SigstoreBundleVerifier, AttestationVerificationResult
from mcp_fingerprints.sanitizer import sanitize_unicode_text, sanitize_metadata, sanitize_tool_definition
from mcp_fingerprints.data_loader import get_passports_path, load_passports
from mcp_fingerprints.installer import ClientInstaller, DockerSandboxBuilder, InstallPlan, SandboxMode, NetworkPolicy
from mcp_fingerprints.policy_exporter import (
    PolicyExporter,
    PolicyFormat,
    PolicyMode,
    RegoPolicyCompiler,
    EnvoyWasmConfigCompiler,
)

from mcp_fingerprints.fuzzer import (
    PayloadCategory,
    FuzzOutcome,
    PayloadMutator,
    FuzzCaseResult,
    FuzzReport,
    SchemaDrivenFuzzer,
)


__version__ = "1.0.19"

from mcp_fingerprints.prober import McpProber, ProbeReport

class McpIdentifier:
    """Top-level unified MCP identifier for stdio and HTTP."""
    def __init__(self, passports_dir: str | Path | None = None):
        from mcp_fingerprints.matcher import FingerprintMatcher
        from pathlib import Path
        
        self.matcher = FingerprintMatcher()
        if passports_dir:
            p = Path(passports_dir)
            if p.is_dir():
                self.matcher.load_from_directory(p)
            else:
                self.matcher.load_from_snapshot(p)
        else:
            try:
                self.matcher.load_default(download_if_missing=False)
            except Exception:
                pass
        self.prober = McpProber(self.matcher)

def identify_stdio(command: list[str], timeout: float = 10.0, passports_dir: str | None = None, **kwargs) -> ProbeReport:
    """Identify a local subprocess over stdio."""
    identifier = McpIdentifier(passports_dir)
    return identifier.prober.probe(target=command, timeout=timeout, **kwargs)

def identify_http(url: str, headers: dict[str, str] | None = None, timeout: float = 10.0, passports_dir: str | None = None, **kwargs) -> ProbeReport:
    """Identify a remote server over HTTP/SSE."""
    identifier = McpIdentifier(passports_dir)
    return identifier.prober.probe(target=url, headers=headers, timeout=timeout, **kwargs)

def scan_local_configs(probe_live: bool = True, scan_global: bool = True, custom_clients_path: str | None = None) -> LocalInventoryReport:
    """Scans all standard system paths for known MCP client configurations."""
    scanner = ConfigScanner()
    return scanner.scan(probe_live=probe_live, scan_global=scan_global, custom_clients_path=custom_clients_path)

def scan_config_file(path, probe_live: bool = True) -> LocalInventoryReport:
    """Scans a single configuration file."""
    from pathlib import Path
    scanner = ConfigScanner()
    return scanner.scan_file(Path(path), probe_live=probe_live)

__all__ = [
    "compare_snapshots",
    "InventorySnapshot",
    "McpIdentifier",
    "identify_stdio",
    "identify_http",
    "FingerprintGenerator",
    "FingerprintMatchResult",
    "FingerprintMatcher",
    "PromptSignature",
    "ResourceSignature",
    "ServerPackageSpec",
    "ToolContractSignature",
    "VersionFingerprint",
    "build_version_fingerprint",
    "compute_capability_similarity",
    "compute_sha256",
    "compute_tool_topology_similarity",
    "compute_toolset_canonical_hash",
    "compute_version_topology_similarity",
    "extract_tool_signature",
    "jaccard_similarity",
    "ConfigScanner",
    "LocalInventoryReport",
    "scan_local_configs",
    "scan_config_file",
    "SBOMFormat",
    "CycloneDXExporter",
    "SigstoreBundleVerifier",
    "AttestationVerificationResult",
    "sanitize_unicode_text",
    "sanitize_metadata",
    "sanitize_tool_definition",
    "get_passports_path",
    "load_passports",
    "ClientInstaller",
    "DockerSandboxBuilder",
    "InstallPlan",
    "SandboxMode",
    "NetworkPolicy",
    "PolicyExporter",
    "PolicyFormat",
    "PolicyMode",
    "RegoPolicyCompiler",
    "EnvoyWasmConfigCompiler",
    "PayloadCategory",
    "FuzzOutcome",
    "PayloadMutator",
    "FuzzCaseResult",
    "FuzzReport",
    "SchemaDrivenFuzzer",
]
