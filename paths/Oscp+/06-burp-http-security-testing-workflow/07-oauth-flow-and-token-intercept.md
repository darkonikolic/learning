# OAuth Flow Interception

Intercepting and testing OAuth 2.0 authorization flows with Burp.

## What to Look For in HTTP History

Browse an app that uses "Login with Google/GitHub/etc." with Burp proxy active.  
In History, filter by URL — look for these requests in order:

```
1. GET /oauth/authorize?client_id=xxx&redirect_uri=https://app.com/callback&state=yyy
2. GET https://app.com/callback?code=AUTH_CODE&state=yyy
3. POST /oauth/token  (code exchanged for access token — may be server-side, invisible)
```

## state Parameter — CSRF Test

```http
# Original
GET /oauth/authorize?client_id=xxx&redirect_uri=https://app.com/callback&state=random123

# Test: remove state parameter entirely
GET /oauth/authorize?client_id=xxx&redirect_uri=https://app.com/callback
```
If the flow completes without `state` → CSRF on OAuth login is possible.

## redirect_uri Manipulation

```http
# Original
GET /oauth/authorize?client_id=xxx&redirect_uri=https://app.com/callback

# Test: change to attacker-controlled domain
GET /oauth/authorize?client_id=xxx&redirect_uri=https://attacker.com/steal

# Test: add path traversal
GET /oauth/authorize?client_id=xxx&redirect_uri=https://app.com/callback/../evil

# Test: add open redirect
GET /oauth/authorize?client_id=xxx&redirect_uri=https://app.com/redirect?url=https://evil.com
```
If the server redirects to your modified URI → the auth code is leaked.

## PKCE Fields

In the request, look for:
- `code_challenge` — hash of the verifier
- `code_verifier` — sent during token exchange

If PKCE is absent on a public client → auth code interception is possible.

## Token Scope Check

After token exchange, the access token may be a JWT.  
Decode it in Decoder (base64) or JWT Editor:
```json
{"sub":"user123","scope":"read","role":"user","exp":1700000000}
```
- Is scope minimal or does it include write/admin?
- Try using the token on endpoints outside the declared scope

## Exercise

Complete all 4 Apprentice OAuth labs on PortSwigger:  
https://portswigger.net/web-security/oauth  

In Burp during each lab: annotate each request in History (right-click → Add comment) to label its role in the flow — AS-REQ, token exchange, callback, etc.
