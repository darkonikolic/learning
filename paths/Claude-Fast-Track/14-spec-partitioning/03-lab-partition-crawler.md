# Lab 14 — Spec partitioning: podijeli crawler na 3 faze

## Cilj
Na kraju ovog laba crawler feature je podijeljen u 3 zasebne SPEC-e s dependency graphom, faze 1 i 2 su implementirane, faza 3 ostaje SPEC-only (vježba zaustavljanja u scope-u).

## Preduvjeti
- Lab 13 završen: `cmd/crawler/main.go` postoji, crawler radi
- `docs/crawler/` postoji s failure analysis dokumentacijom
- task-api server radi

## Kontekst
Monolitni crawler iz Lab 13 radi, ali kao jedan blob koda. Ovaj lab razbija ga na 3 logične faze s eksplicitnim dependency graphom. Ključna lekcija: faza 3 (scheduling) ostaje SPEC-only — vježba discipline zaustavljanja i ne implementiranja out-of-scope feature-a čak i kad je "lako dodati".

## Koraci

### Korak 1 — Analiziraj postojeći crawler i particioniraj ga

Otvori Claude sesiju:

```bash
claude
```

```
Read cmd/crawler/main.go and docs/crawler/ directory.

Partition the crawler into 3 phases based on ownership domains:

Phase 1: Fetch + Parse
- Scope: HTTP call to jsonplaceholder, JSON parsing, validation
- Output: []Todo struct with id, title, completed fields
- Ownership: data_source package

Phase 2: Dedup + Insert
- Scope: check for duplicate titles in task-api, insert new todos
- Dependencies: Phase 1 output ([]Todo), task-api running
- Output: InsertReport{inserted, skipped, failed}
- Ownership: task_inserter package

Phase 3: Scheduling (SPEC ONLY — do not implement)
- Scope: periodic execution, configurable interval
- Dependencies: Phase 1 + Phase 2
- Ownership: scheduler package

For each phase, describe:
1. What it provides (output contract)
2. What it consumes (input dependencies)
3. Whether it can run independently

Do not create any code yet — just the analysis.
```

---

### Korak 2 — Napiši SPEC za Fazu 1: Fetch + Parse

Napravi `docs/specs/crawler-phase1-fetch-parse.md`:

```
Create docs/specs/crawler-phase1-fetch-parse.md using the full SPEC template.

Phase 1 scope:
- Fetch all todos from https://jsonplaceholder.typicode.com/todos
- Parse JSON response into []Todo
- Validate: title must not be empty, id must be positive integer
- Return: []Todo, error

SPEC requirements:
- Problem: one sentence
- Goal: measurable output
- Out of scope: deduplication, insertion, scheduling, authentication  
- Constraint: stdlib only for HTTP; max timeout 10 seconds
- Acceptance: minimum 5 binary criteria covering:
  - Successful fetch returns N todos
  - Each todo has required fields
  - Empty title is filtered/rejected
  - Network timeout is handled
  - Response status != 200 is handled
- Provides: []Todo with fields {ID int, Title string, Completed bool}
- Consumes: nothing (no dependencies)
```

Provjeri:

```bash
cat docs/specs/crawler-phase1-fetch-parse.md
```

---

### Korak 3 — Napiši SPEC za Fazu 2: Dedup + Insert

Napravi `docs/specs/crawler-phase2-dedup-insert.md`:

```
Create docs/specs/crawler-phase2-dedup-insert.md.

Phase 2 scope:
- Accept []Todo from Phase 1
- Check task-api GET /tasks for existing titles (dedup check)
- Insert only todos that don't already exist (by title)
- Return: InsertReport with counts

SPEC requirements:
- Consumes: Phase 1 output ([]Todo), task-api running at configured URL
- Provides: InsertReport{Inserted int, Skipped int, Failed int, Errors []string}
- Constraint: dedup by title exact match (case-sensitive)
- Acceptance: minimum 6 criteria covering:
  - All non-duplicate todos are inserted
  - Duplicate titles are skipped (not error)
  - task-api unavailable returns error (not panic)
  - InsertReport counts match actual operations
  - Empty input returns empty report (not error)
  - Partial failure: some inserted, some failed → report both

This spec depends on Phase 1 being approved.
Note in the Consumes section: "Consumes: Phase 1 rev 1 ([]Todo with ID, Title, Completed fields)"
```

---

### Korak 4 — Napiši SPEC za Fazu 3 (SPEC-only)

Napravi `docs/specs/crawler-phase3-scheduling.md`:

```
Create docs/specs/crawler-phase3-scheduling.md.

Phase 3 scope:
- Periodic execution of Phase 1 + Phase 2
- Configurable interval (env var: CRAWLER_INTERVAL, default 1 hour)
- Graceful shutdown on SIGINT/SIGTERM
- Run report logged after each execution

Requirements:
- Status: SPEC ONLY — NOT IMPLEMENTED
- Add a clear note at the top: "## Implementation status: SPEC ONLY — Phase 3 is out of scope for current iteration"
- Acceptance criteria must be written (even though not implemented)
- Consumes: Phase 1 + Phase 2

Do not create any scheduling code.
```

---

### Korak 5 — Napiši dependency graph

Napravi `docs/crawler/dependency-graph.md`:

```
Create docs/crawler/dependency-graph.md with:

1. ASCII dependency graph showing Phase 1 → Phase 2 → Phase 3
2. For each phase:
   - Status: IMPLEMENTED / SPEC ONLY
   - Provides: [output contract]
   - Consumes: [input dependencies]
3. Cross-phase consistency check:
   - Does Phase 2 SPEC use the same field names as Phase 1 SPEC provides?
   - Does Phase 3 SPEC reference Phase 1+2 correctly?
4. Implementation decision table:
   Phase | Status | Reason
   1     | IMPLEMENT | Required for Phase 2
   2     | IMPLEMENT | Core feature
   3     | SPEC ONLY | Out of scope — scheduling not needed for Phase 1 delivery
```

---

### Korak 6 — Implementiraj Fazu 1: Fetch + Parse

Sada implementiraj prema Phase 1 SPEC-u:

```
Implement Phase 1 of the crawler based on docs/specs/crawler-phase1-fetch-parse.md.

Create cmd/crawler/fetcher/fetcher.go:
- Package: fetcher
- Type: Fetcher struct (no fields needed for basic implementation)
- Method: FetchTodos() ([]Todo, error)
- Type: Todo struct {ID int, Title string, Completed bool}
- Timeout: 10 seconds (per SPEC constraint)
- URL: https://jsonplaceholder.typicode.com/todos (or from env TODOS_URL)

Do not implement Phase 2 or Phase 3.
Run go build ./... after creation.
```

**Verificiraj Phase 1:**

```bash
# Napiši kratak test skript
cat > /tmp/test_fetcher.go << 'EOF'
package main

import (
    "fmt"
    "log"
    "github.com/yourname/task-api/cmd/crawler/fetcher"
)

func main() {
    f := fetcher.Fetcher{}
    todos, err := f.FetchTodos()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Fetched %d todos\n", len(todos))
    if len(todos) > 0 {
        fmt.Printf("First: %s\n", todos[0].Title)
    }
}
EOF
go run /tmp/test_fetcher.go
# Ocekivano: Fetched 200 todos
```

---

### Korak 7 — Implementiraj Fazu 2: Dedup + Insert

```
Implement Phase 2 of the crawler based on docs/specs/crawler-phase2-dedup-insert.md.

Create cmd/crawler/inserter/inserter.go:
- Package: inserter
- Type: Inserter struct {TaskAPIURL string}
- Method: Insert(todos []fetcher.Todo) (InsertReport, error)
- Type: InsertReport struct {Inserted int, Skipped int, Failed int, Errors []string}
- Dedup: GET /tasks from task-api, check titles, skip if already exists
- Insert: POST /tasks for non-duplicates

Dependency: imports fetcher package from Phase 1.
Do not implement scheduling (Phase 3).
Run go build ./... after creation.
```

**Verificiraj Phase 2:**

```bash
# Server mora biti up
go run main.go &
SERVER_PID=$!

go test ./cmd/crawler/inserter/... -v 2>&1 | head -30

kill $SERVER_PID 2>/dev/null
```

---

### Korak 8 — Verificiraj da Faza 3 ostaje SPEC-only

Provjeri da nema scheduling koda:

```bash
grep -r "CRAWLER_INTERVAL\|time.Tick\|ticker\|cron\|schedule" cmd/crawler/
# Ocekivano: nema output-a (samo u SPEC fajlu ako postoji)

grep -r "scheduler\|periodic" cmd/crawler/
# Ocekivano: nema output-a u .go fajlovima
```

Provjeri da Phase 3 SPEC postoji:

```bash
head -5 docs/specs/crawler-phase3-scheduling.md
# Ocekivano: "## Implementation status: SPEC ONLY"
```

---

### Korak 9 — End-to-end test: Faza 1 + 2 zajedno

Napravi ažurirani crawler binary koji koristi Faze 1 i 2:

```
Update cmd/crawler/main.go to use the fetcher and inserter packages.

Flow:
1. Create fetcher.Fetcher{}, call FetchTodos()
2. Create inserter.Inserter{TaskAPIURL: "http://localhost:8080"}, call Insert(todos)
3. Print the InsertReport

Do NOT add scheduling (Phase 3 is out of scope).
Run go build ./cmd/crawler/... after update.
```

Test:

```bash
go run main.go &

go run cmd/crawler/main.go
# Ocekivano: report s brojem insertovanih/skippovanih todos

kill %1
```

---

### Korak 10 — Commituj sve

```bash
git add cmd/crawler/ docs/specs/crawler-*.md docs/crawler/dependency-graph.md
git commit -m "feat: crawler partitioned into 3 phases — Phase 1+2 implemented, Phase 3 SPEC-only"
```

## Verifikacija

- [ ] `docs/specs/crawler-phase1-fetch-parse.md` postoji s ≥5 ACs
- [ ] `docs/specs/crawler-phase2-dedup-insert.md` postoji s ≥6 ACs
- [ ] `docs/specs/crawler-phase3-scheduling.md` postoji s explicit "SPEC ONLY" status header-om
- [ ] `docs/crawler/dependency-graph.md` postoji s ASCII grafom
- [ ] `cmd/crawler/fetcher/fetcher.go` postoji (Phase 1 implementirana)
- [ ] `cmd/crawler/inserter/inserter.go` postoji (Phase 2 implementirana)
- [ ] Nema scheduling koda u cmd/crawler/ (`grep -r "time.Tick" cmd/crawler/` je prazan)
- [ ] `go build ./...` prolazi
- [ ] End-to-end crawler insertuje todos s dedup-om

## Šta si naučio

- **Particioniranje po ownership domenama** nije po broju linija — fetcher i inserter su zasebni domeni jer ih bi održavali zasebni timovi
- **Dependency graph** je eksplicitni contract: Phase 2 ne može početi dok Phase 1 nije approved — jer Phase 2 SPEC koristi Phase 1 output types
- **SPEC-only faza** je disciplina zaustavljanja — Phase 3 je "lako dodati", ali nije u scopeu. Dokumentovati pa ne implementovati je jača disciplina nego ne dokumentovati
- **Cross-phase consistency**: field names u Phase 1 provides moraju biti isti kao field names u Phase 2 consumes — to je upstream/downstream contract
- **Phased delivery**: možeš isporučiti Phase 1 + 2 danas, Phase 3 sljedeće sedmice, bez da imaš monolitni "sve ili ništa" delivery
