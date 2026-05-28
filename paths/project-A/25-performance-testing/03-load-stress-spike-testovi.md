# 03 — Load, Stress i Spike testovi

## Load test — 100 concurrent korisnika

Simulira normalan radni dan. Svi endpointi, realističan mix zahteva.

```javascript
// tests/performance/load-test.js
import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { getAuthToken } from './helpers/auth.js';
import { BASE_URL } from './helpers/config.js';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // ramp up
    { duration: '5m', target: 100 },   // steady state
    { duration: '2m', target: 0 },     // ramp down
  ],
  thresholds: {
    http_req_duration:               ['p(95)<500'],
    'http_req_duration{name:login}': ['p(95)<300'],
    'http_req_duration{name:health}':['p(99)<100'],
    http_req_failed:                  ['rate<0.001'],
    errors:                           ['rate<0.001'],
  },
};

export default function () {
  const token = getAuthToken();

  const authHeaders = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  };

  group('dashboard flow', () => {
    const dashRes = http.get(
      `${BASE_URL}/api/dashboard`,
      { ...authHeaders, tags: { name: 'dashboard' } }
    );
    check(dashRes, { 'dashboard 200': (r) => r.status === 200 });

    const usersRes = http.get(
      `${BASE_URL}/api/users?page=1&per_page=20`,
      { ...authHeaders, tags: { name: 'users-list' } }
    );
    check(usersRes, { 'users 200': (r) => r.status === 200 });

    errorRate.add(dashRes.status !== 200 || usersRes.status !== 200);
  });

  group('health check', () => {
    const healthRes = http.get(
      `${BASE_URL}/health`,
      { tags: { name: 'health' } }
    );
    check(healthRes, {
      'health 200': (r) => r.status === 200,
      'health fast': (r) => r.timings.duration < 100,
    });
  });

  sleep(1);
}
```

---

## Stress test — raste do pucanja

Cilj je naći tačku pucanja. `abortOnFail: true` zaustavlja test kad threshold pređe granicu.

```javascript
// tests/performance/stress-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { BASE_URL } from './helpers/config.js';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },    // normalno opterećenje
    { duration: '2m', target: 200 },    // 2x normalno
    { duration: '2m', target: 400 },    // 4x normalno
    { duration: '2m', target: 600 },    // 6x normalno
    { duration: '2m', target: 800 },    // 8x normalno — ovdje obično puca
    { duration: '2m', target: 1000 },   // fallback ako EKS skalira dobro
    { duration: '5m', target: 0 },      // cooldown — gledaj recovery
  ],
  thresholds: {
    // abortOnFail: test se zaustavlja i prijavljuje gdje je limit
    http_req_failed: [
      { threshold: 'rate<0.1', abortOnFail: true },
    ],
    http_req_duration: [
      { threshold: 'p(95)<2000', abortOnFail: true },   // 2s je "puklo"
    ],
  },
};

export default function () {
  const res = http.get(`${BASE_URL}/api/dashboard`, {
    headers: { 'Authorization': `Bearer ${__ENV.TEST_TOKEN}` },
  });

  const ok = check(res, {
    'not 5xx': (r) => r.status < 500,
    'response received': (r) => r.body.length > 0,
  });

  errorRate.add(!ok);
  sleep(0.5);   // agresivniji od load testa
}
```

**Šta gledaš u Grafana tokom stress testa:**

```
Korelacija metrika kad app počne pucati:
─────────────────────────────────────────────────────────────────
Ako pada MySQL:
  → go-service logs: "Error 1040: Too many connections"
  → mysql_global_status_threads_connected blizu max_connections (151 default)
  → Rješenje: povećaj max_connections ili connection pooling (pgbouncer za MySQL)

Ako pada PHP-FPM:
  → nginx access log: masivno 502 Bad Gateway
  → php-fpm status: active processes == pm.max_children
  → Rješenje: pm.max_children, ili horizontalni scale PHP podova

Ako pada Go service:
  → kubectl top pods: CPU 100% na go-service podovima
  → HPA event log: scale-up trigerovan ali treba 2-3 min
  → Rješenje: povećaj HPA min replicas, smanjimo CPU request/limit

Ako pada Redis:
  → go-service latency spike na svim read-heavy endpointima
  → redis INFO stats: rejected_connections > 0
  → Rješenje: povećaj maxclients, ili connection pool u Go kodu
```

---

## Spike test — Black Friday scenarij

Simulira iznenadni skok traffic-a. EKS HPA ne skalira instantno — interesantno je šta se dešava u tih 2-3 minute.

```javascript
// tests/performance/spike-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { BASE_URL } from './helpers/config.js';

const errorRate = new Rate('errors');
const recoveryTime = new Trend('recovery_time_ms');

export const options = {
  stages: [
    { duration: '2m',  target: 10  },   // normalan traffic
    { duration: '10s', target: 500 },   // iznenadan spike — 50x za 10 sekundi
    { duration: '3m',  target: 500 },   // spike se zadržava 3 minute
    { duration: '10s', target: 10  },   // pad nazad na normalno
    { duration: '5m',  target: 10  },   // provjera recovery — da li se app oporavila?
  ],
  // Ne failamo test — želimo vidjeti cijeli ciklus
  thresholds: {
    errors: ['rate<0.5'],   // dopuštamo do 50% error tokom spike-a
  },
};

let spikeStarted = false;
let spikeStartTime = 0;
let recovered = false;

export default function () {
  const startTime = Date.now();

  const res = http.get(`${BASE_URL}/health`);
  const ok = check(res, { 'health ok': (r) => r.status === 200 });

  // Bilježi moment recovery-a
  if (!ok && !spikeStarted) {
    spikeStarted = true;
    spikeStartTime = startTime;
  }
  if (spikeStarted && ok && !recovered) {
    recovered = true;
    recoveryTime.add(startTime - spikeStartTime);
  }

  errorRate.add(!ok);
  sleep(0.2);   // agresivno pooling tokom spike-a
}
```

**Šta analiziraš nakon spike testa:**

```
recovery_time_ms p95 = 127.3s → EKS HPA trebao 2+ minute za scale-up
→ Akcija: povećaj minReplicas s 2 na 4 u HPA konfiguraciji

Error rate tokom spike-a = 38%
→ Circuit breaker nije trigerovan — Go service je primao sve i failing
→ Akcija: implementiraj circuit breaker (golang.org/x/time/rate za rate limiting)

Error rate NAKON spike-a = 0.3% (ne 0%)
→ App se nije potpuno oporavila — some sessions/connections ostale u lošem stanju
→ Akcija: provjeri Redis connection pool reset, PHP-FPM graceful restart
```

---

## Soak test — 24h stability

```javascript
// tests/performance/soak-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';
import { BASE_URL } from './helpers/config.js';

// Trend kroz vrijeme — pratimo drift
const p95Trend = new Trend('p95_over_time');

export const options = {
  stages: [
    { duration: '5m',  target: 50 },    // ramp up
    { duration: '24h', target: 50 },    // steady state — 24 sata
    { duration: '5m',  target: 0 },     // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.001'],
  },
};

export default function () {
  const res = http.get(`${BASE_URL}/api/dashboard`, {
    headers: { 'Authorization': `Bearer ${__ENV.TEST_TOKEN}` },
  });

  check(res, { 'ok': (r) => r.status === 200 });
  p95Trend.add(res.timings.duration);

  sleep(1);
}
```

**Što tražiš u Grafana tokom soak testa:**

```
Go service:
  kubectl port-forward pod/go-service-xxx 6060:6060 &
  # Goroutine count svaki sat:
  watch -n 3600 'curl -s http://localhost:6060/debug/pprof/goroutine?debug=1 | head -5'
  # Ako broj raste: goroutine leak → provjeri HTTP handler context cancelation

PHP-FPM:
  # Memory per worker ne smije rasti
  kubectl exec php-xxx -- php -r "echo memory_get_peak_usage(true)/1024/1024 . 'MB';"

MySQL:
  # Provjeri InnoDB buffer pool hit rate svaki sat
  # Treba biti > 99%: (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests)

Redis:
  kubectl exec redis-xxx -- redis-cli INFO memory | grep used_memory_human
  # Memorija ne smije rasti ako cache pravilno expireuje
```

---

## Bottleneck identifikacija — decision tree

```
p95 latency visoka?
├── Da: http_req_waiting visok (TTFB)?
│   ├── Da: problem je server-side
│   │   ├── Go service: kubectl top pods → CPU? Memory?
│   │   ├── MySQL: SHOW PROCESSLIST; slow query log?
│   │   └── Redis: redis-cli SLOWLOG GET 10
│   └── Ne: problem je network/connection
│       ├── http_req_connecting visok → TCP connection pool exhausted
│       └── http_req_tls_handshaking visok → TLS overhead (keepalive?)
│
└── Ne: error rate visoka?
    ├── HTTP 502 → upstream service down (PHP-FPM workers exhausted)
    ├── HTTP 503 → EKS HPA nije stigao skalirati (circuit breaker)
    ├── HTTP 504 → timeout (DB query predugo traje)
    └── HTTP 429 → rate limiting trigerovan (naš vlastiti limit)
```
