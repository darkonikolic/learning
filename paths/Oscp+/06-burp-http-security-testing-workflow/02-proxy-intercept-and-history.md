# Proxy Intercept and HTTP History

Intercept pauses traffic so you can inspect and modify requests before they reach the server. HTTP History stores everything that flows through the proxy.

## Intercept ON vs OFF

- **Intercept ON**: every browser action pauses — you see each raw request, can edit, then forward or drop
- **Intercept OFF**: traffic flows freely — use History to review after the fact

Toggle: Proxy → Intercept tab → "Intercept is on/off" button.

## Populate History

1. Set Intercept OFF
2. Browse DVWA — click login, navigate pages, submit forms
3. Open HTTP History tab — all requests appear
4. Filter: "Show only in-scope items" (requires scope set under Target → Scope)

## HTTP History Columns

| Column | Why it matters |
|--------|---------------|
| Method | GET vs POST — POST often has bodies with credentials |
| URL | find interesting endpoints |
| Status | 302 = redirect (login flow), 200 = success, 403 = forbidden |
| Length | large difference between responses = different content = worth comparing |
| MIME | `application/json` = API endpoint |

## Right-Click Actions

- **Send to Repeater** — manual retesting (Ctrl+R)
- **Send to Intruder** — automated fuzzing
- **Send to Comparer** — diff two responses

## Search History

Ctrl+F in HTTP History → search `password`, `token`, `secret`, `key` in responses.  
Use "Filter" bar → type keyword to narrow visible requests.

## Exercise

1. Browse DVWA with Intercept ON
2. Attempt login — intercept the POST request
3. Note: `username=admin&password=password` in body
4. Forward to Repeater (Ctrl+R)
5. Forward the request to complete login
6. Turn Intercept OFF, browse 5 more pages
7. In History, locate the login POST — note the `Set-Cookie` header in the response
8. Search History for the word `password` — how many responses contain it?
