"""CLI for MCP Fingerprint and Passport Knowledge Base."""
from __future__ import annotations
from pathlib import Path


import argparse
import json
import logging
import os
import sys
from collections import Counter

from mcp_fingerprints.config_exporter import (
    export_all_client_configs,
    export_client_config,
)
from mcp_fingerprints.drift_detector import (
    compare_passports_for_drift,
    dispatch_drift_webhook,
    format_drift_report,
)
from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.models import ServerPackageSpec
from mcp_fingerprints.prober import McpProber
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

    if len(sys.argv) == 1 and sys.stdin.isatty():
        from mcp_fingerprints.hub import run_interactive_hub
        run_interactive_hub()
        return

    parser = argparse.ArgumentParser(
        description="MCP Fingerprint & Passport Knowledge Base CLI"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mcp-fingerprints {mcp_fingerprints.__version__}",
    )
    
    # Check if there's no command and not a tty
    if len(sys.argv) == 1 and not sys.stdin.isatty():
        parser.print_help()
        sys.exit(0)

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Hub
    subparsers.add_parser(
        "interactive", aliases=["hub"], help="Launch Interactive MCP Command Hub"
    )

    # Init
    subparsers.add_parser(
        "init", help="Run interactive setup wizard to bootstrap configuration"
    )

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
        "--docker", action="store_true", help="Include Docker Hub discovery"
    )
    sync_p.add_argument(
        "--polyglot", action="store_true", help="Include Polyglot (Rust/Go) discovery"
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
    sync_p.add_argument(
        "--time-budget",
        type=int,
        default=2400,
        help="Time budget in seconds for the sync process (default: 2400, 0 = unlimited)",
    )
    sync_p.add_argument(
        "--ignore-checkpoint",
        action="store_true",
        help="Ignore any existing checkpoint and start from the beginning",
    )
    sync_p.add_argument(
        "--clear-checkpoint",
        action="store_true",
        help="Clear any existing checkpoint and start from the beginning",
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
        help="Probe a live MCP server over stdio, extract signatures, and match against passport knowledge base",
    )
    probe_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    probe_p.add_argument(
        "--url", help="HTTP/HTTPS endpoint URL to probe (alternative to stdio command)"
    )
    probe_p.add_argument(
        "--header",
        action="append",
        help="Custom HTTP header in 'Key: Value' format (can be specified multiple times)",
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
        "--json",
        action="store_true",
        help="Output full probe report as JSON (deprecated, use --format json)",
    )
    probe_p.add_argument(
        "--format",
        "-f",
        choices=["short", "long", "table", "json"],
        default="long",
        help="Output format",
    )
    probe_p.add_argument(
        "-s", "--short", action="store_true", help="Shortcut for --format short"
    )
    probe_p.add_argument(
        "-l", "--long", action="store_true", help="Shortcut for --format long"
    )
    probe_p.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="Server launch command and arguments (e.g. -- npx ...)",
    )

    # Validate
    val_p = subparsers.add_parser(
        "validate", help="Validate passport directory invariants"
    )
    val_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport directory to validate"
    )
    val_p.add_argument(
        "--no-cache", action="store_true", help="Disable caching and force revalidation"
    )
    val_p.add_argument(
        "--workers", type=int, default=None, help="Number of parallel worker processes"
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
    export_p.add_argument(
        "package", nargs="?", help="Package name to export configuration for"
    )
    export_p.add_argument(
        "--dir", default="data/fingerprints", help="Passport data directory"
    )
    export_p.add_argument(
        "--target",
        choices=["claude", "cursor", "cline", "zed", "windsurf", "docker"],
        help="Client type (alias for --client)",
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
    export_p.add_argument(
        "--config", help="Path to config file to patch (JSONC supported)"
    )
    export_p.add_argument(
        "--server", help="Server name/alias (overrides package name for config key)"
    )

    # Validate Protocol
    validate_p = subparsers.add_parser(
        "validate-protocol", help="Validate server JSON-RPC 2.0 and MCP Protocol conformance"
    )
    validate_p.add_argument(
        "server_command", nargs="+", help="Server command to run"
    )

    # Detect
    detect_p = subparsers.add_parser(
        "detect", help="Generic MCP Server Detection"
    )
    detect_p.add_argument(
        "target", nargs="+", help="URL or Server command to probe"
    )
    detect_p.add_argument(
        "--transport", choices=["stdio", "http"], help="Transport override (default: auto-detect from target)"
    )
    detect_p.add_argument(
        "--timeout", type=float, default=3.0, help="Connection timeout in seconds"
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

    # Scan Configs
    scan_configs_p = subparsers.add_parser(
        "scan-configs", aliases=["scan"],
        help="Scan local configuration files, build inventory, and detect schema drift.",
    )
    scan_configs_p.add_argument(
        "--auto", action="store_true", default=True, help="Automatically search all standard system paths for known clients (default: True)"
    )
    scan_configs_p.add_argument(
        "--no-auto", dest="auto", action="store_false", help="Disable automatic search of system paths"
    )
    scan_configs_p.add_argument(
        "--path", help="Scan a specific configuration file or directory."
    )
    scan_configs_p.add_argument(
        "--probe-live", action="store_true", default=True, help="Actively launch/connect to each declared server to verify live schemas (default: True)"
    )
    scan_configs_p.add_argument(
        "--no-probe-live", dest="probe_live", action="store_false", help="Skip live probing"
    )
    scan_configs_p.add_argument(
        "--client", help="Client type to scan (claude, cursor, etc.)"
    )
    scan_configs_p.add_argument(
        "--config-file", help="Path to config file"
    )
    scan_configs_p.add_argument(
        "--custom-clients", help="Path to custom client config file"
    )
    scan_configs_p.add_argument(
        "--auto-passport", action="store_true", help="Auto generate passports for newly discovered active servers"
    )
    scan_configs_p.add_argument(
        "--diff", help="Alias for --compare-snapshot"
    )
    scan_configs_p.add_argument(
        "--save-baseline", dest="save_baseline", help="Save current scan as baseline snapshot (default: mcp-inventory.json)"
    )
    scan_configs_p.add_argument(
        "--format", choices=["table", "json", "markdown", "summary", "detailed"], default="table", help="Output formatting option"
    )
    scan_configs_p.add_argument(
        "--output", help="Save full inventory report to a JSON file."
    )
    
    scan_configs_p.add_argument(
        "--compare-snapshot", help="Compare current scan against a previous baseline snapshot"
    )
    scan_configs_p.add_argument(
        "--fail-on-drift", action="store_true", help="Exit with non-zero status code (exit 2) if schema drift or unexpected additions are detected"
    )
    scan_configs_p.add_argument(
        "--scan-global", action="store_true", default=True, help="Scan globally installed npm and npx packages for MCP servers (default: True)"
    )
    scan_configs_p.add_argument(
        "--no-scan-global", dest="scan_global", action="store_false", help="Disable scanning of global npm/npx packages"
    )

    args = parser.parse_args()

    if args.command in ("interactive", "hub"):
        from mcp_fingerprints.hub import run_interactive_hub

        run_interactive_hub()
    elif args.command == "init":
        from mcp_fingerprints.wizard import run_init_wizard

        run_init_wizard()
    elif args.command == "detect":
        from mcp_fingerprints.detector import detect_mcp
        target = args.target[0] if len(args.target) == 1 and args.target[0].startswith("http") else args.target
        result = detect_mcp(target=target, transport=args.transport, timeout=args.timeout)
        print(json.dumps(result, indent=2))
        if not result["is_mcp"]:
             sys.exit(1)

    elif args.command == "scan-configs" or args.command == "scan":
        import mcp_fingerprints.snapshot_diff as snapshot_diff
        from mcp_fingerprints.config_scanner import LocalInventoryReport

        paths = None
        if args.path:
            paths = [Path(args.path)]
        elif not args.auto:
            logger.error("Must specify --path if --no-auto is used.")
            sys.exit(1)

        if args.path:
            from mcp_fingerprints import scan_config_file

            report = scan_config_file(args.path, probe_live=args.probe_live)
        else:
            from mcp_fingerprints import scan_local_configs

            report = scan_local_configs(probe_live=args.probe_live, scan_global=args.scan_global, custom_clients_path=args.custom_clients)

        if isinstance(report, snapshot_diff.InventorySnapshot):
            inventory = report
        elif isinstance(report, LocalInventoryReport):
            discovered = []
            for s in report.servers:
                c_name = Path(s.get("config_source", "")).name or "unknown"
                discovered.append(
                    snapshot_diff.DiscoveredServer(
                        server_name=s.get("name", ""),
                        client_name=c_name,
                        command=s.get("command"),
                        args=s.get("args", []),
                        env=s.get("env", {}),
                        url=s.get("url"),
                        headers=s.get("headers", {}),
                    )
                )
            inventory = snapshot_diff.InventorySnapshot(servers=discovered)
        else:
            inventory = snapshot_diff.InventorySnapshot()

        if args.output:
            if isinstance(report, LocalInventoryReport):
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(report.to_dict(), f, indent=2)
                logger.info(f"Report saved to {args.output}")
            else:
                inventory.save(args.output)
                print(f"Saved local inventory to {args.output}")


        if getattr(args, "auto_passport", False) and isinstance(report, LocalInventoryReport):
            from mcp_fingerprints.auto_passport import generate_auto_passport
            from mcp_fingerprints.prober import ProbeReport
            for s in report.servers:
                if s.get("live_probe", {}).get("connection_successful") and "tools_observed" in s["live_probe"]:
                     probe_rep = ProbeReport(
                         server_command=s.get("command", []),
                         connection_successful=True,
                         tools_observed=s["live_probe"]["tools_observed"]
                     )
                     generate_auto_passport(probe_rep, Path("data/fingerprints"), server_name=s.get("name"))

        if args.save_baseline:
            snapshot_diff.save_inventory_snapshot(inventory, args.save_baseline)
            print(f"Saved snapshot to {args.save_baseline}")

        if (args.compare_snapshot or getattr(args, "diff", None)):
            baseline = snapshot_diff.InventorySnapshot.load_file((args.compare_snapshot or getattr(args, "diff", None)))
            diff = snapshot_diff.compare_snapshots(baseline, inventory)

            print("======================================================================")
            print("               LOCAL MCP INVENTORY DRIFT REPORT")
            print("======================================================================")
            print(f"Baseline Snapshot: {(args.compare_snapshot or getattr(args, 'diff', None))} (Captured: {baseline.timestamp})")
            print(f"Current Scan:      {inventory.timestamp} ({len(inventory.servers)} servers observed)")
            print("")
            print(f"➕ ADDED SERVERS ({len(diff.added_servers)}):")
            if not diff.added_servers:
                print("  (None)")
            for s in diff.added_servers:
                print(f"  • [{s.client_name}] {s.server_name} -> {s.package_name or 'Custom'} (v{s.version or 'unknown'})")
            print("")
            print(f"➖ REMOVED SERVERS ({len(diff.removed_servers)}):")
            if not diff.removed_servers:
                print("  (None)")
            for s in diff.removed_servers:
                print(f"  • [{s.client_name}] {s.server_name}")
            print("")
            print(f"🔄 MODIFIED / DRIFTED SERVERS ({len(diff.modified_servers)}):")
            if not diff.modified_servers:
                print("  (None)")
            for m in diff.modified_servers:
                print(f"  • [{m.client_name}] {m.server_name}")
                if m.old_version != m.new_version:
                    print(f"    - Version: {m.old_version} -> {m.new_version}")
                if m.old_hash != m.new_hash:
                    print(
                        f"    - Toolset Canonical Hash: Drifted ({m.old_hash} -> {m.new_hash})"
                    )
                if m.changes:
                    print("    - Tool Contract Mutations:")
                    for c in m.changes:
                        print(f"      * {c}")

            print(
                "======================================================================"
            )
            print(
                f"Result: {len(diff.added_servers)} server(s) added, {len(diff.modified_servers)} server(s) drifted."
            )

            if args.fail_on_drift and diff.has_changes:
                sys.exit(2)

        if isinstance(report, LocalInventoryReport):
            if args.format == "json":
                print(json.dumps(report.to_dict(), indent=2))
            elif args.format == "table":
                print(
                    f"{'Server Name':<20} | {'Config Source':<40} | {'Command':<20} | {'Status'}"
                )
                print("-" * 100)
                for srv in report.servers:
                    status = "N/A"
                    if "live_probe" in srv:
                        status = (
                            "Success"
                            if srv["live_probe"].get("connection_successful")
                            else "Failed"
                        )
                    cmd_str = srv.get("command") or srv.get("url") or ""
                    print(
                        f"{srv.get('name', 'Unknown')[:20]:<20} | {srv.get('config_source', '')[:40]:<40} | {cmd_str[:20]:<20} | {status}"
                    )
            elif args.format == "markdown":
                print("| Server Name | Config Source | Command | Status |")
                print("|---|---|---|---|")
                for srv in report.servers:
                    status = "N/A"
                    if "live_probe" in srv:
                        status = (
                            "Success"
                            if srv["live_probe"].get("connection_successful")
                            else "Failed"
                        )
                    cmd_str = srv.get("command") or srv.get("url") or ""
                    print(
                        f"| {srv.get('name', 'Unknown')} | {srv.get('config_source', '')} | {cmd_str} | {status} |"
                    )

            if report.errors:
                print("\nErrors encountered:")
                for e in report.errors:
                    print(f" - {e}")

    elif args.command == "sync":
        sync = PassportSynchronizer(
            output_dir=args.output,
            time_budget=args.time_budget,
            ignore_checkpoint=args.ignore_checkpoint,
            clear_checkpoint=args.clear_checkpoint,
        )
        if args.all or (
            not args.update_existing and not args.discover_new and not args.enrich_ast
            and not getattr(args, "docker", False) and not getattr(args, "polyglot", False)
        ):
            logger.info("Running full multi-source passport synchronization...")
            sync.run_sync_pipeline(
                update_existing=True,
                enrich_ast=True,
                discover_new=True,
                docker=True,
                polyglot=True,
                limit=args.limit,
                max_workers=args.workers,
                probe_runtime=getattr(args, "probe_runtime", False),
                runtime_limit=args.runtime_limit,
                runtime_timeout=args.runtime_timeout,
            )
        else:
            sync.run_sync_pipeline(
                update_existing=args.update_existing,
                enrich_ast=args.enrich_ast,
                discover_new=args.discover_new,
                docker=getattr(args, "docker", False),
                polyglot=getattr(args, "polyglot", False),
                limit=args.limit,
                max_workers=args.workers,
                probe_runtime=getattr(args, "probe_runtime", False),
                runtime_limit=args.runtime_limit,
                runtime_timeout=args.runtime_timeout,
            )

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
        valid, invalid, errors, stats = PassportSchemaValidator.validate_directory(
            args.dir, use_cache=not args.no_cache, max_workers=args.workers
        )
        total = valid + invalid
        print(
            f"Valid: {valid} ({stats['cached']} cached, {stats['validated']} validated in {stats['time_s']:.2f}s)"
        )
        if invalid > 0:
            print(f"Validation summary: {valid} valid, {invalid} invalid passports.")
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
        headers_dict = {}
        if args.header:
            for h in args.header:
                if ":" in h:
                    k, v = h.split(":", 1)
                    headers_dict[k.strip()] = v.strip()

        cmd = args.cmd
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]

        target = args.url if args.url else cmd

        if not target:
            print(
                "ERROR: No server target specified. Usage: mcp-fingerprints probe --url <URL> OR mcp-fingerprints probe -- <command> [args...]"
            )
            sys.exit(1)

        matcher = FingerprintMatcher()
        matcher.load_from_directory(args.dir)
        prober = McpProber(matcher)

        report = prober.probe(
            target=target,
            headers=headers_dict if args.url else None,
            timeout=args.timeout,
            server_name_hint=args.server_hint,
            min_confidence_threshold=args.threshold,
        )

        fmt = args.format
        if args.json:
            fmt = "json"
        elif getattr(args, "short", False):
            fmt = "short"
        elif getattr(args, "long", False):
            fmt = "long"

        from mcp_fingerprints.reporter import format_probe_report

        print(format_probe_report(report, format_type=fmt))

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
        from mcp_fingerprints.config_exporter import (
            ZedExporter,
            ClineExporter,
            WindsurfExporter,
            ClaudeExporter,
            CursorExporter,
            DockerExporter,
            extract_base_config,
        )

        target_client = args.target if args.target else args.client
        search_pkg = args.package or args.server

        if not search_pkg:
            print(
                "ERROR: Must provide either a package positional argument or --server."
            )
            sys.exit(1)

        urllib.parse.quote_plus(search_pkg).replace("%40", "@")

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
                if content.get("package_name") == search_pkg:
                    if args.config:
                        # Patch in place
                        exporters = {
                            "zed": ZedExporter,
                            "cline": ClineExporter,
                            "windsurf": WindsurfExporter,
                            "claude": ClaudeExporter,
                            "cursor": CursorExporter,
                            "docker": DockerExporter,
                        }
                        exporter_cls = exporters.get(target_client, ClaudeExporter)

                        config_path = Path(args.config)
                        existing_content = (
                            config_path.read_text(encoding="utf-8")
                            if config_path.exists()
                            else ""
                        )

                        base_config = extract_base_config(content)
                        package_name = content.get("package_name", "unknown")
                        server_name = args.server or package_name.replace(
                            "@", ""
                        ).replace("/", "-").replace("_", "-")

                        patched = exporter_cls.patch_config(
                            existing_content, server_name, base_config
                        )
                        config_path.write_text(patched, encoding="utf-8")
                        print(f"Patched configuration into {config_path}")
                    else:
                        if args.all_clients:
                            configs = export_all_client_configs(content)
                            print(json.dumps(configs, indent=2))
                        else:
                            config = export_client_config(content, client=target_client)
                            print(json.dumps(config, indent=2))
                    found = True
                    break
            except Exception:
                pass

        if not found:
            print(f"ERROR: Package '{search_pkg}' not found in passports.")
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

    elif args.command == "validate-protocol":
        from mcp_fingerprints.protocol_validator import ProtocolViolationError
        import subprocess
        import threading
        import queue

        if not args.server_command:
            print("ERROR: Command required for validate-protocol")
            sys.exit(1)

        cmd = args.server_command

        try:
            print(f"Validating protocol conformance for: {' '.join(cmd)}")

            # Start process
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            q = queue.Queue()

            def reader_thread(stream):
                for line in stream:
                    q.put(line)

            t = threading.Thread(target=reader_thread, args=(proc.stdout,), daemon=True)
            t.start()

            def send_msg(msg):
                proc.stdin.write(json.dumps(msg) + "\n")
                proc.stdin.flush()

            def read_msg(timeout=2.0):
                try:
                    line = q.get(timeout=timeout)
                    return json.loads(line)
                except queue.Empty:
                    return None
                except json.JSONDecodeError:
                    return None

            from mcp_fingerprints.protocol_validator import (
                validate_mcp_handshake,
                validate_jsonrpc_message,
            )

            # 1. Valid handshake
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "validator", "version": "1.0"},
                },
            }
            send_msg(init_req)

            init_resp = read_msg()
            if not init_resp:
                print("FAIL: No response to initialize request")
                proc.kill()
                sys.exit(1)

            init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            send_msg(init_notif)

            messages = [init_req, init_resp, init_notif]
            try:
                validate_mcp_handshake(messages)
                print("PASS: Valid sequence")
            except ProtocolViolationError as e:
                print(f"FAIL: Handshake validation failed: {e}")
                proc.kill()
                sys.exit(1)

            # 2. Intentional invalid method to test error object structure
            bad_req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "invalid/method/does/not/exist",
                "params": {},
            }
            send_msg(bad_req)

            bad_resp = read_msg()
            if not bad_resp:
                print("FAIL: No response to invalid request")
                proc.kill()
                sys.exit(1)

            try:
                # Should have jsonrpc, id matching, and valid error object
                validate_jsonrpc_message(bad_resp, request_id=2)
                if "error" not in bad_resp:
                    print("FAIL: Invalid request did not return an error object")
                    proc.kill()
                    sys.exit(1)
                print("PASS: Error object structure")
            except ProtocolViolationError as e:
                print(f"FAIL: Error response validation failed: {e}")
                proc.kill()
                sys.exit(1)

            print("==================================================")
            print("Protocol Conformance: PASS")
            print("==================================================")
            proc.kill()

        except Exception as e:
            print(f"FAIL: Exception during validation: {e}")
            if "proc" in locals() and proc.poll() is None:
                proc.kill()
            sys.exit(1)


if __name__ == "__main__":
    main()
