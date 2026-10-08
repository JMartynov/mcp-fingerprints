"""Config Exporter module for generating Claude Desktop and Cursor client configurations."""

from typing import Any


SUPPORTED_CLIENTS = ("claude", "cursor", "cline", "zed", "windsurf", "docker")


def export_client_config(passport: dict[str, Any], client: str = "claude") -> dict[str, Any]:
    """
    Format client configuration for 'claude', 'cursor', 'cline', 'zed', 'windsurf', or 'docker'.
    
    Inspects connections and ecosystem in the latest version:
      - If stdio: extracts command, args, and env.
      - If npm: default command `npx -y <package_name>`.
      - If pypi: default command `uvx <package_name>` or `python -m <module>`.
      - If sse: extracts url.
    """
    if client not in SUPPORTED_CLIENTS:
        raise ValueError(f"Unsupported client: {client}. Must be one of {SUPPORTED_CLIENTS}.")
        
    package_name = passport.get("package_name", "unknown")
    ecosystem = passport.get("ecosystem", "unknown")
    
    versions = passport.get("versions", [])
    if not versions:
        raise ValueError("Passport has no versions.")
        
    # Get the most recent version (assuming sorted or we just grab the first that has connections)
    latest_version = versions[0]
    for v in versions:
        if v.get("connections"):
            latest_version = v
            break
            
    connections = latest_version.get("connections", [])
    
    # Try to find a stdio or sse connection
    conn = None
    if connections:
        for c in connections:
            if c.get("type") in ("stdio", "sse"):
                conn = c
                break
        if not conn:
            conn = connections[0]
            
    safe_name = package_name.replace("@", "").replace("/", "-").replace("_", "-")

    # Handle SSE connections
    if conn and conn.get("type") == "sse":
        url = conn.get("url") or conn.get("deploymentUrl") or ""
        if client in ("claude", "cursor", "windsurf"):
            return {
                "mcpServers": {
                    safe_name: {
                        "type": "sse",
                        "url": url,
                    }
                }
            }
        elif client == "cline":
            return {
                "mcpServers": {
                    safe_name: {
                        "type": "sse",
                        "url": url,
                        "disabled": False,
                        "autoApprove": [],
                    }
                }
            }
        elif client == "zed":
            return {
                "context_servers": {
                    safe_name: {
                        "url": url,
                    }
                }
            }
        elif client == "docker":
            return {
                "sseUrl": url,
                "note": "SSE connection does not require local container execution.",
            }

    # Stdio or fallback command extraction
    command = ""
    args = []
    env = {}
    
    if conn and conn.get("type") == "stdio":
        command = conn.get("command", "")
        args = conn.get("args", [])
        env = conn.get("env", {})
        
    # Fallback defaults if command is missing
    if not command:
        if ecosystem == "npm":
            command = "npx"
            args = ["-y", package_name] + args
        elif ecosystem == "pypi":
            command = "uvx"
            args = [package_name] + args
        else:
            command = package_name

    # Client-specific formatting
    if client in ("claude", "cursor", "windsurf"):
        server_conf: dict[str, Any] = {
            "command": command,
            "args": args,
        }
        if env:
            server_conf["env"] = env
        return {
            "mcpServers": {
                safe_name: server_conf
            }
        }
    elif client == "cline":
        cline_conf: dict[str, Any] = {
            "command": command,
            "args": args,
            "disabled": False,
            "autoApprove": [],
        }
        if env:
            cline_conf["env"] = env
        return {
            "mcpServers": {
                safe_name: cline_conf
            }
        }
    elif client == "zed":
        cmd_obj: dict[str, Any] = {
            "path": command,
            "args": args,
        }
        if env:
            cmd_obj["env"] = env
        return {
            "context_servers": {
                safe_name: {
                    "command": cmd_obj
                }
            }
        }
    elif client == "docker":
        if ecosystem == "npm":
            image = "node:22-alpine"
        elif ecosystem == "pypi":
            image = "python:3.12-slim"
        else:
            image = "alpine:latest"

        cmd_parts = ["docker", "run", "-i", "--rm"]
        for k, v in env.items():
            cmd_parts.extend(["-e", f"{k}={v}"])
        cmd_parts.append(image)
        cmd_parts.append(command)
        cmd_parts.extend(args)

        return {
            "dockerCommand": " ".join(cmd_parts),
            "container": {
                "image": image,
                "command": command,
                "args": args,
                "env": env,
            }
        }

    return {}


def export_all_client_configs(passport: dict[str, Any]) -> dict[str, Any]:
    """Export client configurations across all supported clients."""
    return {c: export_client_config(passport, client=c) for c in SUPPORTED_CLIENTS}

