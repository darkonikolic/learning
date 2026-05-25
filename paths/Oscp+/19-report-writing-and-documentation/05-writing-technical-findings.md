# Writing Technical Findings

Technical findings must be reproducible by someone who was not on the assessment. A developer reading your finding should be able to reproduce and verify the fix without asking you any questions.

## Specificity Rules

Bad: "There is an injection vulnerability in the login form."

Good: "The `username` parameter in the POST request to `/api/v1/auth/login` is vulnerable to SQL injection. The application constructs the query via string concatenation, bypassing input validation."

Bad: "Data can be accessed by an attacker."

Good: "An attacker can extract all 50,000 user records from the `customers` table, including full names, email addresses, hashed passwords, and billing addresses."

## Evidence Requirements

Every finding needs at minimum:
- Screenshot showing the vulnerability triggered (Burp request + response, or terminal output)
- The exact input used
- The exact output observed

Label all evidence: `Figure 3 — SQLi payload extracting database version (POST /api/login)`

## Steps to Reproduce Format

```
Steps to Reproduce:
1. Open Burp Suite and configure browser proxy to 127.0.0.1:8080
2. Navigate to https://target.com/login
3. Enter any username and password, intercept with Burp
4. Modify the POST body: username=admin'--&password=anything
5. Forward the request
6. Observe: server responds 200 OK and sets authenticated session cookie
   Expected: 401 Unauthorized
```

Numbered. Exact values. Expected vs actual outcome stated.

## Remediation — Be Specific

Bad: "Update the software and implement input validation."

Good:
```
Remediation:
Replace string concatenation with parameterized queries:

  # Vulnerable
  query = "SELECT * FROM users WHERE username = '" + username + "'"

  # Fixed
  cursor.execute("SELECT * FROM users WHERE username = %s", (username,))

Additionally, implement an allowlist for the username field:
  /^[a-zA-Z0-9_]{3,32}$/

Reference: OWASP SQL Injection Prevention Cheat Sheet
https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
```

## Impact — Business Language

Translate technical impact to business risk:
- RCE → "attacker gains full control of the server and everything it can reach"
- SQLi → "attacker can read, modify, or delete all data in the database"
- LFI → "attacker can read sensitive files including credentials and private keys"
- IDOR → "any authenticated user can access any other user's data"

## Proof of Concept Policy

Include enough PoC to prove exploitability. Do not include weaponized exploit code in client reports — show the vulnerability exists, not a complete attack toolkit.
