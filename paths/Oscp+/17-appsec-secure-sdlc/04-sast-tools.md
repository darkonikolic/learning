# SAST Tools

Static Application Security Testing — scan source code without running it. Integrate into CI/CD to catch issues early.

## Resources

- Semgrep rules registry: https://semgrep.dev/r
- Bandit docs: https://bandit.readthedocs.io/
- SonarQube Community: https://www.sonarqube.org/downloads/

## Semgrep (Best Free Option — Multi-Language)

```bash
# Install
pip install semgrep

# Scan with auto-selected rules (recommended starting point)
semgrep --config=auto src/

# Use specific ruleset from registry
semgrep --config=p/python src/
semgrep --config=p/javascript src/
semgrep --config=p/php src/
semgrep --config=p/go src/
semgrep --config=p/owasp-top-ten src/

# Fail with non-zero exit code on findings (for CI)
semgrep --config=auto --error src/

# JSON output for pipeline ingestion
semgrep --config=auto --json src/ > results.json

# Custom rule example (rules.yaml)
# rules:
#   - id: sql-injection-risk
#     pattern: cursor.execute("..." + $X)
#     message: Possible SQL injection
#     severity: ERROR
#     languages: [python]
semgrep --config=./rules.yaml src/
```

## Bandit (Python Only)

```bash
pip install bandit

# Scan a directory
bandit -r ./src/

# High severity only
bandit -r ./src/ -l -i

# Skip false-positive-heavy tests
bandit -r ./src/ --skip B101,B601

# JSON output
bandit -r ./src/ -f json -o bandit-results.json
```

## Brakeman (Ruby on Rails)

```bash
gem install brakeman

# Basic scan
brakeman app/

# Output HTML report
brakeman -o report.html app/

# Exit non-zero on warnings (CI use)
brakeman --exit-on-warn app/
```

## ESLint Security Plugin (JavaScript/TypeScript)

```bash
npm install --save-dev eslint eslint-plugin-security

# .eslintrc.json
# {
#   "plugins": ["security"],
#   "extends": ["plugin:security/recommended"]
# }

eslint src/
```

## SonarQube (Self-Hosted, Broader Coverage)

```bash
# Run via Docker
docker run -d --name sonarqube -p 9000:9000 sonarqube:community

# Scanner (download sonar-scanner)
sonar-scanner \
  -Dsonar.projectKey=myproject \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=<token>
```

## CI/CD Integration (GitHub Actions)

```yaml
- name: Semgrep SAST
  uses: returntocorp/semgrep-action@v1
  with:
    config: p/owasp-top-ten

- name: Bandit Python scan
  run: |
    pip install bandit
    bandit -r ./src/ -l -i --exit-zero
```

## Triage Notes

- False positives are common — review HIGH/ERROR findings manually
- SAST finds: injection, hardcoded secrets, insecure functions, missing checks
- SAST misses: logic flaws, auth bypass, IDOR (needs DAST or manual review)
- Target: zero HIGH findings in CI before merge
