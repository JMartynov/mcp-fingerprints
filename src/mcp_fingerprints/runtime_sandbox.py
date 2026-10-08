import json
import os
import subprocess
import threading
import time
import queue
from typing import Any


def sanitize_environment(env_updates: dict[str, str] | None = None) -> dict[str, str]:
    """
    Sanitize the environment by stripping dangerous variables.
    """
    dangerous_prefixes = (
        "AWS_",
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "SSH_",
    )
    safe_env = {}
    
    for k, v in os.environ.items():
        if any(k.startswith(prefix) for prefix in dangerous_prefixes):
            continue
        safe_env[k] = v

    if "PATH" not in safe_env:
        safe_env["PATH"] = "/usr/local/bin:/usr/bin:/bin"

    if env_updates:
        for k, v in env_updates.items():
            if any(k.startswith(prefix) for prefix in dangerous_prefixes):
                continue
            safe_env[k] = v
            
    return safe_env


def enqueue_output(out, q):
    try:
        for line in iter(out.readline, ''):
            q.put(line)
    except Exception:
        pass
    finally:
        out.close()


def probe_mcp_server_stdio(
    cmd: list[str],
    env: dict[str, str] | None = None,
    timeout_seconds: float = 5.0,
) -> list[dict[str, Any]]:
    """
    Spawns a subprocess to probe an MCP server over stdio.
    """
    safe_env = sanitize_environment(env)

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=safe_env,
            text=True,
            bufsize=1, # Line buffered
        )
    except Exception:
        return []

    if process.stdin is None or process.stdout is None:
        try:
            process.kill()
        except Exception:
            pass
        return []

    def _terminate_process():
        try:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=1.0)
            except Exception:
                pass
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    tools: list[dict[str, Any]] = []
    
    q = queue.Queue()
    t = threading.Thread(target=enqueue_output, args=(process.stdout, q))
    t.daemon = True
    t.start()

    try:
        start_time = time.time()
        
        # 1. Request initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "VerityAuditor", "version": "1.0"},
            },
        }
        process.stdin.write(json.dumps(init_req) + "\n")
        process.stdin.flush()

        # Wait for initialize response
        initialized = False
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                _terminate_process()
                return []
                
            try:
                line = q.get(timeout=min(0.1, timeout_seconds - elapsed))
            except queue.Empty:
                if process.poll() is not None:
                    return []
                continue
                
            if not line:
                continue
                
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            if msg.get("id") == 1 and "result" in msg:
                initialized = True
                break

        if not initialized:
            _terminate_process()
            return []

        # 2. Notification notifications/initialized
        init_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(init_notif) + "\n")
        process.stdin.flush()

        # 3. Request tools/list
        tools_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        process.stdin.write(json.dumps(tools_req) + "\n")
        process.stdin.flush()

        # Wait for tools/list response
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                break
                
            try:
                line = q.get(timeout=min(0.1, timeout_seconds - elapsed))
            except queue.Empty:
                if process.poll() is not None:
                    break
                continue
                
            if not line:
                continue
                
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            if msg.get("id") == 2 and "result" in msg:
                result = msg["result"]
                if "tools" in result and isinstance(result["tools"], list):
                    for tool in result["tools"]:
                        if isinstance(tool, dict) and "name" in tool and "description" in tool and "inputSchema" in tool:
                            tools.append({
                                "name": tool["name"],
                                "description": tool["description"],
                                "inputSchema": tool["inputSchema"]
                            })
                break

    except Exception:
        pass
    finally:
        try:
            if process.stdin:
                process.stdin.close()
        except Exception:
            pass
        _terminate_process()

    return tools
