# 13 — Vežba: priprema AI-okvira i sync (Docker)

Potvrđuješ i proširuješ AI-okvir za Docker rad, pa Dockerfile iz laba 08 provodiš kroz taj okvir — lintovanje, skeniranje i smoke test.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Odlučujemo da li je potreban Docker-specifičan artefakt u okviru (glob-rule za Dockerfile), pa Dockerfile iz laba 08 provodimo kroz hadolint i Trivy i verifikujemo da nema HIGH/CRITICAL nalaza.

**Pretpostavke za potvrdu:**
- Lab `08-lab-kontejnerizuj-app` je završen — postoje `Dockerfile` i `docker-compose.yml`
- Pročitani moduli `01`–`07` ove oblasti (best practices, bezbednost)
- Postoji `CLAUDE.md` u korenu radnog repoa sa `## Project-A workflow` sekcijom

**Van opsega:**
- Ne menjamo docker-compose.yml niti CI pipeline ovde
- Ne radimo K8s deployment — samo lokalni Docker build i smoke test

**Prompt za diskusiju:**
```
Radim Docker oblast u project-A. Kontekst je u CLAUDE.md (sekcija ## Project-A workflow).
Da li mi treba posebna CLAUDE.md sekcija ili .claude/rules/ fajl za Docker validaciju,
ili je pokriveno postojećim pravilima? Predloži kao kandidat sa evidencijom i confidence,
bez automatskog kreiranja.
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Dockerfile prolazi hadolint bez rešivih grešaka i Trivy bez HIGH/CRITICAL nalaza; smoke test vraća HTTP 200.

**Fajlovi koji se diraju:**
- `Dockerfile`
- `.dockerignore` (ako ne postoji — kreirati)
- `CLAUDE.md` ili `.claude/rules/dockerfile-checks.md` (ako je odluka „dodaj")

**Fajlovi koji se NE diraju:**
- `docker-compose.yml` — nije predmet ove vežbe
- Aplikacijski kod — samo Dockerfile i build config

**AI okvir za ovu oblast:**

Dodaj sekciju `## Docker validation checklist` u `CLAUDE.md`, ili napravi `.claude/rules/dockerfile-checks.md`

Sadržaj pravila:
```
- Pinuj verziju base image-a (nginx:1.25.3-alpine, ne :latest).
- Multi-stage build gde se kompajlira (Go/Node) → final image bez build alata.
- Ne pokreći kao root gde nije nužno; USER direktiva po potrebi.
- .dockerignore postoji i isključuje .git i .env fajlove.
- Bez secrets u layer-ima — koristi --mount=type=secret.
- HEALTHCHECK ili health endpoint za K8s liveness probe.
```

Anti-sprawl: Docker se ponavlja kroz module 01, 13 i 28 — minimalan dodatak je opravdan. Ako je pokriveno postojećim pravilima, zapiši odluku i preskoči kreiranje.

**Acceptance criteria:**
- [ ] Odluka o artefaktu doneta i zapisana u `.claude/memory/decisions.md` ili `CLAUDE.md`
- [ ] `docker run --rm -i hadolint/hadolint < Dockerfile` — nula rešivih grešaka
- [ ] `trivy image --severity HIGH,CRITICAL helloworld:local` — nula rešivih nalaza
- [ ] `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080` vraća `200`
- [ ] Sync zapisan u `.claude/memory/decisions.md` ili `CLAUDE.md ## Decision log`

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Donosim odluku o dockerfile-checks artefaktu
- Pokrećem hadolint, popravljam nalaze, rebuildujem
- Pokrećem Trivy scan
- Smoke test: docker run, curl 8080, docker rm

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Lint sa hadolint:

```bash
docker run --rm -i hadolint/hadolint < Dockerfile
```

> **Podman alternativa:** `podman run --rm -i hadolint/hadolint < Dockerfile`

Tipični nalazi: `DL3006 Always tag the version of an image explicitly`, `DL3025 Use arguments JSON notation for CMD and ENTRYPOINT`. Popravi po checklist-i iz AI okvira.

Build i scan sa Trivy:

```bash
docker build -t helloworld:local .
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image --severity HIGH,CRITICAL helloworld:local
```

> **Podman alternativa:** zameni socket sa `/run/user/$(id -u)/podman/podman.sock:/var/run/docker.sock`

Smoke test:

```bash
docker run -d --name hw -p 8080:80 helloworld:local
curl -o /dev/null -s -w "%{http_code}\n" http://localhost:8080
docker rm -f hw
```

Ako hadolint ili Trivy prijavi nalaz koji ne razumeš:

```
hadolint daje [nalaz] na ovom Dockerfile-u:
[sadržaj]
Objasni pravilo, zašto je bitno za produkciju, i minimalan fix.
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- hadolint bez rešivih grešaka
- trivy --severity HIGH,CRITICAL bez rešivih nalaza
- smoke test vraća 200
- sync zapisan u .claude/memory/decisions.md ili CLAUDE.md

Evo outputa:
[ovde lepiš hadolint output, trivy output, curl output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `docker run --rm -i hadolint/hadolint < Dockerfile` | Terminalni izlaz ne sadrži linije koje počinju sa `DL` ili `SC` |
| 2 | Pokreni `trivy image --severity HIGH,CRITICAL helloworld:local` | Tabela rezultata prikazuje 0 HIGH i 0 CRITICAL ranjivosti |
| 3 | Pokreni `docker run -d --name hw -p 8080:80 helloworld:local && curl -s -o /dev/null -w "%{http_code}" http://localhost:8080` | Shell ispisuje `200` |
| 4 | Pokreni `docker rm -f hw` i potom `docker ps -a \| grep hw` | Nema izlaza — kontejner je uklonjen |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Docker sync (oblast 01)
- Urađeno: dockerfile-checks rule dodat / ili: odlučeno bez dodatka jer ...
- Naučeno: hadolint + trivy kao Docker validacija u project-a-workflow
- Šta bi promenio:
```
