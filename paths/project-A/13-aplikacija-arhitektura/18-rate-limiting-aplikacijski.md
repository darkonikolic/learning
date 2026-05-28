# 18 — Rate Limiting: Aplikacijski nivo

## Zašto Nginx rate limiting nije dovoljan

Nginx (modul 01) radi rate limiting po IP adresi. Problem:

```
Korporativni NAT: 500 korisnika → isti javni IP
Nginx vidi: "IP 203.0.113.50 prešao limit"
Rezultat:   500 korisnika ne mogu se prijaviti

Ispravno:   Rate limit po user ID (JWT sub claim)
            Svaki korisnik ima vlastiti brojaš, neovisno o IP-u
```

Drugi problem: Nginx ne poznaje poslovnu logiku. Ne zna da `/api/auth/forgot-password`
treba stroži limit od `/api/users/profile`.

---

## Go middleware za rate limiting po korisniku

```go
// middleware/ratelimit/ratelimit.go
package ratelimit

import (
    "context"
    "fmt"
    "math"
    "net/http"
    "strconv"
    "time"

    "github.com/redis/go-redis/v9"
)

// RateLimit definira limit za jedan endpoint ili grupu endpointova.
type RateLimit struct {
    Requests int
    Window   time.Duration
}

// Konfiguracija limita po putu. Najduži prefix pobjeđuje (longest prefix match).
var defaultLimits = map[string]RateLimit{
    "/api/auth/login":            {Requests: 5, Window: 10 * time.Minute},
    "/api/auth/register":         {Requests: 3, Window: time.Hour},
    "/api/auth/resend-verify":    {Requests: 3, Window: time.Hour},
    "/api/auth/forgot-password":  {Requests: 3, Window: time.Hour},
    "/api/auth/reset-password":   {Requests: 5, Window: time.Hour},
    "/api/":                      {Requests: 100, Window: time.Minute}, // Default za sve ostale
}

// Limiter drži Redis klijenta i konfiguraciju.
type Limiter struct {
    redis  *redis.Client
    limits map[string]RateLimit
}

// New kreira novi Limiter.
func New(redisClient *redis.Client) *Limiter {
    return &Limiter{
        redis:  redisClient,
        limits: defaultLimits,
    }
}

// Middleware vraća http.Handler koji provjerava rate limit.
func (l *Limiter) Middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        identifier, identifierType := l.getIdentifier(r)
        limit := l.getLimitForPath(r.URL.Path)
        key := fmt.Sprintf("ratelimit:%s:%s", r.URL.Path, identifier)

        count, err := l.redis.Incr(r.Context(), key).Result()
        if err != nil {
            // Redis greška → fail open (propusti zahtjev)
            // Logiraj ali ne blokiraj — dostupnost > zaštita u ovom slučaju
            next.ServeHTTP(w, r)
            return
        }

        // Postavi TTL samo na prvi zahtjev (Incr je atomičan)
        if count == 1 {
            l.redis.Expire(r.Context(), key, limit.Window)
        }

        remaining := int(math.Max(0, float64(limit.Requests-int(count))))
        resetTime := time.Now().Add(limit.Window).Unix()

        // Standard rate limit headers (RFC 6585 + industry praksa)
        w.Header().Set("X-RateLimit-Limit",     strconv.Itoa(limit.Requests))
        w.Header().Set("X-RateLimit-Remaining", strconv.Itoa(remaining))
        w.Header().Set("X-RateLimit-Reset",     strconv.FormatInt(resetTime, 10))

        if int(count) > limit.Requests {
            w.Header().Set("Retry-After", strconv.Itoa(int(limit.Window.Seconds())))
            w.Header().Set("Content-Type", "application/json")
            w.WriteHeader(http.StatusTooManyRequests)
            fmt.Fprintf(w, `{"error":"rate_limit_exceeded","message":"Previše zahtjeva. Pričekaj %ds.","retry_after":%d}`,
                int(limit.Window.Seconds()),
                int(limit.Window.Seconds()),
            )

            // Prometheus counter (definisan u metrics.go)
            rateLimitHitsTotal.WithLabelValues(r.URL.Path, identifierType).Inc()
            return
        }

        next.ServeHTTP(w, r)
    })
}

// getIdentifier vraća identifikator za rate limiting i tip identifikatora.
// Prioritet: JWT user ID > X-Real-IP header > RemoteAddr
func (l *Limiter) getIdentifier(r *http.Request) (identifier, identifierType string) {
    // JWT user ID je injectovan od auth middlewarea u context
    if userID, ok := r.Context().Value(contextKeyUserID).(int64); ok && userID > 0 {
        return fmt.Sprintf("user:%d", userID), "user"
    }

    // X-Real-IP setuje Nginx/Ingress (bez ovoga dobijamo pod IP, ne korisnikov)
    if ip := r.Header.Get("X-Real-IP"); ip != "" {
        return fmt.Sprintf("ip:%s", ip), "ip"
    }

    // Fallback: RemoteAddr (rijetko, samo bez Ingressa)
    return fmt.Sprintf("ip:%s", r.RemoteAddr), "ip"
}

// getLimitForPath vraća najspecifičniji limit za dati URL path.
func (l *Limiter) getLimitForPath(path string) RateLimit {
    bestMatch := ""
    var bestLimit RateLimit

    for prefix, limit := range l.limits {
        if len(prefix) > len(bestMatch) && len(path) >= len(prefix) && path[:len(prefix)] == prefix {
            bestMatch = prefix
            bestLimit = limit
        }
    }

    if bestMatch == "" {
        return RateLimit{Requests: 100, Window: time.Minute} // Sigurni default
    }
    return bestLimit
}

type contextKey string
const contextKeyUserID contextKey = "userID"
```

### Prometheus metrics

```go
// middleware/ratelimit/metrics.go
package ratelimit

import "github.com/prometheus/client_golang/prometheus"

var rateLimitHitsTotal = prometheus.NewCounterVec(
    prometheus.CounterOpts{
        Namespace: "project_a",
        Name:      "rate_limit_hits_total",
        Help:      "Ukupan broj zahtjeva koji su pogodili rate limit",
    },
    []string{"endpoint", "identifier_type"}, // "user" ili "ip"
)

func init() {
    prometheus.MustRegister(rateLimitHitsTotal)
}
```

### Registracija middlewarea

```go
// cmd/main.go

limiter := ratelimit.New(redisClient)

// Rate limit middleware dolazi POSLIJE auth middlewarea
// (da bi imao user ID iz JWT-a za per-user limiting)
handler := limiter.Middleware(
    authMiddleware.Middleware(
        appRouter,
    ),
)
```

---

## PHP middleware za rate limiting

```php
<?php
// middleware/RateLimitMiddleware.php

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface as RequestHandler;
use Predis\Client as Redis;
use Slim\Psr7\Response as SlimResponse;

class RateLimitMiddleware implements MiddlewareInterface
{
    private array $limits = [
        '/api/auth/login'           => ['requests' => 5,  'window' => 600],  // 10 min
        '/api/auth/register'        => ['requests' => 3,  'window' => 3600], // 1h
        '/api/auth/resend-verify'   => ['requests' => 3,  'window' => 3600],
        '/api/auth/forgot-password' => ['requests' => 3,  'window' => 3600],
        '/api/'                     => ['requests' => 100, 'window' => 60],
    ];

    public function __construct(private readonly Redis $redis) {}

    public function process(Request $request, RequestHandler $handler): Response
    {
        $path       = $request->getUri()->getPath();
        $limit      = $this->getLimitForPath($path);
        $identifier = $this->getIdentifier($request);
        $key        = "php:ratelimit:{$path}:{$identifier}";

        $count = (int) $this->redis->incr($key);

        if ($count === 1) {
            $this->redis->expire($key, $limit['window']);
        }

        $remaining = max(0, $limit['requests'] - $count);

        if ($count > $limit['requests']) {
            $response = new SlimResponse(429);
            $response = $response
                ->withHeader('Content-Type', 'application/json')
                ->withHeader('Retry-After', (string) $limit['window'])
                ->withHeader('X-RateLimit-Limit', (string) $limit['requests'])
                ->withHeader('X-RateLimit-Remaining', '0');

            $response->getBody()->write(json_encode([
                'error'       => 'rate_limit_exceeded',
                'message'     => sprintf('Previše zahtjeva. Pričekaj %ds.', $limit['window']),
                'retry_after' => $limit['window'],
            ]));

            return $response;
        }

        $response = $handler->handle($request);

        return $response
            ->withHeader('X-RateLimit-Limit',     (string) $limit['requests'])
            ->withHeader('X-RateLimit-Remaining', (string) $remaining);
    }

    private function getIdentifier(Request $request): string
    {
        // JWT user ID iz atributa (setuje auth middleware)
        $userID = $request->getAttribute('user_id');
        if ($userID !== null) {
            return 'user:' . $userID;
        }

        // X-Real-IP iz Nginx/Ingress headera
        $realIP = $request->getHeaderLine('X-Real-IP');
        if ($realIP !== '') {
            return 'ip:' . $realIP;
        }

        // Fallback
        $serverParams = $request->getServerParams();
        return 'ip:' . ($serverParams['REMOTE_ADDR'] ?? 'unknown');
    }

    private function getLimitForPath(string $path): array
    {
        $bestMatch  = '';
        $bestLimit  = ['requests' => 100, 'window' => 60];

        foreach ($this->limits as $prefix => $limit) {
            if (strlen($prefix) > strlen($bestMatch) && str_starts_with($path, $prefix)) {
                $bestMatch = $prefix;
                $bestLimit = $limit;
            }
        }

        return $bestLimit;
    }
}
```

```php
<?php
// public/index.php — registracija

$app->add(new RateLimitMiddleware($redis));
// Rate limit middleware mora biti POSLIJE AuthMiddleware-a
// (da bi imao user_id atribut iz JWT-a)
```

---

## Vue.js: Graceful handling 429

```typescript
// src/plugins/axios.ts

import axios, { type AxiosError } from 'axios'
import { useToast }               from '@/composables/useToast'
import { useAuthStore }           from '@/stores/auth'

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 10_000,
})

apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        if (error.response?.status === 429) {
            const retryAfter = parseInt(
                (error.response.headers['retry-after'] as string) ?? '60',
                10,
            )
            const minutes = Math.ceil(retryAfter / 60)
            const message = retryAfter >= 60
                ? `Previše zahtjeva. Pričekaj ${minutes} min.`
                : `Previše zahtjeva. Pričekaj ${retryAfter}s.`

            useToast().warning(message, { duration: 8000 })

            // NE retry automatski — korisnik mora čekati
            // Dodaj info na response da UI može deaktivirati dugme
            return Promise.reject({
                ...error,
                isRateLimit:  true,
                retryAfter,
            })
        }

        return Promise.reject(error)
    },
)

export default apiClient
```

```typescript
// Primjer: deaktivacija "Prijavi se" dugmeta nakon 429
// src/views/LoginView.vue

import { ref } from 'vue'
import apiClient from '@/plugins/axios'

const isRateLimited   = ref(false)
const rateLimitSeconds = ref(0)

async function handleLogin(): Promise<void> {
    try {
        await apiClient.post('/api/auth/login', { email, password })
    } catch (error: any) {
        if (error.isRateLimit) {
            isRateLimited.value    = true
            rateLimitSeconds.value = error.retryAfter

            // Odbrojavanje — re-enable dugme kad prođe window
            const interval = setInterval(() => {
                rateLimitSeconds.value--
                if (rateLimitSeconds.value <= 0) {
                    isRateLimited.value = false
                    clearInterval(interval)
                }
            }, 1000)
        }
    }
}
```

```vue
<!-- Dugme u template-u: -->
<button
  @click="handleLogin"
  :disabled="isRateLimited"
>
  {{ isRateLimited ? `Pričekaj ${rateLimitSeconds}s` : 'Prijavi se' }}
</button>
```

---

## Redis struktura ključeva

```
ratelimit:/api/auth/login:user:42          → brojaš za korisnika #42
ratelimit:/api/auth/login:ip:203.0.113.50  → brojaš za IP (neulogirani korisnik)
ratelimit:/api/:user:42                    → globalni limit za korisnika #42

TTL:  automatski (EXPIRE postavljen na prvi INCR)
Tip:  STRING (integer value)
```

```bash
# Debug u development okruženju:
kubectl exec -n project-a-dev deployment/redis -- \
  redis-cli KEYS "ratelimit:*" | head -20

kubectl exec -n project-a-dev deployment/redis -- \
  redis-cli GET "ratelimit:/api/auth/login:ip:127.0.0.1"

kubectl exec -n project-a-dev deployment/redis -- \
  redis-cli TTL "ratelimit:/api/auth/login:ip:127.0.0.1"
```

---

## Monitoring i alerting

```go
// Grafana dashboard query (PromQL):
// Rate limit hitovi po endpointu u zadnjih 5 minuta:
//   sum(rate(project_a_rate_limit_hits_total[5m])) by (endpoint)

// Alert: ako login endpoint ima > 10 rate limit hitova/min → mogući brute force
```

```yaml
# helm/project-a/templates/prometheusrule.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: {{ include "project-a.fullname" . }}-rate-limits
spec:
  groups:
    - name: rate-limits
      rules:
        - alert: HighRateLimitHitsOnLogin
          expr: |
            sum(rate(project_a_rate_limit_hits_total{endpoint="/api/auth/login"}[5m])) > 10
          for: 2m
          labels:
            severity: warning
          annotations:
            summary: "Visok broj rate limit hitova na login endpointu"
            description: "Moguć brute force napad. {{ $value | humanize }} hitova/s"
```

---

## Sažetak arhitekture rate limitinga

```
Request dolazi
     │
     ▼
[Nginx Ingress]
  Rate limit po IP-u za sve (gruba zaštita, visoki prag)
     │
     ▼
[Auth Middleware]
  Parsira JWT, injectuje user_id u context
     │
     ▼
[Rate Limit Middleware]
  Čita user_id (ili fallback IP)
  Provjeri Redis brojaš
  Postavi X-RateLimit-* headere
  429 ako je prekoračen limit
     │
     ▼
[Handler]
  Poslovna logika
```

---

## Checklist

- [ ] Redis klijent je dostupan rate limit middlewareu
- [ ] Middleware je registrovan POSLIJE auth middlewarea (da ima user ID)
- [ ] `X-Real-IP` header proslijeđen iz Nginx Ingressa (bez njega svi imaju isti IP)
- [ ] Svi auth endpointovi imaju stroge limite (login: 5/10min)
- [ ] Fail open: Redis greška ne blokira zahtjev
- [ ] Vue axios interceptor prikazuje poruku i deaktivira dugme
- [ ] Prometheus counter registrovan i pojavljuje se na `/metrics`
- [ ] Grafana alert konfigurisan za brute force detekciju na login endpointu
