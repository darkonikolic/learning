# Burp Suite core workflow — intercept, modify, replay

Burp is the primary tool for web security testing. Learn these four workflows.

## Setup check

```
Burp running → Proxy listener on 127.0.0.1:8080
Browser proxy set to 127.0.0.1:8080
CA cert installed in browser
Intercept: ON
```

## Workflow 1 — Intercept and modify a request

1. Browse to DVWA login page: http://localhost/login.php
2. Burp Proxy → Intercept ON
3. Submit login form in browser
4. Request appears in Burp — see the POST body: `username=admin&password=password`
5. Modify the password field → click Forward
6. Intercept OFF to stop capturing every request

## Workflow 2 — Repeater (replay and modify)

1. Burp Proxy → HTTP history → find the login POST
2. Right-click → Send to Repeater
3. Repeater tab → change `password=password` to `password=wrongpass` → click Send
4. Response panel shows server response — compare 200 vs 302 vs 401

## Workflow 3 — Decoder

1. Burp Decoder tab
2. Paste a base64 value from a cookie or JWT header
3. Click Decode as → Base64 → see plaintext
4. URL-encode a payload: paste `<script>alert(1)</script>` → Encode as → URL

## Workflow 4 — Comparer

1. Send two responses to Comparer (right-click → Send to Comparer)
2. Click Words or Bytes — highlights differences
3. Useful for: comparing response with valid vs invalid session, or admin vs user response

## Key Burp tabs

| Tab | Purpose |
|---|---|
| Proxy → Intercept | Pause and modify in-flight requests |
| Proxy → HTTP history | Full log of all requests made through proxy |
| Repeater | Manually replay and tweak individual requests |
| Decoder | Encode/decode base64, URL, HTML, hex |
| Comparer | Diff two requests or responses |
| Intruder | Automated fuzzing (rate-limited in Community edition) |

## Practice

PortSwigger "Burp Suite for Beginners": https://portswigger.net/burp/documentation/desktop/getting-started
