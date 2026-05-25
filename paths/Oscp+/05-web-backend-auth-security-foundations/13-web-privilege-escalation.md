# Web privilege escalation — horizontal and vertical

Role and permission escalation at the application layer. Distinct from OS PrivEsc — no exploit needed, just logic flaws.

## Two types

**Horizontal**: access another user's data at the same privilege level (user A reads user B's orders).
**Vertical**: access functionality above your role (regular user reaches admin panel).

## IDOR / BOLA — horizontal escalation

```http
GET /api/users/1042/profile     ← your ID
→ change to:
GET /api/users/1043/profile     ← another user's data
```

Test on every object reference: numeric IDs, UUIDs, usernames in paths/params/body. Automate with Burp Intruder or ffuf.

```bash
ffuf -u "http://target/api/orders/FUZZ" -w ids.txt -H "Cookie: session=yours" -fc 403,404
```

Reference: PortSwigger Access Control labs — https://portswigger.net/web-security/access-control

## Parameter tampering — vertical escalation

```http
POST /api/user/update
{"role": "admin", "email": "attacker@evil.com"}
```

Test: add `role`, `admin`, `is_admin`, `user_type` to any profile/registration/update request. Also test in URL params and cookies.

Mass assignment (frameworks that bind all request fields):

```json
{"name": "test", "email": "x@x.com", "role": "superadmin"}
```

Practice: OWASP crAPI — mass assignment on `/community/api/v2/user/dashboard`

## JWT role manipulation

```bash
# Decode header.payload.signature — payload:
{"sub": "user123", "role": "user", "exp": 1234567890}

# Attacks:
# 1. None algorithm: set alg=none, remove signature, change role to admin
# 2. Weak secret: crack with hashcat -m 16500 token.txt rockyou.txt
# 3. Key confusion: RS256 → HS256, sign with public key
```

Burp JWT Editor extension handles all three attack types. PortSwigger JWT labs cover each attack step-by-step.

## Cookie and session manipulation

```
role=user → role=admin
admin=0 → admin=1
user_level=1 → user_level=99
```

Check every cookie field. Decode base64 values. Tamper and observe response differences (403 vs 200 vs redirect).

## Forced browsing — bypassing UI controls

Admin panel hidden from UI but accessible directly:

```bash
gobuster dir -u http://target -w /usr/share/wordlists/dirb/common.txt
# Common admin paths: /admin, /administrator, /manage, /dashboard, /console, /internal
```

Try direct access without admin role — server may only check at UI level not at route level.

## HTTP method override — access control bypass

Some apps check role on GET but not on PUT/DELETE:

```http
GET /api/user/1042   → 200 (own record)
DELETE /api/user/1043 → may succeed if only GET is guarded
```

Test all HTTP methods on every endpoint: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS.

## Privilege escalation via account takeover chain

1. Find password reset token leak or IDOR on reset endpoint
2. Reset admin account password
3. Login as admin

Or: find admin email via user enumeration → trigger reset → intercept token if weakly generated.

## Practice

- PortSwigger: Access Control labs (full series, free)
- OWASP crAPI: local Docker lab — covers BOLA, mass assignment, broken function level auth
- DVWA: CSRF + IDOR combination drills
- TryHackMe: "IDOR" room, "Walking an Application" room
