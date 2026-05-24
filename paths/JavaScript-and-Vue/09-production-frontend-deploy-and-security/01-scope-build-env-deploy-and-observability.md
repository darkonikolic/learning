# Unit 1 — Scope: production frontend (build, deploy, security, ops)

Mindset shift: from “works on localhost” toward **artefacts, environments, cache, and attack surface.**

## Learning outcomes

- **Build vs dev**: Vite/`npm run build` output anatomy; source maps stance; prod minification/size reality.
- **Environment config**: `.env.*` layering; **`import.meta.env`** (Vite mental model); no secrets baked into client bundles.
- **Delivery path**: artefact → static host / **`nginx`** container / Compose stack — repeatable local prod-like run.
- **Cache busting**: hashed asset filenames vs stale JS after deploy incidents.
- **Security**: XSS mindset; CSP overview; **`httpOnly` cookies vs `localStorage` tokens** — threat-model trade-offs, not zealotry.
- **Security headers** (conceptual CSP, `X-Frame-Options`, HSTS mentions) as infra + app collaboration.
- **Observability**: client error capture hooks (e.g. Sentry-class); bridge user “it broke” reports to breadcrumbs.
- **Incident triage**: cache vs API vs CORS vs timeout hypotheses.

Extend **`shop-spa/`** deployed beside Symfony/fake backend per your lab constraints.
