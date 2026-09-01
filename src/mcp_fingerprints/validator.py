"""Strict validator to verify whether a package is a genuine Model Context Protocol (MCP) server."""

from __future__ import annotations

import re

# Official namespaces and organizations
OFFICIAL_SCOPES = {
    "@modelcontextprotocol",
    "modelcontextprotocol",
    "smithery-ai",
}

# Known core MCP SDK dependencies across ecosystems
CORE_MCP_DEPENDENCIES = {
    "@modelcontextprotocol/sdk",
    "@modelcontextprotocol/ext-apps",
    "@modelcontextprotocol/client",
    "@modelcontextprotocol/server",
    "mcp",
    "mcp-server",
    "fastmcp",
    "fastmcp-slim",
    "langchain-mcp",
    "mcp-proxy",
}

# False-positive blacklisted keywords (e.g. Minecraft modding, MS Certs)
FALSE_POSITIVE_KEYWORDS = {
    "minecraft",
    "modpack",
    "minecraft-forge",
    "minecraft forge",
    "fabricmc",
    "spigotmc",
    "bukkit",
    "microsoft certified",
    "music coprocessor",
    "media control protocol",
}


class McpServerValidator:
    """Deterministic validation rules to distinguish genuine MCP servers from false positives."""

    @classmethod
    def is_valid_mcp_server(
        cls,
        package_name: str,
        ecosystem: str,
        dependencies: list[str] | dict[str, str] | None = None,
        keywords: list[str] | None = None,
        description: str | None = None,
        has_tools_declared: bool = False,
        is_curated_source: bool = False,
    ) -> tuple[bool, str]:
        """Evaluate whether a package is genuinely an MCP server.

        Returns (is_valid, reason).
        """
        pkg_lower = package_name.lower().strip()
        desc_lower = (description or "").lower()
        kws = [k.lower() for k in (keywords or [])]

        # 1. Reject explicit false-positive domains
        for bad_kw in FALSE_POSITIVE_KEYWORDS:
            if bad_kw in desc_lower or any(bad_kw in k for k in kws) or bad_kw in pkg_lower:
                return False, f"rejected: matched false-positive keyword '{bad_kw}'"

        # 2. Official organization scope rule
        for scope in OFFICIAL_SCOPES:
            if pkg_lower.startswith(f"{scope}/") or pkg_lower == scope:
                return True, f"approved: official scope '{scope}'"

        # 3. Core SDK dependency rule (highest confidence)
        dep_names: set[str] = set()
        if isinstance(dependencies, dict):
            dep_names = {k.lower() for k in dependencies}
        elif isinstance(dependencies, list):
            for d in dependencies:
                # Handle PEP 508 dependency strings (e.g. "fastmcp>=0.1.0")
                m = re.match(r"^([a-zA-Z0-9_\-/@]+)", d)
                if m:
                    dep_names.add(m.group(1).lower())

        for core_dep in CORE_MCP_DEPENDENCIES:
            if core_dep.lower() in dep_names:
                return True, f"approved: core MCP SDK dependency '{core_dep}'"

        # 4. Declared tools contract rule (e.g. Smithery or MCP JSON-RPC schemas)
        if has_tools_declared:
            return True, "approved: declared valid MCP tool contracts"

        # 5. Exact semantic phrase rule
        if "model context protocol" in desc_lower or "model context protocol" in " ".join(kws):
            return True, "approved: explicit 'model context protocol' semantic declaration"

        if ("mcp server" in desc_lower or "mcp server" in " ".join(kws)) and (
            "server" in pkg_lower or "mcp" in pkg_lower
        ):
            return True, "approved: explicit 'mcp server' keyword match"

        # 6. Curated directory approval (for awesome-mcp-servers community catalog)
        if is_curated_source:
            return True, "approved: curated community MCP catalog"

        return False, "rejected: missing core MCP SDK dependency or structural proof"
