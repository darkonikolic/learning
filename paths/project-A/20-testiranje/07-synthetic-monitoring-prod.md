# 07 — Synthetic monitoring za produkciju

## Deploy E2E vs synthetic monitoring: ključna razlika

```
Deploy pipeline E2E                    Synthetic monitoring
─────────────────────────────────      ──────────────────────────────────
Pokreće se: pri svakom deployu         Pokreće se: svakih 15 minuta (cron)
Cilj: blokira loš deployment           Cilj: detektuje degradaciju u prod
Okruženje: review app / staging        Okruženje: PRODUKCIJA
Failure: MR ne može biti mergean       Failure: Slack/PagerDuty alert
Trajanje: 5-10 minuta                  Trajanje: 2-3 minute (samo smoke)
Testovi: happy path + edge cases       Testovi: samo kritični happy path
Upravljanje: deploy tim                Upravljanje: on-call tim
```

Deploy E2E testira: "je li ovaj kod siguran za deployment?"
Synthetic monitoring testira: "radi li produkcija u ovom trenutku?"

Ovo su različita pitanja koja zahtijevaju različite alate i odgovore. Pomiješati ih (npr. koristiti deploy E2E za prod monitoring) znači: ili blokiraš produkcioni deployment svaki put kad je prod down, ili ne testiraš produkciju dovoljno.

---

## GitLab Scheduled Pipeline

GitLab CI → Schedules → New schedule:

```
Description:  Synthetic monitoring - svakih 15 minuta
Interval:     */15 * * * *
Branch:       main
Variables:
  SYNTHETIC_MONITORING: "true"
  APP_URL: "https://app.firma.com"
  MONITORING_ENV: "production"
```

```yaml
# .gitlab-ci.yml — dodatni job koji se pokreće SAMO u scheduled pipeline-u

synthetic:monitoring:
  stage: test
  image: mcr.microsoft.com/playwright:v1.42.0-jammy
  variables:
    APP_URL: "https://app.firma.com"
    E2E_PROD_EMAIL: $SYNTHETIC_MONITOR_EMAIL      # masked CI/CD variable
    E2E_PROD_PASSWORD: $SYNTHETIC_MONITOR_PASSWORD  # masked CI/CD variable
    CI: "true"
  script:
    - cd tests/e2e
    - npm ci --prefer-offline  # koristiti npm cache, ne preuzimati svaki put
    - npx playwright test --grep @smoke --reporter=junit,list
  after_script:
    # Obavijesti Slack/PagerDuty ako je job pao
    - |
      if [ $CI_JOB_STATUS = "failed" ]; then
        curl -X POST $SLACK_WEBHOOK_URL \
          -H 'Content-type: application/json' \
          --data "{\"text\":\"PROD ALERT: Synthetic monitoring failed. Pipeline: $CI_PIPELINE_URL\"}"
      fi
  artifacts:
    when: always
    reports:
      junit: tests/e2e/junit.xml
    paths:
      - tests/e2e/playwright-report/
    expire_in: 3 days
  rules:
    # Pokreće se SAMO u scheduled pipeline-u s ovom varijablom
    - if: $SYNTHETIC_MONITORING == "true"
```

`--grep @smoke` — Playwright filter koji pokreće samo testove označene s `@smoke` tagom. Ovi testovi su minimalni (login + health check), ne cijeli E2E suite.

---

## Smoke testovi za produkciju (`@smoke`)

```typescript
// tests/smoke/production.spec.ts

import { test, expect } from '@playwright/test';

// @smoke tag — ovi testovi se pokreću u synthetic monitoring
test('@smoke login flow', async ({ page }) => {
  const start = Date.now();
  
  await page.goto('/');
  await page.fill('[data-testid="email"]', process.env.E2E_PROD_EMAIL!);
  await page.fill('[data-testid="password"]', process.env.E2E_PROD_PASSWORD!);
  await page.click('[data-testid="login-button"]');
  
  await expect(page.locator('[data-testid="welcome-message"]'))
    .toContainText('Hello World', { timeout: 10000 });
  
  const responseTime = Date.now() - start;
  
  // Response time threshold: ako traje dulje od 2 sekunde, nešto nije u redu
  expect(responseTime).toBeLessThan(2000);
  console.log(`Login flow completed in ${responseTime}ms`);
});

test('@smoke health endpoints are responding', async ({ request }) => {
  // Go service health endpoint
  const goHealth = await request.get(`${process.env.APP_URL}/api/health`);
  expect(goHealth.status()).toBe(200);
  
  const goBody = await goHealth.json();
  expect(goBody.status).toBe('ok');
  expect(goBody.mysql).toBe('connected');
  expect(goBody.redis).toBe('connected');
  
  // PHP service health (ako postoji zasebni health endpoint)
  const phpHealth = await request.get(`${process.env.APP_URL}/health`);
  expect(phpHealth.status()).toBe(200);
});

test('@smoke login response time under threshold', async ({ request }) => {
  const start = Date.now();
  
  const response = await request.post(`${process.env.APP_URL}/api/auth/login`, {
    data: {
      email: process.env.E2E_PROD_EMAIL,
      password: process.env.E2E_PROD_PASSWORD,
    },
  });
  
  const duration = Date.now() - start;
  
  expect(response.status()).toBe(200);
  
  // P95 threshold za produkcijski login
  expect(duration).toBeLessThan(2000);
  
  console.log(`API login response time: ${duration}ms`);
});
```

Smoke testovi su namjerno minimalni. Ne testiraju edge case-ove. Ne testiraju validation. Testiraju samo: "je li kritični happy path end-to-end funkcionalan u ovom trenutku?"

---

## Zasebni test korisnik za produkciju

```sql
-- Jednom pri prod bootstrap (ne u migraciji, u ručnom provisioning script-u)
-- Email domena koja nikad neće biti pravi korisnik
INSERT INTO users (
  email,
  password_hash,
  is_test_account,
  created_at,
  email_verified_at  -- ako postoji email verification, pre-verify
) VALUES (
  'synthetic@monitor.internal',
  '$2y$12$...',  -- bcrypt hash, generiran jednom i sačuvan u secrets manageru
  true,
  NOW(),
  NOW()
);

-- Test account nema permisije pristupa pravim podacima
-- Limitiran je na "hello world" feature koji synthetic test verificira
INSERT INTO user_roles (user_id, role)
SELECT id, 'synthetic_monitor'
FROM users
WHERE email = 'synthetic@monitor.internal';
```

Zašto zasebni korisnik:
1. Password nikad ne ističe (nema account expiry policy za service account)
2. Audit log ne miješa test akcije s pravim korisničkim akcijama
3. Rate limiting se može exemptovati za ovaj specifični account
4. Account se može lako identificirati i ukloniti

### Čišćenje test data iz produkcije

Synthetic monitoring korisnik generiše sesije, logove, eventualno test narudžbe ili sl. Ovo treba čistiti:

```sql
-- Cron job koji se pokreće svaki sat (Kubernetes CronJob ili RDS event scheduler)
-- Briše sve sesije synthetic monitoring korisnika starije od 2 sata
DELETE FROM sessions
WHERE user_id IN (
  SELECT id FROM users WHERE is_test_account = true
)
AND created_at < NOW() - INTERVAL 2 HOUR;

-- Briše sve akcije (audit log) synthetic monitoring korisnika
DELETE FROM audit_log
WHERE user_id IN (
  SELECT id FROM users WHERE is_test_account = true
)
AND created_at < NOW() - INTERVAL 24 HOUR;
```

```yaml
# k8s/cronjob-cleanup-test-data.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-synthetic-test-data
  namespace: production
spec:
  schedule: "0 * * * *"  # svaki sat
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: cleanup
              image: mysql:8.0
              command:
                - /bin/sh
                - -c
                - |
                  mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME \
                    -e "DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE is_test_account = true) AND created_at < NOW() - INTERVAL 2 HOUR;"
              envFrom:
                - secretRef:
                    name: db-credentials
          restartPolicy: OnFailure
```

---

## Alertmanager integracija

Scheduled pipeline failure automatski triggeruje alert. Postoje dva pristupa:

### Direktno iz pipeline-a (simple)

```yaml
# U after_script synthetic monitoring job-a (vidi gore)
after_script:
  - |
    if [ "$CI_JOB_STATUS" = "failed" ]; then
      curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-type: application/json' \
        --data "{
          \"text\": \"PROD DOWN\",
          \"attachments\": [{
            \"color\": \"danger\",
            \"text\": \"Synthetic monitoring failed.\nPipeline: $CI_PIPELINE_URL\nJob: $CI_JOB_URL\nTime: $(date -u)\"
          }]
        }"
    fi
```

### Kroz Prometheus + Alertmanager (napredni)

GitLab eksponira pipeline status kao metric. Prometheus scrape-a GitLab API, Alertmanager šalje notifikacije.

```yaml
# prometheus/rules/gitlab-synthetic.yml
groups:
  - name: synthetic-monitoring
    rules:
      - alert: SyntheticMonitoringFailed
        expr: |
          gitlab_ci_pipeline_status{
            project="firma/app",
            ref="main",
            source="schedule"
          } == 0
        for: 5m  # Čekaj 5 minuta (može biti lažni alarm pri jednom fail-u)
        labels:
          severity: critical
          team: on-call
        annotations:
          summary: "Synthetic monitoring je pao"
          description: "GitLab scheduled pipeline za produkcijsko monitoring je pao {{ $value }} puta u zadnjih 5 minuta"
          runbook_url: "https://wiki.firma.com/runbooks/synthetic-monitoring"
          dashboard_url: "https://grafana.firma.com/d/synthetic-monitoring"
```

```yaml
# alertmanager/config.yml
route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1h
  receiver: 'slack-critical'
  routes:
    - match:
        severity: critical
      receiver: pagerduty-oncall

receivers:
  - name: slack-critical
    slack_configs:
      - api_url: $SLACK_WEBHOOK_URL
        channel: '#prod-alerts'
        title: 'PROD ALERT: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: pagerduty-oncall
    pagerduty_configs:
      - routing_key: $PAGERDUTY_KEY
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
```

---

## SSL certifikat expiry monitoring

SSL expiry nije samo "upozorenje" — expired cert = produkcija je down za sve korisnike.

```typescript
// tests/smoke/ssl.spec.ts

test('@smoke ssl certificate valid and not expiring soon', async ({ request }) => {
  // Playwright/Node.js ne eksponira cert info direktno
  // Koristimo shell comandu ili zasebni check
  
  // Alternativno: provjeri kroz API endpoint koji eksponuje cert info
  const response = await request.get(`${process.env.APP_URL}/api/health/ssl`);
  expect(response.status()).toBe(200);
  
  const body = await response.json();
  expect(body.ssl_valid).toBe(true);
  
  // Expiry ne smije biti unutar 30 dana
  const expiryDate = new Date(body.ssl_expires_at);
  const now = new Date();
  const daysUntilExpiry = Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  
  console.log(`SSL cert expires in ${daysUntilExpiry} days (${body.ssl_expires_at})`);
  
  // Warning threshold: 30 dana
  if (daysUntilExpiry < 30) {
    console.warn(`WARNING: SSL cert expires in ${daysUntilExpiry} days!`);
  }
  
  // Hard failure: 7 dana ili manje
  expect(daysUntilExpiry).toBeGreaterThan(7);
});
```

Go health endpoint koji vraća SSL info:

```go
// handlers/health.go
func HealthHandler(w http.ResponseWriter, r *http.Request) {
    // Provjeri MySQL
    mysqlOK := db.Ping() == nil
    
    // Provjeri Redis
    redisOK := rdb.Ping(context.Background()).Err() == nil
    
    // SSL cert expiry
    certs, err := tls.LoadX509KeyPair(certFile, keyFile)
    var sslExpiresAt time.Time
    if err == nil && len(certs.Certificate) > 0 {
        cert, _ := x509.ParseCertificate(certs.Certificate[0])
        sslExpiresAt = cert.NotAfter
    }
    
    status := map[string]interface{}{
        "status":          "ok",
        "mysql":           map[string]bool{"connected": mysqlOK}["connected"],
        "redis":           map[string]bool{"connected": redisOK}["connected"],
        "ssl_valid":       err == nil,
        "ssl_expires_at":  sslExpiresAt.Format(time.RFC3339),
    }
    
    statusCode := http.StatusOK
    if !mysqlOK || !redisOK {
        status["status"] = "degraded"
        statusCode = http.StatusServiceUnavailable
    }
    
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(statusCode)
    json.NewEncoder(w).Encode(status)
}
```

---

## Pregled: šta synthetic monitoring pokriva

| Check | Frekvencija | Threshold | Alert ako |
|-------|------------|-----------|-----------|
| Login happy path | 15 min | < 2s | padne 2x zaredom |
| Go health endpoint | 15 min | HTTP 200 | pade |
| MySQL connectivity | 15 min | connected | pade |
| Redis connectivity | 15 min | connected | pade |
| Login API response time | 15 min | < 2s | > 2s dva puta |
| SSL cert expiry | svaki sat | > 30 dana | < 30 dana (warning), < 7 dana (critical) |

Synthetic monitoring nije zamjena za application metrics (Prometheus + Grafana). To je vanjska provjera: "može li pravi korisnik koristiti aplikaciju u ovom trenutku?" dok metrics govore "šta se dešava unutar aplikacije".

Idealno: i jedno i drugo. Monitoring kao slojevita odbrana.
