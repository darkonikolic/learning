# 02 — Go testovi

## Pokretanje testova

```bash
go test ./... -race -count=1
```

`-race` je obavezan za concurrent code. Go race detector instrumentira memorijske pristupe i detektuje data race uslove koji se inače pojavljuju jednom u hiljadu pokretanja. U produkciji se race ne može reproducirati — u testu s `-race` zastava puca odmah.

`-count=1` onemogućava Go test cache. Bez njega, ako se kod nije promijenio, Go vraća cached rezultat iz prethodnog pokretanja. U CI-ju ne želiš cached rezultate — hoćeš fresh run svaki put.

`./...` rekurzivno testira sve pakete. Za single paket: `go test ./internal/auth/...`

Korisne kombinacije:

```bash
# Verbose output — vidi svaki test i duration
go test ./... -v -race -count=1

# Samo specifični test (regex)
go test ./internal/auth/... -run TestValidateLogin -v

# Timeout za cijeli test suite
go test ./... -race -count=1 -timeout 5m

# Paralelno (defaultno je GOMAXPROCS, ali možeš limitirati)
go test ./... -race -count=1 -p 4
```

---

## Table-driven tests

Table-driven pristup je idiomatski Go. Umjesto da pišeš N funkcija za N slučajeva, definišeš struct slice s ulazima i očekivanim rezultatima.

```go
func TestValidateLogin(t *testing.T) {
    tests := []struct {
        name     string
        email    string
        password string
        wantErr  bool
    }{
        {"valid credentials", "user@test.com", "correctpass", false},
        {"empty email", "", "pass", true},
        {"empty password", "u@t.com", "", true},
        {"invalid email format", "notanemail", "pass", true},
        {"sql injection attempt", "'; DROP TABLE users;--", "x", true},
        {"email too long", string(make([]byte, 256)) + "@t.com", "pass", true},
        {"unicode email", "ñoño@tëst.com", "pass", false}, // valid per RFC
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := validateLogin(tt.email, tt.password)
            if (err != nil) != tt.wantErr {
                t.Errorf("validateLogin() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

`t.Run()` kreira subtest. Svaki subtest se može pokrenuti zasebno:
```bash
go test ./... -run "TestValidateLogin/sql_injection_attempt"
```

Prednost: kad dobaviš bug report "SQL injection ne blokira se", dodaš red u tablicu i test odmah postoji. Ne trebaš pisati novu funkciju.

### Parallel subtests

```go
for _, tt := range tests {
    tt := tt // capture loop variable — obavezno u Go < 1.22
    t.Run(tt.name, func(t *testing.T) {
        t.Parallel() // ovaj subtest može raditi paralelno s drugima
        err := validateLogin(tt.email, tt.password)
        // ...
    })
}
```

Go 1.22+ ne treba `tt := tt` zbog promjene loop variable semantike. Do tada — obavezno.

---

## Testcontainers-go: integration tests s pravom bazom

Testcontainers-go pokreće Docker containere iz Go koda. Nema mocking baze — pravi MySQL, pravi Redis, pravi container koji živi koliko i test.

```go
import (
    "context"
    "testing"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/wait"
)

func TestUserRepository(t *testing.T) {
    ctx := context.Background()

    // MySQL container
    mysqlC, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: testcontainers.ContainerRequest{
            Image: "mysql:8.0",
            Env: map[string]string{
                "MYSQL_ROOT_PASSWORD": "test",
                "MYSQL_DATABASE":      "testdb",
                "MYSQL_USER":          "testuser",
                "MYSQL_PASSWORD":      "testpass",
            },
            ExposedPorts: []string{"3306/tcp"},
            WaitingFor: wait.ForLog("ready for connections").
                WithOccurrence(2). // MySQL loga ovo dva puta pri startu
                WithStartupTimeout(60 * time.Second),
        },
        Started: true,
    })
    if err != nil {
        t.Fatalf("failed to start mysql container: %v", err)
    }
    defer mysqlC.Terminate(ctx)

    // Dohvati mapped port (Docker randomly assignuje host port)
    host, _ := mysqlC.Host(ctx)
    port, _ := mysqlC.MappedPort(ctx, "3306")

    dsn := fmt.Sprintf("testuser:testpass@tcp(%s:%s)/testdb?parseTime=true", host, port.Port())
    db, err := sql.Open("mysql", dsn)
    if err != nil {
        t.Fatalf("failed to connect to mysql: %v", err)
    }
    defer db.Close()

    // Migriraj shemu
    runMigrations(t, db)

    // Kreiraj repository s pravom DB konekcijom
    repo := NewUserRepository(db)

    // Test
    user, err := repo.Create(ctx, "test@example.com", "hashedpassword")
    if err != nil {
        t.Fatalf("Create() error = %v", err)
    }
    if user.Email != "test@example.com" {
        t.Errorf("Create() email = %v, want %v", user.Email, "test@example.com")
    }

    // Fetch back
    fetched, err := repo.FindByEmail(ctx, "test@example.com")
    if err != nil {
        t.Fatalf("FindByEmail() error = %v", err)
    }
    if fetched.ID != user.ID {
        t.Errorf("FindByEmail() ID = %v, want %v", fetched.ID, user.ID)
    }
}
```

### Zašto ne mock bazu?

Mock baze (npr. `sqlmock`) testiraju da li tvoj kod poziva `db.QueryRow` s određenim SQL stringom. To nije korisno — testiraš implementation detail, ne ponašanje. Ako refaktorišeš SQL query, mock test puca iako logika ostaje ispravna.

Testcontainers testiraju stvarno ponašanje: da li tvoj kod ispravno čita i zapisuje podatke u MySQL. Ako MySQL vrati drugačiji row od onog što očekuješ — test pada iz pravog razloga.

### Redis integration test

```go
func TestCacheLayer(t *testing.T) {
    ctx := context.Background()

    redisC, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: testcontainers.ContainerRequest{
            Image:        "redis:7-alpine",
            ExposedPorts: []string{"6379/tcp"},
            WaitingFor:   wait.ForLog("Ready to accept connections"),
        },
        Started: true,
    })
    if err != nil {
        t.Fatalf("redis container: %v", err)
    }
    defer redisC.Terminate(ctx)

    host, _ := redisC.Host(ctx)
    port, _ := redisC.MappedPort(ctx, "6379")

    rdb := redis.NewClient(&redis.Options{
        Addr: fmt.Sprintf("%s:%s", host, port.Port()),
    })
    defer rdb.Close()

    cache := NewSessionCache(rdb)

    // Test cache miss → dohvata iz DB
    t.Run("cache miss fetches from db", func(t *testing.T) {
        dbCalled := false
        dbFallback := func(id string) (*Session, error) {
            dbCalled = true
            return &Session{UserID: id, Token: "jwt123"}, nil
        }

        session, err := cache.GetSession(ctx, "user-1", dbFallback)
        assert.NoError(t, err)
        assert.True(t, dbCalled, "expected DB fallback to be called on cache miss")
        assert.Equal(t, "jwt123", session.Token)
    })

    // Test cache hit → ne dohvata iz DB
    t.Run("cache hit skips db", func(t *testing.T) {
        // Prethodni test je cachirao session, drugi poziv treba cache hit
        dbCalled := false
        dbFallback := func(id string) (*Session, error) {
            dbCalled = true
            return nil, errors.New("should not be called")
        }

        session, err := cache.GetSession(ctx, "user-1", dbFallback)
        assert.NoError(t, err)
        assert.False(t, dbCalled, "expected cache hit, DB should not be called")
        assert.Equal(t, "jwt123", session.Token)
    })
}
```

Ovaj test verificira stvarno Redis TTL, stvarno serijalizovanje/deserijalizovanje podataka, stvarni network round-trip.

---

## httptest: HTTP handler testing bez networka

`net/http/httptest` kreira in-memory HTTP server. Nema TCP konekcije, nema porta — direktan poziv handlera.

```go
func TestLoginHandler(t *testing.T) {
    tests := []struct {
        name       string
        body       string
        wantStatus int
        wantBody   string
    }{
        {
            name:       "valid credentials",
            body:       `{"email":"u@t.com","password":"correctpass"}`,
            wantStatus: http.StatusOK,
        },
        {
            name:       "wrong password",
            body:       `{"email":"u@t.com","password":"wrongpass"}`,
            wantStatus: http.StatusUnauthorized,
        },
        {
            name:       "malformed json",
            body:       `{not json}`,
            wantStatus: http.StatusBadRequest,
        },
        {
            name:       "missing fields",
            body:       `{}`,
            wantStatus: http.StatusBadRequest,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            req := httptest.NewRequest(
                "POST",
                "/api/auth/login",
                strings.NewReader(tt.body),
            )
            req.Header.Set("Content-Type", "application/json")

            rec := httptest.NewRecorder()

            // handler je tvoj http.Handler
            handler.ServeHTTP(rec, req)

            if rec.Code != tt.wantStatus {
                t.Errorf("status = %d, want %d, body: %s",
                    rec.Code, tt.wantStatus, rec.Body.String())
            }
        })
    }
}
```

`httptest.NewRecorder()` implementira `http.ResponseWriter` i bilježi sve što handler piše. Nakon poziva možeš inspekcirati `rec.Code`, `rec.Body`, `rec.Header()`.

### Testiranje middlewarea

```go
func TestAuthMiddleware(t *testing.T) {
    // Handler koji samo vrati 200 ako middleware propusti request
    next := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    })

    handler := AuthMiddleware(next)

    t.Run("valid token passes", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/api/protected", nil)
        req.Header.Set("Authorization", "Bearer "+validTestToken)
        rec := httptest.NewRecorder()
        handler.ServeHTTP(rec, req)
        assert.Equal(t, http.StatusOK, rec.Code)
    })

    t.Run("missing token returns 401", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/api/protected", nil)
        rec := httptest.NewRecorder()
        handler.ServeHTTP(rec, req)
        assert.Equal(t, http.StatusUnauthorized, rec.Code)
    })

    t.Run("expired token returns 401", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/api/protected", nil)
        req.Header.Set("Authorization", "Bearer "+expiredTestToken)
        rec := httptest.NewRecorder()
        handler.ServeHTTP(rec, req)
        assert.Equal(t, http.StatusUnauthorized, rec.Code)
    })
}
```

---

## Coverage

```bash
# Generiši coverage profile
go test -coverprofile=coverage.out ./...

# Prikaži po funkciji
go tool cover -func=coverage.out

# HTML report (otvori u browseru)
go tool cover -html=coverage.out -o coverage.html

# Samo total
go tool cover -func=coverage.out | tail -1
```

Output `tail -1`:
```
total:    (statements)    73.4%
```

Ovaj format je bitan za GitLab coverage regex:
```yaml
coverage: '/total:\s+\(statements\)\s+(\d+\.\d+)%/'
```

Coverage threshold — fail ako ispod 70%:
```bash
COVERAGE=$(go tool cover -func=coverage.out | tail -1 | awk '{print $3}' | tr -d '%')
if (( $(echo "$COVERAGE < 70" | bc -l) )); then
  echo "Coverage $COVERAGE% je ispod minimuma 70%"
  exit 1
fi
```

---

## JUnit output za GitLab

GitLab UI prikazuje test rezultate u MR-u samo ako su u JUnit XML formatu.

```bash
# Instaliraj go-junit-report
go install github.com/jstemmer/go-junit-report/v2@latest

# Pokrni testove i konvertuj output
go test ./... -v -race -count=1 2>&1 | go-junit-report -set-exit-code > junit.xml
```

`-v` je obavezan — go-junit-report treba verbose output da parsira test names i rezultate.
`-set-exit-code` — proces exituje s 1 ako ijedan test padne (inače go-junit-report uvijek exituje 0).

U GitLab CI:
```yaml
artifacts:
  reports:
    junit: junit.xml
```

GitLab će prikazati u MR: koji testovi su prošli, koji padali, diff od prethodnog run-a.

---

## Test Dockerfile stage

Testovi kao dio Docker builda — ako padnu, image se ne kreira.

```dockerfile
# Stage 1: Dependencies (cached layer)
FROM golang:1.22-alpine AS deps
WORKDIR /app
COPY go.mod go.sum .
RUN go mod download

# Stage 2: Test (ovisi o deps, ne o build)
FROM deps AS test
COPY . .
RUN go test ./... -race -count=1

# Stage 3: Build (ovisi o deps, ne o test — paralelno u BuildKit)
FROM deps AS build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /app/server .

# Stage 4: Production (minimalan image)
FROM scratch AS production
COPY --from=build /app/server /server
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
ENTRYPOINT ["/server"]
```

`FROM scratch` — prazan base image. Samo binary i SSL certifikati. Nema shell, nema package manager, nema attack surface. Veličina image-a: ~15MB umjesto ~300MB.

BuildKit napomena: `test` i `build` stage oba ovise o `deps`, ali ne ovise jedan o drugom. BuildKit može graditi oba paralelno. Final `production` stage ovisi samo o `build` (ne o `test`) — što znači:

```bash
# Samo test stage (CI koji samo treba test rezultate)
docker build --target test .

# Final image (implicitno pokreće sve dependency stages, uključujući test)
docker build --target production .
```

> **Podman:** `podman build --target test .`
> **Podman:** `podman build --target production .`

Ako `test` stage padne, `production` stage se nikad ne pokreće — ne možeš deployati untested kod.

### BuildKit cache za module download

```dockerfile
FROM golang:1.22-alpine AS deps
WORKDIR /app
COPY go.mod go.sum .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download
```

`--mount=type=cache` drži module cache između buildova. Bez toga svaki build preuzima sve dependencije iznova. S cache mountom, `go mod download` traje sekundi umjesto minuta.

### Testcontainers u Dockerfile buildu: ne radi

Testcontainers zahtijeva Docker daemon (socket `/var/run/docker.sock`). Unutar Docker builda nema Docker daemon-a — to je nested Docker problem. Opcije:

1. **Preporučeno**: Integration testovi idu u CI job s `services:` (MySQL, Redis kao sidecar) — ne u Dockerfile
2. Docker-in-Docker (DinD): kompleksno, sigurnosni problemi, ne preporučuje se
3. Testcontainers s Ryuk disabled + external socket: moguće ali fragile u CI okruženjima

Pragmatično rješenje: unit testovi u Dockerfile stage, integration testovi u CI job.
