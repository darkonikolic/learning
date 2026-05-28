# RTO, RPO i DR koncepti

## Definicije

Ova dva pojma definišu koliko oporavak od incidenta smije koštati — u vremenu i u podacima.

```
RTO (Recovery Time Objective):
  Koliko DUGO smije trajati oporavak od incidenta?
  "Produkcija mora biti operativna za X sati/minuta od trenutka incidenta"
  Mjeri se: od trenutka incidenta do trenutka kada je sistem ponovo funkcionalan

RPO (Recovery Point Objective):
  Koliko podataka smijemo IZGUBITI?
  "Možemo prihvatiti gubitak podataka nastalih u posljednjih X sati/minuta"
  Mjeri se: od zadnjeg backup-a do trenutka incidenta
```

**Primjer:** Incident se desi u 14:00. Zadnji backup je bio u 13:55 (RPO = 5 min). Sistem je ponovo operativan u 14:30 (RTO = 30 min).

---

## Ciljevi za project-a

| Scenarij | RTO | RPO | Mehanizam oporavka |
|----------|-----|-----|-------------------|
| App crash (pod restart) | < 30s | 0 — nema gubitka | K8s self-healing, liveness probe |
| EKS node fail | < 2 min | 0 | K8s rescheduling na drugi node |
| AZ outage | < 5 min | 0 | Multi-AZ EKS + RDS automatic failover |
| Region outage | 2-4h | < 1h | Manual failover iz backup-a |
| Accidental data delete | 15-30 min | < 5 min | PITR restore na RDS |
| Total destroy + recreate | 35-40 min | Zadnji snapshot | `terraform apply` + `prod-resume.sh` |

**Napomena:** Za regionalni outage i total destroy, RTO/RPO vrijednosti pretpostavljaju da je recovery runbook testiran i tim zna korake.

---

## Šta određuje RTO za project-a

Svaki korak u oporavku ima trajanje. Zbroj svih koraka = ukupni RTO.

```
terraform apply (EKS + RDS + VPC + SGs):    ~15 minuta
helm deploy svih servisa:                    ~3 minuta
RDS restore iz snapshot-a:                  ~15 minuta
RDS PITR (Point-In-Time Recovery):          ~20 minuta
DNS propagacija:                             0 minuta (ALB URL je dinamički,
                                             ne mijenja se — nema DNS čekanja)

Ukupni RTO za total disaster (snapshot):    ~35 minuta
Ukupni RTO za total disaster (PITR):        ~40 minuta
```

**Šta usporava RTO:**
- Terraform state nije u S3 → ručna rekonstrukcija (sati)
- Helm values nisu u git-u → ručna konfiguracija (sati)
- Recovery runbook nije testiran → tim ne zna redosljed koraka (sati)
- RDS snapshot ne postoji → nemoguće, ili čekanje mysqldump (sati)

**Zaključak:** Infrastruktura-kao-kod (Terraform + Helm u git-u) je preduvjet za RTO od 35-40 minuta.

---

## Šta određuje RPO

RPO ovisi o tome koliko često pravimo backup i kakav backup.

```
RDS automated backup (PITR):
  Granularnost: 5 minuta (transaction log shipping)
  RPO = ~5 minuta
  Omogućeno: da, uz retention period = 7 dana

RDS manual snapshot (pre-deploy):
  Granularnost: ručno (samo kad pokrenemo)
  RPO = od trenutka zadnjeg ručnog snapshot-a
  Koristiti: uvijek prije schema migracija

mysqldump (weekly, za archival):
  Granularnost: sedmično
  RPO = do 7 dana gubitka podataka
  Koristiti: za long-term archival, ne za disaster recovery
```

**Za prod okruženje:** automated backup (PITR) daje RPO ~5 minuta. To je prihvatljivo za ovaj projekat.

---

## Multi-AZ vs Multi-Region

**Šta već imamo (Multi-AZ):**

```
EKS worker nodes:
  eu-west-1a — 1+ node
  eu-west-1b — 1+ node

RDS Multi-AZ:
  Primary:  eu-west-1a
  Standby:  eu-west-1b (synchronous replication)
  Failover: automatski, ~60 sekundi

Šta štiti od: jedan AWS AZ pada (struja, mrežni problem)
Koliko često: AZ outage se dešava, ali rijetko (jednom godišnje ili rjeđe)
```

**Šta nemamo (Multi-Region) i zašto:**

```
Multi-Region bi značilo:
  Replica u eu-central-1 (Frankfurt) ili us-east-1
  Read replica RDS u drugom regionu
  Route 53 health check + failover routing
  Cross-region S3 replication

Šta štiti od: cijeli AWS region pada (izuzetno rijetko)
Posljednji poznati primjer: us-east-1 parcijalni outage, 2021

Kompleksnost: 10x veća infrastruktura i operativni teret
Troškovi: ~2x (data transfer između regiona je skup)

Za project-a: nije opravdano u ovoj fazi.
  Multi-AZ je dovoljan za razumnu zaštitu.
  Multi-Region ako/kad regulatorni zahtjevi ili SLA to zahtijevaju.
```

---

## RDS Multi-AZ failover — šta se dešava

```
Normalni rad:
  Sve write operacije → Primary (eu-west-1a)
  Standby (eu-west-1b) je pasivan, synchrno repliciran

AZ outage ili Primary failure:
  RDS detektuje problem → automatski failover
  DNS endpoint (nije IP!) se preusmjeri na Standby
  Standby postaje novi Primary

Trajanje failover-a: ~30-120 sekundi
Gubitak podataka: 0 (synchronous replication)
Intervencija tima: nije potrebna

Aplikacija: koristi RDS endpoint (DNS), ne IP adresu.
  Kratkotrajni connection errors su normalni tokom failover-a.
  Connection pooler (PgBouncer/ProxySQL) ili retry logika u kodu apsorbuje ovo.
```

---

## Runbook za total disaster

Koristi kada je cijela produkciona infrastruktura nedostupna ili uništena.

```bash
# ==========================================
# TOTAL DISASTER RECOVERY RUNBOOK
# Trajanje: ~35-40 minuta
# Preduvjet: AWS credentials, terraform + helm na lokalnoj mašini
# ==========================================

# KORAK 1: Potvrdi da je disaster stvaran (ne paniči bez provjere)
aws eks describe-cluster --name project-a-prod --region eu-west-1
# Ako vidi "ResourceNotFoundException" ili timeout → disaster je potvrđen

# KORAK 2: Provjeri zadnji dostupni snapshot
aws rds describe-db-snapshots \
  --snapshot-type manual \
  --query 'sort_by(DBSnapshots,&SnapshotCreateTime)[-1].[DBSnapshotIdentifier,SnapshotCreateTime]' \
  --output text
# Zapamti DBSnapshotIdentifier (npr. "project-a-prod-pre-deploy-20240115")

# KORAK 3: Provjeri Terraform state (mora biti u S3)
aws s3 ls s3://project-a-terraform-state/
# Potvrdi da state fajl postoji

# KORAK 4: Pokreni recovery
cd terraform/environments/prod
terraform init
terraform apply -auto-approve
# Traje ~15 minuta

# KORAK 5: Restore database iz snapshot-a
bash scripts/prod-resume.sh project-a-prod-pre-deploy-20240115
# Ili za PITR (ako znaš tačno vrijeme do kog vraćaš):
bash scripts/prod-pitr-restore.sh "2024-01-15T13:55:00Z"

# KORAK 6: Deploy aplikacije
helm upgrade --install project-a ./charts/project-a \
  --namespace project-a-prod \
  --values values/prod.yaml \
  --set image.tag=$(git rev-parse --short HEAD)

# KORAK 7: Verifikacija
APP_URL=$(kubectl get ingress -n project-a-prod -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')
echo "App URL: https://$APP_URL"
curl -sf "https://$APP_URL/health" && echo "Health check PASSED" || echo "Health check FAILED"

# KORAK 8: Obavijesti tim i stakeholder-e
# Upiši u post-mortem: što se desilo, koliko je trajalo, šta poduzeti
```

---

## Testiranje disaster recovery-a

Disaster recovery koji nije testiran nije disaster recovery — to je nada.

**Preporučena učestalost:** jednom kvartalno u staging okruženju.

```bash
# DR test u staging-u (ne brisati prod!):
# 1. Uništi staging infrastrukturu
terraform destroy -target=module.eks -var-file=staging.tfvars

# 2. Pokreni recovery
bash scripts/staging-resume.sh <latest-snapshot>

# 3. Izmjeri stvarno trajanje — dokumentuj
# 4. Ažuriraj runbook ako su koraci promijenjeni

# Šta provjeri tokom DR testa:
# [ ] Terraform apply radi bez ručnih intervencija
# [ ] DB restore vraća tačne podatke
# [ ] Aplikacija se podiže i health check prolazi
# [ ] Login, kreiranje naloga, osnovne operacije rade
# [ ] Monitoring i alerting su funkcionalni
```

---

## Monitoring i alerting za incident detection

Recovery ne može početi dok se incident ne detektuje. MTTD (Mean Time To Detect) direktno utiče na efektivni RTO.

```yaml
# alertmanager rules
- alert: AppDown
  expr: up{job="project-a"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Project-A is down"
    description: "Start DR runbook: <link>"

- alert: DBConnectionFailed
  expr: db_connections_failed_total > 10
  for: 30s
  labels:
    severity: critical

- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 2m
  labels:
    severity: warning
```

---

## Checklist

- [ ] RDS automated backup uključen, retention = 7 dana
- [ ] Ručni snapshot se pravi prije svakog deploy-a s DB migracijama
- [ ] Terraform state je u S3 (ne lokalno)
- [ ] Recovery runbook je u git-u i ažuriran
- [ ] DR test odrađen u staging-u u posljednjih 90 dana
- [ ] Tim zna gdje je runbook i ima AWS credentials za emergency
- [ ] Alerting je konfigurisan za app down i DB failure
- [ ] RTO/RPO ciljevi su dokumentovani i komunicirani stakeholder-ima
