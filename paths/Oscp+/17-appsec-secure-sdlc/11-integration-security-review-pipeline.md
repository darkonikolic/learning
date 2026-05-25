# Integration Security Review Pipeline

End-to-end AppSec review exercise. Take any open-source app and run a full security review in 3–4 hours.

## Resources

- DVWA: https://github.com/digininja/DVWA
- NodeGoat (Node.js): https://github.com/OWASP/NodeGoat
- OWASP Juice Shop: https://github.com/juice-shop/juice-shop
- Security review report template: https://github.com/magicmarkh/pentest-report-template

## Setup Target App

```bash
# Option A: DVWA (PHP)
docker run --rm -p 80:80 vulnerables/web-dvwa

# Option B: Juice Shop (Node.js — more modern)
docker run --rm -p 3000:3000 bkimminich/juice-shop

# Option C: NodeGoat (Express — good for JS review)
git clone https://github.com/OWASP/NodeGoat
cd NodeGoat && docker-compose up
```

## Step 1 — Threat Model (15 min)

```
Pick one feature (e.g., login, user profile, shopping cart)
1. Draw data flow on paper or Threat Dragon
2. Identify all trust boundaries
3. Apply STRIDE — write 1-2 threats per boundary
4. Note the top 3 risks to verify in later steps
```

## Step 2 — SAST (20 min)

```bash
# Clone the app source
git clone https://github.com/OWASP/NodeGoat && cd NodeGoat

# Run Semgrep
semgrep --config=p/javascript .
semgrep --config=p/nodejs .

# Check for secrets
trufflehog git file://. --only-verified

# Manual grep for high-value patterns
grep -rn "exec(\|eval(" . --include="*.js"
grep -rn "password" . --include="*.js" | grep -v "test\|node_modules"
grep -rn "innerHTML" . --include="*.js"
```

## Step 3 — SCA (10 min)

```bash
# Dependency scan
snyk test
# or
npm audit
# or
trivy fs ./

# Note: Juice Shop has many intentional vulns in deps — that's the point
```

## Step 4 — Secrets in History (10 min)

```bash
trufflehog git file://. --json 2>/dev/null | jq '.'
gitleaks detect --source=. -v
```

## Step 5 — Deploy and DAST (30 min)

```bash
# ZAP baseline (passive, fast)
docker run --rm ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t http://localhost:3000 -r zap-report.html

# Nuclei
nuclei -u http://localhost:3000 -severity medium,high,critical

# Nikto
nikto -h http://localhost:3000
```

## Step 6 — Manual Testing of OWASP Top 3 (60 min)

```bash
# Open Burp Suite, proxy browser to localhost

# Test 1: SQL Injection (if applicable)
# → Login form: username = admin'--   password = anything
# → Observe response

# Test 2: Broken Access Control
# → Login as low-priv user
# → Try accessing /admin, /api/v1/users/1 (another user's ID)
# → Modify your user ID in requests

# Test 3: XSS
# → Search fields, profile name, comment boxes
# → Payload: <script>alert(1)</script>
# → Payload: <img src=x onerror=alert(1)>
```

## Step 7 — Security Review Report

```markdown
# Security Review — [App Name] — [Date]

## Scope
- Application: Juice Shop v15.x
- Review type: Lightweight security review
- Duration: 4 hours

## Findings

### FINDING-001: SQL Injection in Login Form
- Severity: Critical
- Location: app/routes/login.js line 42
- Evidence: `' OR '1'='1` bypasses authentication
- Remediation: Use parameterized queries with pg/mysql2

### FINDING-002: Hardcoded JWT Secret
- Severity: High
- Location: config/env/all.js line 12
- Evidence: `secret: 'keyboard cat'`
- Remediation: Load from environment variable, rotate secret

### FINDING-003: Missing Rate Limiting on Login
- Severity: Medium
- Location: POST /rest/user/login
- Evidence: 1000 requests sent, none blocked
- Remediation: Add express-rate-limit middleware

## Summary
3 findings: 1 Critical, 1 High, 1 Medium
Immediate action required on FINDING-001 and FINDING-002.
```

## Time Budget for 3-4 Hour Review

```
15 min  — Threat modeling
20 min  — SAST + secrets
10 min  — SCA
30 min  — DAST
60 min  — Manual testing
45 min  — Report writing
```
