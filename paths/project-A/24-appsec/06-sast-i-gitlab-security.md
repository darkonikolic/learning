# 06 — SAST i GitLab Security

## Šta Je SAST

SAST (Static Application Security Testing) analizira izvorni kod **bez pokretanja aplikacije**. Traži poznate uzorke ranjivog koda.

```
Developer piše kod
      ↓
git push / MR otvoren
      ↓
GitLab CI pokrne SAST
      ↓
Analizator skenira izvorni kod
  - Traži SQL injection uzorke
  - Traži hardcoded secrets
  - Traži insecure crypto funkcije
  - Traži command injection
      ↓
Rezultati u GitLab Security Dashboard
      ↓
Developer vidi findings u MR-u
```

**Prednosti:** Brzo (sekunde do minuta), integriše se u svaki commit, pronalazi greške rano (cheap to fix).

**Mane:** False positives (lažni alarmi), ne pronalazi runtime logičke ranjivosti, ne testira konfiguraciju.

---

## GitLab SAST (Ugrađeno, Besplatno)

GitLab SAST je besplatan za sve GitLab planove (Free, Premium, Ultimate). Automatski detektuje jezik i bira odgovarajući analizator.

### Aktivacija

```yaml
# .gitlab-ci.yml

include:
  - template: Security/SAST.gitlab-ci.yml

variables:
  # Isključi putanje koje ne želimo skenirati
  SAST_EXCLUDED_PATHS: "vendor,node_modules,migrations,tests/fixtures,.git"
  
  # Isključi specifične ranjivosti (false positive management)
  # SAST_EXCLUDED_ANALYZERS: "gosec"  # Ako gosec daje previše false positives
  
  # Putanje za analizatore:
  GOPATH: "$CI_PROJECT_DIR/.go"
```

### Koji Analizatori Se Koriste

GitLab automatski bira na osnovu fajlova u projektu:

| Jezik | Analizator | Detektuje |
|-------|-----------|-----------|
| Go | `gosec` | SQL injection, weak crypto, command injection, hardcoded creds |
| PHP | `phpcs-security-audit` + `semgrep` | XSS, SQLi, file inclusion, eval |
| JavaScript/Vue | `semgrep`, `eslint-sast` | XSS, prototype pollution, eval |
| Secrets (svi) | `gitleaks` | API ključevi, tokeni, lozinke |

### Napredna Konfiguracija

```yaml
# .gitlab-ci.yml

include:
  - template: Security/SAST.gitlab-ci.yml

sast:
  variables:
    SAST_EXCLUDED_PATHS: "vendor,node_modules,migrations"
  
  # Pokreni SAST samo na MR-ovima i default branch-u
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: always
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: always
    - when: never

# Override za gosec (Go SAST):
gosec-sast:
  variables:
    GOFLAGS: "-mod=mod"
    # Disable specific rules koje su false positive u našem kodu:
    # G304 = "File path provided as taint input" — OK za config file loading
    GOSEC_OPTIONS: "-exclude=G304"
  before_script:
    - cd services/go-service
```

### Gdje Vidjet Rezultate

1. **MR page**: GitLab → MR → Security tab → SAST findings
2. **Security Dashboard**: GitLab → Project → Security → Dashboard
3. **Pipeline artifacts**: `gl-sast-report.json`

---

## gosec — Go Security Checker

gosec je Go-specifičan SAST tool koji GitLab koristi interno.

```bash
# Lokalna instalacija i pokretanje:
go install github.com/securego/gosec/v2/cmd/gosec@latest

# Skeniranje:
cd services/go-service
gosec ./...

# Output primjer:
# [/app/repository/user.go:45] - G201 (CWE-89): SQL string formatting (Confidence: HIGH, Severity: HIGH)
#    45: query := fmt.Sprintf("SELECT * FROM users WHERE email = '%s'", email)
```

### gosec Pravila Relevantna za Naš Stack

```
G101 — Hardcoded credentials (lozinke/ključevi u kodu)
G102 — Bind to all interfaces (0.0.0.0 — ok za kontejnere, ali pazi)
G103 — Use of unsafe.Pointer
G104 — Errors unhandled (err ne provjeren)
G106 — Use of ssh InsecureIgnoreHostKey
G107 — URL provided to HTTP request as taint input (SSRF)
G201 — SQL query construction using format string (SQL INJECTION!)
G202 — SQL query construction using string concatenation (SQL INJECTION!)
G203 — Use of unescaped data in HTML templates (XSS)
G204 — Subprocess launched with variable (Command Injection)
G401 — Use of weak cryptographic primitive (MD5, SHA1)
G402 — TLS InsecureSkipVerify set to true
G403 — Use of weak key length for RSA/DSA/EC
G404 — Use of weak random number generator (math/rand vs crypto/rand)
G501 — Import blocklist: crypto/md5
G502 — Import blocklist: crypto/des
```

### Lokalno kao Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Pokrećem gosec skeniranje..."

if command -v gosec &> /dev/null; then
    cd services/go-service
    gosec -quiet ./... 2>&1
    if [ $? -ne 0 ]; then
        echo "BLOKIRANO: gosec je pronašao sigurnosne probleme!"
        echo "Pokreni 'gosec ./...' za detalje."
        exit 1
    fi
fi

exit 0
```

```bash
chmod +x .git/hooks/pre-commit
```

---

## Semgrep — Customizabilni SAST

Semgrep je moćan SAST tool koji dolazi sa stotinama gotovih pravila i podržava custom pravila za naš specifičan stack.

### U GitLab CI

```yaml
# .gitlab-ci.yml

semgrep:
  stage: test
  image: semgrep/semgrep:latest
  script:
    - |
      semgrep \
        --config=auto \
        --config=p/owasp-top-ten \
        --config=p/golang \
        --config=p/php \
        --config=p/javascript \
        --config=.semgrep/custom-rules.yml \
        --error \
        --exclude=vendor \
        --exclude=node_modules \
        --exclude="*.test.go" \
        --json > semgrep-report.json
    - |
      # Brojimo CRITICAL i HIGH findings:
      CRITICAL=$(cat semgrep-report.json | \
        python3 -c "
        import json, sys
        data = json.load(sys.stdin)
        findings = data.get('results', [])
        critical = sum(1 for f in findings if f.get('extra', {}).get('severity') == 'ERROR')
        print(critical)
        ")
      echo "Critical findings: $CRITICAL"
      if [ "$CRITICAL" -gt "0" ]; then
        semgrep --config=.semgrep/custom-rules.yml --error ./services/  # Pokaži output
        exit 1
      fi
  artifacts:
    when: always
    reports:
      sast: semgrep-report.json
    paths:
      - semgrep-report.json
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Custom Semgrep Pravila za Naš Stack

```yaml
# .semgrep/custom-rules.yml

rules:
  # Pravilo 1: SQL injection via fmt.Sprintf
  - id: go-sql-sprintf-injection
    patterns:
      - pattern: fmt.Sprintf($QUERY, ...)
      - metavariable-pattern:
          metavariable: $QUERY
          pattern-regex: "(?i)(select|insert|update|delete|drop|union).*(%s|%v|%d)"
    message: |
      Potencijalni SQL injection: string formatting u SQL upitu.
      Koristiti prepared statements: db.QueryRowContext(ctx, query, params...)
    languages: [go]
    severity: ERROR
    metadata:
      category: security
      cwe: CWE-89
      owasp: A03:2021

  # Pravilo 2: SQL concatenation u Go
  - id: go-sql-string-concat
    patterns:
      - pattern: |
          $QUERY = $QUERY + $VAR
      - pattern-not: |
          $QUERY = $QUERY + "?"
    message: |
      SQL string concatenation može biti SQL injection ranjivost.
      Koristiti parameterized queries.
    languages: [go]
    severity: WARNING
    metadata:
      cwe: CWE-89

  # Pravilo 3: fmt.Sprintf u SQL query-u (stringbuilder varijanta)
  - id: go-sql-fmt-in-query
    pattern: |
      $DB.$METHOD(fmt.Sprintf(...), ...)
    message: |
      Direktno fmt.Sprintf u DB method pozivu je SQL injection ranjivost.
    languages: [go]
    severity: ERROR
    metadata:
      cwe: CWE-89

  # Pravilo 4: PHP eval() — command injection
  - id: php-eval-user-input
    patterns:
      - pattern: eval($INPUT)
      - pattern-not: eval("...")  # String literal je ok (ali i dalje loš stil)
    message: |
      eval() s user inputom je Remote Code Execution ranjivost.
    languages: [php]
    severity: ERROR
    metadata:
      cwe: CWE-94

  # Pravilo 5: PHP shell_exec s variablama
  - id: php-shell-exec-injection
    patterns:
      - pattern: shell_exec($CMD)
      - pattern-not: shell_exec("...")
    message: |
      shell_exec() s varijablom može biti Command Injection.
      Koristiti escapeshellarg() ili proc_open() s array parametrima.
    languages: [php]
    severity: ERROR
    metadata:
      cwe: CWE-78

  # Pravilo 6: Go http.Get s user inputom (SSRF)
  - id: go-ssrf-http-get
    patterns:
      - pattern: http.Get($URL)
      - pattern-not: http.Get("https://...")
    message: |
      http.Get s dinamičkim URL-om može biti SSRF ranjivost.
      Validiraj URL i dozvoli samo whitelisted hostove.
    languages: [go]
    severity: WARNING
    metadata:
      cwe: CWE-918

  # Pravilo 7: Hardcoded lozinke u Go kodu
  - id: go-hardcoded-password
    patterns:
      - pattern: $VAR := "..."
      - metavariable-pattern:
          metavariable: $VAR
          pattern-regex: "(?i)(password|passwd|secret|api_?key|token)"
    message: |
      Potencijalno hardcoded credentials. Koristiti environment varijable
      ili AWS Secrets Manager (vidjeti modul 14).
    languages: [go]
    severity: WARNING
    metadata:
      cwe: CWE-798

  # Pravilo 8: math/rand umjesto crypto/rand za security-relevant operacije
  - id: go-weak-random-for-tokens
    patterns:
      - pattern: math/rand.$FUNC(...)
      - pattern-near:
          pattern: $VAR := ...token...
    message: |
      math/rand nije kriptografski siguran. Za tokene koristiti crypto/rand.
    languages: [go]
    severity: ERROR
```

### Semgrep Lokalno

```bash
# Instalacija:
pip install semgrep
# ili:
brew install semgrep

# Pokretanje s auto pravilima (preporučeno za prvo skeniranje):
semgrep --config=auto services/go-service/

# Pokretanje s OWASP pravilima:
semgrep --config=p/owasp-top-ten services/

# Custom pravila:
semgrep --config=.semgrep/custom-rules.yml services/

# Interaktivni mode (za debugging pravila):
semgrep --config=.semgrep/custom-rules.yml --verbose services/go-service/
```

---

## Secret Scanning

### GitLab Secret Detection

```yaml
# .gitlab-ci.yml

include:
  - template: Security/Secret-Detection.gitlab-ci.yml

secret_detection:
  variables:
    SECRET_DETECTION_HISTORIC_SCAN: "false"  # true = skenira cijelu git historiju (sporo)
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

GitLab Secret Detection traži:
- AWS Access Keys (`AKIA[0-9A-Z]{16}`)
- Private RSA/PEM ključevi
- GitHub/GitLab tokens
- Stripe API ključeve
- SendGrid, Twilio, Firebase ključeve
- Opće uzorke (`password = "..."`, `api_key = "..."`)

### Gitleaks — Pre-commit i CI

```bash
# Lokalno skeniranje (provjerava i git historiju):
docker run --rm \
  -v $(pwd):/repo \
  zricethezav/gitleaks:latest \
  detect \
  --source=/repo \
  --verbose \
  --redact  # Redaktuje pronađene secretse u outputu

# Skeniranje samo uncommited promjena (brže):
docker run --rm \
  -v $(pwd):/repo \
  zricethezav/gitleaks:latest \
  protect \
  --staged \
  --source=/repo \
  --verbose
```

### `.gitleaks.toml` Konfiguracija

```toml
# .gitleaks.toml

title = "Project-A Gitleaks Config"

[extend]
# Koristi default pravila
useDefault = true

[[rules]]
id = "project-a-internal-key"
description = "Project-A Internal API Key"
regex = '''firma-api-[a-zA-Z0-9]{32}'''
severity = "CRITICAL"

[[rules]]
id = "db-connection-string"
description = "Database connection string with credentials"
regex = '''mysql://[^:]+:[^@]+@[^/]+/'''
severity = "CRITICAL"

[allowlist]
description = "Allowlist for false positives"
regexes = [
    # Test fixture files mogu sadržavati example credentials
    '''example_api_key''',
    '''test_token_placeholder''',
]
paths = [
    '''tests/fixtures/''',
    '''docs/examples/''',
]
```

### Gitleaks kao pre-commit Hook

```yaml
# .pre-commit-config.yaml (koristiti s pre-commit tool-om)

repos:
  - repo: https://github.com/zricethezav/gitleaks
    rev: v8.18.2
    hooks:
      - id: gitleaks
        args: ["protect", "--staged"]
```

```bash
# Instalacija pre-commit:
pip install pre-commit
pre-commit install

# Ručno pokretanje:
pre-commit run gitleaks --all-files
```

---

## Kompletan Security Pipeline

```yaml
# .gitlab-ci.yml — kompletan security sekcija

stages:
  - build
  - security-sast
  - security-secrets
  - test
  - deploy

# --- GitLab ugrađeni ---
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml

# --- Semgrep custom ---
semgrep:custom:
  stage: security-sast
  image: semgrep/semgrep:latest
  script:
    - semgrep --config=.semgrep/custom-rules.yml --error ./services/
  artifacts:
    when: always
    paths: [semgrep-report.json]

# --- Gitleaks (dodatni, GitLab Secret Detection i radi istu stvar) ---
gitleaks:
  stage: security-secrets
  image:
    name: zricethezav/gitleaks:latest
    entrypoint: [""]
  script:
    - /usr/bin/gitleaks detect --source=. --verbose --redact
  allow_failure: false  # Blokiraj pipeline na pronađeni secret

# --- Security gate: blokiraj deployment na critical findings ---
security:gate:
  stage: test  # Nakon security stage-a
  image: python:3.12-alpine
  script:
    - pip install -q jq 2>/dev/null; apk add --no-cache jq
    - |
      CRITICAL=0
      
      # Provjeri SAST report:
      if [ -f gl-sast-report.json ]; then
        SAST_CRITICAL=$(jq '[.vulnerabilities[] | select(.severity == "Critical")] | length' gl-sast-report.json)
        CRITICAL=$((CRITICAL + SAST_CRITICAL))
        echo "SAST Critical: $SAST_CRITICAL"
      fi
      
      # Provjeri Dependency Scanning report:
      if [ -f gl-dependency-scanning-report.json ]; then
        DEP_CRITICAL=$(jq '[.vulnerabilities[] | select(.severity == "Critical")] | length' gl-dependency-scanning-report.json)
        CRITICAL=$((CRITICAL + DEP_CRITICAL))
        echo "Dependency Critical: $DEP_CRITICAL"
      fi
      
      if [ "$CRITICAL" -gt "0" ]; then
        echo "BLOKIRANO: $CRITICAL Critical sigurnosnih nalaza! Deploy nije moguć."
        exit 1
      fi
      
      echo "Security gate prošao. Nema Critical nalaza."
  needs:
    - job: sast
      optional: true
    - job: dependency_scanning
      optional: true
```

---

## Upravljanje False Positives

SAST alati ponekad prijave ranjivosti koje su zapravo lažni alarmi. Kako upravljati:

### gosec Inline Suppression

```go
// Suppres gosec pravilo za konkretnu liniju:
password := config.DefaultAdminPassword // #nosec G101 -- ovo je default lozinka iz env, nije hardcoded

// Suppres za čitav fajl (rijetko koristiti):
// #nosec
```

### Semgrep Inline Suppression

```go
// nosemgrep: go-hardcoded-password
password := "changeme-in-env"  // Ovo je placeholder koji se zamjeni env varijablom

// PHP:
eval($safeConfig); // nosemgrep: php-eval-user-input -- $safeConfig je konstanta, ne user input
```

### GitLab Vulnerability Management

U GitLab UI (Security Dashboard):
1. Klikni na finding
2. "Dismiss" → odaberi razlog: "False positive", "Won't fix", "Acceptable risk"
3. Dodaj komentar s objašnjenjem
4. Finding više ne blokira pipeline (ali ostaje vidljiv u dashboardu)

---

## Lokalni Developer Workflow

```bash
# Ručno pokretanje svih SAST alata lokalno (simulira CI):

# 1. gosec (Go):
cd services/go-service && gosec ./...

# 2. Semgrep:
semgrep --config=.semgrep/custom-rules.yml ./services/

# 3. Gitleaks:
docker run --rm -v $(pwd):/repo zricethezav/gitleaks:latest detect --source=/repo

# 4. npm audit:
cd services/frontend && npm audit --audit-level=high

# 5. govulncheck:
cd services/go-service && govulncheck ./...

# 6. composer audit:
cd services/php-service && composer audit

# Sve u jednom skriptu:
# scripts/security-check.sh
#!/bin/bash
set -e
echo "=== Go SAST (gosec) ==="
(cd services/go-service && gosec ./...)

echo "=== Semgrep ==="
semgrep --config=.semgrep/custom-rules.yml ./services/

echo "=== Go Vulnerabilities ==="
(cd services/go-service && govulncheck ./...)

echo "=== npm Audit ==="
(cd services/frontend && npm audit --audit-level=high)

echo "=== Composer Audit ==="
(cd services/php-service && composer audit)

echo "Sve sigurnosne provjere prošle!"
```
