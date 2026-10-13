# Task 32: Strict JSON-RPC 2.0 & MCP Protocol Conformance Validator

### 1. Architectural Context & Technical Objective
The Model Context Protocol operates over JSON-RPC 2.0 via `stdio` or HTTP/SSE. Currently, `mcp_fingerprints` assumes servers behave correctly during extraction or probing.
The objective is to implement a strict protocol conformance validator tool (`validate-protocol`) that actively probes a running server and asserts its responses adhere perfectly to the JSON-RPC 2.0 specification (e.g., correct `jsonrpc` version string, proper handling of `id`, valid `error` object structures) and the specific MCP initialization handshake sequence.

### 2. Technical Implementation Specifications
1. Create `src/mcp_fingerprints/protocol_validator.py`.
2. Implement specific test suites for JSON-RPC 2.0 compliance:
   - Missing `jsonrpc: "2.0"` field.
   - Malformed `id` reflection.
   - Structured Error handling (Code, Message).
3. Implement specific test suites for MCP compliance:
   - Proper `initialize` request and response structure.
   - Proper `notifications/initialized` sequence.
4. Update the CLI with a `validate-protocol` command.

### 3. Clear Acceptance Criteria
- [ ] Protocol validation test suites implemented for JSON-RPC 2.0 and MCP handshake.
- [ ] CLI command `validate-protocol` exists.
- [ ] Validator detects missing `jsonrpc` fields and malformed errors.
- [ ] Zero reliance on heavy third-party JSON schema libraries.

### 4. Unit Test Plan
1. **Valid Sequence:** Provide a mock sequence of valid JSON-RPC strings representing a perfect initialization handshake. Assert the validator returns success.
2. **Missing jsonrpc Field:** Provide a mock response missing `"jsonrpc": "2.0"`. Assert the validator flags a strict JSON-RPC 2.0 violation.
3. **Invalid Error Object:** Provide an error response missing the `code` integer field. Assert the validator flags an invalid error object structure.

### 5. Live Acceptance Test Plan
Use `uv run mcp-fingerprints validate-protocol <path-to-test-server-binary>`. The command should spawn the server, perform the handshake, deliberately send a malformed request, and verify the server's error response compliance, printing a pass/fail report to stdout.
