# 15 — Fixtures i Seed Data

Stack: Go 1.22 + MySQL 8.0. Environments: local (Docker Compose), dev (AWS EKS), staging (AWS EKS).

---

## 1. Strategija po environmentu

```
Local (Docker Compose):
  docker compose up → MySQL empty → go-service seed → fixtures loaded
  make dev → uvijek svježe fixtures

Dev (AWS EKS):
  terraform apply → RDS empty → pipeline: migrate + seed → fixtures loaded
  Pokreće se automatski pri kreiranju environment-a

Staging (AWS EKS):
  terraform apply → RDS empty → pipeline: mysqldump prod → restore
  Staging NEMA fixtures — ima kopiju prod podataka

Prod:
  terraform apply → RDS empty → pipeline: migrate only (nema seed!)
  Korisnici sami popunjavaju podatke
```

Ključno pravilo: **fixtures nikada ne idu u staging ili prod**. Staging dobija kopiju produkcijske baze putem `mysqldump`. Dev i lokalni environment dobijaju deterministički set test podataka.

---

## 2. Go seed komanda — implementacija

Dodaj command u go-service. Seed se registruje kao subkomanda uz `migrate`, `worker` i sl.

```go
// cmd/seed.go
package main

import (
    "context"
    "database/sql"
    "flag"
    "fmt"
    "log"

    "golang.org/x/crypto/bcrypt"
)

// Seeder drži referencu na DB konekciju i izvršava sve seed operacije.
type Seeder struct {
    db *sql.DB
}

func runSeed(db *sql.DB) {
    ifEmpty := flag.Bool("if-empty", false, "Run seed only if DB is empty")
    flag.Parse()

    seeder := &Seeder{db: db}
    ctx := context.Background()

    if *ifEmpty {
        count, err := seeder.countUsers(ctx)
        if err != nil {
            log.Fatalf("count users: %v", err)
        }
        if count > 0 {
            fmt.Printf("Skipping seed: %d users already exist\n", count)
            return
        }
    }

    fmt.Println("Running seed...")
    if err := seeder.seed(ctx); err != nil {
        log.Fatalf("seed failed: %v", err)
    }
    fmt.Println("Seed complete.")
}

func (s *Seeder) countUsers(ctx context.Context) (int, error) {
    var count int
    return count, s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM users").Scan(&count)
}

func (s *Seeder) seed(ctx context.Context) error {
    // Transakcija: sve ili ništa — djelimičan seed je gori od prazne baze
    tx, err := s.db.BeginTx(ctx, nil)
    if err != nil {
        return err
    }
    defer tx.Rollback()

    if err := s.seedUsers(ctx, tx); err != nil {
        return fmt.Errorf("seed users: %w", err)
    }

    return tx.Commit()
}
```

Zašto transakcija: ako seed korisnika A uspije ali korisnik B ne, aplikacija dobija nepotpun skup fixture podataka. `defer tx.Rollback()` garantira čišćenje u slučaju greške — `Commit()` poništava efekt `Rollback()` ako sve prođe.

---

## 3. Fixture korisnici — različiti slučajevi upotrebe

Svaki fixture korisnik pokriva konkretan scenarij testiranja. Nije dovoljno imati "admin" i "user" — trebaju i edge case korisnici za neočekivane tokove.

```go
func (s *Seeder) seedUsers(ctx context.Context, tx *sql.Tx) error {
    users := []struct {
        Email    string
        Password string
        Role     string
        IsActive bool
        Notes    string
    }{
        // ── Admin i test korisnici ──────────────────────────────
        {
            Email:    "admin@project-a.local",
            Password: "Admin123!",
            Role:     "admin",
            IsActive: true,
            Notes:    "Admin korisnik za dev",
        },
        {
            Email:    "user@project-a.local",
            Password: "User123!",
            Role:     "user",
            IsActive: true,
            Notes:    "Standardni korisnik za dev",
        },
        // ── Playwright E2E test korisnici ───────────────────────
        {
            Email:    "e2e-test@project-a.local",
            Password: "E2ETest123!",
            Role:     "user",
            IsActive: true,
            Notes:    "Playwright automation korisnik",
        },
        {
            Email:    "synthetic@monitor.internal",
            Password: "Synthetic123!",
            Role:     "user",
            IsActive: true,
            Notes:    "Synthetic monitoring korisnik (prod safe)",
        },
        // ── Edge case korisnici za testiranje ───────────────────
        {
            Email:    "unverified@project-a.local",
            Password: "Unverified123!",
            Role:     "user",
            IsActive: false, // Nije verificirao email
            Notes:    "Za testiranje unverified flow-a",
        },
    }

    for _, u := range users {
        hash, err := bcrypt.GenerateFromPassword([]byte(u.Password), 12)
        if err != nil {
            return err
        }

        _, err = tx.ExecContext(ctx, `
            INSERT INTO users (email, password_hash, is_active, created_at, updated_at)
            VALUES (?, ?, ?, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                password_hash = VALUES(password_hash),
                is_active     = VALUES(is_active),
                updated_at    = NOW()
        `, u.Email, string(hash), u.IsActive)

        if err != nil {
            return fmt.Errorf("insert %s: %w", u.Email, err)
        }
        fmt.Printf("  ✓ %s (%s)\n", u.Email, u.Notes)
    }
    return nil
}
```

`ON DUPLICATE KEY UPDATE` čini seed **idempotentnim**: može se pokrenuti više puta bez kreiranja duplikata. Ako korisnik već postoji, password hash se ažurira — korisno kada promijeniš test lozinku.

`bcrypt.GenerateFromPassword` s cost faktorom 12 je spor (~300ms po korisniku). Za 5 korisnika prihvatljivo. Ako imas 100+ fixture korisnika, snizi na 10 za dev brzinu.

---

## 4. Registracija seed komande u main.go

Svi subcommands se registruju na jednom mjestu. `os.Args` shift je neophodan jer `flag.Parse()` čita od `os.Args[1:]` — bez shifta bi `seed` bio parseran kao flag argument.

```go
// cmd/main.go
package main

import (
    "log"
    "os"
)

func main() {
    if len(os.Args) < 2 {
        runAPIServer()
        return
    }

    switch os.Args[1] {
    case "migrate":
        runMigrations()
    case "seed":
        os.Args = os.Args[1:] // shift args za flag.Parse() u runSeed
        runSeed(initDB())
    case "seed:e2e":
        runSeedE2E(initDB()) // Čisti i svježi E2E korisnici
    case "worker":
        runWorker()
    default:
        log.Fatalf("Unknown command: %s", os.Args[1])
    }
}
```

`initDB()` je helper koji čita `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` iz environment varijabli i vraća `*sql.DB`. Isti helper koristi API server — ne dupliciraj konekcijsku logiku.

---

## 5. Pokretanje seedova

### Lokalno (Docker Compose)

```bash
# Automatski u Makefile (make dev → docker compose up → seed):
docker compose exec go-service /server seed

# Sa --if-empty zastavicom (sigurno za ponovljeno pokretanje):
docker compose exec go-service /server seed --if-empty

# Force override — obriše stare hasheve, piše nove:
docker compose exec go-service /server seed
```
> **Podman:** `podman compose exec go-service /server seed`

Makefile integracija:

```makefile
.PHONY: dev seed

dev:
	docker compose up -d
	docker compose exec go-service /server migrate
	docker compose exec go-service /server seed --if-empty

seed:
	docker compose exec go-service /server seed
```
> **Podman:** zamijeni `docker compose` sa `podman compose` u Makefile targetima

### Na AWS EKS (kubectl)

```bash
# Dev environment — jednom po kreiranju, preskače ako postoje podaci:
kubectl exec -n project-a-dev deployment/go-service -- /server seed --if-empty

# Force re-seed (pažnja u dijeljenom dev env!):
kubectl exec -n project-a-dev deployment/go-service -- /server seed

# Provjeri status:
kubectl exec -n project-a-dev deployment/go-service -- \
  /server seed --if-empty 2>&1
# Očekivani output: "Skipping seed: 5 users already exist" → OK
# Ako vidiš "Seed complete." → seed je upravo prošao prvi put
```

---

## 6. Seed kao Kubernetes Job u Helm pipeline-u

Helm hook `post-install,post-upgrade` osigurava da seed Job teče **nakon** što je Deployment kreiran i migracije završene. `hook-weight: "10"` znači da seed čeka migracije koje imaju manji weight.

```yaml
# helm/project-a/templates/seed-job.yaml
{{- if .Values.seed.enabled }}
apiVersion: batch/v1
kind: Job
metadata:
  name: seed-{{ .Release.Revision }}
  namespace: {{ .Release.Namespace }}
  annotations:
    "helm.sh/hook": post-install,post-upgrade
    "helm.sh/hook-weight": "10"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 120
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: seed
          image: {{ .Values.goService.image.repository }}:{{ .Values.goService.image.tag }}
          command: ["/server", "seed", "--if-empty"]
          env:
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: host
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: username
            - name: DB_NAME
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: dbname
{{- end }}
```

Helm values po environmentu:

```yaml
# values/dev.yaml
seed:
  enabled: true  # Dev dobija fixtures automatski

# values/staging.yaml
seed:
  enabled: false  # Staging dobija prod dump, ne fixtures

# values/prod.yaml
seed:
  enabled: false  # Prod nema seed — korisnici popunjavaju sami
```

`hook-delete-policy: before-hook-creation,hook-succeeded` — stari Job se briše pri sljedećem deployu i odmah po uspješnom završetku. `hook-delete-policy: hook-failed` bi zadržao neuspješne Jobove za debug — dodaj ga tokom razvoja seed logi ke.

---

## 7. GitLab CI pipeline integracija

```yaml
# .gitlab-ci.yml

seed:dev:
  stage: migrate  # Poslije migrate, prije verify
  needs:
    - migrate:dev
    - deploy:dev
  image: bitnami/kubectl:1.29
  environment: development
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  script:
    - echo "$KUBE_CONFIG_DEV" | base64 -d > ~/.kube/config

    # Čekaj da go-service bude spreman prije seed-a
    - kubectl rollout status deployment/go-service -n project-a-dev --timeout=3m

    # Seed samo ako je prazan (--if-empty) — siguran za svaki push na main
    - |
      RESULT=$(kubectl exec -n project-a-dev deployment/go-service -- \
        /server seed --if-empty 2>&1)
      echo "$RESULT"
      echo "$RESULT" | grep -q "Seed complete\|Skipping seed" || exit 1

    - echo "Seed complete"

# Manuelni trigger za dev reset — korisno kad treba čista baza za debugging
reseed:dev:
  stage: migrate
  when: manual
  needs: []
  image: bitnami/kubectl:1.29
  environment: development
  script:
    - echo "$KUBE_CONFIG_DEV" | base64 -d > ~/.kube/config
    - kubectl exec -n project-a-dev deployment/go-service -- /server seed
    - echo "Force reseed complete"
```

Zašto `grep -q "Seed complete\|Skipping seed" || exit 1`: osigurava da CI ne prođe tiho ako seed komanda vrati neočekivani output (npr. greška bez exit code > 0 zbog loše error handling-a).

---

## 8. Playwright test korisnici — poseban seed

Playwright testovi zahtijevaju **deterministički čist state** pri svakom pokretanju. Nasumični emailovi (`uuid@test.com`) su anti-pattern jer kompliciraju debugging i ostavljaju smeće u bazi.

```go
// Seed:e2e komanda — briše i kreira svježe test korisnike
func runSeedE2E(db *sql.DB) {
    ctx := context.Background()

    // Čisti state — briši sve test korisnike
    if _, err := db.ExecContext(ctx,
        "DELETE FROM users WHERE email LIKE '%@project-a.local'",
    ); err != nil {
        log.Fatalf("delete test users: %v", err)
    }
    if _, err := db.ExecContext(ctx,
        "DELETE FROM users WHERE email LIKE '%@monitor.internal'",
    ); err != nil {
        log.Fatalf("delete monitor users: %v", err)
    }

    // Kreiraj svježe korisnike kroz isti seeder
    seeder := &Seeder{db: db}
    tx, err := db.BeginTx(ctx, nil)
    if err != nil {
        log.Fatalf("begin tx: %v", err)
    }
    defer tx.Rollback()

    if err := seeder.seedUsers(ctx, tx); err != nil {
        log.Fatalf("seed e2e users: %v", err)
    }
    if err := tx.Commit(); err != nil {
        log.Fatalf("commit: %v", err)
    }

    fmt.Println("E2E seed complete.")
}
```

GitLab CI — seed:e2e uvijek teče **prije** Playwright testova:

```yaml
seed:e2e:staging:
  stage: migrate
  needs:
    - deploy:staging
  image: bitnami/kubectl:1.29
  environment: staging
  script:
    - echo "$KUBE_CONFIG_STAGING" | base64 -d > ~/.kube/config
    - kubectl exec -n project-a-staging deployment/go-service -- /server seed:e2e
    - echo "E2E seed complete"

e2e:staging:
  stage: test
  needs:
    - seed:e2e:staging
  # ... playwright testovi koriste hardkodirane emailove iz seeda
```

Playwright test fajl koristi konstante, ne generiše emailove:

```typescript
// tests/constants.ts
export const TEST_USERS = {
  admin: {
    email: "admin@project-a.local",
    password: "Admin123!",
  },
  user: {
    email: "user@project-a.local",
    password: "User123!",
  },
  e2e: {
    email: "e2e-test@project-a.local",
    password: "E2ETest123!",
  },
  unverified: {
    email: "unverified@project-a.local",
    password: "Unverified123!",
  },
} as const;
```

---

## 9. Lokalni fixtures fajl za brzi razvoj

Za slučaj kada ne pokrećeš cijeli Docker stack (npr. samo testiraš migracije ili radiš na mašini bez Dockera):

```sql
-- scripts/fixtures.sql
-- Direktni SQL import bez potrebe za go-service binarijom.
-- Bcrypt hashevi odgovaraju lozinkama iz Go seeda.
-- VAŽNO: Ažuriraj hasheve ako promijeniš lozinke u seed.go!

INSERT IGNORE INTO users (email, password_hash, is_active, created_at, updated_at)
VALUES
  ('admin@project-a.local',      '$2a$12$rKfvK7xQp3mN8jLwY2aBcOtHdE1uVnPsA4gIqFyZe6kRmXoT5bJh.', 1, NOW(), NOW()),
  ('user@project-a.local',       '$2a$12$tL9pJ4wRm7nK3eXvD1cBsOuGhF2vZoQpB5iJrEyAf7jSmYnU6aKg.', 1, NOW(), NOW()),
  ('e2e-test@project-a.local',   '$2a$12$nM5bV2xTp8qL4fYwE3dCtPvIiG3wAqRpC6kKsHzBg8lUnZoV7bJi.', 1, NOW(), NOW()),
  ('synthetic@monitor.internal', '$2a$12$oN6cW3yUp9rM5gZxF4eDuQwJjH4xBrSpD7lLtIaCh9mVoApW8cKj.', 1, NOW(), NOW()),
  ('unverified@project-a.local', '$2a$12$pO7dX4zVq0sN6hAyG5eFvRxKkI5yCsUqE8mMuJbDi0nWpBqX9dLk.', 0, NOW(), NOW());
```

```bash
# Import direktno u MySQL:
mysql -h 127.0.0.1 -P 3306 -u root -p project_a < scripts/fixtures.sql

# Kroz Docker Compose (bez interaktivne lozinke):
docker compose exec -T mysql mysql \
  -u root -p"${MYSQL_ROOT_PASSWORD}" project_a \
  < scripts/fixtures.sql
```
> **Podman:** `podman compose exec -T mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" project_a < scripts/fixtures.sql`

Napomena: `INSERT IGNORE` preskače red ako email već postoji (za razliku od `ON DUPLICATE KEY UPDATE` koji ažurira). Za SQL fajl je `IGNORE` lakši za čitanje i dovoljno dobar za lokalni dev.

---

## 10. Kompletna mapa fajlova

```
go-service/
├── cmd/
│   ├── main.go          ← registracija subcommandova
│   └── seed.go          ← Seeder struct, runSeed, runSeedE2E
│
helm/project-a/
├── templates/
│   └── seed-job.yaml    ← Helm hook Job
└── values/
    ├── dev.yaml         ← seed.enabled: true
    ├── staging.yaml     ← seed.enabled: false
    └── prod.yaml        ← seed.enabled: false
│
scripts/
└── fixtures.sql         ← direktni SQL za lokalni import bez binarije
│
tests/
└── constants.ts         ← hardkodirani emailovi za Playwright
│
.gitlab-ci.yml           ← seed:dev, reseed:dev, seed:e2e:staging jobovi
Makefile                 ← make dev pokreće seed automatski
```

---

## 11. Checklist za implementaciju

```
[ ] go-service ima `seed` komandu implementiranu (cmd/seed.go)
[ ] go-service ima `seed:e2e` komandu za čisti E2E state
[ ] Seed je idempotentno (ON DUPLICATE KEY UPDATE)
[ ] --if-empty zastavica postoji i radi ispravno
[ ] values/dev.yaml: seed.enabled: true
[ ] values/staging.yaml: seed.enabled: false
[ ] values/prod.yaml: seed.enabled: false
[ ] Helm seed-job.yaml postoji s ispravnim hook annotacijama
[ ] GitLab CI: seed:dev job postoji (auto na main)
[ ] GitLab CI: reseed:dev job postoji (manual trigger)
[ ] GitLab CI: seed:e2e:staging job teče prije e2e testova
[ ] E2E test korisnici su u seedu s poznatim lozinkama
[ ] Playwright koristi konstante iz TEST_USERS, ne nasumične emailove
[ ] make dev automatski pokreće seed
[ ] scripts/fixtures.sql postoji za direktni SQL import
[ ] bcrypt cost faktor: 12 za dev (prihvatljivo sporo), 12+ za prod
```
