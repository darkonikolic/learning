# SCA — Dependency Scanning

Software Composition Analysis finds known CVEs in your third-party dependencies. Most breaches hit dependencies, not custom code.

## Resources

- Snyk: https://snyk.io/ (free tier available)
- OSV Scanner (Google, free): https://github.com/google/osv-scanner
- OWASP Dependency-Check: https://owasp.org/www-project-dependency-check/
- Trivy: https://github.com/aquasecurity/trivy

## Snyk

```bash
# Install
npm install -g snyk
# or: brew install snyk

# Authenticate
snyk auth

# Scan Node.js project
snyk test

# Scan Python project
snyk test --file=requirements.txt

# Scan Go project
snyk test --file=go.mod

# Scan Java/Maven
snyk test --file=pom.xml

# High severity only
snyk test --severity-threshold=high

# Monitor ongoing (sends to Snyk dashboard)
snyk monitor

# Container image scan
snyk container test nginx:latest

# Fix suggestions
snyk wizard
```

## Trivy (All-In-One — Container + Code + IaC)

```bash
# Install
brew install aquasecurity/trivy/trivy
# or: apt install trivy

# Container image scan
trivy image nginx:latest
trivy image myapp:latest --severity HIGH,CRITICAL

# Fail CI on critical findings
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Filesystem scan (dependencies in project)
trivy fs ./

# Git repo scan (includes secrets)
trivy repo https://github.com/org/repo

# JSON output
trivy image --format json myapp:latest -o trivy-results.json

# IaC scan (Terraform, Kubernetes manifests)
trivy config ./infra/
```

## OWASP Dependency-Check

```bash
# Download
wget https://github.com/jeremylong/DependencyCheck/releases/latest/download/dependency-check-*.zip
unzip dependency-check-*.zip

# Scan project
./dependency-check/bin/dependency-check.sh \
  --project "MyApp" \
  --scan ./ \
  --format HTML \
  --out ./dc-report/

# Update NVD data (do this regularly)
./dependency-check/bin/dependency-check.sh --updateonly
```

## OSV Scanner (Google — Free, Fast)

```bash
# Install
go install github.com/google/osv-scanner/cmd/osv-scanner@v1

# Scan current directory
osv-scanner scan --recursive ./

# Scan lock files
osv-scanner scan --lockfile=package-lock.json
osv-scanner scan --lockfile=requirements.txt
osv-scanner scan --lockfile=go.sum
```

## GitHub Dependabot (Automatic PRs)

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Remediation Priority

```
1. CRITICAL CVEs with known public exploits (CVSS 9+, exploitDB entry)
2. HIGH CVEs in internet-facing components
3. HIGH CVEs in auth/crypto libraries
4. MEDIUM CVEs in actively maintained packages
5. LOW CVEs — schedule for next release
```

## CI/CD Integration

```yaml
- name: Trivy dependency scan
  run: trivy fs --exit-code 1 --severity HIGH,CRITICAL ./

- name: Snyk check
  run: snyk test --severity-threshold=high
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```
