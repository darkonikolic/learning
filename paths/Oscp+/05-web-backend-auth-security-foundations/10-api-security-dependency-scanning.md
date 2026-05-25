# API security testing and dependency scanning

APIs have their own OWASP Top 10. Test auth, object-level access, and data exposure separately from web app.

## API recon — find the surface

```bash
# Look for API docs
curl http://target.com/api/docs
curl http://target.com/swagger.json
curl http://target.com/openapi.yaml
curl http://target.com/api/v1/

# Directory fuzzing for API endpoints
gobuster dir -u http://target.com/api/ -w /usr/share/wordlists/dirb/common.txt -x json
feroxbuster -u http://target.com/api/ --extensions json
```

## API auth testing with curl

```bash
# Test unauthenticated access
curl http://target.com/api/users

# Test with valid token
curl http://target.com/api/users \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test BOLA — access another object
curl http://target.com/api/users/2 \
  -H "Authorization: Bearer USER_1_TOKEN"

# Test excessive data exposure
curl http://target.com/api/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
# Check: does response include fields not shown in UI (role, internal ID, hashed password)?

# Test HTTP method override
curl http://target.com/api/users/2 -X DELETE \
  -H "Authorization: Bearer USER_TOKEN"
```

## OWASP API Security Top 10

| # | Name | Quick test |
|---|---|---|
| API1 | BOLA | Change object ID in URL |
| API2 | Broken Auth | Remove token, use expired token |
| API3 | Excessive Data | Compare API response to what UI shows |
| API4 | Rate Limiting | Send 100 requests, check if blocked |
| API5 | Function-Level Auth | Call admin endpoints as regular user |
| API6 | Unrestricted Access to Business Flows | Replay purchase flow multiple times |
| API7 | Server-Side Request Forgery | Inject internal URL in webhook/callback param |
| API8 | Security Misconfiguration | Check CORS, debug endpoints, verbose errors |
| API9 | Improper Inventory Management | Find old API versions: /api/v1 vs /api/v2 |
| API10 | Unsafe Consumption | Third-party API data injected into queries |

## Dependency scanning

```bash
# Node.js
npm audit
npm audit --fix        # auto-fix where possible

# Python
pip install pip-audit
pip-audit

# Ruby
bundle audit

# Container images
trivy image myapp:latest

# Snyk (free tier)
npm install -g snyk
snyk auth
snyk test
```

## Practice

OWASP crAPI (deliberately vulnerable API): https://github.com/OWASP/crAPI
PortSwigger API testing labs: https://portswigger.net/web-security/api-testing
TryHackMe "OWASP API Security Top 10": https://tryhackme.com/room/owaspapisecuritytop105
