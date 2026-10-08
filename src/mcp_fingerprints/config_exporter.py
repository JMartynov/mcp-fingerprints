"""Config Exporter module for generating Claude Desktop and Cursor client configurations."""

from typing import Any


def export_client_config(passport: dict[str, Any], client: str = "claude") -> dict[str, Any]:
    """
    Format client configuration for 'claude' (claude_desktop_config.json) or 'cursor' (mcpServers).
    
    Inspects connections and ecosystem in the latest version:
      - If stdio: extracts command, args, and env.
      - If npm: default command `npx -y <package_name>`.
      - If pypi: default command `uvx <package_name>` or `python -m <module>`.
      - If sse: extracts url.
    """
    if client not in ("claude", "cursor"):
        raise ValueError("Unsupported client. Must be 'claude' or 'cursor'.")
        
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
            
    server_config = {}
    
    # Extract command, args, env, or url
    if conn and conn.get("type") == "sse":
        if client == "claude":
            server_config = {
                "type": "sse",
                "url": conn.get("url") or conn.get("deploymentUrl") or ""
            }
        else: # cursor
            server_config = {
                "type": "sse",
                "url": conn.get("url") or conn.get("deploymentUrl") or ""
            }
    else: # stdio or fallback
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
                
        server_config = {
            "command": command,
            "args": args
        }
        if env:
            server_config["env"] = env
            
    # Format according to client
    # Clean the package name for the server key (e.g., '@namespace/pkg' -> 'namespace-pkg')
    safe_name = package_name.replace("@", "").replace("/", "-").replace("_", "-")
    
    if client == "claude":
        return {
            "mcpServers": {
                safe_name: server_config
            }
        }
    else: # cursor
        return {
            "mcpServers": {
                safe_name: server_config
            }
        }
