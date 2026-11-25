"""Locked ATDD unit tests for AC-105.7: deep_zero_tool_auditor TLS hardening."""

from __future__ import annotations

import inspect
import json
import shutil
import ssl
import subprocess
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import mcp_fingerprints.deep_zero_tool_auditor as auditor_mod
from mcp_fingerprints.deep_zero_tool_auditor import DeepZeroToolAuditor


class _OkHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = json.dumps({"ok": True}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def test_no_cert_none() -> None:
    """Verify deep_zero_tool_auditor has no ssl.CERT_NONE and enforces hostname/cert verification."""
    source = inspect.getsource(auditor_mod)
    assert "CERT_NONE" not in source
    assert "check_hostname = False" not in source

    auditor = DeepZeroToolAuditor()
    ctx = auditor._create_ssl_context()
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_valid_tls_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Paired benign control: valid trusted TLS server succeeds; untrusted TLS is rejected."""
    openssl_bin = shutil.which("openssl")
    assert openssl_bin is not None, "openssl binary is required for local TLS verification test"

    cert_file = tmp_path / "cert.pem"
    key_file = tmp_path / "key.pem"
    subprocess.run(
        [
            openssl_bin,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            str(key_file),
            "-out",
            str(cert_file),
            "-days",
            "1",
            "-nodes",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost,IP:127.0.0.1",
        ],
        check=True,
        capture_output=True,
    )

    server = ThreadingHTTPServer(("127.0.0.1", 0), _OkHandler)
    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ctx.load_cert_chain(certfile=str(cert_file), keyfile=str(key_file))
    server.socket = server_ctx.wrap_socket(server.socket, server_side=True)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        auditor = DeepZeroToolAuditor()

        # Trusted cert via SSL_CERT_FILE succeeds with full verification enabled.
        monkeypatch.setenv("SSL_CERT_FILE", str(cert_file))
        trusted_ctx = auditor._create_ssl_context()
        assert trusted_ctx.verify_mode == ssl.CERT_REQUIRED
        assert trusted_ctx.check_hostname is True
        with urllib.request.urlopen(
            f"https://127.0.0.1:{port}/", context=trusted_ctx, timeout=5
        ) as resp:
            assert resp.status == 200
            assert json.loads(resp.read().decode("utf-8")) == {"ok": True}

        # Untrusted cert without SSL_CERT_FILE must fail verification.
        monkeypatch.delenv("SSL_CERT_FILE", raising=False)
        untrusted_ctx = auditor._create_ssl_context()
        with pytest.raises(urllib.error.URLError):
            urllib.request.urlopen(
                f"https://127.0.0.1:{port}/", context=untrusted_ctx, timeout=5
            )
    finally:
        server.shutdown()
        server.server_close()
