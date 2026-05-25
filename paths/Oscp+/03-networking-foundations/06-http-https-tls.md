# HTTP, HTTPS, and TLS

HTTP is the protocol of web exploitation. Understand requests, responses, headers, and TLS — you will manipulate all of these.

## HTTP with curl

```bash
curl https://example.com                          # GET request, print body
curl -I https://example.com                       # HEAD only — see response headers
curl -s -o /dev/null -w "%{http_code}" https://example.com  # just the status code
curl -v https://example.com 2>&1 | head -50       # verbose: see TLS + all headers
curl -L https://example.com                       # follow redirects
curl -b "session=abc; user=admin" http://target/  # send cookies
curl -H "X-Forwarded-For: 127.0.0.1" http://target/  # custom header
curl -X POST -H "Content-Type: application/json" \
     -d '{"user":"admin","pass":"password123"}' \
     http://target/api/login
```

## HTTP status codes

| Code | Meaning | Security relevance |
|------|---------|-------------------|
| 200 | OK | Request succeeded |
| 301/302 | Redirect | Note the Location header |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Auth ok but access denied — enumerate further |
| 404 | Not Found | Path doesn't exist |
| 500 | Server Error | May indicate code path reached — useful signal |

## Important HTTP headers

```bash
# See response headers:
curl -I https://example.com

# Headers to look for:
# Server: Apache/2.4.49        ← version disclosure
# X-Powered-By: PHP/7.4.3     ← stack disclosure
# Set-Cookie: session=abc; HttpOnly; Secure
# Content-Security-Policy: ...
# X-Frame-Options: DENY
```

## TLS inspection with openssl

```bash
openssl s_client -connect example.com:443          # raw TLS connection, shows cert chain
openssl s_client -connect example.com:443 </dev/null 2>/dev/null | \
  openssl x509 -noout -text | grep -A2 "Subject:\|Issuer:\|Not After"

# Check cipher suites
openssl s_client -connect example.com:443 -cipher 'NULL'  # test for null ciphers
nmap --script ssl-enum-ciphers -p 443 example.com          # enumerate supported ciphers
```

## Wireshark — capture HTTP (not HTTPS)

```bash
# HTTP is plaintext — capture it
sudo tcpdump -i lo -w /tmp/http.pcap &
# Start a local HTTP server
python3 -m http.server 8080 &
curl http://localhost:8080/
kill %1 %2

# In Wireshark: filter http
# Right-click a request → Follow → HTTP Stream — see full request+response
```

## Practice

- TryHackMe "HTTP in Detail": https://tryhackme.com/room/httpindetail
- TryHackMe "Burp Suite Basics": https://tryhackme.com/room/burpsuitebasics
- curl manual: https://curl.se/docs/manpage.html

## Completion bar

Make a GET, POST, and HEAD request with curl. Read TLS certificate details with openssl. Capture HTTP traffic with tcpdump and follow a stream in Wireshark. Identify five HTTP response headers and explain what each discloses.
