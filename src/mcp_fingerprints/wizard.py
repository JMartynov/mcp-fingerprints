import sys
from pathlib import Path


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
