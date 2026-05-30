# 06 — Vežba: priprema AI-okvira i sync (performance testing)

Pripremaš AI-okvir za load testove (k6) i profiling, pa meriš prema definisanim pragovima.

## Cilj

- okvir koji povezuje load testove sa SLO pragovima i profiling-om uskih grla
- dokazano: test prolazi prag (npr. p95 latencija, error rate), bottleneck identifikovan

## Deo A — Priprema AI-okvira za performance

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DevOps/observability | da | `observability-checks` |
| Load test / profiling checklist | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat checklist-skill `perf-test-plan` (definiši SLO prag pre testa; realan profil opterećenja; profiling tek nakon merenja). Uvedi samo ako se merenja ponavljaju bez jasnih pragova.

### A3 — Minimalni dodatak (primer)

```
# kandidat: perf-test-plan
- Definiši prag PRE testa (p95 < Xms, error rate < Y%).
- Profil opterećenja realan (ramp-up, plato), ne samo max RPS.
- Profiling (pprof) tek kad test padne — meri, ne nagađaj.
```

## Deo B — Praktičan rad (sync)

### Load test i profiling

```bash
docker run --rm -i grafana/k6 run - < load.js     # k6 sa thresholds
# Go profiling kad padne prag:
go tool pprof http://<host>/debug/pprof/profile
```

## Validacija — acceptance kriterijumi

- [ ] (po potrebi) odluka A2 doneta preko `/system-maintainer`
- [ ] prag definisan pre testa (k6 `thresholds`)
- [ ] test prolazi prag ili je bottleneck jasno identifikovan
- [ ] profiling korišćen samo posle merenja
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Hoću k6 load test za [endpoint] sa pragom p95 < 200ms i error rate < 1%.
Daj skriptu sa thresholds i realnim ramp-up profilom; objasni kako da čitam rezultat.
```
