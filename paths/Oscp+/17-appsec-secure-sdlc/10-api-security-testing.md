# API Security Testing

API security is its own discipline. REST APIs fail differently from web apps — test BOLA, mass assignment, and auth on every endpoint.

## Resources

- OWASP API Security Top 10: https://owasp.org/www-project-api-security/
- OWASP crAPI lab: https://github.com/OWASP/crAPI
- PortSwigger API testing: https://portswigger.net/web-security/api-testing

## Setup crAPI Lab

```bash
# Full local API security lab
git clone https://github.com/OWASP/crAPI
cd crAPI
docker-compose -f deploy/docker/docker-compose.yml up -d

# App at http://localhost:8888
# Mail server at http://localhost:8025
```

## Recon — Find the API

```bash
# Common API documentation locations
curl http://target/swagger.json
curl http://target/swagger.yaml
curl http://target/openapi.json
curl http://target/api-docs
curl http://target/v1/api-docs
curl http://target/.well-known/openapi

# Fuzz for API paths
ffuf -u http://target/api/FUZZ -w /usr/share/wordlists/SecLists/Discovery/Web-Content/api/api-endpoints.txt

# Check JS files for API calls
grep -r "fetch\|axios\|http\." dist/ --include="*.js" | grep -i "api\|/v[0-9]"
```

## Core API Test Checklist

```
[ ] Auth on every endpoint — remove token, does it still respond?
[ ] BOLA/IDOR — change resource ID to another user's ID
[ ] Mass assignment — add extra fields (isAdmin, role, price)
[ ] HTTP methods — try DELETE/PUT where only GET is expected
[ ] Rate limiting — send 100 requests, is it blocked?
[ ] JWT validation — decode, modify claims, re-encode with no signature
[ ] Input validation — SQL/XSS/command injection in all params
[ ] Error messages — do 4xx/5xx responses leak internal info?
[ ] CORS — does it allow any origin? Does it allow credentials?
[ ] Versioning — does v1 have vulns that v2 patched?
```

## BOLA Testing (Broken Object Level Authorization)

```bash
# Login as user A, get their resource ID
GET /api/v1/users/1234/orders HTTP/1.1
Authorization: Bearer <user_A_token>

# Change ID to user B's ID with user A's token
GET /api/v1/users/5678/orders HTTP/1.1
Authorization: Bearer <user_A_token>    # Should be 403 — often isn't
```

## Mass Assignment Testing

```bash
# Normal registration
POST /api/v1/users
{"username": "test", "password": "pass123"}

# Try adding privileged fields
POST /api/v1/users
{"username": "test", "password": "pass123", "role": "admin", "isAdmin": true, "credit": 9999}
```

## JWT Testing

```bash
# Decode JWT (no verification)
echo "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.xxx" | cut -d. -f2 | base64 -d

# Try algorithm confusion: change alg to "none"
# Header: {"alg":"none","typ":"JWT"}
# Payload: {"sub":"admin","role":"admin"}
# Signature: (empty)

# Burp Suite JWT Editor extension — automates this testing
```

## Automated API Scanning

```bash
# Nuclei API templates
nuclei -u http://target/api -t ~/nuclei-templates/http/exposures/apis/

# Import OpenAPI spec into ZAP for full coverage
# ZAP: Import → OpenAPI Definition File → run active scan

# Postman collection to security test
# Import API collection → run collection with security-focused test scripts
```

## OWASP API Top 10 Quick Reference

```
API1  BOLA — access other users' objects by changing IDs
API2  Broken Auth — weak tokens, no expiry, missing validation
API3  Broken Object Property Auth — mass assignment, excessive data exposure
API4  Unrestricted Resource Consumption — no rate limits
API5  Broken Function Level Auth — user calls admin endpoints
API6  Unrestricted Access to Sensitive Business Flows — no bot protection
API7  SSRF — server fetches user-supplied URL
API8  Security Misconfiguration — verbose errors, open CORS
API9  Improper Inventory Management — old versions, test endpoints in prod
API10 Unsafe API Consumption — trusting third-party API responses
```

## Ethical Note

API testing sends real payloads that modify data. Always use a dedicated test environment with test accounts. Never test against APIs you don't own or have written authorization to test.
