# 04 — k6 u GitLab CI

## Osnovna integracija

Performance test na staging okruženju, trigerovan nakon deploy job-a.

```yaml
# .gitlab-ci.yml (dodaj u postojeći pipeline)

stages:
  - build
  - test
  - deploy
  - verify      # nova faza — post-deploy validation

# ... postojeći jobs ...

performance:staging:
  stage: verify
  needs:
    - job: deploy:staging
      artifacts: false
  image: grafana/k6:0.49.0
  variables:
    BASE_URL: "https://app.staging.firma.com"
    K6_TEST: "tests/performance/load-test.js"
  script:
    - k6 run
        --env BASE_URL=${BASE_URL}
        --out json=k6-results.json
        --summary-export=k6-summary.json
        ${K6_TEST}
  artifacts:
    when: always    # čuvaj rezultate i kad test faila
    paths:
      - k6-results.json
      - k6-summary.json
    reports:
      dotenv: k6-summary.json   # opcionalno — expose kao CI varijable
    expire_in: 2 weeks
  allow_failure: true   # ne blokiraj deploy — samo upozori
  environment:
    name: staging
  tags:
    - docker
```

---

## Threshold koji blokira pipeline

Kad hoćeš da performance regresija blokira deploy:

```javascript
// tests/performance/ci-smoke.js
// Brz test — 2 minute, 20 VU — za svaki MR
import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL } from './helpers/config.js';

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m',  target: 20 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    // Ovi thresholds FAILAJU CI (exit code 1 → job red)
    http_req_duration: ['p(95)<500'],         // strožije: 500ms za CI smoke
    http_req_failed:   ['rate<0.05'],         // 5% error rate je neprihvatljivo
    checks:            ['rate>0.95'],          // 95% check-ova mora proći
  },
};

export default function () {
  // Samo kritični endpointi za smoke test
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, { 'health up': (r) => r.status === 200 });

  const loginRes = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email: 'test@firma.com', password: 'TestPass123!' }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(loginRes, {
    'login ok': (r) => r.status === 200,
    'has token': (r) => r.json('access_token') !== undefined,
  });

  sleep(1);
}
```

```yaml
# Job koji BLOKIRA pipeline
performance:smoke:blocking:
  stage: verify
  needs: [deploy:staging]
  image: grafana/k6:0.49.0
  script:
    - k6 run
        --env BASE_URL=https://app.staging.firma.com
        tests/performance/ci-smoke.js
  # allow_failure: false  ← default, ne treba pisati
  # Ako k6 exit code 1 (threshold fail) → job red → pipeline blokiran
```

---

## Kompletan pipeline s performance testovima

```yaml
# .gitlab-ci.yml — relevantna sekcija

# Definišemo reusable k6 job template
.k6_base:
  image: grafana/k6:0.49.0
  artifacts:
    when: always
    paths: [k6-*.json]
    expire_in: 2 weeks

performance:smoke:
  extends: .k6_base
  stage: verify
  needs: [deploy:staging]
  script:
    - k6 run
        --env BASE_URL=${STAGING_URL}
        --out json=k6-smoke.json
        tests/performance/ci-smoke.js
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

performance:load:
  extends: .k6_base
  stage: verify
  needs: [deploy:staging]
  script:
    - k6 run
        --env BASE_URL=${STAGING_URL}
        --out json=k6-load.json
        tests/performance/load-test.js
  allow_failure: true   # informativno, ne blokira
  rules:
    - if: $CI_COMMIT_BRANCH == "main"   # samo na main push

performance:report:
  stage: verify
  needs:
    - job: performance:smoke
      artifacts: true
    - job: performance:load
      artifacts: true
  image: python:3.11-slim
  script:
    - pip install jq-python 2>/dev/null || true
    # Parsira k6 JSON i pravi human-readable summary
    - |
      python3 - <<'EOF'
      import json, sys

      with open('k6-smoke.json') as f:
          data = json.load(f)

      metrics = data.get('metrics', {})
      p95 = metrics.get('http_req_duration', {}).get('values', {}).get('p(95)', 'N/A')
      fail_rate = metrics.get('http_req_failed', {}).get('values', {}).get('rate', 'N/A')

      print(f"=== Performance Summary ===")
      print(f"p95 latency:  {p95:.1f}ms" if isinstance(p95, float) else f"p95 latency:  {p95}")
      print(f"Error rate:   {fail_rate:.4%}" if isinstance(fail_rate, float) else f"Error rate:   {fail_rate}")

      if isinstance(p95, float) and p95 > 300:
          print("WARNING: p95 latency exceeds 300ms SLO")
          sys.exit(1)
      EOF
  allow_failure: true
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## k6 rezultati u Prometheus

Integriraj k6 metrike s postojećim Prometheus + Grafana stack-om:

```yaml
# docker-compose.override.yml — lokalni razvoj
services:
  k6:
    image: grafana/k6:0.49.0
    depends_on:
      - prometheus
    command: >
      run
      --out experimental-prometheus-rw=http://prometheus:9090/api/v1/write
      --env BASE_URL=http://nginx:80
      /tests/load-test.js
    volumes:
      - ./tests:/tests
    networks:
      - project-a
    environment:
      K6_PROMETHEUS_RW_SERVER_URL: http://prometheus:9090/api/v1/write
```

```yaml
# Za k6 → Prometheus remote write, prometheus.yml mora imati:
# remote_write:
#   - url: 'http://prometheus:9090/api/v1/write'
#
# I treba biti pokrenut s --web.enable-remote-write-receiver flag-om
```

**Grafana k6 dashboard:** Importaj dashboard ID `2587` iz Grafana.com — "k6 Load Testing Results".

---

## CI environment varijable za k6

```yaml
# GitLab → Settings → CI/CD → Variables

STAGING_URL:       https://app.staging.firma.com   # protected, not masked
PERF_TEST_EMAIL:   test@firma.com                   # test korisnik
PERF_TEST_PASS:    TestPass123!                     # masked, protected
K6_CLOUD_TOKEN:    (opcionalno, za k6 Cloud)
```

```javascript
// Korišćenje u skripti:
const loginRes = http.post(
  `${__ENV.BASE_URL}/api/auth/login`,
  JSON.stringify({
    email: __ENV.PERF_TEST_EMAIL || 'test@firma.com',
    password: __ENV.PERF_TEST_PASS || 'TestPass123!',
  }),
  { headers: { 'Content-Type': 'application/json' } }
);
```

---

## Kad koristiti lokalno vs CI

| Scenarij | Lokalno | CI (staging) |
|----------|---------|--------------|
| Razvijanje k6 skripte | Da | Ne |
| Brza validacija novog endpointa | Da | Opcionalno |
| Smoke test na svakom MR | Ne | Da |
| Load test na main push | Ne | Da |
| Stress/spike test (planiran) | Ne | Da (ručni trigger) |
| Soak test (24h) | Ne | Da (scheduled pipeline) |

```yaml
# Scheduled soak test — GitLab CI scheduled pipelines
performance:soak:
  stage: verify
  image: grafana/k6:0.49.0
  script:
    - k6 run
        --env BASE_URL=${STAGING_URL}
        tests/performance/soak-test.js
  allow_failure: true
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
      variables:
        K6_TEST_TYPE: "soak"
  timeout: 26h   # malo više od 24h testa
```
