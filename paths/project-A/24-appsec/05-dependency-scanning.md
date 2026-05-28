# 05 — Dependency Scanning

## Zašto Dependency Scanning

Svaka aplikacija koristi desetine ili stotine biblioteka (dependencies). Svaka od tih biblioteka može imati poznatu ranjivost (CVE — Common Vulnerabilities and Exposures).

### Realni Incidenti

**Log4Shell (CVE-2021-44228)** — Decembar 2021
- Biblioteka: Apache Log4j2 (Java logging)
- Ranjivost: RCE (Remote Code Execution) — napadač šalje string kao input, biblioteka ga izvršava kao komandu
- CVSS Score: 10.0 (maksimalan)
- Uticaj: Pogođene su milijarde sistema. Amazon, Apple, Cloudflare, Microsoft, većina enterprise softvera
- Fix: Update Log4j2 na 2.17.1+

**Polyfill.io incident** — Jun 2024
- Šta se desilo: CDN domen `cdn.polyfill.io` je preuzela kineska kompanija i počela inject-ovati maliciozni JavaScript
- Uticaj: 100,000+ web stranica koje su koristile `<script src="https://cdn.polyfill.io/...">` su distribuirale malware
- Lekcija: Ne koristiti vanjske CDN-ove za kritični JavaScript. Self-host sve skripte.

**xz utils backdoor (CVE-2024-3094)** — Mart 2024
- Šta se desilo: Kompromitovani maintainer dodao backdoor u xz utils (Linux compression tool)
- Uticaj: SSH pristup sistemima s kompromitovanom verzijom
- Lekcija: Supply chain napadi su realni i sofisticirani

**Naš stack je ranjiv na:**
- Go module s poznatim CVE-ovima (`golang.org/x/net`, `golang.org/x/crypto`, itd.)
- npm paketi s RCE ili XSS ranjivostima
- Composer (PHP) paketi
- Bazni Docker image-i s OS ranjivostima

---

## Go Dependency Vulnerabilities

### govulncheck — Googleov Zvanični Tool

`govulncheck` provjerava Go module-e protiv Go Vulnerability Database (`vuln.go.dev`) — zvanična Google/Go tim baza.

```bash
# Instalacija:
go install golang.org/x/vuln/cmd/govulncheck@latest

# Skeniranje lokalnog projekta:
govulncheck ./...

# Output primjer:
# Vulnerability #1: GO-2024-2660
# A malicious HTTP/2 sender can cause excessive CPU consumption
# More info: https://pkg.go.dev/vuln/GO-2024-2660
# Module: golang.org/x/net
# Found in: golang.org/x/net@v0.16.0
# Fixed in: golang.org/x/net@v0.23.0
# Example traces found:
# ...
```

### govulncheck u Docker (bez instalacije Go lokalno)

```bash
# U CI/CD ili ako Go nije instaliran lokalno:
docker run --rm \
  -v $(pwd)/services/go-service:/app \
  -w /app \
  golang:1.22-alpine \
  sh -c "go install golang.org/x/vuln/cmd/govulncheck@latest && govulncheck ./..."
```

### go.sum i Module Integrity

Go automatski verifikuje integritet modula:

```bash
# go.sum sadrži hash za svaki modul
# Automatska provjera pri svakom go build/test/get
cat go.sum | head -5
# golang.org/x/crypto v0.19.0 h1:ENy74+V9E5KqWX8T5KHGh+WJB59sNFalvq8kbCOBKCs=
# golang.org/x/crypto v0.19.0/go.mod h1:Hs8ZFb9HkHMYo8vxNSfk3CAN7yLY5LlRhBpJEMzEWo=

# Provjeri da niko nije tampero s go.sum:
go mod verify
# all modules verified
```

### Automatski Update Go Dependencies

```bash
# Provjeri zastarjele module:
go list -m -u all 2>/dev/null | grep '\['
# github.com/gin-gonic/gin v1.9.0 [v1.9.1]
# golang.org/x/crypto v0.16.0 [v0.21.0]

# Update jednog modula:
go get golang.org/x/crypto@latest

# Update svih modula (pažnja — može break-ati API):
go get -u ./...

# Uvijek pokreni testove nakon update-a:
go test ./...
```

---

## npm Audit za Vue.js

### Lokalno

```bash
cd services/frontend

# Instaliraj i auditi:
npm ci && npm audit

# Samo high i critical:
npm audit --audit-level=high

# Output:
# found 2 vulnerabilities (1 moderate, 1 high)
# 
# high: Regular Expression Denial of Service in semver
# fix: npm audit fix
# 
# moderate: Prototype Pollution in lodash
# More info: https://github.com/advisories/GHSA-p6mc-m468-83gw

# Automatski fix (bezbedan):
npm audit fix

# Fix s breaking changes (pažnja!):
npm audit fix --force
```

### U Docker-u

```bash
docker run --rm \
  -v $(pwd)/services/frontend:/app \
  -w /app \
  node:20-alpine \
  sh -c "npm ci --prefer-offline && npm audit --audit-level=high"
```

### npm audit Limiti

`npm audit` provjerava samo direktne i transitivne dependencije iz `package-lock.json`. Ali:

```bash
# Provjeri i devDependencies (obično nisu na produkciji, ali mogu biti u CI):
npm audit --include=dev

# Lista svih zastarjelih paketa:
npm outdated

# Interaktivni update (lokalno samo):
npx npm-check-updates -i
```

### package-lock.json Mora Biti u git-u

```gitignore
# .gitignore — NE dodavaj ovo:
# package-lock.json  ← GREŠKA! lock fajl mora biti commitovan

# Ispravno:
node_modules/       # Generirani, ne commitovati
dist/               # Build output, ne commitovati
# package-lock.json se NE ignoriše
```

Bez `package-lock.json`: `npm install` može instalirati različite verzije na dev vs CI vs prod → različita ponašanja, različite ranjivosti.

---

## Composer Audit za PHP

### Lokalno

```bash
cd services/php-service

# composer audit (ugrađeno od Composer 2.4+):
composer audit

# Output:
# Found 1 security vulnerability advisory affecting 1 package:
# Package: guzzlehttp/guzzle
# CVE:     CVE-2023-29197
# Title:   Improper header validation in Guzzle
# URL:     https://github.com/advisories/GHSA-q2pj-9pq2-4j2v
# Affected versions: >=7.0.0,<7.5.0
# Reported at: 2023-04-17T00:00:00+00:00
```

### U Docker-u

```bash
docker run --rm \
  -v $(pwd)/services/php-service:/app \
  -w /app \
  php:8.3-cli \
  sh -c "composer install --no-interaction && composer audit"
```

### composer.lock Mora Biti u git-u

Isto kao `package-lock.json` — mora biti commitovan:

```bash
# Provjeri zastarjele pakete:
composer outdated

# Update jednog paketa:
composer update slim/slim

# Update svih (pažnja — provedi testove!):
composer update
```

---

## GitLab Dependency Scanning (Ugrađeno)

GitLab dolazi s Dependency Scanning kao dio GitLab SAST/Security alata. Besplatno za sve planove od GitLab 15.4+.

```yaml
# .gitlab-ci.yml

include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml

variables:
  DS_EXCLUDED_PATHS: "vendor,node_modules,migrations,tests"
  # DS_EXCLUDED_ANALYZERS: "" # Sve analizatore uključi
  
dependency_scanning:
  stage: test
  # GitLab automatski bira pravi analizator:
  # - gemnasium za Gemfile (Ruby)
  # - gemnasium-maven za pom.xml (Java)
  # - retire.js za package.json (JavaScript)
  # - gemnasium za composer.json (PHP)
  # - govulncheck za go.mod (Go)
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

**Gdje vidjet rezultate:** GitLab UI → MR → Security → Dependency Scanning tab

Ranjivosti se prikazuju u MR-u s:
- Severity (Critical/High/Medium/Low)
- CVE broj i link
- Affected i fixed verzija
- Option to create issue

### Blocking na Critical Ranjivosti

```yaml
# Dodaj u .gitlab-ci.yml za blokiranje deploymenta:
dependency_scanning_gate:
  stage: verify  # Nakon dependency_scanning stage-a
  image: alpine:latest
  script:
    - |
      # Provjeri da nema critical ranjivosti u artifact-u
      if [ -f gl-dependency-scanning-report.json ]; then
        CRITICAL=$(cat gl-dependency-scanning-report.json | \
          python3 -c "import json,sys; data=json.load(sys.stdin); \
          print(len([v for v in data.get('vulnerabilities', []) if v.get('severity') == 'Critical']))")
        
        if [ "$CRITICAL" -gt "0" ]; then
          echo "BLOKIRANO: $CRITICAL Critical ranjivost(i) pronađene!"
          exit 1
        fi
      fi
  needs: [dependency_scanning]
```

---

## Renovate Bot — Automatski Dependency Updates

Renovate Bot automatski kreira MR-ove za dependency update-e. Integriše se s GitLab-om.

### Konfiguracija u GitLab-u

1. GitLab → Settings → Integrations → Renovate (ili self-hosted Renovate)
2. Ili dodaj `renovate.json` u root projekta za Renovate GitHub App / Mend Renovate

### `renovate.json` Konfiguracija

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "timezone": "Europe/Sarajevo",
  "schedule": ["before 9am on Monday"],
  "labels": ["dependencies", "automated"],
  "automerge": false,
  "assignees": ["@darko"],
  "reviewers": ["@darko"],
  
  "packageRules": [
    {
      "matchUpdateTypes": ["patch"],
      "matchCurrentVersion": "!/^0/",
      "automerge": true,
      "automergeType": "pr",
      "minimumReleaseAge": "3 days"
    },
    {
      "matchUpdateTypes": ["minor", "major"],
      "automerge": false,
      "labels": ["dependencies", "review-required"]
    },
    {
      "matchPackageNames": ["golang.org/x/crypto", "golang.org/x/net"],
      "groupName": "Go security packages",
      "automerge": true
    },
    {
      "matchManagers": ["npm"],
      "matchDepTypes": ["devDependencies"],
      "automerge": true,
      "minimumReleaseAge": "1 day"
    }
  ],
  
  "vulnerabilityAlerts": {
    "enabled": true,
    "automerge": true,
    "labels": ["security", "urgent"]
  },
  
  "lockFileMaintenance": {
    "enabled": true,
    "schedule": ["before 9am on the first day of the month"]
  }
}
```

### Renovate Workflow

```
1. Renovate Bot skenira go.mod, package.json, composer.json
   (po rasporedu: ponedjeljak ujutro)

2. Pronađe: golang.org/x/net v0.16.0 → v0.26.0

3. Kreira MR:
   Title: "chore(deps): update module golang.org/x/net to v0.26.0"
   
4. GitLab CI pokrne sve testove na MR-u
   - Ako testovi prolaze + patch update → automerge (ako konfigurisano)
   - Ako minor/major → čeka review

5. Security vulnerability update:
   - Renovate odmah kreira MR (ne čeka raspored)
   - Label: "security", "urgent"
   - Može biti automerge za patch security fix-ove
```

---

## Kompletan Dependency Scanning Pipeline

```yaml
# .gitlab-ci.yml — dependency scanning sekcija

stages:
  - build
  - scan
  - verify
  - deploy

# --- Go dependency scan ---
go:vuln-check:
  stage: scan
  image: golang:1.22-alpine
  script:
    - cd services/go-service
    - go install golang.org/x/vuln/cmd/govulncheck@latest
    - govulncheck ./... | tee govulncheck-report.txt
    - |
      # Fail pipeline ako ima HIGH ili CRITICAL
      if grep -q "Vulnerability #" govulncheck-report.txt; then
        echo "Go vulnerabilities found!"
        cat govulncheck-report.txt
        exit 1
      fi
  artifacts:
    when: always
    paths:
      - services/go-service/govulncheck-report.txt
    expire_in: 1 week

# --- npm audit ---
npm:audit:
  stage: scan
  image: node:20-alpine
  script:
    - cd services/frontend
    - npm ci --prefer-offline
    - npm audit --audit-level=high --json > npm-audit-report.json || true
    - |
      HIGH=$(cat npm-audit-report.json | node -e "
        const data = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'));
        const counts = data.metadata?.vulnerabilities || {};
        console.log((counts.high || 0) + (counts.critical || 0));
      ")
      if [ "$HIGH" -gt "0" ]; then
        echo "HIGH/CRITICAL npm vulnerabilities found: $HIGH"
        npm audit --audit-level=high
        exit 1
      fi
  artifacts:
    when: always
    paths:
      - services/frontend/npm-audit-report.json

# --- Composer audit ---
php:composer-audit:
  stage: scan
  image: php:8.3-cli
  script:
    - cd services/php-service
    - curl -sS https://getcomposer.org/installer | php
    - php composer.phar install --no-interaction --no-dev
    - php composer.phar audit --no-dev --format=json > composer-audit-report.json || true
    - |
      ADVISORIES=$(cat composer-audit-report.json | \
        php -r "
          \$data = json_decode(file_get_contents('php://stdin'), true);
          echo count(\$data['advisories'] ?? []);
        ")
      if [ "$ADVISORIES" -gt "0" ]; then
        echo "Composer security advisories found: $ADVISORIES"
        php composer.phar audit --no-dev
        exit 1
      fi
  artifacts:
    when: always
    paths:
      - services/php-service/composer-audit-report.json

# --- GitLab ugrađeni Dependency Scanning ---
include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml
```

---

## Urgentni Proces za CVE Fikseve

Kad CERT/GitLab/Renovate javi kritičnu ranjivost:

```bash
# 1. Provjeri je li naša verzija ranjiva:
govulncheck ./...                    # Go
npm audit --audit-level=critical     # npm
composer audit                       # PHP

# 2. Provjeri postoji li fix:
go get golang.org/x/net@latest       # Go
npm update <paket>                   # npm
composer update <vendor/paket>       # PHP

# 3. Pokreni testove:
go test ./...
npm test
composer test

# 4. Kreira MR s labelom "security":
git checkout -b security/fix-CVE-2024-XXXXX
git commit -am "security: update golang.org/x/net to fix CVE-2024-XXXXX"
# Push i kreira MR

# 5. Fast-track review — security fix-evi ne čekaju normalni review proces
```

---

## Cheatsheet: Komande za Svaki Dan

```bash
# Provjeri Go ranjivosti:
govulncheck ./...

# Provjeri npm ranjivosti:
npm audit --audit-level=moderate

# Provjeri PHP ranjivosti:
composer audit

# Provjeri zastarjele Go module:
go list -m -u all 2>/dev/null | grep '\['

# Provjeri zastarjele npm pakete:
npm outdated

# Provjeri zastarjele Composer pakete:
composer outdated --direct

# Verifikacija integriteta Go modula:
go mod verify

# Provjeri sve Docker image-e za OS ranjivosti (Trivy):
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image projekta-a/go-service:latest
```
