# Unit 1 — Backend security threat model (OWASP-flavoured realism)

Security is not “add JWT and done.” Start from assets, trust boundaries, attackers, and blast radius.

Themes to internalise:

```
authn vs authz
secret lifecycle
rate limiting & abuse patterns
SSRF when fetching user-supplied URLs
mTLS for internal east-west (often mesh/ingress assisted)
```

Practice: write a 1-page mini threat model for **`auth-service/`** capstone path (Unit 10).
