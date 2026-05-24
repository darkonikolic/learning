# Security Engineering Operations — framing

## Phase framing — SecOps Reality (`37`)

**Units:** `01`–`05` (topic order only).

### Separation from adjacent tracks

| Track | Focus | This phase fills |
|-------|-------|------------------|
| `22-ai-security-engineering` | Model prompt/tool injection class | Operational identity & infra hardening cadence |
| `23-threat-modeling-engineering` | STRIDE & attack surfaces | Lifecycle controls (secrets, certs, scanners) tying mitigations |

Staff expectation: articulate **lifecycle** mechanics (rotation, revocation, blast radius)—not solely «we use JWT.»

Themes: **OAuth2/OIDC**, **JWT lifecycle**, **Secrets rotation**, **KMS/Vault conceptual ownership**, **mTLS/cert lifecycle**, **rate limiting**, **WAF framing**, **OWASP ASVS as checklist lens**, **SBOM/supply chain**, **SAST/DAST positioning**, **container & image scanning**, **runtime security**, **K8s RBAC & NetworkPolicies** reinforcing **`13-production-kubernetes`** & **`05`** appendix.
