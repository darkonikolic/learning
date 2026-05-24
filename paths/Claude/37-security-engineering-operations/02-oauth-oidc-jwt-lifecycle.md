# OAuth2 • OIDC • JWT lifecycle ownership

### OAuth2 / OIDC differentiation (operational viewpoint)

Flows you permit (auth code + PKCE class patterns for SPAs/mobile); **opaque vs JWT access tokens strategy** consciously chosen.

### JWT lifecycle realities

Issuer trust, JWKS rotation, **`kid` rollover playbook**, revocation stories (often partial—document holes), skewed clocks defensive coding, **`aud`, `exp`, `nbf`** rigor—not optional decoration.

Symfony / Go vignettes: middleware validation chokepoints consistent.

### LAB

Produce **JWT Failure Modes Appendix** tied to rollout & dependency upgrade windows.
