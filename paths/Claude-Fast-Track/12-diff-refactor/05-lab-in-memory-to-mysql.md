# Lab 12 — Refaktor: in-memory store → MySQL storage

## Cilj
Na kraju ovog laba `task-api` koristi MySQL storage umjesto in-memory store-a, svi API endpoints rade s MySQL, testovi prolaze, nema orphaned code, i svaka promjena je pregledana kroz diff review disciplinu.

## Preduvjeti
- Lab 09 završen: Docker Compose s MySQL radi (`docker compose up` podiže MySQL)
- Lab 10 završen: config/config.go postoji i čita DB konfiguraciju
- Lab 11 završen: `docs/specs/mysql-store.md` postoji s acceptance criteria
- `tasks/mysql_store_test.go` postoji (iz Lab 11)
- `go build ./...` prolazi
- `go test ./...` prolazi (in-memory testovi)

## Kontekst
Ovo je najveći refaktor do sada: mijenjamo storage layer a da ne mijenjamo HTTP API. Ključna disciplina: korak-po-korak, svaki korak kompajlira i testovi prolaze. Nikad ne brišemo stari kod dok novi nije verificiran. Koristimo diff review na svakom koraku.

## Koraci

### Korak 1 — Identifikuj blast radius

PRIJE pisanja ijedne linije koda, mapiraš šta će se promijeniti:

Otvori Claude sesiju:

```bash
claude
```

```
Read tasks/store.go, tasks/handler.go, main.go, config/config.go.

Perform blast radius analysis for replacing MemStore with MySQLStore:

1. List all files that import or use the store package
2. List all methods that would need a MySQL equivalent
3. List all places in main.go where store is instantiated
4. Identify any handler code that accesses store struct fields directly (not through interface)
5. List tests that depend on in-memory behavior

Write the analysis to docs/refactor/mysql-migration-blast-radius.md
```

Provjeri output:

```bash
cat docs/refactor/mysql-migration-blast-radius.md
```

---

### Korak 2 — Definiši Store interface

Ako ne postoji, napravi eksplicitan Store interface koji oba store-a moraju implementirati:

```
Read tasks/store.go.

Create or update the Store interface in tasks/store.go.
The interface must include all methods used by handler:
- AddTask(title string) (Task, error)
- List() ([]Task, error)
- CompleteTask(id string) (Task, error)

IMPORTANT: If handler currently uses MemStore directly (not through interface),
that is a scope boundary violation. Report it — do not fix it yet.

Run go build ./... after change.
```

**Diff review:**

```bash
git diff tasks/store.go
```

Provjeri: dodaje li ovaj commit SAMO interface definiciju? Ne smije mijenjati MemStore, handler, niti main.go u ovom koraku.

---

### Korak 3 — Implementiraj MySQLStore

Ovo je najveći korak. Pokreni MySQL container:

```bash
docker compose up -d db
```

```
Create tasks/mysql_store.go implementing the Store interface.

Context:
- Interface: tasks/store.go (Store interface)
- SPEC: docs/specs/mysql-store.md (acceptance criteria)
- Test file: tasks/mysql_store_test.go (tests are already written)
- Config: config/config.go (connection details)

Requirements:
- Type: MySQLStore struct with *sql.DB field
- Constructor: NewMySQLStore(cfg config.Config) (*MySQLStore, error)
- Method: Setup() error — runs CREATE TABLE IF NOT EXISTS
- Implement all 3 Store interface methods
- Use database/sql stdlib + github.com/go-sql-driver/mysql
- Error wrapping: fmt.Errorf("AddTask: %w", err)
- Task ID: generate with crypto/rand (UUID format)
- Table: tasks (id VARCHAR(36), title VARCHAR(200), completed BOOLEAN DEFAULT FALSE, created_at DATETIME)

Idempotent setup:
CREATE TABLE IF NOT EXISTS tasks (
  id VARCHAR(36) PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  completed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

After creating, run: go build ./...
```

---

### Korak 4 — Diff review za mysql_store.go

OBAVEZNO pregledati svaki hunk:

```bash
git diff --stat
git diff tasks/mysql_store.go
```

Provjeri svaki hunk:

| Provjera | Prolazi? |
|----------|----------|
| Koristi stdlib database/sql? | |
| Jedini external package je go-sql-driver/mysql? | |
| Sve SQL greške su wrapped? | |
| Task ID je generiran (ne priman od handlera)? | |
| completeTask je idempotentno? | |
| Nema direktan struct field access? | |

Ako nešto ne prolazi, revertuj i popravit:

```
Flaw: [opis]
Location: tasks/mysql_store.go:[line/function]
Expected: [ocekivano ponasanje]
Do not change: [sta ne treba mijenjati]
```

---

### Korak 5 — Napiši idempotent migraciju

Dodaj setup SQL u MySQLStore (ako nije u Koraku 3):

```
Add a Setup() method to MySQLStore in tasks/mysql_store.go.

Requirements:
- Creates tasks table if not exists (idempotent)
- SQL: CREATE TABLE IF NOT EXISTS tasks (...)
- Returns error if creation fails

This method will be called from main.go during startup.
Run go build ./... after change.
```

Provjeri da je idempotentno:

```bash
# Pokreni Setup() dva puta — ne smije fail-ati
# Testirat ćemo to u sljedećem koraku
```

---

### Korak 6 — Integriraj MySQLStore u main.go

```
Update main.go to support both MemStore and MySQLStore based on environment.

Logic:
- If DB_HOST env var is set: use MySQLStore (call NewMySQLStore, then Setup())
- If DB_HOST is not set: use MemStore (existing behavior — backward compatible)

Import go-sql-driver/mysql with blank import: import _ "github.com/go-sql-driver/mysql"

Run go build ./... after change.
```

Provjeri diff:

```bash
git diff main.go
```

Provjeri: mijenja li samo main.go? Nema handler ili store izmjena?

---

### Korak 7 — Pokreni integration testove

```bash
# MySQL mora biti up
docker compose up -d db

# Pricekaj healthcheck
until docker compose ps | grep "db" | grep "healthy"; do
  echo "Waiting for MySQL..."
  sleep 2
done

# Pokreni integration testove (iz Lab 11)
go test -tags integration ./tasks/... -v -run TestMySQLStore
```

**Očekivani output:**
Testovi koji su pisali u Lab 11 sad trebaju prolaziti (ne skipovati). Ako testovi failikovaju, pročitaj poruku greške i popravit koristeći targeted correction pattern:

```
Flaw: TestMySQLStore_List_ReturnsEmptySlice fails with [error message]
Location: tasks/mysql_store.go, List() method
Expected: [ocekivano ponasanje per AC-03]
```

---

### Korak 8 — End-to-end test s MySQL

```bash
# Pokreni cijeli stack
docker compose up -d

# Pricekaj da je sve up
sleep 5

# Testiraj sve endpointe
# POST /tasks
ID=$(curl -s -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"mysql test task"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Created task: $ID"

# GET /tasks
curl -s http://localhost:8080/tasks | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
print(f'Tasks: {len(tasks)}')
print(f'First: {tasks[0][\"title\"]}')
"

# PATCH /tasks/:id/complete
curl -s -X PATCH http://localhost:8080/tasks/$ID/complete | python3 -c "
import sys, json
t = json.load(sys.stdin)
print(f'Completed: {t.get(\"completed\") or t.get(\"done\")}')
"

# GET /tasks - provjeri completed status
curl -s http://localhost:8080/tasks | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
for t in tasks:
    print(f'{t[\"title\"]}: {t.get(\"completed\") or t.get(\"done\")}')
"
```

Restart server i provjeri da podaci PREŽIVLJAVAJU restart (ovo je ključna razlika od in-memory):

```bash
docker compose restart app

# Pricekaj da se app restartuje
sleep 3

# Taskovi moraju biti i dalje tu
curl -s http://localhost:8080/tasks | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
print(f'After restart: {len(tasks)} tasks (should be > 0 if MySQL works)')
"
```

---

### Korak 9 — Identifikuj orphaned code

Provjeri postoji li kod koji se više ne koristi:

```
Read tasks/store.go (MemStore), tasks/mysql_store.go (MySQLStore), main.go, tasks/handler.go.

Find any orphaned code:
1. Methods on MemStore that are NOT in the Store interface
2. Fields in MemStore struct that are NOT needed for interface implementation
3. Helper functions in store.go that are never called
4. Any imports that are no longer used

Report findings. Do not remove anything yet — just report.
```

Donesi odluku o svakom orphaned item:
- Ako je MemStore korisni fallback: ostavi ga
- Ako je dead code: ukloni ga u zasebnom commit-u

---

### Korak 10 — Final diff review i commituj

```bash
# Pregledaj sve promjene od pocetka laba
git diff HEAD~3...HEAD --stat
git log --oneline -5
```

Provjeri da svaki commit ima jednu jasnu svrhu. Tada:

```bash
go test ./...
go test -tags integration ./tasks/...
go build ./...
```

Sve mora prolaziti. Zatim:

```bash
git add go.mod go.sum tasks/mysql_store.go docs/refactor/ docs/specs/mysql-store.md
git commit -m "feat: MySQL storage layer with backward-compatible fallback to MemStore"
```

## Verifikacija

- [ ] `docker compose up` pokreće cijeli stack
- [ ] POST /tasks, GET /tasks, PATCH /tasks/:id/complete rade s MySQL
- [ ] Podaci preživljavaju server restart (key MySQL validation)
- [ ] `go test ./...` prolazi (in-memory testovi)
- [ ] `go test -tags integration ./tasks/...` prolazi (MySQL testovi)
- [ ] Coverage > 80% za mysql_store.go
- [ ] `docs/refactor/mysql-migration-blast-radius.md` postoji
- [ ] Nema orphaned code (ili je dokumentovano zašto ostaje)
- [ ] go.mod sadrži samo stdlib + go-sql-driver/mysql kao external package

## Šta si naučio

- **Interface-first refactoring**: definicija Store interface-a PRIJE implementacije MySQLStore-a — handler ne mora znati koji store koristi
- **Blast radius analiza** prije refaktoring-a sprečava surprises — znaš točno koji fajlovi će biti dirnuti
- **Idempotent migrations** (`CREATE TABLE IF NOT EXISTS`) znače da možeš restartovati app bez straha od duplikata
- **Korak-po-korak** svaki korak kompajlira i testovi prolaze — možeš stati u bilo kom koraku i sistem radi
- **Diff review na svakom koraku** hvata scope creep — svaki hunk mora imati razlog zašto je tu
