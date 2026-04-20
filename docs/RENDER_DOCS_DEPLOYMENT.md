# Render Docs Deployment

This repository includes:

- a Render Blueprint in `render.yaml` for a free static site, and
- a GitHub Actions workflow (`.github/workflows/deploy-docs-render.yml`) for continuous deployment.

## 1. Create the Render static site from Blueprint

1. In Render, go to **New > Blueprint**.
2. Select this repository and the `main` branch.
3. Confirm `render.yaml` is detected.
4. Deploy the Blueprint.

The service name in the blueprint is `vfarm-device-sdk-docs` and uses the free static plan.

## 2. Create a Render Deploy Hook

1. Open the created static site in Render.
2. Go to **Settings > Deploy Hook**.
3. Create/copy the deploy hook URL.

## 3. Add GitHub Secret

In GitHub repo settings, add:

- `RENDER_DOCS_DEPLOY_HOOK_URL`: the deploy hook URL copied from Render.

## 4. Continuous Deployment Behavior

The workflow deploys on pushes to `main` when relevant docs/source files change, and on manual dispatch.

Workflow path:

- `.github/workflows/deploy-docs-render.yml`

Pipeline steps:

1. install dependencies
2. run docs completeness check
3. run strict Sphinx build (`-W --keep-going`)
4. call Render deploy hook

## Notes

- `render.yaml` sets `autoDeployTrigger: off` intentionally, so deployments are controlled by the GitHub workflow.
- If you prefer Render-managed auto deploys, switch `autoDeployTrigger` to `checksPass` or `commit`.
