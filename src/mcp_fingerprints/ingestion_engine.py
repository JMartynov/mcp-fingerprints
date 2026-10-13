import asyncio
import logging
import urllib.request
import urllib.error
from typing import Any, Callable, Coroutine
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception

logger = logging.getLogger(__name__)

def _is_retryable_http_error(exception: Exception) -> bool:
    """Check if the exception is an HTTP error that should be retried."""
    if isinstance(exception, urllib.error.HTTPError):
        # 429 Too Many Requests or 5xx Server Errors
        if exception.code == 429 or 500 <= exception.code < 600:
            return True
    return False

@retry(
    wait=wait_exponential_jitter(initial=1, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception(_is_retryable_http_error),
    reraise=True,
)
def fetch_with_retry(url: str, **kwargs: Any) -> bytes:
    """Fetch a URL with exponential backoff and jitter for 429/5xx errors.
    
    Args:
        url: The URL to fetch.
        **kwargs: Additional arguments to pass to urllib.request.urlopen.
        
    Returns:
        The response bytes.
    """
    logger.debug(f"Fetching {url}")
    req = urllib.request.Request(url, **kwargs)
    with urllib.request.urlopen(req) as response:
        return response.read()


class ResilientIngestionEngine:
    """Engine for processing bulk ingestion tasks with rate limit awareness and retries."""
    
    def __init__(self, concurrency_limit: int = 10):
        """Initialize the ingestion engine.
        
        Args:
            concurrency_limit: Maximum number of concurrent tasks.
        """
        self.concurrency_limit = concurrency_limit
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        
    async def process_bulk(self, tasks: list[Callable[[], Coroutine[Any, Any, Any]]]) -> list[Any]:
        """Process a list of tasks concurrently, respecting the concurrency limit.
        
        Args:
            tasks: A list of async callables to execute.
            
        Returns:
            A list of results corresponding to the tasks.
        """
        async def run_task_with_semaphore(task: Callable[[], Coroutine[Any, Any, Any]]) -> Any:
            async with self.semaphore:
                return await task()
                
        return await asyncio.gather(*(run_task_with_semaphore(task) for task in tasks))
