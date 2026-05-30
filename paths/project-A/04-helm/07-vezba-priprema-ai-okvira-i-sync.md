# 07 — Vežba: priprema AI-okvira i sync (Helm)

Pripremaš AI-okvir za Helm chart-ove, pa validiraš `helloworld` chart iz ove oblasti.

## Cilj

- okvir koji pokriva pisanje/validaciju Helm chart-ova
- chart koji prolazi `helm lint` i renderuje validne manifeste po okruženju

## Deo A — Priprema AI-okvira za Helm

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DevOps persona | da | `/devops-engineer` |
| Helm/templating checklist | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: da li proširiti `k8s-manifest-checks` na Helm (values po okruženju, `_helpers.tpl`, bez hardkodovanih vrednosti) ili dodati zaseban rule. Helm se ponavlja (04, 13, 22) → minimalan dodatak.

### A3 — Minimalni dodatak (primer)

```
# dopuna pravila za templates/*.yaml
- Vrednosti dolaze iz values/<env>.yaml, ne hardkodovane u template.
- Svaki resurs koristi `{{ include "...labels" . }}` iz _helpers.tpl.
- resources/probes parametrizovani po okruženju.
```

## Deo B — Praktičan rad (sync)

### Validacija chart-a (`helloworld` referenca iz oblasti)

```bash
helm lint helloworld -f helloworld/values/dev.yaml
helm template helloworld -f helloworld/values/prod.yaml | kubectl apply --dry-run=server -f -
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `helm lint` bez grešaka za svako okruženje
- [ ] `helm template | kubectl --dry-run=server` prolazi
- [ ] nema hardkodovanih vrednosti u template-ima
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
helm lint prijavljuje:
[greška]
Evo template-a i values:
[sadržaj]
Koja vrednost nedostaje i kako da je parametrizujem po okruženju?
```
