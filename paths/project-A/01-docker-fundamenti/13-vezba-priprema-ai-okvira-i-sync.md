# 13 — Vežba: priprema AI-okvira i praktični sync

Ovo je model-vežba koju svaka oblast dobija: prvo **pripremiš AI-okvir** (agente/rules/skills) za temu oblasti, pa onda radiš **praktičan rad** kroz taj okvir i na kraju **sync**-uješ naučeno nazad u config. Prati `project-a-workflow` petlju (plan → diskusija → egzekucija → validacija → capture).

## Cilj

Na kraju imaš:
- jasnu odluku koji `.cursor` agenti/rules/skills pokrivaju Docker rad u project-A (i šta, ako išta, dodaješ)
- najmanji smislen dodatak okvira (ili obrazloženje zašto dodatak nije potreban)
- Dockerfile iz laba 08 provučen kroz taj okvir: lintovan, skeniran, validiran
- zabeležen `sync` u `.cursor/memory/decision_log.md`

## Preduslovi

- Završen lab `08-lab-kontejnerizuj-app` (imaš `Dockerfile`, `docker-compose.yml`)
- Pročitano `01`–`07` ove oblasti (best practices, bezbednost)
- Postojeći `.cursor` sistem (`/devops-engineer`, `project-a-workflow`, `/system-maintainer`, `process-feedback`)

---

## Deo A — Priprema AI-okvira za Docker

### Korak A1 — Mapiraj šta Docker rad traži

Napravi tabelu: za tipičan Docker zadatak (napiši/popravi Dockerfile, build, skeniraj) — šta od okvira već postoji, a šta fali.

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Persona za DevOps rad | da | `/devops-engineer` |
| Petlja plan→validacija | da | `project-a-workflow` |
| Konkretna **Docker validacija** (lint/scan kriterijumi) | ? | — |
| Odluka da/ne dodajem alat | — | `/system-maintainer` |

### Korak A2 — Odluči (anti-sprawl)

**Ne pravi pravilo/skill po refleksu.** Pusti `/system-maintainer` i `process-feedback` da klasifikuju potrebu i predlože:

```
Classification: workflow
Candidate:      skill `review-dockerfile` ili glob-rule za **/Dockerfile
Change:         add | none
Evidence:       Docker se ponavlja kroz module 01, 13-aplikacija, 28
Confidence:     ...
Action:         ...
```

Pravilo odluke: dodaješ **samo** ako se potreba ponavlja kroz više modula i nije pokrivena postojećim. Za Docker to obično jeste slučaj (ponavlja se), pa je minimalan dodatak opravdan.

### Korak A3 — Implementiraj minimalni dodatak

Ako je odluka „dodaj", napravi **jedan** mali artefakt — npr. glob-scoped rule za Dockerfile-ove:

```
# .cursor/rules/dockerfile-checks.mdc
---
description: Dockerfile review checklist for project-A
globs: paths/project-A/**/Dockerfile
alwaysApply: false
---

# Dockerfile checks

- Pinuj verziju base image-a (nginx:1.25.3-alpine, ne :latest).
- Multi-stage gde se kompajlira (Go/Node) → final image bez build alata.
- Ne pokreći kao root gde nije nužno; `USER` po potrebi.
- `.dockerignore` postoji i isključuje .git/.env.
- Bez secrets u layer-ima (koristi `--mount=type=secret`).
- HEALTHCHECK ili health endpoint za K8s liveness.
```

Ako je odluka „ne dodaj", zapiši u `decision_log.md` zašto (npr. „pokriveno sa `/devops-engineer` + best practices iz 07").

**Acceptance A:** postoji zapis odluke i (ako dodato) jedan funkcionalan artefakt koji se učitava na Dockerfile.

---

## Deo B — Praktičan rad (sync)

Sada koristiš okvir na pravom zadatku: pooštri Dockerfile iz laba 08 kroz pripremljeni okvir.

### Korak B1 — Plan (Plan mode)

Cilj: Dockerfile prolazi lint + scan bez high/critical nalaza. Zapiši dodirnute fajlove i acceptance kriterijume pre izmene.

### Korak B2 — Lint sa hadolint

```bash
docker run --rm -i hadolint/hadolint < Dockerfile
```

> **Podman:** `podman run --rm -i hadolint/hadolint < Dockerfile`

Tipičan nalaz: `DL3006 Always tag the version of an image explicitly`, `DL3025`, itd. Popravi po checklist-i iz Dela A.

### Korak B3 — Build i scan sa Trivy

```bash
docker build -t helloworld:local .
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image --severity HIGH,CRITICAL helloworld:local
```

> **Podman:** zameni socket sa `/run/user/$(id -u)/podman/podman.sock:/var/run/docker.sock`

Cilj: nula HIGH/CRITICAL koje možeš da rešiš (npr. update base image tag).

### Korak B4 — Smoke test

```bash
docker run -d --name hw -p 8080:80 helloworld:local
curl -o /dev/null -s -w "%{http_code}\n" http://localhost:8080   # 200
docker rm -f hw
```

### Korak B5 — Sync (capture)

Zatvori petlju — vrati naučeno u config:
- ako si u B otkrio nov kriterijum (npr. dodaj `DL3059` u checklist), ažuriraj artefakt iz A3
- zapiši u `.cursor/memory/decision_log.md`: šta je dodato/promenjeno i zašto

```
## <datum> — Docker tooling sync (oblast 01)
- Dodat dockerfile-checks rule / ili: odlučeno bez dodatka jer ...
- hadolint + trivy uvedeni kao Docker validacija u project-a-workflow
```

---

## Validacija — acceptance kriterijumi

- [ ] Tabela iz A1 popunjena; odluka iz A2 doneta preko `/system-maintainer`
- [ ] (ako „dodaj") artefakt postoji i učitava se na `**/Dockerfile`
- [ ] `hadolint` bez grešaka koje su rešive
- [ ] `trivy ... --severity HIGH,CRITICAL` bez rešivih nalaza
- [ ] smoke test vraća `200`
- [ ] sync zapisan u `decision_log.md`

„Izgleda dobro" nije validacija — kriterijum je zelen lint/scan/test izlaz.

---

## AI workflow

Za odluku da/ne u Delu A:

```
Radim Docker oblast u project-A. Postojeći okvir: /devops-engineer +
project-a-workflow. Da li mi treba poseban Docker artefakt (rule ili skill),
ili je pokriveno? Predloži kao kandidat sa evidencijom i confidence, bez
automatskog kreiranja.
```

Kad hadolint/trivy prijavi nalaz koji ne razumeš:

```
hadolint daje [nalaz] na ovom Dockerfile-u:
[sadržaj]
Objasni pravilo, zašto je bitno za produkciju, i minimalan fix.
```
