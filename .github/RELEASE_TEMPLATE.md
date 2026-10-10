# Release Checklist

## Pre-flight Checks
- [ ] Verify all tests pass on the main branch.
- [ ] Ensure `CHANGELOG.md` is updated with the latest changes.
- [ ] Verify version bump in relevant files (e.g., `pyproject.toml`, `__init__.py`).

## TestPyPI Dry-Run Verification
- [ ] Run `.github/workflows/test_release.yml` to trigger a dry-run release to TestPyPI.
- [ ] Verify the TestPyPI package installs correctly locally.

## Release Process
- [ ] Create a git tag for the new version: `git tag vX.Y.Z`
- [ ] Push the tag: `git push origin vX.Y.Z`
- [ ] Verify the production `.github/workflows/release.yml` completes successfully with OIDC trusted publishing.

## Post-release
- [ ] Perform a post-release smoke test by installing from PyPI.
- [ ] Publish GitHub Release notes based on the tag and `CHANGELOG.md`.
