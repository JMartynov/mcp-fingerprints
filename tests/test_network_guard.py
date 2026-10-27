import pytest
import socket
import urllib.request
import urllib.error

def test_outbound_network_blocked():
    with pytest.raises(RuntimeError) as excinfo:
        # Try to connect to example.com
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("93.184.216.34", 80))
    
    assert "Unmocked network call blocked during unit test" in str(excinfo.value)
    
def test_outbound_urllib_blocked():
    with pytest.raises(RuntimeError) as excinfo:
        urllib.request.urlopen("http://example.com")
        
    assert "Unmocked network call blocked during unit test" in str(excinfo.value)

def test_localhost_allowed():
    # Attempt connecting to localhost. Might fail with ConnectionRefusedError 
    # if no service is running, but it shouldn't raise our RuntimeError
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", 12345))
    except ConnectionRefusedError:
        pass
    except RuntimeError as e:
        pytest.fail(f"Localhost connection unexpectedly blocked: {e}")

@pytest.mark.network
def test_network_marker_bypasses_guard():
    # This might fail with timeout or connection refused in a strict environment,
    # but we just want to ensure our RuntimeError isn't raised
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to a non-existent host/port with a timeout just to trigger connect
        s.settimeout(1)
        s.connect(("8.8.8.8", 53))
    except (socket.timeout, OSError):
        pass
    except RuntimeError as e:
        pytest.fail(f"Connection with @pytest.mark.network unexpectedly blocked: {e}")
