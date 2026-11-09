#!/bin/bash
# 🎬 MCP Fingerprints - Interactive Sandboxed Demo
# This script sets up an ephemeral, isolated environment to demonstrate all CLI commands.

set -e

# ==============================================================================
# Help check
# ==============================================================================
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: ./demo.sh [OPTIONS]"
    echo ""
    echo "Sandboxed demonstration of all mcp-fingerprints CLI commands."
    echo ""
    echo "Options:"
    echo "  --all, --non-interactive  Run all command demonstrations non-interactively"
    echo "  --command <name>          Run a specific command demo (e.g. --command probe)"
    echo "  --help, -h                Show this help message and exit"
    exit 0
fi

# ==============================================================================
# 1. Ephemeral Sandbox Setup
# ==============================================================================
export SANDBOX_DIR=$(mktemp -d)
export BACKGROUND_PIDS=""

cleanup() {
    echo -e "\n🧹 Cleaning up sandbox at $SANDBOX_DIR..."
    if [ -n "$BACKGROUND_PIDS" ]; then
        for pid in $BACKGROUND_PIDS; do
            kill $pid 2>/dev/null || true
            wait $pid 2>/dev/null || true
        done
    fi
    pkill -f "$SANDBOX_DIR/mock_http_server.py" 2>/dev/null || true
    rm -rf "$SANDBOX_DIR"
    echo "✨ Cleanup complete."
}
trap cleanup EXIT INT TERM

# ==============================================================================
# 2. Mock Servers and Data
# ==============================================================================
echo "🛠️ Provisioning sandbox fixtures in $SANDBOX_DIR..."

# 2.1 Mock stdio MCP Server (Python JSON-RPC 2.0)
cat << 'MOCK_PY' > "$SANDBOX_DIR/mock_stdio_server.py"
import sys, json

def send_response(req_id, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}) + "\n")
    sys.stdout.flush()

def send_error(req_id, code, message):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}) + "\n")
    sys.stdout.flush()

for line in sys.stdin:
    if not line.strip(): continue
    try:
        req = json.loads(line)
        method = req.get("method")
        req_id = req.get("id")
        
        if method == "initialize":
            send_response(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {"name": "mock-stdio-server", "version": "1.0.0"}
            })
        elif method == "notifications/initialized":
            pass # No response needed
        elif method == "tools/list":
            send_response(req_id, {
                "tools": [
                    {
                        "name": "query_database",
                        "description": "Query the database",
                        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}},
                        "readOnlyHint": True
                    },
                    {
                        "name": "list_tables",
                        "description": "List all tables",
                        "inputSchema": {"type": "object", "properties": {}},
                        "idempotentHint": True
                    }
                ]
            })
        else:
            if req_id is not None:
                send_error(req_id, -32601, "Method not found")
    except Exception as e:
        if req_id is not None:
            send_error(req_id, -32700, "Parse error")
MOCK_PY

# 2.2 Mock HTTP Server
cat << 'MOCK_HTTP' > "$SANDBOX_DIR/mock_http_server.py"
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        req = json.loads(post_data.decode('utf-8'))
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        method = req.get("method")
        req_id = req.get("id")
        
        if method == "initialize":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {"name": "mock-http-server", "version": "1.0.0"}
            }}
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {
                "tools": [
                    {
                        "name": "fetch_url",
                        "description": "Fetch a URL",
                        "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}}
                    }
                ]
            }}
        else:
            resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
            
        self.wfile.write(json.dumps(resp).encode('utf-8'))

    def log_message(self, format, *args):
        pass

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

server = ReusableHTTPServer(('127.0.0.1', 8888), MCPHandler)
server.serve_forever()
MOCK_HTTP

# Start background HTTP server
pkill -f mock_http_server.py 2>/dev/null || true
python3 "$SANDBOX_DIR/mock_http_server.py" >/dev/null 2>&1 </dev/null &
BACKGROUND_PIDS="$BACKGROUND_PIDS $!"
sleep 1 # Wait for server to bind

# 2.3 Mock Agent Configs
mkdir -p "$SANDBOX_DIR/configs"
cat << 'CUST' > "$SANDBOX_DIR/configs/custom_clients.json"
{
  "test_client": {
    "paths": ["test_path.json"]
  }
}
CUST
cat << CONF1 > "$SANDBOX_DIR/configs/claude_desktop_config.json"
{
  "mcpServers": {
    "demo-stdio": {
      "command": "python3",
      "args": ["$SANDBOX_DIR/mock_stdio_server.py"]
    }
  }
}
CONF1

cat << 'CONF2' > "$SANDBOX_DIR/configs/cursor_mcp.json"
{
  "mcpServers": {
    // JSONC comment
    "demo-http": {
      "url": "http://127.0.0.1:8888/mcp"
    }
  }
}
CONF2

# 2.4 Subsets of Passports
mkdir -p "$SANDBOX_DIR/fingerprints_v1"
mkdir -p "$SANDBOX_DIR/fingerprints_v2"
# Copy up to 5 real passports to v1
find data/fingerprints -name "*.json" -type f | head -n 5 | xargs -I {} cp {} "$SANDBOX_DIR/fingerprints_v1/"
# Ensure icohangar-ops_codesentinel.json is present for export-config and export-sbom demos
[ -f "data/fingerprints/icohangar-ops_codesentinel.json" ] && cp "data/fingerprints/icohangar-ops_codesentinel.json" "$SANDBOX_DIR/fingerprints_v1/"
# Copy them to v2
cp "$SANDBOX_DIR/fingerprints_v1"/* "$SANDBOX_DIR/fingerprints_v2/"
# Mutate one in v2 to simulate drift (tamper hash and add tool)
TARGET_JSON=$(ls "$SANDBOX_DIR/fingerprints_v2"/*.json | head -n 1)
# Create a modified file
jq '.versions[0].toolset_canonical_hash = "sha256:drift1234567890abcdef1234567890abcdef"' "$TARGET_JSON" > "$TARGET_JSON.tmp"
mv "$TARGET_JSON.tmp" "$TARGET_JSON"

# Create a mock tool manifest for matching
cat << 'MANIFEST' > "$SANDBOX_DIR/observed_tools.json"
{
  "tools": [
    {
      "name": "query_database",
      "description": "Query the database",
      "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}
    }
  ]
}
MANIFEST

# Environment Variable overrides to prevent external lookups
export MCP_FINGERPRINTS_CACHE_DIR="$SANDBOX_DIR/cache"
export PATH="/bin:/usr/bin:$PATH"

# ==============================================================================
# 3. Execution Functions
# ==============================================================================
# Uses `uv run mcp-fingerprints` assuming it's available in the env

run_cmd() {
    echo -e "\n------------------------------------------------------------"
    echo "▶ Executing: $@"
    echo "------------------------------------------------------------"
    uv run mcp-fingerprints "$@" || true
}

run_cmd_exit() {
    echo -e "\n------------------------------------------------------------"
    echo "▶ Executing (Expecting Exit Code $1): ${@:2}"
    echo "------------------------------------------------------------"
    uv run mcp-fingerprints "${@:2}" || actual_exit=$?
    actual_exit=${actual_exit:-0}
    if [ $actual_exit -eq $1 ]; then
        echo "✅ Exited with expected code $1"
    else
        echo "❌ Expected exit code $1, got $actual_exit"
    fi
}

run_help() {
    echo -e "\n------------------------------------------------------------"
    echo "▶ Executing: uv run mcp-fingerprints $1 --help"
    echo "------------------------------------------------------------"
    uv run mcp-fingerprints "$1" --help || true
}

demo_1() {
    run_cmd --version
    run_cmd --help
}

demo_2() {
    echo -e "\n--- Scan Configs ---"
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --client claude --config-file "$SANDBOX_DIR/configs/claude_desktop_config.json" --custom-clients "$SANDBOX_DIR/configs/custom_clients.json" --probe-live --no-probe-live --scan-global --no-scan-global --auto-passport --format table --output "$SANDBOX_DIR/scan.json" --no-auto
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --format summary --no-auto --no-scan-global --no-probe-live
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --format detailed --no-auto --no-scan-global --no-probe-live
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --format markdown --no-auto --no-scan-global --no-probe-live
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --format json --no-auto --no-scan-global --no-probe-live
    run_cmd scan-configs --path "$SANDBOX_DIR/configs/claude_desktop_config.json" --probe-live --no-scan-global --no-auto
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --no-scan-global --no-probe-live --no-auto --save-baseline "$SANDBOX_DIR/baseline.json"
    echo "Mutating baseline to trigger drift..."
    jq '.servers[0].toolset_canonical_hash = "sha256:tamperedhash" | .servers[0].toolset_hash = "sha256:tamperedhash"' "$SANDBOX_DIR/baseline.json" > "$SANDBOX_DIR/baseline.tmp" && mv "$SANDBOX_DIR/baseline.tmp" "$SANDBOX_DIR/baseline.json"
    run_cmd_exit 2 scan-configs --path "$SANDBOX_DIR/configs/claude_desktop_config.json" --no-scan-global --no-auto --compare-snapshot "$SANDBOX_DIR/baseline.json" --fail-on-drift
}

demo_3() {
    echo -e "\n--- Detect ---"
    run_cmd detect --transport stdio --timeout 5 --format text "python3 $SANDBOX_DIR/mock_stdio_server.py"
    run_cmd detect --transport http --timeout 5 --format json http://127.0.0.1:8888/mcp
}

demo_4() {
    echo -e "\n--- Probe ---"
    echo "Setting sensitive AWS_ACCESS_KEY_ID before probe..."
    export AWS_ACCESS_KEY_ID="SECRET123"
    run_cmd probe -s -- python3 "$SANDBOX_DIR/mock_stdio_server.py"
    unset AWS_ACCESS_KEY_ID
    
    run_cmd probe --dir "$SANDBOX_DIR/fingerprints_v1" --server-hint "mock-server" --threshold 0.8 --timeout 5 --format short -- python3 "$SANDBOX_DIR/mock_stdio_server.py"
    run_cmd probe --dir "$SANDBOX_DIR/fingerprints_v1" --format long -- python3 "$SANDBOX_DIR/mock_stdio_server.py"
    run_cmd probe --dir "$SANDBOX_DIR/fingerprints_v1" --format json -- python3 "$SANDBOX_DIR/mock_stdio_server.py"
    run_cmd probe --url http://127.0.0.1:8888 --header "Authorization: Bearer test" --format table --dir "$SANDBOX_DIR/fingerprints_v1"
}

demo_5() {
    echo -e "\n--- Validate Protocol ---"
    run_cmd validate-protocol python3 "$SANDBOX_DIR/mock_stdio_server.py"
}

demo_6() {
    echo -e "\n--- Match ---"
    run_cmd match -i "$SANDBOX_DIR/observed_tools.json" --dir "$SANDBOX_DIR/fingerprints_v1" --server-hint "test" --threshold 0.5 --json
    cat "$SANDBOX_DIR/observed_tools.json" | uv run mcp-fingerprints match -i - --dir "$SANDBOX_DIR/fingerprints_v1"
}

demo_7() {
    echo -e "\n--- Search ---"
    run_cmd search "query" --dir "$SANDBOX_DIR/fingerprints_v1" --limit 2
    # --semantic requires fastembed, we just show it's passed, might fallback or succeed.
    run_cmd search "query" --dir "$SANDBOX_DIR/fingerprints_v1" --limit 2 --semantic
}

demo_8() {
    echo -e "
--- Export Config ---"
    run_cmd export-config "icohangar-ops/codesentinel" --client claude --dir "$SANDBOX_DIR/fingerprints_v1"
    run_cmd export-config "icohangar-ops/codesentinel" --all-clients --dir "$SANDBOX_DIR/fingerprints_v1"
    run_cmd export-config "icohangar-ops/codesentinel" --server patched-server --config "$SANDBOX_DIR/configs/cursor_mcp.json" --dir "$SANDBOX_DIR/fingerprints_v1"
    echo "Patched JSONC File Output:"
    cat "$SANDBOX_DIR/configs/cursor_mcp.json"
}

demo_9() {
    echo -e "\n--- Export SBOM ---"
    run_cmd export-sbom --all --format cyclonedx --dir "$SANDBOX_DIR/fingerprints_v1" --output "$SANDBOX_DIR/sbom.json"
    cat "$SANDBOX_DIR/sbom.json" | head -n 15
    run_cmd export-sbom --passport "icohangar-ops/codesentinel" --format spdx --dir "$SANDBOX_DIR/fingerprints_v1" --output "$SANDBOX_DIR/sbom.spdx.json"
}

demo_10() {
    echo -e "\n--- Validate ---"
    run_cmd validate --dir "$SANDBOX_DIR/fingerprints_v1" --workers 2 --no-cache
}

demo_11() {
    echo -e "\n--- Snapshot ---"
    run_cmd snapshot --data-dir "$SANDBOX_DIR/fingerprints_v1" --output-gz "$SANDBOX_DIR/snap.json.gz" --output-json "$SANDBOX_DIR/snap.json"
}

demo_12() {
    echo -e "\n--- Detect Drift ---"
    run_cmd_exit 1 detect-drift --old "$SANDBOX_DIR/fingerprints_v1" --new "$SANDBOX_DIR/fingerprints_v2" --fail-on-tamper --webhook-url "http://127.0.0.1:8888/webhook" --json --output "$SANDBOX_DIR/drift.json"
}

demo_13() {
    echo -e "
--- Command Help Demos (All Supported Commands & Options) ---"
    run_help scan-configs
    run_help detect
    run_help probe
    run_help validate-protocol
    run_help match
    run_help search
    run_help export-config
    run_help export-sbom
    run_help validate
    run_help snapshot
    run_help detect-drift
    run_help build-index
    run_help sync
    run_help browse
    run_help interactive
    run_help init
}

run_all() {
    echo "============================================================"
    echo "   Running Full Sandboxed Demo Suite"
    echo "============================================================"
    demo_1
    demo_2
    demo_3
    demo_4
    demo_5
    demo_6
    demo_7
    demo_8
    demo_9
    demo_10
    demo_11
    demo_12
    demo_13
    echo -e "\n============================================================"
    echo "   Demo Complete"
    echo "============================================================"
}

# ==============================================================================
# 4. Interactive Menu
# ==============================================================================

if [[ "$1" == "--all" || "$1" == "--non-interactive" ]]; then
    run_all
elif [[ "$1" == "--command" ]]; then
    case "$2" in
        version|help) demo_1 ;;
        scan-configs|scan) demo_2 ;;
        detect) demo_3 ;;
        probe) demo_4 ;;
        validate-protocol) demo_5 ;;
        match) demo_6 ;;
        search) demo_7 ;;
        export-config) demo_8 ;;
        export-sbom) demo_9 ;;
        validate) demo_10 ;;
        snapshot) demo_11 ;;
        detect-drift) demo_12 ;;
        safe|extra) demo_13 ;;
        *) echo "Unknown command: $2"; exit 1 ;;
    esac
else
    while true; do
        echo -e "\n======================================="
        echo "   MCP Fingerprints Demo Menu"
        echo "   Sandbox: $SANDBOX_DIR"
        echo "======================================="
        echo "1. Version & Help"
        echo "2. scan-configs"
        echo "3. detect"
        echo "4. probe"
        echo "5. validate-protocol"
        echo "6. match"
        echo "7. search"
        echo "8. export-config"
        echo "9. export-sbom"
        echo "10. validate"
        echo "11. snapshot"
        echo "12. detect-drift"
        echo "13. Safe Demos (Help commands for indexing/sync/UI)"
        echo "14. Run All (--all)"
        echo "0. Exit"
        read -p "Select an option: " choice

        case $choice in
            1) demo_1 ;;
            2) demo_2 ;;
            3) demo_3 ;;
            4) demo_4 ;;
            5) demo_5 ;;
            6) demo_6 ;;
            7) demo_7 ;;
            8) demo_8 ;;
            9) demo_9 ;;
            10) demo_10 ;;
            11) demo_11 ;;
            12) demo_12 ;;
            13) demo_13 ;;
            14) run_all ;;
            0) exit 0 ;;
            *) echo "Invalid option." ;;
        esac
    done
fi
