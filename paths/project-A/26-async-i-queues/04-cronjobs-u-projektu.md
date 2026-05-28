# 04 — CronJobovi u project-a

Svi K8s CronJobovi na jednom mjestu. Svaki koristi `restartPolicy: OnFailure`
i `concurrencyPolicy: Forbid` kako ne bi teklo više instanci istovremeno.

---

## 1. Cleanup expired tokens

Briše MySQL redove za neotvorene registracije starije od 24h.
Redis `verify:*` ključevi se automatski brišu TTL-om — ovdje čistimo samo MySQL.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-expired-tokens
  namespace: project-a-prod
spec:
  schedule: "*/30 * * * *"   # Svakih 30 minuta
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: cleanup
              image: registry.gitlab.com/user/project/go-service:v1.2.0
              command: ["/server", "cleanup", "expired-tokens"]
              env:
                - name: DB_DSN
                  valueFrom:
                    secretKeyRef:
                      name: db-credentials
                      key: dsn
              resources:
                requests:
                  cpu: 10m
                  memory: 32Mi
                limits:
                  cpu: 100m
                  memory: 64Mi
```

**Go handler za cleanup:**
```go
// cmd/cleanup/expired_tokens.go
func CleanupExpiredTokens(ctx context.Context, db *sql.DB) error {
    result, err := db.ExecContext(ctx, `
        DELETE FROM users
        WHERE email_verified_at IS NULL
          AND created_at < NOW() - INTERVAL 24 HOUR
    `)
    if err != nil {
        return fmt.Errorf("cleanup expired tokens: %w", err)
    }

    affected, _ := result.RowsAffected()
    log.Printf("Deleted %d unverified accounts", affected)
    return nil
}
```

---

## 2. Weekly DB backup

Backup MySQL baze na S3 svake nedjelje u 03:00 UTC.
Koristi replica host da ne opterećuje primary.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: weekly-db-backup
  namespace: project-a-prod
spec:
  schedule: "0 3 * * 0"        # Nedjelja 03:00 UTC
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 5
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          serviceAccountName: backup-sa   # IRSA: s3:PutObject na project-a-backups
          containers:
            - name: backup
              image: registry.gitlab.com/user/project/db-tools:latest
              # Bazira se na mysql:8.0 + aws-cli
              command:
                - /bin/sh
                - -c
                - |
                  set -e
                  FILENAME="weekly/$(date +%Y%m%d-%H%M%S).sql.gz"
                  echo "Starting backup: $FILENAME"
                  mysqldump \
                    -h "$DB_REPLICA_HOST" \
                    -u "$DB_USER" \
                    -p"$DB_PASS" \
                    --single-transaction \
                    --set-gtid-purged=OFF \
                    --databases project_a \
                  | gzip \
                  | aws s3 cp - "s3://project-a-backups/$FILENAME"
                  echo "Backup complete: $FILENAME"
              env:
                - name: DB_REPLICA_HOST
                  valueFrom:
                    secretKeyRef:
                      name: db-credentials
                      key: replica-host
                - name: DB_USER
                  valueFrom:
                    secretKeyRef:
                      name: db-credentials
                      key: username
                - name: DB_PASS
                  valueFrom:
                    secretKeyRef:
                      name: db-credentials
                      key: password
              resources:
                requests:
                  cpu: 100m
                  memory: 128Mi
                limits:
                  cpu: 500m
                  memory: 256Mi
```

---

## 3. Dead letter monitor

Svaki dan ujutro provjeri ima li poruka u dead letter queue-u i pošalji Slack alert.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: dead-letter-monitor
  namespace: project-a-prod
spec:
  schedule: "0 9 * * *"        # Svaki dan 09:00 UTC
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: monitor
              image: redis:7-alpine
              command:
                - /bin/sh
                - -c
                - |
                  set -e
                  COUNT=$(redis-cli -u "$REDIS_URL" XLEN queue:email:dead)
                  echo "Dead letter count: $COUNT"
                  if [ "$COUNT" -gt "0" ]; then
                    curl --fail -s -X POST \
                      -H 'Content-type: application/json' \
                      --data "{\"text\":\"Dead letter queue: $COUNT unprocessed emails in queue:email:dead\"}" \
                      "$SLACK_WEBHOOK"
                    echo "Slack alert sent"
                  else
                    echo "Dead letter queue is clean"
                  fi
              env:
                - name: REDIS_URL
                  valueFrom:
                    secretKeyRef:
                      name: redis-credentials
                      key: url
                - name: SLACK_WEBHOOK
                  valueFrom:
                    secretKeyRef:
                      name: slack-credentials
                      key: webhook-url
              resources:
                requests:
                  cpu: 10m
                  memory: 16Mi
                limits:
                  cpu: 50m
                  memory: 32Mi
```

---

## 4. Synthetic monitoring

Playwright scheduled testovi — pokriveno u modulu 24 (performance-testing).
CronJob tamo pokreće headless browser i verifikuje kritične korisničke tokove.

---

## Pregled svih CronJobova

| Naziv | Schedule | Što radi | Kritičnost |
|-------|----------|----------|------------|
| cleanup-expired-tokens | `*/30 * * * *` | Briše neotvorene registracije | Niska |
| weekly-db-backup | `0 3 * * 0` | MySQL backup na S3 | Visoka |
| dead-letter-monitor | `0 9 * * *` | Alert za zaglavljene emailove | Srednja |
| synthetic-monitor | `*/15 * * * *` | E2E smoke test | Visoka |

---

## CronJob troubleshooting

```bash
# Lista svih CronJobova i zadnji run
kubectl get cronjobs -n project-a-prod

# Zadnjih 5 Jobova (sortirano po vremenu)
kubectl get jobs -n project-a-prod \
  --sort-by=.metadata.creationTimestamp | tail -5

# Status konkretnog Joba
kubectl describe job weekly-db-backup-1705363200 -n project-a-prod

# Logovi konkretnog Joba
kubectl logs -n project-a-prod job/weekly-db-backup-1705363200

# Ručno pokreni CronJob (za testiranje)
kubectl create job --from=cronjob/dead-letter-monitor \
  dead-letter-monitor-manual -n project-a-prod

# Provjeri Events ako Job ne startuje
kubectl get events -n project-a-prod \
  --field-selector reason=FailedCreate | tail -10
```
