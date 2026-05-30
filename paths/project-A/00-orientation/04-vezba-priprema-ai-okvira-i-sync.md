# 04 — Vežba: priprema AI-okvira i sync (orijentacija)

Pre prvog modula inicijalizuješ i potvrđuješ AI-okvir kojim ćeš voditi ceo project-A — ovo je „nulti" sync koji postavlja temelj koji svaka kasnija oblast nadograđuje.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Mapiramo koji agenti, pravila i skills već postoje u `.cursor/` okviru, potvrđujemo da `project-a-workflow` radi u radnom repou, i donosi se odluka šta (ako išta) inicijalizovati pre prvog modula.

**Pretpostavke za potvrdu:**
- Radni repo je kreiran i ima `.cursor/` direktorijum ili ga treba inicijalizovati
- Postoje agenti `/devops-engineer`, `/learning-architect`, `/system-maintainer`
- `project-a-workflow` pravilo je dostupno i scopovano na ovaj repo

**Van opsega:**
- Ne dodajemo oblast-specifična pravila ovde (to rade kasniji moduli)
- Ne menjamo globalni `.cursor/` config — samo radni repo

**Prompt za diskusiju:**
```
Krećem project-A u novom repou. Koji minimalni .cursor setup
(rules, agenti) mi treba da bih radio po plan→validacija petlji,
bez dodavanja suvišnog? Koji agenti i pravila već postoje u okviru?
Predloži šta da inicijalizujem, ne kreiraj automatski.
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene  
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Inicijalizovati minimalni AI-okvir u radnom repou tako da `project-a-workflow` petlja radi i Plan mode blokira izmene bez odobrenog plana.

**Fajlovi koji se diraju:**
- `.cursor/rules/project-a-workflow.mdc`

**Fajlovi koji se NE diraju:**
- Svi ostali fajlovi u repou — nulti sync ne menja kod

**AI okvir za ovu oblast:**

> **Cursor:** napravi/ažuriraj `.cursor/rules/project-a-workflow.mdc` (globs: `paths/project-A/**/*`)  
> **Claude Code:** dodaj sekciju `## Project-A workflow` u `CLAUDE.md`, ili napravi `.claude/rules/project-a-workflow.md`

Sadržaj pravila (isti za oba alata):
```
- Pre svake izmene: napiši plan i dobij potvrdu (Plan mode / /plan).
- Petlja: diskusija → plan → egzekucija → validacija → sync/capture.
- Agenti: /devops-engineer za DevOps rad, /learning-architect za strukturu, /system-maintainer za odluke o okviru.
- Anti-sprawl: ne dodaj rule/skill dok se potreba ne ponovi kroz više modula.
- Svaka oblast završava sync-om u decision_log.md.
```

Anti-sprawl: ovo je osnovno pravilo — mora se dodati. Oblast-specifična pravila dolaze tek u kasnijim modulima.

**Acceptance criteria:**
- [ ] Tabela agenti/pravila/skills popunjena i potvrđena
- [ ] `project-a-workflow` pravilo se učitava u radnom repou (Cursor prikazuje rule u context; Claude Code: `/plan` komanda prepoznata)
- [ ] Plan mode dokazano read-only — pokušaj izmene bez plana je odbijen (Cursor) ili `/plan` blokira direktnu egzekuciju (Claude Code)

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Inicijalizujem .cursor/rules/project-a-workflow.mdc scoped na ovaj repo
- Potvrđujem da se učitava i da Plan mode blokira izmene bez plana

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta za DevOps rad  
> **Claude Code:** direktno u terminalu, Claude izvršava komande

Provjeri strukturu `.cursor/` direktorijuma:

```bash
ls -la .cursor/rules/ 2>/dev/null || echo "Direktorijum ne postoji — treba ga kreirati"
```

Inicijalizuj direktorijum ako ne postoji:

```bash
mkdir -p .cursor/rules .cursor/memory
```

Potvrdi koji agenti su dostupni (pregledaj globalni `.cursor/` config):

```bash
ls ~/.cursor/rules/ 2>/dev/null || ls ~/.config/cursor/rules/ 2>/dev/null
```

Provjeri da li se pravilo učitava u Cursor-u: otvori bilo koji fajl u repou i u Cursor chat potvrdi da `project-a-workflow` rule je u kontekstu.

> **Claude Code alternativa:** Provjeri da je `CLAUDE.md` kreiran u korenu repoa sa sekcijom `## Project-A workflow`, ili da postoji `.claude/rules/project-a-workflow.md`.

```bash
cat CLAUDE.md | grep -A 10 "Project-A workflow" 2>/dev/null || echo "CLAUDE.md nema workflow sekciju"
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- Tabela agenti/pravila/skills popunjena i potvrđena
- project-a-workflow pravilo se učitava u radnom repou
- Plan mode dokazano read-only

Evo outputa / konfiguracije:
[ovde lepiš ls output .cursor/rules/, sadržaj pravila, i rezultat testa Plan mode-a]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Otvori Cursor, kucaj u chat bez uključenog Plan mode-a i pokušaj da izmenjaš fajl | Cursor prikazuje upozorenje ili odbija izmenu dok plan nije odobren |
| 2 | U Cursor chat napiši `/devops-engineer` i pošalji poruku | Agent se aktivira i odgovara u DevOps personi |
| 3 | U terminalu (Claude Code) pokreni `/plan` | Komanda traži plan pre egzekucije, ne izvršava odmah |
| 4 | Provjeri `.cursor/rules/` direktorijum | Postoji `project-a-workflow.mdc` sa ispravnim `globs:` poljem |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`  
> **Claude Code:** zapiši u `docs/decisions/orientation-tooling.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Orijentacija sync
- Urađeno: inicijalizovan project-a-workflow rule; potvrđeni agenti i Plan mode
- Naučeno: koji agenti postoje, kako Plan mode blokira izmene
- Šta bi promenio:
```
