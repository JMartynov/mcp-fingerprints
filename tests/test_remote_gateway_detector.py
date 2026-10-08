import io
import json
import tarfile
import pytest
from unittest.mock import patch, MagicMock

from mcp_fingerprints.synchronizer import PassportSynchronizer
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint


def test_detect_remote_gateway_hardcoded():
    syncer = PassportSynchronizer(output_dir="data/test_fingerprints")
    code = """
    import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
    import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';
    const transport = new SSEClientTransport(new URL("https://mcp.tridentchart.com/mcp"));
    """
    conns, caps = syncer._detect_remote_gateway(code)
    assert len(conns) == 1
    assert conns[0]["type"] == "streamable-http"
    assert conns[0]["deploymentUrl"] == "https://mcp.tridentchart.com/mcp"
    assert caps.get("proxy_gateway") is True
    assert caps.get("remote_endpoint") is True


def test_detect_remote_gateway_env_fallback():
    syncer = PassportSynchronizer(output_dir="data/test_fingerprints")
    code = """
    const mcp_url = process.env.MCP_URL || 'https://mcp.apiguru.app/mcp';
    """
    conns, caps = syncer._detect_remote_gateway(code)
    assert len(conns) == 1
    assert conns[0]["type"] == "streamable-http"
    assert conns[0]["deploymentUrl"] == "https://mcp.apiguru.app/mcp"
    assert caps.get("proxy_gateway") is True
    assert caps.get("remote_endpoint") is True


def test_detect_remote_gateway_no_match():
    syncer = PassportSynchronizer(output_dir="data/test_fingerprints")
    code = """
    import { Server } from '@modelcontextprotocol/sdk/server/index.js';
    server.tool("test_tool", {}, () => {});
    """
    conns, caps = syncer._detect_remote_gateway(code)
    assert len(conns) == 0
    assert not caps


def test_merge_and_enrich_passport_with_remote_gateway():
    syncer = PassportSynchronizer(output_dir="data/test_fingerprints")
    gateway_conns = [{
        "type": "streamable-http",
        "deploymentUrl": "https://mcp.apiguru.app/mcp",
        "configSchema": {},
    }]
    gateway_caps = {"proxy_gateway": True, "remote_endpoint": True}

    npm_data = {
        "dist-tags": {"latest": "1.0.0"},
        "time": {"1.0.0": "2026-01-01T00:00:00Z"},
        "versions": {
            "1.0.0": {
                "name": "apiguru-mcp",
                "version": "1.0.0",
                "dependencies": {},
            }
        },
        "description": "APIs.guru OpenAPI search & exploration MCP gateway",
    }

    spec = syncer.merge_and_enrich_passport(
        package_name="apiguru-mcp",
        ecosystem="npm",
        npm_data=npm_data,
        auto_cross_resolve=False,
        pre_extracted_connections=gateway_conns,
        pre_extracted_capabilities=gateway_caps,
    )

    assert spec is not None
    assert len(spec.versions) == 1
    v = spec.versions[0]
    assert len(v.connections) == 1
    assert v.connections[0]["type"] == "streamable-http"
    assert v.connections[0]["deploymentUrl"] == "https://mcp.apiguru.app/mcp"
    assert v.capabilities.get("proxy_gateway") is True
    assert v.capabilities.get("remote_endpoint") is True


def test_detect_remote_gateway_from_npm_tarball_mocked():
    syncer = PassportSynchronizer(output_dir="data/test_fingerprints")

    # Create an in-memory tarball containing gateway proxy JS code
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tar:
        code_bytes = b"const endpoint = 'https://mcp.tridentchart.com/mcp';\n"
        ti = tarfile.TarInfo(name="package/dist/index.js")
        ti.size = len(code_bytes)
        tar.addfile(ti, io.BytesIO(code_bytes))
    tar_bytes = tar_buf.getvalue()

    metadata_resp = MagicMock()
    metadata_resp.read.return_value = json.dumps({
        "dist-tags": {"latest": "1.0.0"},
        "versions": {
            "1.0.0": {
                "dist": {"tarball": "https://registry.npmjs.org/trident-mcp/-/trident-mcp-1.0.0.tgz"}
            }
        }
    }).encode("utf-8")
    metadata_resp.__enter__.return_value = metadata_resp
    metadata_resp.__exit__.return_value = False

    tarball_resp = MagicMock()
    tarball_resp.read.side_effect = [tar_bytes, b""]
    tarball_resp.__enter__.return_value = tarball_resp
    tarball_resp.__exit__.return_value = False

    with patch("urllib.request.urlopen", side_effect=[metadata_resp, tarball_resp]):
        conns, caps = syncer._detect_remote_gateway_from_npm_tarball("trident-mcp")

    assert len(conns) == 1
    assert conns[0]["type"] == "streamable-http"
    assert conns[0]["deploymentUrl"] == "https://mcp.tridentchart.com/mcp"
    assert caps.get("proxy_gateway") is True
    assert caps.get("remote_endpoint") is True
