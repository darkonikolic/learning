# 04 — Authentication Security

## Password Hashing — Zašto bcrypt

### Zašto Ne MD5/SHA1/SHA256

```
MD5("password123")   = 482c811da5d5b4bc6d497ffa98491e38
SHA1("password123")  = cbfdac6008f9cab4083784cbd1874f76618d2a97
SHA256("password123") = ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f
```

**Problem:** Ovo su hash funkcije namijenjene brzini. GPU može izračunati:
- MD5: **50+ milijardi** hasheva/sekundi
- SHA256: **10+ milijardi** hasheva/sekundi

Baza s 1 milion SHA256 lozinki može biti cracked za **minutu** na consumer GPU-u.

### bcrypt — Namjerno Spor

```
bcrypt(cost=12, "password123") = $2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewV/MH7ZTi2ZmZyK
                                   ↑  ↑
                             algo cost
```

- **cost=12**: 2^12 = 4096 iteracija → ~100-200ms po hashu
- **Salt ugrađen**: Svaki hash je jedinstven čak i za istu lozinku
- **Adaptivan**: Možeš povećati cost s godinama (kako CPU postaje brži)

```go
import "golang.org/x/crypto/bcrypt"

// Registracija / promjena lozinke
func hashPassword(password string) (string, error) {
    // cost=12 je dobar kompromis između sigurnosti i brzine (2025.)
    // cost=10: ~25ms (previše brzo za moderne servere)
    // cost=12: ~100-200ms (preporučeno)
    // cost=14: ~400ms (za extra osjetljive sisteme)
    hash, err := bcrypt.GenerateFromPassword([]byte(password), 12)
    if err != nil {
        return "", fmt.Errorf("hash password: %w", err)
    }
    return string(hash), nil
}

// Login — provjera lozinke
func checkPassword(password, hash string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
    return err == nil
    // bcrypt.CompareHashAndPassword je constant time — otporan na timing napade
}
```

### Migracija Starih MD5/SHA1 Hash-ova

Ako naslijeđena baza ima MD5 lozinke:

```go
// Strategija: migriraj pri login-u (lazy migration)
func (s *AuthService) Login(ctx context.Context, email, password string) (*User, error) {
    user, err := s.userRepo.FindByEmail(ctx, email)
    if err != nil {
        return nil, ErrInvalidCredentials
    }
    
    // Provjeri tip hash-a
    if strings.HasPrefix(user.PasswordHash, "$2") {
        // bcrypt hash — moderna provjera
        if !checkPassword(password, user.PasswordHash) {
            return nil, ErrInvalidCredentials
        }
    } else if len(user.PasswordHash) == 32 {
        // Stari MD5 hash
        legacyHash := fmt.Sprintf("%x", md5.Sum([]byte(password)))
        if !subtle.ConstantTimeCompare([]byte(legacyHash), []byte(user.PasswordHash)) == 1 {
            return nil, ErrInvalidCredentials
        }
        // Migracija: prepiši s bcrypt
        newHash, _ := hashPassword(password)
        s.userRepo.UpdatePasswordHash(ctx, user.ID, newHash)
    } else {
        return nil, ErrInvalidCredentials
    }
    
    return user, nil
}
```

---

## Brute-Force Zaštita na Login Endpoint-u

### Redis Rate Limiting

```go
// services/auth/rate_limiter.go

type RateLimiter struct {
    redis *redis.Client
}

const (
    maxAttemptsPerIP     = 20  // 20 pokušaja po IP adresi
    maxAttemptsPerEmail  = 5   // 5 pokušaja po email adresi
    windowDuration       = 10 * time.Minute
    lockoutDuration      = 15 * time.Minute
    hardLockoutDuration  = 1 * time.Hour
)

// Provjeri i inkrementiraj pokušaje za IP
func (r *RateLimiter) CheckIP(ctx context.Context, ip string) error {
    key := "rate:ip:" + ip
    
    count, err := r.redis.Incr(ctx, key).Result()
    if err != nil {
        // Redis greška — ne blokiraj (fail open), ali loguj
        log.WithError(err).Error("Redis rate limiter error")
        return nil
    }
    
    if count == 1 {
        r.redis.Expire(ctx, key, windowDuration)
    }
    
    if count > maxAttemptsPerIP {
        return ErrRateLimitExceeded
    }
    return nil
}

// Account lockout po email-u
func (s *AuthService) recordFailedAttempt(ctx context.Context, email string) error {
    failKey := "login_fails:" + email
    lockKey := "locked:" + email
    
    count, err := s.redis.Incr(ctx, failKey).Result()
    if err != nil {
        return nil // Fail open na Redis grešku
    }
    
    if count == 1 {
        s.redis.Expire(ctx, failKey, windowDuration)
    }
    
    switch {
    case count >= 20:
        // Hard lockout (1 sat) — vjerovatno automatizirani napad
        s.redis.Set(ctx, lockKey, "hard", hardLockoutDuration)
        return ErrAccountLocked
    case count >= 10:
        // Soft lockout (15 minuta)
        s.redis.Set(ctx, lockKey, "soft", lockoutDuration)
        return ErrAccountLocked
    case count >= 5:
        // Upozorenje — u prave slučajeve možeš poslati email korisniku
        log.WithField("email", email).Warn("Multiple failed login attempts")
        return ErrTooManyAttempts
    }
    
    return nil
}

// Provjeri je li nalog zaključan
func (s *AuthService) isAccountLocked(ctx context.Context, email string) (bool, error) {
    val, err := s.redis.Get(ctx, "locked:"+email).Result()
    if err == redis.Nil {
        return false, nil
    }
    if err != nil {
        return false, err
    }
    return val != "", nil
}

// Reset fail counter pri uspješnom loginu
func (s *AuthService) clearFailedAttempts(ctx context.Context, email string) {
    s.redis.Del(ctx, "login_fails:"+email)
    s.redis.Del(ctx, "locked:"+email)
}
```

### Login Handler s Kompletnom Zaštitom

```go
func (h *AuthHandler) Login(c *gin.Context) {
    var req LoginRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": "invalid request"})
        return
    }
    
    // 1. Input validation
    if err := validateLoginInput(req.Email, req.Password); err != nil {
        c.JSON(400, gin.H{"error": "invalid credentials format"})
        return
    }
    
    // 2. IP rate limiting
    clientIP := c.ClientIP()
    if err := h.rateLimiter.CheckIP(c.Request.Context(), clientIP); err != nil {
        c.Header("Retry-After", "600")
        c.JSON(429, gin.H{"error": "too many requests"})
        return
    }
    
    email := strings.ToLower(strings.TrimSpace(req.Email))
    
    // 3. Provjeri account lockout
    locked, err := h.authService.isAccountLocked(c.Request.Context(), email)
    if err != nil {
        c.JSON(500, gin.H{"error": "internal server error"})
        return
    }
    if locked {
        // VAŽNO: Ista greška kao za pogrešnu lozinku!
        // Ne otkrivaj da li nalog postoji ili je zaključan
        c.JSON(401, gin.H{"error": "invalid credentials"})
        return
    }
    
    // 4. Autentikacija
    user, err := h.authService.Authenticate(c.Request.Context(), email, req.Password)
    if err != nil {
        // 5. Zabilježi neuspjeli pokušaj
        h.authService.recordFailedAttempt(c.Request.Context(), email)
        
        // NIKAD ne vraćaj "user not found" vs "wrong password" — napadač bi znao koji emailovi postoje
        c.JSON(401, gin.H{"error": "invalid credentials"})
        return
    }
    
    // 6. Uspješan login — reset fail counter
    h.authService.clearFailedAttempts(c.Request.Context(), email)
    
    // 7. Generiši tokene
    accessToken, refreshToken, err := h.authService.GenerateTokens(c.Request.Context(), user)
    if err != nil {
        c.JSON(500, gin.H{"error": "token generation failed"})
        return
    }
    
    // 8. Postavi refresh token kao httpOnly cookie
    c.Header("Set-Cookie", fmt.Sprintf(
        "refresh_token=%s; Max-Age=%d; Path=/api/auth/refresh; Secure; HttpOnly; SameSite=Strict",
        refreshToken, 7*24*3600,
    ))
    
    // 9. Loguj uspješan login
    log.WithFields(log.Fields{
        "user_id": user.ID,
        "ip":      clientIP,
        "ua":      c.Request.UserAgent(),
    }).Info("Successful login")
    
    c.JSON(200, gin.H{
        "access_token": accessToken,
        "expires_in":   900,
    })
}
```

### Exponential Backoff na Klijentskoj Strani

```javascript
// Nije zamjena za server-side zaštitu — dodatni sloj
// composables/useAuth.js

const loginAttempts = ref(0)
const backoffUntil = ref(null)

async function login(email, password) {
  // Provjeri backoff
  if (backoffUntil.value && Date.now() < backoffUntil.value) {
    const remaining = Math.ceil((backoffUntil.value - Date.now()) / 1000)
    throw new Error(`Molimo pričekajte ${remaining} sekundi`)
  }
  
  try {
    const response = await api.post('/auth/login', { email, password })
    loginAttempts.value = 0
    backoffUntil.value = null
    return response.data
  } catch (error) {
    if (error.response?.status === 401 || error.response?.status === 429) {
      loginAttempts.value++
      // Exponential backoff: 2^n sekundi (1, 2, 4, 8, 16...)
      const delay = Math.min(Math.pow(2, loginAttempts.value) * 1000, 30000)
      backoffUntil.value = Date.now() + delay
    }
    throw error
  }
}
```

---

## JWT Security Best Practices

### Kratki Expiry Vremeni

```go
// services/auth/token.go

const (
    AccessTokenDuration  = 15 * time.Minute  // Kratak — ako ukraden, brzo istekne
    RefreshTokenDuration = 7 * 24 * time.Hour // Duži — samo httpOnly cookie
)

type JWTClaims struct {
    UserID int64  `json:"sub"`
    Email  string `json:"email"`
    Role   string `json:"role"`
    JTI    string `json:"jti"` // JWT ID — za revokaciju
    jwt.RegisteredClaims
}

func (s *TokenService) GenerateAccessToken(user *User) (string, error) {
    jti := generateJTI() // UUID v4
    
    claims := JWTClaims{
        UserID: user.ID,
        Email:  user.Email,
        Role:   user.Role,
        JTI:    jti,
        RegisteredClaims: jwt.RegisteredClaims{
            Issuer:    "project-a",
            Subject:   strconv.FormatInt(user.ID, 10),
            Audience:  jwt.ClaimStrings{"project-a-api"},
            IssuedAt:  jwt.NewNumericDate(time.Now()),
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(AccessTokenDuration)),
            NotBefore: jwt.NewNumericDate(time.Now()),
        },
    }
    
    token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
    return token.SignedString(s.privateKey)
}
```

### RS256 vs HS256

```
HS256 (HMAC-SHA256):
  - Jedan isti ključ za signing i verificiranje
  - Svi servisi koji verificiraju token moraju imati isti secret
  - Ako jedan servis kompromitovan → napadač može forge-ati tokene

RS256 (RSA-SHA256):
  - Private key: samo auth service (signing)
  - Public key: svi drugi servisi (samo verifikacija)
  - Kompromitovan servisi ne mogu forge-ati tokene
```

```go
import (
    "crypto/rsa"
    "github.com/golang-jwt/jwt/v5"
)

// Auth service: čita private key iz Secrets Manager-a (modul 14)
func loadPrivateKey() (*rsa.PrivateKey, error) {
    keyPEM, err := secretsManager.GetSecret(ctx, "jwt-private-key")
    if err != nil {
        return nil, err
    }
    block, _ := pem.Decode([]byte(keyPEM))
    return x509.ParsePKCS1PrivateKey(block.Bytes)
}

// Drugi servisi: verificiraju s public key-em
func loadPublicKey() (*rsa.PublicKey, error) {
    keyPEM, err := secretsManager.GetSecret(ctx, "jwt-public-key")
    if err != nil {
        return nil, err
    }
    block, _ := pem.Decode([]byte(keyPEM))
    pub, err := x509.ParsePKIXPublicKey(block.Bytes)
    return pub.(*rsa.PublicKey), err
}

// Generisanje RSA keypair-a (jednokratno, pri setup-u):
// openssl genrsa -out private.pem 4096
// openssl rsa -in private.pem -pubout -out public.pem
```

### JWT Revokacija s Redis Denylist

```go
// Svaki access token ima jedinstveni JTI (JWT ID)
// Pri logout-u, dodamo JTI u Redis denylist

func (s *TokenService) RevokeToken(ctx context.Context, jti string, expiresAt time.Time) error {
    ttl := time.Until(expiresAt)
    if ttl <= 0 {
        return nil // Token je već istekao, nije ga potrebno revokirati
    }
    
    // Ključ: "denylist:jti:<JTI>"
    // TTL: do isteka tokena (ne čuvamo zauvijek)
    return s.redis.Set(ctx, "denylist:jti:"+jti, "revoked", ttl).Err()
}

func (s *TokenService) IsRevoked(ctx context.Context, jti string) (bool, error) {
    val, err := s.redis.Get(ctx, "denylist:jti:"+jti).Result()
    if err == redis.Nil {
        return false, nil // Nije na denylist-u — validan
    }
    return val == "revoked", err
}

// JWT Middleware s denylist provjerom
func JWTMiddleware(tokenService *TokenService) gin.HandlerFunc {
    return func(c *gin.Context) {
        tokenStr := extractBearerToken(c)
        claims, err := tokenService.ValidateAccessToken(tokenStr)
        if err != nil {
            c.AbortWithStatusJSON(401, gin.H{"error": "invalid token"})
            return
        }
        
        // Provjeri denylist
        revoked, err := tokenService.IsRevoked(c.Request.Context(), claims.JTI)
        if err != nil || revoked {
            c.AbortWithStatusJSON(401, gin.H{"error": "token revoked"})
            return
        }
        
        c.Set("claims", claims)
        c.Next()
    }
}
```

### Ne Stavljaj Sensitive Podatke u JWT Payload

JWT payload je **Base64 encoded, nije enkriptovan**. Svako tko ima token može ga decodirati:

```bash
# Payload svakog JWT-a je čitljiv:
echo "eyJzdWIiOiIxMjM0IiwiZW1haWwiOiJ1c2VyQGZpcm1hLmNvbSIsInJvbGUiOiJ1c2VyIn0" | base64 -d
# {"sub":"1234","email":"user@firma.com","role":"user"}
```

```go
// NIKAD u JWT payload:
type DangerousJWTClaims struct {
    Password    string `json:"password"`    // Očigledno ne
    CreditCard  string `json:"cc"`          // PCI DSS violation
    SocialSec   string `json:"ssn"`         // GDPR/HIPAA violation
    APIKey      string `json:"api_key"`     // Leakuje u svaki log
    FullAddress string `json:"address"`     // Nepotrebno
}

// OK u JWT payload (minimalni podaci):
type SafeJWTClaims struct {
    UserID int64  `json:"sub"`   // ID za dohvat podataka iz baze
    Email  string `json:"email"` // Za prikaz, ne povjerljivo
    Role   string `json:"role"`  // Za authorization check
    JTI    string `json:"jti"`   // Za revokaciju
    // Ostali podaci: dohvati iz baze po potrebi
}
```

---

## Timing Attacks — `crypto/subtle`

Naivna usporedba stringova je ranjiva na timing napade:

```go
// RANJIVO — string usporedba se zaustavi na prvom različitom byte-u
func validateToken(provided, expected string) bool {
    return provided == expected
    // Ako provided = "abc" i expected = "xyz":
    // - Prva slova 'a' vs 'x' → različito → odmah return false (brže!)
    // Napadač mjeri response time i "pogađa" token bajt po bajt
}

// SIGURNO — constant time usporedba (uvijek pregledava sve byte-ove)
import "crypto/subtle"

func validateToken(provided, expected string) bool {
    // ConstantTimeCompare UVIJEK traje isto, bez obzira na gdje se razlikuju
    return subtle.ConstantTimeCompare([]byte(provided), []byte(expected)) == 1
}
```

**Zašto to vrijedi:** Napadač šalje 1000 zahtjeva s `"a..."`, mjeri prosječni response time. Ako `"a"` traje malo duže nego `"z"`, zna da je prvi karakter ispravno pogođen. Ponavljaj za svaki karakter → cijeli secret "pogođen" bez ikakvog poznavanja sistema.

bcrypt.CompareHashAndPassword je već constant time — ne treba dodatna zaštita za lozinke.

### Gdje Koristiti ConstantTimeCompare

```go
// API key validacija
func (m *APIKeyMiddleware) validate(provided string) bool {
    return subtle.ConstantTimeCompare([]byte(provided), []byte(m.expectedKey)) == 1
}

// CSRF token validacija
func validateCSRFToken(fromCookie, fromHeader string) bool {
    if len(fromCookie) == 0 || len(fromHeader) == 0 {
        return false
    }
    return subtle.ConstantTimeCompare([]byte(fromCookie), []byte(fromHeader)) == 1
}

// Webhook signature validacija (GitHub/Stripe stil)
func validateWebhookSignature(payload []byte, signature, secret string) bool {
    mac := hmac.New(sha256.New, []byte(secret))
    mac.Write(payload)
    expected := hex.EncodeToString(mac.Sum(nil))
    return subtle.ConstantTimeCompare([]byte(signature), []byte(expected)) == 1
}
```

---

## Kompletni Auth Flow Dijagram

```
LOGIN REQUEST:
  1. Input validation (email format, password length)
  2. IP rate limit check (Redis: 20 req / 10 min)
  3. Account lockout check (Redis: locked:<email>)
  4. Dohvati user iz MySQL (prepared statement)
  5. bcrypt.CompareHashAndPassword (constant time)
  6. Ako fail: inkrementiraj Redis fail counter
  7. Ako success: generiši RS256 JWT (access + refresh)
  8. Postavi refresh token kao httpOnly SameSite=Strict cookie
  9. Vrati access token u response body
  10. Loguj event (success ili fail) s IP, UA, timestamp

SVAKI AUTHENTICATED REQUEST:
  1. Extract Bearer token iz Authorization headera
  2. Verificiraj RS256 signature
  3. Provjeri expiry (exp claim)
  4. Provjeri denylist (Redis: denylist:jti:<JTI>)
  5. Postavi claims u context
  6. Role check (ako endpoint to zahtijeva)

LOGOUT:
  1. Dodaj access token JTI u Redis denylist (do expiry-a)
  2. Obriši refresh token cookie (Set-Cookie: Max-Age=0)
  3. Loguj logout event

TOKEN REFRESH:
  1. httpOnly cookie se automatski šalje
  2. Verificiraj refresh token (database lookup + expiry)
  3. Invaliduj stari refresh token (rotation)
  4. Generiši novi access + refresh token par
  5. Vrati novi access token, postavi novi httpOnly cookie
```

---

## Security Checklist za Auth

- [ ] bcrypt cost=12 za sve nove lozinke
- [ ] Migracija strategija za legacy MD5/SHA1 hash-ove
- [ ] Redis rate limiting po IP (20 req/10 min)
- [ ] Account lockout po email-u (10 fail → 15 min lock)
- [ ] Generička greška ("invalid credentials") — nikad ne otkrivaj da li email postoji
- [ ] RS256 JWT (ne HS256)
- [ ] Access token: 15 min expiry
- [ ] Refresh token: httpOnly, Secure, SameSite=Strict cookie
- [ ] JWT denylist u Redis (revokacija pri logout-u)
- [ ] Nikakvi sensitive podaci u JWT payload
- [ ] `crypto/subtle.ConstantTimeCompare` za sve token usporedbe
- [ ] Loguj sve auth evente (success + fail) s IP i user agentom
