# Lab 07 — Audit: SPEC vs implementacija

## Cilj
Na kraju ovog laba imaš kompletni audit report koji mapira svaki SPEC acceptance criterion na implementaciju, pronašao/la si barem jedan drift, dokumentovao/la ga u `docs/decisions/`, i donio/la eksplicitnu odluku: acceptiraj ili revertuj.

## Preduvjeti
- Lab 06 završen: `docs/specs/get-tasks.md` postoji s acceptance criteria
- Lab 03 završen: `docs/specs/complete-task.md` postoji
- Svi 3 endpointa implementirani i kompajliraju
- `go build ./...` prolazi

## Kontekst
Kod koji je Claude napisao uvijek ima nešto što nije u SPEC-u. Ne zato što Claude griješi — nego zato što Claude "popunjava praznine" koje smatra korisnim. Ovaj lab te uči kako sistematski pronaći ove razlike. Audit je rutinska provjera, ne istraga — uvijek raditi after execute.

## Koraci

### Korak 1 — Napravi audit prompt

Otvori Claude sesiju:

```bash
claude
```

Pošalji setup:

```
Read CLAUDE.md, docs/specs/get-tasks.md, and docs/specs/complete-task.md.
Read tasks/handler.go and tasks/store.go.

You are now performing a spec-vs-implementation audit.
Do not modify any files.
```

Sada pošalji audit prompt:

```
Perform a complete spec-vs-implementation audit.

For docs/specs/get-tasks.md:
1. List every acceptance criterion (AC-01 through AC-07)
2. For each AC, find the corresponding code in tasks/handler.go or tasks/store.go
3. Mark: IMPLEMENTED / NOT IMPLEMENTED / PARTIALLY IMPLEMENTED
4. Find any behavior in the implementation that is NOT described in the SPEC

For docs/specs/complete-task.md:
1. List every acceptance criterion
2. For each AC, find the corresponding code
3. Mark: IMPLEMENTED / NOT IMPLEMENTED / PARTIALLY IMPLEMENTED
4. Find any behavior in the implementation that is NOT described in the SPEC

Output format:
## GET /tasks Audit
| AC | Criterion | Status | Code location |
|----|-----------|--------|---------------|
...
### Excess behavior (not in SPEC):
...

## PATCH /tasks/:id/complete Audit
[same format]

## Summary
Total ACs: X
Implemented: X
Not implemented: X
Excess behavior items: X
```

**Očekivani output:**
Claude treba producirati detaljni audit report. Barem jedan excess behavior item UVIJEK postoji — Claude skoro uvijek doda nešto što nije u SPEC-u.

---

### Korak 2 — Sačuvaj audit report

```bash
mkdir -p docs/audit
```

U Claude sesiji:

```
Write the complete audit report to docs/audit/spec-audit-[datum].md
Use today's date in the filename.
```

Provjeri da fajl postoji:

```bash
ls docs/audit/
```

---

### Korak 3 — Identifikuj drift kandidate

Pročitaj audit report. Za svaki excess behavior item, postavljaj pitanje:

**"Je li ovo intentionally added ili accidental drift?"**

Korisna heuristika:
- Ako je u SPEC Out of scope sekciji → ovo je drift
- Ako SPEC uopće ne pominje ovo ponašanje → ovo je "excess behavior"
- Ako ACC criterion kaže nešto drugačije od implementacije → ovo je klasičan drift

Tipični excess behavior primjeri koji se pojavljuju u task-api:

| Čest excess behavior | Zašto Claude ga dodaje |
|---------------------|----------------------|
| Extra response field (npr. `updated_at`) | "Sviđa mi se ideja" |
| Extra error case (npr. 422 za wrong content-type) | "Robusno je" |
| Query param koji se prihvata (npr. `?format=json`) | "Fleksibilno je" |
| Logging koji otkriva internals | "Korisno za debug" |

---

### Korak 4 — Verificiraj drift s konkretnim curl komandama

Za svaki excess behavior koji si identificovao/la, napisi verificirajuću komandu.

Primjer: ako je Claude dodao `updated_at` field koji nije u SPEC-u:

```bash
go run main.go &

# Verificiraj: ima li updated_at u GET /tasks response?
curl -s http://localhost:8080/tasks | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
if tasks:
    print('Fields in response:', sorted(tasks[0].keys()))
else:
    # Napravi task pa provjeri
    pass
"
```

Provjeri SPEC acceptance criterion AC-04:
```
AC-04: Svaki task objekt sadrži: id (string), title (string), completed (bool), created_at (string)
```

Ako response sadrži `updated_at` — SPEC kaže samo 4 polja. Ovo je drift.

---

### Korak 5 — Dokumentuj svaki drift

Za svaki pronađeni drift, napravi decision dokumentaciju:

```bash
mkdir -p docs/decisions
```

Format za svaki fajl `docs/decisions/drift-NNN-[ime].md`:

```markdown
# Drift NNN: [kratki opis]

## Detection date
[datum]

## Audit source
docs/audit/spec-audit-[datum].md

## What drifted
[Konkretni opis: koji fajl, koja funkcija, koje ponašanje]

## SPEC evidence
- [Navedi konkretni AC koji je prekršen ili koji nije pokriven]
- [Ili: Out of scope sekcija kaže ...]

## Classification
[ ] SPEC is correct, code has drifted → FIX CODE
[ ] Code is correct, SPEC is outdated → UPDATE SPEC  
[ ] Both wrong → REWRITE CRITERION

## Severity
[ ] Critical (security/data integrity)
[X] High (acceptance criterion fails)
[ ] Medium (excess behavior, not harmful)
[ ] Low (internal implementation differs from SPEC strategy)

## Decision
[ ] REVERT — remove excess behavior from code
[ ] ACCEPT — update SPEC to include this behavior (spec evolution)

## Rationale
[Zašto si donio/la ovu odluku?]

## Action taken
[Šta si konkretno uradio/la: revertovao kod, ažurirao SPEC, etc.]
```

---

### Korak 6 — Izvrši odluku: acceptiraj ili revertuj

Za svaki drift item, izvrši svoju odluku.

**Ako revertiraš:**

```
Remove the following excess behavior from tasks/handler.go:
[Paste specifičnog koda koji trebaš ukloniti]

Reason: This behavior is not in docs/specs/get-tasks.md.
AC-XX explicitly excludes it.

Do not change anything else.
Run go build ./... after change.
```

**Ako acceptiraš (spec evolution):**

```
Add the following to docs/specs/get-tasks.md under Acceptance:
- [ ] AC-XX: [novi criterion koji pokriva excess behavior]

Also update the Tradeoff section to note that this behavior was discovered
during implementation and accepted as spec evolution on [datum].

Do not change any production code.
```

Provjeri da si konzistentan/na:
- Ako acceptiraš behavior — SPEC mora biti ažuriran
- Ako revertiraš — kod mora biti ažuriran, SPEC ostaje

---

### Korak 7 — Re-run audit nakon korekcija

Nakon što si proveo/la sve odluke, pokreni kratak re-audit:

```
Perform a quick re-audit of tasks/handler.go and tasks/store.go against:
- docs/specs/get-tasks.md
- docs/specs/complete-task.md

Only check items that were marked as drift or excess behavior in the previous audit.
Confirm: is each item now resolved?
```

---

### Korak 8 — Commituj audit artefakte

```bash
git add docs/audit/ docs/decisions/ tasks/handler.go tasks/store.go docs/specs/
git commit -m "audit: spec-vs-implementation audit, document and resolve drift items"
```

## Verifikacija

- [ ] `docs/audit/spec-audit-[datum].md` postoji s kompletnim audit resultima
- [ ] Svaki AC ima status: IMPLEMENTED/NOT IMPLEMENTED/PARTIALLY
- [ ] Barem jedan drift item je identificiran (uvijek postoji)
- [ ] Svaki drift ima dokumentaciju u `docs/decisions/drift-NNN-*.md`
- [ ] Svaki drift ima eksplicitnu odluku: REVERT ili ACCEPT
- [ ] Odluke su izvršene (revertovani kod ili ažurirani SPEC)
- [ ] `go test ./...` prolazi nakon korekcija

## Šta si naučio

- **Audit je rutina, ne istraga** — svaki execute session treba završiti s spot-checkom ACs
- **Excess behavior nije automatski greška** — može biti dobra ideja koja je "preskočila" SPEC process
- **Tri drift cases**: code wrong → fix code; SPEC wrong → update SPEC; both wrong → rewrite criterion
- **Dokumentacija odluke** je jednako važna kao i sama odluka — u `docs/decisions/` je permanent record koji objašnjava ZA ŠTO je kod ovakav
- **Spec evolution** (deliberate change) i **spec drift** (accidental divergence) izgledaju isto — razlikuje ih process: evolution se dokumentuje, drift se pronalazi
