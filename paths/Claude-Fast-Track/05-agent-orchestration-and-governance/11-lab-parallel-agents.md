# Lab 05 — Parallel agents: tester + reviewer s HITL checkpointom

## Cilj
Na kraju ovog laba imaš dva paralelna agenta koji su radili na task-api: tester je napisao testove za store.go, reviewer je reviewovao handler.go — uz HITL checkpoint između njih i verificirano da reviewer nema write permissions.

## Preduvjeti
- Lab 04 završen: kompletna Claude konfiguracija, svi 3 endpointa rade
- `.claude/agents/code-reviewer.md` postoji (iz Lab 04)
- `go build ./...` prolazi
- `go test ./...` prolazi (barem osnvni testovi)

## Kontekst
Do sada si radio/la sa jednom Claude sesijom. Ovaj lab uvodi multi-agent orchestration: orchestrator agent koordinira dva worker agenta koji rade paralelno (conceptually — u Claude Code pokrećeš ih sekvencijalno ali ih dizajniraš kao da rade paralelno). HITL checkpoint između faza znači da ti odobriš output jednog agenta PRIJE nego počne drugi.

## Koraci

### Korak 1 — Pripremi agent definition fajlove

Napravi tester agenta:

```bash
mkdir -p .claude/agents
```

Napravi `.claude/agents/store-tester.md`:

```markdown
---
name: store-tester
description: Write unit tests for store.go based on SPEC acceptance criteria. Has read/write access to test files only.
model: claude-sonnet-4-6
---

# Store Tester Agent

## Role
Ti si test-writer za task-api store layer.
Pišeš unit testove za tasks/store.go koristeći acceptance criteria iz docs/specs/ kao izvor istine.

## Allowed tools
- Read (čitanje svih fajlova)
- Write/Edit (SAMO za *_test.go fajlove)
- Bash (go test ./... samo)

## Forbidden
- Edit/Write production code (tasks/store.go, tasks/handler.go, main.go)

## Test requirements

Svaki test mora:
1. Imati naziv koji se tracira na acceptance criterion (format: TestStore_<Behaviour>_<Condition>)
2. Imati komentar koji mapira na AC: // AC-01: store.List() returns non-nil empty slice
3. Koristiti tylko stdlib testing package — ne testify niti druge library-e
4. Koristiti httptest za handler testove

## Output
Napiši testove u tasks/store_test.go.
Svaki test treba imati komentar koji mapira na AC iz docs/specs/.
Nakon pisanja, pokreni go test ./... i report rezultate.
```

---

### Korak 2 — Definiraj orchestrator plan

Napravi orchestration plan na disku:

```bash
mkdir -p docs/plans
```

Napravi `docs/plans/05-parallel-agents-plan.md`:

```markdown
# Plan: Parallel Agents Lab

## Cilj
Pisanje testova (store-tester) i review koda (code-reviewer) kao paralelni agenti.

## Wave 1 — Tester agent (nema prerequisites)
Agent: store-tester
Task: Write unit tests for tasks/store.go
Files it can write: tasks/store_test.go
SPEC reference: docs/specs/ (svi SPEC fajlovi za acceptance criteria)

Acceptance za Wave 1:
- [ ] tasks/store_test.go postoji
- [ ] Svaki test ima AC mapping komentar
- [ ] go test ./... prolazi

## HITL Checkpoint — MORA biti odobren prije Wave 2
[ ] Pročitao/la sam testove
[ ] Svaki test je mapiran na AC koji postoji
[ ] Testovi su koristili stdlib testing, ne vanjske library-e
[ ] go test ./... prolazi
[ ] ODOBRAVAM nastavak

## Wave 2 — Reviewer agent (depends on Wave 1 completion + HITL approval)
Agent: code-reviewer
Task: Review tasks/handler.go
Files it can write: NIKAKVE (read-only agent)
Output: docs/review/handler-review.md

Acceptance za Wave 2:
- [ ] docs/review/handler-review.md postoji
- [ ] Review je popunjen s PASS/FAIL za svaki checklist item
- [ ] Reviewer NIJE izmijenio nijedan production fajl

## Dependency
Wave 2 počinje SAMO kada Wave 1 prolazi HITL checkpoint.
```

---

### Korak 3 — Pokreni Wave 1: store-tester agent

Otvori Claude sesiju:

```bash
claude
```

Pošalji orchestrator instrukciju:

```
You are the orchestrator for a parallel agents run.

Wave 1: Deploy the store-tester agent.

Agent definition: .claude/agents/store-tester.md
Task: Write unit tests for tasks/store.go

Context to provide to the agent:
- Read tasks/store.go to understand the current implementation
- Read docs/specs/ to find acceptance criteria to map tests against
- Write tests to tasks/store_test.go
- Each test must have a comment mapping to an AC: // AC-01: [criterion text]
- Use only stdlib testing package
- After writing, run: go test ./...

Execute Wave 1 now. Do not start Wave 2 until I explicitly approve.
```

**Očekivani output:**
Claude (kao orchestrator) će delegirati store-tester agentu. Agent čita store.go i specs/, piše testove, i pokreće `go test ./...`.

---

### Korak 4 — HITL Checkpoint: provjeri testove

OVO JE TVOJA ODGOVORNOST. Orchestrator se zaustavio i čeka tvoje odobrenje.

Provjeri svaki test:

```bash
cat tasks/store_test.go
```

Za svaki test, provjeri:
1. Ima li komentar koji mapira na AC?
2. Je li naziv testa describovan dovoljno (`TestStore_List_ReturnsEmptySlice` je dobar, `TestList` nije)?
3. Je li test koristio stdlib testing (ne testify)?
4. Testira li test ono što kaže AC?

Pokreni testove:

```bash
go test ./...
```

**Ako testovi ne prolaze ili kvalitet nije dobar:**

```
Wave 1 REJECTED. Issues found:
1. [Specifičan problem 1]
2. [Specifičan problem 2]

Re-run store-tester agent with these corrections:
- [Korekcija 1]
- [Korekcija 2]
```

**Ako je sve OK, popuni HITL checkbox u docs/plans/05-parallel-agents-plan.md i pošalji:**

```
HITL Checkpoint APPROVED.

Verification results:
- tasks/store_test.go reviewed: [X] tests, all have AC mapping comments
- go test ./...: PASS
- No external testing libraries used
- Tests are derived from AC, not from implementation

Proceed to Wave 2: deploy code-reviewer agent.
```

---

### Korak 5 — Pokreni Wave 2: code-reviewer agent

Nakon HITL approvela:

```
Wave 2: Deploy the code-reviewer agent.

Agent definition: .claude/agents/code-reviewer.md
Task: Review tasks/handler.go

Instructions for agent:
- Read tasks/handler.go
- Read CLAUDE.md for project constraints
- Read docs/specs/ for acceptance criteria
- Apply the review checklist from the agent definition
- Write review results to docs/review/handler-review.md
- DO NOT modify any production files

CRITICAL: This agent must have read-only behavior.
After completion, I will verify no files were modified.
```

---

### Korak 6 — Verificiraj da reviewer nije pisao fajlove

Ovo je ključna provjera. Code-reviewer agent smije samo čitati:

```bash
# Provjeri da nije modificirao production fajlove
git status
git diff tasks/handler.go
git diff tasks/store.go
```

**Očekivani output:** `git status` treba pokazati samo `docs/review/handler-review.md` kao novi fajl. Nijedan production fajl ne smije biti modificiran.

Ako je reviewer modificirao fajlove:

```bash
git diff tasks/handler.go
```

Revert sve neovlaštene izmjene:

```bash
git checkout tasks/handler.go
git checkout tasks/store.go
```

Zatim ažuriraj `.claude/agents/code-reviewer.md` da eksplicitno zabrani Write/Edit tools.

---

### Korak 7 — Pročitaj review report

Provjeri review:

```bash
cat docs/review/handler-review.md
```

Za svaki HIGH finding:
1. Otvori novi Claude chat
2. Pošalji targeted fix (ne cijeli feature):

```
Fix only this specific issue in tasks/handler.go:
[Paste HIGH finding]

Do not change anything else.
Run go build ./... after fix.
```

Za MEDIUM i LOW findings: napravi note, ali ne treba odmah riješiti.

---

### Korak 8 — Commituj sve

```bash
mkdir -p docs/review
git add tasks/store_test.go docs/review/ docs/plans/05-parallel-agents-plan.md .claude/agents/
git commit -m "feat: parallel agents — store tests + handler review with HITL checkpoint"
```

## Verifikacija

- [ ] `tasks/store_test.go` postoji s testovima koji imaju AC mapping komentare
- [ ] `go test ./...` prolazi
- [ ] `docs/review/handler-review.md` postoji s popunjenim PASS/FAIL findings
- [ ] `git diff tasks/handler.go tasks/store.go` je prazan (reviewer nije modificirao)
- [ ] HITL checkpoint u `docs/plans/05-parallel-agents-plan.md` je popunjen
- [ ] Možeš objasniti zašto je HITL checkpoint između Wave 1 i Wave 2 bio neophodan

## Šta si naučio

- **Orchestrator-worker pattern**: orchestrator koordinira i delegira, ne implementira — ti si orchestrator koji daje instrukcije agentima
- **Fan-out/fan-in**: oba agenta mogu teoretski raditi paralelno jer nemaju dependency jedan na drugog (u ovom labu radimo sekvencijalno ali dizajniramo kao parallel)
- **HITL checkpoint** nije opcionalan u production workflows — svaki agent output koji postaje input za drugi agent MORA biti verificiran od strane čovjeka
- **Least privilege za agente**: code-reviewer nema write permissions jer mu nije potrebno — minimalne permissions = manji blast radius ako agent pogriješi
- **Verification ownership separation**: orchestrator ne verificira agent output sebe — ti verificiraš (provjera git status, testovi)
