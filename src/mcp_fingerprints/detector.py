import json
import subprocess
import threading
import queue
import time
import urllib.request
import urllib.error
from typing import Any

def detect_mcp_stdio(command: list[str], timeout: float = 3.0) -> dict[str, Any]:
    """Detect if a local stdio command is an MCP server."""
    result = {
        "is_mcp": False,
        "transport": "stdio",
        "server_info": {},
        "capabilities": {},
        "error": None
    }
    try:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        q = queue.Queue()
        def reader_thread():
            for line in proc.stdout:
                q.put(line)

        t = threading.Thread(target=reader_thread, daemon=True)
        t.start()
        
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "detector", "version": "1.0"}
            }
        }
        
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                line = q.get(timeout=0.1)
                data = json.loads(line)
                if data.get("id") == 1 and "result" in data:
                    res = data["result"]
                    if "serverInfo" in res and "capabilities" in res:
                        result["is_mcp"] = True
                        result["server_info"] = res["serverInfo"]
                        result["capabilities"] = res["capabilities"]
                        break
            except queue.Empty:
                continue
            except json.JSONDecodeError:
                continue
                
        proc.kill()
        
    except Exception as e:
        result["error"] = str(e)
        
    return result

def detect_mcp_http(url: str, timeout: float = 3.0) -> dict[str, Any]:
    """Detect if a URL points to an MCP server (HTTP/SSE)."""
    result = {
        "is_mcp": False,
        "transport": "http",
        "server_info": {},
        "capabilities": {},
        "error": None
    }
    try:
        req = urllib.request.Request(
            url,
            method="POST",
            data=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "detector", "version": "1.0"}
                }
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("id") == 1 and "result" in data:
                    res = data["result"]
                    if "serverInfo" in res and "capabilities" in res:
                        result["is_mcp"] = True
                        result["server_info"] = res["serverInfo"]
                        result["capabilities"] = res["capabilities"]
                        # Could be SSE or streamable-http, general is http
                        if "text/event-stream" in response.headers.get("Content-Type", ""):
                             result["transport"] = "sse"
    except Exception as e:
        result["error"] = str(e)
        
    return result

def detect_mcp(target: str | list[str], transport: str | None = None, timeout: float = 3.0) -> dict[str, Any]:
    """Generic detection interface."""
    if isinstance(target, list) or (transport == "stdio"):
         return detect_mcp_stdio(target if isinstance(target, list) else [target], timeout=timeout)
    else:
         if str(target).startswith("http"):
              return detect_mcp_http(str(target), timeout=timeout)
         else:
              return detect_mcp_stdio([str(target)], timeout=timeout)
