# 08 — Vežba: priprema AI-okvira i sync (monitoring)

Pripremaš AI-okvir za Prometheus/Grafana/Loki, pa validiraš pravila i dashboard-e.

## Cilj

- okvir koji pokriva alert pravila, SLO/SLI i dashboard higijenu
- pravila i konfiguracije koje prolaze validaciju pre deploy-a

## Deo A — Priprema AI-okvira za monitoring

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DevOps persona | da | `/devops-engineer` |
| Alert/SLO checklist | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat rule `observability-checks` (svaki alert ima `for:`, severity, runbook link; dashboard ima jasne jedinice). Uvedi jer monitoring koristi i oblast 22 (deploy metrics).

### A3 — Minimalni dodatak (primer)

```
# kandidat: observability-checks
- Alert: ima `for:`, `severity`, i `annotations.runbook_url`.
- Bazirati alert na simptomu (SLO burn), ne na uzroku gde god je moguće.
- Dashboard panel: jedinice + opis; bez "magičnih" pragova bez objašnjenja.
```

## Deo B — Praktičan rad (sync)

### Validacija konfiguracije

```bash
promtool check rules rules/*.yml
promtool check config prometheus.yml
amtool check-config alertmanager.yml
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `promtool check rules/config` prolazi
- [ ] svaki alert ima `for:`, severity i runbook
- [ ] dashboard panel-i imaju jedinice i opis
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Hoću SLO-based alert za [servis] (npr. 99.9% dostupnost).
Daj Prometheus pravilo sa error-budget burn rate i objasni pragove.
```
