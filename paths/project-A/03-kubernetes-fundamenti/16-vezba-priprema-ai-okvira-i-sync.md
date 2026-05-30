# 16 — Vežba: priprema AI-okvira i sync (Kubernetes)

Pripremaš AI-okvir za K8s manifeste, pa validiraš deployment na lokalni kind.

## Cilj

- okvir koji pokriva pisanje/validaciju K8s manifesta
- manifesti koji prolaze schema validaciju i server dry-run

## Deo A — Priprema AI-okvira za Kubernetes

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DevOps persona | da | `/devops-engineer` |
| Validacija manifesta | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: glob-rule za `**/k8s/**/*.yaml` (resource limits, probes, no `:latest`, securityContext) — K8s se ponavlja (03, 13, 16, 22) → opravdano.

### A3 — Minimalni dodatak (primer)

```
# .cursor/rules/k8s-manifest-checks.mdc
- Svaki kontejner ima resources.requests/limits.
- liveness + readiness probe definisani.
- Image tag pinovan (ne :latest).
- securityContext: runAsNonRoot gde je moguće.
```

## Deo B — Praktičan rad (sync)

### Validacija manifesta

```bash
# Schema validacija (offline)
docker run --rm -v "$PWD":/w ghcr.io/yannh/kubeconform:latest -strict /w/k8s/

# Server-side dry-run (validira protiv API-ja)
kubectl apply --dry-run=server -f k8s/
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `kubeconform -strict` bez grešaka
- [ ] `kubectl apply --dry-run=server` prolazi
- [ ] svi kontejneri imaju limite + probe
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
kubectl apply --dry-run=server daje:
[greška]
Evo manifesta:
[sadržaj]
Šta je pogrešno i koji je minimalan ispravan oblik?
```
