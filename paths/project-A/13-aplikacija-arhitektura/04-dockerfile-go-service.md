# 04 — Dockerfile: Go servis

## Zašto scratch final image

`scratch` je prazan Docker image — nema OS-a, nema shell-a, nema ničega. Samo binary.

Prednosti:
- **Veličina**: Go binary + CA certifikati = 8-20MB. `golang:1.22-alpine` base ima 300MB+.
- **Attack surface**: Nema shell-a, nema package manager-a, nema utilities-a. Ako napadač dobije RCE, nema alata za daljnji exploit.
- **CVE scan**: Svi CVE-ovi koji se nalaze u Alpine OS-u (bash, busybox, musl libc) ne postoje u scratch image-u.

Cijena: nemogućnost `kubectl exec` debug sesije (nema shell-a). Za debugging koristiti sidecar ili ephemeral debug container.

---

## Dockerfile

```dockerfile
# ---- Build stage ----
FROM golang:1.22-alpine AS builder

# Build alati za CGO (nije potrebno ako CGO_ENABLED=0, ali alpine treba git za go modules)
RUN apk add --no-cache git ca-certificates tzdata

WORKDIR /app

# Prekopiraj go.mod i go.sum za layer caching
# go mod download se ne rerunuje ako se zavisnosti nisu promijenile
COPY go.mod go.sum ./
RUN go mod download

# Kopiraj source
COPY . .

# Build: statički binary, nema dynamic linking
# CGO_ENABLED=0: isključi C interop (potrebno za scratch image)
# GOOS=linux: cross-compile ako buildaš na Mac-u
# -ldflags="-w -s": strip debug info i symbol table (~30% manji binary)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-w -s" -o /app/server ./cmd/server

# ---- Final stage: scratch ----
FROM scratch

# CA certifikati — KRITIČNO za HTTPS pozive ka vanjskim servisima
# Bez ovih, tls.Dial i http.Client sa https:// failaju sa "x509: certificate signed by unknown authority"
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Timezone data — za time.LoadLocation("Europe/Sarajevo") i slično
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Binary
COPY --from=builder /app/server /app/server

EXPOSE 8080

# Health check: Go binary sa -health flagom izlazi s 0 ako je server OK
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD ["/app/server", "-health"]

USER 1000:1000  # Non-root, numerički jer scratch nema /etc/passwd

ENTRYPOINT ["/app/server"]
```

---

## main.go — kompletan primjer sa MySQL master/replica i Redis

```go
package main

import (
    "context"
    "database/sql"
    "encoding/json"
    "flag"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/go-redis/redis/v8"
    _ "github.com/go-sql-driver/mysql"
)

type App struct {
    masterDB  *sql.DB
    replicaDB *sql.DB
    redis     *redis.Client
    logger    *log.Logger
}

func main() {
    // Health check mode: binary se može pozvati sa -health flagom
    // Radi HTTP request na localhost, izlazi 0 ako OK, 1 ako nije
    healthCheck := flag.Bool("health", false, "Run health check and exit")
    flag.Parse()

    if *healthCheck {
        resp, err := http.Get("http://localhost:8080/health")
        if err != nil || resp.StatusCode != 200 {
            os.Exit(1)
        }
        os.Exit(0)
    }

    logger := log.New(os.Stdout, "[go-service] ", log.LstdFlags|log.Lshortfile)

    // MySQL master konekcija (write operacije)
    masterDSN := os.Getenv("MYSQL_MASTER_DSN")
    masterDB, err := sql.Open("mysql", masterDSN)
    if err != nil {
        logger.Fatalf("master db open: %v", err)
    }
    masterDB.SetMaxOpenConns(25)
    masterDB.SetMaxIdleConns(5)
    masterDB.SetConnMaxLifetime(5 * time.Minute)

    // MySQL replica konekcija (read operacije)
    replicaDSN := os.Getenv("MYSQL_REPLICA_DSN")
    replicaDB, err := sql.Open("mysql", replicaDSN)
    if err != nil {
        logger.Fatalf("replica db open: %v", err)
    }
    replicaDB.SetMaxOpenConns(50)  // Replica prima više konekcija (read-heavy)
    replicaDB.SetMaxIdleConns(10)
    replicaDB.SetConnMaxLifetime(5 * time.Minute)

    // Redis klijent
    rdb := redis.NewClient(&redis.Options{
        Addr:         os.Getenv("REDIS_ADDR"),
        Password:     os.Getenv("REDIS_PASSWORD"),
        DB:           0,
        PoolSize:     10,
        DialTimeout:  3 * time.Second,
        ReadTimeout:  3 * time.Second,
        WriteTimeout: 3 * time.Second,
    })

    app := &App{
        masterDB:  masterDB,
        replicaDB: replicaDB,
        redis:     rdb,
        logger:    logger,
    }

    // HTTP handler setup
    mux := http.NewServeMux()
    mux.HandleFunc("/health", app.healthHandler)
    mux.HandleFunc("/api/users", app.usersHandler)
    mux.HandleFunc("/api/users/login", app.loginHandler)

    // X-Request-ID middleware: propagacija tracing ID-ja kroz sve logove
    handler := requestIDMiddleware(mux)

    srv := &http.Server{
        Addr:         ":8080",
        Handler:      handler,
        ReadTimeout:  10 * time.Second,
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  60 * time.Second,
    }

    // Graceful shutdown: čekaj završetak in-flight zahtjeva
    go func() {
        logger.Printf("starting on :8080")
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            logger.Fatalf("listen: %v", err)
        }
    }()

    // Čekaj OS signal za shutdown
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)
    <-quit

    logger.Println("shutting down, draining connections...")
    ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        logger.Fatalf("shutdown: %v", err)
    }
    logger.Println("shutdown complete")
}

// healthHandler provjerava sve zavisnosti
func (a *App) healthHandler(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
    defer cancel()

    checks := map[string]string{}
    healthy := true

    // Master DB ping
    if err := a.masterDB.PingContext(ctx); err != nil {
        checks["mysql_master"] = "failed: " + err.Error()
        healthy = false
    } else {
        checks["mysql_master"] = "ok"
    }

    // Replica DB ping
    if err := a.replicaDB.PingContext(ctx); err != nil {
        checks["mysql_replica"] = "failed: " + err.Error()
        // Replica failure nije fatalan — može raditi samo sa master-om
        checks["mysql_replica"] = "degraded: " + err.Error()
    } else {
        checks["mysql_replica"] = "ok"
    }

    // Redis ping
    if err := a.redis.Ping(ctx).Err(); err != nil {
        checks["redis"] = "failed: " + err.Error()
        healthy = false
    } else {
        checks["redis"] = "ok"
    }

    status := http.StatusOK
    if !healthy {
        status = http.StatusServiceUnavailable
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(map[string]interface{}{
        "status": func() string {
            if healthy {
                return "healthy"
            }
            return "degraded"
        }(),
        "checks": checks,
    })
}

// loginHandler: write na master, ne na repliku
func (a *App) loginHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
        return
    }

    ctx := r.Context()

    var creds struct {
        Email    string `json:"email"`
        Password string `json:"password"`
    }
    if err := json.NewDecoder(r.Body).Decode(&creds); err != nil {
        http.Error(w, "invalid json", http.StatusBadRequest)
        return
    }

    // Query na repliku za read — pronađi korisnika
    var userID int64
    var hashedPassword string
    err := a.replicaDB.QueryRowContext(ctx,
        "SELECT id, password_hash FROM users WHERE email = ? LIMIT 1",
        creds.Email,
    ).Scan(&userID, &hashedPassword)
    if err == sql.ErrNoRows {
        http.Error(w, "invalid credentials", http.StatusUnauthorized)
        return
    }
    if err != nil {
        a.logger.Printf("login query: %v", err)
        http.Error(w, "internal error", http.StatusInternalServerError)
        return
    }

    // Verify password (bcrypt ili argon2)
    // if !verifyPassword(creds.Password, hashedPassword) { ... }

    // Update last_login na MASTER — write operacija
    _, err = a.masterDB.ExecContext(ctx,
        "UPDATE users SET last_login = NOW() WHERE id = ?",
        userID,
    )
    if err != nil {
        a.logger.Printf("update last_login: %v", err)
        // Non-fatal: logovati ali ne failati login zahtjev
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]interface{}{
        "user_id": userID,
        "status":  "authenticated",
    })
}

// requestIDMiddleware: dodaj/propagiraj X-Request-ID kroz sve servise
func requestIDMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            // Generiši novi ako nije primljen od upstream-a
            requestID = generateRequestID()
        }
        w.Header().Set("X-Request-ID", requestID)
        next.ServeHTTP(w, r)
    })
}

func generateRequestID() string {
    // U produkciji koristiti uuid library ili crypto/rand
    return time.Now().Format("20060102150405.000000000")
}
```

---

## Expert gotcha: CA certifikati u scratch image-u

Ovo je najčešći razlog zašto Go aplikacija u scratch image-u ne funkcioniše u produkciji a radi lokalno.

Alpine builder image ima CA certifikate na `/etc/ssl/certs/ca-certificates.crt`. Scratch nema. Svaki HTTPS poziv (ka AWS S3, ka external API-ju, ka MySQL sa SSL-om) failuje:

```
tls: failed to verify certificate: x509: certificate signed by unknown authority
```

Rješenje je explicitno kopiranje u final image:
```dockerfile
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
```

Ako se koristi `distroless/static` umjesto `scratch`, CA certifikati su uključeni. `distroless` je kompromis između scratch (maximo sigurnost) i alpine (debug mogućnosti).

---

## Connection pool sizing za MySQL

```go
// Master DB: primarna write konekcija
masterDB.SetMaxOpenConns(25)   // Maksimalan broj otvorenih konekcija
masterDB.SetMaxIdleConns(5)    // Konekcije koje čekaju u pool-u
masterDB.SetConnMaxLifetime(5 * time.Minute)  // Recikliranje konekcija (spriječava stale connections)

// Replica DB: više konekcija jer read-heavy workload
replicaDB.SetMaxOpenConns(50)
replicaDB.SetMaxIdleConns(10)
```

`MaxOpenConns` mora biti usklađen sa MySQL `max_connections` postavkom. Ako imaš 3 replika Go pod-a sa MaxOpenConns=50, to je 150 konekcija samo od Go servisa. MySQL default `max_connections = 151` — prekoračenje uzrokuje "too many connections" error.

Formula za K8s: `mysql_max_connections = (broj_pod_replika × MaxOpenConns) × 1.2` (20% buffer za admin konekcije i migracije).
