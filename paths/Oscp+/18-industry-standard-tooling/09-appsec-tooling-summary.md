# AppSec Tooling Summary

The standard AppSec engineer toolbox. Deep coverage in Phase 17 — this is the quick-reference map.

## Tool Quick Reference

| Tool | Type | Use Case | Free? |
|------|------|----------|-------|
| Semgrep | SAST | Multi-language code scanning | Yes |
| Bandit | SAST | Python-specific | Yes |
| Brakeman | SAST | Ruby on Rails | Yes |
| ESLint security | SAST | JavaScript/TypeScript | Yes |
| Snyk | SCA | Dependency + container vulns | Free tier |
| Trivy | SCA + Container | All-in-one scanner | Yes |
| OWASP Dep-Check | SCA | Java/.NET focus | Yes |
| OSV Scanner | SCA | Google, multi-ecosystem | Yes |
| Trufflehog | Secrets | Git history + live | Yes |
| GitLeaks | Secrets | Git scanning | Yes |
| detect-secrets | Secrets | Pre-commit hooks | Yes |
| OWASP ZAP | DAST | Web app automated scanning | Yes |
| Burp Suite Pro | DAST/Manual | Manual web testing | Paid |
| Nuclei | DAST | Template-based scanning | Yes |
| Checkmarx | SAST | Enterprise, broad language | Paid |
| Veracode | SAST+DAST | Enterprise SaaS | Paid |
| SonarQube CE | SAST | Code quality + security | Yes (CE) |
| pre-commit | Gates | Pre-commit hook framework | Yes |

## Installation One-Liner

```bash
# Install core free toolset
pip install semgrep bandit detect-secrets trufflehog
brew install trivy gitleaks nuclei
apt install zaproxy

# Go tools
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Node audit (built-in)
npm audit

# Pre-commit framework
pip install pre-commit
```

## CI/CD Security Gate (Minimal)

```yaml
# Minimum viable AppSec pipeline
- SAST:    semgrep --config=auto --error src/
- SCA:     trivy fs --exit-code 1 --severity HIGH,CRITICAL ./
- Secrets: trufflehog git file://. --only-verified --fail
- DAST:    nuclei -u http://staging -severity high,critical -exit-code 1
```

## Tool Decision Guide

```
Writing Python?              → Bandit + Semgrep p/python
Writing JavaScript?          → ESLint security + Semgrep p/javascript
Writing Go?                  → Semgrep p/go + gosec
Scanning containers?         → Trivy image myapp:latest
Checking dependencies?       → Snyk test OR trivy fs
Finding secrets in history?  → Trufflehog git OR gitleaks detect
Running automated web scan?  → Nuclei (fast) OR ZAP (thorough)
Manual web testing?          → Burp Suite Pro
Enterprise SAST?             → Checkmarx or Veracode
Self-hosted code quality?    → SonarQube Community
```

## What Commercial Tools Add Over Free

```
Checkmarx / Veracode:
  + Dataflow analysis (taint tracking) — fewer false positives
  + IDE integration out-of-box
  + Compliance reporting (PCI, SOC2, ISO 27001)
  + Priority support and SLAs

SonarQube Developer Edition (paid):
  + Branch analysis
  + Pull request decoration
  + Security hotspot triage

Snyk (paid tiers):
  + Priority score (reachability analysis)
  + License compliance
  + IaC scanning
  + Unlimited scans
```

## Pre-Commit Config Template

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.1
    hooks:
      - id: gitleaks

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]

  - repo: https://github.com/returntocorp/semgrep
    rev: v1.40.0
    hooks:
      - id: semgrep
        args: ["--config=auto", "--error"]
```
