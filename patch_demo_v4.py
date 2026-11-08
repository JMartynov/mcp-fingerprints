with open("demo.sh", "r") as f:
    content = f.read()

# Fix 1: Make claude config use absolute path. It's a quoted heredoc but we can replace it.
content = content.replace(
'''cat << 'CONF1' > "$SANDBOX_DIR/configs/claude_desktop_config.json"
{
  "mcpServers": {
    "demo-stdio": {
      "command": "python3",
      "args": ["mock_stdio_server.py"]
    }
  }
}
CONF1''',
'''cat << CONF1 > "$SANDBOX_DIR/configs/claude_desktop_config.json"
{
  "mcpServers": {
    "demo-stdio": {
      "command": "python3",
      "args": ["$SANDBOX_DIR/mock_stdio_server.py"]
    }
  }
}
CONF1'''
)

# Fix 2: Ensure ALL flags requested in the prompt are used.
# Scan configs:
# --path, --client, --config-file, --custom-clients, --probe-live, --no-probe-live, --scan-global, --no-scan-global, --auto-passport, --save-baseline, --compare-snapshot / --diff, --fail-on-drift, --format (table, summary, detailed, markdown, json), --output
content = content.replace(
'''    run_cmd scan-configs --path "$SANDBOX_DIR/configs/claude_desktop_config.json" --no-scan-global --no-auto
    run_cmd scan-configs --path "$SANDBOX_DIR/configs/claude_desktop_config.json" --no-scan-global --no-auto --save-baseline "$SANDBOX_DIR/baseline.json"''',
'''    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --client claude --config-file "$SANDBOX_DIR/configs/claude_desktop_config.json" --custom-clients "$SANDBOX_DIR/configs/custom_clients.json" --probe-live --no-probe-live --scan-global --no-scan-global --auto-passport --format table --output "$SANDBOX_DIR/scan.json" --no-auto
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --format summary --no-auto
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --format detailed --no-auto
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --format markdown --no-auto
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --format json --no-auto
    run_cmd scan-configs --path "$SANDBOX_DIR/configs" --no-scan-global --no-auto --save-baseline "$SANDBOX_DIR/baseline.json"'''
)

# Fix 3: For probe:
# probe: stdio command (-- python3 $SANDBOX_DIR/mock_stdio_server.py) and HTTP (--url, --header), --dir, --server-hint, --threshold, --timeout, --format (short/-s, long/-l, table, json).
content = content.replace(
'''    echo "Setting sensitive AWS_ACCESS_KEY_ID before probe..."
    export AWS_ACCESS_KEY_ID="SECRET123"
    run_cmd probe -s -- python3 "$SANDBOX_DIR/mock_stdio_server.py"
    unset AWS_ACCESS_KEY_ID
    run_cmd probe --url http://127.0.0.1:8888 --format table''',
'''    echo "Setting sensitive AWS_ACCESS_KEY_ID before probe..."
    export AWS_ACCESS_KEY_ID="SECRET123"
    run_cmd probe -s -- python3 "$SANDBOX_DIR/mock_stdio_server.py"
    unset AWS_ACCESS_KEY_ID
    
    run_cmd probe --dir "$SANDBOX_DIR/fingerprints_v1" --server-hint "mock-server" --threshold 0.8 --timeout 5 --format short -- python3 "$SANDBOX_DIR/mock_stdio_server.py"
    run_cmd probe --dir "$SANDBOX_DIR/fingerprints_v1" --format long -- python3 "$SANDBOX_DIR/mock_stdio_server.py"
    run_cmd probe --dir "$SANDBOX_DIR/fingerprints_v1" --format json -- python3 "$SANDBOX_DIR/mock_stdio_server.py"
    run_cmd probe --url http://127.0.0.1:8888 --header "Authorization: Bearer test" --format table --dir "$SANDBOX_DIR/fingerprints_v1"'''
)

# Fix 4: detect: stdio target and HTTP URL target, --transport (stdio, http), --timeout, --format (text, json)
content = content.replace(
'''    run_cmd detect --format text "python3 $SANDBOX_DIR/mock_stdio_server.py"
    run_cmd detect --format json http://127.0.0.1:8888/mcp''',
'''    run_cmd detect --transport stdio --timeout 5 --format text "python3 $SANDBOX_DIR/mock_stdio_server.py"
    run_cmd detect --transport http --timeout 5 --format json http://127.0.0.1:8888/mcp'''
)

# Fix 5: match: -i / --input-file (and stdin -), --dir, --server-hint, --threshold, --json
content = content.replace(
'''    run_cmd match -i "$SANDBOX_DIR/observed_tools.json" --dir "$SANDBOX_DIR/fingerprints_v1"''',
'''    run_cmd match -i "$SANDBOX_DIR/observed_tools.json" --dir "$SANDBOX_DIR/fingerprints_v1" --server-hint "test" --threshold 0.5 --json
    cat "$SANDBOX_DIR/observed_tools.json" | uv run mcp-fingerprints match -i - --dir "$SANDBOX_DIR/fingerprints_v1"'''
)

# Fix 6: search: keyword query, --dir, --limit, --semantic
content = content.replace(
'''    run_cmd search "query" --dir "$SANDBOX_DIR/fingerprints_v1" --limit 2''',
'''    run_cmd search "query" --dir "$SANDBOX_DIR/fingerprints_v1" --limit 2
    # --semantic requires fastembed, we just show it's passed, might fallback or succeed.
    run_cmd search "query" --dir "$SANDBOX_DIR/fingerprints_v1" --limit 2 --semantic'''
)

# Fix 7: export-sbom: --passport, --all, --format (cyclonedx, spdx), --output, --dir
import glob
import json
passports = glob.glob("data/fingerprints/*.json")
if passports:
    with open(passports[0], "r") as p:
        data = json.load(p)
        pkg_name = data.get("package_name", "unknown")
else:
    pkg_name = "unknown"
content = content.replace(
'''    run_cmd export-sbom --all --format cyclonedx --dir "$SANDBOX_DIR/fingerprints_v1" --output "$SANDBOX_DIR/sbom.json"
    cat "$SANDBOX_DIR/sbom.json" | head -n 15''',
f'''    run_cmd export-sbom --all --format cyclonedx --dir "$SANDBOX_DIR/fingerprints_v1" --output "$SANDBOX_DIR/sbom.json"
    cat "$SANDBOX_DIR/sbom.json" | head -n 15
    run_cmd export-sbom --passport "{pkg_name}" --format spdx --dir "$SANDBOX_DIR/fingerprints_v1" --output "$SANDBOX_DIR/sbom.spdx.json"'''
)

# Fix 8: validate: --dir, --workers, --no-cache
content = content.replace(
'''    run_cmd validate --dir "$SANDBOX_DIR/fingerprints_v1" --no-cache''',
'''    run_cmd validate --dir "$SANDBOX_DIR/fingerprints_v1" --workers 2 --no-cache'''
)

# Fix 9: snapshot: --data-dir, --output-gz, --output-json
content = content.replace(
'''    run_cmd snapshot --data-dir "$SANDBOX_DIR/fingerprints_v1" --output-gz "$SANDBOX_DIR/snap.json.gz" --output-json "$SANDBOX_DIR/snap.json"
    ls -lh "$SANDBOX_DIR/snap.json"*''',
'''    run_cmd snapshot --data-dir "$SANDBOX_DIR/fingerprints_v1" --output-gz "$SANDBOX_DIR/snap.json.gz" --output-json "$SANDBOX_DIR/snap.json"'''
)

# Fix 10: detect-drift: --old, --new, --webhook-url, --fail-on-tamper, --json, --output
content = content.replace(
'''    run_cmd_exit 1 detect-drift --old "$SANDBOX_DIR/fingerprints_v1" --new "$SANDBOX_DIR/fingerprints_v2" --fail-on-tamper''',
'''    run_cmd_exit 1 detect-drift --old "$SANDBOX_DIR/fingerprints_v1" --new "$SANDBOX_DIR/fingerprints_v2" --fail-on-tamper --webhook-url "http://127.0.0.1:8888/webhook" --json --output "$SANDBOX_DIR/drift.json"'''
)

# Fix custom clients json
content = content.replace(
'''# 2.3 Mock Agent Configs
mkdir -p "$SANDBOX_DIR/configs"''',
'''# 2.3 Mock Agent Configs
mkdir -p "$SANDBOX_DIR/configs"
cat << 'CUST' > "$SANDBOX_DIR/configs/custom_clients.json"
{
  "test_client": {
    "paths": ["test_path.json"]
  }
}
CUST'''
)

with open("demo.sh", "w") as f:
    f.write(content)
