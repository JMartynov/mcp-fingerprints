"""Unit tests for npm tarball multi-layout batch extraction."""

import io
import json
import tarfile
from unittest.mock import MagicMock, patch

import pytest

from mcp_fingerprints.synchronizer import PassportSynchronizer


@pytest.fixture
def synchronizer(tmp_path):
    output_dir = tmp_path / "fingerprints"
    return PassportSynchronizer(output_dir=str(output_dir))


def build_mock_tarball(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path, code in files.items():
            encoded = code.encode("utf-8")
            ti = tarfile.TarInfo(name=path)
            ti.size = len(encoded)
            tar.addfile(ti, io.BytesIO(encoded))
    return buf.getvalue()


class MockResponse:
    def __init__(self, data: bytes, status: int = 200):
        self._data = data
        self.status = status
        self._pos = 0

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            res = self._data[self._pos :]
            self._pos = len(self._data)
            return res
        else:
            res = self._data[self._pos : self._pos + size]
            self._pos += size
            return res

    def decode(self, *args, **kwargs):
        return self._data.decode(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


@patch("urllib.request.urlopen")
def test_npm_tarball_nested_dist_extraction(mock_urlopen, synchronizer):
    npm_meta = {
        "dist-tags": {"latest": "1.0.0"},
        "versions": {
            "1.0.0": {
                "dist": {
                    "tarball": "https://registry.npmjs.org/my-pkg/-/my-pkg-1.0.0.tgz"
                }
            }
        }
    }

    server_code = """
server.tool("dist_tool", "Dist tool description", { query: z.string() }, async () => {});
"""
    tar_bytes = build_mock_tarball({
        "package/package.json": '{"name": "my-pkg", "version": "1.0.0"}',
        "package/dist/index.js": server_code,
    })

    def side_effect(req, *args, **kwargs):
        if req.full_url == "https://registry.npmjs.org/my-pkg":
            return MockResponse(json.dumps(npm_meta).encode("utf-8"))
        elif req.full_url == "https://registry.npmjs.org/my-pkg/-/my-pkg-1.0.0.tgz":
            return MockResponse(tar_bytes)
        raise ValueError(f"Unexpected url {req.full_url}")

    mock_urlopen.side_effect = side_effect

    tools = synchronizer._extract_tools_from_npm_tarball("my-pkg")

    assert len(tools) == 1
    assert tools[0]["name"] == "dist_tool"
    assert tools[0]["description"] == "Dist tool description"


@patch("urllib.request.urlopen")
def test_npm_tarball_build_and_bin_fallback(mock_urlopen, synchronizer):
    npm_meta = {
        "dist-tags": {"latest": "1.0.0"},
        "versions": {
            "1.0.0": {
                "dist": {
                    "tarball": "https://registry.npmjs.org/cli-pkg/-/cli-pkg-1.0.0.tgz"
                }
            }
        }
    }

    server_code = """
server.tool("cli_cmd", "Execute CLI command", { cmd: z.string() }, async () => {});
"""
    tar_bytes = build_mock_tarball({
        "package/package.json": '{"name": "cli-pkg", "version": "1.0.0"}',
        "package/bin/index.js": server_code,
    })

    def side_effect(req, *args, **kwargs):
        if req.full_url == "https://registry.npmjs.org/cli-pkg":
            return MockResponse(json.dumps(npm_meta).encode("utf-8"))
        elif req.full_url == "https://registry.npmjs.org/cli-pkg/-/cli-pkg-1.0.0.tgz":
            return MockResponse(tar_bytes)
        raise ValueError(f"Unexpected url {req.full_url}")

    mock_urlopen.side_effect = side_effect

    tools = synchronizer._extract_tools_from_npm_tarball("cli-pkg")

    assert len(tools) == 1
    assert tools[0]["name"] == "cli_cmd"
