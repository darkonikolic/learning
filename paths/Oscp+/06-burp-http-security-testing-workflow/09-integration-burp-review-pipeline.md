# Full Burp Review Pipeline

End-to-end testing workflow on DVWA. Run this pipeline on every new target.

## Target: DVWA (Security Level = Low)

```bash
docker run -d -p 80:80 vulnerables/web-dvwa
# Browse to http://localhost — login admin/password — set security to Low
```

## Step 1 — Populate History

Set Intercept OFF. Browse every page in DVWA:
- Login, logout, login again
- SQL Injection page
- File Upload page
- Command Injection page
- XSS (Reflected and Stored) pages
- CSRF page
- Brute Force page

Goal: every endpoint appears in HTTP History.

## Step 2 — Review History

Filter: "Show only in-scope items" (scope = `localhost`).  
Look for:
- POST requests with form bodies
- Requests with numeric IDs in URL or params
- Requests with session cookies
- Any `token` or `csrf` parameters

## Step 3 — Auth Testing in Repeater

Send the login POST to Repeater.  
Test: delete Cookie header → send → 200 or 302?  
Test: change username parameter → different user data returned?

## Step 4 — Injection Testing in Repeater

Find the SQL Injection page request in History → send to Repeater.
```
# In the id parameter, test:
id=1
id=1'
id=1' OR '1'='1
id=1 AND SLEEP(5)--
```

## Step 5 — Decode Cookies

Copy session cookie value → Decoder tab → Base64 Decode → what's inside?  
Is the user role or ID embedded in the cookie?

## Step 6 — JWT Attack (Juice Shop)

Switch target to Juice Shop. Log in → find `Authorization: Bearer <token>` in History.  
JWT Editor tab → attempt alg:none attack → change role to admin.

## Step 7 — Param Miner

On a key DVWA endpoint (e.g., the SQL Injection page): right-click → Extensions → Param Miner → Guess params.  
Wait for results — any hidden parameters discovered?

## Findings Table

| Endpoint | Vulnerability | Payload | Result |
|----------|--------------|---------|--------|
| /dvwa/vulnerabilities/sqli/ | SQL Injection | `1' OR '1'='1` | All users returned |
| /login.php | Auth | removed Cookie | Redirected to login (protected) |
| /api/Users/2 | IDOR | changed user ID | Other user's email returned |
