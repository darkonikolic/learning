# 07 — Vežba: priprema AI-okvira i sync (Secrets Manager)

Pripremaš AI-okvir za upravljanje tajnama (AWS Secrets Manager), pa validiraš da nigde nema plaintext secrets.

## Cilj

- okvir koji forsira „nema secrets u kodu" i sync iz SM u runtime
- dokazano: repo je čist od tajni, aplikacija čita iz SM-a

## Deo A — Priprema AI-okvira za secrets

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Terraform/secrets checklist | delom | `terraform-checks` |
| Secret scanning | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat rule `secrets-hygiene` (zabrana plaintext tajni u commit-u; reference na SM ARN; rotacija). Uvedi — rizik curenja je visok i ponavlja se kroz oblasti.

### A3 — Minimalni dodatak (primer)

```
# kandidat: secrets-hygiene
- Nikad plaintext secret u repo (kod, .tfvars, compose, manifesti).
- App dobija tajne preko SM/External Secrets u runtime-u, ne build-time.
- Predvideti rotaciju (rotation lambda ili managed rotation).
```

## Deo B — Praktičan rad (sync)

### Scan i provera sync-a

```bash
docker run --rm -v "$PWD":/repo zricethezav/gitleaks detect --source=/repo
aws secretsmanager get-secret-value --secret-id <ime> --query SecretString
# u K8s: proveri da External Secrets kreira Secret bez plaintext-a u manifestu
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `gitleaks` ne nalazi tajne u repou
- [ ] aplikacija čita iz SM-a u runtime-u
- [ ] plan rotacije postoji
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Hoću da [servis] u Kubernetes-u dobija lozinke iz AWS Secrets Manager-a
bez plaintext-a u manifestima. Predloži pristup (External Secrets Operator)
i objasni rotaciju.
```
