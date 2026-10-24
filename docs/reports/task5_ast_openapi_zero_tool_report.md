# Technical Report: Live Run and Invariant Test Suite for Polyglot AST Parsers, OpenAPI Specs, Zero-Tool Deep Inspection, and Unicode Sanitization

## Executive Summary
This report summarizes the implementation and execution of a live run and invariant test suite validating `mcp-fingerprints`' deep parser ecosystem. The test suite systematically probes the codebase's Polyglot AST Extraction across six target programming languages (Python, TypeScript, Go, Rust, Java, C#), OpenAPI JSON/YAML Specification Parser, Markdown Document Tool Extraction, and Unicode Sanitization pipelines. The test artifacts establish concrete guarantees that source components extract tool signatures from diverse language environments seamlessly while preserving structural and encoded invariants.

All test assertions evaluated successfully without exception.

## Invariant Conformance Matrix

| Rule | Test Fixture | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| Python FastMCP AST Extraction | `test_ast_python_fastmcp` | Extract `@mcp.tool()` with typed params | Extracted correctly | 🟢 Pass |
| TypeScript Zod AST Extraction | `test_ast_typescript_zod` | Support Dynamic Arrays and Zod Schemas | Extracted correctly | 🟢 Pass |
| Golang mark3labs/mcp-go | `test_ast_go_mcp` | Extract `mcp.NewTool` definitions | Extracted correctly | 🟢 Pass |
| Rust rmcp Macro | `test_ast_rust_mcp` | Extract `#[tool]` annotated functions | Extracted correctly | 🟢 Pass |
| Java Spring AI @Tool | `test_ast_jvm_mcp` | Extract `@Tool` annotated methods | Extracted correctly | 🟢 Pass |
| C# [McpServerTool] | `test_ast_dotnet_mcp` | Extract `[McpServerTool]` properties | Extracted correctly | 🟢 Pass |
| OpenAPI Specification Parsing | `test_openapi_parser` | Parse paths and operation IDs into tools | Extracted endpoints | 🟢 Pass |
| Markdown README Extraction | `test_markdown_doc_parser` | Parse Markdown table into tool definitions | Extracted tools | 🟢 Pass |
| Unicode Sanitization | `test_unicode_sanitization_invariants` | Strip ASCII control bytes, preserve I18N | Control bytes removed | 🟢 Pass |

## Technical Findings by Severity

- 🟢 **Low Severity**: All tested invariants passed. No significant degradation or faults found during AST traversal or semantic metadata parsing.
- 🟢 **Low Severity**: Unicode sanitization cleanly targets targeted byte ranges `[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]`, enabling robust globalization support (e.g., CJK and Emoji properties map safely).

## Code Recommendations & Concrete Patches

- The existing codebase is stable and correct according to the specified constraints.
- No direct code patches are recommended in `mcp_fingerprints.ast_parser`, `mcp_fingerprints.openapi_parser`, `mcp_fingerprints.doc_parser`, or `mcp_fingerprints.sanitizer` at this time.
