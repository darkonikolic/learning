# Web Testing Tools

Manual testing with Burp Suite Pro is the core skill. Automate the rest.

## Resources

- Burp Suite Pro extensions: https://portswigger.net/bappstore
- Nuclei templates: https://github.com/projectdiscovery/nuclei-templates
- SecLists wordlists: https://github.com/danielmiessler/SecLists

## Burp Suite Pro — Core Workflow

```
Proxy → Intercept → Forward to Repeater (Ctrl+R) → Modify → Send
Target → Site map → right-click → Scan (active scan)
Intruder → paste request → mark $positions$ → set wordlist → start attack
Collaborator → generate URL → paste in payload → check for DNS/HTTP callbacks
```

```bash
# Key extensions to install (BApp Store)
Autorize          — automated auth bypass testing (BOLA/IDOR)
JWT Editor        — decode, modify, resign JWTs
Param Miner       — discover hidden parameters
HTTP Request Smuggler — CL.TE and TE.CL smuggling detection
ActiveScan++      — extended active scanning checks
Logger++          — advanced request logging
```

## OWASP ZAP (Free Burp Alternative)

```bash
# Install
apt install zaproxy
# or: docker pull ghcr.io/zaproxy/zaproxy:stable

# GUI mode
zaproxy &

# Daemon mode for scripting
zaproxy -daemon -port 8090 -config api.key=mysecretkey

# ZAP CLI
pip install zapcli
zap-cli --api-key mysecretkey spider http://target.local
zap-cli --api-key mysecretkey active-scan http://target.local
zap-cli --api-key mysecretkey report -o report.html -f html
```

## Nikto (Basic Web Server Misconfiguration)

```bash
# Basic scan
nikto -h http://target.local

# HTTPS
nikto -h https://target.local -ssl

# Specific port
nikto -h target.local -p 8443

# Save report
nikto -h http://target.local -o nikto-report.html -Format html

# Through proxy (Burp)
nikto -h http://target.local -useproxy http://127.0.0.1:8080
```

## Nuclei (Template-Based, Low False Positives)

```bash
# Install
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Update templates
nuclei -update-templates

# Full scan
nuclei -u http://target.local

# High/Critical only
nuclei -u http://target.local -severity high,critical

# Specific template categories
nuclei -u http://target.local -t ~/nuclei-templates/http/cves/
nuclei -u http://target.local -t ~/nuclei-templates/http/default-logins/
nuclei -u http://target.local -t ~/nuclei-templates/http/exposures/

# Multiple targets
nuclei -list targets.txt -severity high,critical

# JSON output
nuclei -u http://target.local -json -o nuclei-results.json
```

## ffuf (Directory and Parameter Fuzzing)

```bash
# Directory brute force
ffuf -u http://target.local/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt

# File extension fuzzing
ffuf -u http://target.local/indexFUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/web-extensions.txt

# Parameter fuzzing (GET)
ffuf -u "http://target.local/search?FUZZ=value" \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt

# POST parameter fuzzing
ffuf -u http://target.local/login \
  -X POST -d "username=admin&password=FUZZ" \
  -w /usr/share/seclists/Passwords/Leaked-Databases/rockyou-50.txt \
  -H "Content-Type: application/x-www-form-urlencoded"

# Filter by response code
ffuf -u http://target.local/FUZZ -w wordlist.txt -fc 404

# Virtual host fuzzing
ffuf -u http://target.local -H "Host: FUZZ.target.local" \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -fs 1234
```

## SQLmap (SQL Injection — Labs Only)

```bash
# Basic GET parameter test
sqlmap -u "http://target/page?id=1" --dbs

# POST parameter test
sqlmap -u "http://target/login" --data="user=admin&pass=test" --dbs

# Dump specific database
sqlmap -u "http://target/page?id=1" -D dbname --tables
sqlmap -u "http://target/page?id=1" -D dbname -T users --dump

# Use Burp-captured request
sqlmap -r request.txt --dbs

# Risk/level increase
sqlmap -u "http://target/page?id=1" --level=5 --risk=3 --dbs
```

## wfuzz (Parameter Fuzzing Alternative)

```bash
# Directory fuzzing
wfuzz -c -z file,/usr/share/seclists/Discovery/Web-Content/common.txt \
  --hc 404 http://target.local/FUZZ

# Brute force login
wfuzz -c -z file,usernames.txt -z file,passwords.txt \
  --hc 302 -d "user=FUZZ&pass=FUZ2Z" http://target.local/login
```

## Ethical Note

SQLmap runs actual injection payloads — only use in authorized labs or engagements. Intruder brute force and active scanning should only target systems in scope.
