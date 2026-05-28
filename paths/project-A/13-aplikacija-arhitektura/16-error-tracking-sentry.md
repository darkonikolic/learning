# 16 — Error Tracking: Sentry

## Zašto logovi nisu dovoljni

Loki i CloudWatch loguju sve — ali kad app crashne u produkciji, tražiš jednu kritičnu grešku
u moru od milijon log linija. Sentry rješava tri problema:

1. **Grupisanje** — 1000 pojava iste greške = 1 issue, ne 1000 notifikacija
2. **Kontekst** — stack trace sa varijablama u trenutku greške, user koji je imao grešku,
   request koji je izazvao, environment, release
3. **Signal vs šum** — vidiš samo greške, ne sve što prolazi kroz sistem

## Sentry Cloud vs Self-hosted

| | Cloud | Self-hosted |
|---|---|---|
| Setup | 5 minuta | 2-4 sata (Docker Compose) |
| Cijena | Besplatno do 5k error/mj | Besplatno (infrastruktura plaćaš) |
| GDPR | Podaci na Sentry serverima | Podaci ostaju kod tebe |
| Preporuka | Ovaj projekat | GDPR / on-premise zahtjevi |

Za ovaj projekat: **Sentry Cloud**, besplatni tier je dovoljan.

---

## Go service integracija

```bash
go get github.com/getsentry/sentry-go
go get github.com/getsentry/sentry-go/http
```

```go
// pkg/sentry/sentry.go
package sentrypkg

import (
    "fmt"
    "strings"

    "github.com/getsentry/sentry-go"
)

func Init(dsn, env, release string) error {
    if dsn == "" {
        return nil // Sentry nije konfigurisan — lokalni dev
    }

    return sentry.Init(sentry.ClientOptions{
        Dsn:              dsn,
        Environment:      env,     // "development", "staging", "production"
        Release:          release, // commit SHA ili verzija, npr. "v1.2.3-abc1234"
        TracesSampleRate: 0.1,     // 10% zahtjeva za performance tracing
        BeforeSend: func(event *sentry.Event, hint *sentry.EventHint) *sentry.Event {
            // Ukloni sensitive podatke prije slanja Sentryu
            if event.User.Email != "" {
                event.User.Email = maskEmail(event.User.Email)
            }
            return event
        },
    })
}

func maskEmail(email string) string {
    parts := strings.SplitN(email, "@", 2)
    if len(parts) != 2 {
        return "***"
    }
    local := parts[0]
    if len(local) <= 2 {
        return "***@" + parts[1]
    }
    return fmt.Sprintf("%s***@%s", local[:2], parts[1])
}
```

```go
// cmd/main.go
func main() {
    if err := sentrypkg.Init(
        os.Getenv("SENTRY_DSN"),
        os.Getenv("APP_ENV"),
        os.Getenv("RELEASE"), // CI_COMMIT_SHA iz GitLab CI
    ); err != nil {
        log.Fatalf("sentry init: %v", err)
    }
    defer sentry.Flush(2 * time.Second) // Pošalji buffered events pri shutdownu
    // ...
}
```

### HTTP middleware — automatsko hvatanje panika

```go
// middleware/sentry.go
package middleware

import (
    "net/http"

    "github.com/getsentry/sentry-go"
    sentryhttp "github.com/getsentry/sentry-go/http"
)

func Sentry() func(http.Handler) http.Handler {
    sentryHandler := sentryhttp.New(sentryhttp.Options{
        Repanic:         true,  // panic i dalje propagira (standardni recovery middleware hvata)
        WaitForDelivery: false, // Ne blokiraj request na slanje u Sentry
    })
    return sentryHandler.Handle
}
```

```go
// Primjena u router setup-u:
mux := http.NewServeMux()
handler := middleware.Sentry()(mux)
handler = middleware.Recovery(handler) // Recovery mora biti IZVAN Sentry middlewarea
```

### Manualno logovanje greške sa kontekstom

```go
// handlers/auth.go

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
    var req LoginRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, `{"error":"invalid_json"}`, http.StatusBadRequest)
        return
    }

    var user User
    err := h.db.QueryRowContext(r.Context(),
        "SELECT id, email, password_hash FROM users WHERE email = ?", req.Email,
    ).Scan(&user.ID, &user.Email, &user.PasswordHash)

    if err != nil && !errors.Is(err, sql.ErrNoRows) {
        // Neočekivana DB greška — pošalji Sentryu sa kontekstom
        sentry.WithScope(func(scope *sentry.Scope) {
            scope.SetTag("endpoint", "POST /auth/login")
            scope.SetTag("db.operation", "SELECT users")
            scope.SetUser(sentry.User{Email: req.Email})
            scope.SetExtra("error_type", fmt.Sprintf("%T", err))
            sentry.CaptureException(err)
        })
        h.respondError(w, http.StatusInternalServerError, "internal_error", "Greška servera")
        return
    }
    // ...
}
```

---

## PHP service integracija

```bash
composer require sentry/sentry
```

```php
<?php
// config/sentry.php

\Sentry\init([
    'dsn'                => $_ENV['SENTRY_DSN'],
    'environment'        => $_ENV['APP_ENV'],
    'release'            => $_ENV['CI_COMMIT_SHA'] ?? 'unknown',
    'traces_sample_rate' => 0.1,
    'before_send'        => function (\Sentry\Event $event): ?\Sentry\Event {
        // Ne šalji 404 greške Sentryu — nisu bugovi
        foreach ($event->getExceptions() as $exception) {
            if ($exception->getType() === 'NotFoundException') {
                return null;
            }
        }
        return $event;
    },
]);
```

```php
<?php
// middleware/SentryMiddleware.php

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface as RequestHandler;

class SentryMiddleware implements MiddlewareInterface
{
    public function process(Request $request, RequestHandler $handler): Response
    {
        // Dodaj request kontekst Sentryu
        \Sentry\configureScope(function (\Sentry\State\Scope $scope) use ($request): void {
            $scope->setExtra('request.method', $request->getMethod());
            $scope->setExtra('request.path', (string) $request->getUri()->getPath());
        });

        try {
            return $handler->handle($request);
        } catch (\Throwable $e) {
            \Sentry\captureException($e);
            throw $e; // Propagiraj — Slim error handler formatira response
        }
    }
}
```

```php
<?php
// public/index.php — registracija middlewarea

require __DIR__ . '/../config/sentry.php';

$app->add(SentryMiddleware::class);
```

---

## Vue.js integracija

```bash
npm install @sentry/vue
```

```typescript
// src/main.ts
import { createApp }    from 'vue'
import { createRouter } from 'vue-router'
import * as Sentry      from '@sentry/vue'
import App              from './App.vue'
import router           from './router'

const app = createApp(App)

// Inicijalizuj Sentry samo u produkciji i samo ako DSN postoji
if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) {
    Sentry.init({
        app,
        dsn:         import.meta.env.VITE_SENTRY_DSN,
        environment: import.meta.env.VITE_APP_ENV,
        integrations: [
            Sentry.browserTracingIntegration({ router }),
        ],
        tracesSampleRate: 0.1,
        // Ne capture greške iz browser ekstenzija — nisu naši bugovi
        denyUrls: [
            /extensions\//i,
            /^chrome:\/\//i,
            /^chrome-extension:\/\//i,
            /^moz-extension:\/\//i,
        ],
    })
}

app.use(router)
app.mount('#app')
```

```typescript
// Manualno postavljanje korisnika nakon logina (src/stores/auth.ts):
import * as Sentry from '@sentry/vue'

function onLoginSuccess(user: User): void {
    Sentry.setUser({ id: String(user.id), email: user.email })
}

function onLogout(): void {
    Sentry.setUser(null)
}
```

---

## Kubernetes: Sentry DSN iz Secrets Manager

```yaml
# helm/project-a/templates/deployment-go.yaml (relevant dio)
env:
  - name: SENTRY_DSN
    valueFrom:
      secretKeyRef:
        name: sentry-credentials
        key: dsn
  - name: APP_ENV
    value: {{ .Values.environment }}
  - name: RELEASE
    value: {{ .Values.image.tag }}
```

```bash
# Kreiranje Kubernetes Secret-a (jednom, ručno ili kroz Terraform):
kubectl create secret generic sentry-credentials \
  --namespace=project-a-prod \
  --from-literal=dsn="https://abc123@o123456.ingest.sentry.io/789"
```

```hcl
# terraform/modules/k8s-secrets/main.tf — ako koristiš AWS Secrets Manager
resource "aws_secretsmanager_secret" "sentry" {
  name = "project-a/${var.env}/sentry"
}

resource "aws_secretsmanager_secret_version" "sentry" {
  secret_id     = aws_secretsmanager_secret.sentry.id
  secret_string = jsonencode({ dsn = var.sentry_dsn })
}
```

---

## Sentry Alerts konfiguracija

U Sentry UI: **Project → Alerts → Create Alert Rule**

```
# Alert 1: Visoka stopa grešaka (produkcijska kriza)
Trigger:   Number of events > 50 in 5 minutes
Filter:    environment = production
Action:    Notify Slack → #alerts-critical

# Alert 2: Nova greška (prvi put viđena)
Trigger:   A new issue is created
Filter:    environment = production
Action:    Notify Slack → #dev-backend

# Alert 3: Regresija (greška koja se ponovo pojavila)
Trigger:   A previously resolved issue comes back
Filter:    environment = production
Action:    Notify Slack → #dev-backend + assign to me
```

---

## GitLab CI — Release tracking

```yaml
# .gitlab-ci.yml — Sentry Release pri deploymentu
.sentry-release:
  stage: deploy
  before_script:
    - curl -sL https://sentry.io/get-cli/ | bash
  script:
    - sentry-cli releases new "${CI_COMMIT_SHA}"
    - sentry-cli releases set-commits "${CI_COMMIT_SHA}" --auto
    - sentry-cli releases finalize "${CI_COMMIT_SHA}"
    - sentry-cli releases deploys "${CI_COMMIT_SHA}" new -e "${CI_ENVIRONMENT_NAME}"
  variables:
    SENTRY_AUTH_TOKEN: ${SENTRY_AUTH_TOKEN}
    SENTRY_ORG:        ${SENTRY_ORG}
    SENTRY_PROJECT:    project-a-backend
```

Release tracking daje Sentryu informaciju koji commit je uveo grešku —
"This issue first appeared in release abc1234" i prikazuje koje su promjene bile u tom commitu.

---

## Checklist

- [ ] Sentry projekt kreiran (Cloud), DSN u Secrets Manager
- [ ] Go: `sentry.Init` u `main.go`, Sentry middleware registrovan
- [ ] PHP: `\Sentry\init` u `config/sentry.php`, SentryMiddleware registrovan
- [ ] Vue: `Sentry.init` samo za `PROD`, `setUser` nakon logina
- [ ] K8s Secret `sentry-credentials` kreiran u svim namespacima
- [ ] GitLab CI: release tracking pri svakom deploymentu
- [ ] Slack alerts: critical (> 50 errors/5min) + new issues
