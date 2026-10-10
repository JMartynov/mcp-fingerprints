# Contributing to MCP Fingerprints

Welcome to MCP Fingerprints! We're glad you're interested in contributing.

## Project Mission and Architectural Overview

The repository's primary purpose is to extract and fingerprint Model Context Protocol (MCP) tool declarations, and to audit MCP server attack surfaces (Verity Red-Team), using static AST parsing for source code and safe runtime stdio sandboxes for compiled binaries/closed-source servers. Additionally, it implements a pre-computed semantic embeddings index for MCP tool fingerprints using `fastembed` and `numpy` vectorized operations.

## Development Setup

1. **Python version**: You'll need Python 3.10+.
2. **Virtual environment**: We recommend using `uv` for environment management and dependencies.
3. **Install dependencies**:
   Run `uv sync --all-extras` to install the project along with any optional dependency groups (e.g., `semantic`). Alternatively, you can use `pip install -e ".[dev]"`.

## Code Quality Standards

We enforce code quality standards to keep our codebase clean and consistent:
- **Formatting**: We use `ruff`. You can run `uv run ruff check --fix` and `uv run ruff format`.
- **Pre-commit hooks**: Ensure you set up local hooks properly.
- **Type Annotations**: Provide proper type hints for functions and classes.

## Running Tests

Standard unit tests must be fast and self-contained. To run the test suite:

```bash
PYTHONPATH=src uv run pytest tests/
```

Live web connections are reserved for integration tests.

## Contributing Passports (New MCP Server)

To contribute a new MCP Server Passport:
- Add a valid MCP passport JSON file in `data/fingerprints/`.
- Required fields: `passport_schema_version`, `purl`, `package_name`, and `ecosystem`.
- Validate your additions using `mcp-fingerprints validate`.

## Security

Responsible security vulnerability disclosure process:
If you find a security vulnerability, please do not open a public issue. Instead, report it privately to the maintainers to allow for responsible disclosure and remediation.
