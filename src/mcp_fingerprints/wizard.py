from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def load_user_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load ~/.mcp_fingerprints.toml (or config_path) and merge the [mcp_fingerprints] section."""
    path = config_path or (Path.home() / ".mcp_fingerprints.toml")
    try:
        if not path.is_file():
            return {}
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    result: dict[str, Any] = dict(data)
    section = result.pop("mcp_fingerprints", None)
    if isinstance(section, dict):
        result.update(section)
    return result


def run_init_wizard() -> None:
    if not sys.stdin.isatty():
        sys.stderr.write("Interactive setup wizard requires a TTY. Aborting.\n")
        sys.exit(1)
        return

    print("Welcome to the MCP Fingerprints Setup Wizard!")
    print("This will guide you through creating your initial configuration.")
    print()

    clients = []

    for client in ["Claude", "Cursor", "Cline", "Zed", "Windsurf"]:
        response = input(f"Do you want to configure {client}? (y/N): ").strip().lower()
        if response == "y":
            clients.append(client)

    semantic_search = (
        input("Do you want to enable semantic search? (y/N): ").strip().lower() == "y"
    )

    config_lines = ["[mcp_fingerprints]"]
    if clients:
        clients_str = ", ".join(f'"{c}"' for c in clients)
        config_lines.append(f"clients = [{clients_str}]")
    else:
        config_lines.append("clients = []")

    config_lines.append(f"semantic_search = {'true' if semantic_search else 'false'}")

    config_content = "\n".join(config_lines) + "\n"

    config_path = Path.home() / ".mcp_fingerprints.toml"
    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        print(f"\nSuccessfully wrote configuration to {config_path}")
    except Exception as e:
        sys.stderr.write(f"\nFailed to write configuration: {e}\n")
        sys.exit(1)
