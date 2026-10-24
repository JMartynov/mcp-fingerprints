# Task Contract: Task 64 — Schema-Driven Active Protocol Fuzzer (`mcp-fingerprints fuzz`)

## 1. Problem Statement
In the Task 8 security benchmark ([`docs/reports/task8_fuzzing_guardrails_benchmark_report.md`](../reports/task8_fuzzing_guardrails_benchmark_report.md) and [`docs/reports/ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md`](../reports/ECOSYSTEM_BENCHMARK_AND_GAP_ANALYSIS_REPORT.md)), we evaluated `mcp-fingerprints` against active security fuzzers and AI guardrail suites (Protect AI Guardian, Verity OWASP Agentic Top 10, NVIDIA Garak, Mindgard).

While `mcp-fingerprints` extracts canonical `inputSchema` JSON Schemas across 6 programming languages and operates a hardened subprocess execution sandbox (`src/mcp_fingerprints/runtime_sandbox.py`) with credential scrubbing and process-tree reaping, its live probing (`stdio_prober.py`) stops after a passive `initialize` and `tools/list` handshake. It never exercises `tools/call` with malformed, boundary, or adversarial inputs to verify whether target MCP servers handle invalid parameters gracefully (`-32602 Invalid params`) or suffer from uncaught exceptions, process crashes, infinite hangs, or JSON-RPC 2.0 protocol violations.

**Task 64** closes this dynamic security testing gap by implementing the **Schema-Driven Active Protocol Fuzzer (`mcp-fingerprints fuzz`)**, synthesizing boundary and adversarial payloads directly from canonical `inputSchema` definitions and executing them inside `runtime_sandbox.py`.

---

## 2. Technical Requirements & Deliverables

### A. Schema-Driven Fuzzing Engine (`src/mcp_fingerprints/fuzzer.py`)
Create `src/mcp_fingerprints/fuzzer.py` with the following core components:

1. **`PayloadCategory` (`str, Enum`)**:
   - `"type_confusion"` — Supplies wrong JSON types (e.g., string for integer, array for string, boolean for object).
   - `"int64_overflow"` — Supplies boundary numbers (`2**63 - 1`, `-2**63`, `2**128`, `0`, `-1`, `1e308`, `-1e308`).
   - `"deep_nesting"` — Supplies deeply nested JSON objects/arrays (e.g., 32–64 levels deep) to test recursion limits.
   - `"empty_or_null_required"` — Omits required fields or sets required fields to `None` / `""` / `{}`.
   - `"sql_injection"` — Injects canonical SQLi probe strings (`"' OR '1'='1' --"`, `"1; DROP TABLE users--"`).
   - `"path_traversal"` — Injects path traversal sequences (`"../../../../etc/passwd"`, `"..\\..\\..\\windows\\win.ini"`, `"/etc/shadow"`).
   - `"command_injection"` — Injects shell metacharacter strings (`"; id #"`, `"$(whoami)"`, `` "`id`" ``, `"| cat /etc/passwd"`).
   - `"control_bytes"` — Injects null bytes and ASCII control characters (`"test\x00null\x07\x1b[31m"`).

2. **`FuzzOutcome` (`str, Enum`)**:
   - `"clean_error"` — Server returned a valid JSON-RPC 2.0 `error` response (e.g., `-32602` Invalid params or `-32603` Internal error) without crashing.
   - `"handled_result"` — Server returned a valid JSON-RPC 2.0 `result` response (including MCP `isError: true` content blocks).
   - `"protocol_violation"` — Server emitted malformed non-JSON stdout, missing `"jsonrpc": "2.0"`, mismatched `id`, or returned neither `result` nor `error`.
   - `"timeout_hang"` — Server failed to respond within the per-request timeout budget and had to be terminated.
   - `"process_crash"` — Server process exited unexpectedly with a non-zero exit code or signal (`SIGSEGV`, `SIGABRT`, unhandled exception EOF).

3. **`PayloadMutator`**:
   - Given a tool name and its JSON Schema (`inputSchema: Dict[str, Any]`), deterministically generates a list of `(PayloadCategory, Dict[str, Any])` test payloads covering all 8 categories above, respecting `--iterations <N>` cap per tool.

4. **`FuzzCaseResult` & `FuzzReport` (Pydantic models or dataclasses)**:
   - `FuzzCaseResult`: `tool_name: str`, `category: PayloadCategory`, `payload: Dict[str, Any]`, `outcome: FuzzOutcome`, `duration_ms: float`, `error_code: Optional[int]`, `detail: str`.
   - `FuzzReport`: `target_command: List[str]`, `passport_name: Optional[str]`, `total_cases: int`, `clean_errors: int`, `handled_results: int`, `protocol_violations: int`, `timeouts: int`, `crashes: int`, `results: List[FuzzCaseResult]`, plus `to_dict()` / `to_json()` serialization and a `passed: bool` property (`protocol_violations == 0 and timeouts == 0 and crashes == 0`).

5. **`SchemaDrivenFuzzer`**:
   - Accepts target command (`List[str]`), optional passport/schema list, `iterations: int = 10`, and `timeout: float = 5.0`.
   - Uses `RuntimeSandbox` (`src/mcp_fingerprints/runtime_sandbox.py`) so all sensitive host environment variables (`AWS_*`, `OPENAI_*`, `GITHUB_*`, `ANTHROPIC_*`, `SSH_AUTH_SOCK`) are scrubbed and child process trees are strictly reaped on timeout or crash.
   - Performs standard MCP JSON-RPC 2.0 handshake (`initialize` -> `notifications/initialized`). If `--passport` is not provided, dynamically queries `tools/list` from the live server to obtain tool `inputSchema` definitions; if `--passport` is provided, loads tool schemas from the passport (or merges with live `tools/list`).
   - Sends `tools/call` JSON-RPC requests for each generated payload, classifies the outcome (`FuzzOutcome`), and restarts the sandboxed process if a crash/timeout occurs so remaining test cases can complete.

### B. CLI Subcommand (`src/mcp_fingerprints/cli.py`)
Register the `fuzz` subcommand in `src/mcp_fingerprints/cli.py`:
```bash
mcp-fingerprints fuzz \
  [--passport <name_or_path>] \
  [--iterations <N>] \
  [--timeout <sec>] \
  [--output <file>] \
  -- <command> [args...]
```
- Supports writing the JSON `FuzzReport` to `--output <file>` and printing a concise human-readable summary table to `stdout`.

### C. Comprehensive Unit Tests (`tests/test_fuzzer.py`)
Create `tests/test_fuzzer.py` covering:
1. **`PayloadMutator` Determinism & Coverage**:
   - Verify that given a tool schema with `string`, `integer`, `boolean`, `array`, and `object` properties plus `required` fields, `PayloadMutator` generates payloads across all 8 `PayloadCategory` types (`type_confusion`, `int64_overflow`, `deep_nesting`, `empty_or_null_required`, `sql_injection`, `path_traversal`, `command_injection`, `control_bytes`).
2. **Live Subprocess Fuzzing Classification (`clean_error`, `protocol_violation`, `timeout_hang`, `process_crash`)**:
   - Spawn synthetic inline Python MCP mock servers (`python3 -c "..."`) over stdio:
     - A resilient server that returns proper JSON-RPC 2.0 `-32602` errors on bad types (`FuzzOutcome.CLEAN_ERROR`).
     - A buggy server that crashes (`sys.exit(1)`) when receiving an integer overflow or SQLi payload (`FuzzOutcome.PROCESS_CRASH`).
     - A server that outputs invalid non-JSON stdout (`FuzzOutcome.PROTOCOL_VIOLATION`).
     - A hanging server (`time.sleep(30)`) that triggers the sandbox timeout (`FuzzOutcome.TIMEOUT_HANG`) within the configured timeout window.
3. **CLI Integration**:
   - Verify `mcp-fingerprints fuzz --iterations 5 --timeout 2.0 --output <tmp.json> -- python3 -c "<mock_server>"` writes a valid JSON report.

---

## 3. Non-Interactive Completion Directive
**IMPORTANT — NON-INTERACTIVE EXECUTION DIRECTIVE:**
Do NOT ask open-ended questions or wait for user confirmation. Implement all specified modules, CLI wiring, and unit tests autonomously. Run `pytest tests/test_fuzzer.py` and `pytest tests/test_dataset_sanitization.py` to verify 100% pass rates, commit all changes cleanly to your branch, and finalize the session so the Cloud VM transitions directly to `Completed`.
