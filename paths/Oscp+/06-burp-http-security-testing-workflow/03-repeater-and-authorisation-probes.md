# Repeater and Authorization Testing

Repeater lets you resend a captured request as many times as you want with manual modifications. It's the primary tool for testing access control.

## Send a Request to Repeater

From HTTP History: right-click → Send to Repeater, or press Ctrl+R.  
Switch to Repeater tab — request appears on the left, response on the right.  
Click "Send" to fire it. Modify and send again.

## What to Modify

```
# Original request
GET /api/user/profile?id=5 HTTP/1.1
Host: localhost
Cookie: session=abc123xyz

# Test 1 — IDOR: change the ID
GET /api/user/profile?id=1 HTTP/1.1

# Test 2 — IDOR: try other IDs
GET /api/user/profile?id=2 HTTP/1.1
GET /api/user/profile?id=0 HTTP/1.1
GET /api/user/profile?id=-1 HTTP/1.1
GET /api/user/profile?id=admin HTTP/1.1

# Test 3 — remove auth entirely
GET /api/user/profile?id=5 HTTP/1.1
Host: localhost
# (no Cookie header)

# Test 4 — replace cookie with another user's session
Cookie: session=differentusercookiehere
```

## Headers to Test

| Header | Test |
|--------|------|
| `Cookie` | remove it, replace it, use another user's session |
| `Authorization` | remove it, use expired token, modify JWT payload |
| `X-User-ID` | change to other user IDs |
| `X-Forwarded-For: 127.0.0.1` | bypass IP-based restrictions |
| `X-Original-URL: /admin` | override routing in some frameworks |

## Reading the Response

- Same content for different IDs → IDOR confirmed
- 200 with no cookie → authentication not enforced
- 403 → access control exists (but may still be bypassable)
- Different content length for different users → data leakage

## Exercise

1. Log into DVWA as `admin`
2. Browse to a user-specific page — intercept or find in History
3. Send to Repeater
4. Delete the `Cookie` header entirely → Send → what response code?
5. Change a numeric parameter to another user's ID → Send → does it return different user's data?
6. Log in as a second DVWA user (create one first), capture their session cookie
7. In Repeater, swap the cookie to the second user's — does admin content still appear?
