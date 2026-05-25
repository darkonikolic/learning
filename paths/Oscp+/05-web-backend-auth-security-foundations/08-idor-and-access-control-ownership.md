# IDOR and access control testing — find and exploit object reference flaws

IDOR: change an ID in a request to access another user's data. The server must enforce ownership — the client cannot be trusted.

## IDOR test methodology

Find any ID in a URL, request body, or response:
```
GET /api/orders/1001          → change to /api/orders/1002
GET /profile?user_id=501      → change to /profile?user_id=502
POST /download {"file_id":33} → change to {"file_id":34}
```

Observe the response:
- Different user's data returned = horizontal IDOR (same role, different user)
- Admin data or elevated function returned = vertical IDOR (role escalation)
- 403 or 404 = access control is working

## Two-user test (most reliable method)

1. Create Account A and Account B (or use two browser sessions)
2. Log in as Account A → perform an action → capture the request in Burp
3. Copy that request → log in as Account B → replay the request in Burp Repeater
4. If Account B's session can access Account A's data: IDOR confirmed

```bash
# Example with curl — user A's token accessing user B's order
curl http://localhost:3000/api/orders/1002 \
  -H "Authorization: Bearer USER_A_TOKEN"

# If you get user B's order data: horizontal IDOR
```

## Vertical access control — accessing admin functions

```bash
# Test if regular user can reach admin endpoints
curl http://localhost/admin/users -b "session=regular_user_cookie"
curl http://localhost/api/admin/deleteUser/5 -b "session=regular_user_cookie"

# Test parameter-based role escalation
curl http://localhost/api/updateProfile \
  -d '{"username":"victim","role":"admin"}' \
  -H "Content-Type: application/json" \
  -b "session=regular_user_cookie"
```

## Burp Autorize extension — automate auth testing

1. Install Autorize from BApp Store
2. Log in as low-privilege user → add their cookie to Autorize config
3. Browse the app as admin
4. Autorize auto-replays every request with the low-privilege cookie
5. Green = protected, Red = access control bypass detected

## Common IDOR locations

- `/api/users/{id}` — user profile data
- `/api/orders/{id}` — order details
- `/api/invoices/{id}` — invoice download
- `/api/messages/{id}` — private messages
- `?file=../../../etc/passwd` — path traversal variant

## Practice

PortSwigger Access Control labs (13 labs): https://portswigger.net/web-security/access-control
TryHackMe "IDOR" room: https://tryhackme.com/room/idor
Juice Shop: solve "View another user's basket" challenge
