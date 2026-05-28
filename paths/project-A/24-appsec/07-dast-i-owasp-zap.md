# 07 — DAST i OWASP ZAP

## DAST vs SAST — Kada Koristiti Što

```
SAST (Static):                    DAST (Dynamic):
  - Analizira kod                   - Testira running aplikaciju
  - Svaki commit (brzo)             - Na staging environmentu
  - Pronalazi: SQLi, XSS patterns   - Pronalazi: realne ranjivosti
  - False positives: česti          - False positives: rijetki
  - False negatives: auth logic     - False negatives: coverage nije 100%
  - Bez pokretanja aplikacije       - Zahtijeva deployanu aplikaciju
```

**DAST je neophodan jer:**
- Testira konfiguraciju (security headers, TLS, CORS) — SAST ne vidi ovo
- Testira runtime ponaša aplikacije pod napadom
- Black-box pristup — kao pravi napadač
- Autenticirani testovi provjeravaju endpoints iza login-a

---

## OWASP ZAP

OWASP ZAP (Zed Attack Proxy) je najkorišćeniji open-source DAST tool. Slobodan, aktivno održavan.

### Vrste ZAP Skeniranja

**Baseline Scan (Brzi):**
- Pasivno skeniranje + ograničeni aktivni napadi
- Traje: 5-15 minuta
- Nalazi: security headers, mixed content, CORS greške, info disclosure
- Preporučeno za: svaki deploy na staging

**Full Scan (Kompletni):**
- Svi aktivni napadi (SQL injection, XSS, SSRF, ...)
- Traje: 30-120 minuta
- Nalazi: sve od baseline + aktivne ranjivosti
- Preporučeno za: tjedni/pred-release scan

**API Scan:**
- Koristi OpenAPI/Swagger specifikaciju
- Testira sve definirane endpoint-e
- Preporučeno za: REST API (naš Go backend)

---

## ZAP Baseline Scan u GitLab CI

```yaml
# .gitlab-ci.yml

dast:staging:
  stage: security-dast
  needs: [deploy:staging]  # Čeka deploy na staging
  image:
    name: ghcr.io/zaproxy/zaproxy:stable
    entrypoint: [""]
  variables:
    ZAP_TARGET: "https://app.staging.firma.com"
    ZAP_RULES_FILE: ".zap/rules.tsv"
  script:
    # Baseline scan — brži, za svaki MR
    - |
      zap-baseline.py \
        -t "$ZAP_TARGET" \
        -r zap-baseline-report.html \
        -J zap-baseline-report.json \
        -x zap-baseline-report.xml \
        --hook=.zap/zap-hooks.py \
        -c "$ZAP_RULES_FILE" \
        -I \
        -d  # Debug mode
    
    - |
      # Provjeri FAIL alerts (ne samo warn):
      HIGH_ALERTS=$(python3 -c "
      import json
      with open('zap-baseline-report.json') as f:
          data = json.load(f)
      sites = data.get('site', [])
      high = sum(
          len([a for a in site.get('alerts', []) if a.get('riskcode') in ['3', '4']])
          for site in (sites if isinstance(sites, list) else [sites])
      )
      print(high)
      ")
      echo "High/Critical ZAP alerts: $HIGH_ALERTS"
      if [ "$HIGH_ALERTS" -gt "0" ]; then
        echo "DAST BLOKIRANO: $HIGH_ALERTS High/Critical alert(a)!"
        exit 1
      fi
  artifacts:
    when: always
    paths:
      - zap-baseline-report.html
      - zap-baseline-report.json
    reports:
      dast: zap-baseline-report.json
    expire_in: 2 weeks
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: on_success
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: on_success

# Full scan — samo na main branch (pred produkcijski deploy):
dast:full:
  stage: security-dast
  needs: [deploy:staging]
  image:
    name: ghcr.io/zaproxy/zaproxy:stable
    entrypoint: [""]
  variables:
    ZAP_TARGET: "https://app.staging.firma.com"
  script:
    - |
      zap-full-scan.py \
        -t "$ZAP_TARGET" \
        -r zap-full-report.html \
        -J zap-full-report.json \
        -c ".zap/rules.tsv" \
        -d
  artifacts:
    when: always
    paths:
      - zap-full-report.html
      - zap-full-report.json
    expire_in: 1 month
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: on_success
  allow_failure: true  # Full scan može imati false positives — warn, ne blokiraj
```

---

## ZAP Autentikacija

Bez autentikacije, ZAP testira samo javne endpoint-e. Autentikacija nam omogućava testiranje `/api/users/me`, `/api/orders`, itd.

### Metoda 1: JSON Login (Naš Stack)

```yaml
# .zap/zap-auth-context.yaml
# ZAP 2.x format za JSON autentikaciju

env:
  contexts:
    - name: "project-a-staging"
      urls:
        - "https://app.staging.firma.com"
      
      includePaths:
        - "https://app.staging.firma.com.*"
      
      excludePaths:
        - "https://app.staging.firma.com/api/auth/logout"
        # Ne logout-uj ZAP korisnika tokom testiranja!
      
      authentication:
        method: "json"
        parameters:
          loginPageUrl: "https://app.staging.firma.com/api/auth/login"
          loginRequestData: >
            {
              "email": "zap-test@firma.com",
              "password": "${ZAP_TEST_PASSWORD}"
            }
          usernameParameter: "email"
          passwordParameter: "password"
        
        verification:
          method: "response"
          loggedInRegex: '"access_token":'
          loggedOutRegex: '"error":"unauthorized"'
      
      users:
        - name: "zap-test-user"
          credentials:
            username: "zap-test@firma.com"
            password: "${ZAP_TEST_PASSWORD}"
      
      sessionManagement:
        method: "httpAuthSessionManagement"
        parameters:
          headerName: "Authorization"
          headerValue: "Bearer {%json:access_token%}"
```

### Metoda 2: Script Hook za JWT

Ako JSON autentikacija nije dovoljna (npr. potreban je refresh token flow):

```python
# .zap/zap-auth-script.py
# ZAP Authentication Script (Jython/Python)

import json
import requests

def authenticate(helper, paramsValues, credentials):
    """Poziva se pri svakoj autentikaciji."""
    login_url = paramsValues.get("loginUrl")
    
    response = requests.post(login_url, json={
        "email": credentials.getParam("username"),
        "password": credentials.getParam("password"),
    }, verify=False)
    
    data = response.json()
    access_token = data.get("access_token")
    
    # Postavi token za ZAP session
    helper.prepareMessage()
    helper.getHttpMessage().getRequestHeader().setHeader(
        "Authorization", f"Bearer {access_token}"
    )
    
    return helper.getHttpMessage()

def getRequiredParamsNames():
    return ["loginUrl"]

def getCredentialsParamsNames():
    return ["username", "password"]
```

### ZAP Test Korisnik na Staging

Kreirati poseban ZAP test korisnički nalog na staging:

```go
// migrations/staging-only/002-zap-test-user.go
// Pokrenuti SAMO na staging environmentu!

package main

import (
    "os"
    "golang.org/x/crypto/bcrypt"
)

func createZAPTestUser(db *sql.DB) error {
    if os.Getenv("ENVIRONMENT") != "staging" {
        return nil // Sigurnosna provjera
    }
    
    password := os.Getenv("ZAP_TEST_PASSWORD")
    if password == "" {
        return fmt.Errorf("ZAP_TEST_PASSWORD not set")
    }
    
    hash, _ := bcrypt.GenerateFromPassword([]byte(password), 12)
    
    _, err := db.Exec(`
        INSERT INTO users (email, password_hash, role, active) 
        VALUES ('zap-test@firma.com', ?, 'user', true)
        ON DUPLICATE KEY UPDATE password_hash = ?
    `, hash, hash)
    
    return err
}
```

Čuvaj lozinku u GitLab CI/CD Variables:
```
Settings → CI/CD → Variables → Add variable:
  Key:   ZAP_TEST_PASSWORD
  Value: <random 32+ char password>
  Protected: true
  Masked: true
```

---

## ZAP Rules Konfiguracija

`.zap/rules.tsv` — kontroliše koji alarmi su FAIL (blokiraju pipeline) vs WARN vs IGNORE:

```tsv
# Format: <rule-id>	<action>	# <komentar>
# Actions: FAIL, WARN, IGNORE

# ===== UVIJEK FAIL (blokiraj deploy) =====
40012	FAIL	# Cross Site Scripting (Reflected)
40014	FAIL	# Cross Site Scripting (Persistent)
40016	FAIL	# Cross Site Scripting (Persistent) - Prime
40017	FAIL	# Cross Site Scripting (Persistent) - Spider
90011	FAIL	# Charset Mismatch (Header vs Meta Charset)
40018	FAIL	# SQL Injection
40019	FAIL	# SQL Injection - MySQL
40020	FAIL	# SQL Injection - Hypersonic SQL
40021	FAIL	# SQL Injection - Oracle
40022	FAIL	# SQL Injection - PostgreSQL
40024	FAIL	# SQL Injection - SQLite
10016	FAIL	# Web Browser XSS Protection Not Enabled
10017	FAIL	# Cross-Domain JavaScript Source File Inclusion
10098	FAIL	# Cross-Domain Misconfiguration

# ===== WARN (prijavi ali ne blokiraj) =====
10010	WARN	# Cookie No HttpOnly Flag
10011	WARN	# Cookie Without Secure Flag
10012	WARN	# Password Autocomplete in Browser
10015	WARN	# Incomplete or No Cache-control and Pragma HTTP Header Set
10019	WARN	# Content-Type Header Missing
10021	WARN	# X-Content-Type-Options Header Missing
10035	WARN	# Strict-Transport-Security Header Not Set
10036	WARN	# Server Leaks Version Information
10037	WARN	# Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s)
10038	WARN	# Content Security Policy (CSP) Header Not Set
10040	WARN	# Secure Pages Include Mixed Content
10041	WARN	# HTTP to HTTPS Insecure Transition in Form Post
10063	WARN	# Feature Policy Header Not Set (staro ime za Permissions-Policy)
10096	WARN	# Timestamp Disclosure - Unix
10202	WARN	# Absence of Anti-CSRF Tokens (naša SPA koristi JWT -- WARN, ne FAIL)

# ===== IGNORE (zanemaruj) =====
10027	IGNORE	# Information Disclosure - Suspicious Comments
90033	IGNORE	# Loosely Scoped Cookie (wildcard domain -- naš setup)
```

---

## ZAP Hooks za Naprednu Konfiguraciju

```python
# .zap/zap-hooks.py
# Poziva se od ZAP-a tokom skeniranja

def zap_started(zap, target):
    """Pokrenut pri početku skena."""
    print(f"ZAP scan started for: {target}")
    
    # Isključi skeniranje admin endpoint-a (ne testiramo admin sa ZAP test userkm):
    zap.ascan.disable_all_scanners()
    zap.ascan.enable_scanners("40012,40014,40018,40019")  # Samo SQLi i XSS
    
    # Postavi User-Agent:
    zap.core.set_option_default_user_agent(
        "Mozilla/5.0 ZAP/2.14 (Security Test)"
    )

def zap_spider_complete(zap, target):
    """Poziva se kada spider završi."""
    urls = zap.spider.results()
    print(f"Spider pronašao {len(urls)} URL-ova")
    
    # Loguj URL-ove koji nisu pokriveni:
    covered = set(urls)
    expected = ["/api/auth/login", "/api/users/me", "/api/orders"]
    for ep in expected:
        if not any(ep in u for u in covered):
            print(f"UPOZORENJE: Endpoint nije pokriven skeniranjem: {ep}")

def zap_ajax_spider_complete(zap, target):
    """Ajax spider (za SPA) završio."""
    pass  # Vue.js SPA -- koristiti ajax spider

def zap_scan_complete(zap, target):
    """Aktivni scan završio."""
    alerts = zap.core.alerts()
    high_alerts = [a for a in alerts if a['risk'] in ['High', 'Critical']]
    
    if high_alerts:
        print(f"\n=== KRITIČNI ALARMI ({len(high_alerts)}) ===")
        for alert in high_alerts:
            print(f"[{alert['risk']}] {alert['name']}")
            print(f"  URL: {alert['url']}")
            print(f"  Evidence: {alert.get('evidence', 'N/A')[:100]}")
            print()
```

---

## Interpretacija ZAP Rezultata

### Risk Level Skala

| Risk | Kod | Akcija |
|------|-----|--------|
| Critical | 4 | BLOKIRAJ deploy odmah |
| High | 3 | BLOKIRAJ deploy, fix u 24h |
| Medium | 2 | Warn, fix u sljedećem sprintu |
| Low | 1 | Log, fix kad je zgodno |
| Informational | 0 | Ignoriraj ili zapiši za audit |

### Česti ZAP Nalazi i Fiksevi za Naš Stack

**Missing Security Headers (Low-Medium)**
```nginx
# Fix: Dodaj u nginx konfiguraciju (vidjeti modul 03)
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

**Cookie Without Secure/HttpOnly (Medium)**
```go
// Fix u Go:
c.Header("Set-Cookie", 
    "session=xxx; Secure; HttpOnly; SameSite=Strict; Path=/")
```

**Information Disclosure — Server Header (Low)**
```nginx
# Fix u nginx:
server_tokens off;
more_clear_headers Server;
```

**CORS Misconfiguration (Medium-High)**
```go
// Fix: Whitelist origins (vidjeti modul 03)
allowedOrigins := map[string]bool{
    "https://app.firma.com": true,
}
// Nikad: "Access-Control-Allow-Origin: *" za authenticated endpoints
```

**SQL Injection (High/Critical)**
```go
// Fix: Prepared statements (vidjeti modul 02)
db.QueryRowContext(ctx, "SELECT * FROM users WHERE email = ?", email)
```

---

## DAST Samo na Staging — Strogo Pravilo

```
NIKAD ne pokrećati DAST (ZAP full scan) na produkciji!

Razlozi:
1. ZAP šalje malformiranu/malicioznu data u svaki form i API endpoint
2. SQL injection testovi mogu korumpirati produkcijsku bazu
3. DoS testovi mogu srušiti produkcijski servis
4. Kreiran test korisnici/podaci u produkcijskoj bazi

Jedine iznimke:
- Baseline scan (pasivan) može ići na produkciju (nema aktivnih napada)
- Uz eksplicitno odobrenje i u vansatno vrijeme
- Uz rollback plan

Review apps:
- Previše kratkotrajan za smisleni DAST
- Baza podataka možda nije realna kopija
- Preporučeno: testiraj samo staging (stabilan, s realnim podacima)
```

---

## Kompletna Slika Security Pipeline-a

```
Push/MR
  ↓
┌─────────────────────────────────────────┐
│  Stage: security-sast (brzo, 2-5 min)  │
│  - gosec (Go)                          │
│  - phpcs-security-audit (PHP)          │
│  - eslint-sast (JavaScript/Vue)        │
│  - semgrep custom rules                │
│  - gitleaks (secret scanning)          │
└─────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│  Stage: security-deps (brzo, 3-8 min)  │
│  - govulncheck (Go)                    │
│  - npm audit (npm)                     │
│  - composer audit (PHP)                │
│  - GitLab Dependency Scanning          │
└─────────────────────────────────────────┘
  ↓
┌────────────────────────────────────────────┐
│  Stage: deploy:staging                    │
│  (deploy na staging environment)          │
└────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────┐
│  Stage: security-dast (sporije, 10-30 min)     │
│  - ZAP baseline scan (svaki MR)               │
│  - ZAP full scan (samo main branch)           │
│  - ZAP API scan (OpenAPI spec)               │
└─────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│  Stage: security-gate                   │
│  - Provjeri sve izvještaje             │
│  - BLOKIRAJ na Critical/High           │
│  - WARN na Medium                      │
└─────────────────────────────────────────┘
  ↓ (ako prošlo)
┌─────────────────────────────────────────┐
│  Stage: deploy:production               │
└─────────────────────────────────────────┘
```

---

## Lokalno ZAP Testiranje

```bash
# Pokreni ZAP GUI lokalno (za development):
docker run -u zap -p 8080:8080 -p 8090:8090 \
  -i ghcr.io/zaproxy/zaproxy:stable \
  zap-webswing.sh

# Otvori browser: http://localhost:8090/zap

# Ili headless baseline scan lokalno:
docker run --rm \
  -v $(pwd)/zap-reports:/zap/wrk/:rw \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py \
    -t "https://app.staging.firma.com" \
    -r /zap/wrk/zap-report.html \
    -J /zap/wrk/zap-report.json

# Pregled HTML izvještaja:
open zap-reports/zap-report.html
```

---

## Preporučeni DAST Raspored

```yaml
# Tjedni full scan (cron job u GitLab):
dast:weekly-full:
  stage: security-dast
  script:
    - zap-full-scan.py -t "$ZAP_TARGET" -r report.html
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      when: always
  
# GitLab Scheduled Pipeline:
# Settings → CI/CD → Schedules → Add new schedule
# Opis: "Weekly DAST Full Scan"
# Interval: "0 3 * * 1" (svaki ponedjeljak u 03:00)
# Branch: main
# Variables: ZAP_FULL_SCAN=true
```
