"""Unit tests for PyPI package extraction logic."""

from __future__ import annotations

import io
import json
import tarfile
import urllib.error
import zipfile
from unittest.mock import MagicMock, patch

import pytest

from mcp_fingerprints.synchronizer import PassportSynchronizer


@pytest.fixture
def synchronizer(tmp_path):
    output_dir = tmp_path / "fingerprints"
    return PassportSynchronizer(output_dir=str(output_dir))


def build_mock_wheel(tools_code: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("my_package/server.py", tools_code)
        zf.writestr("my_package/test_server.py", "def test_stuff(): pass")
        zf.writestr("my_package/README.md", "# Hello")
    return buf.getvalue()


def build_mock_sdist(tools_code: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        # server.py
        server_py = tools_code.encode("utf-8")
        ti = tarfile.TarInfo(name="my_package-1.0.0/my_package/main.py")
        ti.size = len(server_py)
        tar.addfile(ti, io.BytesIO(server_py))

        # test file
        test_py = b"def test_stuff(): pass"
        ti = tarfile.TarInfo(name="my_package-1.0.0/my_package/test_main.py")
        ti.size = len(test_py)
        tar.addfile(ti, io.BytesIO(test_py))
    return buf.getvalue()


class MockResponse:
    def __init__(self, data: bytes):
        self._data = data
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
def test_pypi_extractor_wheel_in_memory(mock_urlopen, synchronizer):
    pypi_json = {
        "urls": [
            {"packagetype": "sdist", "url": "https://pypi.org/files/my_package-1.0.0.tar.gz"},
            {"packagetype": "bdist_wheel", "url": "https://pypi.org/files/my_package-1.0.0-py3-none-any.whl"},
        ]
    }

    tools_code = '''
from fastmcp import FastMCP
mcp = FastMCP("demo")

@mcp.tool()
def hello_world(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"
'''
    wheel_bytes = build_mock_wheel(tools_code)

    def side_effect(req, *args, **kwargs):
        if req.full_url == "https://pypi.org/pypi/my_package/json":
            return MockResponse(json.dumps(pypi_json).encode("utf-8"))
        elif req.full_url == "https://pypi.org/files/my_package-1.0.0-py3-none-any.whl":
            return MockResponse(wheel_bytes)
        raise ValueError(f"Unexpected URL: {req.full_url}")

    mock_urlopen.side_effect = side_effect

    tools = synchronizer._extract_tools_from_pypi_package("my_package")

    assert len(tools) == 1
    assert tools[0]["name"] == "hello_world"
    assert "Say hello." in tools[0]["description"]
    assert tools[0]["inputSchema"]["properties"]["name"]["type"] == "string"


@patch("urllib.request.urlopen")
def test_pypi_extractor_sdist_in_memory(mock_urlopen, synchronizer):
    pypi_json = {
        "urls": [
            {"packagetype": "sdist", "url": "https://pypi.org/files/my_package-1.0.0.tar.gz"},
        ]
    }

    tools_code = '''
from fastmcp import FastMCP
mcp = FastMCP("demo")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''
    sdist_bytes = build_mock_sdist(tools_code)

    def side_effect(req, *args, **kwargs):
        if req.full_url == "https://pypi.org/pypi/my_package/json":
            return MockResponse(json.dumps(pypi_json).encode("utf-8"))
        elif req.full_url == "https://pypi.org/files/my_package-1.0.0.tar.gz":
            return MockResponse(sdist_bytes)
        raise ValueError(f"Unexpected URL: {req.full_url}")

    mock_urlopen.side_effect = side_effect

    tools = synchronizer._extract_tools_from_pypi_package("my_package")

    assert len(tools) == 1
    assert tools[0]["name"] == "add_numbers"
    assert "Add two numbers." in tools[0]["description"]
    assert tools[0]["inputSchema"]["properties"]["a"]["type"] == "integer"


@patch("urllib.request.urlopen")
def test_pypi_extractor_size_guard(mock_urlopen, synchronizer):
    pypi_json = {
        "urls": [
            {"packagetype": "bdist_wheel", "url": "https://pypi.org/files/big_package-1.0.0-py3-none-any.whl"},
        ]
    }

    # Generate a payload > 10MB
    large_payload = b"0" * (10 * 1024 * 1024 + 1024)

    def side_effect(req, *args, **kwargs):
        if req.full_url == "https://pypi.org/pypi/big_package/json":
            return MockResponse(json.dumps(pypi_json).encode("utf-8"))
        elif req.full_url == "https://pypi.org/files/big_package-1.0.0-py3-none-any.whl":
            return MockResponse(large_payload)
        raise ValueError(f"Unexpected URL: {req.full_url}")

    mock_urlopen.side_effect = side_effect

    tools = synchronizer._extract_tools_from_pypi_package("big_package")
    assert tools == []  # Rejected gracefully due to size limit

