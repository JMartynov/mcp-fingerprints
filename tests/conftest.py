import sys
import socket
from pathlib import Path
import pytest

# Add project root to PYTHONPATH so tests can import from 'scripts'
sys.path.insert(0, str(Path(__file__).parent.parent))

# Keep a reference to the original socket.connect
_original_socket_connect = socket.socket.connect

ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}

def _blocked_connect(self, address):
    # address is usually a tuple (host, port) for AF_INET/AF_INET6
    # or a string for AF_UNIX
    if isinstance(address, tuple):
        host = address[0]
        if host not in ALLOWED_HOSTS:
            raise RuntimeError(f"Unmocked network call blocked during unit test: {host}:{address[1]}. Unit tests must mock external HTTP/socket requests.")
    return _original_socket_connect(self, address)

@pytest.fixture(autouse=True)
def network_guard(request):
    """
    Blocks outgoing network requests by monkeypatching socket.connect.
    Can be bypassed using the @pytest.mark.network or @pytest.mark.integration marker.
    """
    if request.node.get_closest_marker("network") or request.node.get_closest_marker("integration"):
        yield
        return
        
    socket.socket.connect = _blocked_connect
    try:
        yield
    finally:
        socket.socket.connect = _original_socket_connect

def pytest_configure(config):
    config.addinivalue_line("markers", "network: mark test to allow external network access")
    config.addinivalue_line("markers", "integration: mark test to allow external network access")
