# 07 — Vežba: priprema AI-okvira i sync (GitLab CI)

Pripremaš AI-okvir za rad sa `.gitlab-ci.yml`, pa praktično validiraš pipeline konfiguraciju kroz `glab ci lint` i checklist.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Odlučujemo da li je potreban CI-specifičan artefakt u okviru (glob-rule za `.gitlab-ci.yml`), pa postojeću CI konfiguraciju provodimo kroz lint i proveravamo da nema plaintext secrets.

**Pretpostavke za potvrdu:**
- Postoji `.gitlab-ci.yml` u radnom repou (iz prethodnih labova oblasti 02)
- `glab` CLI je instalisan i autentifikovan na GitLab instancu
- Postoji `.cursor/` okvir sa `/devops-engineer` i `project-a-workflow`

**Van opsega:**
- Ne menjamo aplikacijski kod niti Dockerfile
- Ne podešavamo GitLab runner — samo validiramo konfiguraciju

**Prompt za diskusiju:**
```
Radim GitLab CI oblast u project-A. Imam .gitlab-ci.yml koji treba da
prođe lint. Postojeći okvir: /devops-engineer + project-a-workflow.
Da li mi treba poseban CI artefakt (rule za .gitlab-ci.yml), ili je
pokriveno? Predloži kao kandidat sa evidencijom i confidence, bez
automatskog kreiranja.
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene  
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** `.gitlab-ci.yml` prolazi `glab ci lint` bez grešaka i ne sadrži plaintext secrets.

**Fajlovi koji se diraju:**
- `.gitlab-ci.yml`
- `.cursor/rules/gitlab-ci-checks.mdc` (ako je odluka „dodaj")

**Fajlovi koji se NE diraju:**
- `Dockerfile` — obrađen u oblasti 01
- Aplikacijski kod — samo CI konfiguracija

**AI okvir za ovu oblast:**

> **Cursor:** napravi/ažuriraj `.cursor/rules/gitlab-ci-checks.mdc` (globs: `paths/project-A/**/.gitlab-ci.yml`)  
> **Claude Code:** dodaj sekciju `## GitLab CI validation checklist` u `CLAUDE.md`, ili napravi `.claude/rules/gitlab-ci-checks.md`

Sadržaj pravila (isti za oba alata):
```
- Svaki job ima stage, rules: (ne only/except), i jasne needs:.
- Path-based rules: changes: da se ne build-uje sve pri svakom commitu.
- Bez plaintext secrets — koristi CI/CD variables (masked, protected).
- interruptible: true za feature grane.
```

Anti-sprawl: CI se ponavlja kroz module 02, 10 i 22 — minimalan dodatak je opravdan. Ako je pokriveno postojećim pravilima, zapiši odluku i preskoči kreiranje.

**Acceptance criteria:**
- [ ] Odluka o artefaktu doneta preko `/system-maintainer` i zapisana
- [ ] `glab ci lint` prolazi bez grešaka
- [ ] `grep -r "password\|secret\|token" .gitlab-ci.yml` — nema plaintext secrets
- [ ] Sync zapisan u `decision_log.md`

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Donosim odluku o gitlab-ci-checks artefaktu
- Pokrećem glab ci lint, popravljam nalaze
- Proveravam da nema plaintext secrets
- Zapisujem sync

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta za DevOps rad  
> **Claude Code:** direktno u terminalu, Claude izvršava komande

Lint GitLab CI konfiguracije:

```bash
glab ci lint
```

YAML sanity check kao alternativa ili dopuna:

```bash
docker run --rm -v "$PWD":/w -w /w cytopia/yamllint .gitlab-ci.yml
```

Provjeri da nema plaintext secrets:

```bash
grep -rn "password\|secret\|token\|api_key" .gitlab-ci.yml
```

Popravi nalaze po checklist-i iz AI okvira (stages, `rules:`, `needs:`, secrets).

Ako lint prijavi grešku koju ne razumeš:

```
Evo mog .gitlab-ci.yml i CI Lint greške:
[konfiguracija]
[greška]
Objasni uzrok i minimalan fix; da li rules: treba prepravku?
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- glab ci lint prolazi bez grešaka
- nema plaintext secrets u konfiguraciji
- sync zapisan u decision_log.md

Evo outputa:
[ovde lepiš glab ci lint output i grep output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `glab ci lint` u korenu repoa | Shell ispisuje `Validation successful` ili ekvivalent bez error linije |
| 2 | Pokreni `grep -rn "password\|secret\|token\|api_key" .gitlab-ci.yml` | Nema izlaza (ili izlaz sadrži samo reference na CI/CD varijable u `$VAR` formatu) |
| 3 | Otvori `.gitlab-ci.yml` i provjeri da svaki job ima `rules:` ključ, ne `only:` | Pretraga `grep "only:" .gitlab-ci.yml` nema izlaza |
| 4 | Otvori `.cursor/rules/gitlab-ci-checks.mdc` ili `CLAUDE.md` | Fajl postoji i sadrži checklist sa 4 pravila |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`  
> **Claude Code:** zapiši u `docs/decisions/gitlab-ci-tooling.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — GitLab CI sync (oblast 02)
- Urađeno: gitlab-ci-checks rule dodat / ili: odlučeno bez dodatka jer ...
- Naučeno: glab ci lint kao CI validacija; rules: vs only/except razlika
- Šta bi promenio:
```
