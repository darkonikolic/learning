# 09 — Auth i JWT (Vue SPA + PHP proxy + Go service)

## Kontekst

Vue SPA poziva API kroz PHP proxy koji prosljeđuje zahtjeve Go servisu. Treba siguran auth sistem koji radi sa stateless API-jem i ne zahtijeva server-side session.

---

## Zašto JWT za API auth

- **SPA priroda**: Vue SPA nema server-side session — svaki servis u pipelinu mora biti u stanju validirati identitet samostalno
- **Self-contained token**: JWT nosi user info (ID, email, roles) — PHP proxy može validirati token bez database lookup-a ili poziva Go servisu za svaki request
- **Stateless skaliranje**: Go service replice ne dijele session storage — JWT eliminira potrebu za sticky sessions
- **Decoupling**: PHP proxy validira JWT lokalno (javni ključ), Go servisu prosljeđuje već validirani kontekst kroz headere

---

## Arhitektura autentifikacije

```
POST /api/auth/login
  → PHP → Go
      ↓ MySQL: SELECT id, email, password_hash FROM users WHERE email = ?
      ↓ bcrypt.Compare(password, hash)
      ↓ Generiši:
          1. Access token:  JWT, RS256, 15 min
                            payload: {sub: userId, email, roles}
          2. Refresh token: opaque (UUID v4), 7 dana
                            čuvan u Redis: "refresh:{uuid}" → userId
      ← HTTP 200
          Body:    {"access_token": "eyJ...", "expires_in": 900}
          Cookie:  Set-Cookie: refresh_token=uuid; HttpOnly; Secure;
                               SameSite=Strict; Path=/api/auth/refresh;
                               Max-Age=604800

Vue: access_token čuva u memoriji (JavaScript varijabla — NIKAD localStorage!)
Svaki API request: Authorization: Bearer eyJ...
```

**Zašto access token u memoriji, a ne localStorage:**
- `localStorage` je dostupan svim JavaScript skriptama na stranici, uključujući XSS payload
- Memorija (JS varijabla) nije perzistentna između tab-ova i page refresh-a, ali je sigurna od XSS krađe
- Refresh token u `httpOnly` cookieju — JS ne može čitati ni pisati httpOnly cookies

---

## RS256 keypair: generisanje i distribucija

```bash
# Generisanje keypair-a (jednom, lokalno ili u CI/CD tajnom koraku)
openssl genrsa -out jwt-private.pem 2048
openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem

# Privatni ključ → AWS Secrets Manager
# Go service čita pri startu — PHP NIKAD ne vidi privatni ključ
aws secretsmanager create-secret \
  --name /project-a/prod/go-service/jwt-private-key \
  --secret-string file://jwt-private.pem

# Javni ključ → Kubernetes ConfigMap
# PHP koristi za verifikaciju — javni ključ nije tajna
kubectl create configmap jwt-public-key \
  --from-file=public.pem=jwt-public.pem \
  -n project-a-prod
```

**Zašto RS256, a ne HS256:**
- HS256 koristi isti ključ za potpisivanje i verifikaciju — PHP bi morao znati isti ključ i mogao bi krivotvoriti tokene
- RS256: Go service potpisuje privatnim ključem, PHP verifikuje javnim — PHP ne može kreirati valjane tokene
- Separation of concerns: samo Go service može biti issuer tokena

---

## Go service: JWT kreiranje i refresh token

```go
// internal/auth/service.go
package auth

import (
    "context"
    "strconv"
    "time"

    "github.com/golang-jwt/jwt/v5"
    "github.com/google/uuid"
)

type Claims struct {
    UserID int64    `json:"sub"`
    Email  string   `json:"email"`
    Roles  []string `json:"roles"`
    jwt.RegisteredClaims
}

type TokenPair struct {
    AccessToken  string
    RefreshToken string
}

func (s *AuthService) CreateTokens(ctx context.Context, user *User) (*TokenPair, error) {
    now := time.Now()

    // Access token: kratko trajanje, nosi user kontekst
    claims := Claims{
        UserID: user.ID,
        Email:  user.Email,
        Roles:  user.Roles,
        RegisteredClaims: jwt.RegisteredClaims{
            // sub mora biti string prema RFC 7519
            Subject:   strconv.FormatInt(user.ID, 10),
            IssuedAt:  jwt.NewNumericDate(now),
            ExpiresAt: jwt.NewNumericDate(now.Add(15 * time.Minute)),
            // Issuer za validaciju na strani PHP-a (provjerava iss claim)
            Issuer:    "project-a",
        },
    }

    token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
    accessToken, err := token.SignedString(s.privateKey)
    if err != nil {
        return nil, fmt.Errorf("sign access token: %w", err)
    }

    // Refresh token: opaque UUID — nema informacija unutar tokena
    // Napadač koji ukrade refresh token ne može dekodirati user info
    refreshToken := uuid.New().String()

    // Redis: key = "refresh:{uuid}", value = userId, TTL = 7 dana
    // SETEX je atomic — nema race condition
    key := "refresh:" + refreshToken
    if err := s.redis.SetEx(ctx, key, user.ID, 7*24*time.Hour).Err(); err != nil {
        return nil, fmt.Errorf("store refresh token: %w", err)
    }

    return &TokenPair{
        AccessToken:  accessToken,
        RefreshToken: refreshToken,
    }, nil
}
```

**Zašto opaque refresh token (UUID), a ne JWT:**
- JWT refresh token bi nosio expiry — napadač zna tačno koliko ima vremena
- Opaque token u Redisu: instant revokacija pri logout-u (DELETE key)
- Redis TTL garantuje čišćenje bez cron jobova

---

## PHP proxy: JWT validacija middleware

```php
<?php
// src/Middleware/JWTMiddleware.php

namespace App\Middleware;

use Firebase\JWT\JWT;
use Firebase\JWT\Key;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Server\RequestHandlerInterface as RequestHandler;

class JWTMiddleware
{
    private string $publicKeyPath;

    public function __construct(string $publicKeyPath = '/etc/jwt/public.pem')
    {
        $this->publicKeyPath = $publicKeyPath;
    }

    public function __invoke(Request $request, RequestHandler $handler): Response
    {
        $header = $request->getHeaderLine('Authorization');

        if (!str_starts_with($header, 'Bearer ')) {
            return $this->unauthorizedResponse('Missing or invalid Authorization header');
        }

        $token = substr($header, 7);

        try {
            // Javni ključ iz ConfigMap volumena — ne iz Secrets Manager-a
            $publicKey = file_get_contents($this->publicKeyPath);
            if ($publicKey === false) {
                throw new \RuntimeException('Cannot read public key');
            }

            // JWT::decode baca iznimku za: expired, invalid signature, wrong issuer
            $decoded = JWT::decode($token, new Key($publicKey, 'RS256'));

            // Validacija issuera — sprječava tokene od drugog servisa
            if (($decoded->iss ?? '') !== 'project-a') {
                return $this->unauthorizedResponse('Invalid token issuer');
            }

            // Proslijedi user kontekst Go servisu kroz interne headere
            // Go service vjeruje ovim headerima SAMO od PHP proxya (network policy!)
            $request = $request
                ->withHeader('X-User-ID', (string) $decoded->sub)
                ->withHeader('X-User-Email', $decoded->email)
                ->withHeader('X-User-Roles', implode(',', $decoded->roles ?? []));

        } catch (\Firebase\JWT\ExpiredException $e) {
            // Poseban error kod za expired — Vue zna da treba refresh
            return $this->unauthorizedResponse('Token expired', 'TOKEN_EXPIRED');
        } catch (\Exception $e) {
            return $this->unauthorizedResponse('Invalid token');
        }

        return $handler->handle($request);
    }

    private function unauthorizedResponse(string $message, string $code = 'UNAUTHORIZED'): Response
    {
        $response = new \Slim\Psr7\Response(401);
        $response->getBody()->write(json_encode([
            'error' => $message,
            'code'  => $code,
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
}
```

**Važno: X-User-* headeri**
PHP proxy postavlja ove headere nakon validacije JWT-a. Go service smije vjerovati ovim headerima samo ako dolaze od PHP proxya — osiguraj NetworkPolicy da direktni pozivi na Go service port nisu mogući izvana.

---

## Go service: čitanje user konteksta

```go
// internal/middleware/user_context.go
package middleware

import (
    "context"
    "net/http"
    "strconv"
    "strings"
)

type contextKey string

const UserContextKey contextKey = "user"

type UserContext struct {
    ID    int64
    Email string
    Roles []string
}

// ExtractUserContext čita headere koje PHP proxy postavlja nakon JWT validacije.
// Go service ne validira JWT — PHP je već to napravio.
func ExtractUserContext(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        userID, err := strconv.ParseInt(r.Header.Get("X-User-ID"), 10, 64)
        if err != nil || userID == 0 {
            http.Error(w, `{"error":"missing user context"}`, http.StatusUnauthorized)
            return
        }

        user := UserContext{
            ID:    userID,
            Email: r.Header.Get("X-User-Email"),
            Roles: strings.Split(r.Header.Get("X-User-Roles"), ","),
        }

        ctx := context.WithValue(r.Context(), UserContextKey, user)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

---

## Refresh flow

```go
// internal/auth/refresh.go

func (s *AuthService) RefreshTokens(ctx context.Context, refreshToken string) (*TokenPair, error) {
    key := "refresh:" + refreshToken

    // Atomično dohvati userId iz Redisa
    userIDStr, err := s.redis.Get(ctx, key).Result()
    if err != nil {
        // redis.Nil = token ne postoji ili je istekao
        return nil, ErrInvalidRefreshToken
    }

    userID, _ := strconv.ParseInt(userIDStr, 10, 64)
    user, err := s.userRepo.FindByID(ctx, userID)
    if err != nil {
        return nil, err
    }

    // Refresh token rotation: stari token se briše, novi se kreira
    // Sprječava replay napade sa ukradenim refresh tokenom
    pipe := s.redis.Pipeline()
    pipe.Del(ctx, key)                                              // brisi stari
    newRefresh := uuid.New().String()
    pipe.SetEx(ctx, "refresh:"+newRefresh, userID, 7*24*time.Hour) // postavi novi
    if _, err := pipe.Exec(ctx); err != nil {
        return nil, fmt.Errorf("rotate refresh token: %w", err)
    }

    // Generiši novi access token
    tokens, err := s.CreateTokens(ctx, user)
    if err != nil {
        return nil, err
    }
    tokens.RefreshToken = newRefresh

    return tokens, nil
}
```

---

## Logout

```go
// internal/auth/logout.go

func (s *AuthService) Logout(ctx context.Context, refreshToken string) error {
    // Brisanje iz Redisa = instant revokacija refresh tokena
    // Del ne vraća grešku ako key ne postoji — idempotentno
    return s.redis.Del(ctx, "refresh:"+refreshToken).Err()
}

// Access token ostaje validan do expiry (15 min maksimalno).
// Ovo je prihvatljiv kompromis za 99% use-caseova.

// Za instant access token revokaciju (ako je potrebno):
// - Dodaj Redis denylist: "denylist:{jti}" → true, TTL = token expiry
// - PHP middleware provjeri denylist pri svakom requestu
// - Tradeoff: svaki API request = 1 Redis lookup
```

---

## Vue: upravljanje tokenima

```typescript
// src/stores/auth.ts (Pinia)
import { ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  // Access token ISKLJUČIVO u memoriji — ne persist() ovo!
  const accessToken = ref<string | null>(null)
  const tokenExpiry = ref<number | null>(null)

  async function login(email: string, password: string) {
    const res = await axios.post('/api/auth/login', { email, password })
    accessToken.value = res.data.access_token
    tokenExpiry.value = Date.now() + res.data.expires_in * 1000
    // refresh_token je automatski u httpOnly cookie — Vue ga ne vidi
  }

  async function refresh() {
    // Axios šalje cookie automatski (withCredentials: true)
    const res = await axios.post('/api/auth/refresh', {}, { withCredentials: true })
    accessToken.value = res.data.access_token
    tokenExpiry.value = Date.now() + res.data.expires_in * 1000
  }

  async function logout() {
    await axios.post('/api/auth/logout', {}, { withCredentials: true })
    accessToken.value = null
    tokenExpiry.value = null
  }

  return { accessToken, tokenExpiry, login, refresh, logout }
})
```

```typescript
// src/plugins/axios.ts — interceptor za automatski refresh
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

axios.interceptors.request.use(config => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401 &&
        error.response?.data?.code === 'TOKEN_EXPIRED') {
      // Pokušaj refresh jedanput
      try {
        const auth = useAuthStore()
        await auth.refresh()
        // Ponovi originalni request sa novim tokenom
        error.config.headers.Authorization = `Bearer ${auth.accessToken}`
        return axios(error.config)
      } catch {
        // Refresh nije uspio — redirect na login
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
```

---

## Kubernetes: montiranje ključeva

```yaml
# PHP Deployment: javni ključ iz ConfigMap
spec:
  template:
    spec:
      volumes:
        - name: jwt-public-key
          configMap:
            name: jwt-public-key
      containers:
        - name: php-service
          volumeMounts:
            - name: jwt-public-key
              mountPath: /etc/jwt
              readOnly: true
---
# Go Deployment: privatni ključ iz Secrets Manager (External Secrets Operator)
# ili direktno iz K8s Secret (ako koristiš sealed-secrets)
spec:
  template:
    spec:
      volumes:
        - name: jwt-private-key
          secret:
            secretName: go-service-jwt-private-key
            defaultMode: 0400
      containers:
        - name: go-service
          volumeMounts:
            - name: jwt-private-key
              mountPath: /etc/jwt
              readOnly: true
```

---

## Security checklist

- [ ] **RS256, ne HS256** — privatni ključ samo u Go servisu, PHP ne može krivotvoriti tokene
- [ ] **Access token u memoriji** — ne `localStorage`, ne `sessionStorage`
- [ ] **Refresh token u `httpOnly` cookieju** — nedostupan JavaScript-u
- [ ] **Kratko trajanje access tokena** — 15 minuta, maksimalno 1 sat
- [ ] **Refresh token rotation** — novi token pri svakom refreshu, stari se briše
- [ ] **Logout = brisanje refresh tokena iz Redisa** — instant revokacija
- [ ] **NetworkPolicy** — direktni pozivi na Go service port samo od PHP proxya
- [ ] **HTTPS posvuda** — TLS na ALB + cert-manager interni TLS (modul 15/07)
- [ ] **Validacija `iss` claima** — PHP odbija tokene od drugog issuera
- [ ] **Nema osjetljivih podataka u JWT payloadu** — password hash, kreditna kartica itd.
