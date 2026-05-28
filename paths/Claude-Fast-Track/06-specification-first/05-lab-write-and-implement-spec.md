# Lab 06 — Specification-first: napiši SPEC pa implementiraj GET /tasks

## Cilj
Na kraju ovog laba imaš kompletnu SPEC za GET /tasks u `docs/specs/get-tasks.md`, implementaciju koja je implementirana isključivo prema SPEC-u, i dokumentovanu spec drift detekciju gdje si uhvatio/la i revertovao/la neovlaštenu paginaciju.

## Preduvjeti
- Lab 01 završen: POST /tasks radi
- Lab 04 završen: CLAUDE.md, settings.json, rules postoje
- `.claude/rules/spec-before-code.md` postoji
- `docs/specs/` direktorijum postoji

## Kontekst
U Lab 02 si implementirao/la GET /tasks bez formalne SPEC procedure. Ovaj lab te tjera da prođeš kroz kompletni specification-first ciklus: napiši SPEC → odobri → implementiraj → provjeri drift. Namjerni drift (paginacija) je tu da te nauči kako detektovati kad Claude doda nešto što nije u SPEC-u.

## Koraci

### Korak 1 — Briši ili rename GET /tasks implementaciju

Ako je GET /tasks već implementiran, moraš ga "resetovati" da vježbaš clean slate:

```bash
# Provjeri sta postoji
grep -n "GET /tasks\|GetTasks\|List()" tasks/handler.go tasks/store.go
```

Za potrebe ovog laba, kloniraj get-tasks handler u novu funkciju s drugačijim imenom, pa obriši original — ili napravi novi branch:

```bash
git checkout -b lab06-spec-first
```

Ako GET /tasks već postoji i radi, samo nastavi s Korakom 2 (SPEC-om) — ovaj lab te uči procesu, ne insistira na brisanju radnog koda.

---

### Korak 2 — Napiši kompletnu SPEC za GET /tasks

Napravi `docs/specs/get-tasks.md`. Pročitaj svaki section i popuni ga PAŽLJIVO:

```markdown
# SPEC: get-tasks

## Problem
API korisnici ne mogu dohvatiti kreirana zadatke. Tasks kreirani via POST /tasks
nisu dostupni nakon kreiranja, što čini API nepotpunim za task management workflow.

## Goal
GET /tasks vraća sve taskove pohranjene u memoriji, u redoslijedu kreiranja
(najstariji prvo), svaki s trenutnim completion statusom.

## Out of scope
- Filtriranje po done/undone statusu
- Paginacija (ne u ovoj fazi)
- Sortiranje po polju osim creation time
- Autentikacija
- Search ili query parametri

## Constraint
- Stdlib only — bez external router packages
- store.List() mora vraćati non-nil empty slice (make([]Task, 0)) — nil serializes to null
- Nema query parametara — endpoint ne prima nikakve params u ovoj fazi

## NFR
- Latency: p99 < 50ms za do 100 taskova u memoriji (hypothesis — nije izmjereno)
- GET /tasks bez taskova vraća 200 + [] (ne 404, ne null)

## Boundary / ownership
- handler package: owns HTTP response formatting, route registration
- store package: owns task retrieval, returns []Task in creation order
- main.go: route registration only

## Acceptance
- [ ] AC-01: GET /tasks bez taskova vraća HTTP 200 i tijelo `[]`
- [ ] AC-02: GET /tasks nakon kreiranja 2 taska vraća HTTP 200 i JSON niz dužine 2
- [ ] AC-03: Taskovi u response su u redoslijedu kreiranja (prvi kreiran = index 0)
- [ ] AC-04: Svaki task objekt sadrži: id (string), title (string), completed (bool), created_at (string)
- [ ] AC-05: completed polje je false za taskove koji nisu završeni
- [ ] AC-06: Response Content-Type header je application/json
- [ ] AC-07: GET /tasks ne prima niti ne obrađuje nikakve query parametre

## Implementation strategy
1. Dodaj List() metodu u tasks/store.go — vraća []Task u insertion order
2. Dodaj GetTasks handler u tasks/handler.go — poziva store.List(), serializes JSON
3. Registruj GET /tasks rutu u main.go

## Tradeoff
Option A: Vraćaj bare array [{"id":"..."}]
Pros: jednostavnije, REST konvencija za collection endpoints
Cons: teže dodati top-level metadata (count, pagination) kasnije

Option B: Vraćaj object wrapper {"tasks":[...], "count":N}
Pros: lakše dodati metadata
Cons: klijenti moraju unwrap, paginacija je out-of-scope za sada

Decision: Option A — paginacija je eksplicitno out-of-scope, wrapper dodaje complexity bez koristi.

## Risk
- nil vs empty slice: json.Marshal(nil) = null u JSON-u — mora biti make([]Task, 0)
- Redoslijed: Go slice insert order je stabilan, ali mutex lock pattern mora biti ispravan

## Rollback
Revertovati GetTasks handler i GET ruta registraciju. store.List() je additive, može ostati.
```

**Uradi ovo:**
Provjeri svaki acceptance criterion. Za svaki, napiši sebi curl komandu za verifikaciju. Ako ne možeš, criterion nije binary — prepiši.

---

### Korak 3 — Self-audit SPEC-a

Prije implementacije, audituraj vlastiti SPEC:

**Problem section:**
- Je li jedna rečenica? Opisuje li šta je broken i zašto je bitno sada?

**Goal section:**
- Je li mjerljiv? Možeš li ga verificirati curl-om?

**Out of scope:**
- Je li paginacija eksplicitno navedena? (Ključno za ovaj lab)
- Je li autentikacija navedena?

**Constraint section:**
- Sadrži li "stdlib only"?
- Sadrži li "non-nil empty slice" constraint?

**Acceptance:**
- Ima li ≥5 criteria?
- Je li svaki binary (pass/fail bez interpretacije)?
- AC-07 (no query parameters) — je li ovdje? Ovo je važno za drift detection.

**Tradeoff:**
- Ima li ≥2 opcije?
- Je li odluka eksplicitna s rationale-om?

---

### Korak 4 — Implementiraj isključivo prema SPEC-u

Otvori Claude sesiju:

```bash
claude
```

Pošalji:

```
Read CLAUDE.md and docs/specs/get-tasks.md.

Implement GET /tasks endpoint based ONLY on docs/specs/get-tasks.md.

Rules:
- Implement exactly what the SPEC acceptance criteria require
- Do not add any behavior not described in the SPEC
- Do not add pagination
- Do not add filtering  
- Do not add query parameters
- AC-07 explicitly states: no query parameters

Files to modify:
- tasks/store.go (add List() method)
- tasks/handler.go (add GetTasks handler)
- main.go (register GET /tasks route)

After implementation, run: go build ./...
```

---

### Korak 5 — Induciraj namjerni spec drift

Ovo je namjerna vježba. Pošalji ovaj prompt koji uzrokuje drift:

```
Add optional pagination to GET /tasks:
- Accept query params: page (default 1) and limit (default 10)
- Return only tasks for the requested page
This will make the API more production-ready.
```

Claude će vjerovatno implementirati paginaciju jer se čini korisnom.

Prihvati ovu implementaciju (ne reverta je odmah) i nastavi na drift detekciju.

---

### Korak 6 — Detektuj drift

Provjeri šta je Claude dodao:

```bash
git diff tasks/handler.go | grep -A5 -B5 "page\|limit\|pagination"
```

Sada provjeri: je li paginacija u SPEC-u?

```bash
grep -i "pagination\|page\|limit" docs/specs/get-tasks.md
```

Output treba biti prazan ili referencirati "Out of scope" sekciju gdje je paginacija eksplicitno zabranjena.

Klasifikuj drift:
- **Out of scope** section kaže paginacija nije u scopeu
- **AC-07** kaže nema query parametara
- Ovo je jasno spec violation — SPEC je correct, kod ima drift

Dokumentuj u `docs/decisions/`:

```bash
mkdir -p docs/decisions
```

Napravi `docs/decisions/drift-001-pagination.md`:

```markdown
# Drift 001: Pagination added outside SPEC scope

## Detection date
[datum]

## What drifted
Pagination (page/limit query params) was added to GET /tasks handler.
This behavior was NOT in docs/specs/get-tasks.md.

## SPEC evidence
- Out of scope: "Paginacija (ne u ovoj fazi)"
- AC-07: "GET /tasks ne prima niti ne obrađuje nikakve query parametre"

## Classification
SPEC is correct, code has drifted.
Severity: Medium (excess behavior not in SPEC but not harmful)

## Decision
REVERT — pagination is explicitly out of scope per SPEC.
It will be considered in a future phase with its own SPEC.

## Action taken
Reverted handler to match SPEC acceptance criteria.
```

---

### Korak 7 — Revertuj drift

```bash
# Vidi difove
git diff tasks/handler.go

# Revertuj handler na zadnji clean state
git checkout tasks/handler.go

# Ili, ako je commitovano:
git log --oneline -5
# git revert <commit-hash-koji-je-dodao-paginaciju>
```

Provjeri da paginacija nije u kodu:

```bash
grep -i "page\|limit\|pagination" tasks/handler.go
# Ocekivano: nema output-a
```

---

### Korak 8 — Verificiraj svih 7 acceptance criteria

Pokreni server:

```bash
go run main.go
```

Verificiraj svaki AC:

```bash
# AC-01: prazan store vraca []
curl -s http://localhost:8080/tasks
# Ocekivano: []

curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/tasks
# Ocekivano: 200

# Kreiraj 2 taska za ostale testove
curl -s -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"first task"}'

curl -s -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"second task"}'

# AC-02: duzina 2
curl -s http://localhost:8080/tasks | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"
# Ocekivano: 2

# AC-03: redoslijed kreiranja
curl -s http://localhost:8080/tasks | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['title'])"
# Ocekivano: first task

# AC-04: sva polja prisutna
curl -s http://localhost:8080/tasks | python3 -c "import sys,json; d=json.load(sys.stdin); print(sorted(d[0].keys()))"
# Ocekivano: ['completed', 'created_at', 'id', 'title'] ili slicno

# AC-05: completed je false
curl -s http://localhost:8080/tasks | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['completed'])"
# Ocekivano: False

# AC-06: Content-Type
curl -sI http://localhost:8080/tasks | grep -i content-type
# Ocekivano: application/json

# AC-07: query params se ignorisu (ne smiju utjecati na rezultat)
curl -s "http://localhost:8080/tasks?page=1&limit=1" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"
# Ocekivano: 2 (query params se ignorisu, vraca sve taskove)
```

---

### Korak 9 — Commituj sve

```bash
git add tasks/handler.go tasks/store.go main.go docs/specs/get-tasks.md docs/decisions/
git commit -m "feat: GET /tasks with spec-first discipline + drift detection doc"
```

## Verifikacija

- [ ] `docs/specs/get-tasks.md` postoji s popunjenim svim sekcijama
- [ ] SPEC ima ≥7 binary acceptance criteria
- [ ] Out of scope sekcija eksplicitno navodi paginaciju
- [ ] AC-07 zabranjuje query parametre
- [ ] Implementacija prolazi svih 7 ACs
- [ ] `docs/decisions/drift-001-pagination.md` dokumentuje detektovani drift
- [ ] Paginacija je revertovana — nema `page/limit` u kodu
- [ ] `go test ./...` prolazi

## Šta si naučio

- **SPEC on disk** je jedini artefakt koji preživljava session close, /compact i multi-agent runs — SPEC u chatu je ephemeral
- **Out of scope sekcija** sprečava scope creep koji je izgledao "korisno" — paginacija je dobar primjer: Claude je "poboljšao" API ali prekršio contract
- **Drift detekcija** je rutinska provjera, ne iznimna situacija — uvijek check after execute
- **Dokumentovati drift** je jednako važno kao i revertovati ga — `docs/decisions/` je permanent record
- **Minimum 5 acceptance criteria** pokriva: happy path, error case, boundary case, structural case, behavioral case — manje od 5 obično znači da nešto nedostaje
