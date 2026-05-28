# Lab 16 — Rule konflikti: spec-before-code vs run-tests skill

## Cilj
Na kraju ovog laba postoji dokumentovani konflikt između `spec-before-code` pravila i `run-tests` skilla, `RULE_PRIORITY.md` ga rješava, Claude poštuje prioritet, i hotfix scenarij ima dokumentovani izuzetak.

## Preduvjeti
- Lab 04 završen: `.claude/rules/spec-before-code.md` i `.claude/skills/run-tests/SKILL.md` postoje
- `.claude/agents/store-tester.md` postoji (iz Lab 05)
- `go build ./...` prolazi

## Kontekst
Realni projekti imaju pravila koja se međusobno suprotstavljaju. `spec-before-code` pravilo kaže: bez SPEC-a nema implementacije. `run-tests` skill poziva testove direktno bez provjere da li SPEC postoji. Ovo je namjerni konflikt koji rješavaš kroz formalni conflict resolution process.

## Koraci

### Korak 1 — Induciraj konflikt

Prvo, napravi konflikt vidljivim. Ažuriraj `run-tests` skill da poziva testove BEZ provjere SPEC-a:

Otvori `.claude/skills/run-tests/SKILL.md` i provjeri: sadrži li provjeru da SPEC postoji? Vjerovatno ne.

Sada napravi situaciju u kojoj konflikt nastaje. Otvori Claude sesiju:

```bash
claude
```

```
Read .claude/rules/spec-before-code.md and .claude/skills/run-tests/SKILL.md.

I want to run tests for a new feature that I haven't written a SPEC for yet.
Specifically: run tests for a "delete task" feature.

The spec-before-code rule says I need a SPEC first.
The run-tests skill would just run tests without checking for a SPEC.

Identify the conflict and tell me which rule wins according to the priority ladder.
Do not run any tests yet.
```

**Očekivani output:**
Claude treba identificirati konflikt između `spec-before-code` (Correctness tier) i run-tests skill (implicitly Maintainability/workflow tier). Treba zaključiti da spec-before-code wins.

---

### Korak 2 — Napiši RULE_PRIORITY.md

Napravi `.claude/RULE_PRIORITY.md`:

```markdown
# RULE_PRIORITY.md
# Priority hierarchy for task-api — highest to lowest

## Level hierarchy

1. Turn-level instructions — what you type in the current message
   - Highest priority for execution
   - Cannot override Security-tier project rules
   - Expires at end of turn

2. Session-level context — docs/plans/*-context.md, session flags
   - Scoped to the current phase/session
   - Can narrow or tighten project rules for this phase
   - Expires when session ends or phase changes

3. Project-level rules — .claude/rules/*.md
   - Default authority for all work in this project
   - Can override global rules within project scope

4. Global rules — ~/.claude/CLAUDE.md
   - Applies to all projects unless overridden
   - Lowest priority when a more specific rule exists

## Priority ladder (severity order)

1. Security — vulnerabilities, auth, secret handling, injection
2. Correctness — spec-compliance, data integrity, contract accuracy
3. Reliability — change safety, reversibility, predictability
4. Maintainability — readability, clarity, long-term understandability
5. Performance / cost — speed, token efficiency

## Rule tier assignments — task-api

| Rule file | Level | Tier | Notes |
|-----------|-------|------|-------|
| spec-before-code.md | Project | Correctness | Cannot implement without SPEC |
| stdlib-only.md | Project | Correctness | Supply-chain integrity |
| handler-contracts.md | Project | Reliability | HTTP boundary enforcement |
| run-tests skill | Project | Maintainability | Workflow convenience |

## Conflict resolution: spec-before-code vs run-tests skill

### Conflict description
- spec-before-code.md requires SPEC to exist before any implementation
- run-tests skill invokes tests without checking SPEC existence
- When asked to run tests for a feature without SPEC: spec-before-code wins

### Resolution
Correctness tier (spec-before-code) > Maintainability tier (run-tests workflow).

run-tests skill is allowed to:
- Run existing tests for existing features
- NOT trigger implementation of new features without SPEC

run-tests skill is NOT allowed to:
- Be used as a way to "test-first" new features without writing SPEC first

## Active exceptions

(none)

## Resolved exceptions

| Exception | Overridden rule | Resolved date | Resolution |
|-----------|----------------|---------------|------------|
```

---

### Korak 3 — Napiši HOTFIX izuzetak

Dodaj hotfix exception u RULE_PRIORITY.md:

```markdown
## Hotfix exception procedure

### When hotfix applies
A hotfix is an emergency fix for a production bug that:
1. Breaks existing functionality (not missing feature)
2. Cannot wait for a full SPEC cycle
3. Is a minimal targeted fix (not a feature addition)

### Hotfix process
1. Create docs/decisions/hotfix-NNN-[description].md
2. Document: what is broken, what the fix is, why it can't wait
3. In the session: state "This is a hotfix for [issue]. Hotfix exception applies per RULE_PRIORITY.md."
4. Implement the minimal fix
5. Write SPEC retroactively within 24 hours

### What hotfix does NOT allow
- Adding new features
- Refactoring while fixing
- Skipping tests (existing tests must still pass after hotfix)

### Hotfix declaration format
To trigger hotfix exception, you MUST say exactly:
"HOTFIX EXCEPTION: [brief description of what is broken]"
Without this declaration, spec-before-code rule applies.
```

---

### Korak 4 — Verificiraj da Claude poštuje prioritet

Otvori novu Claude sesiju:

```bash
claude
```

**Test 1: Claude odbija bez SPEC-a:**

```
Read .claude/RULE_PRIORITY.md and .claude/rules/spec-before-code.md.

I want to implement a DELETE /tasks/:id endpoint.
I don't have a SPEC yet. Can you start implementing it?
```

**Očekivani output:**
Claude treba odbiti i referirati se na spec-before-code pravilo i RULE_PRIORITY.md.

**Test 2: run-tests skill odbija za novi feature:**

```
/run-tests
Can you also test the delete endpoint that we haven't implemented yet?
```

**Očekivani output:**
Claude treba pokrenuti testove za postojeće feature-e, ali odbiti testovanje nepostojećeg delete endpoint-a bez SPEC-a.

**Test 3: HOTFIX izuzetak radi:**

```
HOTFIX EXCEPTION: GET /tasks returns 500 on empty database (production bug)

This is an emergency fix — existing functionality is broken.
The fix is: ensure store.List() returns empty slice, not error, when table has 0 rows.

Apply hotfix exception per .claude/RULE_PRIORITY.md.
```

**Očekivani output:**
Claude treba prihvatiti hotfix exception (jer je korektno deklariran) i raditi na popravku bez zahtijevanja SPEC-a.

---

### Korak 5 — Documentuj jedan resolver primjer

Napravi `docs/decisions/conflict-001-spec-before-code-vs-run-tests.md`:

```markdown
# Conflict 001: spec-before-code vs run-tests skill

## Detection date
[datum]

## Conflict type
Type 1 — Risk vs ergonomics

## Rule A
spec-before-code.md (Project level, Correctness tier)
Requirement: SPEC must exist before implementation

## Rule B
run-tests skill (Project level, Maintainability tier)
Requirement: runs tests conveniently without SPEC check

## Contradiction
run-tests skill can be invoked for a feature without SPEC,
implicitly allowing a "test-first without SPEC" workflow.

## Resolution
Apply priority ladder: Correctness (spec-before-code) > Maintainability (run-tests).

run-tests skill is narrowed: runs existing tests only.
Cannot be used to drive new feature implementation.

## Documentation
.claude/RULE_PRIORITY.md updated with explicit conflict resolution.

## Expiry
N/A — permanent rule, no expiry needed.
```

---

### Korak 6 — Verificiraj da Claude primjenjuje hotfix u pravom kontekstu

Napiši kratak test koji demonstrira da hotfix NIJE odobreno bez deklaracije:

```
I need to quickly fix something in handler.go — it's urgent.
Don't worry about the SPEC — just make this change...
[describe a change]
```

**Očekivani output:**
Claude treba odbiti jer "urgent" nije isto što i "HOTFIX EXCEPTION: [description]". Hotfix exception zahtijeva eksplicitnu deklaraciju.

---

### Korak 7 — Commituj konfiguraciju

```bash
git add .claude/RULE_PRIORITY.md docs/decisions/conflict-001-spec-before-code-vs-run-tests.md
git commit -m "config: RULE_PRIORITY.md with conflict resolution and hotfix exception"
```

## Verifikacija

- [ ] `.claude/RULE_PRIORITY.md` postoji s tier assignments i conflict resolution sekcijom
- [ ] Claude odbija implementaciju bez SPEC-a (Test 1 prolazi)
- [ ] Claude odbija testovanje nepostojećih feature-a bez SPEC-a (Test 2 prolazi)
- [ ] Claude prihvata hotfix exception s eksplicitnom deklaracijom (Test 3 prolazi)
- [ ] Claude odbija "urgent" bez eksplicitne HOTFIX EXCEPTION deklaracije (Test 4 prolazi)
- [ ] `docs/decisions/conflict-001-*.md` postoji s dokumentovanim resolution-om

## Šta si naučio

- **Priority ladder** (Security > Correctness > Reliability > Maintainability > Performance) nije apstraktan — koristiš ga da riješiš konkretne konflikte
- **"Risk vs ergonomics"** je najčešći konflikt tip: spec-before-code je risk rule, run-tests je ergonomics — risk uvijek pobijedi
- **Explicit exception declaration** sprečava abuse: "urgent" nije hotfix, "HOTFIX EXCEPTION: [opis]" jest — deklaracija je namjerna frikcija
- **RULE_PRIORITY.md je living document**: svaki novi konflikt koji riješiš dodaje se kao conflict resolution primjer
- **Session-level instructions ne mogu override Security-tier pravila**: čak i turn-level "just do it" ne može pregaziti security constraint — to je hard boundary
