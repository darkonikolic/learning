# Burp Suite: Setup and Practice Environment

Install Burp Community and configure a working lab before touching any other file in this phase.

## Install Burp Suite Community

Download: https://portswigger.net/burp/communitydownload  
On Kali: already included — run `burpsuite` from terminal.

## Browser Proxy Config

Set Firefox proxy to `127.0.0.1:8080` (manual proxy, all protocols).  
Or use Burp's built-in browser: Proxy → Open Browser.

Install Burp CA cert:
1. Browse to `http://burpsuite` while proxy is active
2. Download `cacert.der`
3. Firefox → Settings → Certificates → Import → select the file

## Lab Targets

```bash
# DVWA
docker run -d -p 80:80 vulnerables/web-dvwa
# Login: admin / password — set Security Level to Low in DVWA settings

# Juice Shop
docker run -d -p 3000:3000 bkimminich/juice-shop
# Browse to http://localhost:3000
```

## Required Extensions (BApp Store)

Open Burp → Extender → BApp Store → install:
- **Autorize** — automated auth testing across user roles
- **JWT Editor** — decode, modify, and attack JWT tokens
- **Param Miner** — discover hidden/undocumented parameters
- **Active Scan++** — enhances active scanner with extra checks

## PortSwigger Web Security Academy

Free course platform: https://portswigger.net/web-security  
Start with: Web Security Academy → Learning Path → "Web Application Security Testing"  
Labs run in the browser — no local setup needed for many exercises.

## Scope Setup (do this first on every test)

Target → Scope → Add host (e.g., `http://localhost`).  
HTTP History → filter → "Show only in-scope items".  
This prevents browser telemetry from polluting your history.

## Exercise

1. Start DVWA and Juice Shop containers
2. Set Firefox proxy to 127.0.0.1:8080
3. Install CA cert — verify HTTPS sites load without certificate warnings
4. Browse DVWA — confirm traffic appears in Burp HTTP History
5. Install all four extensions from BApp Store
6. Set scope to `localhost` only
