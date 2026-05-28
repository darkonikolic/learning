# Lab 03 — Prompt layering: PATCH /tasks/:id/complete

## Cilj
Na kraju ovog laba imaš implementiran PATCH /tasks/:id/complete endpoint koristeći layered context strategiju, i možeš demonstrirati razliku između vague, grounded i grounded+constraints prompta.

## Preduvjeti
- Lab 01 završen: POST /tasks endpoint radi
- Lab 02 završen: GET /tasks endpoint radi
- CLAUDE.md postoji s ispravnim constraints
- `docs/plans/` direktorijum postoji

## Kontekst
Do sada si implementirao/la endpointe bez formalne spec dokumentacije. Ovaj lab uvodi layered context: svaki prompt mora biti groundovan u konkretan fajl na disku, ne u chat memory. Ovo je priprema za Modul 06 (Specification-First) — uči te naviku referenciranja fajlova umjesto opisivanja iz sjećanja.

## Koraci

### Korak 1 — Napiši SPEC za complete-task

Napravi direktorijum i SPEC fajl:

```bash
mkdir -p docs/specs
```

Napravi `docs/specs/complete-task.md`:

```markdown
# SPEC: complete-task

## Problem
API korisnici ne mogu označiti task kao završen. Tasks kreiran via POST /tasks
nemaju mehanizam za update completion statusa.

## Goal
PATCH /tasks/:id/complete postavlja done polje na true i vraća ažurirani task.
Operacija je idempotentna — višestruki pozivi vraćaju isti 200 odgovor.

## Out of scope
- Un-completing task (vraćanje done na false)
- Bulk complete operacije
- Autentikacija
- Partial updates (samo completion je podržan, ne i title update)

## Constraint
- Stdlib only — bez external packages
- Operacija mora biti idempotentna
- Mora se promijeniti SAMO done polje — title i created_at ostaju nepromijenjeni
- Ne smije utjecati na ostale taskove

## Acceptance
- [ ] PATCH /tasks/:id/complete s validnim id-em vraća HTTP 200
- [ ] Response body za validan request sadrži ažurirani task s done=true
- [ ] Response body uključuje id, title, done, created_at polja
- [ ] title polje u response je nepromijenjeno od originalnog POST-a
- [ ] PATCH na already-completed task vraća HTTP 200 (idempotentno)
- [ ] PATCH s nepostojećim id-em vraća HTTP 404
- [ ] 404 response body je {"error":"task not found"}

## Rollback
Revertovati handler Complete() metodu i registraciju rute.
store.CompleteTask() ostaje — additive change, bez breaking efekta.
```

**Uradi ovo:**
Pročitaj svaki acceptance criterion. Za svaki, napiši curl komandu kojom bi ga verificirao/la. Ako ne možeš napisati curl, criterion nije dovoljno konkretan — prepiši ga.

---

### Korak 2 — Razumij instruction hierarchy

Prije otvaranja Claude sesije, razumi slojeve koji će biti aktivni:

| Layer | Fajl | Sadržaj |
|-------|------|---------|
| Layer 3 — Project | CLAUDE.md | Stack, constraints, conventions |
| Layer 2 — Spec/Plan | docs/specs/complete-task.md | Acceptance criteria, constraints |
| Layer 1 — Per-message | Tvoj prompt | Konkretna instrukcija za ovaj turn |

Svaki viši layer (niži broj) ima veću authority. Per-message constraints mogu sužavati scope, ali ne mogu contradictovati project constraints (npr. ne možeš reći "use gin" jer CLAUDE.md kaže stdlib only).

---

### Korak 3 — Prompt vježba: 3 načina isti zahtjev

Otvori Claude sesiju:

```bash
claude
```

Pošalji setup prompt:

```
Read CLAUDE.md and docs/specs/complete-task.md before anything else.
Confirm you understand the project constraints and the spec for complete-task.
```

Sada ćemo demonstrirati tri prompta za isti zahtjev. **Pošalji svaki redom, ali NEMOJ odobriti nikakve izmjene fajlova — koristimo plan mode.**

**Prompt 1 — Vague:**

```
/plan implement complete task feature
```

Pogledaj šta Claude predlaže. Zabilježi: koliko je plan specifičan? Koja pitanja ostaju otvorena?

**Prompt 2 — Grounded u fajl:**

```
/plan Implement PATCH /tasks/:id/complete per docs/specs/complete-task.md.
No implementation yet — just the plan.
```

Usporedi s Promptom 1. Da li je plan konkretniji? Da li se Claude referira na specifične acceptance criteria?

**Prompt 3 — Grounded + constraints:**

```
/plan Implement PATCH /tasks/:id/complete.

Context files:
- CLAUDE.md (project constraints)
- docs/specs/complete-task.md (acceptance criteria and constraints)

Plan requirements:
- Each plan step must name the specific file (tasks/store.go or tasks/handler.go or main.go)
- Store CompleteTask() must come before handler implementation (dependency order)
- Plan must include idempotency handling (already-complete task must return 200)
- No external packages — stdlib only
- Write plan to docs/plans/03-complete-task-plan.md

No implementation yet.
```

**Uradi ovo:**
Pregledaj sva tri plana. Koji je najprecizniji? Koji bi ti dao najbolju osnovu za implementaciju? Odgovori sebi na ovo pitanje PRIJE nego nastaviš.

---

### Korak 4 — Provjeri plan iz Prompta 3

Plan se treba nalaziti u `docs/plans/03-complete-task-plan.md`. Otvori ga i provjeri:

- Je li store korak PRIJE handler koraka?
- Ima li svaki korak specifičan fajl?
- Je li idempotency handling u planu?
- Nema li external packages?

Ako nešto nedostaje, pošalji targeted revision:

```
Revise docs/plans/03-complete-task-plan.md:
- Step for store.CompleteTask must come before handler step
- Add explicit idempotency requirement: if task is already complete, return 200 (not 409)
- Each step must name the specific file being modified
```

---

### Korak 5 — Implementiraj s layered context

Sada implementiraj, ali s eksplicitnim referenciranjem fajlova:

```
Execute the plan from docs/plans/03-complete-task-plan.md.

Context for this implementation:
- Project constraints: CLAUDE.md
- Acceptance contract: docs/specs/complete-task.md — every acceptance item must be satisfied
- Plan: docs/plans/03-complete-task-plan.md

Execute all steps. Do not add behavior not in the spec.
After implementation, run: go build ./...
```

**Očekivani output:**
Claude implementira CompleteTask() u store.go, dodaje handler u handler.go, registrira rutu u main.go. `go build ./...` mora proći.

**Grounding provjera:**
Ako Claude u bilo kom trenutku kaže nešto bez citiranja izvora ("the handler probably should..."), zaustavi ga:

```
Before making that change, cite the specific acceptance criterion from docs/specs/complete-task.md 
that requires it. If it's not in the spec, don't add it.
```

---

### Korak 6 — Verificiraj sve acceptance criteria

Pokreni server:

```bash
go run main.go
```

Za svaki acceptance criterion iz SPEC-a, pokreni verificirajuću komandu:

```bash
# Kreiraj task za testiranje
ID=$(curl -s -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"learn prompt layering"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Task ID: $ID"

# Criterion 1: 200 na validan id
curl -s -o /dev/null -w "%{http_code}\n" \
  -X PATCH http://localhost:8080/tasks/$ID/complete
# Ocekivano: 200

# Criterion 2: done=true u response
curl -s -X PATCH http://localhost:8080/tasks/$ID/complete | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['done'])"
# Ocekivano: True

# Criterion 3: sva polja su prisutna
curl -s -X PATCH http://localhost:8080/tasks/$ID/complete | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(sorted(d.keys()))"
# Ocekivano: ['completed', 'created_at', 'id', 'title'] (ili slicno, ovisno o implementaciji)

# Criterion 4: title nepromijenjen
curl -s -X PATCH http://localhost:8080/tasks/$ID/complete | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['title'])"
# Ocekivano: learn prompt layering

# Criterion 5: idempotentno (drugi PATCH vraca 200)
curl -s -o /dev/null -w "%{http_code}\n" \
  -X PATCH http://localhost:8080/tasks/$ID/complete
# Ocekivano: 200

# Criterion 6: 404 za nepostojeci id
curl -s -o /dev/null -w "%{http_code}\n" \
  -X PATCH http://localhost:8080/tasks/nonexistent-id/complete
# Ocekivano: 404

# Criterion 7: 404 body
curl -s -X PATCH http://localhost:8080/tasks/nonexistent-id/complete | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['error'])"
# Ocekivano: task not found
```

Za svaki FAIL, dokumentiraj failure class i napiši targeted correction:

```
Flaw: [opis greske]
Location: [fajl:funkcija]
Expected: [ocekivano ponasanje]
Do not change: [sta ne smijes mijenjati]
```

---

### Korak 7 — Dokumentiraj zašto je Prompt 3 bio najefikasniji

Napravi kratak fajl s tvojim zaključcima:

```bash
mkdir -p docs/decisions
```

Napravi `docs/decisions/prompt-layering-observations.md`:

```markdown
# Prompt layering observations

## Prompt 1 (vague): "implement complete task feature"
Problem: [napiši što je bilo loše — šta je Claude pretpostavio?]

## Prompt 2 (grounded): reference na spec fajl
Poboljšanje: [šta je bolje bilo u planu?]
Ostaje problem: [šta još nije bilo specificno?]

## Prompt 3 (grounded + constraints): reference + explicit requirements  
Zašto je bio najefikasniji: [napiši u 2-3 rečenice]
Ključni elementi koji su napravili razliku: [nabrojaj 3-4 elementa]
```

---

### Korak 8 — Commituj

```bash
git add tasks/handler.go tasks/store.go main.go docs/
git commit -m "feat: implement PATCH /tasks/:id/complete with layered context discipline"
```

## Verifikacija

- [ ] `curl -X PATCH http://localhost:8080/tasks/$ID/complete` vraća 200 s done=true
- [ ] Drugi PATCH na isti ID vraća 200 (idempotentno)
- [ ] `curl -X PATCH http://localhost:8080/tasks/nonexistent/complete` vraća 404 s `{"error":"task not found"}`
- [ ] title polje je nepromijenjeno u response-u
- [ ] `docs/specs/complete-task.md` postoji i sadrži sve acceptance criteria
- [ ] `docs/plans/03-complete-task-plan.md` postoji s dependency-aware redoslijedom
- [ ] `docs/decisions/prompt-layering-observations.md` postoji s tvojim zaključcima
- [ ] Možeš objasniti zašto je Prompt 3 bio najefikasniji

## Šta si naučio

- **Layered context** znači da svaki prompt referencira konkretan fajl — CLAUDE.md, SPEC, plan — ne chat memory koji će biti izgubljen nakon /compact
- **Grounding principle**: svaki zahtjev za implementacijom treba citirati specifičan fajl i sekciju, ne opisivati iz sjećanja
- **Per-message constraints** mogu sužavati scope (step-by-step) ali ne mogu contradictovati project constraints (stdlib-only je hard rule)
- **Specifičnost prompta** direktno utječe na specifičnost plana — vague prompt → vague plan → surprises during execution
- **SPEC na disku** je jedini artefakt koji preživljava /compact, session close i multi-agent kontekst — chat nije contracts
