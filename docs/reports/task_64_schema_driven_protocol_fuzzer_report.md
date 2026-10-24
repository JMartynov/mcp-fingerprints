# Engineering Verification Report: Schema-Driven Protocol Fuzzer (Task 64)

## 1. Module Design and Architecture
The newly implemented schema-driven protocol fuzzer (`src/mcp_fingerprints/fuzzer.py`) provides an automated, dynamic QA harness to enforce JSON-RPC 2.0 conformance and schema resilience in Model Context Protocol (MCP) servers.

The system is composed of several core elements:
- **`PayloadMutator`**: Generates deterministic payloads corresponding to standard fuzzing categories based on actual parameter schemas (`inputSchema`). 
- **`SchemaDrivenFuzzer`**: A sandboxed process orchestrator that dispatches generated JSON-RPC payloads, manages lifecycles (timeout/crash restart loops), and classifies server behavior during the tool calling phase.
- **Reporting structures (`FuzzReport`, `FuzzCaseResult`)**: Track and export standardized fuzz results in both CLI and JSON formats.

## 2. Schema Validation Categories (Coverage)
The `PayloadMutator` deterministically covers the following 8 categories:
1. `type_confusion`: Passing `int` where `string` is required, or objects for arrays.
2. `int64_overflow`: Boundary injection (`2**63 - 1`, `-2**63`, `2**128`, etc.)
3. `deep_nesting`: Sending objects deeply nested up to 64 layers to test recursion limits.
4. `empty_or_null_required`: Passing `null`, `{}` or omitting strict requirement fields.
5. `sql_injection`: Punctuation string inputs (`"test_quote' --"`).
6. `path_traversal`: Injecting `../` segments into fields to verify normalization checks.
7. `command_injection`: Injecting subshell tokens and pipes (`"test | cat"`).
8. `control_bytes`: Sending ASCII control bytes and nulls (`\x00`, `\x07`).

## 3. Sandbox Lifecycle Management
To ensure a safe testing environment that isolates process panics and out-of-memory crashes:
- The system correctly utilizes `RuntimeSandbox` (`src/mcp_fingerprints/runtime_sandbox.py`), which manages robust environment sanitization.
- The state machine implements explicit timeout budgets per JSON-RPC request.
- The process tree is forcefully terminated in the event of timeouts or unhandled exits, effectively restarting a fresh instance of the server so that subsequent fuzzer iterations are not halted by a single crash.

## 4. Unit Test Verification Results
The test suite (`tests/test_fuzzer.py`) successfully asserts:
- Deterministic behavior in `PayloadMutator` seeding.
- Full generation coverage across all 8 defined PayloadCategories.
- Five distinct `FuzzOutcome` classifications (`clean_error`, `handled_result`, `protocol_violation`, `timeout_hang`, `process_crash`) simulated using inline python mock handlers.
- End-to-end integration within the CLI context (`mcp-fingerprints fuzz`).

All tests run cleanly with no regression.

## 5. Protocol Robustness Findings (Classification Examples)
- **High Severity (Crash/Hang):** A failure to catch payload exceptions causing a `process_crash` or stalling entirely causing `timeout_hang` demonstrates missing exception boundary handlers inside the tool function. 
- **Medium Severity (Protocol Violation):** Returning malformed JSON or failing to correctly encapsulate errors in a standard `error` object (`code`, `message`) rather than a string response directly in `stdout`.
- **Low Severity (Clean Error):** Returning a standard JSON-RPC error response (`code: -32602`), correctly handled and bubbled to the client natively. 

