from mcp_fingerprints.config_exporter import (
    patch_jsonc,
    ZedExporter,
    ClineExporter,
    WindsurfExporter,
)


def test_patch_jsonc_preserves_comments():
    original_config = """{
  // Top level comment
  "mcpServers": {
    /* inline comment */
    "existing": {
      "command": "node"
    }
  }
}"""
    server_config = {"command": "uvx", "args": ["test-server"]}
    patched = patch_jsonc(original_config, "mcpServers", "my-server", server_config)

    assert "// Top level comment" in patched
    assert "/* inline comment */" in patched
    assert '"existing":' in patched
    assert '"my-server": {' in patched
    assert '"command": "uvx"' in patched


def test_patch_jsonc_empty_config():
    original_config = ""
    server_config = {"command": "uvx", "args": ["test-server"]}
    patched = patch_jsonc(original_config, "mcpServers", "my-server", server_config)

    assert '"mcpServers": {' in patched
    assert '"my-server": {' in patched
    assert '"command": "uvx"' in patched


def test_zed_exporter_schema():
    base_config = {"command": "npx", "args": ["-y", "zed-server"], "env": {"VAR": "1"}}
    generated = ZedExporter.generate_server_config(base_config)

    assert "command" in generated
    assert generated["command"]["path"] == "npx"
    assert generated["command"]["args"] == ["-y", "zed-server"]
    assert generated["command"]["env"] == {"VAR": "1"}


def test_cline_exporter_schema():
    base_config = {"command": "npx", "args": ["-y", "cline-server"]}
    generated = ClineExporter.generate_server_config(base_config)

    assert generated["command"] == "npx"
    assert generated["args"] == ["-y", "cline-server"]
    assert generated["disabled"] is False
    assert generated["autoApprove"] == []


def test_windsurf_exporter_schema():
    base_config = {"command": "npx", "args": ["-y", "windsurf-server"]}
    generated = WindsurfExporter.generate_server_config(base_config)

    assert generated["command"] == "npx"
    assert generated["args"] == ["-y", "windsurf-server"]
    assert "disabled" not in generated
    assert "autoApprove" not in generated


def test_zed_sse_schema():
    base_config = {
        "type": "sse",
        "url": "https://example.com/sse",
        "headers": {"Authorization": "Bearer x"},
    }
    generated = ZedExporter.generate_server_config(base_config)
    assert generated.get("url") == "https://example.com/sse"
    assert generated.get("headers") == {"Authorization": "Bearer x"}
