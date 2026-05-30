# 09 — Vežba: priprema AI-okvira i sync (Terraform)

Pripremaš AI-okvir za Terraform, pa validiraš lokalnu konfiguraciju iz oblasti.

## Cilj

- okvir koji pokriva pisanje/validaciju Terraform koda
- konfiguracija koja prolazi `fmt`, `validate` i čist `tflint`

## Deo A — Priprema AI-okvira za Terraform

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DevOps persona | da | `/devops-engineer` |
| Terraform checklist | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: glob-rule za `**/*.tf` (remote state, varijable bez default-a za secrets, tagovi, pinovane verzije provider-a). Terraform se ponavlja (05, 08, 14, 15) → opravdano.

### A3 — Minimalni dodatak (primer)

```
# .cursor/rules/terraform-checks.mdc — globs: paths/project-A/**/*.tf
- required_version i required_providers pinovani.
- Nema secrets u .tf/.tfvars commit-ovanim u repo.
- Svaki resurs nosi standardne tagove (env, project, owner).
- State je remote (S3 + DynamoDB lock), ne lokalni.
```

## Deo B — Praktičan rad (sync)

### Validacija konfiguracije

```bash
terraform fmt -check -recursive
terraform validate
docker run --rm -v "$PWD":/data -t ghcr.io/terraform-linters/tflint
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `terraform fmt -check` čist
- [ ] `terraform validate` prolazi
- [ ] `tflint` bez warning-a
- [ ] nema secrets u kodu; verzije pinovane
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
terraform validate / tflint daje:
[greška]
Evo .tf koda:
[sadržaj]
Objasni uzrok i predloži minimalan ispravan oblik.
```
