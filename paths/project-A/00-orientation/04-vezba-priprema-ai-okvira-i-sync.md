# 04 — Vežba: priprema AI-okvira i sync (orijentacija)

Pre prvog modula inicijalizuješ i potvrđuješ AI-okvir kojim ćeš voditi ceo project-A — ovo je „nulti" sync koji postavlja temelj koji svaka kasnija oblast nadograđuje.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Inicijalizujemo `CLAUDE.md` u radnom repou, potvrđujemo da `## Project-A workflow` sekcija radi, i donosi se odluka šta (ako išta) inicijalizovati pre prvog modula.

**Pretpostavke za potvrdu:**
- Radni repo je kreiran i Claude Code CLI je instaliran (`claude --version` radi)
- `CLAUDE.md` ne postoji ili treba inicijalizovati sa `claude /init`
- `## Project-A workflow` sekcija treba biti dodata ručno posle inicijalizacije

**Van opsega:**
- Ne dodajemo oblast-specifična pravila ovde (to rade kasniji moduli)
- Ne menjamo globalni Claude Code config — samo radni repo

**Prompt za diskusiju:**
```
Krećem project-A u novom repou. Koji minimalni CLAUDE.md setup
mi treba da bih radio po plan→validacija petlji,
bez dodavanja suvišnog? Šta staviti u ## Project-A workflow sekciju?
Predloži sadržaj, ne kreiraj automatski.
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Inicijalizovati minimalni AI-okvir u radnom repou tako da `## Project-A workflow` sekcija u `CLAUDE.md` radi i `/plan` blokira izmene bez odobrenog plana.

**Fajlovi koji se diraju:**
- `CLAUDE.md` — kreiranje sa `## Project-A workflow` sekcijom

**Fajlovi koji se NE diraju:**
- Svi ostali fajlovi u repou — nulti sync ne menja kod

**AI okvir za ovu oblast:**

Dodaj sekciju `## Project-A workflow` u `CLAUDE.md`, ili napravi `.claude/rules/project-a-workflow.md`

Sadržaj pravila:
```
## Project-A workflow

- Pre svake izmene: napiši plan i dobij potvrdu (/plan u Claude Code terminalu).
- Petlja: diskusija → plan → egzekucija → validacija → sync/capture.
- Kontekst: uvijek uključi verzije alata, cloud region, i existing konfiguraciju pri DevOps pitanjima.
- Anti-sprawl: ne dodaj CLAUDE.md sekciju ili .claude/rules/ fajl dok se potreba ne ponovi kroz više modula.
- Svaka oblast završava sync-om u .claude/memory/decisions.md ili CLAUDE.md ## Decision log sekciji.
```

Anti-sprawl: ovo je osnovno pravilo — mora se dodati. Oblast-specifična pravila dolaze tek u kasnijim modulima.

**Acceptance criteria:**
- [ ] `CLAUDE.md` postoji u korenu radnog repoa
- [ ] `## Project-A workflow` sekcija je prisutna u `CLAUDE.md`
- [ ] `/plan` komanda u Claude Code terminalu prepoznaje workflow i traži plan pre egzekucije

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Pokrećem claude /init da kreiram CLAUDE.md
- Dodajem ## Project-A workflow sekciju ručno
- Potvrđujem da se učitava: /plan u terminalu

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Inicijalizuj `CLAUDE.md` ako ne postoji:

```bash
# Pokreni u korenu radnog repoa
claude /init
```

Provjeri da li postoji i sadrži workflow sekciju:

```bash
grep -A 10 "Project-A workflow" CLAUDE.md 2>/dev/null || echo "CLAUDE.md nema workflow sekciju — dodaj je ručno"
```

Provjeri `.claude/` direktorijum:

```bash
ls -la .claude/ 2>/dev/null || echo "Direktorijum .claude/ ne postoji"
```

Ako trebaš posebna pravila po oblasti (umjesto CLAUDE.md sekcija), napravi `.claude/rules/` folder:

```bash
mkdir -p .claude/rules .claude/memory
```

Provjeri da `/plan` radi — pokreni `claude` u terminalu i kucaj `/plan`. Claude treba da odgovori tražeći plan opis pre bilo kakve egzekucije.

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- CLAUDE.md postoji u korenu repoa
- ## Project-A workflow sekcija je prisutna
- /plan komanda prepoznaje workflow

Evo outputa:
[ovde lepiš: cat CLAUDE.md | head -30, ls .claude/, i rezultat /plan testa]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `cat CLAUDE.md` | Fajl postoji i sadrži `## Project-A workflow` sekciju sa pravilima |
| 2 | U Claude Code terminalu kucaj `/plan` | Claude traži opis plana i ne izvršava odmah ništa |
| 3 | U Claude Code terminalu napiši pitanje o DevOps temi | Claude odgovara uzimajući u obzir kontekst iz CLAUDE.md |
| 4 | Provjeri `ls .claude/` | Postoji `.claude/` direktorijum (settings.json i/ili rules/ i/ili memory/) |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Orijentacija sync
- Urađeno: inicijalizovan CLAUDE.md sa ## Project-A workflow sekcijom; potvrđen /plan workflow
- Naučeno: kako CLAUDE.md daje kontekst Claudeu, kako /plan blokira direktnu egzekuciju
- Šta bi promenio:
```
