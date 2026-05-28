# Lab 11 — Spec-backed testovi za MySQL store

## Cilj
Na kraju ovog laba imaš test suite za MySQL store layer gdje svaki test mapira na jedan acceptance criterion iz SPEC-a, pronašao/la si edge case koji nije u SPEC-u i dodao/la ga, i coverage je >80%.

## Preduvjeti
- Lab 09 završen: Docker Compose s MySQL radi
- Lab 10 završen: config/config.go postoji
- `docs/specs/` sadrži barem `get-tasks.md` i `complete-task.md`
- `docker compose up` podiže MySQL

## Kontekst
U Lab 09 smo postavili Docker Compose s MySQL, ali task-api još uvijek koristi in-memory storage. Ovaj lab piše testove ZA MYSQL STORE koji još ne postoji — to je spec-driven TDD: testovi se pišu prema SPEC-u, pa implementacija slijedi. Ovo je jedini lab gdje pišeš testove PRIJE implementacije.

## Koraci

### Korak 1 — Definiši MySQL store interface u SPEC-u

Napravi `docs/specs/mysql-store.md`:

```markdown
# SPEC: mysql-store

## Problem
In-memory store gubi sve podatke pri restartu aplikacije. Trebamo persistent storage.

## Goal
MySQL store implementira isti interface kao in-memory store:
AddTask, List, CompleteTask — ali persists data u MySQL bazi.

## Out of scope
- Migracije (koristimo CREATE TABLE IF NOT EXISTS)
- Connection pooling konfiguracija
- Read replicas
- Soft delete

## Constraint
- Must use stdlib database/sql — no ORM, no external DB drivers EXCEPT go-sql-driver/mysql
- go-sql-driver/mysql je jedini dozvoljeni external package (nutna za MySQL)
- All DB errors must be wrapped: fmt.Errorf("operation: %w", err)
- Store mora biti safe za concurrent use (ne treba mutex — MySQL handles concurrency)
- Idempotent setup: CREATE TABLE IF NOT EXISTS

## NFR
- AddTask: < 10ms za lokalni MySQL (hypothesis)
- List: < 20ms za do 1000 taskova (hypothesis)

## Boundary
- Store package: owns all SQL, connection lifecycle, error wrapping
- Handler package: calls store methods, does NOT know SQL exists
- Config package: owns DB connection string construction

## Acceptance
- [ ] AC-01: MySQLStore implementira Store interface (compile-time check)
- [ ] AC-02: AddTask inserira task s auto-generated UUID id i vraća ga s id, title, completed=false, created_at
- [ ] AC-03: List vraća non-nil empty slice kad nema taskova
- [ ] AC-04: List vraća sve taskove u insertion order (ASC created_at)
- [ ] AC-05: CompleteTask postavlja completed na true i vraća ažurirani task
- [ ] AC-06: CompleteTask je idempotentno — drugi poziv vraća isti task s completed=true
- [ ] AC-07: CompleteTask za nepostojeći id vraća specifičnu grešku
- [ ] AC-08: AddTask s praznim title vraća validation error

## Rollback
Revertovati tasks/mysql_store.go. MemStore ostaje kao fallback.
```

---

### Korak 2 — Napiši test stubs prema SPEC-u

Otvori Claude sesiju:

```bash
claude
```

```
Read docs/specs/mysql-store.md.

Create tasks/mysql_store_test.go with empty test stubs.
Each stub corresponds to one acceptance criterion.

Requirements:
- One test function per AC
- Test name format: TestMySQLStore_<Behaviour>_<Condition>
- Comment in each test: // AC-XX: [exact criterion text from SPEC]
- Tests should be empty stubs (t.Skip("not implemented yet") is OK)
- Use stdlib testing package only
- Add build tag: //go:build integration at top

Do NOT implement the tests yet — only stubs.
Do NOT create mysql_store.go yet.
```

**Provjeri stub fajl:**

```bash
cat tasks/mysql_store_test.go
```

Svaki test treba izgledati ovako:

```go
// AC-02: AddTask inserira task s auto-generated UUID id i vraća ga s id, title, completed=false, created_at
func TestMySQLStore_AddTask_ReturnsTaskWithGeneratedID(t *testing.T) {
    t.Skip("not implemented yet")
}
```

---

### Korak 3 — Implementiraj testove (ne store)

Sada implementiraj TESTOVE. Store implementacija dolazi u Lab 12. Za sada ćemo koristiti dummy/mock store da možemo verificirati test strukturu.

```
Implement the test functions in tasks/mysql_store_test.go.

Context: docs/specs/mysql-store.md — each test must verify exactly its AC.

For now, create a test helper that connects to MySQL:
- Host: localhost (or from env: DB_HOST)
- Port: 3306 (or from env: DB_PORT)  
- User: taskapi (or from env: DB_USER)
- Password: dev_secret_123 (or from env: DB_PASSWORD)
- Database: taskapi (or from env: DB_NAME)

Each test should:
1. Skip if DB is not available (use t.Skip if connection fails)
2. Set up a clean table before running
3. Run the test assertion
4. Clean up after

Do NOT create mysql_store.go — tests will fail with "undefined: MySQLStore"
That's expected — we're writing tests before implementation.
```

---

### Korak 4 — Pronađi edge case koji nije u SPEC-u

Razmisli o MySQL-specific edge case-ovima koji nisu u SPEC-u. Primjeri:

- Što se dešava ako MySQL connection padne mid-transaction?
- Što se dešava ako je `title` string od 1000 karaktera (MySQL column limit)?
- Što se dešava s concurrent AddTask pozivima?

Odaberi jedan edge case koji nije pokriven nijednim AC-om. Napiši test za njega:

```
Add one additional test to mysql_store_test.go for an edge case NOT in the SPEC:
[Opiši edge case koji si pronašao/la]

Test name format: TestMySQLStore_EdgeCase_<Description>
Comment: // EDGE CASE (not in SPEC): [opis]
```

Zatim dodaj ovaj edge case u SPEC:

```
Update docs/specs/mysql-store.md to add a new acceptance criterion for the edge case:
- [ ] AC-09: [Binary criterion za tvoj edge case]

Update Implementation strategy and Risk sections if needed.
```

---

### Korak 5 — Pokreni testove (oni će failikovati — to je OK)

Pokreni MySQL container:

```bash
docker compose up -d db
```

Pričekaj da baza bude ready:

```bash
docker compose ps
# db treba biti "healthy"
```

Pokreni testove s integration build tagom:

```bash
go test -tags integration ./tasks/... -v -run TestMySQLStore 2>&1 | head -50
```

**Očekivani output:**
Testovi failikovaju s greškom poput `undefined: MySQLStore` — to je ispravno! Testovi su napisani prema SPEC-u, implementacija još ne postoji.

Ako testovi ne compile-uju uopće, provjeri da je interface definiran (mozda trebas napraviti placeholder):

```bash
# Provjeri compile errore
go build -tags integration ./tasks/... 2>&1
```

---

### Korak 6 — Provjeri coverage cilj

Kada implementiraš MySQL store u Lab 12, ovi testovi moraju pokriti >80% koda.

Za sada, napravi estimate coverage-a na osnovu testova:

```
Review tasks/mysql_store_test.go.
Assuming MySQLStore is fully implemented, estimate:
- What percentage of AddTask logic would be covered?
- What percentage of List logic would be covered?
- What percentage of CompleteTask logic would be covered?
- Are there any obvious coverage gaps?

Report: estimated coverage per method and overall.
```

Ako je coverage estimate < 80%, dodaj testove za nepokrivene paths.

---

### Korak 7 — Commituj testove

```bash
git add tasks/mysql_store_test.go docs/specs/mysql-store.md
git commit -m "test: spec-backed MySQL store tests with AC mappings (implementation pending Lab 12)"
```

## Verifikacija

- [ ] `tasks/mysql_store_test.go` postoji s testovima za sve ACs
- [ ] Svaki test ima komentar `// AC-XX: [criterion text]`
- [ ] Edge case test postoji s komentarom `// EDGE CASE (not in SPEC):`
- [ ] Edge case je dodan u `docs/specs/mysql-store.md` kao AC-09
- [ ] `go build -tags integration ./...` kompajlira (možda s greškama o undefined MySQLStore — OK)
- [ ] `docs/specs/mysql-store.md` postoji s ≥9 ACs
- [ ] Estimated coverage je >80% za svu MySQL store logiku

## Šta si naučio

- **Spec-backed testovi** su derivirani od SPEC AC-a, ne od čitanja koda — zato catch wrong implementation, ne samo implementaciju kakva je
- **Test stubs** se pišu PRIJE implementacije — ovo je spec-driven TDD, ne retrofitting
- **AC mapping comment** (`// AC-02:`) čini traceability eksplicitnom — iduća osoba koja čita test odmah zna koji requirement testira
- **Edge cases izvan SPEC-a** su signal da SPEC treba update — dodavanje AC-09 čini kontrakt potpunijim
- **Integration build tag** (`//go:build integration`) znači da testovi koji zahtijevaju Docker ne runaju u normalnom `go test` — samo kad eksplicitno kažeš `-tags integration`
