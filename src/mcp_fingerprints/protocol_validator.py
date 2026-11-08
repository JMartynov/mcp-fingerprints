from typing import Any, Dict, List, Optional, Union

SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = (
    "2026-07-28",
    "2025-11-25",
    "2025-06-18",
    "2024-11-05",
)
LATEST_PROTOCOL_VERSION = "2026-07-28"
INTERMEDIATE_PROTOCOL_VERSION = "2025-11-25"
LEGACY_PROTOCOL_VERSION = "2024-11-05"


def build_discover_request(req_id: int = 1, client_name: str = "mcp-fingerprints") -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "server/discover",
        "params": {
            "protocolVersion": LATEST_PROTOCOL_VERSION,
            "clientInfo": {"name": client_name, "version": "1.1.0"},
        },
    }


def build_initialize_request(
    req_id: int = 2,
    protocol_version: str = INTERMEDIATE_PROTOCOL_VERSION,
    client_name: str = "mcp-fingerprints",
) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "initialize",
        "params": {
            "protocolVersion": protocol_version,
            "capabilities": {},
            "clientInfo": {"name": client_name, "version": "1.1.0"},
        },
    }


def is_discover_unsupported_error(msg: dict[str, Any]) -> bool:
    """Detect legacy MCP 1.x servers that reject server/discover with -32601 or -32602."""
    error = msg.get("error")
    if not isinstance(error, dict):
        return False
    return error.get("code") in (-32601, -32602)


class ProtocolViolationError(Exception):
    pass

def validate_jsonrpc_message(msg: Dict[str, Any], request_id: Optional[Union[int, str]] = None) -> None:
    if "jsonrpc" not in msg:
        raise ProtocolViolationError("Missing 'jsonrpc' field in message.")
    if msg["jsonrpc"] != "2.0":
        raise ProtocolViolationError(f"Invalid 'jsonrpc' version: {msg.get('jsonrpc')}. Expected '2.0'.")
    
    # ID reflection validation
    if request_id is not None:
        if "id" not in msg:
            raise ProtocolViolationError("Missing 'id' in response.")
        if msg["id"] != request_id:
            raise ProtocolViolationError(f"ID reflection failed. Expected {request_id}, got {msg.get('id')}.")
    elif "id" in msg and "method" not in msg: 
        # If it's a response but we didn't expect a specific ID, at least we can check if it's there
        # but normally we want to pass request_id. 
        pass

    # Error object validation
    if "error" in msg:
        error = msg["error"]
        if not isinstance(error, dict):
            raise ProtocolViolationError("Error field must be an object.")
        if "code" not in error or not isinstance(error["code"], int):
            raise ProtocolViolationError("Error object must contain an integer 'code' field.")
        if "message" not in error or not isinstance(error["message"], str):
            raise ProtocolViolationError("Error object must contain a string 'message' field.")

def validate_mcp_handshake(messages: List[Dict[str, Any]]) -> None:
    """
    Validates a sequence of messages representing an MCP handshake.
    The sequence is expected to be:
    1. Client initialize request
    2. Server initialize response
    3. Client notifications/initialized
    Or for newer versions:
    1. Client server/discover request
    2. Server server/discover response
    """
    if not messages:
        raise ProtocolViolationError("Handshake requires at least 3 messages: initialize request, response, and notifications/initialized.")
        
    req = messages[0]
    if req.get("method") == "server/discover":
        if len(messages) < 2:
            raise ProtocolViolationError("Handshake requires at least 2 messages for server/discover or 3 messages: initialize request, response, and notifications/initialized.")
        resp = messages[1]
        validate_jsonrpc_message(req)
        validate_jsonrpc_message(resp, request_id=req.get("id"))
        
        if "params" not in req or not isinstance(req["params"], dict):
            raise ProtocolViolationError("server/discover request missing 'params'.")
        if "protocolVersion" not in req["params"]:
            raise ProtocolViolationError("server/discover request params missing 'protocolVersion'.")
        if "clientInfo" not in req["params"]:
            raise ProtocolViolationError("server/discover request params missing 'clientInfo'.")
            
        if "result" not in resp or not isinstance(resp["result"], dict):
            raise ProtocolViolationError("server/discover response missing 'result' field.")
        result = resp["result"]
        if "protocolVersion" not in result:
            raise ProtocolViolationError("server/discover response result missing 'protocolVersion'.")
        if "capabilities" not in result:
            raise ProtocolViolationError("server/discover response result missing 'capabilities'.")
        if "serverInfo" not in result:
            raise ProtocolViolationError("server/discover response result missing 'serverInfo'.")
        
        return
        
    if len(messages) < 3:
        raise ProtocolViolationError("Handshake requires at least 3 messages: initialize request, response, and notifications/initialized.")

    req = messages[0]
    resp = messages[1]
    notif = messages[2]

    # Validate jsonrpc for all
    validate_jsonrpc_message(req)
    validate_jsonrpc_message(resp, request_id=req.get("id"))
    validate_jsonrpc_message(notif)

    # 1. Initialize request
    if req.get("method") != "initialize":
        raise ProtocolViolationError("First message must be an 'initialize' request.")
    if "params" not in req or not isinstance(req["params"], dict):
        raise ProtocolViolationError("Initialize request missing 'params'.")
    if "protocolVersion" not in req["params"]:
        raise ProtocolViolationError("Initialize request params missing 'protocolVersion'.")
    if "capabilities" not in req["params"]:
        raise ProtocolViolationError("Initialize request params missing 'capabilities'.")
    if "clientInfo" not in req["params"]:
        raise ProtocolViolationError("Initialize request params missing 'clientInfo'.")

    # 2. Initialize response
    if "result" not in resp:
        raise ProtocolViolationError("Initialize response missing 'result' field.")
    result = resp["result"]
    if "protocolVersion" not in result:
        raise ProtocolViolationError("Initialize response result missing 'protocolVersion'.")
    if "capabilities" not in result:
        raise ProtocolViolationError("Initialize response result missing 'capabilities'.")
    if "serverInfo" not in result:
        raise ProtocolViolationError("Initialize response result missing 'serverInfo'.")

    # 3. Initialized notification
    if notif.get("method") != "notifications/initialized":
        raise ProtocolViolationError("Third message must be 'notifications/initialized'.")
    if "id" in notif:
        raise ProtocolViolationError("Notifications must not contain an 'id' field.")

