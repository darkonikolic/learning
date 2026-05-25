# HTTP from attacker perspective — requests, cookies, and DevTools

Understanding HTTP structure is prerequisite for every web attack.

## URL anatomy

```
https://shop.example.com:443/products?id=5&sort=asc#reviews
^^^^^   ^^^^^^^^^^^^^^^^ ^^^  ^^^^^^^^ ^^^^^^^^^^^^ ^^^^^^^
scheme  host             port path     query params  fragment
```

Query parameters (`id=5`) are attacker input. Every parameter is a potential injection point.

## HTTP verbs and what attackers target

| Verb | Purpose | Attack angle |
|---|---|---|
| GET | Fetch resource | Inject via URL params |
| POST | Submit data | Inject via request body |
| PUT | Replace resource | Unauthorized data modification |
| DELETE | Remove resource | Unauthorized deletion |
| PATCH | Partial update | Privilege escalation via field |

## Cookies and sessions

```bash
# curl — save cookies then resend them
curl -c cookies.txt http://target/login -d "user=admin&pass=password"
curl -b cookies.txt http://target/dashboard

# Check what flags a cookie has
curl -v http://target/login 2>&1 | grep Set-Cookie
# Good: Set-Cookie: session=abc; HttpOnly; Secure; SameSite=Strict
# Bad:  Set-Cookie: session=abc
```

Missing `HttpOnly` → XSS can steal it. Missing `Secure` → sent over HTTP. Missing `SameSite` → CSRF risk.

## Same-origin policy

Browser blocks JS on `evil.com` from reading responses from `bank.com`. This is the main browser defense.
CORS headers (`Access-Control-Allow-Origin: *`) can weaken it — look for overly permissive CORS configs.

## DevTools workflow

1. Open F12 → Network tab
2. Browse to any login page
3. Submit the form — watch the POST request appear
4. Click the request → Headers tab (see what was sent) → Response tab (see what came back)
5. Right-click the request → Copy → Copy as cURL
6. Paste in terminal → replay the request → modify parameters

## Practice

TryHackMe "How The Web Works" path (4 rooms, all free):
https://tryhackme.com/module/how-the-web-works
