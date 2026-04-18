# Publishing Setup

This repo is configured for trusted publishing from GitHub Actions to:

- TestPyPI: `.github/workflows/publish-testpypi.yml`
- PyPI: `.github/workflows/publish-pypi.yml`

## 1. Configure Trusted Publishers (one-time)

In TestPyPI project settings:

- Owner: `kaiqi-eng`
- Repository name: `vfarm-device-sdk`
- Workflow name: `publish-testpypi.yml`
- Environment name: *(leave blank unless you add one)*

In PyPI project settings:

- Owner: `kaiqi-eng`
- Repository name: `vfarm-device-sdk`
- Workflow name: `publish-pypi.yml`
- Environment name: *(leave blank unless you add one)*

## 2. Test publish

Run the TestPyPI workflow manually from GitHub Actions:

- Workflow: **Publish to TestPyPI**
- Trigger: **Run workflow**
- Guard checks enforced in workflow:
  - version changed from latest release tag
  - `CHANGELOG.md` includes current version
  - compatibility matrix entry exists for current version
  - version does not already exist on TestPyPI

## 3. Production publish

Create a GitHub release (published) to trigger PyPI publish:

1. Bump version in `pyproject.toml`
2. Commit and push
3. Create tag and release (e.g. `v0.1.1`)
4. Workflow **Publish to PyPI** runs automatically
5. Workflow guard verifies release tag exactly matches `v<project.version>`

## Release discipline docs

- Full release process and required files: `docs/RELEASE_CHECKLIST.md`
- Compatibility source of truth: `contracts/sdk_compatibility_matrix.json`
- Rendered compatibility table: `docs/SDK_COMPATIBILITY.md`

## 4. Verify install

From PyPI:

```bash
pip install vfarm-device-sdk
```

From TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple vfarm-device-sdk
```
