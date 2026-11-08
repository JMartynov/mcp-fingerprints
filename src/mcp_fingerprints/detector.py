import json
import subprocess
import threading
import queue
import time
import urllib.request
import urllib.error
from typing import Any

from mcp_fingerprints.protocol_validator import (
    LATEST_PROTOCOL_VERSION,
    LEGACY_PROTOCOL_VERSION,
    INTERMEDIATE_PROTOCOL_VERSION,
    build_discover_request,
    build_initialize_request,
    is_discover_unsupported_error,
)


def detect_mcp_stdio(command: list[str], timeout: float = 3.0) -> dict[str, Any]:
    """Detect if a local stdio command is an MCP server."""
    result = {
        "is_mcp": False,
        "transport": "stdio",
        "server_info": {},
        "capabilities": {},
        "protocol_version": None,
        "error": None,
    }
    try:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        q = queue.Queue()

        def reader_thread():
            for line in proc.stdout:
                q.put(line)

        t = threading.Thread(target=reader_thread, daemon=True)
        t.start()

        discover_req = build_discover_request(req_id=1, client_name="detector")
        proc.stdin.write(json.dumps(discover_req) + "\n")
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
                        result["protocol_version"] = res.get("protocolVersion", LATEST_PROTOCOL_VERSION)
                        break
                elif data.get("id") == 1 and is_discover_unsupported_error(data):
                    init_req = build_initialize_request(
                        req_id=2, protocol_version=INTERMEDIATE_PROTOCOL_VERSION, client_name="detector"
                    )
                    proc.stdin.write(json.dumps(init_req) + "\n")
                    proc.stdin.flush()
                elif data.get("id") == 2 and "result" in data:
                    res = data["result"]
                    if "serverInfo" in res and "capabilities" in res:
                        result["is_mcp"] = True
                        result["server_info"] = res["serverInfo"]
                        result["capabilities"] = res["capabilities"]
                        result["protocol_version"] = res.get("protocolVersion", INTERMEDIATE_PROTOCOL_VERSION)
                        break
                elif data.get("id") == 2 and "error" in data:
                    # Retry with LEGACY_PROTOCOL_VERSION
                    init_req = build_initialize_request(req_id=3, protocol_version=LEGACY_PROTOCOL_VERSION, client_name="detector")
                    proc.stdin.write(json.dumps(init_req) + "\n")
                    proc.stdin.flush()
                elif data.get("id") == 3 and "result" in data:
                    res = data["result"]
                    if "serverInfo" in res and "capabilities" in res:
                        result["is_mcp"] = True
                        result["server_info"] = res["serverInfo"]
                        result["capabilities"] = res["capabilities"]
                        result["protocol_version"] = res.get("protocolVersion", LEGACY_PROTOCOL_VERSION)
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
        "protocol_version": None,
        "error": None,
    }
    try:
        discover_req = build_discover_request(req_id=1, client_name="detector")
        req = urllib.request.Request(
            url,
            method="POST",
            data=json.dumps(discover_req).encode("utf-8"),
            headers={"Content-Type": "application/json", "MCP-Protocol-Version": LATEST_PROTOCOL_VERSION},
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                
                if is_discover_unsupported_error(data):
                    init_req = build_initialize_request(
                        req_id=2, protocol_version=INTERMEDIATE_PROTOCOL_VERSION, client_name="detector"
                    )
                    req2 = urllib.request.Request(
                        url,
                        method="POST",
                        data=json.dumps(init_req).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(req2, timeout=timeout) as response2:
                        if response2.status == 200:
                            data = json.loads(response2.read().decode("utf-8"))
                            if "error" in data:
                                init_req3 = build_initialize_request(req_id=3, protocol_version=LEGACY_PROTOCOL_VERSION, client_name="detector")
                                req3 = urllib.request.Request(
                                    url,
                                    method="POST",
                                    data=json.dumps(init_req3).encode("utf-8"),
                                    headers={"Content-Type": "application/json"},
                                )
                                with urllib.request.urlopen(req3, timeout=timeout) as response3:
                                    if response3.status == 200:
                                        data = json.loads(response3.read().decode("utf-8"))
                                        response = response3
                            else:
                                response = response2

                if "result" in data:
                    res = data["result"]
                    if "serverInfo" in res and "capabilities" in res:
                        result["is_mcp"] = True
                        result["server_info"] = res["serverInfo"]
                        result["capabilities"] = res["capabilities"]
                        result["protocol_version"] = res.get(
                            "protocolVersion", 
                            LATEST_PROTOCOL_VERSION if data.get("id") == 1 else (LEGACY_PROTOCOL_VERSION if data.get("id") == 3 else INTERMEDIATE_PROTOCOL_VERSION)
                        )
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
