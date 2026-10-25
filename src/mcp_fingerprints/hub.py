import json
import logging
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import mcp_fingerprints.config_scanner as config_scanner
from mcp_fingerprints.auto_passport import generate_auto_passport
from mcp_fingerprints.cache import PassportCacheEngine
from mcp_fingerprints.detector import detect_mcp
from mcp_fingerprints.prober import McpStdioProber
from mcp_fingerprints.search import format_search_results, search_passports
from mcp_fingerprints.snapshot_diff import DiscoveredServer, InventoryDiffer, InventorySnapshot
from mcp_fingerprints.models import ServerPackageSpec
from mcp_fingerprints.sbom_exporter import CycloneDXExporter, SBOMFormat

logger = logging.getLogger("mcp_fingerprints.hub")


@dataclass
class ActionItem:
    category: str
    emoji: str
    title: str
    handler: Callable
    order: int


class ActionRegistry:
    def __init__(self):
        self._actions: list[ActionItem] = []

    def register(self, category: str, emoji: str, title: str, handler: Callable, order: int = 0):
        self._actions.append(ActionItem(category, emoji, title, handler, order))

    def get_categories(self) -> list[str]:
        categories = []
        for action in sorted(self._actions, key=lambda a: a.order):
            if action.category not in categories:
                categories.append(action.category)
        return categories

    def get_actions(self, category: str) -> list[ActionItem]:
        return sorted([a for a in self._actions if a.category == category], key=lambda a: a.order)


def get_status_header() -> str:
    os_name = platform.system()
    if os_name == "Darwin":
        os_name = "macOS"

    scanner = config_scanner.ConfigScanner()
    report = scanner.scan(probe_live=False)

    client_names = set()
    for s in report.servers:
        if "client_path" in s:
            client_names.add(s["client_path"])

    servers = len(report.servers)

    baseline_status = "Not initialized"
    if os.path.exists("workstation_baseline.json"):
        baseline_status = "Saved"

    header = f"""
============================================================
      Interactive MCP Command Hub
============================================================
 OS: {os_name}
 Paths Scanned: {len(client_names)}
 Total MCP Servers Configured: {servers}
 Baseline Status: {baseline_status}
============================================================
"""
    return header


def prompt_choice(prompt: str, choices: list[str]) -> str | None:
    print(f"\n{prompt}")
    for i, choice in enumerate(choices, 1):
        print(f" {i}. {choice}")
    while True:
        try:
            choice = input("Select an option (or Enter to cancel): ").strip()
            if not choice:
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
            print("Invalid choice. Try again.")
        except ValueError:
            print("Please enter a valid number.")


def prompt_input(prompt: str) -> str:
    return input(f"{prompt}: ").strip()


def run_interactive_hub(registry: ActionRegistry = None):
    if not sys.stdin.isatty():
        print("Interactive mode requires a TTY. Please run with a terminal.")
        sys.exit(0)

    if registry is None:
        registry = setup_default_registry()

    while True:
        try:
            print(get_status_header())
            categories = registry.get_categories()
            categories.append("🚪 5. Exit")

            cat_choice = prompt_choice("Main Menu:", categories)
            if cat_choice is None:
                continue

            if cat_choice == "🚪 5. Exit":
                break

            actions = registry.get_actions(cat_choice)
            action_titles = [f"{a.emoji} {a.title}" for a in actions]
            action_titles.append("🔙 Back to Main Menu")

            act_choice = prompt_choice(f"--- {cat_choice} ---", action_titles)
            if act_choice is None or act_choice == "🔙 Back to Main Menu":
                continue

            for action in actions:
                if f"{action.emoji} {action.title}" == act_choice:
                    print(f"\nRunning: {action.title}...")
                    action.handler()
                    break
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Interactive Hub.")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            input("Press Enter to continue...")


def scan_all_agents():
    print("Scanning all agents...")
    scanner = config_scanner.ConfigScanner()
    report = scanner.scan(probe_live=False)
    print(f"Found {len(report.servers)} servers.")

    _post_scan_menu(report.servers)


def scan_specific_agent():
    print("Scanning specific agent...")
    path = prompt_input("Enter client path (e.g. ~/.config/Claude/claude_desktop_config.json)")
    if not path:
        return

    scanner = config_scanner.ConfigScanner()
    report = scanner.scan(paths=[Path(path)], probe_live=False)
    print(f"Found {len(report.servers)} servers.")
    _post_scan_menu(report.servers)


def _post_scan_menu(servers: list[dict[str, Any]]):
    if not servers:
        return

    choice = prompt_choice("Post-Scan Options:", ["Display Formatted Table", "Save Results to JSON File", "Skip"])
    if choice == "Display Formatted Table":
        for s in servers:
            print(f"- {s.get('server_name')} ({s.get('client_path')})")
    elif choice == "Save Results to JSON File":
        filename = prompt_input("Filename") or "scan_results.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(servers, f, indent=2)
        print(f"Saved to {filename}")


def save_baseline():
    scanner = config_scanner.ConfigScanner()
    report = scanner.scan(probe_live=False)

    servers = []
    for s in report.servers:
        server = DiscoveredServer(
            server_name=s.get("server_name", "unknown"),
            client_name=str(s.get("client_path", "unknown")),
        )
        servers.append(server)

    snap = InventorySnapshot(servers=servers)
    with open("workstation_baseline.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(snap.to_dict(), indent=2))
    print("Baseline saved to workstation_baseline.json.")


def diff_baseline():
    if not os.path.exists("workstation_baseline.json"):
        print("No workstation_baseline.json found. Save a baseline first.")
        return

    with open("workstation_baseline.json", encoding="utf-8") as f:
        data = json.loads(f.read())
        baseline = InventorySnapshot.from_dict(data)

    scanner = config_scanner.ConfigScanner()
    report = scanner.scan(probe_live=False)

    servers = []
    for s in report.servers:
        server = DiscoveredServer(
            server_name=s.get("server_name", "unknown"),
            client_name=str(s.get("client_path", "unknown")),
        )
        servers.append(server)

    current = InventorySnapshot(servers=servers)
    diff = InventoryDiffer.compare(baseline, current)

    print(f"Added servers: {len(diff.added_servers)}")
    for s in diff.added_servers:
        print(f"  + {s.server_name} ({s.client_name})")

    print(f"Removed servers: {len(diff.removed_servers)}")
    for s in diff.removed_servers:
        print(f"  - {s.server_name} ({s.client_name})")

    print(f"Modified servers: {len(diff.modified_servers)}")
    for s in diff.modified_servers:
        print(f"  ~ {s.server_name} ({s.client_name})")
        # Since ServerDriftDetail doesn't have tool drift in basic diff right now, we just output it.


def search_db():
    keyword = prompt_input("Enter search keyword")
    if not keyword:
        return
    results = search_passports("data/fingerprints", keyword, limit=10)
    print(format_search_results(results, "table"))


def add_unknown_mcp():
    cmd = prompt_input("Enter stdio command for unindexed server (e.g. npx -y @modelcontextprotocol/server-everything)")
    if not cmd:
        return

    print("Probing server...")
    prober = McpStdioProber()
    try:
        report = prober.probe(cmd.split())
        spec = generate_auto_passport(report, Path("data/fingerprints/npm/u/"))
        if spec:
            print(f"Generated passport for {spec.package_name}")
    except Exception as e:
        print(f"Probe failed: {e}")


def browse_passports():
    print("Browsing not implemented in basic interactive hub. Use web UI for complex browsing.")
    # For full interactive hub this would be a paginated print using standard input matching
    print("Interactive Browse is available in the rich client extension.")


def detect_mcp_cmd():
    target = prompt_input("Enter command or URL to detect")
    if not target:
        return

    result = detect_mcp(target)
    print(json.dumps(result, indent=2))


def deep_probe():
    cmd = prompt_input("Enter command for deep probe")
    if not cmd:
        return

    prober = McpStdioProber()
    try:
        report = prober.probe(cmd.split())
        print(f"Found {len(report.tools_observed)} tools.")
        for t in report.tools_observed:
            print(f"- {t.get('name')}: {t.get('description')}")
    except Exception as e:
        print(f"Probe failed: {e}")


def auto_generate_passport_hub():
    cmd = prompt_input("Enter command to probe and save")
    if not cmd:
        return

    prober = McpStdioProber()
    try:
        report = prober.probe(cmd.split())
        spec = generate_auto_passport(report, Path("data/fingerprints/npm/u/"))
        if spec:
            print(f"Generated passport for {spec.package_name}")
    except Exception as e:
        print(f"Probe failed: {e}")


def view_cache():
    cache = PassportCacheEngine()
    print("Cache statistics:")
    print(f"Entries: {len(cache.cache_data)}")


def clear_cache():
    cache = PassportCacheEngine()
    cache.cache_data = {}
    cache.save_cache()
    print("Cache cleared.")


def inspect_checkpoints():
    print("Active checkpoints and time budgets:")
    print("Not fully implemented in this stub.")


def export_sbom_hub():
    mode = prompt_choice("Export Mode", ["Single Passport from DB", "Entire Catalog Snapshot"])
    if not mode:
        return

    out_path_str = prompt_input(f"Output Filepath (default: ./{'mcp_catalog_sbom.cdx.json' if mode == 'Entire Catalog Snapshot' else '<pkg>_sbom.cdx.json'})")
    if not out_path_str:
        if mode == 'Entire Catalog Snapshot':
            out_path_str = "./mcp_catalog_sbom.cdx.json"

    specs = []
    
    if mode == "Single Passport from DB":
        keyword = prompt_input("Enter exact package name or keyword")
        if not keyword:
            return
        results = search_passports("data/fingerprints", keyword, limit=1)
        if not results:
            print("No matching passport found.")
            return
        
        try:
            spec = ServerPackageSpec.from_dict(results[0])
            specs.append(spec)
            if not out_path_str:
                pkg_name = spec.package_name.replace("/", "_").replace("@", "")
                out_path_str = f"./{pkg_name}_sbom.cdx.json"
        except Exception as e:
            print(f"Failed to load spec: {e}")
            return
            
    elif mode == "Entire Catalog Snapshot":
        # Load all passports
        data_dir = Path("data/fingerprints")
        skip_files = {"sync_state.json", "index.json", ".passport_index.pickle"}
        for file_path in data_dir.rglob("*.json"):
            if file_path.name in skip_files:
                continue
            try:
                content = json.loads(file_path.read_text(encoding="utf-8"))
                if "package_name" in content:
                    specs.append(ServerPackageSpec.from_dict(content))
            except Exception:
                pass
        
        if not specs:
            print("No passports found in catalog.")
            return

    exporter = CycloneDXExporter()
    try:
        sbom = exporter.export(specs, format=SBOMFormat.CYCLONEDX)
        sbom_str = json.dumps(sbom, indent=2)
        
        out_path = Path(out_path_str)
        out_path.write_text(sbom_str, encoding="utf-8")
        
        file_size = len(sbom_str)
        components = sbom.get("components", [])
        print(f"✅ Successfully exported CycloneDX 1.6 SBOM to {out_path.absolute()}")
        print(f"   Component Count: {len(components)}")
        print(f"   File Size: {file_size} bytes")
    except Exception as e:
        print(f"Export failed: {e}")

def setup_default_registry() -> ActionRegistry:
    registry = ActionRegistry()
    registry.register("🖥️ 1. Workstation Discovery & Inventory", "🔍", "Scan All Local AI Agents", scan_all_agents, order=10)
    registry.register("🖥️ 1. Workstation Discovery & Inventory", "🎯", "Scan Specific Agent...", scan_specific_agent, order=20)
    registry.register("🖥️ 1. Workstation Discovery & Inventory", "💾", "Save Current State as Baseline JSON", save_baseline, order=30)
    registry.register("🖥️ 1. Workstation Discovery & Inventory", "⚖️", "Diff Against Previous Baseline", diff_baseline, order=40)

    registry.register("🌐 2. Search Ready Database & Ingest Unknown Local MCPs", "🔤", "Search Ready Database by Keyword", search_db, order=50)
    registry.register("🌐 2. Search Ready Database & Ingest Unknown Local MCPs", "📥", "Add Unknown MCP from Local Machine", add_unknown_mcp, order=60)
    registry.register("🌐 2. Search Ready Database & Ingest Unknown Local MCPs", "📚", "Browse Catalog Passports", browse_passports, order=70)
    registry.register("🌐 2. Search Ready Database & Ingest Unknown Local MCPs", "📦", "Export CycloneDX 1.6 SBOM for Server / Catalog", export_sbom_hub, order=75)

    registry.register("🧪 3. Live Prober & Generic MCP Detector", "🔬", "Detect if Command/URL is an MCP Server", detect_mcp_cmd, order=80)
    registry.register("🧪 3. Live Prober & Generic MCP Detector", "🩺", "Deep Live Server Probe", deep_probe, order=90)
    registry.register("🧪 3. Live Prober & Generic MCP Detector", "🏷️", "Auto-Generate & Save Passport", auto_generate_passport_hub, order=100)

    registry.register("⚙️ 4. Performance, Cache & System", "⚡", "View Cache & Benchmark Stats", view_cache, order=110)
    registry.register("⚙️ 4. Performance, Cache & System", "🧹", "Clear Validation / Passport Cache", clear_cache, order=120)
    registry.register("⚙️ 4. Performance, Cache & System", "⏱️", "Inspect Active Checkpoints & Time Budgets", inspect_checkpoints, order=130)
    return registry


if __name__ == "__main__":
    run_interactive_hub()
