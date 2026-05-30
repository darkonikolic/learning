# 08 — Vežba: AppSec

Ugradiš AppSec provere (SAST, dependency scan, DAST, security headers) u CI pipeline i verifikuješ da build pada na critical nalazima.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Dodajemo AppSec fazu u GitLab CI — semgrep za SAST, trivy za dependency CVE scan, ZAP baseline za DAST — i postavljamo security headers na aplikaciji. Build mora da padne na critical nalazima.

**Pretpostavke za potvrdu:**
- Semgrep, trivy i ZAP dostupni kao Docker slike ili GitLab CI komponente
- Aplikacija je dostupna na review URL-u za ZAP baseline sken
- Postoji makar jedan endpoint koji vraća HTTP response (za header proveru)

**Van opsega:**
- Pentest / ručni security audit
- Upravljanje CVE izuzecima (samo svesno prihvatanje)
- Konfiguracija WAF-a

**Prompt za diskusiju:**
```
Evo CI konfiguracije i app endpoint-a. Dodaj SAST (semgrep) i dependency scan (trivy) fazu
koja obara build na critical nalazima. Predloži minimalan set security headers (CSP, HSTS,
X-Content-Type-Options, X-Frame-Options) i gde ih postaviti u Go/nginx konfiguraciji.
Koji OWASP Top 10 rizici su relevantni za ovaj servis? Objasni svaki korak.
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** AppSec provere integrisane u CI, build pada na critical, security headers prisutni.

**Fajlovi koji se diraju:**
- `.gitlab-ci.yml` — nova `security` faza
- `nginx.conf` ili middleware fajl — security headers
- `.semgrep/` — opciona lokalna konfiguracija

**Fajlovi koji se NE diraju:**
- `go.sum` / `go.mod` — dependency verzije menja samo vlasnik
- `Dockerfile` — samo ako je CVE u base image (poseban task)

**AI okvir za ovu oblast:**

Dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/appsec-checks.md`

Sadržaj pravila:
```
- CI faza za SAST (semgrep) i dependency scan (trivy); build pada na critical.
- Security headers obavezni: CSP, HSTS, X-Content-Type-Options, X-Frame-Options.
- DAST (ZAP baseline) pokreće se na review app; high-risk alarm blokira merge.
- Validacija i escaping inputa po OWASP Top 10 (injection, XSS) — review pri svakom PR-u.
- Nikad ne commit-ovati tajne; koristiti CI/CD variables ili vault.
```

**Acceptance criteria:**
- [ ] `semgrep` prolazi bez critical nalaza (ili su svesno prihvaćeni sa komentarom)
- [ ] `trivy fs` prolazi bez critical CVE (ili su svesno prihvaćeni)
- [ ] ZAP baseline ne prijavljuje high-risk alarme
- [ ] Security headers prisutni u HTTP response-u (`curl -I`)
- [ ] CI security faza blokira build pri critical nalazu (exit code != 0)
- [ ] Sync zapisan

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Dodati security fazu u .gitlab-ci.yml (semgrep + trivy + ZAP)
2. Dodati security headers u nginx.conf / middleware
3. Lokalno verifikovati svaku alatku pre push-a

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno u CI konfiguraciji za ovaj servis?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Pokreni lokalne provere pre nego što push-uješ na GitLab:

```bash
# SAST — statička analiza koda
docker run --rm -v "$PWD":/src returntocorp/semgrep semgrep --config=auto /src

# Dependency scan — CVE provera
docker run --rm -v "$PWD":/src aquasec/trivy fs /src

# DAST — baseline sken pokrenute aplikacije
docker run --rm -t owasp/zap2docker-stable zap-baseline.py -t https://<host>

# Security headers — proveri response
curl -I https://<host> | grep -E "Strict-Transport|Content-Security|X-Content-Type|X-Frame"
```

GitLab CI push:

```bash
git add .gitlab-ci.yml nginx.conf
git commit -m "feat: add appsec stage (semgrep, trivy, ZAP)"
git push origin feature/appsec
glab ci view   # prati security fazu u GitLab-u
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- semgrep bez critical nalaza
- trivy bez critical CVE
- ZAP baseline bez high-risk alarma
- Security headers prisutni u HTTP response-u
- CI security faza blokira build pri critical nalazu

Evo outputa semgrep / trivy / ZAP i curl -I odgovora:
[ovde lepiš stvarni output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali i kako popraviti?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | `glab ci run` pa otvori Security tab u GitLab-u | Security stage zelen; nema HIGH/CRITICAL nalaza u Security dashboard-u |
| 2 | `curl -I https://<host>` | Response sadrži `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options` |
| 3 | Ubaci intentionalnu ranjivost (npr. `eval(input)`) i push-uj na feature granu | CI security faza pada, merge blokiran |
| 4 | Otvori GitLab Security Dashboard | Dependency scan prikazuje pinned verzije bez critical CVE |
| 5 | Ukloni ranjivost, push-uj ponovo | Security faza prolazi, merge dozvoljen |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — AppSec sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
