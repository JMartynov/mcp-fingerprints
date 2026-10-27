# Task Contract: Task 89 — Pytest Network Isolation Guard in Unit Tests

## 1. Problem Statement & Motivation
During recent Jules task executions (e.g. Task 58, 85, 87), tests for crawlers, synchronizers, and auditors inadvertently triggered live unmocked HTTP/HTTPS requests to external services (GitHub API, PyPI, and npm registry). This causes:
- Flaky tests vulnerable to remote HTTP 429 rate limits or transient outages.
- Slow test suite runs (averaging ~95s).
- Python 3.14 SSL certificate verification warnings.

`tests/conftest.py` currently only sets `sys.path`. It must be upgraded with a reliable, lightweight socket guard that blocks unmocked outbound network connections during unit test execution while cleanly allowing localhost and socketpair connections needed by internal asyncio and pytest runners.

---

## 2. Technical Scope & Implementation Plan

### A. Network Isolation Guard in `tests/conftest.py`
1. Implement a pytest autouse fixture or socket blocker in `tests/conftest.py`:
   - Intercept `socket.socket.connect` or monkeypatch standard socket connections.
   - Allow local loopback addresses: `127.0.0.1`, `::1`, `localhost`, and `socket.AF_UNIX`.
   - Disallow external IPv4/IPv6 outbound connections when running standard unit tests.
   - If an unmocked network call is attempted:
     - Raise a clear, descriptive `RuntimeError`:
       `"Unmocked network call blocked during unit test: <host>:<port>. Unit tests must mock external HTTP/socket requests."`
2. Integration Test Opt-Out:
   - Provide a `@pytest.mark.network` or `@pytest.mark.integration` marker allowing legitimate live acceptance tests (e.g. `tests/test_live_acceptance_*.py`) to bypass the network guard when explicitly marked.

### B. Unit Test Validation (`tests/test_network_guard.py`)
1. Test that attempting an outbound connection to an external address fails fast with `RuntimeError`.
2. Test that loopback / localhost connections succeed.
3. Test that existing unit tests pass without hanging or unexpected network errors.

### C. Repository Test Suite Verification
Run the full test suite:
```bash
PYTHONPATH=src .venv/bin/pytest -q tests/
```
Ensure all tests pass cleanly without regressions.

---

## 3. Strict Safety & Publication Gates
- **Domain Constraint**: Pure test harness hardening. Zero security or offensive features.
- Clean up any temporary scratch files before finishing.
- Verified test pass required prior to merge.
