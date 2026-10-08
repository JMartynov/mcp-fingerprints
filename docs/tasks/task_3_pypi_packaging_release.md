# Task Specification: PyPI Packaging & Automated Release Pipeline

## Objective
Enable seamless distribution of `mcp-fingerprints` to Python Package Index (PyPI) by enriching package metadata in `pyproject.toml`, configuring package data, and establishing an automated GitHub Actions release pipeline using trusted publishing.

## Scope & Requirements
1. **Metadata & Packaging Configuration (`pyproject.toml`)**:
   - Add rich metadata:
     - `authors = [{name = "MCP Fingerprints Contributors"}]`
     - `license = {text = "MIT"}`
     - `keywords = ["mcp", "model-context-protocol", "security", "fingerprints", "ai-agents", "llm"]`
     - `classifiers`:
       - `Development Status :: 5 - Production/Stable`
       - `Intended Audience :: Developers`
       - `Topic :: Security`
       - `License :: OSI Approved :: MIT License`
       - `Programming Language :: Python :: 3`
       - `Programming Language :: Python :: 3.10`
       - `Programming Language :: Python :: 3.11`
       - `Programming Language :: Python :: 3.12`
     - `urls`:
       - `Homepage = "https://jmartynov.github.io/mcp-fingerprints/"`
       - `Repository = "https://github.com/JMartynov/mcp-fingerprints"`
       - `Issues = "https://github.com/JMartynov/mcp-fingerprints/issues"`
2. **Release GitHub Action (`.github/workflows/release.yml`)**:
   - Trigger on:
     - `release: [published]`
     - `workflow_dispatch:`
   - Permissions: `id-token: write`, `contents: read`
   - Jobs:
     - `build`:
       - Checkout repo
       - Set up Python 3.12
       - Install `build`
       - Run `python -m build`
       - Verify built wheel and sdist files exist in `dist/`
     - `publish`:
       - Needs: `build`
       - Uses `pypa/gh-action-pypi-publish@release/v1` (with `skip-existing: true` or environment `pypi`)
3. **Tests & Validation**:
   - Create `tests/test_packaging_metadata.py`:
     - Test `pyproject.toml` contains valid version, classifiers, entry points, and dependencies.
     - Test `.github/workflows/release.yml` syntax, trigger conditions, and PyPI publish action.

## Acceptance Criteria
- [ ] `pyproject.toml` contains complete PyPI metadata (classifiers, keywords, urls, author).
- [ ] `.github/workflows/release.yml` is defined with build and publish jobs using trusted publishing.
- [ ] Unit tests pass verifying packaging metadata and workflow integrity.
