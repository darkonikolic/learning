# Resources and lab setup — web and auth security

PortSwigger Web Security Academy is the primary platform. Everything is free.

## Primary resources

- PortSwigger Web Security Academy: https://portswigger.net/web-security
  Complete all Apprentice labs as minimum. Practitioner labs for depth.
- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/

## Local lab — vulnerable apps via Docker

```bash
# DVWA — classic vulnerable PHP app
docker run -d -p 80:80 vulnerables/web-dvwa
# Browse to http://localhost → login: admin/password → Setup/Reset DB button

# OWASP Juice Shop — covers all OWASP Top 10 with gamified challenges
docker run -d -p 3000:3000 bkimminich/juice-shop
# Browse to http://localhost:3000

# WebGoat — Java-based, structured lessons
docker run -d -p 8080:8080 webgoat/webgoat
# Browse to http://localhost:8080/WebGoat

# OWASP crAPI — modern API vulnerable app
docker run -d -p 8888:8888 crapi/crapi
```

## Burp Suite Community — install and configure

1. Download: https://portswigger.net/burp/communitydownload
2. Open Burp → Proxy → Options → Proxy listener on 127.0.0.1:8080
3. In browser: set manual proxy to 127.0.0.1:8080 (or use FoxyProxy extension)
4. Import Burp CA cert: browse to http://burpsuite → Download CA certificate → install in browser
5. Verify: browse to any site → Burp Proxy → HTTP history shows the request

## Recommended lab order

1. PortSwigger Apprentice labs for each topic (do them alongside each unit)
2. DVWA — set security to Low, work through all modules
3. Juice Shop — solve challenges while learning each attack type
4. Repeat DVWA on Medium and High after completing the whole phase
