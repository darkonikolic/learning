# JWT Analysis and Attack

JWTs appear in Authorization headers (`Bearer eyJ...`) and cookies. Practice on Juice Shop which uses JWTs throughout.

## Spot JWTs

In Burp HTTP History: search for `Bearer` or `eyJ`. In browser DevTools: Application tab → Cookies or LocalStorage.

## Decode Without Tools

```bash
# Decode header (part 1)
echo "eyJhbGciOiJIUzI1NiJ9" | base64 -d 2>/dev/null

# Decode payload (part 2)
echo "eyJzdWIiOiJ1c2VyIiwicm9sZSI6InVzZXIifQ" | base64 -d 2>/dev/null

# One-liner for full JWT payload
echo "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.xxx" | cut -d. -f2 | base64 -d 2>/dev/null
```

Online decoder: jwt.io — paste token, see header/payload decoded.

## None Algorithm Attack (in Burp)

1. Install JWT Editor extension in Burp
2. Intercept a request with a JWT
3. Go to JSON Web Token tab
4. Click "Attack" → "None Signing Algorithm"
5. Modify payload (e.g. change `"role":"user"` to `"role":"admin"`)
6. Forward the modified request

## Weak Secret — Hashcat

```bash
# Crack JWT with rockyou
hashcat -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt

# jwt.txt contains the full token: header.payload.signature
```

## Key Confusion Attack (RS256 → HS256)

If server uses RS256, try switching to HS256 and signing with the public key. JWT Editor in Burp handles this — "Embedded JWK" attack.

## Find JWTs in Traffic

Burp History → Filter → search `Bearer` in request headers. Export interesting JWTs to a file for cracking.

## Practice

Juice Shop exercise:
1. Login, capture the JWT from the Authorization header
2. Decode payload — note the `email` field
3. Attempt to crack signature with `hashcat -m 16500`
4. Try changing the `role` claim and re-submitting (none algorithm attack)
