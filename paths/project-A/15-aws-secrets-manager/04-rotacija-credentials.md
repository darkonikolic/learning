# 04 — Rotacija credentials

## RDS MySQL — AWS managed rotation

AWS managed rotation za RDS funkcioniše putem Lambda funkcije koja:
1. Kreira novu verziju secretsa sa `AWSPENDING` label
2. Postavlja novi password direktno na RDS instancu (`ALTER USER`)
3. Testira konekciju sa novim passwordom
4. Premješta `AWSCURRENT` na novu verziju, staru na `AWSPREVIOUS`

```hcl
# Konfiguracija rotacije - detalji iz modula 03, ovdje fokus na MonitorING
resource "aws_cloudwatch_event_rule" "rotation_failure" {
  name        = "project-a-${var.environment}-rotation-failure"
  description = "Alert on SM rotation failure"

  event_pattern = jsonencode({
    source      = ["aws.secretsmanager"]
    detail-type = ["AWS API Call via CloudTrail"]
    detail = {
      eventSource = ["secretsmanager.amazonaws.com"]
      eventName   = ["RotationFailed"]
      requestParameters = {
        secretId = [{ prefix = "/project-a/${var.environment}/" }]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "rotation_failure_sns" {
  rule = aws_cloudwatch_event_rule.rotation_failure.name
  arn  = aws_sns_topic.alerts.arn
}

resource "aws_sns_topic_subscription" "rotation_failure_slack" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url  # Slack webhook za #ops-alerts
}
```

### Česta greška: Lambda i VPC

Rotation Lambda mora biti u istom VPC-u kao RDS i mora imati SG koji dozvoljava egress na port 3306. Također mora imati pristup SM endpoint-u — ili kroz internet (NAT Gateway) ili kroz VPC Interface Endpoint za SM:

```hcl
# VPC Endpoint za SM — eliminisati NAT dependency za rotation Lambda
resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.private_subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}
```

---

## Go service — bezšavna rotacija bez downtime

Go aplikacija koristi `database/sql` connection pool. Kada ESO ažurira K8s Secret i Reloader pokrene rolling restart, novi podovi dobijaju novi password. Problem je window između SM rotacije i pod restart-a.

### Pattern: Connection retry sa SM refresh

```go
// internal/database/pool.go

type DBPool struct {
    db           *sql.DB
    secretARN    string
    smClient     *secretsmanager.Client
    mu           sync.RWMutex
    lastRefresh  time.Time
    refreshEvery time.Duration
}

func (p *DBPool) getConnection(ctx context.Context) (*sql.Conn, error) {
    conn, err := p.db.Conn(ctx)
    if err == nil {
        return conn, nil
    }

    // Auth error → pokušaj refresh credentials
    if isAuthError(err) {
        if time.Since(p.lastRefresh) > 30*time.Second {
            // Throttle: ne refreshuj više od jednom/30s
            if refreshErr := p.refreshCredentials(ctx); refreshErr != nil {
                return nil, fmt.Errorf("auth error and refresh failed: %w", refreshErr)
            }
        }
        return p.db.Conn(ctx)
    }

    return nil, err
}

func isAuthError(err error) bool {
    var mysqlErr *mysql.MySQLError
    if errors.As(err, &mysqlErr) {
        return mysqlErr.Number == 1045  // Access denied for user
    }
    return false
}

func (p *DBPool) refreshCredentials(ctx context.Context) error {
    p.mu.Lock()
    defer p.mu.Unlock()

    result, err := p.smClient.GetSecretValue(ctx, &secretsmanager.GetSecretValueInput{
        SecretId: aws.String(p.secretARN),
    })
    if err != nil {
        return err
    }

    var creds DBCredentials
    if err := json.Unmarshal([]byte(*result.SecretString), &creds); err != nil {
        return err
    }

    dsn := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?parseTime=true&tls=true",
        creds.Username, creds.Password, creds.Host, creds.Port, creds.DBName)

    newDB, err := sql.Open("mysql", dsn)
    if err != nil {
        return err
    }

    oldDB := p.db
    p.db = newDB
    p.lastRefresh = time.Now()

    // Zatvoriti stari pool gracefully
    go func() {
        time.Sleep(30 * time.Second)
        oldDB.Close()
    }()

    return nil
}
```

Napomena: Ovaj pattern je za direktno SM čitanje iz aplikacije. Sa ESO pristupom (preporučen), aplikacija čita iz K8s Secret koji ESO ažurira — dovoljno je samo rolling restart konfigurisan putem Reloader controllera.

---

## Redis AUTH token rotacija — manual process

ElastiCache ne podržava AWS managed rotation. AUTH token rotacija je manual operacija.

### Problem: ElastiCache TOKEN_ROTATION

ElastiCache podržava **dva AUTH token-a simultano** za zero-downtime rotaciju:

```bash
# Korak 1: Dodati novi token uz stari (ElastiCache prihvata oba)
aws elasticache modify-replication-group \
    --replication-group-id project-a-prod-redis \
    --auth-token-update-strategy ROTATE \
    --auth-token "$NEW_TOKEN"
    --apply-immediately

# Korak 2: Ažurirati SM sa novim tokenom
aws secretsmanager put-secret-value \
    --secret-id /project-a/prod/redis/auth-token \
    --secret-string "$NEW_TOKEN"

# Korak 3: ESO osvježi K8s Secret (ili čekati refreshInterval)
# Force refresh:
kubectl annotate externalsecret redis-auth-token force-sync=$(date +%s) -n project-a

# Korak 4: Rolling restart podova koji koriste Redis
kubectl rollout restart deployment/go-service -n project-a
kubectl rollout status deployment/go-service -n project-a  # Pratiti

# Korak 5: Nakon što svi podovi koriste novi token, ukloniti stari
aws elasticache modify-replication-group \
    --replication-group-id project-a-prod-redis \
    --auth-token-update-strategy SET \  # SET = samo novi token
    --auth-token "$NEW_TOKEN" \
    --apply-immediately
```

### Automatizacija Redis rotacije — Lambda + EventBridge Scheduler

```hcl
resource "aws_scheduler_schedule" "redis_token_rotation" {
  name       = "project-a-${var.environment}-redis-rotation"
  group_name = "default"

  flexible_time_window {
    mode                      = "FLEXIBLE"
    maximum_window_in_minutes = 60
  }

  schedule_expression = "rate(30 days)"

  target {
    arn      = aws_lambda_function.redis_rotator.arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      secret_id          = "/project-a/${var.environment}/redis/auth-token"
      replication_group  = "project-a-${var.environment}-redis"
      deployment_name    = "go-service"
      namespace          = "project-a"
    })
  }
}
```

---

## GitLab credentials rotacija

### OIDC — nema rotacije (ephemeral tokens)

GitLab CI sa AWS OIDC integracija generiše privremene STS token-e za svaki job. Token živi samo za trajanje job-a (max 3600 sekundi). Nema ništa za rotirati.

```yaml
# .gitlab-ci.yml — OIDC pristup
assume-role:
  id_tokens:
    AWS_TOKEN:
      aud: sts.amazonaws.com
  script:
    - >
      export $(aws sts assume-role-with-web-identity
        --role-arn $AWS_ROLE_ARN
        --role-session-name gitlab-ci-${CI_JOB_ID}
        --web-identity-token $AWS_TOKEN
        --duration-seconds 3600
        | jq -r '.Credentials | "AWS_ACCESS_KEY_ID=\(.AccessKeyId)\nAWS_SECRET_ACCESS_KEY=\(.SecretAccessKey)\nAWS_SESSION_TOKEN=\(.SessionToken)"'
      )
```

### GitLab Registry Token rotacija

Container registry access token nije pokriven OIDC — treba periodičnu rotaciju:

```bash
#!/bin/bash
# scripts/rotate-gitlab-registry-token.sh
# Pokretati kao dio scheduled CI job-a ili Lambda

set -euo pipefail

GITLAB_API="https://gitlab.example.com/api/v4"
SECRET_PATH="/project-a/${ENVIRONMENT}/gitlab/registry-token"

# Kreirati novi token via GitLab API
NEW_TOKEN=$(curl -sf \
    -X POST \
    -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
    "$GITLAB_API/projects/$PROJECT_ID/access_tokens" \
    -d "name=registry-ci-$(date +%Y%m)" \
    -d "scopes[]=read_registry" \
    -d "scopes[]=write_registry" \
    -d "expires_at=$(date -d '+90 days' +%Y-%m-%d)" \
    | jq -r '.token')

# Ažurirati SM
aws secretsmanager put-secret-value \
    --secret-id "$SECRET_PATH" \
    --secret-string "{\"token\": \"$NEW_TOKEN\", \"rotated_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

# Revokovati stari token
# (Čuvati ID starog tokena u SM za revokaciju)
OLD_TOKEN_ID=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_PATH-metadata" \
    --query SecretString --output text | jq -r '.token_id')

curl -sf -X DELETE \
    -H "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
    "$GITLAB_API/projects/$PROJECT_ID/access_tokens/$OLD_TOKEN_ID"

echo "Registry token rotated successfully"
```

---

## Alerting na rotation failure

```hcl
# CloudWatch Alarm za neuspjelu rotaciju
resource "aws_cloudwatch_metric_alarm" "rotation_overdue" {
  alarm_name          = "project-a-${var.environment}-secret-rotation-overdue"
  alarm_description   = "SM secret has not been rotated within expected window"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ResourceCount"
  namespace           = "AWS/Config"
  period              = 86400  # Dnevna provjera
  statistic           = "Maximum"
  threshold           = 0

  # AWS Config rule koja prati rotation compliance
  dimensions = {
    ConfigRuleName = aws_config_config_rule.secrets_rotation.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_config_config_rule" "secrets_rotation" {
  name = "project-a-secrets-rotation-enabled"

  source {
    owner             = "AWS"
    source_identifier = "SECRETSMANAGER_ROTATION_ENABLED_CHECK"
  }

  scope {
    tag_key   = "ManagedBy"
    tag_value = "terraform"
  }
}
```

---

## Incident response — rotation failure runbook

Kada rotacija zakaže:

1. **Identifikovati razlog:** CloudWatch Logs za rotation Lambda  
   ```bash
   aws logs tail /aws/lambda/SecretsManagerRDSMySQLRotationSingleUser \
       --filter-pattern "ERROR" \
       --since 1h
   ```

2. **Najčešći razlozi i fix:**
   - `AWSPENDING` verzija nije kreirana → SM API permissions problema
   - Lambda ne može dostići RDS → SG ili subnet routing problem
   - RDS user nema GRANT privilege → kreirati user ručno i re-trigger rotaciju

3. **Prisilna rotacija:**
   ```bash
   aws secretsmanager rotate-secret \
       --secret-id /project-a/prod/rds/app-user-password \
       --rotate-immediately
   ```

4. **Emergency manual rotation:** Ako Lambda ne radi, promjeniti password direktno:
   ```bash
   # Direktno na RDS
   mysql -h $RDS_ENDPOINT -u admin -p"$MASTER_PASS" \
       -e "ALTER USER 'appuser'@'%' IDENTIFIED BY '$NEW_PASS';"
   
   # Ažurirati SM ručno
   aws secretsmanager put-secret-value \
       --secret-id /project-a/prod/rds/app-user-password \
       --secret-string "{...novi JSON...}"
   ```

5. **Post-rotation verifikacija:**
   ```bash
   # Test konekcija sa novim credentials
   mysql -h $RDS_ENDPOINT -u appuser -p"$NEW_PASS" $DB_NAME -e "SELECT 1;"
   
   # Provjera da ESO ažurira K8s Secret
   kubectl get externalsecret go-service-db-credentials -n project-a -o jsonpath='{.status.conditions}'
   ```
