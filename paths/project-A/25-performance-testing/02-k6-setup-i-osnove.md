# 02 — k6: Setup i osnove

## Pokretanje k6 kroz Docker

Nema instalacije. Koristiš `grafana/k6:0.49.0` image direktno:

```bash
# Osnovno pokretanje — čita skriptu sa stdin
docker run --rm -i grafana/k6:0.49.0 run - < test.js

# S environment varijablama i output-om
docker run --rm -i \
  -e BASE_URL=https://app.dev.firma.com \
  grafana/k6:0.49.0 run - < tests/performance/login.js

# S JSON output-om za analizu
docker run --rm -i \
  -e BASE_URL=https://app.staging.firma.com \
  grafana/k6:0.49.0 run \
  --out json=k6-results.json \
  - < tests/performance/login.js
```

**Napomena za lokalni docker-compose stack:** k6 container mora biti u istoj Docker mreži:

```bash
docker run --rm -i \
  --network project-a_default \
  -e BASE_URL=http://nginx:80 \
  grafana/k6:0.49.0 run - < tests/performance/login.js
```

---

## Struktura k6 skripte

```javascript
// tests/performance/login.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrike — pojavljuju se u output-u pored default-nih
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');

// Konfiguracija testa — stages i thresholds
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // ramp up: 0 → 10 VU
    { duration: '1m',  target: 10 },   // steady state: 10 VU kroz 1 minutu
    { duration: '30s', target: 0 },    // ramp down: 10 → 0 VU
  ],
  thresholds: {
    // Test FAILA (exit code 1) ako ovi uvjeti nisu ispunjeni
    http_req_duration: ['p(95)<300'],   // 95% zahteva < 300ms
    errors: ['rate<0.01'],              // error rate < 1%
    http_req_failed: ['rate<0.01'],     // HTTP failures < 1%
  },
};

// Glavna funkcija — svaki VU (Virtual User) izvršava ovo u loop-u
export default function () {
  const loginRes = http.post(
    `${__ENV.BASE_URL}/api/auth/login`,
    JSON.stringify({
      email: 'test@firma.com',
      password: 'TestPass123!',
    }),
    {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'login' },   // za grupiranje metrika u Grafana
    }
  );

  // check() vrača true/false i mjeri pass/fail rate
  const success = check(loginRes, {
    'status is 200':           (r) => r.status === 200,
    'has access_token':        (r) => r.json('access_token') !== undefined,
    'response time OK':        (r) => r.timings.duration < 300,
    'no error in body':        (r) => !r.json('error'),
  });

  errorRate.add(!success);
  loginDuration.add(loginRes.timings.duration);

  sleep(1);   // pauza između iteracija — simulira realnog korisnika
}
```

---

## Razumijevanje k6 metrika

Default metrike koje k6 uvijek mjeri:

| Metrika | Što mjeri | Naš threshold |
|---------|-----------|---------------|
| `http_req_duration` | Ukupno trajanje HTTP zahteva | p(95)<300ms (login) |
| `http_req_failed` | Rate zahteva koji su failed (4xx/5xx) | rate<0.01 |
| `http_reqs` | Ukupan broj zahteva (throughput) | — |
| `vus` | Trenutni broj Virtual Users | — |
| `vus_max` | Maksimalni broj VU u testu | — |
| `iterations` | Ukupan broj izvršenih iteracija | — |
| `data_received` | Primljeni podaci (bytes) | — |
| `data_sent` | Poslani podaci (bytes) | — |

`http_req_duration` komponente:
```
http_req_blocked    — čekanje na slobodan TCP connection
http_req_connecting — TCP handshake
http_req_tls_handshaking — TLS/SSL
http_req_sending    — slanje request body
http_req_waiting    — čekanje na prvi byte odgovora (TTFB)
http_req_receiving  — primanje response body
```

Za dijagnozu latency problema: ako je `http_req_waiting` visok → server spor, ako je `http_req_connecting` visok → network ili connection pool problem.

---

## Čitanje k6 output-a

```
     ✓ status is 200
     ✓ has access_token
     ✓ response time OK

     checks.........................: 99.87% ✓ 2996  ✗ 4
     data_received..................: 2.4 MB 38 kB/s
     data_sent......................: 456 kB 7.2 kB/s
     http_req_blocked...............: avg=2.1ms    min=1µs    med=3µs    max=1.2s    p(90)=5µs   p(95)=10µs
     http_req_connecting............: avg=89µs     min=0s     med=0s     max=1.2s    p(90)=0s    p(95)=0s
     http_req_duration..............: avg=87.3ms   min=42ms   med=75ms   max=892ms   p(90)=143ms p(95)=198ms ✓
   ✓ { expected_response:true }...: avg=86.9ms   min=42ms   med=74ms   max=892ms   p(90)=142ms p(95)=196ms
     http_req_failed................: 0.13%  ✓ 4     ✗ 2996
     http_req_receiving.............: avg=412µs    min=26µs   med=89µs   max=34ms    p(90)=1.1ms p(95)=2.3ms
     http_req_sending...............: avg=89µs     min=12µs   med=57µs   max=4.9ms   p(90)=168µs p(95)=241µs
     http_req_tls_handshaking.......: avg=1.7ms    min=0s     med=0s     max=1.2s    p(90)=0s    p(95)=0s
     http_req_waiting...............: avg=86.8ms   min=41ms   med=74ms   max=891ms   p(90)=141ms p(95)=194ms
     http_reqs......................: 3000   47.6/s
     iteration_duration.............: avg=1.09s    min=1.04s  med=1.08s  max=1.89s   p(90)=1.14s p(95)=1.19s
     iterations.....................: 3000   47.6/s
     vus............................: 5      min=5       max=10
     vus_max........................: 10     min=10      max=10

✓ means threshold passed (green in terminal)
✗ means threshold failed (red, exit code 1)
```

Ključni brojevi za naše SLO:
- `http_req_duration p(95)` — mora biti < 300ms za login
- `http_req_failed rate` — mora biti < 0.01 (1%)
- `checks` pass rate — treba biti > 99%

---

## Organizacija test fajlova

```
tests/
└── performance/
    ├── login.js           # Login flow test
    ├── dashboard.js       # Dashboard load test
    ├── health.js          # Health endpoint test
    ├── load-test.js       # Svi endpointi, normalno opterećenje
    ├── stress-test.js     # Raste do pucanja
    └── helpers/
        ├── auth.js        # Reusable login helper
        └── config.js      # Shared thresholds i konfiguracija
```

```javascript
// tests/performance/helpers/config.js
export const BASE_URL = __ENV.BASE_URL || 'http://localhost';

export const SLO_THRESHOLDS = {
  login: {
    http_req_duration: ['p(95)<300'],
    http_req_failed: ['rate<0.001'],
  },
  dashboard: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.001'],
  },
  health: {
    http_req_duration: ['p(99)<100'],
    http_req_failed: ['rate<0.0001'],
  },
};
```

```javascript
// tests/performance/helpers/auth.js
import http from 'k6/http';
import { BASE_URL } from './config.js';

export function getAuthToken() {
  const res = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email: 'test@firma.com', password: 'TestPass123!' }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  return res.json('access_token');
}
```
