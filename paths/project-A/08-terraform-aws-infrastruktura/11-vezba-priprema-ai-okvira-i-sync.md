# 11 — Vežba: priprema AI-okvira i sync (Terraform na AWS)

Pripremaš AI-okvir za AWS infrastrukturu kao kod, pa validiraš plan i sigurnost.

## Cilj

- okvir koji pokriva AWS Terraform module i bezbednosni scan
- `plan` bez iznenađenja i čist security scan pre `apply`

## Deo A — Priprema AI-okvira za Terraform/AWS

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Terraform checklist | da | `terraform-checks` (oblast 05) |
| AWS security scan | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: proširi `terraform-checks` AWS-specifičnim stavkama (enkripcija, public access, security group pravila) umesto novog rule-a. Dodaj samo ako postojeći ne pokriva.

### A3 — Minimalni dodatak (primer)

```
# dopuna terraform-checks (AWS)
- S3/EBS/RDS enkripcija uključena; bez public read.
- Security group: bez 0.0.0.0/0 na 22/3306 osim kroz bastion/SSM.
- IAM role po servisu, ne deljeni admin.
```

## Deo B — Praktičan rad (sync)

### Plan + security scan

```bash
terraform plan -out=tfplan
docker run --rm -v "$PWD":/src bridgecrew/checkov -d /src
# ili: tfsec /src
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `terraform plan` pregledan (create/change/destroy svesno)
- [ ] `checkov`/`tfsec` bez high/critical nalaza (ili svesno suppress sa razlogom)
- [ ] nema public exposure neželjenih resursa
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
checkov/tfsec prijavljuje:
[nalaz]
Evo modula:
[.tf]
Da li je nalaz realan rizik ovde i koji je minimalan fix bez rušenja arhitekture?
```
