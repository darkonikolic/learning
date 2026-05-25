# Security in CI/CD

Security gates in the pipeline — catch issues automatically before code ships.

## Resources

- GitHub Actions security hardening: https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions
- OWASP DevSecOps Guideline: https://owasp.org/www-project-devsecops-guideline/
- Cosign (image signing): https://github.com/sigstore/cosign

## Pipeline Security Stages

```
Code commit
    ↓
[Pre-commit hooks]   → secrets scan (trufflehog), linting
    ↓
[SAST]               → Semgrep, Bandit, ESLint security
    ↓
[Build]              → Docker image build
    ↓
[SCA + Container]    → Snyk / Trivy dependency + image scan
    ↓
[Secrets in image]   → Trufflehog docker scan
    ↓
[Deploy to staging]
    ↓
[DAST]               → Nuclei, ZAP baseline scan
    ↓
[Sign image]         → cosign sign
    ↓
[Deploy to prod]
```

## GitHub Actions — Full Security Pipeline

```yaml
name: Security Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Semgrep SAST
        uses: returntocorp/semgrep-action@v1
        with:
          config: p/owasp-top-ten

      - name: Bandit (Python)
        run: |
          pip install bandit
          bandit -r ./src/ -l -i -f json -o bandit.json || true

  sca-and-container:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Snyk dependency check
        run: snyk test --severity-threshold=high
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Trivy container scan
        run: |
          trivy image \
            --exit-code 1 \
            --severity HIGH,CRITICAL \
            myapp:${{ github.sha }}

  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # full history for trufflehog

      - name: Trufflehog secrets scan
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          only-verified: true

  dast:
    needs: [sast, sca-and-container]
    runs-on: ubuntu-latest
    steps:
      - name: Nuclei DAST
        run: |
          nuclei -u http://staging.internal \
            -severity high,critical \
            -exit-code 1

      - name: ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.10.0
        with:
          target: 'http://staging.internal'
```

## Secret Management — Never Hardcode

```bash
# GitHub Secrets (CI use)
# Settings → Secrets and variables → Actions → New repository secret
# Access in workflow: ${{ secrets.MY_SECRET }}

# HashiCorp Vault
vault kv get secret/myapp/db-password
vault kv put secret/myapp/db-password value="s3cr3t"

# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id myapp/db-password

# Pass to container at runtime (not baked in image)
docker run -e DB_PASSWORD=$(vault kv get -field=value secret/db) myapp:latest
```

## Branch Protection Rules

```
Settings → Branches → Add rule for main:
  [x] Require status checks to pass before merging
      → Add: semgrep, trivy-scan, snyk-check
  [x] Require pull request reviews before merging
  [x] Dismiss stale pull request approvals
  [x] Restrict who can push to matching branches
```

## Container Image Signing

```bash
# Install cosign
brew install cosign

# Generate key pair
cosign generate-key-pair

# Sign image after build + scan pass
cosign sign --key cosign.key myregistry/myapp:latest

# Verify before deploy
cosign verify --key cosign.pub myregistry/myapp:latest

# Keyless signing (GitHub OIDC)
cosign sign myregistry/myapp:latest
```
