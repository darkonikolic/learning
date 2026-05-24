# Unit 2 — Labs: prod-shaped exercises

## Build & env

- Compare dev HMR bundle vs **`dist/`** output; annotate largest chunks with import graph reasoning.
- Wire **staging vs production** API base URLs purely via env + build artefacts.

## Deploy shape

- **Dockerfile + nginx** (or Compose) serving SPA with sensible caching headers vs HTML freshness.

## Incident tabletops

- **Stale bundle** after deploy (users on old hashed JS): detection + remediation narrative.
- **Checkout timeout** separating browser vs CDN vs API path.
- **CORS regression** vs misconfigured env URLs.
- **Global error spike** traced via monitoring breadcrumbs.

## Checklists

Maintain a **release checklist**: build validation, smoke, monitoring deltas, rollback path.

Interview focus: XSS/CSP/token storage trade-offs, hashed assets + cache busting, header roles, rollback, env separation.
