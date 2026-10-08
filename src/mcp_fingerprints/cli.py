"""CLI for MCP Fingerprint and Passport Knowledge Base."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from mcp_fingerprints.enricher import VulnerabilityEnricher
from mcp_fingerprints.matcher import FingerprintMatcher
from mcp_fingerprints.prober import McpStdioProber
from mcp_fingerprints.schema_validator import PassportSchemaValidator
from mcp_fingerprints.snapshot import build_snapshot
from mcp_fingerprints.synchronizer import PassportSynchronizer
from collections import Counter
from mcp_fingerprints.models import ServerPackageSpec
from mcp_fingerprints.search import search_passports, format_search_results
from mcp_fingerprints.config_exporter import export_client_config, export_all_client_configs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
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
    parser = argparse.ArgumentParser(description="MCP Fingerprint & Passport Knowledge Base CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sync
    sync_p = subparsers.add_parser("sync", help="Synchronize MCP server passports from registries")
    sync_p.add_argument("--output", default="data/fingerprints", help="Output directory")
    sync_p.add_argument("--update-existing", action="store_true", help="Check and update existing MCP versions")
    sync_p.add_argument("--discover-new", action="store_true", help="Discover and pull new MCP servers")
    sync_p.add_argument("--enrich-ast", action="store_true", help="Extract tool contracts via static AST parsing for zero-tool repositories")
    sync_p.add_argument("--limit", type=int, default=500, help="Max passports to probe")
    sync_p.add_argument("--workers", type=int, default=8, help="Concurrency worker threads")
    sync_p.add_argument("--report", action="store_true", help="Run and print the ecosystem health report after sync")
    sync_p.add_argument("--all", action="store_true", help="Run both update and discovery")
    sync_p.add_argument("--snapshot", action="store_true", default=True, help="Compile snapshot after sync")

    # Match
    match_p = subparsers.add_parser("match", help="Match observed runtime tools against the fingerprint knowledge base")
    match_p.add_argument("--input-file", "-i", default="-", help="Path to JSON file containing observed tools/manifest, or '-' for stdin")
    match_p.add_argument("--dir", default="data/fingerprints", help="Directory containing passport files")
    match_p.add_argument("--server-hint", help="Optional server name hint to guide candidate disambiguation")
    match_p.add_argument("--threshold", type=float, default=0.65, help="Minimum confidence threshold (0.0 to 1.0)")
    match_p.add_argument("--json", action="store_true", help="Output full match results as JSON")

    # Probe
    probe_p = subparsers.add_parser("probe", help="Probe a live MCP server over stdio, fingerprint it, and audit known vulnerabilities")
    probe_p.add_argument("--dir", default="data/fingerprints", help="Passport data directory")
    probe_p.add_argument("--server-hint", help="Optional server name hint")
    probe_p.add_argument("--threshold", type=float, default=0.65, help="Minimum confidence threshold")
    probe_p.add_argument("--timeout", type=float, default=10.0, help="Connection and RPC timeout in seconds")
    probe_p.add_argument("--json", action="store_true", help="Output full probe report as JSON")
    probe_p.add_argument("cmd", nargs=argparse.REMAINDER, help="Server launch command and arguments (e.g. -- npx ...)")

    # Enrich
    enrich_p = subparsers.add_parser("enrich", help="Enrich passports with OSV vulnerability metadata")
    enrich_p.add_argument("--vulnerabilities", "-v", required=True, help="Path to vulnerabilities.json.gz or vulnerabilities.json")
    enrich_p.add_argument("--dir", default="data/fingerprints", help="Passport data directory")
    enrich_p.add_argument("--snapshot", action="store_true", default=True, help="Compile snapshot after enrichment")

    # Validate
    val_p = subparsers.add_parser("validate", help="Validate passport directory invariants")
    val_p.add_argument("--dir", default="data/fingerprints", help="Passport directory to validate")

    # Snapshot
    snap_p = subparsers.add_parser("snapshot", help="Compile all passports into consolidated .json.gz")
    snap_p.add_argument("--data-dir", default="data/fingerprints", help="Passport data directory")
    snap_p.add_argument("--output-gz", default="passports.json.gz", help="Output gzip file path")
    snap_p.add_argument("--output-json", default=None, help="Optional uncompressed JSON output path")

    # Search
    search_p = subparsers.add_parser("search", help="Fuzzy search MCP servers by keyword or capability")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--dir", default="data/fingerprints", help="Passport data directory")
    search_p.add_argument("--limit", type=int, default=10, help="Maximum results to return")

    # Export Config
    export_p = subparsers.add_parser("export-config", help="Export client configuration (Claude/Cursor/Cline/Zed/Windsurf/Docker)")
    export_p.add_argument("package", help="Package name to export configuration for")
    export_p.add_argument("--dir", default="data/fingerprints", help="Passport data directory")
    export_p.add_argument(
        "--client",
        choices=["claude", "cursor", "cline", "zed", "windsurf", "docker"],
        default="claude",
        help="Client type (claude, cursor, cline, zed, windsurf, docker)",
    )
    export_p.add_argument("--all-clients", action="store_true", help="Export configuration for all supported clients")

    args = parser.parse_args()

    if args.command == "sync":
        sync = PassportSynchronizer(output_dir=args.output)
        if args.all or (not args.update_existing and not args.discover_new and not args.enrich_ast):
            logger.info("Running full multi-source passport synchronization...")
            sync.update_existing_passports()
            sync.enrich_zero_tool_passports(limit=args.limit, max_workers=args.workers)
            sync.discover_new_mcps()
        else:
            if args.update_existing:
                sync.update_existing_passports()
            if args.enrich_ast:
                sync.enrich_zero_tool_passports(limit=args.limit, max_workers=args.workers)
            if args.discover_new:
                sync.discover_new_mcps()

        if args.snapshot:
            logger.info("Compiling consolidated snapshot...")
            build_snapshot(data_dir=args.output, output_gz=f"{Path(args.output).parent}/passports.json.gz" if args.output != "data/fingerprints" else "passports.json.gz")

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
        res = build_snapshot(data_dir=args.data_dir, output_gz=args.output_gz, output_json=args.output_json)
        print(f"Compiled {res['total_passports']} passports ({res['size_kb']:.2f} KB) -> {res['snapshot_path']}")

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
                print(f"Matched Tools:      {match_res.matched_tool_count} / {match_res.total_observed_tools}")
                if match_res.unmatched_observed_tools:
                    print(f"Unmatched Tools:    {', '.join(match_res.unmatched_observed_tools)}")
                if match_res.missing_expected_tools:
                    print(f"Missing Tools:      {', '.join(match_res.missing_expected_tools)}")
            else:
                print(f"Confidence:         {match_res.confidence_score * 100:.1f}%")
                print(f"Reason:             No candidate passport met threshold >= {args.threshold}")
            print("==================================================")

    elif args.command == "probe":
        cmd = args.cmd
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        if not cmd:
            print("ERROR: No server command specified. Usage: mcp-fingerprints probe -- <command> [args...]")
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
            print(f"Connection:         {'SUCCESS' if report.connection_successful else 'FAILED'}")
            if report.error:
                print(f"Error:              {report.error}")
            print(f"Observed Tools:     {len(report.tools_observed)}")
            print(f"Observed Prompts:   {len(report.prompts_observed)}")
            print(f"Observed Resources: {len(report.resources_observed)}")
            print("--------------------------------------------------")
            if report.match_result and report.match_result.matched:
                print(f"Identified Package: {report.match_result.package_name}")
                print(f"Identified Version: {report.match_result.matched_version}")
                print(f"Confidence:         {report.match_result.confidence_score * 100:.1f}% ({report.match_result.match_layer})")
                print("--------------------------------------------------")
                if report.is_vulnerable:
                    print("SECURITY STATUS:    ⚠️  VULNERABLE")
                    print(f"Max CVSS Score:     {report.max_cvss_score:.1f}")
                    if report.recommended_fixed_version:
                        print(f"Recommended Fix:    Upgrade to >= {report.recommended_fixed_version}")
                    print(f"Active Advisories:  {len(report.active_advisories)}")
                    for adv in report.active_advisories:
                        print(f"  - [{adv['severity']}] {adv['id']}: {adv.get('summary', '')}")
                else:
                    print("SECURITY STATUS:    ✅ CLEAN (No known CVEs affecting this version)")
            else:
                print("Identified Package: UNKNOWN (Confidence below threshold)")
            print("==================================================")

    elif args.command == "enrich":
        enricher = VulnerabilityEnricher(args.vulnerabilities)
        total, with_vulns = enricher.enrich_directory(args.dir)
        print(f"Enrichment summary: {total} passports audited, {with_vulns} enriched with known vulnerabilities.")
        if args.snapshot:
            logger.info("Compiling snapshot with enriched security profiles...")
            snap_path = f"{Path(args.dir).parent}/passports.json.gz" if args.dir != "data/fingerprints" else "passports.json.gz"
            build_snapshot(data_dir=args.dir, output_gz=snap_path)

    elif args.command == "search":
        results = search_passports(args.dir, args.query, args.limit)
        print(format_search_results(results))

    elif args.command == "export-config":
        import urllib.parse
        urllib.parse.quote_plus(args.package).replace("%40", "@")
        
        # In actual structure it looks like dir / package_name.json but slashes are replaced by _
        # Usually it's purl or name - let's search for package_name
        found = False
        for j_file in Path(args.dir).rglob("*.json"):
            if j_file.name in ("sync_state.json", "index.json", ".passport_index.pickle"):
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


if __name__ == "__main__":
    main()


