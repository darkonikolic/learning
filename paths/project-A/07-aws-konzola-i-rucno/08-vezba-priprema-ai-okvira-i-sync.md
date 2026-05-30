# 08 — Vežba: priprema AI-okvira i sync (ručno preko konzole)

Pripremaš AI-okvir koji te vodi kroz ručno pravljenje resursa u konzoli, pa verifikuješ rezultat CLI-jem.

## Cilj

- okvir koji vodi „ručno → razumevanje → kasnije Terraform" tok
- svaki ručno napravljen resurs verifikovan i dokumentovan za kasniji IaC

## Deo A — Priprema AI-okvira za ručni rad

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DevOps persona | da | `/devops-engineer` |
| „ručno pa IaC" princip | da | `00-orientation` + `project-a-workflow` |

### A2 — Odluka (anti-sprawl)

Najčešće **ništa novo** — ručni korak je za razumevanje. Eventualni dodatak: checklist-skill „šta zabeležiti o ručnom resursu da bi se kasnije preveo u Terraform". Uvedi samo ako se gubi trag konfiguracije.

### A3 — Minimalni dodatak (primer)

```
# kandidat: rucni-resurs-zapis (checklist)
Za svaki ručno kreiran resurs zabeleži: ID/ARN, region, ključne parametre,
zavisnosti, i mapiranje na budući Terraform resource tip.
```

## Deo B — Praktičan rad (sync)

### Verifikacija ručno kreiranog resursa

```bash
aws ec2 describe-instances --filters "Name=tag:Name,Values=<ime>"
aws ec2 describe-security-groups --group-ids <sg-id>
```

Zabeleži parametre po checklist-i da kasnija oblast 08 (Terraform) ima izvor istine.

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] resurs postoji i `describe-*` vraća očekivane parametre
- [ ] zapis parametara spreman za prevod u Terraform
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Napravio sam ručno [resurs] sa parametrima [...].
Koje parametre moram da zabeležim da bih ga kasnije verno opisao u Terraform-u?
```
