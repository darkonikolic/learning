# DAST Tools

Dynamic Application Security Testing — scan a running application. Use against staging, never production.

## Resources

- ZAP docs: https://www.zaproxy.org/docs/
- Nuclei templates: https://github.com/projectdiscovery/nuclei-templates
- Nikto: https://github.com/sullo/nikto

## OWASP ZAP

```bash
# Install via package or Docker
docker pull ghcr.io/zaproxy/zaproxy:stable

# Daemon mode (headless)
docker run -u zap -p 8090:8090 ghcr.io/zaproxy/zaproxy:stable \
  zap.sh -daemon -port 8090 -config api.key=mysecretkey

# ZAP CLI (wrapper for scripting)
pip install zapcli
export ZAP_API_KEY=mysecretkey

# Spider the target
zap-cli --api-key mysecretkey spider http://target.local

# Run active scan
zap-cli --api-key mysecretkey active-scan http://target.local

# Export report
zap-cli --api-key mysecretkey report -o zap-report.html -f html

# Full automation — baseline scan (passive only, fast)
docker run --rm ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t http://target.local -r report.html

# Full scan (active — slower, more findings)
docker run --rm ghcr.io/zaproxy/zaproxy:stable \
  zap-full-scan.py -t http://target.local -r report.html
```

## Nuclei (Template-Based, Fast, Low False Positives)

```bash
# Install
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
# or: brew install nuclei

# Update templates
nuclei -update-templates

# Scan single target
nuclei -u http://target.local

# High/Critical only
nuclei -u http://target.local -severity high,critical

# Use specific template category
nuclei -u http://target.local -t ~/nuclei-templates/http/cves/
nuclei -u http://target.local -t ~/nuclei-templates/http/exposures/
nuclei -u http://target.local -t ~/nuclei-templates/http/misconfigurations/

# Scan from file of URLs
nuclei -list urls.txt -t ~/nuclei-templates/ -severity high,critical

# JSON output
nuclei -u http://target.local -json -o results.json

# API-specific templates
nuclei -u http://target.local -t ~/nuclei-templates/http/default-logins/
```

## Nikto (Basic Web Server Scan)

```bash
# Install
apt install nikto

# Basic scan
nikto -h http://target.local

# HTTPS target
nikto -h https://target.local -ssl

# Save output
nikto -h http://target.local -o nikto-report.html -Format html

# Specific port
nikto -h target.local -p 8443
```

## CI/CD Integration (GitHub Actions)

```yaml
- name: Nuclei DAST scan
  run: |
    nuclei -u http://staging.internal \
      -severity high,critical \
      -exit-code 1 \
      -json -o nuclei-results.json

- name: ZAP baseline scan
  run: |
    docker run --rm ghcr.io/zaproxy/zaproxy:stable \
      zap-baseline.py -t http://staging.internal -r zap-report.html
```

## Scope and Ethics

- DAST sends real attack payloads — only run against systems you own or have written authorization to test
- Always use a dedicated staging environment, never production
- Active scans can cause application errors, data corruption, or crashes on fragile apps
- ZAP active scan can be noisy — warn the team before running in shared staging
