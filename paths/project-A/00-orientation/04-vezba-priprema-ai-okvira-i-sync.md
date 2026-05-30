# 04 — Vežba: priprema AI-okvira i sync (orijentacija)

Pre prvog modula upoznaješ i potvrđuješ AI-okvir kojim ćeš voditi ceo project-a. Ovo je „nulti" sync — postavljaš temelj koji svaka kasnija oblast nadograđuje.

## Cilj

- razumeš koji `.cursor` agenti/rules/skills postoje i čemu služe
- znaš obaveznu petlju `project-a-workflow` (plan → diskusija → egzekucija → validacija → capture)
- imaš plan kako AI-okvir putuje u radni repo

## Deo A — Priprema AI-okvira (pregled)

### A1 — Mapiraj okvir

| Sloj | Šta postoji | Kad se koristi |
|------|-------------|----------------|
| Agenti | `/devops-engineer`, `/learning-architect`, `/system-maintainer` | persona za rad/plan/održavanje |
| Pravila | `project-a-workflow`, `reality-guard`, `learning-*` | uvek tokom project-a rada |
| Skills | `check-prerequisites`, `process-feedback`, `generate-project` | po koraku petlje |

### A2 — Odluka (anti-sprawl)

Na startu **ništa ne dodaješ** — prvo koristiš postojeće. Novi rule/skill se uvodi tek kad se potreba ponovi kroz module (`/system-maintainer` + `process-feedback`).

## Deo B — Praktičan rad (sync)

U radnom project-a repou:
- inicijalizuj `.cursor/` sa `project-a-workflow` pravilom (scoped na taj repo)
- potvrdi da se pravilo učitava i da Plan mode blokira izmene dok plan nije odobren

## Validacija — acceptance kriterijumi

- [ ] tabela A1 popunjena
- [ ] u radnom repou se `project-a-workflow` učitava
- [ ] Plan mode dokazano read-only (pokušaj izmene odbijen bez plana)

## AI workflow

```
Krećem project-a u novom repou. Koji minimalni .cursor setup
(rules/agenti) mi treba da bih radio po plan→validacija petlji,
bez dodavanja suvišnog? Predloži, ne kreiraj automatski.
```
