# 11 — Vežba: priprema AI-okvira i sync (RDS i ElastiCache)

Pripremaš AI-okvir za upravljane baze (RDS MySQL master/replica) i Redis (ElastiCache), pa validiraš konekciju i backup.

## Cilj

- okvir koji pokriva RDS/ElastiCache module i konekcionu higijenu
- dokazano: konekcija radi, backup/replica postoji, secrets nisu u kodu

## Deo A — Priprema AI-okvira za RDS/ElastiCache

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Terraform/AWS checklist | da | `terraform-checks` |
| DB konekcija/secrets | delom | (oblast 15 — SM) |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: proširi `terraform-checks` DB stavkama (enkripcija at-rest, automated backups, multi-AZ za prod, parametar grupe) umesto novog rule-a.

### A3 — Minimalni dodatak (primer)

```
# dopuna terraform-checks (data)
- RDS: storage_encrypted=true, backup_retention >= 7, deletion_protection u prod.
- Read replica definisana gde aplikacija čita više nego što piše.
- Lozinke iz Secrets Manager-a, ne u .tf/.tfvars.
```

## Deo B — Praktičan rad (sync)

### Validacija konekcije i backup-a

```bash
terraform plan
mysql -h <rds-endpoint> -u app -p -e "SELECT 1;"
aws rds describe-db-instances --query "DBInstances[].{id:DBInstanceIdentifier,backup:BackupRetentionPeriod,enc:StorageEncrypted}"
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] konekcija na master i replica radi
- [ ] enkripcija at-rest uključena, backup retention > 0
- [ ] kredencijali dolaze iz Secrets Manager-a (ne hardkodovani)
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Treba mi RDS MySQL master + read replica preko Terraform-a,
sa enkripcijom, backup-om i lozinkom iz Secrets Manager-a.
Daj modul i objasni replica/failover ponašanje.
```
