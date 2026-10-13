import asyncio
import urllib.error
from unittest.mock import patch, MagicMock

import pytest

from mcp_fingerprints.ingestion_engine import fetch_with_retry, ResilientIngestionEngine


class MockHTTPError(urllib.error.HTTPError):
    def __init__(self, code):
        super().__init__("http://mock", code, "Mock Error", {}, None)

@patch("urllib.request.urlopen")
def test_fetch_with_retry_success_after_429(mock_urlopen):
    # Setup mock to return 429 three times, then 200 OK
    
    mock_response = MagicMock()
    mock_response.__enter__.return_value.read.return_value = b"success"
    
    mock_urlopen.side_effect = [
        MockHTTPError(429),
        MockHTTPError(429),
        MockHTTPError(429),
        mock_response,
    ]
    
    result = fetch_with_retry("http://example.com")
    
    assert result == b"success"
    assert mock_urlopen.call_count == 4


@patch("urllib.request.urlopen")
def test_fetch_with_retry_failure_after_500s(mock_urlopen):
    # Setup mock to return 500 six times
    
    mock_urlopen.side_effect = [
        MockHTTPError(500),
        MockHTTPError(500),
        MockHTTPError(500),
        MockHTTPError(500),
        MockHTTPError(500),
        MockHTTPError(500),
    ]
    
    with pytest.raises(urllib.error.HTTPError):
        fetch_with_retry("http://example.com")
        
    assert mock_urlopen.call_count == 5  # Max attempts is 5

@patch("urllib.request.urlopen")
def test_fetch_with_retry_fails_immediately_on_404(mock_urlopen):
    # 404 should not be retried
    mock_urlopen.side_effect = [
        MockHTTPError(404),
    ]
    
    with pytest.raises(MockHTTPError):
        fetch_with_retry("http://example.com")
        
    assert mock_urlopen.call_count == 1

def test_resilient_ingestion_engine_bulk():
    async def run_test():
        engine = ResilientIngestionEngine(concurrency_limit=2)
        
        active_tasks = 0
        max_active_tasks = 0
        
        async def mock_task():
            nonlocal active_tasks, max_active_tasks
            active_tasks += 1
            max_active_tasks = max(max_active_tasks, active_tasks)
            await asyncio.sleep(0.1)
            active_tasks -= 1
            return "done"
            
        tasks = [mock_task for _ in range(5)]
        
        results = await engine.process_bulk(tasks)
        
        assert results == ["done", "done", "done", "done", "done"]
        assert max_active_tasks == 2  # Concurrency limit should be respected

    asyncio.run(run_test())
