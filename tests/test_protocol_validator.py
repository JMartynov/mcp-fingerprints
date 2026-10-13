import pytest
from mcp_fingerprints.protocol_validator import validate_jsonrpc_message, validate_mcp_handshake, ProtocolViolationError

def test_valid_jsonrpc_message():
    msg = {"jsonrpc": "2.0", "id": 1, "result": {}}
    validate_jsonrpc_message(msg, request_id=1)

def test_missing_jsonrpc_field():
    msg = {"id": 1, "result": {}}
    with pytest.raises(ProtocolViolationError, match="Missing 'jsonrpc' field in message"):
        validate_jsonrpc_message(msg)

def test_invalid_jsonrpc_version():
    msg = {"jsonrpc": "1.0", "id": 1, "result": {}}
    with pytest.raises(ProtocolViolationError, match="Invalid 'jsonrpc' version"):
        validate_jsonrpc_message(msg)

def test_id_reflection_missing():
    msg = {"jsonrpc": "2.0", "result": {}}
    with pytest.raises(ProtocolViolationError, match="Missing 'id' in response"):
        validate_jsonrpc_message(msg, request_id=1)

def test_id_reflection_mismatch():
    msg = {"jsonrpc": "2.0", "id": 2, "result": {}}
    with pytest.raises(ProtocolViolationError, match="ID reflection failed"):
        validate_jsonrpc_message(msg, request_id=1)

def test_valid_error_object():
    msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32601,
            "message": "Method not found"
        }
    }
    validate_jsonrpc_message(msg, request_id=1)

def test_invalid_error_object_missing_code():
    msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "message": "Method not found"
        }
    }
    with pytest.raises(ProtocolViolationError, match="Error object must contain an integer 'code' field"):
        validate_jsonrpc_message(msg, request_id=1)

def test_invalid_error_object_missing_message():
    msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32601
        }
    }
    with pytest.raises(ProtocolViolationError, match="Error object must contain a string 'message' field"):
        validate_jsonrpc_message(msg, request_id=1)

def test_valid_mcp_handshake():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"}
        }
    }
    resp = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "server", "version": "1"}
        }
    }
    notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    validate_mcp_handshake([req, resp, notif])

def test_invalid_mcp_handshake_missing_messages():
    with pytest.raises(ProtocolViolationError, match="Handshake requires at least 3 messages"):
        validate_mcp_handshake([])

def test_invalid_mcp_handshake_first_message_not_initialize():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "not_initialize",
        "params": {}
    }
    with pytest.raises(ProtocolViolationError, match="First message must be an 'initialize' request"):
        validate_mcp_handshake([req, req, req])

def test_invalid_mcp_handshake_missing_client_info():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    with pytest.raises(ProtocolViolationError, match="Initialize request params missing 'clientInfo'"):
        validate_mcp_handshake([req, req, req])

