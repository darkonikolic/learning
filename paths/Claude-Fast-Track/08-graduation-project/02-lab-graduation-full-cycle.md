# Lab 08 — Graduation: kompletni feature cycle za PATCH /tasks/:id/complete

## Cilj
Na kraju ovog laba imaš PR-ready commit za PATCH /tasks/:id/complete endpoint, prošavši kompletni ciklus: SPEC → /plan → implementacija → audit → testovi → diff review → docs/state.md checkpoint. Sve bez gledanja u dokumentaciju mid-loop.

## Preduvjeti
- Lab 01 završen: POST /tasks radi
- Lab 02 završen: GET /tasks radi
- Lab 04 završen: CLAUDE.md, settings.json, rules konfiguracija postoji
- Lab 06 završen: SPEC authoring disciplina savladana
- Lab 07 završen: drift detection disciplina savladana
- `go build ./...` prolazi
- CLAUDE.md postoji s kompletnim constraints

## Kontekst
Ovo je capstone lab — nema hand-holdinga po koracima. Svaki korak ima jasni cilj i verifikacijsku provjeru, ali ti si u potpunosti zadužen/a za sve odluke. Ako nisi siguran/na u korak — ne gledaj documentaciju, nego razmisli kako si to riješio/la u prethodnim labovima. **Cilj je demonstrirati da možeš proći kompletni ciklus samostalno.**

## Format graduation-a

Svaki korak ima:
- **Cilj** — šta trebaš napraviti
- **Exit criteria** — binarna provjera da si završio/la korak
- **Ako zaglavi** — hint (ne rješenje)

---

## FAZA 1 — Napiši SPEC

### Cilj
Napiši `docs/specs/complete-task.md` koristeći kompletni SPEC template.

SPEC MORA sadržavati:
- Problem (jedna rečenica)
- Goal (mjerljiv outcome)
- Out of scope (barem 4 eksplicitne isključene stvari)
- Constraint (barem 3, sve binary)
- NFR
- Boundary / ownership
- Acceptance (≥7 criteria, sve binary, verificabilne curl-om)
- Implementation strategy
- Tradeoff (≥2 opcije, eksplicitna odluka)
- Risk
- Rollback

**Exit criteria:**
- [ ] `docs/specs/complete-task.md` postoji
- [ ] Sve sekcije su popunjene (nema [fill in])
- [ ] ≥7 acceptance criteria, svaki binary
- [ ] Za svaki AC možeš napisati curl komandu bez postavljanja pitanja

**Ako zaglavi:**
Poglavi Lab 06 Korak 2 za SPEC template, ili `06-specification-first/01-spec-template-and-acceptance.md`.

---

## FAZA 2 — /plan

### Cilj
Pokreni `/plan` koristeći SPEC kao jedini kontekst. Sačuvaj plan u `docs/plans/03-complete-task-plan.md`.

```
/plan PATCH /tasks/:id/complete — plan only, no implementation yet.
Read docs/specs/complete-task.md.
Write plan to docs/plans/03-complete-task-plan.md.
Each plan step must name a specific file.
Dependency order: store before handler.
```

Review plan. Za svaki task provjeri:
- Ime li specifičan fajl?
- Je li redoslijed ispravan (store → handler → main)?
- Je li idempotency handling eksplicitan?

**Exit criteria:**
- [ ] `docs/plans/03-complete-task-plan.md` postoji
- [ ] Svaki task ima specifičan fajl
- [ ] store.CompleteTask() korak je PRIJE handler koraka
- [ ] Nema external packages u planu

**Ako zaglavi:**
Lab 02 Korak 3 — kako reviewovati plan prije odobrenja.

---

## FAZA 3 — Implementiraj

### Cilj
Implementiraj prema planu. Koristi oba fajla kao context:

```
Implement PATCH /tasks/:id/complete.

Context:
- SPEC: docs/specs/complete-task.md (acceptance section is the contract)
- Plan: docs/plans/03-complete-task-plan.md (execute all tasks)

Rules:
- Do not add behavior not in the SPEC
- After implementation: run go build ./... and go test ./...
```

**Exit criteria:**
- [ ] `go build ./...` prolazi
- [ ] `go test ./...` prolazi
- [ ] Handler ne modifikuje nijedan field osim done

**Ako zaglavi:**
Lab 03 Korak 5 — implementacija s layered context.

---

## FAZA 4 — Audit SPEC vs implementacija

### Cilj
Provjeri je li implementacija u skladu sa SPEC-om. Pokreni audit prompt iz Lab 07:

```
Read docs/specs/complete-task.md and tasks/handler.go and tasks/store.go.
Perform a spec-vs-implementation audit.
For each acceptance criterion, find the corresponding code and mark: IMPLEMENTED / NOT IMPLEMENTED.
Also find any behavior in the implementation NOT described in the SPEC.
Write audit to docs/audit/complete-task-audit.md.
```

Za svaki pronađeni excess behavior, donesi odluku i dokumentiraj u `docs/decisions/`.

**Exit criteria:**
- [ ] `docs/audit/complete-task-audit.md` postoji
- [ ] Svaki AC ima status
- [ ] Svaki excess behavior item ima odluku (REVERT ili ACCEPT)
- [ ] Odluke su izvršene

**Ako zaglavi:**
Lab 07 Koraci 3-6.

---

## FAZA 5 — Napiši testove

### Cilj
Napiši testove za CompleteTask() koristeći AC-e iz SPEC-a kao jedini izvor:

```
Write tests for the PATCH /tasks/:id/complete endpoint.

Source of truth: docs/specs/complete-task.md acceptance criteria.
Each test must map to exactly one AC (comment in code: // AC-01).
Test file: tasks/handler_test.go or tasks/complete_test.go

Test coverage required:
- Each AC from docs/specs/complete-task.md gets one test
- Run go test ./... after writing tests
```

**Exit criteria:**
- [ ] Test fajl postoji
- [ ] Svaki test ima komentar koji mapira na AC (// AC-01: ...)
- [ ] `go test ./...` prolazi
- [ ] Coverage > 70% za complete-task handler

**Ako zaglavi:**
Lab 05 Korak 3 za store-tester agent pattern, ili `11-test-engineering/01-spec-backed-testing.md`.

---

## FAZA 6 — Diff review disciplina

### Cilj
Provjeri SVAKU promjenu u diff-u. Ne mergaj ništa što nisi pročitao/la.

```bash
git diff main...HEAD
```

Za svaki hunk u diff-u, postavi pitanje:

| Provjera | Da li prolazi? |
|----------|----------------|
| Je li ova promjena u planu? | |
| Mijenja li samo fajlove koji su u planu? | |
| Nema li rename koji nije planiran? | |
| Nema li refaktoring koji nije zahtjevan? | |
| Nema li external packages? | |

Ako nešto ne prolazi: identificiraj specifični hunk, revertuj ga, i dokumentuj zašto:

```bash
git diff --name-only HEAD~1
# ili
git show HEAD --stat
```

**Exit criteria:**
- [ ] Svaki izmijenjeni fajl je u planu
- [ ] Nema rename drifta
- [ ] Nema formatiranje-only izmjena
- [ ] Nema external packages u go.mod

**Ako zaglavi:**
`12-diff-refactor/03-diff-review-discipline.md`.

---

## FAZA 7 — Napiši docs/state.md checkpoint

### Cilj
Napiši checkpoint packet koji opisuje trenutno stanje projekta:

Napravi ili ažuriraj `docs/state.md`:

```markdown
# Project State

## Last updated
[datum]

## Completed phases
- Phase 1: POST /tasks — COMPLETE (verified [datum])
- Phase 2: GET /tasks — COMPLETE (verified [datum])  
- Phase 3: PATCH /tasks/:id/complete — COMPLETE (verified [datum])

## Verified acceptance criteria

### POST /tasks (docs/specs/post-tasks.md)
[Navedi svaki AC s PASS/FAIL]

### GET /tasks (docs/specs/get-tasks.md)
[Navedi svaki AC s PASS/FAIL]

### PATCH /tasks/:id/complete (docs/specs/complete-task.md)
[Navedi svaki AC s PASS/FAIL]

## Open decisions
[Navedi sve otvorene odluke koje nisu u fajlovima]

## Known gotchas discovered during this phase
[Navedi sve što si naučio/la što nije u CLAUDE.md]

## Next phase
[Šta dolazi sljedeće — Docker, MySQL, Crawler]
```

**Exit criteria:**
- [ ] `docs/state.md` postoji s popunjenim svim sekcijama
- [ ] Svaki AC za Phase 3 ima PASS/FAIL status s datumom
- [ ] Open decisions su dokumentovane
- [ ] Next phase je definisan

---

## ZAVRŠNA VERIFIKACIJA — End-to-end smoke test

Ovo je zadnja provjera prije final commit-a. Pokreni cijeli flow:

```bash
go run main.go &
SERVER_PID=$!

# Kreiraj task
ID=$(curl -s -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"graduation task"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Created task ID: $ID"

# Verificiraj u listi
echo "--- GET /tasks ---"
curl -s http://localhost:8080/tasks | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
print(f'Tasks count: {len(tasks)}')
print(f'First task title: {tasks[0][\"title\"]}')
print(f'First task completed: {tasks[0][\"completed\"]}')
"

# Complete task
echo "--- PATCH /tasks/$ID/complete ---"
curl -s -X PATCH http://localhost:8080/tasks/$ID/complete | python3 -c "
import sys, json
task = json.load(sys.stdin)
print(f'done: {task[\"done\"] if \"done\" in task else task.get(\"completed\")}')
print(f'title unchanged: {task[\"title\"]}')
"

# Idempotency check
echo "--- Idempotency check ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH http://localhost:8080/tasks/$ID/complete)
echo "Second PATCH status: $STATUS"

# 404 check
echo "--- 404 check ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH http://localhost:8080/tasks/nonexistent/complete)
echo "Unknown ID status: $STATUS"

# Cleanup
kill $SERVER_PID 2>/dev/null
```

---

## Graduation commit

```bash
git add tasks/ docs/ main.go
git commit -m "feat: PATCH /tasks/:id/complete — graduation cycle complete

- SPEC: docs/specs/complete-task.md (7 acceptance criteria)
- Plan: docs/plans/03-complete-task-plan.md  
- Audit: docs/audit/complete-task-audit.md
- Tests: mapped to AC criteria
- State: docs/state.md updated

Acceptance criteria verified:
- 200 on valid id: PASS
- done=true in response: PASS  
- idempotent second PATCH: PASS
- 404 on unknown id: PASS
- title unchanged: PASS
- all fields present: PASS
- error body correct: PASS"
```

## Graduation checklist

Ovo je tvoja graduation provjera. Svaki item mora biti PASS:

### SPEC disciplina
- [ ] SPEC postoji na disku PRIJE implementacije
- [ ] SPEC ima ≥7 binary acceptance criteria
- [ ] Tradeoff sekcija ima ≥2 opcije s eksplicitnom odlukom
- [ ] Out of scope sekcija ima ≥4 eksplicitnih isključenja

### Plan disciplina
- [ ] /plan je pokrenut s SPEC-om kao context
- [ ] Plan je reviewovan i editovan PRIJE execute
- [ ] Dependency order je ispravan (store before handler)

### Implementacija
- [ ] `go build ./...` prolazi
- [ ] `go test ./...` prolazi
- [ ] Handler ne modifikuje nijedan field osim done

### Audit
- [ ] Svih 7 ACs su verificirani s konkretnim curl komandama
- [ ] Barem jedan excess behavior item je identificiran i odlučen
- [ ] Drift dokumentacija postoji u `docs/decisions/`

### Testovi
- [ ] Svaki test mapira na AC (komentar u kodu)
- [ ] Coverage > 70%

### Diff review
- [ ] Svaki izmijenjeni fajl je u planu
- [ ] Nema neovlaštenih rename-a ili refaktoring-a

### State
- [ ] `docs/state.md` postoji s Phase 3 PASS statusom
- [ ] End-to-end smoke test prolazi

## Šta si naučio

- **Kompletni cycle** je mjerljiv: SPEC → plan → impl → audit → tests → review → state — bez preskakanja koraka
- **"PR-ready"** znači: svaka provjera prolazi, svaka odluka je dokumentovana, diff je čist
- **Bez dokumentacije mid-loop** demonstrira da si internalizovao/la workflow, ne samo naučio/la slijediti upute
- **docs/state.md** je checkpoint koji omogućava resume bez regression — nova sesija čita state.md i zna točno gdje je projekt
- **Graduation** nije "sve radi" — graduation je "sve radi I sve je dokumentovano I sve je auditable"
