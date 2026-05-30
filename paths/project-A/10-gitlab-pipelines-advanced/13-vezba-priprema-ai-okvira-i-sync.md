# 13 — Vežba: priprema AI-okvira i sync (napredni pipeline-i)

Pripremaš AI-okvir za napredne GitLab pipeline-e (review apps, matrice, multi-stage), pa validiraš tok.

## Cilj

- okvir koji pokriva napredne CI obrasce (DAG `needs`, child pipelines, review apps)
- pipeline koji prolazi lint i ima ispravan tok zavisnosti

## Deo A — Priprema AI-okvira za napredni CI

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| CI checklist | da | `gitlab-ci-checks` (oblast 02) |
| Review apps / ephemeral env | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: proširi `gitlab-ci-checks` stavkama za review apps (dynamic environment, `on_stop`, auto-cleanup) umesto novog rule-a.

### A3 — Minimalni dodatak (primer)

```
# dopuna gitlab-ci-checks (advanced)
- Review app ima `environment.on_stop` i `auto_stop_in` (cleanup).
- Skupe faze (build/test) koriste `needs:` (DAG), ne čekaju ceo stage.
- Child pipeline-i za nezavisne servise umesto monolitnog joba.
```

## Deo B — Praktičan rad (sync)

### Validacija pipeline-a

```bash
glab ci lint
# vizuelno: CI/CD → Pipelines → DAG view (proveri needs/zavisnosti)
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `glab ci lint` prolazi
- [ ] review app se kreira i `on_stop` čisti okruženje
- [ ] `needs:` DAG smanjuje vreme pipeline-a
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Hoću review app po merge request-u sa auto-cleanup.
Daj minimalan `.gitlab-ci.yml` blok (environment + on_stop + auto_stop_in)
i objasni kako se čisti.
```
