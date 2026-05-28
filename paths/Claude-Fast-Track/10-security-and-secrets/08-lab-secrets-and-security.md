# Lab 10 — Secrets i sigurnost: env config, gitleaks, .claudeignore

## Cilj
Na kraju ovog laba `task-api` čita DB konfiguraciju iz environment varijabli, gitleaks scan pronalazi namjerno propušteni secret i `".env"` nije u git historiji.

## Preduvjeti
- Lab 09 završen: Docker Compose konfiguracija postoji
- `.env.example` postoji
- `.env` je u `.gitignore`

## Kontekst
task-api trenutno može imati hardcoded portove ili connection stringove. Ovaj lab uvodi proper secrets management: config.go koji čita iz env, gitleaks za scanning, i verifikacija da secrets nisu propušteni. Namjerni "leak" u komentaru je tu da demonstriraš da gitleaks stvarno radi.

## Koraci

### Korak 1 — Napiši config/config.go

Napravi `config/config.go` koji čita konfiguraciju iz environment varijabli:

Otvori Claude sesiju:

```bash
claude
```

```
Read CLAUDE.md.

Create config/config.go that reads configuration from environment variables.

Requirements:
- Package: config
- Struct: Config with fields: Port (string), LogLevel (string), DBHost (string), 
  DBUser (string), DBPassword (string), DBName (string), DBPort (string)
- Function: Load() Config — reads from environment with defaults
- Optional vars use getEnv(key, default) helper — returns default if not set
- Required vars use requireEnv(key) helper — calls log.Fatalf if not set
- Port: optional, default "8080"
- LogLevel: optional, default "info"  
- DB_HOST, DB_USER, DB_PASSWORD, DB_NAME: optional for Phase 1 (empty default OK)
- DB_PORT: optional, default "3306"

CRITICAL: Never log DBPassword value. Only log that connection is configured.

After creating, verify: go build ./...
```

**Provjeri implementaciju:**

```bash
cat config/config.go
```

Provjeri da `DBPassword` nije nigdje logiran. Ako jest:

```
Flaw: DBPassword is logged in config.Load()
Location: config/config.go
Expected: log only that DB is configured, never log the password value
```

---

### Korak 2 — Integriraj config u main.go

```
Update main.go to use config.Load() instead of hardcoded values.

Changes needed:
- Import config package
- Call cfg := config.Load() at startup
- Use cfg.Port for the HTTP server address (e.g., ":"+cfg.Port)
- Log startup with log.Printf("starting task-api on :%s", cfg.Port)

Do not change any handler or store code.
Run go build ./... after change.
```

Testiraj s custom portom:

```bash
PORT=9090 go run main.go &
curl -s http://localhost:9090/tasks
# Ocekivano: []
kill %1
```

---

### Korak 3 — Napiši .gitleaks.toml

gitleaks je alat za skeniranje git historije u potrazi za secrets. Instaliraj ga ako nije:

```bash
# macOS
brew install gitleaks

# Ili direktno (provjeri najnoviju verziju na github.com/gitleaks/gitleaks)
# Zahtijeva Go 1.21+
go install github.com/gitleaks/gitleaks/v8@latest
```

Napravi `.gitleaks.toml` konfiguraciju:

```toml
# .gitleaks.toml
title = "task-api gitleaks config"

[extend]
useDefault = true

[[rules]]
id = "taskapi-hardcoded-password"
description = "Hardcoded database password"
regex = '''(?i)(db_password|database_password|mysql_password)\s*[=:]\s*['"]?[a-z0-9_@#$!]{6,}['"]?'''
tags = ["secret", "password"]

[[rules]]
id = "taskapi-connection-string"
description = "Database connection string with credentials"
regex = '''(?i)(mysql|postgres)://[^:]+:[^@]+@'''
tags = ["secret", "connection-string"]

[allowlist]
description = "Ignore example and test files"
paths = [
  ".env.example",
  ".*_test\\.go$"
]
```

---

### Korak 4 — Namjerno "procuri" secret

Ovo je namjerna vježba. Dodaj hardcoded secret u komentar u nekom Go fajlu:

```bash
# Uradi ovo rucno — dodaj komentar s hardcoded passwordom u config.go
# Primjer:
# // TODO: remove this before push — dev password: DB_PASSWORD=hunter2_dev_secret
```

Edituj `config/config.go` i dodaj komentar na vrhu:

```go
// config package reads application configuration from environment variables.
// Development credentials: DB_PASSWORD=hunter2_dev_secret (REMOVE BEFORE PUSH)
package config
```

Commituj ovaj fajl (namjerno loš commit):

```bash
git add config/config.go
git commit -m "wip: add config package (TODO: remove hardcoded creds)"
```

---

### Korak 5 — Pokreni gitleaks scan

```bash
gitleaks detect --source . --verbose
```

**Očekivani output:**
gitleaks treba pronaći secret iz koraka 4. Vidjet ćeš nešto slično:

```
Finding:     // Development credentials: DB_PASSWORD=hunter2_dev_secret
Secret:      hunter2_dev_secret
RuleID:      generic-password
Entropy:     3.45
File:        config/config.go
Line:        2
Commit:      [hash]
```

Provjeri i git historiju:

```bash
gitleaks detect --source . --log-opts "HEAD~5..HEAD" --verbose
```

---

### Korak 6 — Ukloni propušteni secret

**VAŽNO: nikad ne koristiti samo `git commit --amend` ako je pushano na shared remote — to mijenja historiju. Za ovaj lab je OK jer smo lokalni.**

Budući da secret NIJE pushed (lokalni commit), možemo ga ukloniti:

```bash
# Ukloni komentar s passwordom iz config.go
```

Edituj `config/config.go` i ukloni komentar s passwordom. Zatim:

```bash
git add config/config.go
git commit -m "fix: remove hardcoded password from config comment"
```

Provjeri da scan sada ne pronalazi ništa:

```bash
gitleaks detect --source . --verbose
# Ocekivano: No leaks found
```

**Napomena o git historiji:**
Čak i nakon uklanjanja, password OSTAJE u git historiji (commit koji smo napravili u Koraku 4). U realnom scenariju, trebalo bi:
1. Immediately revoke the secret
2. Use `git filter-branch` ili `BFG Repo Cleaner` za rewrite historije
3. Force push (na shared repo — uz prethodnu komunikaciju s timom)

Za ovaj lab, samo dokumentuj da razumiješ ovaj problem.

---

### Korak 7 — Verifikacija .env zaštite

```bash
# Provjeri da .env nije u git historiji
git log --all -- .env
# Ocekivano: prazan output (nikad nije bio commitovan)

# Provjeri da .env nije tracked
git ls-files .env
# Ocekivano: prazan output

# Provjeri .gitignore
cat .gitignore | grep "\.env"
# Ocekivano: .env

# Provjeri .claudeignore  
cat .claudeignore | grep "\.env"
# Ocekivano: .env
```

---

### Korak 8 — Commituj sigurnosnu konfiguraciju

```bash
git add config/config.go main.go .gitleaks.toml .claudeignore
git commit -m "security: env-based config, gitleaks scan, claudeignore secrets protection"
```

## Verifikacija

- [ ] `config/config.go` postoji i čita PORT, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME iz env
- [ ] `go build ./...` prolazi
- [ ] `PORT=9090 go run main.go` pokreće server na portu 9090
- [ ] `.gitleaks.toml` postoji
- [ ] `gitleaks detect --source .` pronalazi namjerni secret iz Koraka 4 (u historiji)
- [ ] Secret je uklonjen iz koda (no longer in working tree)
- [ ] `gitleaks detect --source . --no-git` ne pronalazi ništa u radnom stablu
- [ ] `.env` nije u git historiji (`git log --all -- .env` vraća ništa)
- [ ] DBPassword nije nigdje logiran u config.go

## Šta si naučio

- **requireEnv vs getEnv**: required secrets uzrokuju fatal startup ako nedostaju — to je željeno ponašanje (fail early, fail loudly)
- **Secret u komentaru** je jednako opasan kao i secret u kodu — gitleaks hvata oba
- **git historija** pamti sve — uklanjanje fajla ne briše secret iz historije, potreban je history rewrite
- **.claudeignore + settings.json deny** su dupla zaštita — ako Claude pita za .env, deny lista ga blokira; .claudeignore mu govori da ni ne pita
- **Revoke immediately** kad se secret propusti — prije bilo kakve sanacije koda, revoke the credential. Rotacija je uvijek prvi korak.
