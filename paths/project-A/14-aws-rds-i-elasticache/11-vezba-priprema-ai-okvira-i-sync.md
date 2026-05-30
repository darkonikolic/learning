# 11 — Vežba: AWS RDS i ElastiCache

Validiraš AI-okvir za upravljane baze podataka (RDS MySQL master/replica) i Redis (ElastiCache), i dokazuješ da konekcija radi isključivo kroz interni put, enkripcija je uključena, a kredencijali dolaze iz Secrets Manager-a.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Proširujemo postojeći `terraform-checks` rule DB stavkama za RDS i ElastiCache. Dokazujemo da konekcija na RDS ide kroz bastion ili interni VPC put (ne javni internet), da je ElastiCache dostupan samo iz app subneta, i da je enkripcija at-rest uključena.

**Pretpostavke za potvrdu:**
- `terraform-checks` rule već postoji iz prethodnih oblasti
- RDS instanca je already deployed ili se deploya u ovoj vežbi
- Bastion host ili SSM Session Manager je dostupan za interne konekcije
- AWS CLI je podešen sa ispravnim profilom i regionom

**Van opsega:**
- RDS Proxy podešavanje
- Aurora Serverless konfiguracija
- Cross-region replikacija

**Prompt za diskusiju:**
```
Treba mi RDS MySQL master + read replica preko Terraform-a,
sa enkripcijom, backup-om i lozinkom iz Secrets Manager-a.
Daj modul i objasni replica/failover ponašanje.
Potom objasni: zašto RDS ne sme biti javno dostupan,
i kako security group pravila enforces pristup samo iz app subneta.
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Proširiti `terraform-checks` za RDS/ElastiCache higijenu i dokazati da infrastruktura zadovoljava sigurnosne i dostupnost zahteve.

**Fajlovi koji se diraju:**
- `terraform/modules/rds/` — RDS modul sa enkripcijom, backup i replica
- `terraform/modules/elasticache/` — ElastiCache modul sa subnet group
- `CLAUDE.md` ili `.claude/rules/terraform-checks.md` — dopuna postojećeg rule-a

**Fajlovi koji se NE diraju:**
- `terraform/modules/vpc/` — mrežna konfiguracija se ne menja
- `terraform/modules/iam/` — IAM role ostaju neizmenjene
- Aplikacioni kod — ovo je isključivo infra vežba

**AI okvir za ovu oblast:**

ažuriraj sekciju u `CLAUDE.md` ili `.claude/rules/terraform-checks.md`

Sadržaj pravila:
```
# dopuna terraform-checks (data tier)
- RDS: storage_encrypted=true, backup_retention >= 7, deletion_protection u prod.
- RDS: publicly_accessible=false; pristup samo iz app security grupe.
- Read replica definisana gde aplikacija čita više nego što piše.
- ElastiCache: dostupan samo iz app subneta, ne iz javnih subneta.
- Lozinke iz Secrets Manager-a, ne u .tf/.tfvars fajlovima.
- Multi-AZ za produkcione RDS instance.
```

Anti-sprawl: ovo je dopuna `terraform-checks` koji postoji — ne pravi se novi rule.

**Acceptance criteria:**
- [ ] `terraform plan` završava bez grešaka
- [ ] Konekcija na RDS master ide kroz bastion ili SSM (ne javni internet)
- [ ] Konekcija na read replica radi odvojeno
- [ ] ElastiCache je dostupan samo iz app subneta (ne spolja)
- [ ] AWS Console potvrđuje: Storage encrypted = Yes za RDS
- [ ] `backup_retention_period` je >= 7 dana
- [ ] Kredencijali se čitaju iz Secrets Manager-a (nema hardkodovanih lozinki u .tf)
- [ ] Sync zapisan

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Dopuniti terraform-checks pravila za RDS i ElastiCache
2. Pokrenuti terraform plan
3. Konektovati se na RDS kroz bastion/SSM i potvrditi konekciju
4. Proveriti AWS Console za enkripciju i backup retention
5. Proveriti da ElastiCache nije dostupan van app subneta

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Validacija Terraform plana:

```bash
terraform plan
```

Konekcija na RDS kroz bastion host (ne direktno s javnog interneta):

```bash
# Kroz SSH tunel via bastion
ssh -L 3306:<rds-endpoint>:3306 ec2-user@<bastion-ip> -N &
mysql -h 127.0.0.1 -u app -p -e "SELECT 1;"

# Ili kroz AWS SSM Session Manager
aws ssm start-session --target <instance-id> \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{"host":["<rds-endpoint>"],"portNumber":["3306"],"localPortNumber":["3306"]}'
mysql -h 127.0.0.1 -u app -p -e "SELECT 1;"
```

Provera RDS konfiguracije u AWS CLI:

```bash
aws rds describe-db-instances \
  --query "DBInstances[].{id:DBInstanceIdentifier,backup:BackupRetentionPeriod,enc:StorageEncrypted,public:PubliclyAccessible,multiAZ:MultiAZ}"
```

Provera da kredencijali dolaze iz Secrets Manager-a (ne iz .tf fajlova):

```bash
grep -r "password" terraform/ --include="*.tf" | grep -v "secretsmanager"
# Rezultat treba biti prazan ili samo reference na SM
```

Provera ElastiCache subnet grupe:

```bash
aws elasticache describe-cache-subnet-groups \
  --query "CacheSubnetGroups[].{name:CacheSubnetGroupName,subnets:Subnets[].SubnetAvailabilityZone}"
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- terraform plan završava bez grešaka
- Konekcija na RDS ide kroz bastion/SSM (ne javni internet)
- Read replica konekcija radi
- ElastiCache nije dostupan van app subneta
- AWS Console: Storage encrypted = Yes
- backup_retention_period >= 7
- Nema hardkodovanih lozinki u .tf fajlovima

Evo outputa / diff-a / konfiguracije:
[ovde lepiš: terraform plan output, aws rds describe-db-instances output, grep rezultat za passwords, screenshot AWS Console enkripcija]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokušaj direktnu konekciju na RDS endpoint sa lokalnog računara (bez tunela) | Konekcija se odbija — RDS nije javno dostupan |
| 2 | Konektuj se na RDS kroz bastion ili SSM tunel, izvrši `SELECT 1` | Vraća `1` — konekcija radi internim putem |
| 3 | Konektuj se na read replica endpoint i izvrši `SHOW SLAVE STATUS\G` | Replikacija je aktivna i Seconds_Behind_Master je mali |
| 4 | Otvori AWS Console → RDS → DB instance → Configuration | Storage encrypted: Yes, Backup retention: ≥ 7 dana |
| 5 | Otvori AWS Console → ElastiCache → Subnet groups | Samo app subneti su navedeni, nema javnih subneta |
| 6 | Proveri AWS Secrets Manager → secret za DB lozinku postoji | Secret postoji i verzija je ažurna |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — RDS i ElastiCache sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
