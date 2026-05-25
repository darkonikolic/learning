# OAuth 2.0 attack surfaces — state, redirect_uri, and token leakage

OAuth flows route auth codes and tokens through redirects — every redirect is an attack surface.

## OAuth Authorization Code flow — what to intercept

```
1. User clicks "Login with Google"
2. Browser redirects to: https://accounts.google.com/o/oauth2/auth
     ?client_id=APP_ID
     &redirect_uri=https://app.com/callback    ← attacker target
     &response_type=code
     &scope=openid email
     &state=RANDOM_VALUE                        ← CSRF protection
3. User approves → Google redirects to: https://app.com/callback?code=AUTH_CODE&state=VALUE
4. App exchanges code for access token at token endpoint
```

## Attack 1 — Missing state parameter (CSRF on OAuth)

If no `state` parameter in step 2, attacker can initiate OAuth flow and fix the auth code to victim's account.

Test: start OAuth flow in Burp, check if `state` is present. Remove it — if flow completes: vulnerable.

## Attack 2 — Open redirect_uri

```
# Legitimate
redirect_uri=https://app.com/callback

# Attacker tries
redirect_uri=https://app.com/callback/../../../evil.com
redirect_uri=https://evil.com
redirect_uri=https://app.com.evil.com
```

In Burp Repeater, modify `redirect_uri` in the authorization request. If the auth code arrives at your domain: account takeover is possible.

## Attack 3 — Token in Referer header

```
https://app.com/callback?code=SECRET_CODE&state=abc
```

If this page loads external resources (analytics, images), the full URL including `code` appears in the Referer header sent to those external servers.

## Attack 4 — Implicit flow token leakage (legacy)

Implicit flow returns `access_token` in URL fragment: `https://app.com/callback#access_token=TOKEN`.
Fragment stays in browser history and may appear in server logs if `redirect_uri` involves server-side redirect.

## PKCE — what it prevents

PKCE (Proof Key for Code Exchange) adds a `code_challenge` to the auth request.
Without the matching `code_verifier`, a stolen auth code cannot be exchanged for a token.
Required for mobile apps and SPAs.

## Test OAuth in Burp

1. Enable Intercept → click "Login with [provider]"
2. Capture every request in the OAuth flow
3. Send authorization request to Repeater
4. Try: remove `state`, modify `redirect_uri`, change `scope`

## Practice

PortSwigger OAuth labs (6 labs): https://portswigger.net/web-security/oauth
TryHackMe "Authentication Bypass": https://tryhackme.com/room/authenticationbypass
