# 03 — XSS, CSRF i Security Headers

## XSS (Cross-Site Scripting) u Vue.js

XSS je napad gdje napadač inject-uje zlonamjerni JavaScript koji se izvršava u pretraživaču žrtve. Cilj: ukrasti session token, preusmjeriti na phishing stranicu, keylog.

### Kako Vue.js Štiti od XSS

Vue.js automatski escape-uje sve vrijednosti u template interpolaciji:

```vue
<template>
  <!-- Korisnik unese: <script>alert('xss')</script> -->
  
  <!-- SIGURNO — Vue escape-uje u HTML entitete -->
  <p>{{ userInput }}</p>
  <!-- Renderuje kao: &lt;script&gt;alert('xss')&lt;/script&gt; -->
  <!-- Prikazano kao tekst, ne izvršava se -->
  
  <!-- SIGURNO — atributi su escape-ovani -->
  <input :value="userInput" />
  <!-- Ne može injektovati event handler -->
  
  <!-- OPASNO — v-html bypass-uje Vue escape -->
  <div v-html="userInput"></div>
  <!-- Renderuje: <script>alert('xss')</script> — IZVRŠAVA SE! -->
</template>
```

**Pravilo:** Traži `v-html` u cijelom codebase-u pri code review-u:

```bash
# Pronađi sve v-html upotrebe u projektu
grep -rn "v-html" services/frontend/src/
```

Svaki `v-html` mora biti justificiran i mora koristiti DOMPurify sanitizaciju.

### DOMPurify — Sanitizacija Rich Text-a

Kada je `v-html` neophodan (npr. editor sadržaj, markdown rendered output):

```javascript
// npm install dompurify
// npm install @types/dompurify  (za TypeScript)

// composables/useSanitize.js
import DOMPurify from 'dompurify'

// Konfiguracija za rich text (blog postovi, opisi)
const RICH_TEXT_CONFIG = {
  ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'b', 'i', 'ul', 'ol', 'li', 'h2', 'h3', 'blockquote'],
  ALLOWED_ATTR: [], // Nema atributa — sprječava href="javascript:", onclick, itd.
}

// Konfiguracija za inline formatiranje (komentari)
const INLINE_CONFIG = {
  ALLOWED_TAGS: ['strong', 'em', 'b', 'i'],
  ALLOWED_ATTR: [],
}

export function sanitizeRichText(html) {
  return DOMPurify.sanitize(html, RICH_TEXT_CONFIG)
}

export function sanitizeInline(html) {
  return DOMPurify.sanitize(html, INLINE_CONFIG)
}

// U komponenti:
import { sanitizeRichText } from '@/composables/useSanitize'

const safeContent = computed(() => sanitizeRichText(props.articleContent))
// <div v-html="safeContent"></div>
```

### DOM-Based XSS u Vue Router

```javascript
// OPASNO — direktno korištenje router query u template-u
// URL: https://app.firma.com/search?q=<script>alert(1)</script>
const route = useRoute()
// template: <h1>Rezultati za: {{ route.query.q }}</h1>  ← OVO je sigurno
// template: <div v-html="'Rezultati za: ' + route.query.q"></div>  ← OVO nije!

// OPASNO — open redirect
function redirectTo(url) {
  // Korisnik može poslati: javascript:alert(1)
  window.location.href = url  // NIKAD ovako s user inputom!
}

// SIGURNO — whitelist allowed paths
function safeRedirect(path) {
  const allowedPaths = ['/dashboard', '/profile', '/orders']
  if (allowedPaths.some(p => path.startsWith(p))) {
    router.push(path)
  } else {
    router.push('/dashboard')  // fallback
  }
}
```

### JWT u localStorage vs httpOnly Cookie

Ovo je jedan od najvažnijih arhitekturalnih security odluka:

```
localStorage.getItem('token')
                    ↑
         Dostupno SVIM JS skriptama!
         Ako ima XSS → token ukraden
         
vs.

httpOnly cookie
      ↑
Browser nikad ne eksponira JS kodu
Automatski šalje uz svaki request
Zaštićen od XSS napada
ALE: ranjiv na CSRF (vidjeti dolje)
```

**Rješenje za naš stack (Vue SPA + Go API):**

```javascript
// auth.js store — Pinia
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // Access token: u memoriji (ne localStorage, ne cookie)
  // Traje samo dok je tab otvoren — dovoljno za 15 min expiry
  const accessToken = ref(null)
  
  async function login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    // Backend postavlja refresh_token kao httpOnly cookie
    // Access token dolazi u response body
    accessToken.value = response.data.access_token
    // Ne: localStorage.setItem('access_token', ...)
  }
  
  async function refreshAccessToken() {
    // httpOnly cookie se automatski šalje — browser brine o tome
    const response = await api.post('/auth/refresh')
    accessToken.value = response.data.access_token
  }
  
  // Axios interceptor automatski dodaje token u header
  // (ne treba čitati iz localStorage)
})
```

```go
// Go backend: postavljanje httpOnly cookie
func (h *AuthHandler) Login(c *gin.Context) {
    // ... autentikacija ...
    
    // Access token u response body (kratkotrajan, 15 min)
    c.JSON(200, gin.H{
        "access_token": accessToken,
        "expires_in":   900,
    })
    
    // Refresh token kao httpOnly cookie (7 dana)
    c.SetCookie(
        "refresh_token",
        refreshToken,
        7*24*3600, // maxAge u sekundama
        "/api/auth/refresh", // path — dostupan samo ovom endpoint-u
        "app.firma.com",     // domain
        true,                // secure (HTTPS only)
        true,                // httpOnly (nije dostupan JS-u)
    )
}
```

---

## CSRF (Cross-Site Request Forgery)

### Zašto Naša SPA Arhitektura Smanjuje CSRF Rizik

CSRF napad: napadač obmanjuje autenticirani pretraživač žrtve da pošalje zahtjev na naš API.

**Klasični CSRF za form-based aplikacije:**
```html
<!-- Na attacker.com -->
<form action="https://bank.com/transfer" method="POST">
  <input name="to" value="attacker-account">
  <input name="amount" value="10000">
</form>
<script>document.forms[0].submit()</script>
```
Pretraživač šalje kolačiće automatski → transfer se izvrši bez znanja korisnika.

**Zašto naš JWT-based SPA je otporniji:**
- Vue.js šalje `Authorization: Bearer <token>` header
- Custom header (`Authorization`) ne može poslati simple CSRF form
- Napadačeva stranica ne može pročitati token iz drugog origin-a (Same-Origin Policy)

**ALE: refresh_token httpOnly cookie JE ranjiv!**

### Zaštita Refresh Token Cookie-a

```go
// SameSite=Strict je prva linija odbrane
c.SetCookie(
    "refresh_token",
    refreshToken,
    7*24*3600,
    "/api/auth/refresh",
    "app.firma.com",
    true,  // Secure
    true,  // HttpOnly
)
// Problem: SameSite ne možemo postaviti direktno kroz gin SetCookie

// Bolje — direktno postavi header:
sameSiteCookie := fmt.Sprintf(
    "refresh_token=%s; Max-Age=%d; Path=/api/auth/refresh; Domain=%s; Secure; HttpOnly; SameSite=Strict",
    refreshToken, 7*24*3600, "app.firma.com",
)
c.Header("Set-Cookie", sameSiteCookie)
```

**SameSite vrijednosti:**
- `Strict`: Cookie se nikad ne šalje s cross-site zahtjeva (najsigurnije, ali može smetati legitimnim slučajevima)
- `Lax`: Šalje se samo za top-level navigaciju (GET) — razuman kompromis
- `None`: Uvijek šalje (mora biti Secure) — ne koristiti za auth

### Double Submit Cookie Pattern

Ako SameSite nije dovoljan (npr. subdomain izolacija):

```go
// Go: generišemo CSRF token
func generateCSRFToken() string {
    b := make([]byte, 32)
    rand.Read(b)
    return base64.URLEncoding.EncodeToString(b)
}

// Login response: šaljemo CSRF token i kao cookie (ne httpOnly!) i u body-u
func (h *AuthHandler) Login(c *gin.Context) {
    csrfToken := generateCSRFToken()
    
    // Cookie: čitljiv JS-om (ne httpOnly) — za CSRF pattern to je ok
    c.SetCookie("csrf_token", csrfToken, 3600, "/", "app.firma.com", true, false)
    
    c.JSON(200, gin.H{
        "access_token": accessToken,
        "csrf_token":   csrfToken,
    })
}

// Middleware: validacija CSRF tokena
func CSRFMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        if c.Request.Method == "GET" || c.Request.Method == "HEAD" {
            c.Next()
            return
        }
        
        cookieToken, err := c.Cookie("csrf_token")
        headerToken := c.GetHeader("X-CSRF-Token")
        
        if err != nil || cookieToken == "" || !crypto_subtle.ConstantTimeCompare(
            []byte(cookieToken), []byte(headerToken)) == 1 {
            c.AbortWithStatusJSON(403, gin.H{"error": "CSRF validation failed"})
            return
        }
        c.Next()
    }
}
```

```javascript
// Vue: šalje CSRF token u header
// api.js
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    // Čitamo iz cookie (nije httpOnly)
    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_token='))
      ?.split('=')[1]
    
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken
    }
  }
  return config
})
```

### PHP: CSRF Token za Form Submissions

Ako PHP proxy ima form submissions (ne samo JSON API):

```php
// Slim middleware
class CsrfMiddleware
{
    public function process(Request $request, RequestHandler $handler): Response
    {
        if (in_array($request->getMethod(), ['POST', 'PUT', 'PATCH', 'DELETE'])) {
            $sessionToken = $_SESSION['csrf_token'] ?? null;
            
            // Provjeri u POST body ili header
            $requestToken = $request->getParsedBody()['_csrf_token'] 
                          ?? $request->getHeaderLine('X-CSRF-Token');
            
            if (!$sessionToken || !hash_equals($sessionToken, $requestToken)) {
                $response = new Response(403);
                $response->getBody()->write(json_encode(['error' => 'CSRF validation failed']));
                return $response;
            }
        }
        
        return $handler->handle($request);
    }
}

// Generisanje CSRF tokena u session-u
function generateCsrfToken(): string
{
    if (!isset($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}
```

---

## Security Headers u nginx

Security headers su HTTP response header-i koji instruiraju pretraživač kako da tretira sadržaj. Dodaju se u nginx konfiguraciju i štite sve stranice automatski.

```nginx
# /etc/nginx/conf.d/security-headers.conf
# Uključi ovaj fajl u server{} blok

# Content Security Policy — najvažniji header
# Govori pretraživaču odakle smije učitati skripte, stilove, slike
add_header Content-Security-Policy "
    default-src 'self';
    script-src 'self';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https://cdn.firma.com;
    font-src 'self' https://fonts.gstatic.com;
    connect-src 'self' https://api.firma.com wss://api.firma.com;
    frame-ancestors 'none';
    base-uri 'self';
    form-action 'self'
" always;

# Zabrani prikazivanje u iframe-u (clickjacking zaštita)
add_header X-Frame-Options "DENY" always;

# Zabrani MIME type sniffing (sprječava browser da "pogodi" content type)
add_header X-Content-Type-Options "nosniff" always;

# Kontroliraj koliko referer info se šalje
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Isključi browser features koje aplikacija ne koristi
add_header Permissions-Policy "
    geolocation=(),
    microphone=(),
    camera=(),
    payment=(),
    usb=(),
    magnetometer=(),
    gyroscope=(),
    accelerometer=()
" always;

# HSTS — govori pretraživaču da UVIJEK koristi HTTPS (1 godina)
# PAŽNJA: Jednom kad se postavi, browser odbija HTTP 1 godinu!
# Tek dodaj kad si siguran da HTTPS radi
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Ukloni nginx verziju iz Server headera
server_tokens off;
```

### CSP Za Vue.js SPA — Česti Problemi

Vue.js build ne treba `unsafe-inline` za skripte, ali developeri često dodaju jer ne znaju šta ga zahtijeva:

```nginx
# Osnovna CSP za Vue.js SPA:
Content-Security-Policy: 
    default-src 'self';
    script-src 'self';          # Vue build je bundleovan — ne treba inline
    style-src 'self' 'unsafe-inline'; # CSS-in-JS komponente (Vuetify, PrimeVue)
                                       # mogu zahtijevati unsafe-inline
    img-src 'self' data: blob:;
    font-src 'self';
    connect-src 'self' https://api.firma.com;
    worker-src 'self' blob:;    # Za web workere (PWA)
    manifest-src 'self';        # Za PWA manifest
```

**Testiranje CSP-a:**

1. Browser DevTools → Console: vidjet ćeš CSP violation greške
2. `report-to` direktiva za prikupljanje violations:

```nginx
# Dodaj u CSP:
Content-Security-Policy: ...; report-uri /api/csp-violations
```

```go
// Go handler za CSP reports (logovanje, ne blokiranje)
func (h *SecurityHandler) CSPViolation(c *gin.Context) {
    var report map[string]interface{}
    json.NewDecoder(c.Request.Body).Decode(&report)
    log.WithField("csp_violation", report).Warn("CSP violation detected")
    c.Status(204)
}
```

---

## CORS Konfiguracija u Go

CORS (Cross-Origin Resource Sharing) kontroliše koji origins smiju raditi cross-origin zahtjeve na naš API.

```go
// middleware/cors.go

var allowedOrigins = map[string]bool{
    "https://app.firma.com":         true,
    "https://app.dev.firma.com":     true,
    "https://app.staging.firma.com": true,
    // NE: "https://*.firma.com" — wildcard subdomain nije siguran
    // NE: "null" — može dozvoliti file:// zahtjeve
    // NE: "*" — dozvolio bi svaki origin za autenticirane zahtjeve!
}

func CORSMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        origin := c.Request.Header.Get("Origin")
        
        if allowedOrigins[origin] {
            c.Header("Access-Control-Allow-Origin", origin)
            c.Header("Access-Control-Allow-Credentials", "true") // Potrebno za cookies
            c.Header("Access-Control-Allow-Headers",
                "Content-Type, Authorization, X-CSRF-Token, X-Request-ID")
            c.Header("Access-Control-Allow-Methods",
                "GET, POST, PUT, PATCH, DELETE, OPTIONS")
            c.Header("Access-Control-Max-Age", "86400") // Preflight cache: 1 dan
        }
        
        // Odgovori na preflight request (OPTIONS)
        if c.Request.Method == "OPTIONS" {
            if allowedOrigins[origin] {
                c.AbortWithStatus(204)
            } else {
                c.AbortWithStatus(403)
            }
            return
        }
        
        c.Next()
    }
}
```

### CORS u Razvoju — Česta Zamka

```javascript
// vue.config.js ili vite.config.js — DEV ONLY proxy
// NE KORISTITI isti pattern u produkciji!
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        // Ovo radi u razvoju jer vite proxy ne šalje Origin header
        // U produkciji: nginx proxy ili direktni API pozivi
      }
    }
  }
})
```

---

## Security Headers Audit

Provjeri security headers bez plaćenog alata:

```bash
# Besplatno online: https://securityheaders.com
# Ili lokalno:

curl -I https://app.firma.com | grep -iE \
  "content-security-policy|x-frame-options|x-content-type|referrer-policy|permissions-policy|strict-transport"
```

**Cilj:** Sve ključne headere dobiti od SecurityHeaders.com.

```bash
# Test da li CSP blokira inline skripte:
curl -I https://app.firma.com | grep -i "content-security-policy"
# Provjeri postoji li 'unsafe-inline' u script-src
```

---

## Kompletna nginx Konfiguracija za project-a

```nginx
server {
    listen 443 ssl http2;
    server_name app.firma.com;
    
    # SSL konfiguracija (certifikati iz modula 15)
    ssl_certificate /etc/nginx/certs/firma.com.crt;
    ssl_certificate_key /etc/nginx/certs/firma.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "
        default-src 'self';
        script-src 'self';
        style-src 'self' 'unsafe-inline';
        img-src 'self' data: https://cdn.firma.com;
        connect-src 'self' https://api.firma.com;
        frame-ancestors 'none'
    " always;
    
    # Ukloni server header
    server_tokens off;
    more_clear_headers Server;  # nginx-extras paket
    
    # Vue.js SPA
    root /var/www/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy ka PHP service-u
    location /api/ {
        proxy_pass http://php-service:9000;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Ne prosljeđuj server header backend-a
        proxy_hide_header X-Powered-By;
        proxy_hide_header Server;
    }
}

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name app.firma.com;
    return 301 https://$host$request_uri;
}
```
