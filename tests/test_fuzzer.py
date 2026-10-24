import json
import os
import sys
import tempfile

from mcp_fingerprints.fuzzer import (
    PayloadCategory,
    FuzzOutcome,
    PayloadMutator,
    SchemaDrivenFuzzer,
)


def test_payload_mutator_coverage_and_determinism():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "is_active": {"type": "boolean"},
            "tags": {"type": "array"},
            "metadata": {"type": "object"},
        },
        "required": ["name", "age"]
    }
    
    # Generate large number of cases to ensure coverage
    cases = PayloadMutator.generate_payloads("test_tool", schema, max_cases=100)
    
    # 1. Determinism check
    cases2 = PayloadMutator.generate_payloads("test_tool", schema, max_cases=100)
    assert cases == cases2
    
    # 2. Coverage check - Ensure all 8 categories are present
    seen_categories = set(cat for cat, _ in cases)
    assert len(seen_categories) == 8
    for cat in PayloadCategory:
        assert cat in seen_categories
        
    # Check max_cases exact length behavior
    cases_small = PayloadMutator.generate_payloads("test_tool", schema, max_cases=5)
    assert len(cases_small) == 5
    
    # Even if max_cases is small, if it's 8 we should see all 8 categories
    cases_eight = PayloadMutator.generate_payloads("test_tool", schema, max_cases=8)
    assert len(cases_eight) == 8
    seen_eight = set(cat for cat, _ in cases_eight)
    assert len(seen_eight) == 8

def _create_mock_server_script(behavior: str) -> str:
    script = """
import sys
import json
import time

def read_msg():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)

def send_msg(msg):
    sys.stdout.write(json.dumps(msg) + "\\n")
    sys.stdout.flush()

# Handshake
msg = read_msg()
if msg and msg.get('method') == 'initialize':
    send_msg({
        "jsonrpc": "2.0",
        "id": msg['id'],
        "result": {
            "capabilities": {},
            "serverInfo": {"name": "mock", "version": "1.0"}
        }
    })
msg = read_msg() # notifications/initialized

# Behavior:
"""
    if behavior == "handled_result":
        script += """
while True:
    req = read_msg()
    if not req: break
    send_msg({
        "jsonrpc": "2.0",
        "id": req.get("id"),
        "result": {"_handled": True}
    })
"""
    elif behavior == "clean_error":
        script += """
while True:
    req = read_msg()
    if not req: break
    send_msg({
        "jsonrpc": "2.0",
        "id": req.get("id"),
        "error": {"code": -32602, "message": "Invalid params"}
    })
"""
    elif behavior == "protocol_violation":
        script += """
while True:
    req = read_msg()
    if not req: break
    sys.stdout.write("Not JSON\\n")
    sys.stdout.flush()
"""
    elif behavior == "timeout_hang":
        script += """
while True:
    req = read_msg()
    if not req: break
    time.sleep(10) # Hang
"""
    elif behavior == "process_crash":
        script += """
while True:
    req = read_msg()
    sys.exit(1)
"""
    return script

def test_schema_driven_fuzzer_outcomes():
    # Test all 5 outcome types using mock servers
    
    schemas = [{
        "name": "test_tool",
        "inputSchema": {
            "type": "object",
            "properties": {"val": {"type": "string"}}
        }
    }]
    
    behaviors_to_outcomes = {
        "handled_result": FuzzOutcome.handled_result,
        "clean_error": FuzzOutcome.clean_error,
        "protocol_violation": FuzzOutcome.protocol_violation,
        "timeout_hang": FuzzOutcome.timeout_hang,
        "process_crash": FuzzOutcome.process_crash,
    }
    
    for behavior, expected_outcome in behaviors_to_outcomes.items():
        script = _create_mock_server_script(behavior)
        
        # Test 1 iteration so we get exactly 1 case to check outcome for
        fuzzer = SchemaDrivenFuzzer(
            target_command=[sys.executable, "-c", script],
            schemas=schemas,
            iterations=1,
            timeout=1.0
        )
        report = fuzzer.fuzz()
        
        assert report.total_cases == 1
        assert len(report.results) == 1
        assert report.results[0].outcome == expected_outcome


def test_cli_fuzz_subcommand():
    script = _create_mock_server_script("handled_result")
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_path = f.name
        
    try:
        from mcp_fingerprints.cli import main
        import sys
        
        # We need a passport to pass
        passport_content = {
            "tools": [{
                "name": "mock_tool",
                "inputSchema": {"type": "object"}
            }]
        }
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as pf:
            json.dump(passport_content, pf)
            passport_path = pf.name
            
        sys.argv = [
            "mcp-fingerprints", "fuzz",
            "--passport", passport_path,
            "--iterations", "1",
            "--timeout", "1.0",
            "--output", out_path,
            "--", sys.executable, "-c", script
        ]
        
        try:
            main()
        except SystemExit as e:
            assert e.code == 0 or e.code is None
            
        with open(out_path, "r") as f:
            report_data = json.load(f)
            
        assert report_data["total_cases"] == 1
        assert report_data["handled_results"] == 1
        assert report_data["passed"] is True
        
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)
        if 'passport_path' in locals() and os.path.exists(passport_path):
            os.remove(passport_path)

