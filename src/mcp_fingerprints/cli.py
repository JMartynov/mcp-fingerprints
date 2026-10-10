"""CLI for MCP Fingerprint and Passport Knowledge Base."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path

from mcp_fingerprints.config_exporter import (
    export_all_client_configs,
    export_client_config,
)
from mcp_fingerprints.conflict_detector import audit_client_config, format_audit_report
from mcp_fingerprints.conflict_resolver import resolve_client_config
from mcp_fingerprints.drift_detector import (
    compare_passports_for_drift,
    dispatch_drift_webhook,
    format_drift_report,
)
from mcp_fingerprints.enricher import VulnerabilityEnricher
from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.models import ServerPackageSpec
from mcp_fingerprints.prober import McpStdioProber
from mcp_fingerprints.remediation_advisor import evaluate_client_config
from mcp_fingerprints.schema_validator import PassportSchemaValidator
from mcp_fingerprints.search import format_search_results, search_passports
from mcp_fingerprints.snapshot import build_snapshot
from mcp_fingerprints.synchronizer import PassportSynchronizer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("mcp_fingerprints.cli")


def print_ecosystem_health_report(data_dir: str | Path) -> None:
    passports = 0
    tools = 0
    ecosystems = Counter()

    dir_path = Path(data_dir)
    for j_file in sorted(dir_path.rglob("*.json")):
        if j_file.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
            continue
        try:
            content = json.loads(j_file.read_text(encoding="utf-8"))
            if isinstance(content, dict) and "package_name" in content:
                passports += 1
                ecosystems[content.get("ecosystem", "unknown")] += 1

                spec = ServerPackageSpec.from_dict(content)
                for v in spec.versions:
                    if v.tool_signatures:
                        tools += len(v.tool_signatures)
        except Exception:
            pass

    print("==================================================")
    print("         ECOSYSTEM HEALTH REPORT                  ")
    print("==================================================")
    print(f"Total Passports:    {passports}")
    print(f"Total Tools:        {tools}")
    print("Ecosystem Breakdown:")
    for eco, count in ecosystems.most_common():
        print(f"  - {eco}: {count}")
    print("==================================================")


def main() -> None:
    import mcp_fingerprints

    parser = argparse.ArgumentParser(
        description="MCP Fingerprint & Passport Knowledge Base CLI"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mcp-fingerprints {mcp_fingerprints.__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sync
    sync_p = subparsers.add_parser(
        "sync", help="Synchronize MCP server passports from registries"
    )
    sync_p.add_argument(
        "--output", default="data/fingerprints", help="Output directory"
    )
    sync_p.add_argument(
        "--update-existing",
        action="store_true",
        help="Check and update existing MCP versions",
    )
    sync_p.add_argument(
        "--discover-new", action="store_true", help="Discover and pull new MCP servers"
    )
    sync_p.add_argument(
        "--enrich-ast",
        action="store_true",
        help="Extract tool contracts via static AST parsing for zero-tool repositories",
    )
    sync_p.add_argument("--limit", type=int, default=500, help="Max passports to probe")
    sync_p.add_argument(
        "--workers", type=int, default=8, help="Concurrency worker threads"
    )
    sync_p.add_argument(
        "--report",
        action="store_true",
        help="Run and print the ecosystem health report after sync",
    )
    sync_p.add_argument(
        "--all", action="store_true", help="Run both update and discovery"
    )
    sync_p.add_argument(
        "--snapshot",
        action="store_true",
        default=True,
        help="Compile snapshot after sync",
    )
    sync_p.add_argument(
        "--probe-runtime",
        action="store_true",
        help="Probe safe servers via sandboxed stdio runtime handshake",
    )
    sync_p.add_argument(
        "--runtime-timeout",
        type=float,
        default=5.0,
        help="Per-server timeout in seconds for runtime handshake (default: 5.0)",
    )
    sync_p.add_argument(
        "--runtime-limit",
        type=int,
        default=50,
        help="Maximum servers to probe in runtime handshake (default: 50)",
    )

    # Match
    match_p = subparsers.add_parser(
        "match",
        help="Match observed runtime tools against the fingerprint knowledge base",
    )
    match_p.add_argument(
        "--input-file",
        "-i",
        default="-",
        help="Path to JSON file containing observed tools/manifest, or '-' for stdin",
    )
    match_p.add_argument(
        "--dir", default="data/fingerprints", help="Directory containing passport files"
    )
    match_p.add_argument(
        "--server-hint",
        help="Optional server name hint to guide candidate disambiguation",
    )
    match_p.add_argument(
        "--threshold",
        type=float,
        default=0.65,
        help="Minimum confidence threshold (0.0 to 1.0)",
    )
    match_p.add_argument(
        "--json", action="store_true", help="Output full match results as JSON"
    )

    # Probe
    probe_p = subparsers.add_parser(
        "probe",
        help="Probe a live MCP server over stdio, fingerprint it, and audit known vulnerabilities",
    )
    probe_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    probe_p.add_argument("--server-hint", help="Optional server name hint")
    probe_p.add_argument(
        "--threshold", type=float, default=0.65, help="Minimum confidence threshold"
    )
    probe_p.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Connection and RPC timeout in seconds",
    )
    probe_p.add_argument(
        "--json", action="store_true", help="Output full probe report as JSON"
    )
    probe_p.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="Server launch command and arguments (e.g. -- npx ...)",
    )

    # Enrich
    enrich_p = subparsers.add_parser(
        "enrich", help="Enrich passports with OSV vulnerability metadata"
    )
    enrich_p.add_argument(
        "--vulnerabilities",
        "-v",
        required=True,
        help="Path to vulnerabilities.json.gz or vulnerabilities.json",
    )
    enrich_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    enrich_p.add_argument(
        "--snapshot",
        action="store_true",
        default=True,
        help="Compile snapshot after enrichment",
    )

    # Validate
    val_p = subparsers.add_parser(
        "validate", help="Validate passport directory invariants"
    )
    val_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport directory to validate"
    )

    # Snapshot
    snap_p = subparsers.add_parser(
        "snapshot", help="Compile all passports into consolidated .json.gz"
    )
    snap_p.add_argument(
        "--data-dir", default="data/fingerprints", help="Passport data directory"
    )
    snap_p.add_argument(
        "--output-gz", default="passports.json.gz", help="Output gzip file path"
    )
    snap_p.add_argument(
        "--output-json", default=None, help="Optional uncompressed JSON output path"
    )

    # Build Index
    build_index_p = subparsers.add_parser(
        "build-index", help="Build semantic embeddings index"
    )
    build_index_p.add_argument(
        "--passports-dir",
        default="data/fingerprints",
        help="Path to passports directory",
    )
    build_index_p.add_argument(
        "--output", default="data/embeddings.npz", help="Path to output NPZ file"
    )

    # Search
    search_p = subparsers.add_parser(
        "search", help="Fuzzy search MCP servers by keyword or capability"
    )
    search_p.add_argument("query", help="Search query")
    search_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    search_p.add_argument(
        "--limit", type=int, default=10, help="Maximum results to return"
    )
    search_p.add_argument(
        "--semantic",
        action="store_true",
        help="Use semantic/embedding-based search (requires fastembed)",
    )

    # Browse (TUI)
    browse_p = subparsers.add_parser(
        "browse", help="Interactive TUI browser for the MCP catalog"
    )
    browse_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    browse_p.add_argument("--query", default="", help="Initial search query")

    # Export Config
    export_p = subparsers.add_parser(
        "export-config",
        help="Export client configuration (Claude/Cursor/Cline/Zed/Windsurf/Docker)",
    )
    export_p.add_argument("package", help="Package name to export configuration for")
    export_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    export_p.add_argument(
        "--client",
        choices=["claude", "cursor", "cline", "zed", "windsurf", "docker"],
        default="claude",
        help="Client type (claude, cursor, cline, zed, windsurf, docker)",
    )
    export_p.add_argument(
        "--all-clients",
        action="store_true",
        help="Export configuration for all supported clients",
    )

    # Audit Config
    audit_p = subparsers.add_parser(
        "audit-config",
        help="Audit MCP client configuration for tool collisions and security shadowing",
    )
    audit_p.add_argument(
        "config_file",
        help="Path to client config file (e.g. claude_desktop_config.json, settings.json)",
    )
    audit_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    audit_p.add_argument(
        "--json", action="store_true", help="Output audit report as JSON"
    )
    audit_p.add_argument(
        "--fix",
        action="store_true",
        help="Automatically remediate detected vulnerabilities and configuration risks",
    )
    audit_p.add_argument(
        "--strategy",
        choices=["upgrade", "replace", "all"],
        default="all",
        help="Remediation strategy to apply",
    )
    audit_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate fixes without writing changes to configuration file",
    )
    audit_p.add_argument(
        "--backup",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Create a backup copy before modifying configuration file",
    )

    # Fix Advisories
    fix_advisories_p = subparsers.add_parser(
        "fix-advisories",
        help="Automated Vulnerability Remediation Advisor for client configurations",
    )
    fix_advisories_p.add_argument(
        "config_file",
        help="Path to client config file (e.g. claude_desktop_config.json)",
    )
    fix_advisories_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    fix_advisories_p.add_argument(
        "--apply", action="store_true", help="Atomically update configuration file"
    )
    fix_advisories_p.add_argument(
        "--strategy",
        choices=["upgrade", "replace", "all"],
        default="all",
        help="Strategy to use for remediation (default: all)",
    )
    fix_advisories_p.add_argument(
        "--output", default=None, help="Output path for modified configuration file"
    )

    # Resolve Config
    resolve_p = subparsers.add_parser(
        "resolve-config", help="Automated conflict resolver and namespacing"
    )
    resolve_p.add_argument("config_file", help="Path to client config file")
    resolve_p.add_argument(
        "--strategy",
        choices=["prefix", "priority", "report"],
        default="prefix",
        help="Resolution strategy (prefix, priority, report)",
    )
    resolve_p.add_argument(
        "--output", help="Optional file path to output sanitized configuration"
    )
    resolve_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    resolve_p.add_argument(
        "--json", action="store_true", help="Output resolution result as JSON"
    )

    # Detect Drift
    drift_p = subparsers.add_parser(
        "detect-drift",
        help="Detect supply-chain tampering and hash drift between passport states",
    )
    drift_p.add_argument(
        "--old",
        required=True,
        help="Baseline passport directory, snapshot gz, or json file",
    )
    drift_p.add_argument(
        "--new", required=True, help="New passport directory, snapshot gz, or json file"
    )
    drift_p.add_argument(
        "--webhook-url", help="Webhook URL to notify upon drift or tamper"
    )
    drift_p.add_argument(
        "--fail-on-tamper",
        action="store_true",
        help="Exit with code 1 if tamper incidents are detected",
    )
    drift_p.add_argument(
        "--json", action="store_true", help="Output audit report as JSON"
    )
    drift_p.add_argument(
        "--output", help="Optional file path to write output drift report"
    )

    args = parser.parse_args()

    if args.command == "sync":
        sync = PassportSynchronizer(output_dir=args.output)
        if args.all or (
            not args.update_existing and not args.discover_new and not args.enrich_ast
        ):
            logger.info("Running full multi-source passport synchronization...")
            sync.update_existing_passports()
            sync.enrich_zero_tool_passports(limit=args.limit, max_workers=args.workers)
            sync.discover_new_mcps()
        else:
            if args.update_existing:
                sync.update_existing_passports()
            if args.enrich_ast:
                sync.enrich_zero_tool_passports(
                    limit=args.limit, max_workers=args.workers
                )
            if args.discover_new:
                sync.discover_new_mcps()

        if getattr(args, "probe_runtime", False):
            logger.info(
                "Probing runtime handshakes for up to %d safe servers...",
                args.runtime_limit,
            )
            probed = sync.probe_runtime_passports(
                limit=args.runtime_limit, timeout=args.runtime_timeout
            )
            logger.info("Successfully runtime-verified %d servers.", probed)

        if args.snapshot:
            logger.info("Compiling consolidated snapshot...")
            build_snapshot(
                data_dir=args.output,
                output_gz=f"{Path(args.output).parent}/passports.json.gz"
                if args.output != "data/fingerprints"
                else "passports.json.gz",
            )

        if getattr(args, "report", False):
            print_ecosystem_health_report(args.output)

    elif args.command == "validate":
        valid, invalid, errors = PassportSchemaValidator.validate_directory(args.dir)
        print(f"Validation summary: {valid} valid, {invalid} invalid passports.")
        if invalid > 0:
            for err in errors:
                print(f"ERROR: {err}")
            sys.exit(1)
        sys.exit(0)

    elif args.command == "snapshot":
        res = build_snapshot(
            data_dir=args.data_dir,
            output_gz=args.output_gz,
            output_json=args.output_json,
        )
        print(
            f"Compiled {res['total_passports']} passports ({res['size_kb']:.2f} KB) -> {res['snapshot_path']}"
        )

    elif args.command == "match":
        matcher = FingerprintMatcher()
        indexed_count = matcher.load_from_directory(args.dir)
        logger.debug("Indexed %d passports for matching", indexed_count)

        if args.input_file == "-" or not args.input_file:
            raw_data = sys.stdin.read()
        else:
            raw_data = Path(args.input_file).read_text(encoding="utf-8")

        parsed = json.loads(raw_data) if raw_data.strip() else {}
        if isinstance(parsed, dict):
            tools = parsed.get("tools") or []
            prompts = parsed.get("prompts")
            resources = parsed.get("resources")
        elif isinstance(parsed, list):
            tools = parsed
            prompts = None
            resources = None
        else:
            tools = []
            prompts = None
            resources = None

        match_res = matcher.match(
            tools=tools,
            prompts=prompts,
            resources=resources,
            server_name_hint=args.server_hint,
            min_confidence_threshold=args.threshold,
        )

        if args.json:
            print(json.dumps(match_res.to_dict(), indent=2))
        else:
            print("==================================================")
            print("         MCP FINGERPRINT MATCH REPORT             ")
            print("==================================================")
            print(f"Matched:            {match_res.matched}")
            if match_res.matched:
                print(f"Package:            {match_res.package_name}")
                print(f"Version:            {match_res.matched_version}")
                print(f"PURL:               {match_res.purl}")
                print(f"Confidence:         {match_res.confidence_score * 100:.1f}%")
                print(f"Match Layer:        {match_res.match_layer}")
                print(f"Topology Score:     {match_res.layer2_topology_score:.2f}")
                print(f"Capability Score:   {match_res.layer3_capability_score:.2f}")
                print(
                    f"Matched Tools:      {match_res.matched_tool_count} / {match_res.total_observed_tools}"
                )
                if match_res.unmatched_observed_tools:
                    print(
                        f"Unmatched Tools:    {', '.join(match_res.unmatched_observed_tools)}"
                    )
                if match_res.missing_expected_tools:
                    print(
                        f"Missing Tools:      {', '.join(match_res.missing_expected_tools)}"
                    )
            else:
                print(f"Confidence:         {match_res.confidence_score * 100:.1f}%")
                print(
                    f"Reason:             No candidate passport met threshold >= {args.threshold}"
                )
            print("==================================================")

    elif args.command == "probe":
        cmd = args.cmd
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        if not cmd:
            print(
                "ERROR: No server command specified. Usage: mcp-fingerprints probe -- <command> [args...]"
            )
            sys.exit(1)

        matcher = FingerprintMatcher()
        matcher.load_from_directory(args.dir)
        prober = McpStdioProber(matcher)

        report = prober.probe(
            command=cmd,
            timeout=args.timeout,
            server_name_hint=args.server_hint,
            min_confidence_threshold=args.threshold,
        )

        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print("==================================================")
            print("         LIVE MCP SERVER AUDIT REPORT             ")
            print("==================================================")
            print(f"Command:            {' '.join(report.server_command)}")
            print(
                f"Connection:         {'SUCCESS' if report.connection_successful else 'FAILED'}"
            )
            if report.error:
                print(f"Error:              {report.error}")
            print(f"Observed Tools:     {len(report.tools_observed)}")
            print(f"Observed Prompts:   {len(report.prompts_observed)}")
            print(f"Observed Resources: {len(report.resources_observed)}")
            print("--------------------------------------------------")
            if report.match_result and report.match_result.matched:
                print(f"Identified Package: {report.match_result.package_name}")
                print(f"Identified Version: {report.match_result.matched_version}")
                print(
                    f"Confidence:         {report.match_result.confidence_score * 100:.1f}% ({report.match_result.match_layer})"
                )
                print("--------------------------------------------------")
                if report.is_vulnerable:
                    print("SECURITY STATUS:    ⚠️  VULNERABLE")
                    print(f"Max CVSS Score:     {report.max_cvss_score:.1f}")
                    if report.recommended_fixed_version:
                        print(
                            f"Recommended Fix:    Upgrade to >= {report.recommended_fixed_version}"
                        )
                    print(f"Active Advisories:  {len(report.active_advisories)}")
                    for adv in report.active_advisories:
                        print(
                            f"  - [{adv['severity']}] {adv['id']}: {adv.get('summary', '')}"
                        )
                else:
                    print(
                        "SECURITY STATUS:    ✅ CLEAN (No known CVEs affecting this version)"
                    )
            else:
                print("Identified Package: UNKNOWN (Confidence below threshold)")
            print("==================================================")

    elif args.command == "enrich":
        enricher = VulnerabilityEnricher(args.vulnerabilities)
        total, with_vulns = enricher.enrich_directory(args.dir)
        print(
            f"Enrichment summary: {total} passports audited, {with_vulns} enriched with known vulnerabilities."
        )
        if args.snapshot:
            logger.info("Compiling snapshot with enriched security profiles...")
            snap_path = (
                f"{Path(args.dir).parent}/passports.json.gz"
                if args.dir != "data/fingerprints"
                else "passports.json.gz"
            )
            build_snapshot(data_dir=args.dir, output_gz=snap_path)

    elif args.command == "build-index":
        script_path = (
            Path(__file__).parent.parent.parent / "scripts" / "build_semantic_index.py"
        )
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "build_semantic_index", script_path
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                module.build_index(args.passports_dir, args.output)
            except ImportError as e:
                print(f"Error: {e}")
                sys.exit(1)
            except Exception as e:
                print(f"Error building index: {e}")
                sys.exit(1)
        else:
            print(f"Error: Could not load {script_path}")
            sys.exit(1)

    elif args.command == "search":
        if getattr(args, "semantic", False):
            from mcp_fingerprints.semantic_search import semantic_search

            index_path = Path("data/embeddings.npz")
            if index_path.exists():
                print("Using pre-computed semantic index.", file=sys.stderr)
            results = semantic_search(
                args.query, args.dir, top_k=args.limit, index_path=index_path
            )
        else:
            results = search_passports(args.dir, args.query, args.limit)
        print(format_search_results(results))

    elif args.command == "export-config":
        import urllib.parse

        urllib.parse.quote_plus(args.package).replace("%40", "@")

        # In actual structure it looks like dir / package_name.json but slashes are replaced by _
        # Usually it's purl or name - let's search for package_name
        found = False
        for j_file in Path(args.dir).rglob("*.json"):
            if j_file.name in (
                "sync_state.json",
                "index.json",
                ".passport_index.pickle",
            ):
                continue
            try:
                content = json.loads(j_file.read_text(encoding="utf-8"))
                if content.get("package_name") == args.package:
                    if args.all_clients:
                        configs = export_all_client_configs(content)
                        print(json.dumps(configs, indent=2))
                    else:
                        config = export_client_config(content, client=args.client)
                        print(json.dumps(config, indent=2))
                    found = True
                    break
            except Exception:
                pass

        if not found:
            print(f"ERROR: Package '{args.package}' not found in passports.")
            sys.exit(1)

    elif args.command == "browse":
        if not sys.stdin.isatty():
            print("Interactive TUI requires a TTY. Exiting cleanly.")
            sys.exit(0)
        from mcp_fingerprints.tui import run_tui

        try:
            run_tui(Path(args.dir), args.query)
        except Exception as e:  # noqa: BLE001
            logger.error("TUI exited with error: %s", e)
            sys.exit(1)

    elif args.command == "resolve-config":
        try:
            result = resolve_client_config(
                config_path=args.config_file,
                strategy=args.strategy,
                output_path=args.output,
                passports_dir=args.dir,
            )
        except Exception as e:
            logger.error("Failed to resolve configuration conflicts: %s", e)
            print(f"ERROR: {e}")
            sys.exit(1)

        if args.json:
            print(json.dumps(result.resolved_config, indent=2))
        else:
            print("==================================================")
            print("         MCP CONFLICT RESOLUTION REPORT           ")
            print("==================================================")
            print(f"Strategy used:      {result.strategy_used}")
            print(f"Modifications made: {len(result.modifications_made)}")
            for mod in result.modifications_made:
                print(f"  - {mod}")

            if not result.audit_report.is_clean and result.strategy_used == "report":
                print("\nAudit Report Summary:")
                print(format_audit_report(result.audit_report))

            print("==================================================")
            if not args.output:
                print("\nResolved Config Preview:")
                print(json.dumps(result.resolved_config, indent=2))

    elif args.command == "audit-config":
        try:
            report = audit_client_config(args.config_file, passports_dir=args.dir)
        except Exception as e:
            logger.error("Failed to audit configuration: %s", e)
            print(f"ERROR: {e}")
            sys.exit(1)

        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(format_audit_report(report))

        if not args.fix:
            if report.has_critical_conflicts:
                sys.exit(1)
        else:
            print("\n==================================================")
            print("     MCP VULNERABILITY REMEDIATION REPORT         ")
            print("==================================================")

            try:
                rem_report = evaluate_client_config(
                    config_path=args.config_file,
                    passport_dir=args.dir,
                )
            except Exception as e:
                logger.error("Failed to evaluate configuration for remediation: %s", e)
                print(f"ERROR: {e}")
                sys.exit(1)

            if rem_report.is_clean:
                print("No vulnerabilities detected in configuration.")
                sys.exit(0)

            print(f"Total unremediated packages: {rem_report.unremediated_count}")
            print(f"Total remediations proposed: {len(rem_report.actions)}")

            for action in rem_report.actions:
                print(f"\nPackage: {action.package_name}@{action.current_version}")
                print(f"  CVEs: {', '.join(action.cve_list)}")
                if action.action_type == "none":
                    print("  Action: NO REMEDIATION AVAILABLE")
                elif action.action_type == "upgrade":
                    if args.strategy in ("all", "upgrade"):
                        print(f"  Action: UPGRADE to {action.target_version}")
                    else:
                        print("  Action: UPGRADE available, but ignored by strategy")
                elif action.action_type == "replace":
                    if args.strategy in ("all", "replace"):
                        print(
                            f"  Action: REPLACE with {action.target_package}@{action.target_version} (Similarity: {action.similarity_score:.2f})"
                        )
                    else:
                        print("  Action: REPLACE available, but ignored by strategy")

            if args.dry_run:
                print("\n[Dry Run] Remediations previewed successfully. No changes written to file.")
            else:
                p = Path(args.config_file)
                if getattr(args, "backup", False):
                    import shutil
                    backup_path = p.with_name(f"{p.name}.bak")
                    shutil.copy2(p, backup_path)
                    print(f"\nBackup created at {backup_path}")

                from mcp_fingerprints.remediation_advisor import apply_remediation_patch
                raw_text = p.read_text(encoding="utf-8")
                patched_text = apply_remediation_patch(raw_text, rem_report, args.strategy)
                
                p.write_text(patched_text, encoding="utf-8")
                print(f"\nConfiguration updated at {p}")

            if rem_report.unremediated_count > 0 or any(
                a.action_type == "none"
                or (a.action_type == "upgrade" and args.strategy == "replace")
                or (a.action_type == "replace" and args.strategy == "upgrade")
                for a in rem_report.actions
            ):
                sys.exit(1)

    elif args.command == "fix-advisories":
        try:
            report = evaluate_client_config(
                config_path=args.config_file,
                passport_dir=args.dir,
            )
        except Exception as e:
            logger.error("Failed to audit configuration: %s", e)
            print(f"ERROR: {e}")
            sys.exit(1)

        print("==================================================")
        print("     MCP VULNERABILITY REMEDIATION REPORT         ")
        print("==================================================")

        if report.is_clean:
            print("No vulnerabilities detected in configuration.")
            sys.exit(0)

        print(f"Total unremediated packages: {report.unremediated_count}")
        print(f"Total remediations proposed: {len(report.actions)}")

        for action in report.actions:
            print(f"\nPackage: {action.package_name}@{action.current_version}")
            print(f"  CVEs: {', '.join(action.cve_list)}")
            if action.action_type == "none":
                print("  Action: NO REMEDIATION AVAILABLE")
            elif action.action_type == "upgrade":
                if args.strategy in ("all", "upgrade"):
                    print(f"  Action: UPGRADE to {action.target_version}")
                else:
                    print("  Action: UPGRADE available, but ignored by strategy")
            elif action.action_type == "replace":
                if args.strategy in ("all", "replace"):
                    print(
                        f"  Action: REPLACE with {action.target_package}@{action.target_version} (Similarity: {action.similarity_score:.2f})"
                    )
                else:
                    print("  Action: REPLACE available, but ignored by strategy")

        if args.apply:
            p = Path(args.config_file)
            from mcp_fingerprints.remediation_advisor import apply_remediation_patch
            raw_text = p.read_text(encoding="utf-8")
            patched_text = apply_remediation_patch(raw_text, report, args.strategy)

            out_path = Path(args.output) if args.output else p
            out_path.write_text(patched_text, encoding="utf-8")
            print(f"\nConfiguration updated at {out_path}")

        if report.unremediated_count > 0 or any(
            a.action_type == "none"
            or (a.action_type == "upgrade" and args.strategy == "replace")
            or (a.action_type == "replace" and args.strategy == "upgrade")
            for a in report.actions
        ):
            sys.exit(1)

    elif args.command == "detect-drift":
        try:
            report = compare_passports_for_drift(args.old, args.new)
        except Exception as e:
            logger.error("Failed to compare passports for drift: %s", e)
            print(f"ERROR: {e}")
            sys.exit(1)

        if (
            args.webhook_url
            or os.environ.get("SECURITY_WEBHOOK_URL")
            or os.environ.get("WEBHOOK_URL")
        ):
            dispatch_drift_webhook(report, webhook_url=args.webhook_url)

        out_content = ""
        if args.json:
            out_content = json.dumps(report.to_dict(), indent=2)
            print(out_content)
        else:
            out_content = format_drift_report(report)
            print(out_content)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out_content)

        if args.fail_on_tamper and report.has_tamper_incidents:
            sys.exit(1)


if __name__ == "__main__":
    main()
