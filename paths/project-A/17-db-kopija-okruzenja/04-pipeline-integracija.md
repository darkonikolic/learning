# 04 — Pipeline integracija

## Arhitektura pipeline db operacija

```
[Scheduled: 02:00 UTC daily]
    └── db:dump-prod
            └── upload latest.sql.gz → S3

[Feature branch push]
    └── (nema db operacija)

[Merge u main → deploy dev]
    └── tf-apply:dev
    └── deploy:dev
    └── db:restore-dev    ← depends_on oba
    └── db:migrate-dev

[Review app kreiranje]
    └── tf-apply:review-$CI_MERGE_REQUEST_IID
    └── deploy:review
    └── db:restore-review ← automatski
    └── db:migrate-review
```

---

## Job: dump prod baze

```yaml
db:dump-prod:
  stage: db-ops
  image: amazon/aws-cli:latest
  when: manual
  environment:
    name: production
  variables:
    DUMP_FILE: "db-dumps/prod_$(date +%Y%m%d_%H%M).sql.gz"
    DUMP_LATEST: "db-dumps/latest.sql.gz"
  before_script:
    - yum install -y docker  # ili: koristi service mysql:8.0 i mysql klijent direktno
  script:
    # Dump iz read replica (ne mastera!), gzip, upload na S3
    - |
      docker run --rm mysql:8.0 mysqldump \
        -h "$RDS_READ_REPLICA_ENDPOINT" \
        -u admin \
        -p"$DB_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --add-drop-table \
        --set-gtid-purged=OFF \
        --column-statistics=0 \
        project_a \
        | gzip -9 \
        | aws s3 cp - "s3://$STATE_BUCKET/$DUMP_FILE"
    # Kopiraj kao latest (overwrite)
    - aws s3 cp "s3://$STATE_BUCKET/$DUMP_FILE" "s3://$STATE_BUCKET/$DUMP_LATEST"
    # Provjeri integritet
    - aws s3 cp "s3://$STATE_BUCKET/$DUMP_LATEST" - | gzip -t && echo "Dump OK"
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_PIPELINE_SOURCE == "web"  # manuelni trigger
  tags:
    - aws-runner  # runner koji ima AWS IAM pristup
```

### Zašto `when: manual` i scheduled?

`when: manual` znači da se job ne pokreće automatski pri svakom puhu — prod dump je destruktivna operacija u smislu S3 state-a (overwrite latest). Svakodnevni automatic dump ide kroz Scheduled Pipeline, ne kroz manuelni trigger u normalnom flow-u.

---

## Job: restore dump u env

```yaml
.db-restore-template: &db-restore
  image: amazon/aws-cli:latest
  stage: post-deploy
  script:
    - |
      aws s3 cp s3://$STATE_BUCKET/db-dumps/latest.sql.gz - \
        | gunzip \
        | docker run --rm -i mysql:8.0 mysql \
            -h "$TARGET_RDS_ENDPOINT" \
            -u admin \
            -p"$DB_PASSWORD" \
            --init-command="SET foreign_key_checks=0; SET unique_checks=0;" \
            project_a
    - echo "Restore complete, running migrations..."
    - $MIGRATION_COMMAND

db:restore-dev:
  <<: *db-restore
  needs:
    - job: tf-apply:dev
      artifacts: true
    - job: deploy:dev
  variables:
    TARGET_RDS_ENDPOINT: $RDS_DEV_ENDPOINT
    MIGRATION_COMMAND: "php artisan migrate --force"
  environment:
    name: dev
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

db:restore-staging:
  <<: *db-restore
  needs:
    - job: tf-apply:staging
      artifacts: true
    - job: deploy:staging
  variables:
    TARGET_RDS_ENDPOINT: $RDS_STAGING_ENDPOINT
    MIGRATION_COMMAND: "php artisan migrate --force"
  environment:
    name: staging
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  when: manual  # staging restore je manuelni korak — ne želi svaki deploy pobisat staging podatke
```

### `needs` vs `dependencies`

`needs` definira DAG zavisnosti — job čeka da navedeni jobovi završe. `artifacts: true` znači da job prima output artifakte od prethodnih jobova (npr. Terraform output sa RDS endpoint-om).

Bez `needs`, restore job može startati dok Terraform još nije kreirao RDS instancu.

---

## Review app restore

```yaml
db:restore-review:
  <<: *db-restore
  needs:
    - job: tf-apply:review
      artifacts: true
    - job: deploy:review
  variables:
    TARGET_RDS_ENDPOINT: $REVIEW_RDS_ENDPOINT  # iz tf-apply:review artifacts
    MIGRATION_COMMAND: "php artisan migrate --force"
  environment:
    name: review/$CI_MERGE_REQUEST_IID
    url: https://review-$CI_MERGE_REQUEST_IID.project-a.dev
    on_stop: cleanup:review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Review app dobiva svježu kopiju prod baze automatski pri kreiranju. Developer odmah ima realne podatke za testiranje promjena.

---

## Scheduled Pipeline konfiguracija

U GitLab UI: **CI/CD → Schedules → New schedule**

```
Description: Daily prod DB dump
Cron: 0 2 * * *      ← 02:00 UTC svaki dan
Timezone: UTC
Branch: main
Variables:
  CI_PIPELINE_SOURCE: schedule  ← trigger rule za dump job
```

Pipeline koji se kreira kroz schedule pokrenut će sve jobove čija je `rules` konfiguracija:
```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "schedule"
```

Ostali jobovi (build, deploy, test) koji nemaju ovo pravilo neće se pokretati — scheduled pipeline pokreće samo dump job.

---

## Expert gotcha: dump ne smije blokirati prod

Ponavljamo jer je kritično: `--single-transaction` sprječava table lock-ove, **ali**:

### Problem s long-running transakcijama

mysqldump otvara jednu veliku transakciju koja traje koliko i cijeli dump. Tokom te transakcije, InnoDB **ne može purgirati undo log** za verzije redova koje ta transakcija koristi. Za veliku bazu s visokim write rate-om, ovo može prouzrokovati:

- Rast undo tablespace-a (historia list length raste)
- Degradaciju performance-a na prod jer InnoDB mora traversirati dužu undo chain za svaki read
- `ibdata1` rast koji se ne može shrinkati bez rebuild-a baze

**Rješenje:** pokretanje na read replica:

```
mysqldump → RDS Read Replica (ne master)
```

Read replica ima vlastiti InnoDB engine. Long-running transakcija na replici utječe samo na repliku, ne na master. Jedini side effect je **replication lag** — replika može zaostajati za masterom dok dump traje.

### Monitoring replication lag tokom dump-a

```sql
-- Na read replici, tokom dump-a:
SHOW REPLICA STATUS\G
-- Gledaj: Seconds_Behind_Source

-- Ili via CloudWatch metrika:
-- RDS → ReplicaLag (sekunde)
```

Ako lag postane prevelik (> 60 sekundi), dump treba pauzirati ili smanjiti throughput. Za projekt-A (mala baza), ovo nije problem — dump traje < 2 minuta pa lag ostaje zanemariv.

### `--max-allowed-packet` za veliku bazu

Za baze sa BLOB/TEXT kolonama sa velikim podacima:

```bash
mysqldump \
  --max-allowed-packet=512M \  # default je 24MB — premalo za large BLOBs
  ...
```

Bez ovoga, dump može pucati sa `ERROR 1153 (08S01): Got a packet bigger than 'max_allowed_packet' bytes`.

---

## Artefakt propagacija između jobova

Terraform apply job treba eksportovati RDS endpoint kao artifact:

```yaml
tf-apply:dev:
  script:
    - terraform apply -auto-approve
    - terraform output -raw rds_endpoint > rds_endpoint.txt
  artifacts:
    reports: {}
    paths:
      - rds_endpoint.txt
    expire_in: 1 hour
```

Restore job koristi taj artefakt:

```yaml
db:restore-dev:
  needs:
    - job: tf-apply:dev
      artifacts: true
  script:
    - export TARGET_RDS_ENDPOINT=$(cat rds_endpoint.txt)
    - ...
```

Alternativa: GitLab environment variables u Terraform — Terraform API poziv koji setuje `RDS_DEV_ENDPOINT` variablu direktno u GitLab env. Čistije od artefakata, ali zahtijeva GitLab API token u Terraform konfiguraciji.

---

## Pipeline security: zaštita dump job-a

Dump job ima pristup prod bazi i S3 bucket-u s osjetljivim podacima. Zaštitni slojevi:

1. **Protected branch:** `rules` ograničava dump job na `main` branch koji je protected
2. **Protected variables:** `DB_PASSWORD`, `RDS_READ_REPLICA_ENDPOINT` su marked as "Protected" u GitLab — vidljive samo u protected branch pipeline-ima
3. **IAM least privilege:** CI runner IAM role ima samo `s3:PutObject` na specifični S3 prefix, ne `s3:*`
4. **Manual trigger za prod:** `when: manual` zahtijeva da developer eksplicitno pokrene dump, ne događa se automatski pri svakom deployu

```yaml
# IAM policy za CI runner (Terraform)
resource "aws_iam_policy" "ci_db_dump" {
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject", "s3:GetObject"]
      Resource = "arn:aws:s3:::${var.state_bucket}/db-dumps/*"
    }]
  })
}
```
