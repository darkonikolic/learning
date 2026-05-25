# Authentication and Session Testing

Testing login flows, session tokens, password resets, and MFA with Burp.

## Cookie Flags

Intercept the login response — look at `Set-Cookie` header:

```http
HTTP/1.1 200 OK
Set-Cookie: session=abc123; HttpOnly; Secure; SameSite=Lax
```

| Flag | Missing = problem |
|------|-------------------|
| `HttpOnly` | JavaScript can read the cookie — XSS can steal it |
| `Secure` | Cookie sent over HTTP — sniffable |
| `SameSite` | CSRF possible without this |

## Session Fixation

1. Note your session ID before logging in (check cookie in Burp History)
2. Log in — intercept the response
3. Check: did `Set-Cookie` issue a **new** session ID?
4. If the ID is the same before and after login → session fixation vulnerability

## Password Reset Flow

Intercept the full reset flow in Burp:
1. Request reset → find the reset token (in URL parameter or response body)
2. Is the token short or numeric? → likely guessable
3. Request two resets quickly → are tokens sequential or similar?
4. Check if the token expires — try reusing it after 10 minutes

## Brute Force and Lockout Testing

```bash
# Test 5 wrong logins manually — does the account lock?
# Test 10 — any CAPTCHA appear?
# Test from two different IPs — is lockout per-IP or per-account?

# Check response for rate limiting headers
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

## MFA Bypass Attempts

Intercept the MFA step (after correct username/password):
```http
POST /verify-mfa HTTP/1.1

code=123456
```
Tests:
- Remove the `code` parameter entirely → does it pass?
- Change `code=000000` → does it accept any value?
- Skip the MFA endpoint entirely — go directly to the post-login page URL

## Exercise

Complete PortSwigger "Authentication" labs — Apprentice tier (all 6 labs):  
https://portswigger.net/web-security/authentication  

For each lab: capture the relevant request in Burp, test the bypass in Repeater, document what parameter or header was the vulnerability.
