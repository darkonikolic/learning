# 12 — Vežba: priprema AI-okvira i sync (graduation)

Završna vežba: konsoliduješ ceo AI-okvir izgrađen kroz oblasti 00–27 i voziš kompletan end-to-end tok kroz njega.

## Cilj

- jedan, konsolidovan i ne-naduvan AI-okvir za ceo project-a
- dokazano: ceo sistem prolazi end-to-end kroz `project-a-workflow` petlju

## Deo A — Konsolidacija AI-okvira

### A1 — Inventar

Izlistaj sva pravila/agente/skills uvedena kroz oblasti (dockerfile, ci, k8s, terraform, observability, security, secrets, test, migration, async, proto…).

### A2 — Odluka (anti-sprawl, finalno)

`/system-maintainer` + `process-feedback`: spoji preklapanja, obriši neiskorišćeno, potvrdi da svaki artefakt ima trigger i da se `project-a-workflow` poštuje na svakom modulu. Ovde dominira **čišćenje**, ne dodavanje.

### A3 — Finalni kriterijum

```
# konačni gate (ai-output-verification + workflow)
Nijedan artefakt ne ide u main bez: (1) domenske validacije svoje oblasti,
(2) prolaska kroz plan→diskusija→egzekucija→validacija→capture.
```

## Deo B — End-to-end (sync)

### Kompletan tok

```bash
docker compose up -d --build && docker compose ps     # ceo stack healthy
# CI: lint → test → security scan → build → deploy (review app)
glab ci lint
kubectl rollout status deployment/<app>
curl -fsS https://<host>/health                        # E2E smoke kroz LB+TLS
```

## Validacija — acceptance kriterijumi

- [ ] inventar okvira kompletan; nema dupliranih/neiskorišćenih pravila
- [ ] ceo stack se diže i E2E smoke prolazi
- [ ] CI lanac (lint→test→scan→deploy) zelen
- [ ] rollback dokazano radi
- [ ] svaki korak prošao `project-a-workflow` petlju
- [ ] finalni sync zapisan u `decision_log.md`

## AI workflow

```
Evo celog .cursor okvira i liste oblasti. Pre „diplome", proveri:
šta je suvišno/preklapa se, da li svaki artefakt ima validaciju,
i da li nešto u end-to-end toku nedostaje. Predloži, ne menjaj automatski.
```
