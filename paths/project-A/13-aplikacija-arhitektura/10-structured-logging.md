# Structured Logging

## Zašto structured logging (ne fmt.Println / error_log)

`fmt.Println("user logged in")` je beskorisno u produkciji. Ne možeš filtrirati, pretraživati ni korelirati.

**Problemi sa plain-text logovima:**
- Nema konteksta — koji user, koji request, koji servis
- Nema filtriranja po severity-u
- Nema korelacije između PHP → Go → DB log zapisa
- Loki/CloudWatch ne može parsirati slobodan tekst efikasno

**JSON structured logging daje:**
- Loki i CloudWatch mogu pretraživati bilo koje polje
- `X-Request-ID` poveže sve log zapise za jedan HTTP request kroz PHP → Go → DB
- Log levels omogućavaju filtriranje: u dev loguješ DEBUG, u prod INFO i više
- Standardizovani format za sve servise u sistemu

**Nikad ne logovati:**
- Passworde (ni hashirane)
- JWT tokene (kompromitovan log = kompromitovani tokeni)
- Credit card brojeve, IBAN, CVV
- PII podatke koji nisu neophodne za debug (puno ime, adresa, JMBG)

---

## Go structured logging sa `zap`

`go.uber.org/zap` je najbrži structured logger za Go. Zero allocation u hot path-u.

```go
import "go.uber.org/zap"

func NewLogger(env string) *zap.Logger {
    var logger *zap.Logger
    if env == "production" {
        logger, _ = zap.NewProduction()  // JSON output, INFO level
    } else {
        logger, _ = zap.NewDevelopment() // Human-readable, DEBUG level
    }
    return logger
}
```

**Korištenje u kodu:**

```go
// INFO — normalne operacije
logger.Info("login attempt",
    zap.String("email", email),       // OK — email nije secret
    zap.String("request_id", requestID),
    zap.String("ip", clientIP),
)

// ERROR — operacija nije uspjela
logger.Error("database error",
    zap.Error(err),
    zap.String("request_id", requestID),
    zap.String("query", "SELECT users"),  // Samo query template, NE parametre!
)

// WARN — degradirano stanje, aplikacija radi ali ne idealno
logger.Warn("slow query detected",
    zap.Duration("duration", elapsed),
    zap.String("query", "SELECT orders"),
    zap.String("request_id", requestID),
)
```

**Sugared logger za manje kritične dijelove:**

```go
sugar := logger.Sugar()
sugar.Infof("cache miss for key %s", cacheKey)  // Manje performantan, ali čitljiviji
```

---

## JSON log format (production)

Svaki log zapis je jedan JSON objekt na jednoj liniji. Loki i CloudWatch indeksiraju ova polja.

```json
{"level":"info","ts":1705312800.123,"caller":"auth/handler.go:42","msg":"login attempt","email":"user@firma.com","request_id":"abc-123","ip":"1.2.3.4"}
{"level":"error","ts":1705312801.456,"caller":"db/user.go:88","msg":"database error","error":"connection refused","request_id":"abc-123"}
{"level":"warn","ts":1705312802.789,"caller":"db/query.go:115","msg":"slow query detected","duration":"2.3s","query":"SELECT orders","request_id":"abc-123"}
```

**Development format (human-readable):**

```
2024-01-15T14:00:00.123+0100    INFO    auth/handler.go:42    login attempt    {"email": "user@firma.com", "request_id": "abc-123", "ip": "1.2.3.4"}
2024-01-15T14:00:01.456+0100    ERROR   db/user.go:88         database error   {"error": "connection refused", "request_id": "abc-123"}
```

---

## X-Request-ID propagacija kroz servise

Svaki HTTP request dobija jedinstveni ID. Taj ID putuje kroz sve servise i pojavljuje se u svim log zapisima vezanim za taj request.

```
Browser → Nginx → PHP → Go → MySQL
              ↓        ↓
         X-Request-ID: abc-123 (kroz sve)
```

**Go middleware — generiši ili prosledi X-Request-ID:**

```go
type contextKey string

func requestIDMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            requestID = uuid.New().String()
        }
        // Stavi u context — dostupan kroz cijeli handler chain
        ctx := context.WithValue(r.Context(), contextKey("request_id"), requestID)
        // Vrati ga u response headeru
        w.Header().Set("X-Request-ID", requestID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Helper za dobijanje iz context-a
func getRequestID(ctx context.Context) string {
    if id, ok := ctx.Value(contextKey("request_id")).(string); ok {
        return id
    }
    return "unknown"
}
```

**PHP — prosledi X-Request-ID na Go service:**

```php
// U HTTP middleware ili base controlleru
$requestId = $request->getHeaderLine('X-Request-ID') ?: uniqid('php-', true);

$response = $httpClient->post('/api/auth/login', [
    'headers' => [
        'X-Request-ID' => $requestId,
        'Content-Type' => 'application/json',
    ],
    'json' => $payload,
]);

// Loguješ u PHP sa istim request_id
$this->logger->info('Forwarding login to Go service', [
    'request_id' => $requestId,
    'user_email' => $email,
]);
```

**Nginx — proslijedi header upstream-u:**

```nginx
location /api/ {
    proxy_pass http://go-service:8080;
    proxy_set_header X-Request-ID $request_id;  # $request_id je Nginx varijabla
    proxy_set_header X-Forwarded-For $remote_addr;
}
```

---

## Nginx access log u JSON formatu

Nginx logove treba staviti u isti JSON format da Loki može korelisati.

```nginx
log_format json_combined escape=json
    '{'
    '"time":"$time_iso8601",'
    '"method":"$request_method",'
    '"uri":"$request_uri",'
    '"status":$status,'
    '"duration":$request_time,'
    '"request_id":"$http_x_request_id",'
    '"upstream_time":"$upstream_response_time",'
    '"bytes_sent":$bytes_sent,'
    '"user_agent":"$http_user_agent"'
    '}';

access_log /var/log/nginx/access.log json_combined;
```

**Rezultat:**

```json
{"time":"2024-01-15T14:00:00+01:00","method":"POST","uri":"/login","status":200,"duration":0.045,"request_id":"abc-123","upstream_time":"0.042","bytes_sent":1024,"user_agent":"Mozilla/5.0"}
```

---

## Log levels policy

| Level | Kada koristiti | Primjeri |
|-------|----------------|----------|
| DEBUG | Samo u dev — isključeno u prod | SQL query sa parametrima, HTTP request body, cache lookup |
| INFO  | Normalne operacije koje treba pratiti | Login success, order created, cache hit/miss |
| WARN  | Aplikacija radi, ali nešto nije idealno | DB retry (2. pokušaj), slow query > 1s, rate limit blizu |
| ERROR | Operacija nije uspjela, user dobio grešku | Auth failed, DB connection error, payment failed |
| FATAL | App ne može nastaviti — izlazi iz procesa | Config error na startupu, missing required env var |

**Pravilo:** U produkciji INFO je minimum. DEBUG se loguje samo lokalno ili uz explicit flag.

```go
// Konfiguracija log levela iz env varijable
func NewLogger(env, logLevel string) *zap.Logger {
    config := zap.NewProductionConfig()
    
    if logLevel == "debug" {
        config.Level = zap.NewAtomicLevelAt(zap.DebugLevel)
    }
    
    logger, _ := config.Build()
    return logger
}
```

---

## Šta NIKAD ne logovati

```go
// LOŠE — password u plain textu u logu
logger.Info("login", zap.String("password", password))

// LOŠE — JWT token kompromituje sve sesije ako log procuri
logger.Info("token issued", zap.String("jwt", token))

// LOŠE — credit card broj
logger.Info("payment", zap.String("card", cardNumber))

// DOBRO — loguješ relevantan kontekst, bez secretova
logger.Info("login attempt",
    zap.String("email", email),       // OK — email nije tajni podatak
    zap.Bool("success", true),
    zap.String("request_id", requestID),
)

// DOBRO — za payment, loguješ transaction ID, ne card broj
logger.Info("payment processed",
    zap.String("transaction_id", txID),
    zap.String("masked_card", "****1234"),  // Samo zadnje 4 cifre
    zap.Int64("amount_cents", amount),
)
```

---

## Loki query za debug po request_id

Kada korisnik prijavi grešku, dobiješ `X-Request-ID` iz response headera i pratiš cijeli flow:

```logql
# Svi logovi za jedan request kroz sve servise
{namespace="project-a-prod"} | json | request_id = "abc-123"

# Samo ERROR logovi u zadnjih sat
{namespace="project-a-prod"} | json | level = "error" | __error__ = "" [1h]

# Spori requestovi — duration > 2s
{namespace="project-a-prod", container="go-service"} | json | duration > 2.0

# Go service errori za specifičan user
{namespace="project-a-prod", container="go-service"} | json | level = "error" | email = "user@firma.com"

# Nginx: sve 5xx greške
{namespace="project-a-prod", container="nginx"} | json | status >= 500
```

**Za CloudWatch Logs Insights:**

```sql
fields @timestamp, level, msg, request_id, email, error
| filter level = "error"
| filter request_id = "abc-123"
| sort @timestamp asc
```

---

## Inicijalizacija logger-a u main.go

```go
func main() {
    env := os.Getenv("APP_ENV")
    logLevel := os.Getenv("LOG_LEVEL")
    
    logger := NewLogger(env, logLevel)
    defer logger.Sync() // Flush buffera pri zatvaranju

    // Proslijedi svim handler-ima kroz dependency injection
    server := &Server{
        logger: logger,
        // ...
    }
    
    logger.Info("server starting",
        zap.String("env", env),
        zap.String("port", os.Getenv("PORT")),
    )
}
```

---

## Checklist

- [ ] Zap inicijalizovan u main.go, proslijeđen kroz DI
- [ ] Request ID middleware registrovan kao prvi middleware
- [ ] PHP prosljeđuje X-Request-ID na Go service
- [ ] Nginx access log u JSON formatu
- [ ] Nema `fmt.Println` ni `log.Printf` u production kodu
- [ ] Code review: nikakvi secreti u log porukama
- [ ] Loki query za request_id provjeren u dev
