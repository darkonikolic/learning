# 07 — Vežba: priprema AI-okvira i sync (deployment strategije)

Pripremaš AI-okvir za rolling/canary/blue-green deploy, pa verifikuješ rollout i rollback.

## Cilj

- okvir koji pokriva strategije izdavanja sa zdravstvenim signalima i rollback-om
- dokazano: rollout uspeva, a rollback vraća prethodnu verziju

## Deo A — Priprema AI-okvira za deploy

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| K8s/CI checklist | da | `k8s-manifest-checks`, `gitlab-ci-checks` |
| Metrike za canary | da | `observability-checks` (oblast 11) |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: proširi postojeća pravila stavkom „svaki deploy ima definisan health gate i rollback put"; po potrebi povezati canary sa SLO metrikama. Bez novog rule-a ako pokrivaju.

### A3 — Minimalni dodatak (primer)

```
# dopuna deploy/CI checks
- Svaki deploy ima readiness gate; CI čeka `rollout status` pre nego što nastavi.
- Canary: promovisati tek ako error-rate/latency metrike ostaju u SLO.
- Definisan i testiran rollback (prethodni revision/image tag).
```

## Deo B — Praktičan rad (sync)

### Rollout i rollback

```bash
kubectl rollout status deployment/<ime> --timeout=120s
kubectl rollout history deployment/<ime>
kubectl rollout undo deployment/<ime>     # rollback test
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `rollout status` uspeva u zadatom timeout-u
- [ ] canary se promoviše samo uz zdrave metrike
- [ ] `rollout undo` dokazano vraća prethodnu verziju
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Hoću canary deploy za [servis] sa promocijom na osnovu error-rate/latency.
Predloži strategiju (manifesti + CI koraci) i siguran rollback.
```
