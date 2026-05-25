# Pre-Send Checklist for Every Interesting Request

Run this checklist on every new endpoint before moving on. Print it and use it during tests.

## The Checklist

**Authentication**
- [ ] Remove the `Cookie` / `Authorization` header — does the server return 401/403, or still 200?
- [ ] Replace the session with an expired or invalid token — does it reject?

**Access Control / IDOR**
- [ ] Is there a numeric user ID, object ID, or record ID in the URL or body?
- [ ] Change it to 1, 2, 3, 0, -1, another user's known ID — does it return different data?
- [ ] Is the same object accessible with a lower-privilege account's session?

**CSRF**
- [ ] Is there a `csrf_token`, `_token`, or `state` parameter in the request?
- [ ] Remove it — does the request still succeed?
- [ ] Is the `SameSite` flag set on the session cookie?

**Hidden Parameters**
- [ ] Right-click → Extensions → Param Miner → Guess params
- [ ] Try adding common params: `debug=true`, `admin=1`, `test=1`, `source=1`

**Injection**
- [ ] Is any parameter value reflected in the response? (`<h1>hello</h1>` in output → XSS candidate)
- [ ] Is any parameter used to fetch or filter data? (`id=1'` → SQL error?)
- [ ] Does the parameter appear to build a file path? (`file=../etc/passwd` → path traversal?)

**Content**
- [ ] Switch `Content-Type: application/json` to `application/xml` — different behavior?
- [ ] Add extra JSON fields (`"isAdmin":true`) — do they get stored or reflected?
- [ ] Switch HTTP method: GET → POST → PUT → DELETE

**Headers**
- [ ] Try `X-Forwarded-For: 127.0.0.1` — does it bypass an IP restriction?
- [ ] Try `X-Original-URL: /admin` — does it change routing?

## Quick Reference — Common Test Payloads

```
SQLi probe:    '  OR  1' OR '1'='1  OR  1 AND SLEEP(5)--
XSS probe:     <script>alert(1)</script>  OR  "><img src=x onerror=alert(1)>
Path traversal: ../../../etc/passwd  OR  ..%2F..%2Fetc%2Fpasswd
IDOR:           change id=5 to id=1,2,3,0,-1,9999
CSRF test:      remove token parameter, resend
Auth test:      remove Cookie header, resend
```

Apply every applicable check from this list before marking an endpoint as reviewed.
