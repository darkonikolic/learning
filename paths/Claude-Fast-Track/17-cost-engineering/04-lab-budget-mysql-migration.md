# Lab 17 — Cost engineering: bugetiranje MySQL migracije

## Cilj
Na kraju ovog laba imaš procijenjeni token cost za MySQL migration fazu PRIJE izvođenja, izmjereni stvarni spend, analizu razlike, i cost ownership tablicu za projekt.

## Preduvjeti
- Lab 12 završen: MySQL migration implementirana
- `docs/` postoji s SPEC fajlovima, planovima i audit dokumentima
- tasks/ direktorijum s handler.go, store.go, mysql_store.go

## Kontekst
Token cost je vidljiv i mjerljiv. Svaka Claude sesija prikazuje token spend na kraju. Ovaj lab te uči procjenjivati cost PRIJE operacije, pa uspoređivati s realnošću. Cilj nije minimizirati cost — cilj je predvidjeti ga i razumjeti gdje tokeni idu.

## Koraci

### Korak 1 — Napiši cost procjenu PRIJE migracije

Pravljenje ove procjene zahtijeva da razumiješ šta Claude čita i piše u toku migration-a.

Napravi `docs/cost/mysql-migration-estimate.md`:

```markdown
# MySQL Migration Cost Estimate

## Date of estimate
[datum]

## Phase: MySQL migration (Lab 12)

## Files that will be read into context

| File | Estimated lines | Estimated tokens |
|------|----------------|-----------------|
| tasks/store.go | [provjeri: `wc -l tasks/store.go`] | [lines × 3] |
| tasks/handler.go | [provjeri] | |
| main.go | [provjeri] | |
| config/config.go | [provjeri] | |
| docs/specs/mysql-store.md | [provjeri] | |
| CLAUDE.md | [provjeri] | |
| docs/plans/[plan fajl] | [provjeri] | |
| **Total context input** | | |

## Claude calls estimation

| Step | Description | Estimated tokens in | Estimated tokens out |
|------|-------------|--------------------|--------------------|
| 1 | Blast radius analysis | [total files] | ~500 (analysis text) |
| 2 | Create Store interface | [store.go + handler.go] | ~200 (interface code) |
| 3 | Implement MySQLStore | [spec + store.go] | ~800 (implementation) |
| 4 | Update main.go | [main.go + config.go] | ~150 |
| 5 | Run tests | [test output] | ~300 |
| **Total** | | | |

## Total estimate

| Category | Tokens |
|----------|--------|
| Input tokens (total) | |
| Output tokens (total) | |
| **Grand total** | |

## Assumptions
- Average file: ~3 tokens per line
- Plan file read once per step (×5 steps)
- One correction loop per step (×1.5 multiplier for corrections)
```

**Uradi ovo:**
Izmjeri stvarne veličine fajlova:

```bash
wc -l tasks/store.go tasks/handler.go main.go config/config.go CLAUDE.md
wc -l docs/specs/mysql-store.md 2>/dev/null || echo "Doesnt exist yet"
```

Popuni tablicu s realnim brojevima. Procijeni tokene (rule of thumb: 1 linija ≈ 3 tokena).

---

### Korak 2 — Izvrši migraciju i mjeri stvarni spend

Ako Lab 12 nije završen, sada ga završi. Tokom izvođenja, prati token spend.

Otvori Claude sesiju za migraciju:

```bash
claude
```

Na kraju svake sesije, Claude prikazuje token usage. Primjer:

```
Session complete. Tokens used:
- Input: 15,432
- Output: 3,891
- Total: 19,323
```

Bilježi ove brojeve. Ako Claude ne prikazuje automatski, pitaj:

```
/cost
```

Ili:

```
How many tokens were used in this session?
```

---

### Korak 3 — Popuni stvarni spend

Ažuriraj `docs/cost/mysql-migration-estimate.md` s aktualnim podacima:

```markdown
## Actual spend (measured)

| Session | Purpose | Input tokens | Output tokens | Total |
|---------|---------|--------------|---------------|-------|
| Session 1 | Blast radius analysis + interface | | | |
| Session 2 | MySQLStore implementation | | | |
| Session 3 | main.go update + tests | | | |
| **Total actual** | | | | |

## Estimate vs actual comparison

| Metric | Estimated | Actual | Difference |
|--------|-----------|--------|------------|
| Total tokens | | | |
| Input tokens | | | |
| Output tokens | | | |
| Accuracy | | | |

## Analysis

Why estimate differed from actual:
- [navedi 2-3 konkretna razloga]

Biggest surprise:
- [šta je koštalo više nego očekivano?]
- [šta je koštalo manje?]
```

---

### Korak 4 — Analiziraj razliku

Otvori Claude sesiju za analizu:

```bash
claude
```

```
Read docs/cost/mysql-migration-estimate.md.

Analyze the difference between estimated and actual token spend for the MySQL migration.

Specific questions:
1. What was the biggest driver of cost overrun (if any)?
2. Was the plan file being read multiple times a significant factor?
3. How would you structure the next migration to reduce token cost by 20%?
4. What context elements were unnecessary (could have been excluded)?

Provide analysis in 3-4 bullet points per question.
Append analysis to docs/cost/mysql-migration-estimate.md under "## Cost analysis".
```

---

### Korak 5 — Napiši cost ownership tablicu za cijeli projekt

```
Read all docs/specs/ files, docs/plans/, and docs/cost/ to understand the full project scope.

Create docs/cost/project-cost-ownership.md with:

1. Cost breakdown by phase:
   | Phase | What was built | Estimated tokens | Notes |
   |-------|----------------|-----------------|-------|
   | Lab 01 | POST /tasks endpoint | | |
   | Lab 02 | GET /tasks | | |
   | Lab 03 | PATCH /tasks/:id/complete | | |
   | Lab 09 | Docker Compose | | |
   | Lab 12 | MySQL migration | [from estimate] | |
   | Lab 13 | Crawler agent | | |

2. Cost drivers table:
   | Driver | Impact | Optimization |
   |--------|--------|-------------|
   | Plan file reads × N tasks | High | Keep plan concise |
   | Large SPEC files | Medium | |
   | Correction loops | Variable | |
   | [other drivers you found] | | |

3. Recommendations for cost discipline:
   - [3-5 concrete recommendations based on this lab's learnings]
```

---

### Korak 6 — Soft i hard ceiling za sljedeću fazu

Na osnovu mjerenja, definiši ceilings za sljedeću veliku fazu (npr. crawler Phase 2):

```
Based on the MySQL migration actual spend in docs/cost/mysql-migration-estimate.md,
define token budgets for the next major phase (crawler Phase 2 implementation).

In docs/cost/crawler-phase2-budget.md, create:

## Crawler Phase 2 Budget

Soft ceiling: [estimated × 1.5]
Hard ceiling: [estimated × 2.0]

When soft ceiling is hit:
- Review remaining tasks
- Check if context can be trimmed
- Consider splitting into a second session

When hard ceiling is hit:
- STOP execution
- Replan remaining tasks with narrower scope
- Do not continue until new session with clean context

Context budget per task:
- Soft: 60% context window fill
- Hard: 80% context window fill
```

---

### Korak 7 — Commituj cost dokumentaciju

```bash
mkdir -p docs/cost
git add docs/cost/
git commit -m "docs: MySQL migration cost estimate vs actual + project cost ownership"
```

## Verifikacija

- [ ] `docs/cost/mysql-migration-estimate.md` postoji s procjenom i aktualnim podacima
- [ ] Razlika između procjene i stvarnosti je dokumentovana (% razlike)
- [ ] `docs/cost/project-cost-ownership.md` postoji s phase breakdown-om
- [ ] `docs/cost/crawler-phase2-budget.md` postoji s soft/hard ceilings
- [ ] Analiza objašnjava konkretne razloge razlike
- [ ] Procjena i stvarnost su unutar 50% (ako nisu, objasni zašto)

## Šta si naučio

- **Token budget i context budget su različiti**: možeš trošiti malo tokena ali puniti context window; možeš trošiti puno tokena ali u kratkim sesijama
- **Execute faza dominira cost-om** — svaki task ponovo čita plan fajl, što se brzo akumulira pri N tasks
- **Procjena PRIJE izvođenja** te tjera da razumiješ šta Claude zapravo radi — slijepo pokretanje bez procjene je kao kod review bez diff-a
- **30% razlika** je realna u prvim procjenama — correction loops i unexpected context reads su najčešći uzroci prekoračenja
- **Cost ownership** je informirano odlučivanje: znati gdje idu tokeni znači moći birati gdje štediti (plan verbosity) i gdje ne štediti (SPEC acceptance criteria — nikad brisati)
