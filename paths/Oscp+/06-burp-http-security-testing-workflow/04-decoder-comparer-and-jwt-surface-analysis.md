# Decoder, Comparer, and JWT Analysis

Three tools for analyzing what's inside tokens and comparing responses.

## Decoder

Open: Burp → Decoder tab.  
Paste any encoded string → select encoding type → click Decode.

Common encodings:
```
Base64:    dXNlcjppZDoxMjM=  →  user:id:123
URL:       user%40email.com  →  user@email.com
HTML:      &lt;script&gt;    →  <script>
Hex:       48656c6c6f       →  Hello
```

Session cookies are often base64-encoded JSON:
```bash
# Paste cookie value into Decoder → Base64 Decode
# Example result:
{"user":"admin","role":"user","exp":1700000000}
```

Chain decoding: URL Decode → then Base64 Decode if the value is double-encoded.

## Comparer

Use case: compare two responses to find differences based on auth level.

1. In Repeater: send request as admin → right-click response → Send to Comparer
2. Change cookie to low-privilege user → Send → Send to Comparer
3. Comparer tab → select both entries → Compare (Words or Bytes)
4. Highlighted differences show what the admin sees that the regular user does not

## JWT Editor Extension

Intercept a request containing a JWT in the `Authorization: Bearer <token>` header.  
Switch to the JWT Editor tab in that request.

```
# JWT structure (3 parts, base64-separated by dots):
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9   <- header
.eyJ1c2VyIjoidXNlciIsInJvbGUiOiJ1c2VyIn0  <- payload
.SomeSignatureHere                          <- signature
```

**Alg:none attack:**
1. In JWT Editor → Header → change `"alg":"HS256"` to `"alg":"none"`
2. Payload → change `"role":"user"` to `"role":"admin"`
3. Remove signature (delete everything after the second dot)
4. Send — if server accepts it, JWT verification is broken

## Exercise

1. Log into Juice Shop — find a JWT in the `Authorization` header (check Burp History)
2. Copy the JWT value into Decoder → Base64 Decode each part
3. Identify all claims in the payload (user ID, role, expiry)
4. Install JWT Editor if not done — open the request in Repeater → JWT Editor tab
5. Attempt alg:none attack — change role to admin — does the server accept it?
6. Use Comparer: send one response as admin and one as a regular user — what fields differ?
