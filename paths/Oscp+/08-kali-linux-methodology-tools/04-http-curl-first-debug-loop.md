# curl for Web Reconnaissance and API Testing

Use curl before opening Burp — faster for quick checks, easier to script.

## Basic Reconnaissance

Headers only (fast server fingerprint):

```bash
curl -I http://target
```

Verbose output — see full request/response including TLS handshake:

```bash
curl -sv http://target 2>&1 | less
```

Quick wins — always check these:

```bash
curl http://target/robots.txt
curl http://target/sitemap.xml
curl http://target/.htaccess
curl http://target/crossdomain.xml
```

## POST Requests

Form data:

```bash
curl -X POST -d "user=admin&pass=test" http://target/login
```

JSON body:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test"}' \
  http://target/api/login
```

## Authentication

Bearer token:

```bash
curl -H "Authorization: Bearer TOKEN" http://target/api/profile
```

Basic auth:

```bash
curl -u admin:password http://target/admin/
```

Cookie handling (save and reuse):

```bash
curl -c cookies.txt -b cookies.txt -X POST -d "user=admin&pass=admin" http://target/login
curl -b cookies.txt http://target/dashboard
```

## Useful Flags

| Flag | Purpose |
|------|---------|
| `-L` | Follow redirects |
| `-k` | Ignore TLS certificate errors |
| `-I` | HEAD request (headers only) |
| `-sv` | Verbose with TLS info |
| `-o file` | Save output to file |
| `-w "%{http_code}"` | Print response code only |

## Check Response Code

```bash
curl -o /dev/null -s -w "%{http_code}\n" http://target/admin/
```

## Practice

Run all basic recon commands against DVWA at `http://localhost:80` before using Burp. Spot what information the headers leak.
