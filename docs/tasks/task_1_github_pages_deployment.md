# Task Specification: GitHub Pages Deployment Workflow

## Objective
Automate the deployment of the static web catalog (`web/`) to GitHub Pages so that the 5,000+ server directory is publicly accessible at `https://jmartynov.github.io/mcp-fingerprints/`.

## Scope & Requirements
1. **GitHub Pages Workflow** (`.github/workflows/deploy_pages.yml`):
   - Trigger on push to `main` when files in `web/` or `scripts/generate_web_catalog.py` change.
   - Also allow `workflow_dispatch`.
   - Set required permissions: `contents: read`, `pages: write`, `id-token: write`.
   - Steps:
     - Checkout repository.
     - Set up Python 3.12.
     - Compile latest `web/catalog.json` using `PYTHONPATH=src:. python scripts/generate_web_catalog.py`.
     - Upload `web/` artifact using `actions/upload-pages-artifact@v3` with path `web`.
     - Deploy to GitHub Pages using `actions/deploy-pages@v4`.
2. **README Link & Live Badge**:
   - Update `README.md` to feature the live web directory link and a badge:
     `[![Web Directory](https://img.shields.io/badge/Web_Directory-Live_Catalog-38bdf8?style=flat-square&logo=googlechrome)](https://jmartynov.github.io/mcp-fingerprints/)`
3. **Tests & Validation**:
   - Add test in `tests/test_ci_pipeline.py` or new `tests/test_pages_workflow.py` validating that `.github/workflows/deploy_pages.yml` is valid YAML and defines standard GitHub Pages actions.

## Acceptance Criteria
- [ ] `.github/workflows/deploy_pages.yml` exists and uses official GitHub Pages actions (`upload-pages-artifact@v3`, `deploy-pages@v4`).
- [ ] `README.md` includes the live web catalog badge and URL.
- [ ] Unit test verifies workflow syntax and structure without errors.
