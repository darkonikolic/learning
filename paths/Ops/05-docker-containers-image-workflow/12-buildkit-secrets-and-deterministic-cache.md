# Unit 12 — BuildKit: build secrets vs cache discipline

BuildKit allows mounting short-lived secrets only during build steps, shrinking the chance they land in immutable layers mirrored to registries. Contrast brittle `COPY` of `.env.build` artefacts—acceptable only on disposable workstations under policy you control explicitly.

Practise: convert one multi-stage Dockerfile to use ephemeral secret mounts fetching private Composer/NPM artefacts; quantify cache invalidation triggers when pinning dependency manifests versus stray README tweaks.

Tie scanners (`18-*`) back in: deterministic rebuilds clarify which layer introduced a CVE escalation when base images churn weekly.
