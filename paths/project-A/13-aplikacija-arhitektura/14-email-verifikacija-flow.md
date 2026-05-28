# 14. Email Verifikacija Flow

## Arhitektura toka

```
Vue /register → POST /api/auth/register (PHP proxy)
                                ↓
                       Go: AuthHandler.Register
                                ↓
                    INSERT users (is_active=0)
                    uuid token → Redis (TTL 24h)
                    email.SendVerificationEmail (goroutine)
                                ↓
                    HTTP 201 → Vue prikazuje poruku

Korisnik klikne link u emailu → Vue /verify?token=uuid
                                ↓
                       POST /api/auth/verify-email?token=uuid
                                ↓
                       Go: AuthHandler.VerifyEmail
                                ↓
                    Redis GET verify:{token} → userID
                    UPDATE users SET is_active=1
                    Redis DEL verify:{token}
                                ↓
                    HTTP 200 → Vue redirect na /login
```

---

## MySQL migracija

```sql
-- migrations/000004_add_email_verification.up.sql

ALTER TABLE users
    ADD COLUMN email_verified_at TIMESTAMP NULL DEFAULT NULL AFTER email,
    ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 0 AFTER email_verified_at;

-- Index za login query (WHERE email = ? AND is_active = 1)
ALTER TABLE users ADD INDEX idx_is_active (is_active);
```

```sql
-- migrations/000004_add_email_verification.down.sql

ALTER TABLE users
    DROP INDEX idx_is_active,
    DROP COLUMN is_active,
    DROP COLUMN email_verified_at;
```

Pokreni migraciju:
```bash
migrate -path ./migrations -database "mysql://user:pass@tcp(localhost:3306)/projecta" up
```

---

## Go: Registration handler

```go
// internal/handler/auth.go
package handler

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "net/mail"
    "time"
    "unicode"

    "github.com/google/uuid"
    "github.com/redis/go-redis/v9"
    "go.uber.org/zap"
    "golang.org/x/crypto/bcrypt"

    "project-a/internal/email"
)

type AuthHandler struct {
    db     DBPool       // interface s Read() i Write() metodama
    redis  *redis.Client
    email  *email.Service
    config Config
    logger *zap.Logger
}

type registerRequest struct {
    Email    string `json:"email"`
    Password string `json:"password"`
}

func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
    var req registerRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, http.StatusBadRequest, "invalid_request_body")
        return
    }

    if err := validateRegistrationInput(req.Email, req.Password); err != nil {
        respondError(w, http.StatusBadRequest, err.Error())
        return
    }

    hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), 12)
    if err != nil {
        h.logger.Error("bcrypt failed", zap.Error(err))
        respondError(w, http.StatusInternalServerError, "internal_error")
        return
    }

    result, err := h.db.Write().ExecContext(r.Context(),
        "INSERT INTO users (email, password_hash, is_active, created_at) VALUES (?, ?, 0, NOW())",
        req.Email, string(hash),
    )
    if err != nil {
        if isMySQLDuplicateError(err) {
            // Ne otkrivamo postojeće emailove (sigurnost) — ista poruka kao uspjeh
            w.WriteHeader(http.StatusCreated)
            json.NewEncoder(w).Encode(map[string]string{
                "message": "registration_initiated",
            })
            return
        }
        h.logger.Error("insert user failed", zap.Error(err))
        respondError(w, http.StatusInternalServerError, "internal_error")
        return
    }

    userID, _ := result.LastInsertId()

    token := uuid.New().String()
    tokenKey := fmt.Sprintf("verify:%s", token)

    if err := h.redis.SetEx(r.Context(), tokenKey, userID, 24*time.Hour).Err(); err != nil {
        h.logger.Error("redis set verification token failed",
            zap.Int64("user_id", userID),
            zap.Error(err),
        )
        // Ne vraćamo grešku korisniku — registracija je uspjela, token je problem
        // Korisnik može zatražiti resend
    }

    // Email šaljemo u goroutini — ne blokiramo HTTP odgovor
    go func() {
        ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
        defer cancel()

        if err := h.email.SendVerificationEmail(ctx, req.Email, token, h.config.BaseURL); err != nil {
            h.logger.Error("send verification email failed",
                zap.String("email", req.Email),
                zap.Error(err),
            )
        }
    }()

    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(map[string]string{
        "message": "registration_initiated",
    })
}

func validateRegistrationInput(email, password string) error {
    // Email format
    if _, err := mail.ParseAddress(email); err != nil {
        return fmt.Errorf("invalid_email")
    }

    // Password: min 8 znakova, jedno veliko, jedan broj
    if len(password) < 8 {
        return fmt.Errorf("password_too_short")
    }
    var hasUpper, hasDigit bool
    for _, r := range password {
        if unicode.IsUpper(r) {
            hasUpper = true
        }
        if unicode.IsDigit(r) {
            hasDigit = true
        }
    }
    if !hasUpper || !hasDigit {
        return fmt.Errorf("password_too_weak")
    }

    return nil
}
```

---

## Go: Email verification handler

```go
// internal/handler/auth_verify.go
package handler

import (
    "encoding/json"
    "fmt"
    "net/http"
    "strconv"

    "github.com/redis/go-redis/v9"
    "go.uber.org/zap"
)

func (h *AuthHandler) VerifyEmail(w http.ResponseWriter, r *http.Request) {
    token := r.URL.Query().Get("token")
    if token == "" {
        respondError(w, http.StatusBadRequest, "missing_token")
        return
    }

    // UUID format validacija (osnovna)
    if len(token) != 36 {
        respondError(w, http.StatusBadRequest, "invalid_token_format")
        return
    }

    tokenKey := fmt.Sprintf("verify:%s", token)

    userIDStr, err := h.redis.Get(r.Context(), tokenKey).Result()
    if err == redis.Nil {
        respondError(w, http.StatusBadRequest, "invalid_or_expired_token")
        return
    }
    if err != nil {
        h.logger.Error("redis get verification token failed", zap.Error(err))
        respondError(w, http.StatusInternalServerError, "internal_error")
        return
    }

    userID, err := strconv.ParseInt(userIDStr, 10, 64)
    if err != nil {
        h.logger.Error("invalid user id in redis",
            zap.String("token_key", tokenKey),
            zap.String("value", userIDStr),
        )
        respondError(w, http.StatusInternalServerError, "internal_error")
        return
    }

    _, err = h.db.Write().ExecContext(r.Context(),
        "UPDATE users SET is_active = 1, email_verified_at = NOW() WHERE id = ? AND is_active = 0",
        userID,
    )
    if err != nil {
        h.logger.Error("update user active failed",
            zap.Int64("user_id", userID),
            zap.Error(err),
        )
        respondError(w, http.StatusInternalServerError, "internal_error")
        return
    }

    // Obriši token — jednokratna upotreba
    h.redis.Del(r.Context(), tokenKey)

    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{
        "message": "email_verified",
    })
}
```

---

## Go: Login provjera verifikacije

```go
// internal/handler/auth_login.go (relevantan dio)

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
    var req struct {
        Email    string `json:"email"`
        Password string `json:"password"`
    }
    json.NewDecoder(r.Body).Decode(&req)

    var user struct {
        ID           int64
        PasswordHash string
        IsActive     bool
    }

    err := h.db.Read().QueryRowContext(r.Context(),
        "SELECT id, password_hash, is_active FROM users WHERE email = ?",
        req.Email,
    ).Scan(&user.ID, &user.PasswordHash, &user.IsActive)

    if err != nil {
        // Isti odgovor za nepostojeći email i pogrešnu lozinku (sprečava user enumeration)
        respondError(w, http.StatusUnauthorized, "invalid_credentials")
        return
    }

    if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
        respondError(w, http.StatusUnauthorized, "invalid_credentials")
        return
    }

    // Provjera email verifikacije — NAKON provjere lozinke
    // (ne otkrivamo da li email postoji prije nego znamo lozinku)
    if !user.IsActive {
        respondError(w, http.StatusForbidden, "email_not_verified")
        return
    }

    // ... generacija JWT tokena i odgovor
}
```

---

## Go: Resend verification (rate limited)

```go
// internal/handler/auth_resend.go
package handler

import (
    "encoding/json"
    "fmt"
    "net/http"
    "time"

    "github.com/google/uuid"
    "go.uber.org/zap"
)

func (h *AuthHandler) ResendVerification(w http.ResponseWriter, r *http.Request) {
    var req struct {
        Email string `json:"email"`
    }
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, http.StatusBadRequest, "invalid_request_body")
        return
    }

    // Rate limit: max 3 zahtjeva po emailu na sat
    rateLimitKey := fmt.Sprintf("resend_rate:%s", req.Email)
    count, err := h.redis.Incr(r.Context(), rateLimitKey).Result()
    if err != nil {
        h.logger.Error("redis incr rate limit failed", zap.Error(err))
        respondError(w, http.StatusInternalServerError, "internal_error")
        return
    }
    if count == 1 {
        // Postavi TTL na prvu upotrebu
        h.redis.Expire(r.Context(), rateLimitKey, time.Hour)
    }
    if count > 3 {
        respondError(w, http.StatusTooManyRequests, "rate_limit_exceeded")
        return
    }

    // Pronađi neaktivnog korisnika
    var userID int64
    err = h.db.Read().QueryRowContext(r.Context(),
        "SELECT id FROM users WHERE email = ? AND is_active = 0",
        req.Email,
    ).Scan(&userID)
    if err != nil {
        // Ne otkrivamo detalje — uvijek ista poruka
        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(map[string]string{"message": "verification_email_sent"})
        return
    }

    token := uuid.New().String()
    tokenKey := fmt.Sprintf("verify:%s", token)
    h.redis.SetEx(r.Context(), tokenKey, userID, 24*time.Hour)

    go func() {
        if err := h.email.SendVerificationEmail(
            r.Context(), req.Email, token, h.config.BaseURL,
        ); err != nil {
            h.logger.Error("resend verification email failed",
                zap.String("email", req.Email),
                zap.Error(err),
            )
        }
    }()

    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{"message": "verification_email_sent"})
}
```

---

## Vue.js: Verify stranica

```vue
<!-- src/views/VerifyEmail.vue -->
<template>
  <div class="verify-container">
    <div v-if="status === 'verifying'" data-testid="verify-loading">
      <p>Verifying your email...</p>
    </div>

    <div v-if="status === 'success'" data-testid="verify-success">
      <h2>Email verified!</h2>
      <p>{{ message }}</p>
    </div>

    <div v-if="status === 'error'" data-testid="verify-error">
      <h2>Verification failed</h2>
      <p>{{ message }}</p>
      <button @click="resendEmail">Resend verification email</button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const status = ref('verifying')
const message = ref('')

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    status.value = 'error'
    message.value = 'Invalid verification link.'
    return
  }

  try {
    await axios.post(`/api/auth/verify-email?token=${token}`)
    status.value = 'success'
    message.value = 'Email verified! Redirecting to login...'
    setTimeout(() => router.push('/login'), 2000)
  } catch (err) {
    status.value = 'error'
    const errorCode = err.response?.data?.error
    message.value = errorCode === 'invalid_or_expired_token'
      ? 'Verification link has expired. Please request a new one.'
      : 'Verification failed. Please try again.'
  }
})

async function resendEmail() {
  // Redirektuj na stranicu za resend ili prikaži inline formu
  router.push('/resend-verification')
}
</script>
```

**Vue router konfiguracija:**
```javascript
// src/router/index.js
const routes = [
  { path: '/login',   component: () => import('../views/Login.vue') },
  { path: '/register', component: () => import('../views/Register.vue') },
  { path: '/verify',  component: () => import('../views/VerifyEmail.vue') },
  { path: '/resend-verification', component: () => import('../views/ResendVerification.vue') },
  // ...ostale rute
]
```

**Vue: Handling 403 email_not_verified u login komponentu:**
```javascript
// src/views/Login.vue (relevantan dio)
async function handleLogin() {
  try {
    const response = await axios.post('/api/auth/login', { email, password })
    // ... spremi token, redirect
  } catch (err) {
    if (err.response?.status === 403 && err.response?.data?.error === 'email_not_verified') {
      loginError.value = 'Please verify your email before logging in.'
      showResendLink.value = true
    } else if (err.response?.status === 401) {
      loginError.value = 'Invalid email or password.'
    } else {
      loginError.value = 'Login failed. Please try again.'
    }
  }
}
```

---

## Playwright E2E testovi

```typescript
// e2e/registration-flow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Registration and email verification', () => {
  const testEmail = `test+${Date.now()}@example.com`

  test('completes full registration flow', async ({ page }) => {
    // 1. Registracija
    await page.goto('/register')
    await page.fill('[data-testid="email"]', testEmail)
    await page.fill('[data-testid="password"]', 'TestPass123!')
    await page.click('[data-testid="register-button"]')

    await expect(page.locator('[data-testid="success-message"]'))
      .toContainText('Check your email')

    // 2. Dohvati link iz Mailpit API-ja
    const mailpit = await fetch('http://localhost:8025/api/v1/messages')
    const data = await mailpit.json()

    expect(data.messages.length).toBeGreaterThan(0)

    // Dohvati puni sadržaj emaila
    const messageID = data.messages[0].ID
    const emailDetail = await fetch(`http://localhost:8025/api/v1/message/${messageID}`)
    const emailData = await emailDetail.json()

    // Izvuci verification URL iz tijela emaila
    const verifyURLMatch = emailData.Text.match(/https?:\/\/\S+verify\S+/)
    expect(verifyURLMatch).not.toBeNull()
    const verifyURL = verifyURLMatch[0]

    // 3. Klikni verification link
    await page.goto(verifyURL)
    await expect(page.locator('[data-testid="verify-success"]')).toBeVisible()

    // 4. Login treba raditi
    await page.goto('/login')
    await page.fill('[data-testid="email"]', testEmail)
    await page.fill('[data-testid="password"]', 'TestPass123!')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/dashboard')
  })

  test('login fails with 403 for unverified user', async ({ page }) => {
    // Registruj ali ne verificiraj
    await page.goto('/register')
    const unverifiedEmail = `unverified+${Date.now()}@example.com`
    await page.fill('[data-testid="email"]', unverifiedEmail)
    await page.fill('[data-testid="password"]', 'TestPass123!')
    await page.click('[data-testid="register-button"]')

    // Pokušaj login bez verifikacije
    await page.goto('/login')
    await page.fill('[data-testid="email"]', unverifiedEmail)
    await page.fill('[data-testid="password"]', 'TestPass123!')
    await page.click('[data-testid="login-button"]')

    await expect(page.locator('[data-testid="login-error"]'))
      .toContainText('verify your email')
  })

  test('expired token returns error', async ({ page }) => {
    await page.goto('/verify?token=00000000-0000-0000-0000-000000000000')
    await expect(page.locator('[data-testid="verify-error"]')).toBeVisible()
    await expect(page.locator('[data-testid="verify-error"]'))
      .toContainText('expired')
  })

  test.afterEach(async () => {
    // Reset Mailpit između testova
    await fetch('http://localhost:8025/api/v1/messages', { method: 'DELETE' })
  })
})
```

**Playwright config za dev okruženje:**
```typescript
// playwright.config.ts
export default {
  use: {
    baseURL: 'http://localhost:5173',  // Vite dev server
  },
  webServer: {
    command: 'docker compose up -d && npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
  },
}
```

---

## Routing za PHP proxy

PHP proxy treba proslijediti nove endpointe na Go servis:

```php
// routes/api.php ili nginx location config

// Postojeći:
// POST /api/auth/login → go-service:8080/auth/login

// Novi:
// POST /api/auth/register          → go-service:8080/auth/register
// POST /api/auth/verify-email      → go-service:8080/auth/verify-email
// POST /api/auth/resend-verification → go-service:8080/auth/resend-verification
```

Ako PHP proxy koristi nginx kao interni router:
```nginx
location /api/auth/ {
    proxy_pass http://go-service:8080/auth/;
    proxy_set_header X-Request-ID $request_id;
    proxy_set_header X-Forwarded-For $remote_addr;
}
```

---

## Sažetak: Redis ključevi i TTL-ovi

| Ključ | Vrijednost | TTL | Svrha |
|-------|-----------|-----|-------|
| `verify:{uuid}` | userID (int64) | 24h | Email verifikacijski token |
| `resend_rate:{email}` | counter (int) | 1h | Rate limit za resend |

Oba ključa se automatski brišu po isteku TTL-a — nema potrebe za cron jobom za čišćenje.
