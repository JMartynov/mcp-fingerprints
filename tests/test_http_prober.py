import json
import threading
import time
import unittest
import queue
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from unittest import mock

from mcp_fingerprints import identify_http, identify_stdio
from mcp_fingerprints.prober import McpHttpProber

sse_queues = []

class MockSSEHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self.wfile.write(b"event: endpoint\n")
        self.wfile.write(b"data: /message\n\n")
        self.wfile.flush()
        
        q = queue.Queue()
        sse_queues.append(q)
        
        try:
            # Keep alive to act as an SSE stream
            for _ in range(50):
                try:
                    resp = q.get(timeout=0.1)
                    self.wfile.write(f"data: {json.dumps(resp)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    time.sleep(0.05)
        except Exception:
            pass
        finally:
            if q in sse_queues:
                sse_queues.remove(q)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length))
        
        method = data.get("method")
        msg_id = data.get("id")
        
        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"protocolVersion": "2024-11-05", "capabilities": {}}
            }
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [{"name": "mock_http_tool", "description": "Mock HTTP"}]
                }
            }
        else:
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        # Send response through SSE stream
        for q in sse_queues:
            q.put(resp)

        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class TestHttpProber(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("localhost", 0), MockSSEHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.1)
        
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()

    def test_mcp_http_prober(self):
        prober = McpHttpProber()
        url = f"http://localhost:{self.port}/sse"
        
        report = prober.probe(url=url, timeout=2.0)
        
        self.assertTrue(report.connection_successful)
        self.assertEqual(len(report.tools_observed), 1)
        self.assertEqual(report.tools_observed[0]["name"], "mock_http_tool")

    def test_identify_http_sdk(self):
        url = f"http://localhost:{self.port}/sse"
        report = identify_http(url, timeout=2.0)
        self.assertTrue(report.connection_successful)
        self.assertEqual(len(report.tools_observed), 1)

    @mock.patch("mcp_fingerprints.prober.McpStdioProber.probe")
    def test_identify_stdio_sdk(self, mock_probe):
        from mcp_fingerprints.prober import ProbeReport
        mock_probe.return_value = ProbeReport(
            server_command=["mock"],
            connection_successful=True,
            tools_observed=[{"name": "mock_stdio_tool"}]
        )
        report = identify_stdio(["mock"], timeout=1.0)
        self.assertTrue(report.connection_successful)
        self.assertEqual(report.tools_observed[0]["name"], "mock_stdio_tool")

if __name__ == "__main__":
    unittest.main()
