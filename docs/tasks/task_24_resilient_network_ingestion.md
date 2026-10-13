# Task 24: Resilient Network Ingestion Engine (`tenacity` & HTTP 429 Queues)

### 1. Architectural Context & Technical Objective
Currently, the ingestion engine in `mcp_fingerprints` (specifically when downloading and verifying MCP repositories or interacting with external package registries) lacks robust handling of transient network failures and rate limits. The current implementation can fail pipelines when encountering HTTP 429 (Too Many Requests) or HTTP 500 errors.
The objective of this task is to integrate the `tenacity` library to provide resilient retry logic with exponential backoff and jitter, specifically tailored for network ingestion tasks in `src/mcp_fingerprints/ingestion.py` (or similar modules), ensuring our data pipelines and CI/CD jobs don't randomly fail due to transient external issues. All data ingestion must remain memory-safe and zero-disk-footprint as per architecture guidelines.

### 2. Technical Implementation Specifications
1. Introduce `tenacity` as a dependency in `pyproject.toml`.
2. Implement a new class or module `ResilientIngestionEngine` in `src/mcp_fingerprints/ingestion_engine.py`.
3. Wrap external network calls (e.g., `requests.get` or `httpx.AsyncClient`) with `@retry` decorators using `tenacity`.
4. Configure retry logic:
   - Handle HTTP 429 and HTTP 5xx explicitly.
   - Use `wait_exponential_jitter`.
   - Max retries: 5.
   - Timeout: 60 seconds.
5. Create an asynchronous queue mechanism for bulk ingestion to distribute load and respect rate limits dynamically.

### 3. Clear Acceptance Criteria
- [ ] `tenacity` is added to `pyproject.toml`.
- [ ] Network ingestion calls are wrapped in `tenacity` retry loops.
- [ ] HTTP 429 and 5xx errors trigger retries with exponential backoff and jitter.
- [ ] Bulk ingestion uses an async queue mechanism.

### 4. Unit Test Plan
1. **Mock Setup:** Use `responses` or `pytest-httpx` to mock external endpoints.
2. **Retry Verification:** Mock a sequence of 3 HTTP 429 responses followed by a 200 OK. Assert the function succeeds and the mock was called 4 times.
3. **Failure Verification:** Mock a sequence of 6 HTTP 500 responses. Assert the function eventually raises a retry error after 5 retries.
4. **Queue Verification:** Assert that bulk ingestion processes items concurrently but with a limited concurrency pool (e.g., max 10 concurrent requests).

### 5. Live Acceptance Test Plan
Run `uv run python -c "from mcp_fingerprints.ingestion_engine import fetch_with_retry; fetch_with_retry('http://httpbin.org/status/429,200')"` and observe logs to verify that the retry happens automatically before successfully completing, entirely without mocks.
