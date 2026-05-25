# Secrets Scanning

Finding leaked credentials in code and git history. Pre-commit prevention beats post-commit detection.

## Resources

- Trufflehog: https://github.com/trufflesecurity/trufflehog
- GitLeaks: https://github.com/gitleaks/gitleaks
- detect-secrets: https://github.com/Yelp/detect-secrets
- pre-commit framework: https://pre-commit.com/

## Trufflehog (Deep Git History Scan)

```bash
# Install
brew install trufflehog
# or: docker pull trufflesecurity/trufflehog

# Scan local repo (entire git history)
trufflehog git file://. --json

# Scan GitHub org
trufflehog github --org=myorg --token=$GITHUB_TOKEN

# Scan a specific GitHub repo
trufflehog github --repo=https://github.com/org/repo

# Scan S3 bucket
trufflehog s3 --bucket=mybucket

# Only verified secrets (reduces false positives)
trufflehog git file://. --only-verified

# Docker image scan
trufflehog docker --image=myapp:latest

# Output JSON for pipeline
trufflehog git file://. --json 2>/dev/null | jq '.SourceMetadata'
```

## GitLeaks

```bash
# Install
brew install gitleaks
# or: go install github.com/gitleaks/gitleaks/v8@latest

# Detect secrets in current repo
gitleaks detect --source=. -v

# Scan with custom config
gitleaks detect --source=. --config=.gitleaks.toml

# Protect mode — check staged changes (use in pre-commit)
gitleaks protect --staged -v

# Report output
gitleaks detect --source=. --report-format=json --report-path=gitleaks-report.json

# Example .gitleaks.toml (add custom patterns)
# [extend]
# useDefault = true
# [[rules]]
# id = "internal-api-key"
# regex = '''MY_APP_KEY_[A-Z0-9]{32}'''
```

## detect-secrets (Pre-Commit Integration)

```bash
# Install
pip install detect-secrets

# Scan current directory
detect-secrets scan > .secrets.baseline

# Audit baseline (review each finding)
detect-secrets audit .secrets.baseline

# Run as pre-commit check
detect-secrets scan --baseline .secrets.baseline
```

## Pre-Commit Hook Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/trufflesecurity/trufflehog
    rev: v3.63.7
    hooks:
      - id: trufflehog
        args: ["git", "file://.", "--only-verified", "--fail"]

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.1
    hooks:
      - id: gitleaks
```

```bash
# Install pre-commit and hooks
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Common Secret Patterns Detected

```
AWS Access Key:       AKIA[0-9A-Z]{16}
GitHub Token:         ghp_[a-zA-Z0-9]{36}
Slack Token:          xox[baprs]-[0-9a-zA-Z]{10,48}
Google API Key:       AIza[0-9A-Za-z\-_]{35}
Private Keys:         -----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----
Stripe Keys:          sk_live_[0-9a-zA-Z]{24}
Twilio:               SK[0-9a-fA-F]{32}
Generic password:     password\s*=\s*['\"][^'"]{8,}['"]
```

## GitHub Native Secret Scanning

- Enabled automatically on all public repos
- Enable on private repos: Settings → Code security → Secret scanning
- Push protection: blocks push if secrets detected
- View alerts: Security → Secret scanning alerts

## If Secrets Are Found in History

```bash
# Rotate the credential immediately — assume it's compromised
# Then remove from history using BFG or git-filter-repo

# BFG Repo Cleaner (faster than filter-branch)
java -jar bfg.jar --replace-text passwords.txt myrepo.git
cd myrepo.git && git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force

# Never rely on "deleted" history being safe — rotate the secret first
```
