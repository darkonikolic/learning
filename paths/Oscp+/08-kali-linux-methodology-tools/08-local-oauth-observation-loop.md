# OAuth Flow Observation and Testing

Intercept and test OAuth flows with Burp Proxy. Practice on PortSwigger OAuth labs.

## Intercept OAuth in Burp

1. Open Burp, set browser proxy to 127.0.0.1:8080
2. Browse to the target app and click "Login with Google/GitHub/etc."
3. Watch HTTP History — the OAuth flow appears as a sequence of requests

## What to Look For

Authorization request — watch for these parameters:

```
GET /oauth/authorize?client_id=APP&redirect_uri=https://target.com/callback&state=RANDOM&response_type=code
```

Key checks:
- Is `state` parameter present? Is it validated?
- What is the `redirect_uri`? Can it be changed?

## Test State Parameter (CSRF)

```bash
# Copy the full /authorize URL
# Remove the state parameter
# Does auth still complete? If yes: CSRF vulnerability
```

## Test redirect_uri Manipulation

In Burp, intercept the authorization request and modify `redirect_uri`:

```
redirect_uri=https://target.com/callback
→ try: redirect_uri=https://evil.com
→ try: redirect_uri=https://target.com.evil.com
→ try: redirect_uri=https://target.com/callback/../admin
```

If the server redirects with the auth code to your modified URI: account takeover via token theft.

## Authorization Code — Grab It

After the callback redirect, the URL contains:

```
https://target.com/callback?code=AUTHCODE&state=VALUE
```

Capture this code in Burp. Try replaying it — is single-use enforced?

## Token Endpoint

Find the POST to `/oauth/token`. Body typically:

```
grant_type=authorization_code&code=AUTHCODE&redirect_uri=...&client_id=...&client_secret=...
```

Check: is `client_secret` exposed client-side?

## Practice

PortSwigger OAuth labs:
- Apprentice lab 1: Authentication bypass via OAuth implicit flow
- Apprentice lab 2: Forced OAuth profile linking
- Practitioner lab 1: OAuth account hijacking via redirect_uri
- Practitioner lab 2: Stealing OAuth access tokens via an open redirect
